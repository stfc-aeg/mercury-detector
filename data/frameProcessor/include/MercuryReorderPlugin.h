/*
 * MercuryReorderPlugin.h
 *
 *  Created on: 14 Oct 2020
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_MERCURYREORDERPLUGIN_H_
#define INCLUDE_MERCURYREORDERPLUGIN_H_

#include "MercuryProcessorPlugin.h"
#include "DataBlockFrame.h"

namespace FrameProcessor
{
  /** Reorder pixels within Mercury Frame objects.
   *
   * The MercuryReorderPlugin class receives a raw data Frame object,
   * reorders the pixels and stores the data as an array of floats.
   */
  class MercuryReorderPlugin : public MercuryProcessorPlugin
  {
    public:
      MercuryReorderPlugin();
      virtual ~MercuryReorderPlugin();

      void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
      void requestConfiguration(OdinData::IpcMessage& reply);
      void status(OdinData::IpcMessage& status);
      bool reset_statistics();

    private:
      /** Configuration constant for clearing out dropped packet counters **/
      static const std::string CONFIG_DROPPED_PACKETS;
      /** Configuration constant for writing raw data (or not) **/
      static const std::string CONFIG_RAW_DATA;
      /** Configuration constant for setting frame number **/
      static const std::string CONFIG_FRAME_NUMBER;

      void process_lost_packets(boost::shared_ptr<Frame>& frame);
      void process_frame(boost::shared_ptr<Frame> frame);
      // Float type array version currently used:
      void reorder_pixels(unsigned short *in, float *out);
      // Convert pixels from unsigned short to float type without reordering
      void convert_pixels_without_reordering(unsigned short *in,
                                            float *out);

      std::size_t reordered_image_size();

      bool write_raw_data_;

      /** Config of sensor(s) **/
      int sensors_config_;
      /** Packet loss counter **/
      int packets_lost_;
      /** Overwrite UDP frame number until firmware fixed to reset
       * it before each acquisition **/
      uint32_t frame_number_;

      int fem_pixels_per_rows_;
      int fem_pixels_per_columns_;
      int fem_total_pixels_;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, MercuryReorderPlugin, "MercuryReorderPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_MERCURYREORDERPLUGIN_H_ */
