#ifndef FRAMESIMULATOR_MERCURYFRAMESIMULATORPLUGIN_H
#define FRAMESIMULATOR_MERCURYFRAMESIMULATORPLUGIN_H

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
using namespace log4cxx;
using namespace log4cxx::helpers;

#include <boost/shared_ptr.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <boost/foreach.hpp>
#include <map>
#include <string>
#include <stdexcept>

#include "ClassLoader.h"
#include "FrameSimulatorPluginUDP.h"


namespace FrameSimulator {

    /** MercuryFrameSimulatorPlugin
     *
     *  'extract_frames' is called on setup: this takes the content of the pcap file and reproduces the
     *  Mercury frames to store
     *  'replay_frames' is called by simulate: this then replays the stored frames
     *  'create_frames' is called on setup if no pcap file is specified. It creates frames based on a
     *  frame pattern config provided
     */
    class MercuryFrameSimulatorPlugin : public FrameSimulatorPluginUDP {

    public:

        MercuryFrameSimulatorPlugin();

        virtual void populate_options(po::options_description& config);
        virtual bool setup(const po::variables_map& vm);

        virtual int get_version_major();
        virtual int get_version_minor();
        virtual int get_version_patch();
        virtual std::string get_version_short();
        virtual std::string get_version_long();

    protected:

        virtual void extract_frames(const u_char* data, const int& size);
        virtual void create_frames(const int &num_frames);

    private:

        /** Pointer to logger **/
        LoggerPtr logger_;

        int total_packets;
        int total_bytes;

        int current_frame_num;
        uint16_t* pixel_data_;
        int num_pixels_;

        std::string image_pattern_json_path_;

    };

    REGISTER(FrameSimulatorPlugin, MercuryFrameSimulatorPlugin, "MercuryFrameSimulatorPlugin");
}

#endif //FRAMESIMULATOR_MERCURYFRAMESIMULATORPLUGIN_H
