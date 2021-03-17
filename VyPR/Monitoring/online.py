"""
Module to contain the logic for performing online monitoring of an instrumented Python 3 program with respect to an iCFTL specification.
"""

from multiprocessing import Process, Queue
import datetime
import logging

from VyPR.Instrumentation.prepare import prepare_specification
from VyPR.Monitoring.formula_trees import FormulaTree

def monitoring_process_function(online_monitor_object, specification_file):
    """
    Consume measurements from online_monitor_object.queue.
    """
    print("[VyPR] subprocess started")
    # read in the specification
    specification = prepare_specification(specification_file)
    # initialise the stop signal to False
    stop_signal_received = False
    # initialise map from map indices to lists of formula trees
    map_index_to_formula_trees = {}
    # get the list of variables from the specification
    variables = specification.get_variables()
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
            # check for an existing list of formula trees with this index
            if not map_index_to_formula_trees.get(map_index):
                map_index_to_formula_trees[map_index] = []
            # if variable_index == 0, we generate a new binding/formula tree pair
            # and add map_index_to_formula_trees under the key map_index
            # if variable_index > 0, we look for existing binding/formula tree pairs
            # under the key map_index and extend the ones whose bindings are of length variable_index

            if variable_index == 0:
                # get the current timestamp
                current_timestamp = datetime.datetime.now()
                # construct a sequence consisting of a single timestamp
                current_timestamp_sequence = [current_timestamp]
                # get the constraint held by the specification
                constraint = specification.get_constraint()
                # generate new binding/formula tree pair
                new_formula_tree = FormulaTree(current_timestamp_sequence, constraint)
                # add to the appropriate list of formula trees
                map_index_to_formula_trees[map_index].append(new_formula_tree)
            else:
                # get existing formula trees
                formula_trees = map_index_to_formula_trees[map_index]
                # iterate through the formula trees
                for formula_tree in formula_trees:
                    # decide whether we need to extend the binding attached to the formula tree
                    pass

        elif new_measurement["type"] == "measurement":
            # extract relevant values
            measurement = new_measurement["measurement"]
            map_index = new_measurement["map_index"]
            atom_index = new_measurement["atom_index"]
            subatom_index = new_measurement["subatom_index"]
            # get the list of formula trees in map_index_to_formula_trees under the key map_index
            # and attempt to update each one with the measurement
            # Note: a formula tree can only be updated with respect to a measurement once - if the update is attempted
            # again, the formula tree will refuse the update

            # get all relevant formula trees
            formula_trees = map_index_to_formula_trees[map_index]

            # attempt to update each formula tree with the measurement received
            for (index, formula_tree) in enumerate(formula_trees):
                # update the formula tree
                updated_formula_tree = formula_tree.update_with_measurement(measurement, atom_index, subatom_index)
    
    print("[VyPR] subprocess ending")

    print("Verdicts:")

    # print verdicts
    for map_index in map_index_to_formula_trees:
        for formula_tree in map_index_to_formula_trees[map_index]:
            print(f"{formula_tree.get_timestamps()} -> {formula_tree.get_configuration()}")
        

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
        # set up queue
        self.queue = Queue()
        # set up the separate process
        self.monitoring_process = Process(target=monitoring_process_function, args=(self, specification_file))
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