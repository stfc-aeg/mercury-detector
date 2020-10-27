/*
 * MercuryFrameDecoder.cpp
 *
 * ODIN data frame decoder plugin for MERCURY detector UDP frame data.
 *
 *  Created on: Aug 11, 2020
 *      Author: Christian Angelsen, STFC DSSG
 */

#include "MercuryFrameDecoder.h"
#include "gettime.h"
#include "version.h"
#include <iostream>
#include <iomanip>
#include <sstream>
#include <string>
#include <arpa/inet.h>
#include <boost/algorithm/string.hpp>

using namespace FrameReceiver;

const std::string MercuryFrameDecoder::CONFIG_FEM_PORT_MAP = "fem_port_map";

#define MAX_IGNORED_PACKET_REPORTS 10

//! Constructor for MercuryFrameDecoder
//!
//! This constructor sets up the decoder, setting default values of frame tracking information
//! and allocating buffers for packet header, dropped frames and scratched packets
//!
MercuryFrameDecoder::MercuryFrameDecoder() :
    FrameDecoderUDP(),
		// sensors_config_(Mercury::sensorConfigTwo),
		current_frame_seen_(Mercury::default_frame_number),
    current_frame_buffer_id_(Mercury::default_frame_number),
    current_frame_buffer_(0),
    current_frame_header_(0),
    dropping_frame_data_(false),
    packets_ignored_(0),
    packets_lost_(0),
	  fem_packets_lost_(0)
{
  // Allocate buffers for packet header, dropped frames and scratched packets
  current_packet_header_.reset(new uint8_t[sizeof(Mercury::PacketHeader)]);
  dropped_frame_buffer_.reset(new uint8_t[Mercury::max_frame_size()]);
  ignored_packet_buffer_.reset(new uint8_t[Mercury::primary_packet_size]);
}

//! Destructor for MercuryFrameDecoder
//!
MercuryFrameDecoder::~MercuryFrameDecoder()
{
}

int MercuryFrameDecoder::get_version_major()
{
  return ODIN_DATA_VERSION_MAJOR;
}

int MercuryFrameDecoder::get_version_minor()
{
  return ODIN_DATA_VERSION_MINOR;
}

int MercuryFrameDecoder::get_version_patch()
{
  return ODIN_DATA_VERSION_PATCH;
}

std::string MercuryFrameDecoder::get_version_short()
{
  return ODIN_DATA_VERSION_STR_SHORT;
}

std::string MercuryFrameDecoder::get_version_long()
{
  return ODIN_DATA_VERSION_STR;
}

//! Initialise the frame decoder.
//!
//! This method initialises the decoder based on a configuration message passed by the
//! application controller. Parameters found in the decoder configuration are parsed and stored
//! in the decoder as appropriate.
//!
//! \param[in] logger - pointer to the message logger
//! \param[in] config_msg - configuration message
//!
void MercuryFrameDecoder::init(LoggerPtr& logger, OdinData::IpcMessage& config_msg)
{
  // Pass the configuration message to the base class decoder
  FrameDecoder::init(logger, config_msg);

  LOG4CXX_DEBUG_LEVEL(2, logger_, "Got decoder config message: " << config_msg.encode());

  // Extract the FEM to port map from the config message and pass to the parser. If no map is
  // present, use the default. If the map cannot be parsed correctly, thrown an exception to signal
  // an error to the app controller. Set the current number of active FEMs based on the output
  // of the map parsing.
  if (config_msg.has_param(CONFIG_FEM_PORT_MAP))
  {
      fem_port_map_str_ = config_msg.get_param<std::string>(CONFIG_FEM_PORT_MAP);
      LOG4CXX_DEBUG_LEVEL(1, logger_, "Parsing FEM to port map found in config: "
                          << fem_port_map_str_);
  }
  else
  {
      LOG4CXX_DEBUG_LEVEL(1,logger_, "No FEM to port map found in config, using default: "
                          << default_fem_port_map);
      fem_port_map_str_ = default_fem_port_map;
  }

  parse_fem_port_map(fem_port_map_str_);

  // Print a packet logger header to the appropriate logger if enabled
  if (enable_packet_logging_)
  {
    LOG4CXX_INFO(packet_logger_, "PktHdr: SourceAddress");
    LOG4CXX_INFO(packet_logger_, "PktHdr: |               SourcePort");
    LOG4CXX_INFO(packet_logger_, "PktHdr: |               |     DestinationPort");
    LOG4CXX_INFO(packet_logger_, "PktHdr: |               |     |      FrameCounter  [4 Bytes]");
    LOG4CXX_INFO(packet_logger_,
        "PktHdr: |               |     |      |           PacketCounter&Flags [4 Bytes]");
    LOG4CXX_INFO(packet_logger_, "PktHdr: |               |     |      |           |");
    LOG4CXX_INFO(packet_logger_, "PktHdr: |-------------- |---- |----  |---------- |----------");
  }

  // Reset the scratched and lost packet counters
  packets_ignored_ = 0;
  packets_lost_ = 0;
  fem_packets_lost_ = 0;
}

