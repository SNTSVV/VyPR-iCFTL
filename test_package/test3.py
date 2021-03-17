from VyPR.Monitoring.online import OnlineMonitor
import logging
import test_package.vypr_config

def g():
    print("g called!")

def func1():
    for i in range(2):
        a = 10*(i+1)
        b = 20
        if b > a:
            #a = 20
            func2()
        else:
            func2()
        g()

def func2():
    print("calling g from func2")
    g()

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