/*
 * MercuryDiscriminationPlugin.h
 *
 *  Created on: 15 Oct 2020
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_MERCURYDISCRIMINATIONPLUGIN_H_
#define INCLUDE_MERCURYDISCRIMINATIONPLUGIN_H_

#include "MercuryProcessorPlugin.h"
#include "MercuryDefinitions.h"

namespace FrameProcessor
{
  /** Implements Discrimination algorithm on Mercury Frame objects.
   *
   * If any hit pixel have any neighbour(s) with hits, clear all hit pixels.
   */
  class MercuryDiscriminationPlugin : public MercuryProcessorPlugin
  {
    public:
      MercuryDiscriminationPlugin();
      virtual ~MercuryDiscriminationPlugin();

      void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
      void requestConfiguration(OdinData::IpcMessage& reply);
      void status(OdinData::IpcMessage& status);
      bool reset_statistics(void);

    private:
      /** Configuration constant for pixel grid size **/
      static const std::string CONFIG_PIXEL_GRID_SIZE;

      void process_frame(boost::shared_ptr<Frame> frame);

      void prepareChargedSharing(float *inFrame);
      void processDiscrimination(float *extendedFrame, int extendedFrameRows,
                                int startPosn, int endPosn);

      int directional_distance_;
      int number_rows_;
      int number_columns_;
 
      int pixel_grid_size_;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, MercuryDiscriminationPlugin, "MercuryDiscriminationPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_MERCURYDISCRIMINATIONPLUGIN_H_ */
