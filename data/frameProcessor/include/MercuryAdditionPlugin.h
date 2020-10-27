/*
 * MercuryAdditionPlugin.h
 *
 *  Created on: 15 Oct 2020
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_MERCURYADDITIONPLUGIN_H_
#define INCLUDE_MERCURYADDITIONPLUGIN_H_

#include "MercuryProcessorPlugin.h"

namespace FrameProcessor
{
  /** Applies the Charged Sharing algorithm to a Mercury frame.
   *
   * The MercuryAdditionPlugin examines surrounding neighbouring pixels
   * moving any event shared across multiple pixels onto the pixel containing
   * the biggest portion of that event.
   */
  class MercuryAdditionPlugin : public MercuryProcessorPlugin
  {
    public:
      MercuryAdditionPlugin();
      virtual ~MercuryAdditionPlugin();

      void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
      void requestConfiguration(OdinData::IpcMessage& reply);
      void status(OdinData::IpcMessage& status);
      bool reset_statistics(void);

    private:
      /** Configuration constant for pixel_grid_size **/
      static const std::string CONFIG_PIXEL_GRID_SIZE;

      void process_frame(boost::shared_ptr<Frame> frame);

      void prepare_charged_sharing(float *input_frame);
      void process_addition(float *extended_frame, int extended_frame_rows,
                            int start_position, int end_position);

      int directional_distance_;
      int number_rows_;
      int number_columns_;

      /** Pixel grid size */
      int pixel_grid_size_;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, MercuryAdditionPlugin, "MercuryAdditionPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_MERCURYADDITIONPLUGIN_H_ */
