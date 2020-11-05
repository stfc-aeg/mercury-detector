#include <string>

#include "MercuryFrameSimulatorPlugin.h"
#include "MercuryDefinitions.h"

#include <cstdlib>
#include <time.h>
#include <iostream>
#include <algorithm>
#include <boost/lexical_cast.hpp>

#include "version.h"

namespace FrameSimulator {


    /** Construct a MercuryFrameSimulatorPlugin
    * setup an instance of the logger
    * initialises data and frame counts
    */
    MercuryFrameSimulatorPlugin::MercuryFrameSimulatorPlugin() : FrameSimulatorPluginUDP() {
        //Setup logging for the class
        logger_ = Logger::getLogger("FS.MercuryFrameSimulatorPlugin");
        logger_->setLevel(Level::getAll());

        total_packets = 0;
        total_bytes = 0;

        current_frame_num = -1;
    }

    /** Extracts the frames from the pcap data file buffer
     * \param[in] data - pcap data
     * \param[in] size
     */
    void MercuryFrameSimulatorPlugin::extract_frames(const u_char *data, const int &size) {

        LOG4CXX_DEBUG(logger_, "Extracting Frame(s) from packet");
        //get first 8 bytes, turn into header
        //check header flags
        const Mercury::PacketHeader* packet_hdr = reinterpret_cast<const Mercury::PacketHeader*>(data);

        uint32_t frame_number = packet_hdr->frame_counter;
        uint32_t packet_number_flags = packet_hdr->packet_number_flags;

        bool is_SOF = packet_number_flags & Mercury::start_of_frame_mask;
        bool is_EOF = packet_number_flags & Mercury::end_of_frame_mask;
        uint32_t packet_number = packet_number_flags & Mercury::packet_number_mask;

        if(is_SOF) {
            LOG4CXX_DEBUG(logger_, "SOF Marker for Frame " << frame_number << " at packet "
                << packet_number << " total " << total_packets);

            if(packet_number != 0) {
                LOG4CXX_WARN(logger_, "Detected SOF marker on packet !=0");
            }

            //it is new frame, so we create a new frame and add it to the list
            UDPFrame frame(frame_number);
            frames_.push_back(frame);
            frames_[frames_.size() - 1].SOF_markers.push_back(frame_number);
        }

        if(is_EOF) {
            LOG4CXX_DEBUG(logger_, "EOF Marker for Frame " << frame_number << " at packet "
                << packet_number << " total " << total_packets);

            frames_[frames_.size() - 1].EOF_markers.push_back(frame_number);
        }

        //create new packet, copy packet data and push into frame
        boost::shared_ptr<Packet> pkt(new Packet());
        unsigned char *datacp = new unsigned char[size];
        memcpy(datacp, data, size);
        pkt->data = datacp;
        pkt->size = size;
        frames_[frames_.size() - 1].packets.push_back(pkt);

        total_packets++;


    }

    /** Creates a number of frames
     *
     * @param num_frames - number of frames to create
     */
    void MercuryFrameSimulatorPlugin::create_frames(const int &num_frames) {
        LOG4CXX_DEBUG(logger_, "Creating Frames");

        // Build array of pixel data used for each frame
        const int num_pixels = Mercury::pixel_columns_per_sensor * Mercury::pixel_rows_per_sensor;
        uint16_t* pixel_data = new uint16_t[num_pixels];

        for(int pixel = 0; pixel < num_pixels; pixel++) {
            pixel_data[pixel] = static_cast<uint16_t>(pixel & 0xFFFF);
        }

        //calculate number of pixel image bytes in frame
        std::size_t image_bytes = num_pixels * sizeof(uint16_t);

        //allocate buffer for packet data including header
        u_char* head_packet_data = new u_char[Mercury::primary_packet_size + sizeof(Mercury::PacketHeader)];
        u_char* tail_packet_data = new u_char[Mercury::tail_packet_size + sizeof(Mercury::PacketHeader)];
        
        // Loop over specified number of frames to generate packet and frame data
        for (int frame = 0; frame < num_frames; frame++) {
            
            u_char* data_ptr = reinterpret_cast<u_char*>(pixel_data);

            uint32_t packet_number = 0;
            uint32_t packet_flags = 0;

            // Setup Head Packet Header
            Mercury::PacketHeader* head_packet_header = 
                reinterpret_cast<Mercury::PacketHeader*>(head_packet_data);
            packet_flags =
                (packet_number & Mercury::packet_number_mask) | Mercury::start_of_frame_mask;
            
            head_packet_header->frame_counter = frame;
            head_packet_header->packet_number_flags = packet_flags;

            //copy data into Head Packet
            memcpy((head_packet_data + sizeof(Mercury::PacketHeader)), data_ptr, Mercury::primary_packet_size);

            //Pass head packet to Frame Extraction
            this->extract_frames(head_packet_data, Mercury::primary_packet_size + sizeof(Mercury::PacketHeader));

            //change packet number and data_ptr for the tail header
            packet_number = 1;
            data_ptr += Mercury::primary_packet_size;
            //Now the same for the Tail Packet Header and Data
            Mercury::PacketHeader* tail_packet_header = 
                reinterpret_cast<Mercury::PacketHeader*>(tail_packet_data);
            packet_flags =
                (packet_number & Mercury::packet_number_mask) | Mercury::end_of_frame_mask;
            
            tail_packet_header->frame_counter = frame;
            tail_packet_header->packet_number_flags = packet_flags;

            //copy data into Head Packet
            memcpy((tail_packet_data + sizeof(Mercury::PacketHeader)), data_ptr, Mercury::tail_packet_size);

            //Pass head packet to Frame Extraction
            this->extract_frames(tail_packet_data, Mercury::tail_packet_size + sizeof(Mercury::PacketHeader));
        }

        delete [] head_packet_data;
        delete [] tail_packet_data;
        delete [] pixel_data;

    }

   /**
    * Get the plugin major version number.
    *
    * \return major version number as an integer
    */
    int MercuryFrameSimulatorPlugin::get_version_major() {
        return ODIN_DATA_VERSION_MAJOR;
    }

    /**
     * Get the plugin minor version number.
     *
     * \return minor version number as an integer
     */
    int MercuryFrameSimulatorPlugin::get_version_minor() {
        return ODIN_DATA_VERSION_MINOR;
    }

    /**
     * Get the plugin patch version number.
     *
     * \return patch version number as an integer
     */
    int MercuryFrameSimulatorPlugin::get_version_patch() {
        return ODIN_DATA_VERSION_PATCH;
    }

    /**
     * Get the plugin short version (e.g. x.y.z) string.
     *
     * \return short version as a string
     */
    std::string MercuryFrameSimulatorPlugin::get_version_short() {
        return ODIN_DATA_VERSION_STR_SHORT;
    }

    /**
     * Get the plugin long version (e.g. x.y.z-qualifier) string.
     *
     * \return long version as a string
     */
    std::string MercuryFrameSimulatorPlugin::get_version_long() {
        return ODIN_DATA_VERSION_STR;
    }

}
