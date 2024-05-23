provides = [
    'trigger_segment_capture',
    'set_cal_pattern_enable',
    'change_calibration_preset',
    'change_calibration_singlepixel',
    'change_calibration_grid',
]

def trigger_segment_capture(segment=20, trigger=1):
    carrier = get_context('carrier')
    carrier.set_segment_capture_triggervalue(trigger)
    carrier.set_segment_capture_selected_segment(segment)
    carrier.trigger_segment_capture()

def set_cal_pattern_enable(dis=False):
    asic = get_context('asic')
    asic.enable_calibration_test_pattern(not dis)

def change_calibration_preset(preset_name='DEFAULT'):
    carrier = get_context('carrier')
    carrier.set_calibration_pattern_preset(preset_name)
    carrier.set_calibration_pattern_mode('PRESET')

def change_calibration_singlepixel(x=1, y=1):
    carrier = get_context('carrier')
    carrier.set_calibration_pattern_single_pixel((x,y))
    carrier.set_calibration_pattern_mode('SINGLE_PIXEL')

def change_calibration_grid(x=1, y=1, cornersonly=False):
    carrier = get_context('carrier')
    carrier.set_calibration_pattern_grid_cornersonly(cornersonly)
    carrier.set_calibration_pattern_grid((x,y))
    carrier.set_calibration_pattern_mode('GRID')
