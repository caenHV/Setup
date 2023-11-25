from caen_setup import Handler
import time
import json

h = Handler('test_config.json', dev_mode=True)
results: dict = dict()

def test1(handler: Handler):
    """ Get params (check the connection).
    """
    results['test1'] = handler.get_params(None, None)
    print('test 1: query')
    return

def test2(handler: Handler):
    """ Set voltage (500 V) -> Wait 2 minutes (query the setup every 15 sec) -> pw_down -> query
    """
    handler.set_voltage(None, 500)
    print('500 V voltage was set.')
    for i in range(8):
        time.sleep(15)
        results[f'test2_{(i + 1) * 15}_sec'] = handler.get_params(None, None)
        print(f'test 2: query after {(i + 1) * 15} sec')
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
        print(f'test 3: query 1 for {volt} V')
        results[f'test3_query_1_{volt}_V'] = handler.get_params(None, None)
        time.sleep(10)
        print(f'test 3: query 2 for {volt} V')
        results[f'test3_query_2_{volt}_V'] = handler.get_params(None, None)
    
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
        results[f'test4_{(i + 1) * 15}_sec'] = handler.get_params(None, None)
        print(f'test 4: query after {(i + 1) * 15} sec')
    handler.pw_down(None)
    print('Power was cut off.')
    print('final query:', handler.get_params(None, None))
    return

with open('res.json', 'w+') as f:
    json.dump(results, f, indent=4)
    