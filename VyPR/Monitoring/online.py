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
    # configure logging (inspired by stackoverflow for now)
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT, filename=f"logs/monitoring/{datetime.datetime.now()}", filemode="a", level=logging.DEBUG)

    logging.info("Starting VyPR monitoring process.")
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
            logging.info("Received stop signal - setting stop flag")
            stop_signal_received = True
        elif new_measurement["type"] == "trigger":
            # get the index of the variable
            variable_index = variables.index(new_measurement["variable"])
            # get the map index
            map_index = new_measurement["map_index"]
            logging.info(f"Received trigger instrument with variable_index = {variable_index}, map_index = {map_index}")
            # check for an existing list of formula trees with this index
            if not map_index_to_formula_trees.get(map_index):
                map_index_to_formula_trees[map_index] = []
            # if variable_index == 0, we generate a new binding/formula tree pair
            # and add map_index_to_formula_trees under the key map_index
            # if variable_index > 0, we look for existing binding/formula tree pairs
            # under the key map_index and extend the ones whose bindings are of length variable_index

            # get the constraint held by the specification
            constraint = specification.get_constraint()

            # check the variable index
            if variable_index == 0:
                # get the current timestamp
                current_timestamp = datetime.datetime.now()
                logging.info(f"Instantiating new formula tree with timestamp {current_timestamp}")
                # construct a sequence consisting of a single timestamp
                current_timestamp_sequence = [current_timestamp]
                # generate new binding/formula tree pair
                new_formula_tree = FormulaTree(current_timestamp_sequence, constraint, variables)
                # add to the appropriate list of formula trees
                map_index_to_formula_trees[map_index].append(new_formula_tree)
            else:
                print("processing", variable_index)
                logging.info(f"Instantiating formula tree using existing ones")
                # get existing formula trees
                formula_trees = map_index_to_formula_trees[map_index]
                # iterate through the formula trees
                for formula_tree in formula_trees:
                    # decide whether we need to extend the binding attached to the formula tree
                    logging.info(f"Inspecting formula tree {formula_tree}")
                    # get the timestamp sequence from the formula tree
                    timestamps = formula_tree.get_timestamps()
                    # check whether the length of the timestamp sequence is equal to variable_index
                    if len(timestamps) == variable_index:
                        # generate an extended timestamp sequence
                        extended_timestamp_sequence = [t for t in timestamps] + [datetime.datetime.now()]
                        # get the assignment of atoms/expressions to measurements from formula_tree
                        measurements = formula_tree.get_measurements_for_variable_index(variable_index)
                        # get the
                        # instantiate new formula tree with the extended timestamp sequence, and the measurements
                        # associated with variables from the old formula tree
                        extended_formula_tree = FormulaTree(extended_timestamp_sequence, constraint, variables, measurements)
                        # store the new formula tree
                        map_index_to_formula_trees[map_index].append(extended_formula_tree)

        elif new_measurement["type"] == "measurement":
            # extract relevant values
            measurement = new_measurement["measurement"]
            map_index = new_measurement["map_index"]
            atom_index = new_measurement["atom_index"]
            subatom_index = new_measurement["subatom_index"]
            logging.info(f"Received measurment instrument with measurement = {measurement}, map_index = {map_index}, atom_index = {atom_index}, subatom_index = {subatom_index}")
            # get the list of formula trees in map_index_to_formula_trees under the key map_index
            # and attempt to update each one with the measurement
            # Note: a formula tree can only be updated with respect to a measurement once - if the update is attempted
            # again, the formula tree will refuse the update

            # get all relevant formula trees
            formula_trees = map_index_to_formula_trees[map_index]

            # attempt to update each formula tree with the measurement received
            for (index, formula_tree) in enumerate(formula_trees):
                # update the formula tree
                logging.info(f"Updating formula tree {formula_tree} with measurement = {measurement}")
                updated_formula_tree = formula_tree.update_with_measurement(measurement, atom_index, subatom_index)
    
    # register verdicts
    online_monitor_object.verdict_queue.put(map_index_to_formula_trees)

    logging.info("Ending VyPR monitoring process.")

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
        # set up verdict dictionary ready for the monitoring algorithm to send verdicts
        self._map_index_to_formula_trees = {}
        # set up queue for subprocess to read from
        self.queue = Queue()
        # set up queue for subprocess to write verdicts to
        self.verdict_queue = Queue()
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
    
    def register_verdicts(self):
        self._map_index_to_formula_trees = self.verdict_queue.get()
    
    def get_verdicts(self):
        return self._map_index_to_formula_trees
    
    def end_monitoring(self):
        # send signal
        self.queue.put({"type": "stop_signal"})
        # join the process
        self.monitoring_process.join()
        # register verdicts
        self.register_verdicts()