void MercuryFrameDecoder::request_configuration(const std::string param_prefix,
    OdinData::IpcMessage& config_reply)
{
  // Call the base class method to populate parameters
  FrameDecoder::request_configuration(param_prefix, config_reply);

  // Add current configuration parameters to reply
  config_reply.set_param(param_prefix + CONFIG_FEM_PORT_MAP, fem_port_map_str_);
}

//! Get the size of the frame buffers required for current operation mode.
//!
//! This method returns the frame buffer size required for the current operation mode, which is
//! determined by frame size.
//!
//! \return size of frame buffer in bytes
//!
const size_t MercuryFrameDecoder::get_frame_buffer_size(void) const
{
  size_t frame_buffer_size = get_frame_header_size() + Mercury::frame_size();
  return frame_buffer_size;
}

//! Get the size of the frame header.
//!
//! This method returns the size of the frame header used by the decoder, which in this case is the
//! MERCURY frame header.
//!
//! \return size of the frame header in bytes
const size_t MercuryFrameDecoder::get_frame_header_size(void) const
{
  return sizeof(Mercury::FrameHeader);
}

//! Get the size of a packet header.
//!
//! This method returns the size of a UDP packet header for the receiver thread, which in this case
//! is the size of the MERCURY packet header.
//!
//! \return size of the packet header in bytes.
//!
const size_t MercuryFrameDecoder::get_packet_header_size(void) const
{
  return sizeof(Mercury::PacketHeader);
}

//! Get a pointer to the packet header buffer.
//!
//! This method returns a pointer to the next packet header buffer. For this decoder, the packet
//! headers are discarded, so the current packet header is always returned.
//!
//! \return pointer to the packet header buffer
//!
void* MercuryFrameDecoder::get_packet_header_buffer(void)
{
  return current_packet_header_.get();
}

//! Process an incoming packet header
//!
//! This method is called to process an incoming packet header that has been received. The source
//! and content of that header is used to determine where to route the payload of the packet to on
//! the next receive. Header information is used to determine which frame buffer the current packet
//! should be routed to, and to request a new frame buffer when the first packet of a given frame
//! is received. Buffer exhaustion is also handled by directing all packets for the current frame
//! to a scratch buffer.
//!
//! \param[in] bytes_received - number of header bytes received
//! \param[in] port - UDP port packet header was received on
//! \param[in] from_addr - socket address structure with details of source of packet
//!
void MercuryFrameDecoder::process_packet_header(size_t bytes_received, int port,
    struct sockaddr_in* from_addr)
{
  // Dump raw header if packet logging enabled
  if (enable_packet_logging_)
  {
    std::stringstream ss;
    uint8_t* hdr_ptr = reinterpret_cast<uint8_t*>(current_packet_header_.get ());
    ss << "PktHdr: " << std::setw (15) << std::left << inet_ntoa (from_addr->sin_addr)
        << std::right << " " << std::setw (5) << ntohs (from_addr->sin_port) << " " << std::setw(5)
        << port << std::hex;

    for (unsigned int hdr_byte = 0; hdr_byte < sizeof(Mercury::PacketHeader); hdr_byte++)
    {
      if (hdr_byte % 8 == 0)
      {
        ss << "  ";
      }
      ss << std::setw (2) << std::setfill ('0') << (unsigned int) *hdr_ptr << " ";
      hdr_ptr++;
    }
    ss << std::dec;
    LOG4CXX_INFO(packet_logger_, ss.str ());
  }

