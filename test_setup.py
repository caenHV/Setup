from caen_setup import Handler


h = Handler('test_config.json', dev_mode=True)
h.set_voltage(None, 1000)