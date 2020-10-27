/*
 * MercuryNextFramePlugin.h
 *
 *  Created on: 16 Oct 2020
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_MERCURYNEXTFRAMEPLUGIN_H_
#define INCLUDE_MERCURYNEXTFRAMEPLUGIN_H_

#include "MercuryProcessorPlugin.h"

namespace FrameProcessor
{
  /** NextFrame Corrector for future Mercury Frame objects.
   *
   * If the same pixel is hit in previous, current frames, clear pixel in current frame.
   */
  class MercuryNextFramePlugin : public MercuryProcessorPlugin
  {
  public:
    MercuryNextFramePlugin();
    virtual ~MercuryNextFramePlugin();

    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void requestConfiguration(OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);
    bool reset_statistics(void);

  private:
    void process_frame(boost::shared_ptr<Frame> frame);
    void apply_algorithm(float *in);

    /** Keep a copy of previous data frame **/
    float *last_frame_;

    long long last_frame_number_;
    void reset_last_frame_values();
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, MercuryNextFramePlugin, "MercuryNextFramePlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_MERCURYNEXTFRAMEPLUGIN_H_ */
