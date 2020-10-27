/*
 * MercuryTemplatePlugin.h
 *
 *  Created on: 11 Aug 2020
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_MERCURYTEMPLATEPLUGIN_H_
#define INCLUDE_MERCURYTEMPLATEPLUGIN_H_

#include "MercuryProcessorPlugin.h"

namespace FrameProcessor
{
  /** Template for future Mercury Frame objects.
   *
   * This template may be the basis for any future Mercury plugin(s).
   */
  class MercuryTemplatePlugin : public MercuryProcessorPlugin
  {
    public:
      MercuryTemplatePlugin();
      virtual ~MercuryTemplatePlugin();

      void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
      void requestConfiguration(OdinData::IpcMessage& reply);
      void status(OdinData::IpcMessage& status);
      bool reset_statistics(void);

    private:
      void process_frame(boost::shared_ptr<Frame> frame);
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, MercuryTemplatePlugin, "MercuryTemplatePlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_MERCURYTEMPLATEPLUGIN_H_ */