  // Resolve the FEM index from the port the packet arrived on
  if (fem_port_map_.count(port)) {
    current_packet_fem_map_ =  fem_port_map_[port];

  }
  else
  {
    current_packet_fem_map_ = MercuryDecoderFemMapEntry(ILLEGAL_FEM_IDX, ILLEGAL_FEM_IDX);
    packets_ignored_++;
    if (packets_ignored_ < MAX_IGNORED_PACKET_REPORTS)
    {
      LOG4CXX_WARN(logger_, "Ignoring packet received on port " << port << " for unknown FEM idx");
    }
    else if (packets_ignored_ == MAX_IGNORED_PACKET_REPORTS)
    {
      LOG4CXX_WARN(logger_, "Reporting limit for ignored packets reached, suppressing further messages");
    }
  }

  // Extract fields from packet header
  uint32_t frame_counter = get_frame_counter ();
  uint32_t packet_number = get_packet_number ();
  bool start_of_frame_marker = get_start_of_frame_marker ();
  bool end_of_frame_marker = get_end_of_frame_marker ();

  int frame = static_cast<int> (frame_counter);

  LOG4CXX_DEBUG_LEVEL(3, logger_, "Got packet header:" << " packet: " << packet_number
      << " SOF: " << (int) start_of_frame_marker << " EOF: " << (int) end_of_frame_marker
      << " port: " << port << " fem idx: " << current_packet_fem_map_.fem_idx_
  );

  // Only handle the packet header and frame logic further if this packet is not being ignored
  if (current_packet_fem_map_.fem_idx_ != ILLEGAL_FEM_IDX)
  {
    if (frame != current_frame_seen_)
    {
      current_frame_seen_ = frame;

      if (frame_buffer_map_.count(current_frame_seen_) == 0)
      {
        if (empty_buffer_queue_.empty())
        {
          current_frame_buffer_ = dropped_frame_buffer_.get();

          if (!dropping_frame_data_)
          {
            LOG4CXX_ERROR(logger_, "First packet from frame " << current_frame_seen_
                << " detected but no free buffers available. Dropping packet data for this frame");
            dropping_frame_data_ = true;
          }
        }
        else
        {

          current_frame_buffer_id_ = empty_buffer_queue_.front();
          empty_buffer_queue_.pop();
          frame_buffer_map_[current_frame_seen_] = current_frame_buffer_id_;
          current_frame_buffer_ = buffer_manager_->get_buffer_address(current_frame_buffer_id_);

          if (!dropping_frame_data_)
          {
            LOG4CXX_DEBUG_LEVEL(2, logger_, "First packet from frame " << current_frame_seen_
                << " detected, allocating frame buffer ID " << current_frame_buffer_id_);
          }
          else
          {
            dropping_frame_data_ = false;
            LOG4CXX_DEBUG_LEVEL(2, logger_, "Free buffer now available for frame "
                << current_frame_seen_ << ", allocating frame buffer ID "
                << current_frame_buffer_id_);
          }
        }

        // Initialise frame header
        current_frame_header_ = reinterpret_cast<Mercury::FrameHeader*>(current_frame_buffer_);
        initialise_frame_header(current_frame_header_);

      }
      else
      {
        current_frame_buffer_id_ = frame_buffer_map_[current_frame_seen_];
        current_frame_buffer_ = buffer_manager_->get_buffer_address(current_frame_buffer_id_);
        current_frame_header_ = reinterpret_cast<Mercury::FrameHeader*>(current_frame_buffer_);
      }

    }

    Mercury::FemReceiveState* fem_rx_state =
        &(current_frame_header_->fem_rx_state);

    // If SOF or EOF markers seen in packet header, increment appropriate field in frame header
    if (start_of_frame_marker)
    {
      (fem_rx_state->sof_marker_count)++;
      (current_frame_header_->total_sof_marker_count)++;
    }
    if (end_of_frame_marker)
    {
      (fem_rx_state->sof_marker_count)++;
      (current_frame_header_->total_eof_marker_count)++;
    }

    // Update packet_number state map in frame header
    fem_rx_state->packet_state[packet_number] = 1;
  }
}

