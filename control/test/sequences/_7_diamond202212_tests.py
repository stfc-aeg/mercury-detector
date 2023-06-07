import time

requires = [
        'serialiser_tests',
        'diamond202212_support',
        '_8_fastdata_support',
        '_9_gpib_support',
        'utility',
        'asic_spi',
        ]

provides = [
        'asic_temp_scan',
        'fast_data_spi_7fF',
        'fast_data_spi_7fF_dark',
        'scan_cds_preamp_live',
        'scan_cds_preamp_darks',
        'scan_tdc_slope_extended',
        'scan_tdc_slope_darks',
        'filename_output_test',
        'scan_area_flux_temp',
        'scan_area_flux_integration',
        'scan_tdc_slope_20keV_darks',
        'scan_tdc_slope_extended_20keV',
        'scan_cds_preamp_live_czt',
        'scan_cds_preamp_darks_czt',
        'scan_tdc_slope_extended_20keV_czt',
        'scan_tdc_slope_20keV_darks_czt',
        'cycle_all_gains_tdcslope',
        'cycle_all_gains_tdcslope_dark',
        'scan_gain_offset_integration',
        'scan_gain_offset_integration_dark',
        'GaAs_leftright_scan',
        'GaAs_leftright_scan_dark',
        'GaAs_fast_scan_settings',
        'cycle_all_gains_offsets_tdcslope',
        'cycle_all_gains_offsets_tdcslope_dark',
        ]

def asic_temp_scan(temperatures=[0, 5, 10, 15, 20, 25, 30], testfolder='temperaturescan'):

    for target_temp in temperatures:
        # Set a stable ASIC temperature
        autoset_asic_temp(target_temp)

        # Start a single capture for 60s
        single_capture(output_folder=testfolder, filename = "temperaturescan", num_frames = 10000000, num_batches = 60)

    print('Scan of ASIC temperatures complete')

def fast_data_spi_7fF(material='Si', test_folder='fast_data_spi_7fF',test_filename="7fF_1b_15C_05Al", suffix='', sector_min=0, sector_max=19):
        asic = get_context('asic')

        test_folder = test_folder + '_' + material
        test_filename = material + '_' + test_filename

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)

        #cycle through collecting data
        for i in range(sector_min, sector_max+1):

                print('\n\n\t\t\t<*>\tNow capturing sector {} to {}\n\n'.format(i, test_filename))

                single_capture(output_folder=test_folder,filename=test_filename, suffix=suffix, num_frames=1000000)
                store_sector_readout(sector_samples=10000,sector_array=[i],vcal_values=[0],test_name=test_filename, test_suffix=suffix, test_index=i)

                # Check if an execution abort has been requested
                if abort_sequence():
                        return

def fast_data_spi_7fF_dark(material='Si', test_folder='fast_data_spi_7fF',test_filename="7fF_1b_15C_05Al", suffix='dark', sector_min=0, sector_max=19):
        asic = get_context('asic')

        test_folder = test_folder + '_' + material
        test_filename = material + '_' + test_filename

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)

        #cycle through collecting data
        for i in range(sector_min, sector_max+1):

                print('\n\n\t\t\t<*>\tNow capturing sector {} to {}\n\n'.format(i, test_filename))

                single_capture(output_folder=test_folder,filename=test_filename, suffix=suffix, num_frames=100000)
                store_sector_readout(sector_samples=1000,sector_array=[i],vcal_values=[0],test_name=test_filename, test_suffix=suffix, test_index=i)

                # Check if an execution abort has been requested
                if abort_sequence():
                        return

def scan_cds_preamp(test_folder='scan_cds_preamp', test_filename='scan_cds_preamp', scan_resolution_ns=1, scan_min=1, scan_max=200, frames_per_point=100000):
        asic = get_context('asic')

        print('Scanning CDS and preamp with resolution {}ns between {}-{}ns'.format(scan_resolution_ns, scan_min, scan_max))
        n = (scan_max - scan_min) + 1
        combinations = (((n * (n-1))/scan_resolution_ns)**2) / 2.0
        print('Total combinations: {}'.format(combinations))

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)

        scan_count = 0
        tstart = time.time()

        # Scan every preamp setting in given resolution
        for preamp_setting in range(scan_min, scan_max+1, scan_resolution_ns):

                # Scan every cds setting in given resolution, must be greater than CDS
                for cds_setting in range(preamp_setting+scan_resolution_ns, scan_max+1, scan_resolution_ns):
                        scan_count = scan_count + 1
                        duration = time.time() - tstart
                        rate = scan_count / duration
                        timeleft_m = ((combinations - scan_count) / rate) / 60.0
                        print('Scan {}/{}: CDS {}ns, Preamp {}ns ({}m left)'.format(scan_count, combinations, cds_setting, preamp_setting, int(timeleft_m)))

                        # Set the preamp setting
                        asic.write_register(12, preamp_setting)

                        # Set the CDS setting
                        asic.write_register(14, cds_setting)

                        # Capture Fast Data
                        storage_filename = test_filename 
                        single_capture(
                                output_folder=test_folder,
                                filename=storage_filename,
                                suffix='CDS{}_PA{}'.format(cds_setting, preamp_setting),
                                num_frames=frames_per_point,
                        )

                        # Exit loop on abort
                        if abort_sequence():
                                raise Exception('Sequence was aborted')

