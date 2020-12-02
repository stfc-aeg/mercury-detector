/*
 * MercuryProcessorPlugin.h
 *
 *  Created on: 23 Sep 2020
 *      Author: ckd27546
 */

#ifndef TOOLS_FILEWRITER_MercuryProcessorPlugin_H_
#define TOOLS_FILEWRITER_MercuryProcessorPlugin_H_

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
using namespace log4cxx;
using namespace log4cxx::helpers;


#include "FrameProcessorPlugin.h"
#include "MercuryDefinitions.h"
#include "ClassLoader.h"
#include <boost/algorithm/string.hpp>
#include <map>

#include "version.h"

namespace FrameProcessor
{
  /** Abstract plugin class, providing common components to all Mercury plugins.
   *
   * All OdinData Mercury plugins must subclass this class. It provides the
   * FrameProcessorPlugin interface to all Mercury plugins. It also provides 
   * methods for configuring plugins and for retrieving status from plugins.
   */
  class MercuryProcessorPlugin: public FrameProcessorPlugin
  {
    public:
      MercuryProcessorPlugin():
        image_width_(Mercury::pixel_columns_per_sensor),
        image_height_(Mercury::pixel_rows_per_sensor),
        image_pixels_(image_width_ * image_height_) {};
      virtual ~MercuryProcessorPlugin(){};

      int get_version_major() {return ODIN_DATA_VERSION_MAJOR;};
      int get_version_minor() {return ODIN_DATA_VERSION_MINOR;};
      int get_version_patch() {return ODIN_DATA_VERSION_PATCH;};
      std::string get_version_short() {return ODIN_DATA_VERSION_STR_SHORT;};
      std::string get_version_long() {return ODIN_DATA_VERSION_STR;};

      virtual void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply) = 0;
      virtual void requestConfiguration(OdinData::IpcMessage& reply) = 0;
      virtual void status(OdinData::IpcMessage& status) = 0;
      virtual bool reset_statistics() = 0;

    protected:
      virtual void process_frame(boost::shared_ptr<Frame> frame) = 0;

      /** Pointer to logger **/
      LoggerPtr logger_;
      /** Image width **/
      int image_width_;
      /** Image height **/
      int image_height_;
      /** Image pixel count **/
      int image_pixels_;
  };

} /* namespace FrameProcessor */

#endif /* TOOLS_FILEWRITER_MercuryProcessorPlugin_H_ */
