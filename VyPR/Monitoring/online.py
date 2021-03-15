"""
Module to contain the logic for performing online monitoring of an instrumented Python 3 program with respect to an iCFTL specification.
"""

from multiprocessing import Process, Queue
import datetime

from VyPR.Instrumentation.prepare import prepare_specification

def monitoring_process_function(online_monitor_object):
    """
    Consume measurements from online_monitor_object.queue.
    """
    print("[VyPR] subprocess started")
    # initialise the stop signal to False
    stop_signal_received = False
    # initialise map from map indices to lists of formula trees
    map_index_to_formula_trees = {}
    # get the list of variables from the specification
    variables = online_monitor_object.specification.get_variables()
    # loop until the end signal is received
    while not stop_signal_received:
        # get the event from the front of the queue
        new_measurement = online_monitor_object.get_new_measurement()
        # check type of measurement
        if new_measurement["type"] == "stop_signal":
            # set stop signal
            stop_signal_received = True
        elif new_measurement["type"] == "trigger":
            # get the index of the variable
            variable_index = variables.index(new_measurement["variable"])
            # get the map index
            map_index = new_measurement["map_index"]
            # if variable_index == 0, we generate a new binding/formula tree pair
            # and add map_index_to_formula_trees under the key map_index
            # if variable_index > 0, we look for existing binding/formula tree pairs
            # under the key map_index and extend the ones whose bindings are of length variable_index

            if variable_index == 0:
                # generate new binding/formula tree pair
                pass
            
            else:
                # get existing formula trees
                formula_trees = map_index_to_formula_trees[map_index]
                # iterate through the formula trees
                for formula_tree in formula_trees:
                    # decide whether we need to extend the binding attached to the formula tree
                    pass

        elif new_measurement["type"] == "measurement":
            print("processing:")
            print(new_measurement)
            # get the list of formula trees in map_index_to_formula_trees under the key map_index
            # and attempt to update each one with the measurement
            # Note: a formula tree can only be updated with respect to a measurement once - if the update is attempted
            # again, the formula tree will refuse the update

            # get all relevant formula trees
            formula_trees = map_index_to_formula_trees[map_index]

            # attempt to update each formula tree with the measurement received
    
    print("[VyPR] subprocess ending")
        

class OnlineMonitor():
    """
    Class to model an online monitoring mechanism.
    """

    def __init__(self, specification_file: str):
        """
        Given a specification file, read in the specification
        and set up the necessary monitor state ready to receive information from instruments,
        and set up the queue that will be used by instruments to pass measurements
        to the monitoring algorithm.

        A separate process is started to run the monitoring loop.  This loop takes measurements
        from a queue.  These measurements are added to the queue by instruments that fire
        during a run of the monitored program.
        """
        # read in the specification
        self.specification = prepare_specification(specification_file)
        # set up queue
        self.queue = Queue()
        # set up the separate process
        self.monitoring_process = Process(target=monitoring_process_function, args=(self,))
        # start the process
        self.monitoring_process.start()
    
    def get_new_measurement(self):
        return self.queue.get()
    
    def send_measurement(self, map_index, atom_index, subatom_index, measurement):
        self.queue.put({
            "type": "measurement",
            "timestamp": datetime.datetime.now(),
            "map_index": map_index,
            "atom_index": atom_index,
            "subatom_index": subatom_index,
            "measurement": measurement
        })
    
    def send_trigger(self, map_index, variable):
        self.queue.put({
            "type": "trigger",
            "map_index": map_index,
            "variable": variable
        })
    
    def end_monitoring(self):
        # send signal
        self.queue.put({"type": "stop_signal"})
        # join the process
        self.monitoring_process.join()