def scan_cds_preamp_live():
        # Scan fine
        scan_cds_preamp(
                test_folder='Si_scan_cds_preamp',
                test_filename='cds_pa_fine',
                scan_resolution_ns=1,
                scan_min=1,
                scan_max=40,
                frames_per_point=100000
        )

        # Scan coarse
        scan_cds_preamp(
                test_folder='Si_scan_cds_preamp',
                test_filename='cds_pa_c',
                scan_resolution_ns=5,
                scan_min=40,
                scan_max=199,
                frames_per_point=100000
        )

def scan_cds_preamp_darks():
        # # Scan fine darks
        scan_cds_preamp(
                test_folder='Si_scan_cds_preamp',
                test_filename='cds_pa_fine_darks',
                scan_resolution_ns=1,
                scan_min=1,
                scan_max=40,
                frames_per_point=100000
        )

        # Scan coarse darks
        scan_cds_preamp(
                test_folder='Si_scan_cds_preamp',
                test_filename='cds_pa_c_darks',
                scan_resolution_ns=5,
                scan_min=100,#40,
                scan_max=199,
                frames_per_point=100000
        )

def scan_tdc_slope_extended():
        # Scan the TDC slope at 1s per position, then wait 10m and try again indefinitely (unless aborted)

        asic = get_context('asic')

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)

        round_count = 0
        while True:
                rount_count = round_count + 1
                print('Scanning 16 TDC settings, round {} starting...'.format(round_count))                

                for tdc_setting in range(0, 16):
                        print('Scanning with TDC register value {} (Abort me)'.format(tdc_setting))

                        # Set the TDC ramp bias
                        asic.set_all_ramp_bias(tdc_setting)

                        # Capture fast data
                        single_capture(
                                output_folder='Si_ramp_bias_scan',
                                filename='ramp_bias_{}_d{}'.format(round_count, tdc_setting),
                                num_frames=1000000,
                        )

                # Delay 10 mins, but check every 1s for an abort signal
                waitstart = time.time()
                while time.time() - waitstart < 600.0:
                        time.sleep(1)
                        if abort_sequence():
                                raise Exception('Aborted')

def scan_tdc_slope_darks():

        asic = get_context('asic')

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)

        print('Scanning 16 TDC settings, starting...')                

        for tdc_setting in range(0, 16):
                print('Scanning with TDC register value {}'.format(tdc_setting))

                # Set the TDC ramp bias
                asic.set_all_ramp_bias(tdc_setting)

                # Capture fast data
                single_capture(
                        output_folder='Si_ramp_bias_scan',
                        filename='ramp_bias_darks_d{}'.format(tdc_setting),
                        num_frames=100000,
                )

def filename_output_test():
        # cycle a pretend parameter between 0-10

        print('Beginning pretend capture')
        for param in range(0,10):
                # Capture fast data and instrument data, recording param as the suffix

                single_capture(output_folder='temp_paramtest',
                filename='pretendparamtest',
                suffix='p{}'.format(param),
                num_frames=100000)

        print('Done')