//! Initialise a frame header
//!
//! This method initialises the frame header specified by the pointer argument, setting
//! fields to their default values, clearing packet counters and setting the active FEM
//! fields as appropriate.
//!
//! \param[in] header_ptr - pointer to frame header to initialise.
//!
void MercuryFrameDecoder::initialise_frame_header(Mercury::FrameHeader* header_ptr)
{

  header_ptr->frame_number = current_frame_seen_;
  header_ptr->frame_state = FrameDecoder::FrameReceiveStateIncomplete;
  header_ptr->total_packets_received = 0;
  header_ptr->total_sof_marker_count = 0;
  header_ptr->total_eof_marker_count = 0;

  for (MercuryDecoderFemMap::iterator it = fem_port_map_.begin();
        it != fem_port_map_.end(); ++it)
  {
    header_ptr->active_fem_idx = (it->second).fem_idx_;
  }

  gettime(reinterpret_cast<struct timespec*>(&(header_ptr->frame_start_time)));
}

//! Get a pointer to the next payload buffer.
//!
//! This method returns a pointer to the next packet payload buffer within the appropriate frame.
//! The location of this is determined by state information set during the processing of the packet
//! header. If thepacket is not from a recognised FEM, a pointer to the ignored packet buffer will
//! be returned instead.
//!
//! \return pointer to the next payload buffer
//!
void* MercuryFrameDecoder::get_next_payload_buffer(void) const
{
  uint8_t* next_receive_location;

  if (current_packet_fem_map_.fem_idx_ != ILLEGAL_FEM_IDX)
  {
    std::size_t frame_size = Mercury::frame_size();

    next_receive_location = reinterpret_cast<uint8_t*>(current_frame_buffer_)
          + get_frame_header_size ()
          + (frame_size * current_packet_fem_map_.buf_idx_)
          + (0)
          + (Mercury::primary_packet_size * get_packet_number());
  }
  else
  {
    next_receive_location = reinterpret_cast<uint8_t*>(ignored_packet_buffer_.get());
  }

  return reinterpret_cast<void*>(next_receive_location);
}

//! Get the next packet payload size to receive.
//!
//! This method returns the payload size to receive for the next incoming packet, based on state
//! information set during processing of the header. The receive size may vary depending on
//! whether a primary or tail packet is being received, the size of both of which is dependent
//! on the current bit depth.
//!
//! \return size of next packet payload in bytes
//!
size_t MercuryFrameDecoder::get_next_payload_size(void) const
{
  size_t next_receive_size = 0;

  if (get_packet_number() < Mercury::num_primary_packets)
  {
    next_receive_size = Mercury::primary_packet_size;
  }
  else
  {
    next_receive_size = Mercury::tail_packet_size;
  }

  return next_receive_size;
}

//! Process a received packet payload.
//!
//! This method processes the payload of a received packet. This is restricted to
//! keeping track of the number of packets, SOF and EOF markers
//! etc received. If this packet is the last required to complete a frame, the number of SOF and EOF
//! markers seen is validated, the frame state is set to complete and the ready callback is called
//! to notify the main thread that the buffer is ready for processing.
//!
//! \param[in] bytes_received - number of packet payload bytes received
//! \return current frame receive state
//!
FrameDecoder::FrameReceiveState MercuryFrameDecoder::process_packet(size_t bytes_received,
		int port, struct sockaddr_in* from_addr)
{
  FrameDecoder::FrameReceiveState frame_state = FrameDecoder::FrameReceiveStateIncomplete;

  // Only process the packet if it is not being ignored due to an illegal port to FEM index mapping
  if (current_packet_fem_map_.fem_idx_ != ILLEGAL_FEM_IDX)
  {

    // Get a convenience pointer to the FEM receive state data in the frame header
    Mercury::FemReceiveState* fem_rx_state = &(current_frame_header_->fem_rx_state);

    // Increment the total and per-FEM packet received counters
    (fem_rx_state->packets_received)++;
    current_frame_header_->total_packets_received++;

    // If we have received the expected number of packets, perform end of frame processing
    // and hand off the frame for downstream processing.
    if (current_frame_header_->total_packets_received == Mercury::num_fem_frame_packets())
    {

      // Check that the appropriate number of SOF and EOF markers (one each per frame) have
      // been seen, otherwise log a warning

      if ((current_frame_header_->total_sof_marker_count != 1) ||
          (current_frame_header_->total_eof_marker_count != 1))
      {
        LOG4CXX_WARN(logger_, "Incorrect number of SOF ("
           << (int)current_frame_header_->total_sof_marker_count << ") or EOF ("
           << (int)current_frame_header_->total_eof_marker_count << ") markers "
           << "seen on completed frame " << current_frame_seen_);
      }

      // Set frame state accordingly
      frame_state = FrameDecoder::FrameReceiveStateComplete;

      // Complete frame header
      current_frame_header_->frame_state = frame_state;

      if (!dropping_frame_data_)
      {
        // Erase frame from buffer map
        frame_buffer_map_.erase(current_frame_seen_);

        // Notify main thread that frame is ready
        ready_callback_(current_frame_buffer_id_, current_frame_header_->frame_number);

        // Reset current frame seen ID so that if next frame has same number (e.g. repeated
        // sends of single frame 0), it is detected properly
        current_frame_seen_ = -1;
      }
    }
  }
  return frame_state;
}

