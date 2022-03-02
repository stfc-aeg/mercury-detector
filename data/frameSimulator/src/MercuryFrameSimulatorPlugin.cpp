#include <string>

#include "MercuryFrameSimulatorPlugin.h"
#include "FrameSimulatorOptionsMercury.h"
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
        extended_packet_header_ = true;

        if (extended_packet_header_)
            packet_header_size_ = sizeof(Mercury::PacketExtendedHeader);
        else
            packet_header_size_ = sizeof(Mercury::PacketHeader);
    }

    void MercuryFrameSimulatorPlugin::populate_options(po::options_description& config) {
        
        FrameSimulatorPluginUDP::populate_options(config);

        opt_image_pattern_json.add_option_to(config);
    }

    bool MercuryFrameSimulatorPlugin::setup(const po::variables_map& vm) {
        LOG4CXX_DEBUG(logger_, "Setting Up Mercury Frame Simulator Plugin");

        // Extract Optional arguments for this plugin
        boost::optional<std::string> image_pattern_json;

        opt_image_pattern_json.get_val(vm, image_pattern_json);
        if(image_pattern_json) {
            image_pattern_json_path_ = image_pattern_json.get();
        }

        LOG4CXX_DEBUG(logger_, "Using Image Pattern from file: " << image_pattern_json_path_);

        //actually read out the data from the image file
        boost::property_tree::ptree img_tree;
        boost::property_tree::json_parser::read_json(image_pattern_json_path_, img_tree);
        
        num_pixels_ = Mercury::pixel_columns_per_sensor * Mercury::pixel_rows_per_sensor;
        pixel_data_ = new uint16_t[num_pixels_];
        int x = 0;
        BOOST_FOREACH(boost::property_tree::ptree::value_type &row, img_tree.get_child("img"))
        {

            BOOST_FOREACH(boost::property_tree::ptree::value_type &cell, row.second)
            {
                pixel_data_[x] = cell.second.get_value<uint16_t>();
                x++;
            }
        }

        return FrameSimulatorPluginUDP::setup(vm);
    }

    /** Extracts the frames from the pcap data file buffer
     * \param[in] data - pcap data
     * \param[in] size
     */
    void MercuryFrameSimulatorPlugin::extract_frames(const u_char *data, const int &size) {

        LOG4CXX_DEBUG(logger_, "Extracting Frame(s) from packet");
        // Get first 8 or 64 (extended header) bytes, turn into header
        //check header flags
        if (extended_packet_header_)
            extract_extended_header(data);
        else
            extract_normal_header(data);

        // Create new packet, copy packet data and push into frame
        boost::shared_ptr<Packet> pkt(new Packet());
        unsigned char *datacp = new unsigned char[size];
        memcpy(datacp, data, size);
        pkt->data = datacp;
        pkt->size = size;
        frames_[frames_.size() - 1].packets.push_back(pkt);

        total_packets++;
    }

    void MercuryFrameSimulatorPlugin::extract_normal_header(const u_char *data) {

        const Mercury::PacketHeader* packet_hdr = reinterpret_cast<const Mercury::PacketHeader*>(data);

        uint32_t frame_number = packet_hdr->frame_number;
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

            // It's a new frame, so we create a new frame and add it to the list
            UDPFrame frame(frame_number);
            frames_.push_back(frame);
            frames_[frames_.size() - 1].SOF_markers.push_back(frame_number);
        }

        if(is_EOF) {
            LOG4CXX_DEBUG(logger_, "EOF Marker for Frame " << frame_number << " at packet "
                << packet_number << " total " << total_packets);

            frames_[frames_.size() - 1].EOF_markers.push_back(frame_number);
        }
    }

    void MercuryFrameSimulatorPlugin::extract_extended_header(const u_char *data) {

        const Mercury::PacketExtendedHeader* packet_hdr = reinterpret_cast<const Mercury::PacketExtendedHeader*>(data);

        uint64_t frame_number = packet_hdr->frame_number;
        uint32_t packet_flags = packet_hdr->packet_flags;
        uint32_t packet_number = packet_hdr->packet_number & Mercury::packet_number_mask;

        bool is_SOF = packet_flags & Mercury::start_of_frame_mask;
        bool is_EOF = packet_flags & Mercury::end_of_frame_mask;

        if(is_SOF) {
            LOG4CXX_DEBUG(logger_, "SOF Marker for Frame " << frame_number << " at packet "
                << packet_number << " total " << total_packets);

            if(packet_number != 0) {
                LOG4CXX_WARN(logger_, "Detected SOF marker on packet !=0");
            }

            // It's new frame, so we create a new frame and add it to the list
            UDPFrame frame(frame_number);
            frames_.push_back(frame);
            frames_[frames_.size() - 1].SOF_markers.push_back(frame_number);
        }

        if(is_EOF) {
            LOG4CXX_DEBUG(logger_, "EOF Marker for Frame " << frame_number << " at packet "
                << packet_number << " total " << total_packets);

            frames_[frames_.size() - 1].EOF_markers.push_back(frame_number);
        }
    }

    /** Creates a number of frames
     *
     * @param num_frames - number of frames to create
     */
    void MercuryFrameSimulatorPlugin::create_frames(const int &num_frames) {
        LOG4CXX_DEBUG(logger_, "Creating Frames");

        //calculate number of pixel image bytes in frame
        std::size_t image_bytes = num_pixels_ * sizeof(uint16_t);

        // Allocate buffer for packet data including header
        u_char* head_packet_data = new u_char[Mercury::primary_packet_size + packet_header_size_];
        u_char* tail_packet_data = new u_char[Mercury::tail_packet_size + packet_header_size_];
        
        // Loop over specified number of frames to generate packet and frame data
        for (int frame = 0; frame < num_frames; frame++) {
            
            u_char* data_ptr = reinterpret_cast<u_char*>(pixel_data_);

            uint32_t packet_number = 0;
            uint32_t packet_flags = 0;

            // Setup Head Packet Header
            if (extended_packet_header_)
            {
                Mercury::PacketExtendedHeader* head_packet_header = 
                    reinterpret_cast<Mercury::PacketExtendedHeader*>(head_packet_data);
                packet_flags = 0;
                // Add SoF if this is the first packet of the frame
                if (packet_number == 0)
                    packet_flags = packet_flags | Mercury::start_of_frame_mask;
                
                head_packet_header->frame_number = frame;
                head_packet_header->packet_number = packet_number;
                head_packet_header->packet_flags = packet_flags;
            }
            else
            {
                Mercury::PacketHeader* head_packet_header = 
                    reinterpret_cast<Mercury::PacketHeader*>(head_packet_data);
                packet_flags = (packet_number & Mercury::packet_number_mask);
                // Add SoF if this is the first packet of the frame
                if (packet_number == 0)
                    packet_flags = packet_flags | Mercury::start_of_frame_mask;

                head_packet_header->frame_number = frame;
                head_packet_header->packet_number_flags = packet_flags;
            }

            // Copy data into Head Packet
            memcpy((head_packet_data + packet_header_size_), data_ptr, Mercury::primary_packet_size);

            // Pass head packet to Frame Extraction
            this->extract_frames(head_packet_data, Mercury::primary_packet_size + packet_header_size_);

            // Increment packet number and data_ptr for the tail header
            packet_number = 1;
            data_ptr += Mercury::primary_packet_size;

            // Repeat for the Tail Packet Header and Data
            if (extended_packet_header_)
            {
                Mercury::PacketExtendedHeader* tail_packet_header = 
                    reinterpret_cast<Mercury::PacketExtendedHeader*>(tail_packet_data);
                packet_flags = Mercury::end_of_frame_mask;
                tail_packet_header->frame_number = frame;
                tail_packet_header->packet_number = packet_number;
                tail_packet_header->packet_flags = packet_flags;
            }
            else
            {
                Mercury::PacketHeader* tail_packet_header = 
                    reinterpret_cast<Mercury::PacketHeader*>(tail_packet_data);
                packet_flags =
                    (packet_number & Mercury::packet_number_mask) | Mercury::end_of_frame_mask;
                tail_packet_header->frame_number = frame;
                tail_packet_header->packet_number_flags = packet_flags;
            }

            // Copy data into Head Packet
            memcpy((tail_packet_data + packet_header_size_), data_ptr, Mercury::tail_packet_size);

            // Pass head packet to Frame Extraction
            this->extract_frames(tail_packet_data, Mercury::tail_packet_size + packet_header_size_);
        }

        delete [] head_packet_data;
        delete [] tail_packet_data;
        delete [] pixel_data_;
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