def scan_area_flux_temp(output_folder='area_flux_temp', filename='area_flux_temp', beamsize="5mm", attenuator='15C_05Al', asic_temp=20, num_frames=1000000, run_lowgain=False):
        asic = get_context('asic')

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        print('Scanning High Gain for {} beam, {} attenuator at {}C...'.format(beamsize, attenuator, asic_temp))                

        # Scan High Gain: set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)

        single_capture(
                output_folder = output_folder,
                filename=filename,
                suffix='highGain_{}_{}_{}deg'.format(beamsize, attenuator, asic_temp),
                num_frames=num_frames)

        # Scan Medium Gain: set to 14fF
        asic.set_register_bit(0, 0b00010000)
        asic.clear_register_bit(  0, 0b00001000)

        single_capture(
                output_folder = output_folder,
                filename=filename,
                suffix='medGain_{}_{}_{}deg'.format(beamsize, attenuator, asic_temp),
                num_frames=num_frames)

        if run_lowgain:
                # Scan Low Gain: set to 21fF
                asic.set_register_bit(0, 0b00010000)
                asic.set_register_bit(0, 0b00001000)

                single_capture(
                        output_folder = output_folder,
                        filename=filename,
                        suffix='lowGain_{}_{}_{}deg'.format(beamsize, attenuator, asic_temp),
                        num_frames=num_frames)

def scan_area_flux_integration(output_folder='area_flux_integration', beamsize="5mm", attenuator='15C_05Al', num_frames=1000000):
        asic = get_context('asic')

        for integration in [1, 2, 5, 10]:
                #setting the diamond default registers
                Set_DiamondDefault_Registers()

                # Set the integration
                asic.write_register(6, integration)

                print('Scanning High Gain for {} beam, {} attenuator with integration  {}...'.format(beamsize, attenuator, integration))                

                # Scan High Gain: set to 7fF
                asic.set_register_bit(0, 0b00001000)
                asic.clear_register_bit(  0, 0b00010000)

                single_capture(
                        output_folder = output_folder,
                        filename='area_flux_temp',
                        suffix='highGain_{}_{}_int{}'.format(beamsize, attenuator, integration),
                        num_frames=num_frames)

                # Scan Medium Gain: set to 14fF
                asic.set_register_bit(0, 0b00010000)
                asic.clear_register_bit(  0, 0b00001000)

                single_capture(
                        output_folder = output_folder,
                        filename='area_flux_temp',
                        suffix='medGain_{}_{}_int{}'.format(beamsize, attenuator, integration),
                        num_frames=num_frames)


def scan_tdc_slope_extended_20keV():
        # Scan the TDC slope at 1s per position, then wait 10m and try again indefinitely (unless aborted)

        asic = get_context('asic')

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)

        round_count = 0
        while True:
                rount_count = round_count + 1
                print('Scanning 16 TDC settings, round {} starting...'.format(round_count))                

                for tdc_setting in range(0, 16):
                        print('Scanning with TDC register value {} (Abort me)'.format(tdc_setting))

                        # Set the TDC ramp bias
                        asic.set_all_ramp_bias(tdc_setting)

                        # Capture fast data
                        single_capture(
                                output_folder='Si_ramp_bias_20keV',
                                filename='Si_ramp_bias_20keV_{}_d{}'.format(round_count, tdc_setting),
                                num_frames=1000000,
                        )

                # Delay 10 mins, but check every 1s for an abort signal
                waitstart = time.time()
                while time.time() - waitstart < 600.0:
                        time.sleep(1)
                        if abort_sequence():
                                raise Exception('Aborted')


def scan_tdc_slope_20keV_darks():

        asic = get_context('asic')

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)

        print('Scanning 16 TDC settings, starting...')                

        for tdc_setting in range(0, 16):
                print('Scanning with TDC register value {}'.format(tdc_setting))

                # Set the TDC ramp bias
                asic.set_all_ramp_bias(tdc_setting)

                # Capture fast data
                single_capture(
                        output_folder='Si_ramp_bias_20keV',
                        filename='Si_ramp_bias_20keV_darks_d{}'.format(tdc_setting),
                        num_frames=100000,
                )

def scan_cds_preamp_live_czt(test_folder='CZT_scan_cds_preamp', filename_prefix='cds_pa'):
        # Scan fine
        scan_cds_preamp(
                test_folder=test_folder,
                test_filename=filename_prefix + '_fine',
                scan_resolution_ns=1,
                scan_min=1,
                scan_max=40,
                frames_per_point=100000
        )

        # Scan coarse
        scan_cds_preamp(
                test_folder=test_folder,
                test_filename=filename_prefix + '_c',
                scan_resolution_ns=5,
                scan_min=40,
                scan_max=199,
                frames_per_point=100000
        )

