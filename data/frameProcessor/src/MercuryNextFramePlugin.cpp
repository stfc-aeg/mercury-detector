/*
 * MercuryNextFramePlugin.cpp
 *
 *  Created on: 16 Oct 2020
 *      Author: Christian Angelsen
 */

#include <MercuryNextFramePlugin.h>
#include "version.h"

namespace FrameProcessor
{
  /**
   * The constructor sets up logging used within the class.
   */
  MercuryNextFramePlugin::MercuryNextFramePlugin() :
      last_frame_number_(-1)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.MercuryNextFramePlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "MercuryNextFramePlugin version " <<
                  this->get_version_long() << " loaded.");

    last_frame_ = (float *) calloc(image_pixels_, sizeof(float));
    sensors_layout_str_ = Mercury::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
  }

  /**
   * Destructor.
   */
  MercuryNextFramePlugin::~MercuryNextFramePlugin()
  {
    LOG4CXX_TRACE(logger_, "MercuryNextFramePlugin destructor.");
    free(last_frame_);
    last_frame_ = NULL;
  }

  /**
   * Configure the Mercury plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - sensors_layout_str_  <=> sensors_layout
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void MercuryNextFramePlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(MercuryNextFramePlugin::CONFIG_SENSORS_LAYOUT))
    {
      sensors_layout_str_= config.get_param<std::string>(MercuryNextFramePlugin::CONFIG_SENSORS_LAYOUT);
      parse_sensors_layout_map(sensors_layout_str_);
    }

    // Parsing sensors above may update width, height members
    if (image_pixels_ != image_width_ * image_height_)
    {
      image_pixels_ = image_width_ * image_height_;
      reset_last_frame_values();
    }
  }

  void MercuryNextFramePlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + MercuryNextFramePlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void MercuryNextFramePlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for MercuryNextFramePlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
  }

  /**
   * Reset process plugin statistics
   */
  bool MercuryNextFramePlugin::reset_statistics(void)
  {
    // Nowt to reset..?

    return true;
  }

  /**
   * Perform processing on the frame.  If same pixel hit in current frame as in the previous,
   *  set pixel in current frame to zero.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void MercuryNextFramePlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    long long current_frame_number = frame->get_frame_number();

    LOG4CXX_TRACE(logger_, "Applying Next Frame algorithm.");

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
      static_cast<const char*>(frame->get_data_ptr()));

    // Check datasets name
    FrameMetaData &incoming_frame_meta = frame->meta_data();
    const std::string& dataset = incoming_frame_meta.get_dataset_name();

    if (dataset.compare(std::string("raw_frames")) == 0)
    {
      LOG4CXX_TRACE(logger_, "Pushing " << dataset << " dataset, frame number: "
                                        << current_frame_number);
      this->push(frame);
    }
    else if (dataset.compare(std::string("processed_frames")) == 0)
    {
      try
      {
        // Define pointer to the input image data
        void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));

        // Don't compare current against last frame if not adjacent
        if ((last_frame_number_+1) != current_frame_number)
        {
          LOG4CXX_TRACE(logger_, "Not correcting current frame; last frame number: " <<
                                  last_frame_number_ << " versus current_frame_number: "
                                  << current_frame_number);
        }
        else
        {
          // Compare current frame versus last frame, if same pixel hit in both
          // 	then clear current pixel
          apply_algorithm(static_cast<float *>(input_ptr));
        }

        LOG4CXX_TRACE(logger_, "Pushing " << dataset << " dataset, frame number: "
                                          << current_frame_number);

        last_frame_number_ = current_frame_number;

        // Copy current frame into last frame's place - regardless of any correction taking place,
        //	as we'll always need the current frame to compare against the previous frame
        memcpy(last_frame_, static_cast<float *>(input_ptr), image_pixels_ * sizeof(float));

        this->push(frame);
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "MercuryNextFramePlugin failed: " << e.what());
      }
    }
    else
    {
      LOG4CXX_ERROR(logger_, "Unknown dataset encountered: " << dataset);
    }
  }

  /**
   * Compare current against last frame, zero Pixel in current frame if hit in the last frame.
   * 
   * \param[in] in - Pointer to the incoming image data.
   * \param[in] out - Pointer to the allocated memory for the corrected image.
   * 
   */
  void MercuryNextFramePlugin::apply_algorithm(float *in)
  {
    for (int i=0; i<image_pixels_; i++)
    {
      // If pixel in last frame is nonzero, clear it from current frame
      // 	(whether hit or not), otherwise don't clear pixel frame current frame
      if (last_frame_[i] > 0.0)
      {
        in[i] = 0.0;
      }
    }
  }

  /** Reset array used to store last_frame values.
   * 
   * This method is called when the number of sensors is changed,
   *  to prevent accessing unassigned memory
   */
  void MercuryNextFramePlugin::reset_last_frame_values()
  {
    free(last_frame_);
    last_frame_ = (float *) calloc(image_pixels_, sizeof(float));
  }

} /* namespace FrameProcessor */
