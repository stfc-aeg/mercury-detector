/*
 * MercuryTemplatePlugin.h
 *
 *  Created on: 11 Aug 2020
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_MERCURYTEMPLATEPLUGIN_H_
#define INCLUDE_MERCURYTEMPLATEPLUGIN_H_

#include "MercuryProcessorPlugin.h"

namespace FrameProcessor
{
  typedef std::map<int, Mercury::MercurySensorLayoutMapEntry> MercurySensorLayoutMap;

  /** Template for future Mercury Frame objects.
   *
   * This template may be the basis for any future Mercury plugin(s).
   */
  class MercuryTemplatePlugin : public MercuryProcessorPlugin
  {
    public:
      MercuryTemplatePlugin();
      virtual ~MercuryTemplatePlugin();

      void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
      void requestConfiguration(OdinData::IpcMessage& reply);
      void status(OdinData::IpcMessage& status);
      bool reset_statistics(void);

    private:
      /** Configuration constant for Hardware sensors **/
      static const std::string CONFIG_SENSORS_LAYOUT;

      std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
      std::string sensors_layout_str_;
      MercurySensorLayoutMap sensors_layout_;

      void process_frame(boost::shared_ptr<Frame> frame);

      /** Pointer to logger **/
      LoggerPtr logger_;
      /** Image width **/
      int image_width_;
      /** Image height **/
      int image_height_;
      /** Image pixel count **/
      int image_pixels_;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, MercuryTemplatePlugin, "MercuryTemplatePlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_MERCURYTEMPLATEPLUGIN_H_ */
