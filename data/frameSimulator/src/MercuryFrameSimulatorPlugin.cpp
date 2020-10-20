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


    /** Construct an MercuryFrameSimulatorPlugin
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
        current_subframe_num = -1;
    }

    /** Extracts the frames from the pcap data file buffer
     * \param[in] data - pcap data
     * \param[in] size
     */
    void MercuryFrameSimulatorPlugin::extract_frames(const u_char *data, const int &size) {

    }

    void MercuryFrameSimulatorPlugin::create_frames(const int &num_frames) {
        
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