//! Monitor the state of currently mapped frame buffers.
//!
//! This method, called periodically by a timer in the receive thread reactor, monitors the state
//! of currently mapped frame buffers. In any frame buffers have been mapped for a sufficiently
//! long time that indicates packets have been lost and the frame is incomplete, the frame is
//! flagged as such and notified to the main thread via the ready callback.
//!
void MercuryFrameDecoder::monitor_buffers(void)
{
  int frames_timedout = 0;
  struct timespec current_time;

  gettime(&current_time);

  // Loop over frame buffers currently in map and check their state
  std::map<int, int>::iterator buffer_map_iter = frame_buffer_map_.begin();
  while (buffer_map_iter != frame_buffer_map_.end())
  {
    int frame_num = buffer_map_iter->first;
    int buffer_id = buffer_map_iter->second;
    void* buffer_addr = buffer_manager_->get_buffer_address(buffer_id);
    Mercury::FrameHeader* frame_header = reinterpret_cast<Mercury::FrameHeader*>(buffer_addr);

    if (elapsed_ms(frame_header->frame_start_time, current_time) > frame_timeout_ms_)
    {

      const std::size_t num_fem_frame_packets =
          Mercury::num_fem_frame_packets();

      // Calculate packets lost on this frame and add to total
      uint32_t packets_lost = num_fem_frame_packets -
          frame_header->total_packets_received;
      packets_lost_ += packets_lost;
      if (packets_lost)
      {
        for (MercuryDecoderFemMap::iterator iter = fem_port_map_.begin();
            iter != fem_port_map_.end(); ++iter)
        {
          fem_packets_lost_ += num_fem_frame_packets -
              (frame_header->fem_rx_state.packets_received);
        }
      }

      LOG4CXX_DEBUG_LEVEL(1, logger_, "Frame " << frame_num << " in buffer " << buffer_id
          << " addr 0x" << std::hex
          << buffer_addr << std::dec << " timed out with " << frame_header->total_packets_received
          << " packets received, " << packets_lost << " packets lost");

      frame_header->frame_state = FrameReceiveStateTimedout;
      ready_callback_(buffer_id, frame_num);
      frames_timedout++;

      frame_buffer_map_.erase(buffer_map_iter++);
    }
    else
    {
      buffer_map_iter++;
    }
  }
  if (frames_timedout)
  {
    LOG4CXX_WARN(logger_, "Released " << frames_timedout << " timed out incomplete frames");
  }
  frames_timedout_ += frames_timedout;

  LOG4CXX_DEBUG_LEVEL(3, logger_,  get_num_mapped_buffers() << " frame buffers in use, "
      << get_num_empty_buffers() << " empty buffers available, "
      << frames_timedout_ << " incomplete frames timed out, "
      << packets_lost_ << " packets lost"
  );
}

//! Get the current status of the frame decoder.
//!
//! This method populates the IpcMessage passed by reference as an argument with decoder-specific
//! status information, e.g. packet loss by source.
//!
//! \param[in] param_prefix - path to be prefixed to each status parameter name
//! \param[in] status_msg - reference to IpcMesssage to be populated with parameters
//!
void MercuryFrameDecoder::get_status(const std::string param_prefix,
    OdinData::IpcMessage& status_msg)
{
  status_msg.set_param(param_prefix + "name", std::string("MercuryFrameDecoder"));
  status_msg.set_param(param_prefix + "packets_lost", packets_lost_);

  // Workaround for lack of array setters in IpcMessage
  rapidjson::Value fem_packets_lost_array(rapidjson::kArrayType);
  rapidjson::Value::AllocatorType allocator;

  fem_packets_lost_array.PushBack(fem_packets_lost_, allocator);

  status_msg.set_param(param_prefix + "fem_packets_lost", fem_packets_lost_array);
}