def scan_cds_preamp_darks_czt(test_folder='CZT_scan_cds_preamp', filename_prefix='cds_pa'):
        # # Scan fine darks
        scan_cds_preamp(
                test_folder=test_folder,
                test_filename=filename_prefix + '_fine_darks',
                scan_resolution_ns=1,
                scan_min=1,
                scan_max=40,
                frames_per_point=100000
        )

        # Scan coarse darks
        scan_cds_preamp(
                test_folder=test_folder,
                test_filename=filename_prefix + '_c_darks',
                scan_resolution_ns=5,
                scan_min=100,#40,
                scan_max=199,
                frames_per_point=100000
        )


def scan_tdc_slope_extended_20keV_czt():
        # Scan the TDC slope at 1s per position, then wait 10m and try again indefinitely (unless aborted)

        asic = get_context('asic')

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)

        round_count = 0
        while True:
                round_count = round_count + 1
                print('Scanning 16 TDC settings, round {} starting...'.format(round_count))                

                for tdc_setting in range(0, 16):
                        print('Scanning with TDC register value {} (Abort me)'.format(tdc_setting))

                        # Set the TDC ramp bias
                        asic.set_all_ramp_bias(tdc_setting)

                        # Capture fast data
                        single_capture(
                                output_folder='Czt_ramp_bias_20keV',
                                filename='Czt_ramp_bias_70Al_20keV'.format(round_count, tdc_setting),
                                suffix='{}_d{}'.format(round_count, tdc_setting),
                                num_frames=1000000,
                        )

                # Delay 10 mins, but check every 1s for an abort signal
                print('Sleeping for 10m')
                waitstart = time.time()
                while time.time() - waitstart < 600.0:
                        time.sleep(1)
                        if abort_sequence():
                                raise Exception('Aborted')


def scan_tdc_slope_20keV_darks_czt():

        asic = get_context('asic')

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)

        print('Scanning 16 TDC settings, starting...')                

        for tdc_setting in range(0, 16):
                print('Scanning with TDC register value {}'.format(tdc_setting))

                # Set the TDC ramp bias
                asic.set_all_ramp_bias(tdc_setting)

                # Capture fast data
                single_capture(
                        output_folder='Czt_ramp_bias_20keV',
                        filename='Czt_ramp_bias_70Al_20keV_darks',
                        suffix='d{}'.format(tdc_setting),
                        num_frames=100000,
                )

def scan_tdc_slope_gain_oneloop(output_folder='Czt_ramp_bias_60keV', filename_prefix='Czt_ramp_bias_gain_60keV', gain_setting=7, loopnum=0, suffix_in = ''):
        # Scan the TDC slope at 1s per position, then wait 10m and try again indefinitely (unless aborted)

        asic = get_context('asic')

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        #set to gain
        if gain_setting == 7:
                asic.set_register_bit(0, 0b00001000)
                asic.clear_register_bit(  0, 0b00010000)
                gainstring = 'highGain'
        elif gain_setting == 14:
                asic.set_register_bit(0, 0b00010000)
                asic.clear_register_bit(  0, 0b00001000)
                gainstring = 'medGain'
        elif gain_setting == 21:
                asic.set_register_bit(0, 0b00010000)
                asic.set_register_bit(0, 0b00001000)
                gainstring = 'lowGain'

        print('Scanning 16 TDC settings, round {} starting...'.format(loopnum))                

        for tdc_setting in range(0, 16):
                print('Scanning with TDC register value {} (Abort me)'.format(tdc_setting))

                # Set the TDC ramp bias
                asic.set_all_ramp_bias(tdc_setting)

                # Capture fast data
                single_capture(
                        output_folder=output_folder,
                        filename=filename_prefix,
                        suffix='{}_{}_d{}_{}'.format(suffix_in, gainstring, tdc_setting, loopnum),
                        num_frames=1000000,
                )


def scan_tdc_slope_gain_darks(output_folder='Czt_ramp_bias_60keV', filename_prefix='Czt_ramp_bias_gain_60keV_dark', gain_setting=7):

        asic = get_context('asic')

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        #set to gain
        if gain_setting == 7:
                asic.set_register_bit(0, 0b00001000)
                asic.clear_register_bit(  0, 0b00010000)
                gainstring = 'highGain'
        elif gain_setting == 14:
                asic.set_register_bit(0, 0b00010000)
                asic.clear_register_bit(  0, 0b00001000)
                gainstring = 'medGain'
        elif gain_setting == 21:
                asic.set_register_bit(0, 0b00010000)
                asic.set_register_bit(0, 0b00001000)
                gainstring = 'lowGain'

        #set to 7fF
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)

        print('Scanning 16 TDC settings, starting...')                

        for tdc_setting in range(0, 16):
                print('Scanning with TDC register value {}'.format(tdc_setting))

                # Set the TDC ramp bias
                asic.set_all_ramp_bias(tdc_setting)

                # Capture fast data
                single_capture(
                        output_folder=output_folder,
                        filename=filename_prefix,
                        suffix='{}_d{}'.format(gainstring, tdc_setting),
                        num_frames=100000,
                )

