/*
 * MercuryTemplatePlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: Christian Angelsen
 */

#include <MercuryTemplatePlugin.h>
#include "version.h"

namespace FrameProcessor
{
  /**
   * The constructor sets up logging used within the class.
   */
  MercuryTemplatePlugin::MercuryTemplatePlugin()
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.MercuryTemplatePlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "MercuryTemplatePlugin version " <<
                  this->get_version_long() << " loaded.");
  }

  /**
   * Destructor.
   */
  MercuryTemplatePlugin::~MercuryTemplatePlugin()
  {
    LOG4CXX_TRACE(logger_, "MercuryTemplatePlugin destructor.");
  }

  /**
   * Configure the Mercury plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - xx_      <=> xx
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void MercuryTemplatePlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {

  }

  void MercuryTemplatePlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void MercuryTemplatePlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for MercuryTemplatePlugin");
  }

  /**
   * Reset process plugin statistics
   */
  bool MercuryTemplatePlugin::reset_statistics(void)
  {
    return true;
  }

  /**
   * Perform processing on the frame.  For a new plugin, amend this
   *  function process data as intended.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void MercuryTemplatePlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Applying ... template algorithm???");

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
    else if (dataset.compare(std::string("data")) == 0)
    {
      try
      {
        // Define pointer to the input image data
        void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));

        ///TODO: This function do not exist; Design it to match requirements
        // some_function(static_cast<float *>(input_ptr));

        LOG4CXX_TRACE(logger_, "Pushing " << dataset << " dataset, frame number: "
                                          << frame->get_frame_number());
        this->push(frame);
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "MercuryTemplatePlugin failed: " << e.what());
      }
    }
    else
    {
      LOG4CXX_ERROR(logger_, "Unknown dataset encountered: " << dataset);
    }
  }

} /* namespace FrameProcessor */