//! Get the current frame counter.
//!
//! This method extracts and returns the frame counter from the current UDP packet header.
//!
//! \return current frame counter
//!
uint32_t MercuryFrameDecoder::get_frame_counter(void) const
{
  return reinterpret_cast<Mercury::PacketHeader*>(current_packet_header_.get())->frame_counter;
}

//! Get the current packet number.
//!
//! This method extracts and returns the packet number from the current UDP packet header.
//!
//! \return current packet number
//!
uint32_t MercuryFrameDecoder::get_packet_number(void) const
{
  return reinterpret_cast<Mercury::PacketHeader*>(
      current_packet_header_.get())->packet_number_flags & Mercury::packet_number_mask;
}

//! Get the current packet start of frame (SOF) marker.
//!
//! This method extracts and returns the start of frame marker from the current UDP packet header.
//!
//! \return true is SOF marker set in packet header
//!
bool MercuryFrameDecoder::get_start_of_frame_marker(void) const
{
  uint32_t packet_number_flags =
      reinterpret_cast<Mercury::PacketHeader*>(current_packet_header_.get())->packet_number_flags;
  return ((packet_number_flags & Mercury::start_of_frame_mask) != 0);
}

//! Get the current packet end of frame (EOF) marker.
//!
//! This method extracts and returns the end of frame marker from the current UDP packet header.
//!
//! \return true is EOF marker set in packet header
//!
bool MercuryFrameDecoder::get_end_of_frame_marker(void) const
{
  uint32_t packet_number_flags =
      reinterpret_cast<Mercury::PacketHeader*>(current_packet_header_.get())->packet_number_flags;
  return ((packet_number_flags & Mercury::end_of_frame_mask) != 0);
}

//! Calculate and return an elapsed time in milliseconds.
//!
//! This method calculates and returns an elapsed time in milliseconds based on the start and
//! end timespec structs passed as arguments.
//!
//! \param[in] start - start time in timespec struct format
//! \param[in] end - end time in timespec struct format
//! \return eclapsed time between start and end in milliseconds
//!
unsigned int MercuryFrameDecoder::elapsed_ms(struct timespec& start, struct timespec& end)
{
  double start_ns = ((double) start.tv_sec * 1000000000) + start.tv_nsec;
  double end_ns = ((double) end.tv_sec * 1000000000) + end.tv_nsec;

  return (unsigned int)((end_ns - start_ns) / 1000000);
}

//! Parse the port to FEM index map configuration string.
//!
//! This method parses a configuration string containing port to FEM index mapping information,
//! which is expected to be of the format "port:idx,port:idx" etc. The map is saved in a member
//! variable for use in packet handling.
//!
//! \param[in] fem_port_map_str - string of port to FEM index mapping configuration
//! \return number of valid map entries parsed from string
//!
std::size_t MercuryFrameDecoder::parse_fem_port_map(const std::string fem_port_map_str)
{
    // Clear the current map
    fem_port_map_.clear();

    // Define entry and port:idx delimiters
    const std::string entry_delimiter(",");
    const std::string elem_delimiter(":");

    // Vector to hold entries split from map
    std::vector<std::string> map_entries;

    // Split into entries
    boost::split(map_entries, fem_port_map_str, boost::is_any_of(entry_delimiter));

    unsigned int buf_idx = 0;
    // Loop over entries, further splitting into port / fem index pairs
    for (std::vector<std::string>::iterator it = map_entries.begin(); it != map_entries.end(); ++it)
    {
        if (buf_idx >= 1) {
          LOG4CXX_WARN(logger_, "Decoder FEM port map configuration contains too many elements, "
                        << "truncating to maximium number of FEMs allowed ("
                        << 1 << ")");
          break;
        }

        std::vector<std::string> entry_elems;
        boost::split(entry_elems, *it, boost::is_any_of(elem_delimiter));

        // If a valid entry is found, save into the map
        if (entry_elems.size() == 2) {
            int port = static_cast<int>(strtol(entry_elems[0].c_str(), NULL, 10));
            int fem_idx = static_cast<int>(strtol(entry_elems[1].c_str(), NULL, 10));
            fem_port_map_[port] = MercuryDecoderFemMapEntry(fem_idx, buf_idx);
            buf_idx++;
        }
    }

    // Return the number of valid entries parsed
    return fem_port_map_.size();
}

