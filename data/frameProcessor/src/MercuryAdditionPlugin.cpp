/*
 * MercuryAdditionPlugin.cpp
 *
 *  Created on: 15 Oct 2020
 *      Author: Christian Angelsen
 */

#include <MercuryAdditionPlugin.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string MercuryAdditionPlugin::CONFIG_PIXEL_GRID_SIZE = "pixel_grid_size";

  /**
   * The constructor sets up logging used within the class.
   */
  MercuryAdditionPlugin::MercuryAdditionPlugin() :
      pixel_grid_size_(3)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.MercuryAdditionPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "MercuryAdditionPlugin version " <<
                            this->get_version_long() << " loaded.");

    directional_distance_ = (int)pixel_grid_size_/2;  // Set to 1 for 3x3: 2 for 5x5 pixel grid
    number_rows_ = image_height_;
    number_columns_ = image_width_;

    sensors_layout_str_ = Mercury::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
  }

  /**
   * Destructor.
   */
  MercuryAdditionPlugin::~MercuryAdditionPlugin()
  {
    LOG4CXX_TRACE(logger_, "MercuryAdditionPlugin destructor.");

  }

  /**
   * Configure the Mercury plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - pixel_grid_size_ 		<=> pixel_grid_size
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void MercuryAdditionPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(MercuryAdditionPlugin::CONFIG_PIXEL_GRID_SIZE))
    {
      pixel_grid_size_ = config.get_param<int>(MercuryAdditionPlugin::CONFIG_PIXEL_GRID_SIZE);
    }

    directional_distance_ = (int)pixel_grid_size_/2;  // Set to 1 for 3x3: 2 for 5x5 pixel grid
  }

  void MercuryAdditionPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + MercuryAdditionPlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
    reply.set_param(base_str + MercuryAdditionPlugin::CONFIG_PIXEL_GRID_SIZE, pixel_grid_size_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void MercuryAdditionPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for MercuryAdditionPlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
    status.set_param(get_name() + "/pixel_grid_size", pixel_grid_size_);
  }

  /**
   * Reset process plugin statistics
   */
  bool MercuryAdditionPlugin::reset_statistics(void)
  {
    // Nowt to reset..?

    return true;
  }

  /**
   * Perform processing on the frame.  The Charged Sharing algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void MercuryAdditionPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Applying CS Addition algorithm.");

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
      static_cast<const char*>(frame->get_data_ptr()));

    // Check datasets name
    FrameMetaData &frame_meta = frame->meta_data();
    const std::string& dataset = frame_meta.get_dataset_name();

    if (dataset.compare(std::string("raw_frames")) == 0)
    {
      LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
            " dataset, frame number: " << frame->get_frame_number());
      this->push(frame);
    }
    else if (dataset.compare(std::string("processed_frames")) == 0)
    {
      try
      {
        // Define pointer to the input image data
        void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));

        // Take Frame object at input_ptr, apply CS Addition algorithm
        prepare_charged_sharing(static_cast<float *>(input_ptr));

        LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
                  " dataset, frame number: " << frame->get_frame_number());
        this->push(frame);
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "MercuryAdditionPlugin failed: " << e.what());
      }
    }
    else
    {
      LOG4CXX_ERROR(logger_, "Unknown dataset encountered: " << dataset);
    }
  }

  /**
   * Prepare frame for charged sharing processing
   *
   * \param[in] input_frame - Pointer to the image data to be processed.
   * \param[in] output_frame - Pointer to the processed image data.
   */
  void MercuryAdditionPlugin::prepare_charged_sharing(float *frame)
  {
    /// extendedFrame contains empty (1-2) pixel(s) on all 4 sides to enable charged
    /// 	sharing algorithm execution
    int sidePadding          = 2 *  directional_distance_;
    int extendedFrameRows    = (number_rows_ + sidePadding);
    int extendedFrameColumns = (number_columns_ + sidePadding);
    int extendedFrameSize    = extendedFrameRows * extendedFrameColumns;

    float *extendedFrame = NULL;
    extendedFrame = (float *) calloc(extendedFrameSize, sizeof(float));

    // Copy frame's each row into extendedFrame leaving (directional_distance_ pixel(s))
    // 	padding on each side
    int startPosn = extendedFrameColumns * directional_distance_ + directional_distance_;
    int endPosn   = extendedFrameSize - (extendedFrameColumns*directional_distance_);
    int increment = extendedFrameColumns;
    float *rowPtr = frame;

    // Copy input_frame to extendedFrame (with frame of 0's surrounding all four sides)
    for (int i = startPosn; i < endPosn; )
    {
      memcpy(&(extendedFrame[i]), rowPtr, number_columns_ * sizeof(float));
      rowPtr = rowPtr + number_columns_;
      i = i + increment;
    }

    //// CS example frame, with directional_distance_ = 1
    ///
    ///      0     1    2    3  ...   79   80   81
    ///     82    83   84   85  ...  161  162  163
    ///    164   165  166  167  ...  243  244  245
    ///     ..    ..  ..   ..         ..   ..   ..
    ///    6642 6643 6644 6645  ... 6721 6722 6723
    ///
    ///   Where frame's first row is 80 pixels from position 83 - 162,
    ///      second row is 165 - 244, etc

    endPosn = extendedFrameSize - (extendedFrameColumns * directional_distance_)
                - directional_distance_;

    process_addition(extendedFrame, extendedFrameRows, startPosn, endPosn);

    /// Copy CS frame (i.e. 82x82) back into original (80x80) frame
    rowPtr = frame;
    for (int i = startPosn; i < endPosn; )
    {
      memcpy(rowPtr, &(extendedFrame[i]), number_columns_ * sizeof(float));
      rowPtr = rowPtr + number_columns_;
      i = i + increment;
    }

    free(extendedFrame);
    extendedFrame = NULL;
  }

  /**
   * Perform charged sharing algorithm
   *
   * \param[in] extended_frame - Pointer to the image data, surrounded by a frame of zeros
   * \param[in] extended_frame_rows - Number of rows of the extended frame
   * \param[in] start_position - The first pixel in the frame
   * \param[in] end_position - The final pixel in the frame
   */
  void MercuryAdditionPlugin::process_addition(float *extended_frame,
      int extended_frame_rows, int start_position, int end_position)
  {
    float *neighbourPixel = NULL, *currentPixel = extended_frame;
    int rowIndexBegin = (-1*directional_distance_);
    int rowIndexEnd   = (directional_distance_+1);
    int colIndexBegin = rowIndexBegin;
    int colIndexEnd   = rowIndexEnd;
    float maxValue;

    for (int i = start_position; i < end_position;  i++)
    {
      if (extended_frame[i] > 0)
      {
        maxValue = extended_frame[i];
        currentPixel = (&(extended_frame[i]));
        for (int row = rowIndexBegin; row < rowIndexEnd; row++)
        {
          for (int column = colIndexBegin; column < colIndexEnd; column++)
          {
            if ((row == 0) && (column == 0)) // Don't compare pixel against itself
              continue;

            neighbourPixel = (currentPixel + (extended_frame_rows*row)  + column);
            if (*neighbourPixel > 0)
            {
              if (*neighbourPixel > maxValue)
              {
                *neighbourPixel += extended_frame[i];
                maxValue = *neighbourPixel;
                extended_frame[i] = 0;
              }
              else
              {
                extended_frame[i] += *neighbourPixel;
                maxValue = extended_frame[i];
                *neighbourPixel = 0;
              }
            }
          }
        }
      }
    }
  }

} /* namespace FrameProcessor */
