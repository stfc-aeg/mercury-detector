import time
import logging
import itertools
from odin_devices.spi_device import SPIDevice

REGISTER_WRITE_TRANSACTION = 0X00
REGISTER_READ_TRANSACTION = 0X80
REGISTER_ADDRESS_MASK = 0b01111111

CAL_PATTERN_DEFAULT_BYTES = {
        'rows': [0x55]*10,
        'cols': [0xAA]*10
        }

class ASICDisabledError (Exception):
    def __init__(self, message):
        super().__init__(message)

class Asic():

    # Maps MERCURY logical channel to (serialiser block, driver number)
    _block_drv_channel_map = {  0   :   (1, 2),
                                1   :   (1, 1),
                                2   :   (2, 1),
                                3   :   (2, 2),
                                4   :   (3, 2),
                                5   :   (3, 1),
                                6   :   (4, 1),
                                7   :   (4, 2),
                                8   :   (5, 2),
                                9   :   (5, 1),
                                10  :   (6, 1),
                                11  :   (6, 2),
                                12  :   (7, 2),
                                13  :   (7, 1),
                                14  :   (8, 1),
                                15  :   (8, 2),
                                16  :   (9, 2),
                                17  :   (9, 1),
                                18  :   (10, 1),
                                19  :   (10, 2),
                                  }
    _serialiser_mode_names = {
        "init":0b00, "bonding":0b01, "data":0b11
    }

    def __init__(self, gpio_nrst, gpio_sync_sel, gpio_sync, bus=2, device=0, hz=2000000):

        # super(Asic, self).__init__(bus, device, hz)
        self.spi = SPIDevice(bus=bus, device=device, hz=hz)
        self.spi.set_mode(0)
        self.spi.set_cs_active_high(False)

        self._logger = logging.getLogger('ASIC')

        self.page = 1

        self.gpio_nrst = gpio_nrst
        self.gpio_sync_sel = gpio_sync_sel
        self.gpio_sync = gpio_sync

        # Set up store for local serialiser configs
        self._serialiser_block_configs = []
        for i in range(1, 11):
            new_serialiser_block = SerialiserBlockConfig()
            self._serialiser_block_configs.append(new_serialiser_block)
        self._logger.info("ASIC init complete")

        # Local State Variables init to None before read
        self._reset_local_states()

    def _reset_local_states(self):
        # Local State Variables init to None before read. Should be done
        # on boot and on ASIC reset
        self._STATE_feedback_capacitance = None
        self._STATE_frame_length_clocks = None
        self._STATE_integration_time = None
        self._STATE_serialiser_mode = None
        self._STATE_all_serialiser_pattern = None
        self._STATE_calibration_test_pattern_en = None

    """ SPI Register Access Functions """
    def _reset_page(self):
        self.page = 1

    def _set_page(self, page):
        page_bit = {1: 0b0, 2: 0b1}[page]

        if self.page != page:
            # Read
            command = 0x00 | REGISTER_READ_TRANSACTION
            transfer_buffer = [command, 0x00]
            config_value = self.spi.transfer(transfer_buffer)[1]

            # Modify
            page_set_value = (config_value & 0b11111110) | (page_bit & 0b1)

            # Write
            command = 0x00 | REGISTER_WRITE_TRANSACTION
            transfer_buffer = [command, page_set_value]
            self.spi.transfer(transfer_buffer)

            self.page = page

    def read_register(self, address):
        if not self.get_enabled():
            raise ASICDisabledError('Cannot read, ASIC disabled')

        if (address > 127):     # Page 2
            self._set_page(2)
        else:                   # Page 1
            self._set_page(1)
        address = address & REGISTER_ADDRESS_MASK

        command = address | REGISTER_READ_TRANSACTION

        transfer_buffer = [command]
        transfer_buffer.append(0x00)

        readback = self.spi.transfer(transfer_buffer)

        self._logger.debug("Register {} read as {}".format(address, readback))

        return readback
    
    def write_register(self, address, value):
        if not self.get_enabled():
            raise ASICDisabledError('Cannot write, ASIC disabled')

        if (address > 127):     # Page 2
            self._set_page(2)
        else:                   # Page 1
            self._set_page(1)
        address = address & REGISTER_ADDRESS_MASK

        command = address | REGISTER_WRITE_TRANSACTION

        transfer_buffer = [command]
        transfer_buffer.append(value)

        self.spi.transfer(transfer_buffer)

        self._logger.debug("Register {} written with {}".format(address, value))

    def burst_read(self, start_register, num_bytes):
        if not self.get_enabled():
            raise ASICDisabledError('Cannot read, ASIC disabled')

        if (start_register > 127):  # Page 2
            self._set_page(2)
        else:                       # Page 1
            self._set_page(1)
        start_register = start_register & REGISTER_ADDRESS_MASK

        command = start_register | REGISTER_READ_TRANSACTION

        transfer_buffer = [command]
        for i in range(0, num_bytes):
            transfer_buffer.append(0x00)

        readback = self.spi.transfer(transfer_buffer)

        return readback

    def burst_write(self, start_register, values):
        if not self.get_enabled():
            raise ASICDisabledError('Cannot write, ASIC disabled')

        if (start_register > 127):  # Page 2
            self._set_page(2)
        else:                       # Page 1
            self._set_page(1)
        start_register = start_register & REGISTER_ADDRESS_MASK

        command = start_register | REGISTER_WRITE_TRANSACTION

        transfer_buffer = [command]
        for i in range(0, len(values)):
            transfer_buffer.append(values[i])

        self.spi.transfer(transfer_buffer)

    def set_register_bit(self, register, bit):
        if not self.get_enabled():
            raise ASICDisabledError('Cannot write, ASIC disabled')
        original = self.read_register(register)[1]
        self.write_register(register, original | bit)

    def clear_register_bit(self, register, bit):
        if not self.get_enabled():
            raise ASICDisabledError('Cannot write, ASIC disabled')
        original = self.read_register(register)[1]
        self.write_register(register, original & (~bit))

    @staticmethod
    def convert_8bit_12bit(values_8bit):
        val1 = 0
        val2 = 0
        val_index = 0
        output_array = []

        for i in range(len(values_8bit)):
            if val_index == 0:      # First byte
                val1 = values_8bit[i]
            elif val_index == 1:    # Second byte
                val2 = values_8bit[i]
            else:                   # Third byte
                val3 = values_8bit[i]

                output_12bit_1 = (val1 << 4) + ((val2 & 0xF0) >> 4)
                output_12bit_2 = ((val2 & 0x0F) << 8) + val3
                output_array.append(output_12bit_1)
                output_array.append(output_12bit_2)

            if val_index == 2:
                val_index = 0
            else:
                val_index += 1

        return output_array

    @staticmethod
    def convert_12bit_8bit(values_12bit):
        output_array = []
        for i in range(len(values_12bit)):
            if i % 2 == 0:      # First 12-bit value in pair
                val_12bit_1 = values_12bit[i]
            else:               # Second 12-bit value in pair
                val_12bit_2 = values_12bit[i]

                # All 24-bits have been collected and can be converted to 8-bit
                byte1 = (val_12bit_1 >> 4) & 0xFF
                byte2 = (((val_12bit_1 & 0xF) << 4) + (val_12bit_2 >> 8)) & 0xFF
                byte3 = (val_12bit_2 & 0xFF)

                output_array.extend(byte1, byte2, byte3)

        return output_array

    """ Pin and power control """
    def enable(self):
        self.gpio_nrst.set_value(1)
        self._reset_page()          # Page is now default value

        # Read into local copies of serialiser config
        for i in range(0, 11):
            self._read_serialiser_config(i)

        self._logger.info('ASIC enabled')

    def get_enabled(self):
        return True if self.gpio_nrst.get_value() == 1 else False

    def disable(self):
        self.gpio_nrst.set_value(0)
        self._logger.info('ASIC disabled')
        self._reset_local_states()  # Local states now None

    def set_sync(self, is_en):
        pin_state = 1 if (is_en) else 0         # High is GPIO 1
        self.gpio_sync.set_value(pin_state)
        self._logger.info('ASIC SYNC set: {}'.format(is_en))

    def get_sync(self):
        enabled = True if self.gpio_sync.get_value() == 1 else False
        return enabled

    def set_sync_source_aux(self, is_aux):
        pin_state = 0 if (is_aux) else 1
        self.gpio_sync_sel.set_value(pin_state)
        source = 'aux' if is_aux else 'zynq'
        self._logger.info('ASIC SYNC configured to come from {}'.format(source))

    def get_sync_source_aux(self):
        return True if self.gpio_sync_sel.get_value() == 0 else False

    def reset(self):
        # Reset the ASIC using the nRST and SYNC control lines
        self._logger.warning("Resetting ASIC...")
        self.disable()          # nReset low
        self.set_sync(False)    # Sync also low
        time.sleep(0.1)

        self.enable()
        time.sleep(0.1)     # Allow ASIC time to come out of reset
        self._logger.debug("ASIC reset complete")

    """ Device function control """
    def enter_global_mode(self):
        # Ensure that the sync is under zynq control
        self.set_sync_source_aux(False)

        # Set the sync line low before reset
        self.set_sync(False)

        # Reset the ASIC
        self.reset()

        # Enable global control of readout, digital signals, analogue signals,
        # analogue bias enable, TDC oscillator enable, serialiser PLL enable,
        # TDC PLL enable, VCAL select, serialiser mode, serialiser analogue/
        # digital reset.
        self.write_register(0x01, 0x7F)
        self.write_register(0x02, 0x63)

        # Set the sync active
        self.set_sync(True)

        # Enter further settings post sync raise
        self.write_register(0x03, 0x08)     # Enable pixel bias
        self.write_register(0x03, 0x09)     # Enable TDC PLLs
        self.write_register(0x03, 0x0D)     # Enable TDC oscillators
        self.write_register(0x03, 0x0F)     # Enable Serialiser PLLs
        self.write_register(0x03, 0x1F)     # Enable pixel analogue signals
        self.write_register(0x03, 0x3F)     # Enable pixel digital signals

        time.sleep(0.1) #TEMP suggested by Lawrence

        # Set serialisers configuration blocks to default working mode
        self._init_serialisers()

        # Remove serialiser digital and analogue reset
        self.write_register(0x04, 0x02) # Remove analogue reset
        time.sleep(0.1) #TEMP suggested by Lawrence
        self.write_register(0x04, 0x03) # Remove digital reset

        # Cycle through serialiser modes, starts in init
        # self.set_global_serialiser_mode("bonding")   # Enter bonding mode from init mode
        #TODO Advance serialiser from bonding to data mode, see manual pg89

        # Enable readout
        self.write_register(0x03, 0x7F)

        # Enable calibrate
        self.enable_calibration_test_pattern(True)

        self._logger.info("Global mode configured")

        # RE-INIT SERIALISERS (Serialisers will not function without additional reset. Reason unknown.)
        time.sleep(0.5)
        self.clear_register_bit(0x04, 0b10) # ana
        self.clear_register_bit(0x04, 0b01) # digi
        time.sleep(0.5)
        self.set_register_bit(0x04, 0b10)   # ana
        self.set_register_bit(0x04, 0b01)   # digi
        self._logger.info("Serialiser encoding state force reset")

    def read_test_pattern(self, sector):
        # Read out a test pattern from a specificed sector using the 480
        # byte test shift register (320 12-bit pixels). The result is
        # returned as an array of 320 12-bit pixel values.

        # Set test register read mode with trigger 0
        self.write_register(0x07, 0x02 | (sector<<2))

        # Keep test register read mode with trigger 1
        self.write_register(0x07, 0x82 | (sector<<2))
        # time.sleep(0.001)

        # Put test shift register into shift mode
        self.write_register(0x07, 0x81 | (sector<<2))

        # Read the test shift register
        readout = self.burst_read(127, 480)

        # Convert to 12-bit data and remove first byte (not part of read)        
        readout_12bit = Asic.convert_8bit_12bit(readout[1:])

        return readout_12bit

    def write_test_pattern(self, pattern_data_12bit, sector):
        # Write a test pattern to the test shift register for a single sector.
        # The input is taken as an array of 360 12-bit pixel values, written in 4x4
        # grids from left to right. Each grid is supplied with values starting at
        # the bottom left pixel, moving horizontally then up one row (see the ASIC
        # manual Test Shfit Reigster Data Order (v1.3 section 5.7.2).

        # Prepare the 8-bit data
        pattern_data_8bit = Asic.convert_12bit_8bit(pattern_data_12bit)

        # Set the test register to shift mode
        self.write_register(0x07, 0x01 | (sector << 2))

        # Burst write register 127 with the 8-bit data
        self.burst_write(pattern_data_8bit, 480)

        # Set the test register to write mode
        self.write_register(0x07, 0x03 | (sector << 2))

    def test_pattern_identify_sector_division(self, sector):
        # Send data to a given sector that will identify individual 4x4 grids with
        # set pattern. Each pixel in the 4x4 grid will have the same value, which is
        # incremented counting the grids from left to right and then top to bottom.
        # Grid numbering will start at 1 to ensure there is something to receive.
        # (i.e. the second grid in the third sector will contain pixel values 43)

        sector_offset = (sector * 20) + 1 # Sector numbering starts at 0, first value 1

        # Generate the 4x4 grid 12-bit values
        pattern_12bit = []
        for grid_id in range(sector_offset, sector_offset+20):
            grid_values = [grid_id] * 20
            pattern_12bit.extend(grid_values)

        # Submit the test pattern
        self.write_test_pattern(pattern_12bit, sector)

    def enable_calibration_test_pattern(self, enable=True):
        if enable:
            self.set_register_bit(0x00, 0b100)
            self._STATE_calibration_test_pattern_en = True
        else:
            self.clear_register_bit(0x00, 0b100)
            self._STATE_calibration_test_pattern_en = False
        self._logger.info(("Enabled" if enable else "Disabled") + " calibration pattern mode")

    def get_calibration_test_pattern_enabled(self, direct=False):
        if direct or self._STATE_calibration_test_pattern_en is None:
            # Read from ASIC and set locally stored state
            latest_value = (self.read_register(0x00)[0] & 0b100) > 0
            self._STATE_calibration_test_pattern_en = latest_value

        return self._STATE_calibration_test_pattern_en

    def set_calibration_test_pattern(self, row_bytes, column_bytes):
        # Submit a calibration test pattern, which consists of two arrays (one for
        # row and the other for columns). Each array contains binary pixel values.
        # The row and column patterns are ANDed toghether, so only pixels that have
        # a high value in both row and column will be high. The ASIC cycles through
        # 4 patterns (rising, falling, and 2 blanks) using this base pattern.
        #
        # Bytes are MSB-first, but the rows are loaded in reverse from 79 to 0 (i.e.
        # to set only the first pixel, the last row byte would be 0b00000001 and the
        # first column byte would be 0b10000000.

        self._logger.debug('Writing calibration test pattern {}'.format(
            [hex(x) for x in (row_bytes + column_bytes)]))

        self.burst_write(126, row_bytes + column_bytes)

    def set_calibration_test_pattern_bits(self, row_bits, column_bits):
        # Constructs a calibration pattern using arrays of bits for rows and columns.
        # Ordering is from pixel count 0 to 79 for each.

        # Reverse the row array, since it is loaded from pixel 79 to 0.
        row_bits_reversed = reversed(row_bits)

        # Convert bits to byte array, MSB First
        row_bytes = [sum([byte[b] << (7- b) for b in range(7,-1,-1)])
                for byte in zip(*(iter(row_bits_reversed),) * 8)]
        column_bytes = [sum([byte[b] << (7- b) for b in range(7,-1,-1)])
                for byte in zip(*(iter(column_bits),) * 8)]

        self.set_calibration_test_pattern(row_bytes=row_bytes, column_bytes=column_bytes)

    def cal_pattern_highlight_sector_division(self, sector, division):
        # Use the calibration test pattern to (within a single sector) zero all pixels
        # except those in a certain division and sector, which will be filled with all
        # high bits. There is one bit per pixel in the calibration pattern.

        row_bits = []
        column_bits = []

        # Only rows with pixels in the correct sector will be highlighted
        for row_id in range(0, 80):
            sector_id = int(row_id / 4)
            if sector_id == sector:
                row_bits.append(1)
            else:
                row_bits.append(0)

        # Only columns with pixels in the correct division will be highlighted
        for column_id in range(0, 80):
            division_id = int(column_id / 4)
            if division_id == division:
                column_bits.append(1)
            else:
                column_bits.append(0)

        self._logger.info("Generated calibration test pattern to highlight sector {}, division {}".format(sector, division))

        # Submit the test pattern and enable it
        self.set_calibration_test_pattern_bits(row_bits=row_bits, column_bits=column_bits)
        self.enable_calibration_test_pattern(True)

    def cal_pattern_set_default(self):
        self.set_calibration_test_pattern(CAL_PATTERN_DEFAULT_BYTES['rows'],
                CAL_PATTERN_DEFAULT_BYTES['cols'])

        self._logger.info("Set calibration test pattern to default value")

    def set_tdc_local_vcal(self, local_vcal_en=True):
        # Enable to use VCAL as the direct comparator input rather than the
        # default.
        if local_vcal_en:
            self.set_register_bit(0x04, 0b1 << 6)
        else:
            self.clear_register_bit(0x04, 0b1 << 6)

    def set_all_ramp_bias(self, bias):
        # Set the ramp bias value for all 40 ramps in the ASIC.
        if not bias in range(0, 16):     # 4-bit field
            raise ValueError("bias must be in range 0-15")

        for register in range(46, 66):
            self.write_register(register, (bias << 4) | bias)   # Set for both nibbles

        self._logger.info("Set ramp bias for all 40 ASIC ramps to {}".format(bias))

    def set_integration_time(self, integration_time_frames):
        if not integration_time_frames in range(0,(0xFF)+1):
            raise ValueError("Integration time frames must be 0-255")

        self.write_register(0x06, integration_time_frames)
        self._STATE_integration_time = integration_time_frames
        self._logger.info('Set integration time to {} frames'.format(integration_time_frames))

    def get_integration_time(self, direct=False):
        # Return the integration time in frames.
        # Returns the locally stored value by default to avoid client request
        # based load. However, a direct reading can be forced (e.g. if relevant
        # bits have been modified directly with another function).
        if direct or self._STATE_integration_time is None:
            # Read from ASIC and set locally stored state
            latest_value = self.read_register(0x06)[1]
            self._STATE_integration_time = latest_value

        return self._STATE_integration_time

    def set_frame_length(self, frame_length_clocks):
        if not frame_length_clocks in range(0,(0xFF)+1):
            raise ValueError("Frame length must be 0-255")

        self.write_register(0x05, frame_length_clocks)
        self._STATE_frame_length = frame_length_clocks
        self._logger.info('Set frame length to  {} clocks'.format(frame_length_clocks))

    def get_frame_length(self, direct=False):
        # Return the frame length in clock cycles.
        # Returns the locally stored value by default to avoid client request
        # based load. However, a direct reading can be forced (e.g. if relevant
        # bits have been modified directly with another function).
        if direct or self._STATE_frame_length_clocks is None:
            # Read from ASIC and set locally stored state
            latest_value = self.read_register(0x05)[1]
            self._STATE_frame_length = latest_value

        return self._STATE_frame_length

    def set_feedback_capacitance(self, feedback_capacitance_fF):
        if not feedback_capacitance_fF in [0, 7, 14, 21]:
            raise ValueError("Capacitance must be 0, 7, 14 or 21 (fF)")

        field_bits = {0 :   0b00,
                      7 :   0b01,
                      14:   0b10,
                      21:   0b11}[feedback_capacitance_fF]

        previous_reg_val = self.read_register(0x00)[1]

        new_reg_val = (previous_reg_val & 0b11100111) | (field_bits << 3)

        self.write_register(0x00, new_reg_val)
        self._STATE_feedback_capacitance = feedback_capacitance_fF  # Cache fF value
        self._logger.info('Set feedback capacitance to  {}fF'.format(feedback_capacitance_fF))

    def get_feedback_capacitance(self, direct=False):
        # Return the current feedback capacitance in fF.
        # Returns the locally stored value by default to avoid client request
        # based load. However, a direct reading can be forced (e.g. if relevant
        # bits have been modified directly with another function).
        if direct or self._STATE_feedback_capacitance is None:
            # Read from ASIC and set locally stored state
            latest_value = (self.read_register(0x00)[1] >> 3) & 0b11
            total_fF = 7 if (latest_value & 0b01 > 0) else 0
            total_fF += 14 if (latest_value & 0b10 > 0) else 0
            self._STATE_feedback_capacitance = total_fF

        return self._STATE_feedback_capacitance

    """ Serialiser Functions """
    def _init_serialisers(self):
        # Configure serialiser control blocks so that they have settings that
        # have been determined during the tuning process. Ideally this should
        # be called after an ASIC reset.

        # Sync current readings with ASIC
        for block_num in range(1, 11):
            self._read_serialiser_config(block_num)
        self._reset_local_states()

        # Set optimal settings
        for serialiser_number in range(1,11):
            serialiser = self._serialiser_block_configs[serialiser_number-1]

            serialiser.enable_ccp             = 0b1       # default
            serialiser.enable_ccp_initial     = 0b1
            serialiser.low_priority_ccp       = 0b1
            serialiser.strict_alignment       = 1         # default
            serialiser.patternControl         = 0b000     # default
            serialiser.ccp_count              = 0b000
            serialiser.bypassScramble         = 0b0       # default
            serialiser.cml_en                 = 0b00      # default (on)
            serialiser.dll_config             = 0b000
            serialiser.dll_phase_config       = 0b0

            # Write the config to the serialiser control block
            self._write_serialiser_config(serialiser_number)

        # Settings that match defaults
    def get_serialiserblk_from_channel(self, channel):
        block_num, driver_num = self._block_drv_channel_map[channel]
        serialiser = self._serialiser_block_configs[block_num]

        self._logger.debug('Channel {} decoded to serialiser {} driver {}'.format(
            channel, block_num, driver_num))

        return (serialiser, block_num, driver_num)

    def _write_serialiser_config(self, serialiser_block_num):
        ser_index = serialiser_block_num - 1    # Datasheet numbering starts at 1
        base_address = 66 + (ser_index) * 6

        # Pack the structure values into the local array and export
        config_block = self._serialiser_block_configs[ser_index].pack()

        # Write to the ASIC
        self._logger.debug("Configured serialiser block {} at start address {}:\t{}".format(
            serialiser_block_num, base_address,
            self._serialiser_block_configs[ser_index].__repr__()
        ))
        self.burst_write(base_address, config_block)

        # Assume the write succeeded and re-import the config bytes
        self._serialiser_block_configs[ser_index].unpack(config_block)

    def _read_serialiser_config(self, serialiser_block_num):
        ser_index = serialiser_block_num - 1    # Datasheet numbering starts at 1
        base_address = 66 + (ser_index) * 6

        config_block = self.burst_read(base_address, 6)[1:]

        self._serialiser_block_configs[ser_index].unpack(config_block)

    def set_serialiser_patternControl(self, serialiser_block_num, pattern, holdoff=False):
        # LEGACY, DO NOT USE
        ser_index = serialiser_block_num - 1    # Datasheet numbering starts at 1
        self._serialiser_block_configs[ser_index].patternControl = pattern

        if not holdoff:
            self._write_serialiser_config(serialiser_block_num)

    def set_ser_enable_CML_drivers(self, enable, holdoff=False):
        # Sets the CML driver enable for all channels

        for serialiser_number in range(1,11):
            serialiser = self._serialiser_block_configs[serialiser_number-1]
            serialiser.set_cml_driver_enable(1, enable)
            serialiser.set_cml_driver_enable(2, enable)
            if not holdoff:
                self._write_serialiser_config(serialiser_number)

    def set_all_serialiser_pattern(self, pattern):
        # Set pattern for all serialisers
        if not pattern in range(0, 8):
            return ValueError('Pattern setting must be 0-7')

        for serialiser_number in range(1,11):
            serialiser = self._serialiser_block_configs[serialiser_number-1]
            serialiser.pattern = pattern
            self._write_serialiser_config(serialiser_number)

        self._logger.info('Serialiser pattern set to {} for all blocks'.format(pattern))

        self._STATE_all_serialiser_pattern = pattern

    def get_all_serialiser_pattern(self, direct=False):
        # Returns the locally stored value by default to avoid client request
        # based load. However, a direct reading can be forced (e.g. if relevant
        # bits have been modified directly with another function).

        # Assume that modes are the same, and only read the first channel
        if direct or self._STATE_all_serialiser_pattern is None:
            # Read from ASIC and set locally stored state
            (serialiser, block_num, driver_num) = self.get_serialiserblk_from_channel(1)
            try:
                latest_value = serialiser.patternControl
            except AttributeError:
                self._read_serialiser_config(block_num)
                self._logger.warning('serialiser: {}'.format(serialiser.__repr__()))
                latest_value = serialiser.patternControl
            
            self._logger.info('read pattern directly from serialiser {} as: {}'.format(
                block_num, serialiser.patternControl))
            self._STATE_all_serialiser_pattern = latest_value

        # self._logger.warning('read pattern as {}'.format(self._STATE_all_serialiser_pattern))
        return self._STATE_all_serialiser_pattern

    def set_all_serialiser_bit_scramble(self, scrable_en):
        bypassScramble = 0 if scramble_en else 1
        
        for serialiser_number in range(1,11):
            serialiser = self._serialiser_block_configs[serialiser_number-1]
            serialiser.bypassScramble = bypassScramble
            self._write_serialiser_config(serialiser_number)

    def set_channel_serialiser_pattern(self, channel, pattern, holdoff=False):
        # Selectively set the output pattern for the serialiser associated with 
        # a channel. Note that this will affect the other channel on the same
        # control block

        if not pattern in range(0, 8):
            return ValueError('Pattern setting must be 0-7')

        serialiser_block, ser_num, drv_num = self.get_serialiserblk_from_channel(channel)

        serialiser_block.patternControl = pattern

        if not holdoff:
            self._write_serialiser_config(ser_num)

        self._logger.info('Serialiser for channel {} pattern set to {}'.format(channel, pattern))

    def set_channel_serialiser_cml_en(self, channel, enable):
        # Selectively enable or disable CML drivers enable for a given channel

        serialiser_block, ser_num, drv_num = self.get_serialiserblk_from_channel(channel)

        serialiser_block.set_cml_driver_enable(enable)

        # Force write to ASIC (no holdoff available)
        self._write_serialiser_config(ser_num)

        self._logger.info('Serialiser for channel {} CML logic enabled: {}'.format(channel, enable))

    def get_channel_serialiser_cml_en(self, channel):
        serialiser_block, ser_num, drv_num = self.get_serialiserblk_from_channel(channel)
        return serialiser_block.get_cml_driver_enable()

    def set_all_serialiser_DLL_Config(self, DLL_Config):
        if not DLL_Config in range(0, 8):
            raise ValueError('DLL Config value must be in range 0-7')

        self._logger.info("Setting dll config to {}".format(DLL_Config))
        for ser_index, ser_block in enumerate(self._serialiser_block_configs):
            ser_block.dll_config = DLL_Config
            self._write_serialiser_config(ser_index+1)

    def set_all_serialiser_DLL_phase_invert(self, DLL_Phase_Config=True):
        # True means inverted phase from nominal
        bit_value = {True: 0b0, False: 0b1}[DLL_Phase_Config]

        self._logger.info("Setting dll phase config to {}".format(bit_value))
        for ser_index, ser_block in enumerate(self._serialiser_block_configs):
            ser_block.dll_phase_config = bit_value
            self._write_serialiser_config(ser_index+1)

    def set_global_serialiser_mode(self, mode):
        # Set the mode bits for both serialisers in reg04

        if isinstance(mode, int):       # Using bits
            mode_bits = mode & 0b11
        elif isinstance(mode, str):     # Using mode name
            mode_bits = self._serialiser_mode_names[mode]

        oldbyte = self.read_register(4)[1]
        oldmasked = oldbyte & 0b11000011

        new = (oldmasked | (mode_bits << 2)) | (mode_bits << 4)
        self.write_register(4, new)

        self._STATE_serialiser_mode = mode_bits

        self._logger.info('Set serialiser mode to {} ({})'.format(
            self._STATE_serialiser_mode, mode
        ))
    
    def get_global_serialiser_mode(self, bits_only=False, direct=False):
        # Return the currently set mode. If bits_only is True, will send
        # the bit encoding rather than the name.
        # Returns the locally stored value by default to avoid client request
        # based load. However, a direct reading can be forced (e.g. if relevant
        # bits have been modified directly with another function).

        # Assume that modes are the same, and only read SERMode1xG
        if direct or self._STATE_serialiser_mode is None:
            # Read from ASIC and set locally stored state
            latest_value = (self.read_register(0x04)[1] >> 2) & 0b11
            self._STATE_serialiser_mode = latest_value

        if bits_only:
            return self._STATE_serialiser_mode
        else:
            for name, mode_bits in self._serialiser_mode_names.items():
                if mode_bits == self._STATE_serialiser_mode:
                    return name


