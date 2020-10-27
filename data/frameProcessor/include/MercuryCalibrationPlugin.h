/*
 * MercuryCalibrationPlugin.h
 *
 *  Created on: 15 Oct 2020
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_MERCURYCALIBRATIONPLUGIN_H_
#define INCLUDE_MERCURYCALIBRATIONPLUGIN_H_

#include "MercuryProcessorPlugin.h"
#include <fstream>

namespace FrameProcessor
{
  /** Calibration of Mercury Frame objects.
   *
   * This plugin takes a gradients and an intercepts file and calibrates each pixel.
   */
  class MercuryCalibrationPlugin : public MercuryProcessorPlugin
  {
    public:
      MercuryCalibrationPlugin();
      virtual ~MercuryCalibrationPlugin();

      void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
      void requestConfiguration(OdinData::IpcMessage& reply);
      void status(OdinData::IpcMessage& status);
      bool reset_statistics(void);

    private:
      /** Configuration constant for Gradients **/
      static const std::string CONFIG_GRADIENTS_FILE;
      /** Configuration constant for Intercepts **/
      static const std::string CONFIG_INTERCEPTS_FILE;

      void process_frame(boost::shared_ptr<Frame> frame);
      void calibrate_pixels(float *image);

      bool gradients_status_;
      bool intercepts_status_;
      float *gradient_values_;
      float *intercept_values_;
      void setGradients(const char *gradientFilename);
      void setIntercepts(const char *interceptFilename);
      bool getData(const char *filename, float *dataValue, float defaultValue);

      std::string gradients_filename_;
      std::string intercepts_filename_;

      void reset_calibration_values();
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, MercuryCalibrationPlugin, "MercuryCalibrationPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_MERCURYCALIBRATIONPLUGIN_H_ */