def cycle_all_gains_tdcslope_dark():
        for gainsetting in [7, 14, 21]:
                # Take darks
                scan_tdc_slope_gain_darks(gain_setting=gainsetting)
        
def cycle_all_gains_tdcslope(mins_delay=5):
        # Take live extended, forever
        iteration_count = 1
        while True:
                iteration_count = iteration_count + 1
                # Scan every gain setting
                for gainsetting in [7, 14, 21]:
                        scan_tdc_slope_gain_oneloop(gain_setting=gainsetting, loopnum=iteration_count)

                # Delay 10 mins, but check every 1s for an abort signal
                print('Sleeping for {}m'.format(mins_delay))
                waitstart = time.time()
                while time.time() - waitstart < (mins_delay * 60.0):
                        time.sleep(1)
                        if abort_sequence():
                                raise Exception('Aborted')


def scan_gain_offset_integration(output_folder='scan_gain_offset_integration', filename='scan_gain_offset_int', integration_values=[1, 2, 5, 10], num_frames=1000000):
        asic = get_context('asic')

        #setting the diamond default registers
        Set_DiamondDefault_Registers()

        # Cycle Gains
        for gain_setting in [7, 14, 21]:

                # Set the gain value
                if gain_setting == 7:
                        asic.set_register_bit(0, 0b00001000)
                        asic.clear_register_bit(  0, 0b00010000)
                        gainstring = 'highGain'
                elif gain_setting == 14:
                        asic.set_register_bit(0, 0b00010000)
                        asic.clear_register_bit(  0, 0b00001000)
                        gainstring = 'medGain'
                elif gain_setting == 21:
                        asic.set_register_bit(0, 0b00010000)
                        asic.set_register_bit(0, 0b00001000)
                        gainstring = 'lowGain'

                # Cycle offsets
                for offset_setting in [0, 1]:

                        # Set offset
                        if offset_setting == 0:
                                asic.clear_register_bit(0, 0b01000000)
                                offsetstring = '-20keV'
                        else:
                                asic.clear_register_bit(0, 0b01000000)
                                offsetstring = '-10keV'

                        # Cycle integration
                        for integration_setting in integration_values:

                                # Set the integration
                                asic.write_register(6, integration_setting)

                                # Perform a single capture of specified number of frames
                                single_capture(
                                       output_folder=output_folder,
                                        filename=filename,
                                        suffix='{}_off_{}_int_{}_'.format(gainstring, offsetstring, integration_setting),
                                        num_frames=num_frames,
                                )

def scan_gain_offset_integration_dark():
        # Call the above, but add darks to filename and reduce frames
        scan_gain_offset_integration(filename='scan_gain_off_int_dark', num_frames=100000)


def GaAs_leftright_scan(test_folder = 'GaAs_21fF_leftright', test_filename='GaAs_21fF_leftright', suffix_in='', fastdata_samples=1000000, spi_samples=10000):
        # Scan left to right, recording fast data on div17, SPI on sectors 2, 3, and 4.
        # Settings: 20fF, both -10 and -20 for offset.
  
        asic = get_context('asic')

        # Setting the diamond default registers
        Set_DiamondDefault_Registers()

        # Set 21fF
        asic.set_register_bit(0, 0b00010000)
        asic.set_register_bit(0, 0b00001000)

        # Cycle the two offset settings
        for offset_setting in [0, 1]:
                # Set offset
                if offset_setting == 0:
                        asic.clear_register_bit(0, 0b01000000)
                        offsetstring = '20keV'
                else:
                        asic.clear_register_bit(0, 0b01000000)
                        offsetstring = '10keV'

                suffix = suffix_in + '_' + offsetstring

                # Capture fast data 
                single_capture(output_folder=test_folder,filename=test_filename, suffix=suffix, num_frames=fastdata_samples)
                
                # Capture SPI for given sectors
                store_sector_readout(sector_samples=spi_samples ,sector_array=[2, 3, 4],vcal_values=[0],test_name=test_filename, test_suffix=suffix, test_index=i)

                # Check if an execution abort has been requested
                if abort_sequence():
                        return

