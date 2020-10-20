/*
 * MercuryThresholdPlugin.cpp
 *
 *  Created on: 16 Oct 2020
 *      Author: Christian Angelsen
 */

#include <MercuryThresholdPlugin.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string MercuryThresholdPlugin::CONFIG_THRESHOLD_MODE  = "threshold_mode";
  const std::string MercuryThresholdPlugin::CONFIG_THRESHOLD_VALUE = "threshold_value";
  const std::string MercuryThresholdPlugin::CONFIG_THRESHOLD_FILE  = "threshold_filename";

  /**
   * The constructor sets up logging used within the class.
   */
  MercuryThresholdPlugin::MercuryThresholdPlugin() :
      threshold_filename_("")
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.MercuryThresholdPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "MercuryThresholdPlugin version " <<
                  this->get_version_long() << " loaded.");

    thresholds_status_    = false;
    threshold_value_      = 0;
    threshold_per_pixel_  = (uint16_t *) calloc(image_pixels_, sizeof(uint16_t));

    /// Set threshold mode to none (initially; 0=none, 1=value ,2=file)
    threshold_mode_ = (ThresholdMode)0;

    sensors_layout_str_ = Mercury::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
  }

  /**
   * Destructor.
   */
  MercuryThresholdPlugin::~MercuryThresholdPlugin()
  {
    LOG4CXX_TRACE(logger_, "MercuryThresholdPlugin destructor.");

    free(threshold_per_pixel_);
    threshold_per_pixel_ = NULL;
  }

  /**
   * Configure the Mercury plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - max_frames_received_ <=> max_frames_received
   * - threshold_mode_      <=> threshold_mode
   * - threshold_value_     <=> threshold_value
   * - threshold_filename_  <=> threshold_file
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void MercuryThresholdPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(MercuryThresholdPlugin::CONFIG_THRESHOLD_MODE))
    {
      std::string threshold_mode = config.get_param<std::string>(
        MercuryThresholdPlugin::CONFIG_THRESHOLD_MODE);

      if (threshold_mode.compare(std::string("none")) == 0)
      {
        threshold_mode_ = (ThresholdMode)0;
        LOG4CXX_TRACE(logger_, "User selected threshold mode: none");
      }
      else if (threshold_mode.compare(std::string("value")) == 0)
      {
        threshold_mode_ = (ThresholdMode)1;
        LOG4CXX_TRACE(logger_, "User selected threshold mode: value");
      }
      else if (threshold_mode.compare(std::string("filename")) == 0)
      {
        threshold_mode_ = (ThresholdMode)2;
        LOG4CXX_TRACE(logger_, "User selected threshold mode: filename");
      }
    }

    if (config.has_param(MercuryThresholdPlugin::CONFIG_THRESHOLD_VALUE))
    {
      threshold_value_ = config.get_param<int>(
        MercuryThresholdPlugin::CONFIG_THRESHOLD_VALUE);
        LOG4CXX_TRACE(logger_, "Setting threshold value to: " << threshold_value_);
    }

    if (config.has_param(MercuryThresholdPlugin::CONFIG_THRESHOLD_FILE))
    {
      threshold_filename_ = config.get_param<std::string>(
        MercuryThresholdPlugin::CONFIG_THRESHOLD_FILE);

      // Update threshold filename if filename mode selected
      if (!threshold_filename_.empty())
      {
        LOG4CXX_TRACE(logger_, "Setting thresholds from file: " << threshold_filename_);
        if (set_threshold_per_pixel(threshold_filename_.c_str()))
        {
          LOG4CXX_TRACE(logger_, "Read thresholds from file successfully");
        }
        else
        {
          LOG4CXX_ERROR(logger_, "Failed to read thresholds from file")
        }
      }
    }
  }

  void MercuryThresholdPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + MercuryThresholdPlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
    int mode = int(threshold_mode_);
    std::string mode_str = determineThresholdMode(mode);
    reply.set_param(base_str + MercuryThresholdPlugin::CONFIG_THRESHOLD_MODE , mode_str);
    reply.set_param(base_str + MercuryThresholdPlugin::CONFIG_THRESHOLD_VALUE, threshold_value_);
    reply.set_param(base_str + MercuryThresholdPlugin::CONFIG_THRESHOLD_FILE , threshold_filename_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void MercuryThresholdPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for MercuryThresholdPlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
    int mode = int(threshold_mode_);
    std::string mode_str = determineThresholdMode(mode);
    status.set_param(get_name() + "/threshold_mode", mode_str);
    status.set_param(get_name() + "/threshold_value", threshold_value_);
    status.set_param(get_name() + "/threshold_filename", threshold_filename_);
  }

  /**
   * Convert threshold mode (enumerated integer) into string
   */
  std::string MercuryThresholdPlugin::determineThresholdMode(int mode)
  {
    std::string mode_str = "";
    switch(mode)
    {
      case 0:
        mode_str = "none";
        break;
      case 1:
        mode_str = "value";
        break;
      case 2:
        mode_str = "filename";
        break;
    }
    return mode_str;
  }

  /**
   * Reset process plugin statistics
   */
  bool MercuryThresholdPlugin::reset_statistics(void)
  {
    // Nowt to reset..?

    return true;
  }

  /**
   * Perform processing on the frame.  Apply selected threshold mode.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void MercuryThresholdPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
      static_cast<const char*>(frame->get_data_ptr()));

    // Check datasets name
    FrameMetaData &incoming_frame_meta = frame->meta_data();
    const std::string& dataset = incoming_frame_meta.get_dataset_name();

    if (dataset.compare(std::string("raw_frames")) == 0)
    {
      LOG4CXX_TRACE(logger_, "Pushing " << dataset << " dataset, frame number: "
                                        << frame->get_frame_number());
      this->push(frame);
    }
    else if (dataset.compare(std::string("processed_frames")) == 0)
    {
      try
      {
        // Define pointer to the input image data
        void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));

        // Execute selected method of applying threshold(s) (none, value, or file)
        switch (threshold_mode_)
        {
          case 0:
            // No threshold processing
            break;
          case 1:
            process_threshold_value(static_cast<float *>(input_ptr));
            LOG4CXX_TRACE(logger_, "Applying threshold value to frame.");
            break;
          case 2:
            process_threshold_file(static_cast<float *>(input_ptr));
            LOG4CXX_TRACE(logger_, "Applying thresholds from file to frame.");
            break;
        }
        LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
                        " dataset, frame number: " << frame->get_frame_number());
        this->push(frame);
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "MercuryThresholdPlugin failed: " << e.what());
      }
    }
    else
    {
      LOG4CXX_ERROR(logger_, "Unknown dataset encountered: " << dataset);
    }
  }

  /**
   * Zero all pixels below threshold_value_.
   *
   * \param[in] in - Pointer to the image data.
   *
   */
  void MercuryThresholdPlugin::process_threshold_value(float *in)
  {
    for (int i=0; i < image_pixels_; i++)
    {
      // Clear pixel if it doesn't meet the threshold:
      if (in[i] < threshold_value_)
      {
        in[i] = 0;
      }
    }
  }

  /**
   * Zero each pixel not meeting its corresponding pixel threshold.
   *
   * \param[in] in - Pointer to the image data.
   *
   */
  void MercuryThresholdPlugin::process_threshold_file(float *in)
  {
    for (int i=0; i < image_pixels_; i++)
    {
      // Clear pixel if it doesn't meet the threshold:
      if (in[i] < threshold_per_pixel_[i])
      {
        in[i] = 0;
      }
    }
  }

  /**
   * Set each pixel threshold from the values by the provided file.
   *
   * \param[in] threshold_filename - the filename containing threshold values.
   *
   * \return bool indicating whether reading file was successful
   */
  bool MercuryThresholdPlugin::set_threshold_per_pixel(const char *threshold_filename)
  {
    uint16_t defaultValue = 0;
    thresholds_status_ = get_data(threshold_filename, defaultValue);

    return thresholds_status_;
  }

  /**
   * Set each pixel threshold from the values by the provided file.
   *
   * \param[in] threshold_filename - the filename containing threshold values.
   * \param[in] default_value - Default value if there's any issues reading the file
   *
   * \return bool indicating whether reading file was successful
   */
  bool MercuryThresholdPlugin::get_data(const char *filename, uint16_t default_value)
  {
    int index = 0, thresholdFromFile = 0;
    bool success = false;

    /// Count number of floats in file:
    std::ifstream file(filename);
    int file_values = std::distance(std::istream_iterator<double>(file),
                                    std::istream_iterator<double>());
    file.close();

    if (image_pixels_ != file_values)
    {
      LOG4CXX_ERROR(logger_, "Expected " << image_pixels_ << " values but read " <<
                    file_values << " values from file: " << filename);

      LOG4CXX_WARN(logger_, "Using default values instead");
      for (int val = 0; val < image_pixels_; val ++)
      {
        threshold_per_pixel_[val] = default_value;
      }
      return success;
    }

    std::ifstream inFile(filename);

    std::string line;
    while(std::getline(inFile, line))
    {
      std::stringstream ss(line);

      while( ss >> thresholdFromFile )
      {
        threshold_per_pixel_[index] = thresholdFromFile;
        index++;
      }
    }

    inFile.close();
    success = true;

    return success;
  }

  /**
   * Reset array used to store threshold values.
   * 
   * This method is called when the number of sensors is changed,
   * to prevent accessing unassigned memory
   */
  void MercuryThresholdPlugin::reset_threshold_values()
  {
    free(threshold_per_pixel_);
    threshold_per_pixel_	= (uint16_t *) calloc(image_pixels_, sizeof(uint16_t));
  }

} /* namespace FrameProcessor */
