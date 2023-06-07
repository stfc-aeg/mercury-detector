import time
import numpy as np

requires = [
        'serialiser_tests',
        'diamond202212_support',
        '_8_fastdata_support',
        '_9_gpib_support',
        'utility',
        'asic_spi',
        ]


provides = ['voltage_scan_tdc_slope_TDCinjection','voltage_scan_tdc_slope_Preampinjection',
        ]


def voltage_scan_tdc_slope_TDCinjection(vcal_min=0,vcal_max=1.5,vcal_step=0.02,folder='Test_pulse_TDC_ramp_TDCInjection',nframes=100000):

        asic = get_context('asic')
        mercury_carrier = get_context('carrier')

        #setting the diamond default registers
        Set_DiamondDefault_Registers()
        asic.set_register_bit(0,0b00000100)
        asic.set_tdc_local_vcal(True)
        print('Enabling VCAL')             

        
        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)
        print('Setting gain to 7fF')      
        
        for tdc_setting in range(0, 16):
                print('Scanning with TDC register value {}'.format(tdc_setting))

                # Set the TDC ramp bias
                asic.set_all_ramp_bias(tdc_setting)

                for i in np.arange(vcal_min,vcal_max,vcal_step):
                    print("Setting VCAL to {} V".format(i))
                    mercury_carrier.set_vcal_in(i)
                    voltage_string = str(i).replace('.','_')

                    time.sleep(1)
                
                    # Capture fast data
                    single_capture(
                            output_folder=folder,
                            filename='voltage_scan_tdc_slope_highGain_d{}_v{}'.format(tdc_setting,voltage_string),
                            num_frames=nframes,
                )
        
        #set to 14fF
        asic.clear_register_bit(0, 0b00001000)
        asic.set_register_bit(  0, 0b00010000)
        print('Setting gain to 14fF')       
        
        for tdc_setting in range(0, 16):
                print('Scanning with TDC register value {}'.format(tdc_setting))

                # Set the TDC ramp bias
                asic.set_all_ramp_bias(tdc_setting)

                for i in np.arange(vcal_min,vcal_max,vcal_step):
                    print("Setting VCAL to {} V".format(i))
                    mercury_carrier.set_vcal_in(i)
                   
                

                    voltage_string = str(i).replace('.','_')

                    time.sleep(1)

                    # Capture fast data
                    single_capture(
                            output_folder=folder,
                            filename='voltage_scan_tdc_slope_medGain_d{}_V{}'.format(tdc_setting,voltage_string),
                            num_frames=nframes,
                )
        
        #set to 21fF
        asic.set_register_bit(0, 0b00001000)
        asic.set_register_bit(  0, 0b00010000)
        print('Setting gain to 21fF')      
        
        for tdc_setting in range(0, 16):
                print('Scanning with TDC register value {}'.format(tdc_setting))

                # Set the TDC ramp bias
                asic.set_all_ramp_bias(tdc_setting)

                for i in np.arange(vcal_min,vcal_max,vcal_step):
                    print("Setting VCAL to {} V".format(i))
                    mercury_carrier.set_vcal_in(i)
                    
                    voltage_string = str(i).replace('.','_')
                    time.sleep(1)

                    # Capture fast data
                    single_capture(
                            output_folder=folder,
                            filename='voltage_scan_tdc_slope_lowGain_d{}_v{}'.format(tdc_setting,voltage_string),
                            num_frames=nframes,
                )


def voltage_scan_tdc_slope_Preampinjection(vcal_min=0,vcal_max=1.5,vcal_step=0.02,folder='Test_pulse_TDC_ramp_PreampInjection',nframes=100000):

        asic = get_context('asic')
        mercury_carrier = get_context('carrier')


        #setting the diamond default registers
        Set_DiamondDefault_Registers()
        asic.set_register_bit(0,0b00000100)
        asic.set_tdc_local_vcal(False)
        print('Enabling VCAL')             

        
        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)
        print('Setting gain to 7fF')      
        
        for tdc_setting in range(0, 16):
                print('Scanning with TDC register value {}'.format(tdc_setting))

                # Set the TDC ramp bias
                asic.set_all_ramp_bias(tdc_setting)

                for i in np.arange(vcal_min,vcal_max,vcal_step):
                    print("Setting VCAL to {} V".format(i))
                    mercury_carrier.set_vcal_in(i)
                    


                    voltage_string = str(i).replace('.','_')


                    # Capture fast data
                    single_capture(
                            output_folder=folder,
                            filename='voltage_scan_tdc_slope_highGain_d{}_v{}'.format(tdc_setting,voltage_string),
                            num_frames=nframes,
                )
        
        #set to 14fF
        asic.clear_register_bit(0, 0b00001000)
        asic.set_register_bit(  0, 0b00010000)
        print('Setting gain to 14fF')       
        
        for tdc_setting in range(0, 16):
                print('Scanning with TDC register value {}'.format(tdc_setting))

                # Set the TDC ramp bias
                asic.set_all_ramp_bias(tdc_setting)

                for i in np.arange(vcal_min,vcal_max,vcal_step):
                    print("Setting VCAL to {} V".format(i))
                    mercury_carrier.set_vcal_in(i)


                    voltage_string = str(i).replace('.','_')


                    # Capture fast data
                    single_capture(
                            output_folder=folder,
                            filename='voltage_scan_tdc_slope_medGain_d{}_V{}'.format(tdc_setting,voltage_string),
                            num_frames=nframes,
                )
        
        #set to 21fF
        asic.set_register_bit(0, 0b00001000)
        asic.set_register_bit(  0, 0b00010000)
        print('Setting gain to 21fF')      
        
        for tdc_setting in range(0, 16):
                print('Scanning with TDC register value {}'.format(tdc_setting))

                # Set the TDC ramp bias
                asic.set_all_ramp_bias(tdc_setting)

                for i in np.arange(vcal_min,vcal_max,vcal_step):
                    print("Setting VCAL to {} V".format(i))
                    mercury_carrier.set_vcal_in(i)

                    voltage_string = str(i).replace('.','_')

                    # Capture fast data
                    single_capture(
                            output_folder=folder,
                            filename='voltage_scan_tdc_slope_lowGain_d{}_v{}'.format(tdc_setting,voltage_string),
                            num_frames=nframes,
                )


