from caen_setup import Handler
import time

h = Handler('test_config.json', dev_mode=True)

def test1(handler: Handler):
    """ Get params (check the connection).
    """
    print(handler.get_params(None, None))
    return

def test2(handler: Handler):
    """ Set voltage (500 V) -> Wait 2 minutes (query the setup every 15 sec) -> pw_down -> query
    """
    handler.set_voltage(None, 1000)
    print('1000 V voltage was set.')
    for i in range(8):
        time.sleep(15)
        print(f'query after {(i + 1) * 15} sec:', handler.get_params(None, None))
    handler.pw_down(None)
    print('Power was cut off.')
    print('final query:', handler.get_params(None, None))
    return

def test3(handler: Handler):
    """ Set voltage gradually (100 V -> 500 V -> 1000 V -> 2000 V; -> == Set voltage + query + wait 10 secs + query) -> pw_down -> query
    """
    voltages = (100, 500, 1000, 2000)
    for volt in voltages:
        handler.set_voltage(None, volt)
        print(f'{volt} V voltage was set.')
        print(f'query 1 for {volt} V:', handler.get_params(None, None))
        time.sleep(10)
        print(f'query 2 for {volt} V:', handler.get_params(None, None))
    
    handler.pw_down(None)
    print('Power was cut off.')
    print('final query:', handler.get_params(None, None))
    return

def test4(handler: Handler):
    """ Set voltage -> Wait 2 hours (query the setup every 2 minutes) -> pw_down -> query
    """
    handler.set_voltage(None, 2000)
    print('2000 V voltage was set.')
    for i in range(480):
        time.sleep(15)
        print(f'query after {(i + 1) * 15} sec:', handler.get_params(None, None))
    handler.pw_down(None)
    print('Power was cut off.')
    print('final query:', handler.get_params(None, None))
    return