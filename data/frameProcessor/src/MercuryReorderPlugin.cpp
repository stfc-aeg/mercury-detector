/*
 * MercuryReorderPlugin.cpp
 *
 *  Created on: 14 Oct 2020
 *      Author: Christian Angelsen
 */

#include <MercuryReorderPlugin.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string MercuryReorderPlugin::CONFIG_DROPPED_PACKETS  = "packets_lost";
  const std::string MercuryReorderPlugin::CONFIG_RAW_DATA         = "raw_data";
  const std::string MercuryReorderPlugin::CONFIG_FRAME_NUMBER     = "frame_number";

  /**
   * The constructor sets up logging used within the class.
   */
  MercuryReorderPlugin::MercuryReorderPlugin() :
  		sensors_config_(Mercury::sensorConfigTwo),
      packets_lost_(0),
      frame_number_(0),
      write_raw_data_(true)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.MercuryReorderPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "MercuryReorderPlugin version " <<
                  this->get_version_long() << " loaded.");

    sensors_layout_str_ = Mercury::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
  }

  /**
   * Destructor.
   */
  MercuryReorderPlugin::~MercuryReorderPlugin()
  {
    LOG4CXX_TRACE(logger_, "MercuryReorderPlugin destructor.");
  }

  /**
   * Configure the Mercury plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage. This
   * plugin supports the following configuration parameters:
   * 
   * - sensors_layout_str_  <=> sensors_layout
   * - write_raw_data_      <=> raw_data
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void MercuryReorderPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(MercuryReorderPlugin::CONFIG_DROPPED_PACKETS))
    {
      packets_lost_ = config.get_param<int>(MercuryReorderPlugin::CONFIG_DROPPED_PACKETS);
    }

    if (config.has_param(MercuryReorderPlugin::CONFIG_RAW_DATA))
    {
      write_raw_data_ = config.get_param<bool>(MercuryReorderPlugin::CONFIG_RAW_DATA);
    }

    if (config.has_param(MercuryReorderPlugin::CONFIG_FRAME_NUMBER))
    {
      frame_number_ = config.get_param<int>(MercuryReorderPlugin::CONFIG_FRAME_NUMBER);
      LOG4CXX_DEBUG(logger_, " *** RESET frame_number to be " << frame_number_);
    }
  }

  void MercuryReorderPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
  	// Return the configuration of the reorder plugin
  	std::string base_str = get_name() + "/";
    reply.set_param(base_str + MercuryReorderPlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
    reply.set_param(base_str + MercuryReorderPlugin::CONFIG_DROPPED_PACKETS, packets_lost_);
    reply.set_param(base_str + MercuryReorderPlugin::CONFIG_RAW_DATA, write_raw_data_);
    reply.set_param(base_str + MercuryReorderPlugin::CONFIG_FRAME_NUMBER, frame_number_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void MercuryReorderPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for MercuryReorderPlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
    status.set_param(get_name() + "/packets_lost", packets_lost_);
    status.set_param(get_name() + "/raw_data", write_raw_data_);
    status.set_param(get_name() + "/frame_number", frame_number_);
  }

  /**
   * Reset process plugin statistics, i.e. counter of packets lost
   */
  bool MercuryReorderPlugin::reset_statistics()
  {
    LOG4CXX_DEBUG(logger_, "Statistics reset requested for Reorder plugin")

    // Reset packets lost counter
    packets_lost_ = 0;
  }

  /**
   * Process and report lost UDP packets for the frame
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void MercuryReorderPlugin::process_lost_packets(boost::shared_ptr<Frame>& frame)
  {
    const Mercury::FrameHeader* hdr_ptr = static_cast<const Mercury::FrameHeader*>(frame->get_data_ptr());
    Mercury::SensorConfigNumber sensors_config = static_cast<Mercury::SensorConfigNumber>(sensors_config_);
    if (hdr_ptr->total_packets_received < Mercury::num_fem_frame_packets(sensors_config)){
      int packets_lost = Mercury::num_fem_frame_packets(sensors_config) - hdr_ptr->total_packets_received;
      LOG4CXX_ERROR(logger_, "Frame number " << hdr_ptr->frame_number << " has dropped " << packets_lost << " packet(s)");
      packets_lost_ += packets_lost;
      LOG4CXX_ERROR(logger_, "Total packets lost since startup " << packets_lost_);
    }
  }

  /**
   * Perform processing on the frame.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void MercuryReorderPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Reordering frame.");
    LOG4CXX_TRACE(logger_, "Frame size: " << frame->get_data_size());

    Mercury::FrameHeader* hdr_ptr = static_cast<Mercury::FrameHeader*>(frame->get_data_ptr());

    this->process_lost_packets(frame);

    //TODO: Interrim fix: (until F/W amended)
    //	Changes header's frame number.
    hdr_ptr->frame_number = frame_number_;
    // Change frame's frame number otherwise FP's will erroneously
    //	display actual Hardware frame number
    frame->set_frame_number(frame_number_);

    LOG4CXX_TRACE(logger_, "Raw frame number: " << hdr_ptr->frame_number);

    // Determine the size of the output reordered image
    const std::size_t output_image_size = reordered_image_size();
    LOG4CXX_TRACE(logger_, "Output image size: " << output_image_size);

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
      static_cast<const char*>(frame->get_data_ptr()) + sizeof(Mercury::FrameHeader)
    );

    // Define pointer to the input image data
    void* input_ptr = static_cast<void *>(
        static_cast<char *>(const_cast<void *>(data_ptr)));

    try
    {
      FrameMetaData frame_meta;

      // Frame meta data common to both datasets
      dimensions_t dims(2);
      dims[0] = image_height_;
      dims[1] = image_width_;
      frame_meta.set_dimensions(dims);
      frame_meta.set_compression_type(no_compression);
      frame_meta.set_data_type(raw_float);
      frame_meta.set_frame_number(hdr_ptr->frame_number);

      // For processed_frames dataset, reuse existing meta data as only the dataset name will differ

      // Set the dataset name
      frame_meta.set_dataset_name("processed_frames");

      boost::shared_ptr<Frame> data_frame;
      data_frame = boost::shared_ptr<Frame>(new DataBlockFrame(frame_meta,
        output_image_size));

      // Get a pointer to the data buffer in the output frame
      void* output_ptr = data_frame->get_data_ptr();

      // Turn unsigned short raw pixel data into float data type
      convert_pixels_without_reordering(static_cast<unsigned short *>(input_ptr),
                                        static_cast<float *>(output_ptr));

      const std::string& dataset = frame_meta.get_dataset_name();
      LOG4CXX_TRACE(logger_, "Pushing " << dataset << " dataset, frame number: " <<
                    data_frame->get_frame_number());
      this->push(data_frame);

      // Only construct raw data frame if configured
      if (write_raw_data_)
      {
        // Set the dataset name
        frame_meta.set_dataset_name("raw_frames");

        boost::shared_ptr<Frame> raw_frame;
        raw_frame = boost::shared_ptr<Frame>(new DataBlockFrame(frame_meta,
                                                                output_image_size));

        // Get a pointer to the data buffer in the output frame
        void* output_ptr = raw_frame->get_data_ptr();

        // Turn unsigned short raw pixel data into float data type
        convert_pixels_without_reordering(static_cast<unsigned short *>(input_ptr),
          static_cast<float *>(output_ptr));

        LOG4CXX_TRACE(logger_, "Pushing raw_frames dataset, frame number: " <<
                      raw_frame->get_frame_number());
        this->push(raw_frame);
      }

      // Manually update frame_number (until fixed in firmware)
      frame_number_++;
    }
    catch (const std::exception& e)
    {
      LOG4CXX_ERROR(logger_, "MercuryReorderPlugin failed: " << e.what());
    }
  }

  /**
   * Determine the size of a reordered image.
   *
   * \return size of the reordered image in bytes
   */
  std::size_t MercuryReorderPlugin::reordered_image_size()
  {
    return image_width_ * image_height_ * sizeof(float);
  }

  /**
   * Convert an image's pixels from unsigned short to float data type, and reorder.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[in] out - Pointer to the allocated memory where the converted image is written.
   *
   */
  void MercuryReorderPlugin::convert_pixels_without_reordering(unsigned short *in, float *out)
  {
    int index = 0;

    for (int i=0; i<image_pixels_; i++)
    {
      // Do not reorder pixels:
      out[i] = (float)in[i];
    }
  }

} /* namespace FrameProcessor */

