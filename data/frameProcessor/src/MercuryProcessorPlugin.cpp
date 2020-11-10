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
  /**
   * The constructor sets up logging used within the class.
   */

  MercuryProcessorPlugin::MercuryProcessorPlugin() :
      image_width_(Mercury::pixel_columns_per_sensor),
      image_height_(Mercury::pixel_rows_per_sensor),
      image_pixels_(image_width_ * image_height_)
  {

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

  // /**
  //  * Reset process plugin statistics
  //  */
  // bool MercuryProcessorPlugin::reset_statistics(void)
  // {
  //   return true;
  // }

}