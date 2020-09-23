/*
 * MercuryProcessorPlugin.cpp
 * 
 *  Created on: 23 Sep 2020
 *      Author: Christian Angelsen
 */

#include <MercuryProcessorPlugin.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string MercuryProcessorPlugin::CONFIG_SENSORS_LAYOUT  = "sensors_layout";

  /**
   * The constructor sets up logging used within the class.
   */

  MercuryProcessorPlugin::MercuryProcessorPlugin() :
      image_width_(Mercury::pixel_columns_per_sensor),
      image_height_(Mercury::pixel_rows_per_sensor),
      image_pixels_(image_width_ * image_height_)
  {
    sensors_layout_str_ = Mercury::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
  }

  /**
   * Destructor.
   */
  MercuryProcessorPlugin::~MercuryProcessorPlugin()
  {
    // Destructor needing to do anything?
    // LOG4CXX_TRACE(logger_, "MercuryProcessorPlugin destructor.");
  }

  int MercuryProcessorPlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int MercuryProcessorPlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int MercuryProcessorPlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string MercuryProcessorPlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string MercuryProcessorPlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

  /**
   * Reset process plugin statistics
   */
  bool MercuryProcessorPlugin::reset_statistics(void)
  {
    return true;
  }

  /**
   * Parse the number of sensors map configuration string.
   * 
   * This method parses a configuration string containing number of sensors mapping information,
   * which is expected to be of the format "NxN" e.g, 2x2. The map's saved in a member variable.
   * 
   * \param[in] sensors_layout_str - string of number of sensors configured
   * \return number of valid map entries parsed from string
   */
  std::size_t MercuryProcessorPlugin::parse_sensors_layout_map(const std::string sensors_layout_str)
  {
    // Clear the current map
    sensors_layout_.clear();

    // Define entry and port:idx delimiters
    const std::string entry_delimiter("x");

    // Vector to hold entries split from map
    std::vector<std::string> map_entries;

    // Split into entries
    boost::split(map_entries, sensors_layout_str, boost::is_any_of(entry_delimiter));

    // If a valid entry is found, save into the map
    if (map_entries.size() == 2) {
      int sensor_rows = static_cast<int>(strtol(map_entries[0].c_str(), NULL, 10));
      int sensor_columns = static_cast<int>(strtol(map_entries[1].c_str(), NULL, 10));
      sensors_layout_[0] = Mercury::MercurySensorLayoutMapEntry(sensor_rows, sensor_columns);
    }

    image_width_ = sensors_layout_[0].sensor_columns_ * Mercury::pixel_columns_per_sensor;
    image_height_ = sensors_layout_[0].sensor_rows_ * Mercury::pixel_rows_per_sensor;
    image_pixels_ = image_width_ * image_height_;

    // Return the number of valid entries parsed
    return sensors_layout_.size();
  }


}