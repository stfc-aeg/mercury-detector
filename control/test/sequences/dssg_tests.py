import time
requires = ['asic_spi']
provides = ['test_time_difference', 'test_proxy_adapter']

def test_time_difference(time_difference=0.001):
    print("This test will check difference if 1ms delay is introduced between each ASIC SPI read")

    print("Beginning baseline test of 40000 samples:")
    baseline_starttime = time.time()
    store_sector_readout(sector_samples=40000, sector_array=[9], vcal_values=[1.0], test_name='time_delay_impacttest', test_index=0, suppress_progress_update=False, timesleep=0.0)
    baseline_finishtime = time.time()
    print("\n Test took {}s to complete".format(baseline_finishtime - baseline_starttime))

    print("Beginning {}s delay test of 40000 samples:".format(time_difference))
    delayed_starttime = time.time()
    store_sector_readout(sector_samples=40000, sector_array=[9], vcal_values=[1.0], test_name='time_delay_impacttest', test_index=time_difference, suppress_progress_update=False, timesleep=time_difference)
    delayed_finishtime = time.time()
    print("\n Test took {}s to complete".format(delayed_finishtime - delayed_starttime))

    time_impact = (delayed_finishtime - delayed_starttime) - (baseline_finishtime - baseline_starttime)
    print("\nA delay of {}s impacted the full read by {}, or {}%".format(
        time_difference, time_impact,
        (time_impact / (baseline_finishtime - baseline_starttime)) * 100))


def test_proxy_adapter():
    pass
