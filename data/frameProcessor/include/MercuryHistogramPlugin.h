/*
 * MercuryHistogramPlugin.h
 *
 *  Created on: 15 Oct 2020
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_MERCURYHISTOGRAMPLUGIN_H_
#define INCLUDE_MERCURYHISTOGRAMPLUGIN_H_

#include "MercuryProcessorPlugin.h"
#include "DataBlockFrame.h"

namespace FrameProcessor
{
  /** Histogram for Mercury Frame objects.
   *
   * The MercuryHistogramPlugin calculates histogram data from all processed frames
   * and periodically writes these histograms to disk.
   */
  class MercuryHistogramPlugin : public MercuryProcessorPlugin
  {
  public:
    MercuryHistogramPlugin();
    virtual ~MercuryHistogramPlugin();

    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void requestConfiguration(OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);
    bool reset_statistics(void);

  private:
    /** Configuration constant for number of frame per acquisition **/
    static const std::string CONFIG_MAX_FRAMES;
    /** Configuration constant for bin start **/
    static const std::string CONFIG_BIN_START;
    /** Configuration constant for bin end **/
    static const std::string CONFIG_BIN_END;
    /** Configuration constant for bin width **/
    static const std::string CONFIG_BIN_WIDTH;
    /** Configuration constant for flush_histograms **/
    static const std::string CONFIG_FLUSH_HISTOS;
    /** Configuration constant for reset_histograms **/
    static const std::string CONFIG_RESET_HISTOS;
    /** Configuration constant for frames processed **/
    static const std::string CONFIG_FRAMES_PROCESSED;
    /** Configuration constant for histograms written **/
    static const std::string CONFIG_HISTOGRAMS_WRITTEN;
    /** Configuration constant for pass processed (dataset) **/
    static const std::string CONFIG_PASS_PROCESSED;

    void process_frame(boost::shared_ptr<Frame> frame);
    void process_end_of_acquisition();

    void add_frame_data_to_histogram_with_sum(float *frame);
    // function copied from MercuryGigE, but not currently in use:
    void addFrameDataToHistogram(float *frame);

    boost::shared_ptr<Frame> spectra_bins_;
    boost::shared_ptr<Frame> summed_spectra_;
    boost::shared_ptr<Frame> pixel_spectra_;

    /** number of frames expected per acquisition **/
    int max_frames_received_;
    /** Count number of frames processed **/
    int frames_processed_;
    /** Flush (remaining data to) histograms **/
    // bool flush_histograms_;
    int flush_histograms_;
    int reset_histograms_;
    int histograms_written_;
    bool pass_processed_;

    int bin_start_;
    int bin_end_;
    double bin_width_;
    long long number_bins_;
    void initialiseHistograms();
    void writeHistogramsToDisk();
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, MercuryHistogramPlugin, "MercuryHistogramPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_MERCURYHISTOGRAMPLUGIN_H_ */