class SerialiserBlockConfig():

    def __init__(self):
        # Simply do not return valid data if read before unpack()
        # self.data_invalid = True
        
        self._local_state_bytes = bytearray(6)

    def __repr__(self):
        outstr= ""
        try:
            outstr += "Enable CCP: {}".format(bool(self.enable_ccp))
            outstr += ", Enable CCP Initial: {}".format(bool(self.enable_ccp_initial))
            outstr += ", Low Priority CCP: {}".format(bool(self.low_priority_ccp))
            outstr += ", Strict Alignment: {}".format(bool(self.strict_alignment))
            outstr += ", Pattern Control: {}".format(self.patternControl)
            outstr += ", CCP Count: {}".format(self.ccp_count)
            outstr += ", Bypass Scramble: {}".format(bool(self.bypassScramble))
            outstr += ", CML EN: {}".format(bool(self.cml_en))
            outstr += ", DLL Config: {}".format(self.dll_config)
            outstr += ", DLL Phase Config: {}".format(self.dll_phase_config)
        except AttributeError as e:
            outstr = "No read (failed on with {})".format(e)

        return outstr

    def unpack(self, bytes_in):
        # Unpack the 6-byte field supplied as read out into config items
        bytes_in = bytearray(bytes_in)
        self._local_state_bytes = bytes_in

        # Reverse byte order so that fields spanning bytes are aligned, and
        # pack into a single value for easier slicing
        combined_fields = int.from_bytes(bytes_in, byteorder='little')

        # Slice config items
        self.enable_ccp             = (combined_fields & (0b1 << 46)) >> 46
        self.enable_ccp_initial     = (combined_fields & (0b1 << 45)) >> 45
        self.low_priority_ccp       = (combined_fields & (0b1 << 44)) >> 44
        self.strict_alignment       = (combined_fields & (0b1 << 41)) >> 41
        self.patternControl         = (combined_fields & (0b111 << 38)) >> 38
        self.ccp_count              = (combined_fields & (0b111 << 35)) >> 35
        self.bypassScramble         = (combined_fields & (0b1 << 42)) >> 42
        self.cml_en                 = (combined_fields & (0b11 << 28)) >> 28
        self.dll_config             = (combined_fields & (0b111 << 30)) >> 30
        self.dll_phase_config       = (combined_fields & (0b1 << 33)) >> 33

    def pack(self):
        # Pack config items into combined fields, without overwriting any
        # currently unsupported fields

        try:
            # Fill integer representation using current local register copy
            combined_fields = int.from_bytes(self._local_state_bytes, byteorder='little')

            # Mask off bits where supported fields exist (manually)
            #               |7     |0   |15    |8   |23    |16  |31    |24  |39    |32  |47    |40
            mask_bytes = [0b11111111, 0b11111111, 0b11111111, 0b00001111, 0b00000100, 0b10001000]
            combined_fields &= int.from_bytes(bytearray(mask_bytes), byteorder='little')

            # Overwrite supported fields
            combined_fields |= (self.enable_ccp & 0b1) << 46
            combined_fields |= (self.enable_ccp_initial &  0b1) << 45
            combined_fields |= (self.low_priority_ccp &  0b1) << 44
            combined_fields |= (self.strict_alignment & 0b1) << 41
            combined_fields |= (self.patternControl & 0b111) << 38
            combined_fields |= (self.ccp_count & 0b111) << 35
            combined_fields |= (self.bypassScramble & 0b1) << 42
            combined_fields |= (self.cml_en & 0b11) << 28
            combined_fields |= (self.dll_config & 0b111) << 30
            combined_fields |= (self.dll_phase_config & 0b1) << 33

        except AttributeError as e:
            raise AttributeError("Invalid pack; config has not been read: {} (structure: {})".format(e, self.__repr__()))

        # Repack into 6-byte little-endian config register set
        bytes_out = int.to_bytes(combined_fields, byteorder='little', length=6)

        return bytes_out

    def set_cml_driver_enable(self, driver, enabled):
        bitmask =   {1: 0b10, 2: 0b01}[driver]
        bitval =    ({1: 0b01, 2:0b10}[driver]) if enabled else 0

        old_cmlen = self.cml_en
        self.cml_en = (self.cml_en & bitmask) | bitval

    def get_cml_driver_enable(self, driver):
        bitmask =   {1: 0b01, 2:0b10}[driver]
        return (bitmask & self.cml_en) > 0
