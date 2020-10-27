/*
 * MercuryHistogramPlugin.cpp
 *
 *  Created on: 15 Oct 2020
 *      Author: Christian Angelsen
 */

#include <MercuryHistogramPlugin.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string MercuryHistogramPlugin::CONFIG_MAX_FRAMES         = "max_frames_received";
  const std::string MercuryHistogramPlugin::CONFIG_BIN_START          = "bin_start";
  const std::string MercuryHistogramPlugin::CONFIG_BIN_END            = "bin_end";
  const std::string MercuryHistogramPlugin::CONFIG_BIN_WIDTH          = "bin_width";
  const std::string MercuryHistogramPlugin::CONFIG_FLUSH_HISTOS       = "flush_histograms";
  const std::string MercuryHistogramPlugin::CONFIG_RESET_HISTOS       = "reset_histograms";
  const std::string MercuryHistogramPlugin::CONFIG_FRAMES_PROCESSED   = "frames_processed";
  const std::string MercuryHistogramPlugin::CONFIG_HISTOGRAMS_WRITTEN = "histograms written";
  const std::string MercuryHistogramPlugin::CONFIG_PASS_PROCESSED     = "pass_processed";

  /**
   * The constructor sets up logging used within the class.
   */
  MercuryHistogramPlugin::MercuryHistogramPlugin() :
      max_frames_received_(0),
      flush_histograms_(0),
      histograms_written_(0),
      frames_processed_(0),
      pass_processed_(true)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.MercuryHistogramPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "MercuryHistogramPlugin version " <<
                  this->get_version_long() << " loaded.");

    bin_start_   = 0;
    bin_end_     = 8000;
    bin_width_   = 10;
    number_bins_ = (int)(((bin_end_ - bin_start_) / bin_width_) + 0.5);

    initialiseHistograms();
  }

  /**
   * Destructor.
   */
  MercuryHistogramPlugin::~MercuryHistogramPlugin()
  {
    LOG4CXX_TRACE(logger_, "MercuryHistogramPlugin destructor.");
  }

  /**
   * Allocate and initialise histograms
   *
   */
  void MercuryHistogramPlugin::initialiseHistograms()
  {
    // Setup the dimension(s) for spectra_bins, summed_spectra
    dimensions_t dims(1);
    dims[0] = number_bins_;

    // Setup the spectra bins

    FrameMetaData spectra_meta;

    spectra_meta.set_dimensions(dims);
    spectra_meta.set_compression_type(no_compression);
    spectra_meta.set_data_type(raw_float);
    spectra_meta.set_frame_number(0);
    spectra_meta.set_dataset_name("spectra_bins");

    spectra_bins_ = boost::shared_ptr<Frame>(new DataBlockFrame(spectra_meta, number_bins_ * sizeof(float)));

    // Setup the summed spectra

    FrameMetaData summed_meta;

    summed_meta.set_dimensions(dims);
    summed_meta.set_compression_type(no_compression);
    summed_meta.set_data_type(raw_64bit);
    summed_meta.set_frame_number(0);
    summed_meta.set_dataset_name("summed_spectra");

    summed_spectra_ = boost::shared_ptr<Frame>(new DataBlockFrame(summed_meta, number_bins_ * sizeof(uint64_t)));

    // Setup the pixel spectra

    // Setup the dimensions pixel_spectra
    dimensions_t pixel_dims(2);
    pixel_dims[0] = image_pixels_;
    pixel_dims[1] = number_bins_;

    FrameMetaData pixel_meta;

    pixel_meta.set_dimensions(pixel_dims);
    pixel_meta.set_compression_type(no_compression);
    pixel_meta.set_data_type(raw_float);
    pixel_meta.set_frame_number(0);
    pixel_meta.set_dataset_name("pixel_spectra");

    pixel_spectra_ = boost::shared_ptr<Frame>(new DataBlockFrame(pixel_meta, image_pixels_ * number_bins_ * sizeof(float)));

    // Initialise bins
    float currentBin = bin_start_;
    float *pHxtBin = static_cast<float *>(spectra_bins_->get_data_ptr());	// New implementation
    for (long i = bin_start_; i < number_bins_; i++, currentBin += bin_width_)
    {
      *pHxtBin = currentBin;
      pHxtBin++;
    }

    // Clear histogram values
    float *pixels = static_cast<float *>(pixel_spectra_->get_data_ptr());
    float *summed = static_cast<float *>(summed_spectra_->get_data_ptr());
    memset(pixels, 0, (number_bins_ * image_pixels_) * sizeof(float));
    memset(summed, 0, number_bins_ * sizeof(uint64_t));
  }

  /**
   * Configure the Mercury plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - max_frames_received_ <=> max_frames_received
   * - bin_start_           <=> bin_start
   * - bin_end_             <=> bin_end
   * - bin_width_           <=> bin_width
   * - flush_histograms_    <=> flush_histograms
   * - reset_histograms_    <=> reset_histograms
   * - pass_processed_      <=> pass_processed
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void MercuryHistogramPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(MercuryHistogramPlugin::CONFIG_MAX_FRAMES))
    {
      max_frames_received_ = config.get_param<int>(MercuryHistogramPlugin::CONFIG_MAX_FRAMES);
    }

    if (config.has_param(MercuryHistogramPlugin::CONFIG_BIN_START))
    {
      bin_start_ = config.get_param<int>(MercuryHistogramPlugin::CONFIG_BIN_START);
    }

    if (config.has_param(MercuryHistogramPlugin::CONFIG_BIN_END))
    {
      bin_end_ = config.get_param<long>(MercuryHistogramPlugin::CONFIG_BIN_END);
    }

    if (config.has_param(MercuryHistogramPlugin::CONFIG_BIN_WIDTH))
    {
      bin_width_ = config.get_param<double>(MercuryHistogramPlugin::CONFIG_BIN_WIDTH);
    }

    number_bins_  = (int)(((bin_end_ - bin_start_) / bin_width_) + 0.5);

    if (config.has_param(MercuryHistogramPlugin::CONFIG_RESET_HISTOS))
    {
      reset_histograms_ = config.get_param<int>(MercuryHistogramPlugin::CONFIG_RESET_HISTOS);

      if (reset_histograms_ == 1)
      {
        frames_processed_ = 0;
        reset_histograms_ = 0;
      }      
    }

    if (config.has_param(MercuryHistogramPlugin::CONFIG_FLUSH_HISTOS))
    {
      flush_histograms_ = config.get_param<int>(MercuryHistogramPlugin::CONFIG_FLUSH_HISTOS);

      if (flush_histograms_ == 1)
      {
        /// Time to push current histogram data
        writeHistogramsToDisk();

        frames_processed_ = 0;

        // Clear flush_histograms_
        flush_histograms_ = 0;
      }
    }

    if (config.has_param(MercuryHistogramPlugin::CONFIG_PASS_PROCESSED))
    {
      pass_processed_ = config.get_param<bool>(MercuryHistogramPlugin::CONFIG_PASS_PROCESSED);
    }

    // (Re-)Initialise memory
    initialiseHistograms();
  }

  void MercuryHistogramPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the histogram plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + MercuryHistogramPlugin::CONFIG_MAX_FRAMES , max_frames_received_);
    reply.set_param(base_str + MercuryHistogramPlugin::CONFIG_BIN_START, bin_start_);
    reply.set_param(base_str + MercuryHistogramPlugin::CONFIG_BIN_END , bin_end_);
    reply.set_param(base_str + MercuryHistogramPlugin::CONFIG_BIN_WIDTH, bin_width_);
    reply.set_param(base_str + MercuryHistogramPlugin::CONFIG_FLUSH_HISTOS, flush_histograms_);
    reply.set_param(base_str + MercuryHistogramPlugin::CONFIG_FRAMES_PROCESSED, frames_processed_);
    reply.set_param(base_str + MercuryHistogramPlugin::CONFIG_HISTOGRAMS_WRITTEN, histograms_written_);
    reply.set_param(base_str + MercuryHistogramPlugin::CONFIG_PASS_PROCESSED, pass_processed_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void MercuryHistogramPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for MercuryHistogramPlugin");
    status.set_param(get_name() + "/max_frames_received", max_frames_received_);
    status.set_param(get_name() + "/bin_start", bin_start_);
    status.set_param(get_name() + "/bin_end", bin_end_);
    status.set_param(get_name() + "/bin_width", bin_width_);
    status.set_param(get_name() + "/flush_histograms", flush_histograms_);
    status.set_param(get_name() + "/frames_processed", frames_processed_);
    status.set_param(get_name() + "/histograms_written", histograms_written_);
    status.set_param(get_name() + "/pass_processed", pass_processed_);
  }

  /**
   * Reset process plugin statistics, i.e. counter of packets lost
   */
  bool MercuryHistogramPlugin::reset_statistics(void)
  {
  	// Nothing to reset??

    return true;
  }

  /**
   * Perform processing on the frame.  Calculate histograms based upon
   * each frame, writing resulting datasets to file when configured
   * maximum number of frames received.
   * 
   * \param[in] frame - Pointer to a Frame object.
   */
  void MercuryHistogramPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
      static_cast<const char*>(frame->get_data_ptr()));

    // Check dataset's name
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

        // Add this frame's contribution onto histograms
        add_frame_data_to_histogram_with_sum(static_cast<float *>(input_ptr));

        // Write histograms to disc when maximum number of frames received
        if ( ((frames_processed_+1) % max_frames_received_) == 0) 
        {
          /// Time to push current histogram data to file
          writeHistogramsToDisk();
          histograms_written_ = frames_processed_;
        }

        /// Histogram will access processed_frames dataset but not change it
        /// Therefore do not need to check frame dimensions, etc

        if (pass_processed_)
        {
          // Pass on processed_frames dataset unmodified:
          LOG4CXX_TRACE(logger_, "Pushing " << dataset << " dataset, frame number: "
                                            << frame->get_frame_number());
          this->push(frame);
        }

        frames_processed_++;
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "MercuryHistogramPlugin failed: " << e.what());
      }
    }
    else
    {
      LOG4CXX_ERROR(logger_, "Unknown dataset encountered: " << dataset);
    }
  }

  /**
   * Write Histogram data to disk.
   */
  void MercuryHistogramPlugin::writeHistogramsToDisk()
  {
    LOG4CXX_TRACE(logger_, "Pushing " << spectra_bins_->get_meta_data().get_dataset_name() << " dataset");
    this->push(spectra_bins_);

    LOG4CXX_TRACE(logger_, "Pushing " << summed_spectra_->get_meta_data().get_dataset_name() << " dataset");
    this->push(summed_spectra_);

    LOG4CXX_TRACE(logger_, "Pushing " << pixel_spectra_->get_meta_data().get_dataset_name() << " dataset");
    this->push(pixel_spectra_);
  }

  /**
   * Perform processing on the frame.  Calculate histograms based upon
   * each frame.
   * 
   * \param[frame] frame - Pointer to a frame object.
   */
  void MercuryHistogramPlugin::add_frame_data_to_histogram_with_sum(float *frame)
  {
    const void* pixel_ptr = static_cast<const void*>(
      static_cast<const char*>(pixel_spectra_->get_data_ptr()));
    void* pixel_input_ptr = static_cast<void *>(
      static_cast<char *>(const_cast<void *>(pixel_ptr)));

    const void* summed_ptr = static_cast<const void*>(
      static_cast<const char*>(summed_spectra_->get_data_ptr()));
    void* summed_input_ptr = static_cast<void *>(
      static_cast<char *>(const_cast<void *>(summed_ptr)));

    float *currentHistogram = static_cast<float *>(pixel_input_ptr);
    uint64_t *summed = static_cast<uint64_t *>(summed_input_ptr);

    float thisEnergy;
    int bin;
    int pixel;
    for (int i = 0; i < image_pixels_; i++)
    {
      pixel = i;
      thisEnergy = frame[i];

      if (thisEnergy <= 0.0)
        continue;
      bin = (int)((thisEnergy / bin_width_));
      if (bin <= number_bins_)
      {
        (*(currentHistogram + (pixel * number_bins_) + bin))++;
        (*(summed + bin)) ++;
      }
    }
  }

  // Called when the user NOT selected spectrum option
  void MercuryHistogramPlugin::addFrameDataToHistogram(float *frame)
  {
    float *currentHistogram = static_cast<float *>(pixel_spectra_->get_data_ptr());
    float thisEnergy;
    int bin;
    int pixel;

    for (int i = 0; i < image_pixels_; i++)
    {
      pixel = i;
      thisEnergy = frame[i];
      if (thisEnergy == 0)
        continue;
      bin = (int)((thisEnergy / bin_width_));
      if (bin <= number_bins_)
      {
        (*(currentHistogram + (pixel * number_bins_) + bin))++;
      }
    }
  }

} /* namespace FrameProcessor */
