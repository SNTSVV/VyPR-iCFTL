import datetime
from VyPR.Monitoring.online import OnlineMonitor
import logging
import test_package.vypr_config

def g():
    print("g called!")

def func1():
    for i in range(2):
        test_package.vypr_config.online_monitor.send_trigger(0, 'q')
        a = 10*(i+1)
        test_package.vypr_config.online_monitor.send_measurement(0, 1, 0, a)
        b = 20
        if b > a:
            func2()
        else:
            func2()
        g()

def func2():
    print("calling g from func2")
    ts_start = datetime.datetime.now()
    g()
    ts_end = datetime.datetime.now()
    duration = (ts_end - ts_start).total_seconds(); test_package.vypr_config.online_monitor.send_measurement(0, 0, 0, duration)

if __name__ == "__main__":
    # configure logging (inspired by stackoverflow for now)
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT)
    # start VyPR monitoring
    test_package.vypr_config.online_monitor = OnlineMonitor("tests/test-data/specifications/test1.py")
    # call test function
    func1()
    # end VyPR monitoring
    test_package.vypr_config.online_monitor.end_monitoring()
    # get verdicts
    verdicts = test_package.vypr_config.online_monitor.get_verdicts()
    # print verdicts
    print("Verdicts:")
    for map_index in verdicts:
        for formula_tree in verdicts[map_index]:
            print(f"{formula_tree.get_timestamps()} -> {formula_tree.get_configuration()}")