def GaAs_leftright_scan_dark():
        GaAs_leftright_scan(suffix_in='dark', fastdata_samples=100000, spi_samples=1000)

def GaAs_fast_scan_settings(test_folder='GaAs_array_scan_60keV', test_filename='GaAs_array_scan_60keV', suffix_in='', division_num=17, isdark=False, sector_num=2, anum=1, fastdata_samples=5000000):
        asic = get_context('asic')

        # Reduce samples if taking darks
        if isdark:
                fastdata_samples = 100000

        # Setting the diamond default registers
        Set_DiamondDefault_Registers()

        total_combinations = 6
        current_combination = 0
        set_progress(current_combination, total_combinations)

        # Cycle Gains
        for gain_setting in [7, 14, 21]:

                # Set the gain value
                if gain_setting == 7:
                        asic.set_register_bit(0, 0b00001000)
                        asic.clear_register_bit(  0, 0b00010000)
                        gainstring = 'highGain'
                elif gain_setting == 14:
                        asic.set_register_bit(0, 0b00010000)
                        asic.clear_register_bit(  0, 0b00001000)
                        gainstring = 'medGain'
                elif gain_setting == 21:
                        asic.set_register_bit(0, 0b00010000)
                        asic.set_register_bit(0, 0b00001000)
                        gainstring = 'lowGain'

                # Cycle offsets
                for offset_setting in [0, 1]:

                        # Set offset
                        if offset_setting == 0:
                                asic.clear_register_bit(0, 0b01000000)
                                offsetstring = '20keV'
                        else:
                                asic.clear_register_bit(0, 0b01000000)
                                offsetstring = '10keV'

                        if isdark:
                                suffix = suffix_in + '_' + gainstring + '_' + offsetstring + '_div' + str(division_num) + '_dark'
                        else:
                                suffix = suffix_in + '_' + gainstring + '_' + offsetstring + '_div' + str(division_num) + '_sec' + str(sector_num) + '_A{:02}'.format(anum)

                        # Capture fast data 
                        single_capture(output_folder=test_folder,filename=test_filename, suffix=suffix, num_frames=fastdata_samples, timeout=120)

                        # Update progress bar
                        current_combination = current_combination + 1; set_progress(current_combination, total_combinations)


def cycle_all_gains_offsets_tdcslope_dark():
        asic = get_context('asic')

        for gainsetting in [7, 14, 21]:
                # Take darks

                # Scan every offset
                for offset_setting in [0, 1]:

                        # Set offset
                        if offset_setting == 0:
                                asic.clear_register_bit(0, 0b01000000)
                                offsetstring = '20keV'
                        else:
                                asic.clear_register_bit(0, 0b01000000)
                                offsetstring = '10keV'

                        scan_tdc_slope_gain_oneloop(output_folder='GaAs_ramp_bias_60keV', filename_prefix='GaAs_ramp_bias_gain_offset_60keV', gain_setting=gainsetting, suffix_in=(offsetstring + '_dark'))
        
def cycle_all_gains_offsets_tdcslope(mins_delay=10, loop_limit=7):
        asic = get_context('asic')

        # Take live extended, forever
        iteration_count = 2
        while iteration_count <=loop_limit:
                # Scan every gain setting
                for gainsetting in [7, 14, 21]:

                        # Scan every offset
                        for offset_setting in [0, 1]:

                                # Set offset
                                if offset_setting == 0:
                                        asic.clear_register_bit(0, 0b01000000)
                                        offsetstring = '20keV'
                                else:
                                        asic.clear_register_bit(0, 0b01000000)
                                        offsetstring = '10keV'
                                
                                scan_tdc_slope_gain_oneloop(output_folder='GaAs_ramp_bias_60keV', filename_prefix='GaAs_ramp_bias_gain_offset_60keV', gain_setting=gainsetting, loopnum=iteration_count, suffix_in=offsetstring)
                                #print('saving {}/{} {} {} {}'.format('GaAs_ramp_bias_60keV', 'GaAs_ramp_bias_gain_offset_60keV', gainsetting, iteration_count, offsetstring))

                # Delay 10 mins, but check every 1s for an abort signal
                print('Sleeping for {}m'.format(mins_delay))
                waitstart = time.time()
                while time.time() - waitstart < (mins_delay * 60.0):
                        time.sleep(1)
                        if abort_sequence():
                                raise Exception('Aborted')

                set_progress(iteration_count, loop_limit)
                iteration_count = iteration_count + 1

        print('TDC slope has finished :)')