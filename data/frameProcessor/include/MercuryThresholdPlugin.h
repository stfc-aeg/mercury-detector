/*
 * MercuryThresholdPlugin.h
 *
 *  Created on: 16 Oct 2020
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_MERCURYTHRESHOLDPLUGIN_H_
#define INCLUDE_MERCURYTHRESHOLDPLUGIN_H_

#include "MercuryProcessorPlugin.h"
#include <fstream>

namespace FrameProcessor
{
  enum ThresholdMode {NONE, SINGLE_VALUE, THRESHOLD_FILE};

  /** Processing of Mercury Frame objects.
   *
   * The MercuryThresholdPlugin class receives Frame objects
   * and reorders the data into valid Mercury frames.
   */
  class MercuryThresholdPlugin : public MercuryProcessorPlugin
  {
    public:
      MercuryThresholdPlugin();
      virtual ~MercuryThresholdPlugin();

      void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
      void requestConfiguration(OdinData::IpcMessage& reply);
      void status(OdinData::IpcMessage& status);
      bool reset_statistics(void);

    private:
      /** Configuration constant for threshold mode **/
      static const std::string CONFIG_THRESHOLD_MODE;
      /** Configuration constant for threshold value **/
      static const std::string CONFIG_THRESHOLD_VALUE;
      /** Configuration constant for threshold file **/
      static const std::string CONFIG_THRESHOLD_FILE;

      void process_frame(boost::shared_ptr<Frame> frame);
      std::size_t thresholded_image_size();

      void process_threshold_value(float *in);
      void process_threshold_file(float *in);
      bool get_data(const char *filename, uint16_t default_value);
      bool set_threshold_per_pixel(const char *threshold_filename);
      std::string determineThresholdMode(int mode);

      void reset_threshold_values();

      // Member variables:
      unsigned int threshold_value_;
      uint16_t *threshold_per_pixel_;
      bool thresholds_status_;
      ThresholdMode threshold_mode_;
      std::string threshold_filename_;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, MercuryThresholdPlugin, "MercuryThresholdPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_MERCURYTHRESHOLDPLUGIN_H_ */
