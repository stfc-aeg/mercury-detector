/*
 * MercuryFrameDecoderLib.cpp
 *
 *  Created on: 11 Aug 2020
 *      Author: ckd27546
 */

#include "MercuryFrameDecoder.h"
#include "ClassLoader.h"

namespace FrameReceiver
{
  /**
   * Registration of this decoder through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameDecoder, MercuryFrameDecoder, "MercuryFrameDecoder");

}
// namespace FrameReceiver

