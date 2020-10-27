/*
 * MercuryDiscriminationPlugin.cpp
 *
 *  Created on: 15 Oct 2020
 *      Author: Christian Angelsen
 */

#include <MercuryDiscriminationPlugin.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string MercuryDiscriminationPlugin::CONFIG_PIXEL_GRID_SIZE = "pixel_grid_size";

  /**
   * The constructor sets up logging used within the class.
   */
  MercuryDiscriminationPlugin::MercuryDiscriminationPlugin() :
      pixel_grid_size_(3)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.MercuryDiscriminationPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "MercuryDiscriminationPlugin version " <<
                            this->get_version_long() << " loaded.");

    directional_distance_ = (int)pixel_grid_size_/2;  // Set to 1 for 3x3: 2 for 5x5 pixel grid
    number_rows_ = image_height_;
    number_columns_ = image_width_;
  }

  /**
   * Destructor.
   */
  MercuryDiscriminationPlugin::~MercuryDiscriminationPlugin()
  {
    LOG4CXX_TRACE(logger_, "MercuryDiscriminationPlugin destructor.");
  }

  /**
   * Configure the Mercury plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - pixel_grid_size_     <=> pixel_grid_size
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void MercuryDiscriminationPlugin::configure(OdinData::IpcMessage& config,
                                              OdinData::IpcMessage& reply)
  {
    if (config.has_param(MercuryDiscriminationPlugin::CONFIG_PIXEL_GRID_SIZE))
    {
      pixel_grid_size_ =
          config.get_param<int>(MercuryDiscriminationPlugin::CONFIG_PIXEL_GRID_SIZE);
    }

    // Set to 1 for 3x3: 2 for 5x5 pixel grid
    directional_distance_ = (int)pixel_grid_size_/2;
  }

  void MercuryDiscriminationPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str +
        MercuryDiscriminationPlugin::CONFIG_PIXEL_GRID_SIZE, pixel_grid_size_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status 
   * IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void MercuryDiscriminationPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for MercuryDiscriminationPlugin");
    status.set_param(get_name() + "/pixel_grid_size", pixel_grid_size_);
  }

  /**
   * Reset process plugin statistics
   */
  bool MercuryDiscriminationPlugin::reset_statistics(void)
  {
    // Nowt to reset..?

    return true;
  }

  /**
   * Perform processing on the frame.  The Charged Sharing algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void MercuryDiscriminationPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Applying CS Discrimination algorithm.");

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

        // Take Frame object at input_pointer, apply CS Discrimination algorithm
        prepareChargedSharing(static_cast<float *>(input_ptr));

        LOG4CXX_TRACE(logger_, "Pushing " << dataset << " dataset, frame number: "
                                          << frame->get_frame_number());
        this->push(frame);
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "MercuryDiscriminationPlugin failed: " << e.what());
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
   * \param[in] frame - Pointer to the image data to be processed.
   */
  void MercuryDiscriminationPlugin::prepareChargedSharing(float *frame)
  {
    /// extendedFrame contains empty (1-2) pixel(s) on all 4 sides to enable charge
    ///   sharing algorithm execution
    int sidePadding          = 2 *  directional_distance_;
    int extendedFrameRows    = (number_rows_ + sidePadding);
    int extendedFrameColumns = (number_columns_ + sidePadding);
    int extendedFrameSize    = extendedFrameRows * extendedFrameColumns;

    float  *extendedFrame;
    extendedFrame = (float *) calloc(extendedFrameSize, sizeof(float));

    // Copy frame's each row into extendedFrame leaving (directional_distance_ pixel(s))
    // 	padding on each side
    int startPosn = extendedFrameColumns * directional_distance_ + directional_distance_;
    int endPosn   = extendedFrameSize - (extendedFrameColumns*directional_distance_);
    int increment = extendedFrameColumns;
    float *rowPtr = frame;

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

    processDiscrimination(extendedFrame, extendedFrameRows, startPosn, endPosn);

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
   * \param[in] extendedFrame - Pointer to the image data, surrounded by a frame of zeros
   * \param[in] extendedFrameRows - Number of rows of the extended frame
   * \param[in] startPosn - The first pixel in the frame
   * \param[in] endPosn - The final pixel in the frame
   */
  void MercuryDiscriminationPlugin::processDiscrimination(float *extendedFrame,
                                                    int extendedFrameRows, int startPosn,
                                                    int endPosn)
  {
    float *neighbourPixel = NULL, *currentPixel = extendedFrame;
    int rowIndexBegin = (-1*directional_distance_);
    int rowIndexEnd   = (directional_distance_+1);
    int colIndexBegin = rowIndexBegin;
    int colIndexEnd   = rowIndexEnd;
    bool bWipePixel = false;

    for (int i = startPosn; i < endPosn;  i++)
    {
      if (extendedFrame[i] > 0)
      {
        currentPixel = (&(extendedFrame[i])); // Point at current (non-Zero) pixel

        for (int row = rowIndexBegin; row < rowIndexEnd; row++)
        {
          for (int column = colIndexBegin; column < colIndexEnd; column++)
          {
            if ((row == 0) && (column == 0)) // Don't compare pixel against itself
              continue;

            neighbourPixel = (currentPixel + (extendedFrameRows*row)  + column);

            // Wipe this pixel if another neighbour was non-Zero
            if (bWipePixel)
            {
              *neighbourPixel = 0;
            }
            else
            {
              // Is this the first neighbouring, non-Zero pixel?
              if (*neighbourPixel > 0)
              {
                // Yes; Wipe neighbour and current (non-zero) pixel
                *neighbourPixel = 0;
                *currentPixel = 0;
                bWipePixel = true;
              }
            }
          }
        }
        bWipePixel = false;
      }
    }
  }

} /* namespace FrameProcessor */
