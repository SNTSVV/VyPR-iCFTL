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
    # configure logging
    FORMAT = '[%(asctime)-15s] [%(funcName)30s] %(message)s'
    logging.basicConfig(format=FORMAT, filename=f"logs/monitoring/{datetime.datetime.now()}", filemode="a", level=logging.DEBUG)

    logging.info("Starting VyPR monitoring process.")
    # read in the specification
    specification = prepare_specification(specification_file)
    logging.info("Reading in specification from file %s" % specification_file)
    # initialise the stop signal to False
    stop_signal_received = False
    # initialise map from map indices to lists of formula trees
    logging.info("Initialising empty dictionary map_index_to_formula_trees")
    map_index_to_formula_trees = {}
    # get the list of variables from the specification
    logging.info("Getting list of variables from specification")
    variables = specification.get_variables()
    logging.info("Sequence of variables in specification is %s" % str(variables))
    # loop until the end signal is received
    logging.info("Beginning monitoring loop - loop while stop_signal_received is False")
    while not stop_signal_received:
        # get the event from the front of the queue
        new_measurement = online_monitor_object.get_new_measurement()
        # check type of measurement
        if new_measurement["type"] == "stop_signal":
            # set stop signal
            logging.info("Received stop signal instrument")
            stop_signal_received = True
            logging.info("stop_signal_received = %s" % stop_signal_received)
        elif new_measurement["type"] == "trigger":
            logging.info("Received trigger instrument")
            logging.info("  map_index = %s" % new_measurement["map_index"])
            logging.info("  variable = %s" % new_measurement["variable"])
            # get timestamp for this trigger
            logging.info("Getting timestamp to be used in new formula tree")
            trigger_timestamp = datetime.datetime.now()
            # get the index of the variable
            logging.info("Getting index of variable in sequence of variables")
            variable_index = variables.index(new_measurement["variable"])
            # get the map index
            map_index = new_measurement["map_index"]
            logging.info("variable_index = %i" % variable_index)
            # check for an existing list of formula trees with this index
            if not map_index_to_formula_trees.get(map_index):
                logging.info("Initialising empty set of formula trees in map_index_to_formula_trees for map_index = %i" % map_index)
                map_index_to_formula_trees[map_index] = []
            # if variable_index == 0, we generate a new binding/formula tree pair
            # and add map_index_to_formula_trees under the key map_index
            # if variable_index > 0, we look for existing binding/formula tree pairs
            # under the key map_index and extend the ones whose bindings are of length variable_index

            # get the constraint held by the specification
            logging.info("Getting constraint part of specification ready for formula tree instantiation")
            constraint = specification.get_constraint()
            logging.info("Got constraint = %s from specification" % str(constraint))

            # check the variable index
            if variable_index == 0:
                logging.info("Instantiating new formula tree with timestamp %s" % str(trigger_timestamp))
                # construct a sequence consisting of a single timestamp
                logging.info("Constructing list containing a single timestamp")
                current_timestamp_sequence = [trigger_timestamp]
                # generate new binding/formula tree pair
                new_formula_tree = FormulaTree(current_timestamp_sequence, constraint, variables)
                logging.info("New formula tree %s instantiated" % str(new_formula_tree))
                # add to the appropriate list of formula trees
                logging.info("Adding formula tree to map_index_to_formula_trees")
                map_index_to_formula_trees[map_index].append(new_formula_tree)
            else:
                logging.info("Instantiating formula tree using existing ones in map_index_to_formula_trees")
                # get existing formula trees
                formula_trees = map_index_to_formula_trees[map_index]
                # iterate through the formula trees
                for formula_tree in formula_trees:
                    # decide whether we need to extend the binding attached to the formula tree
                    logging.info("Inspecting formula tree %s" % formula_tree)
                    # get the timestamp sequence from the formula tree
                    timestamps = formula_tree.get_timestamps()
                    # check whether the length of the timestamp sequence is equal to variable_index
                    if len(timestamps) == variable_index:
                        logging.info("Using state in formula tree %s to instantiate a new one" % formula_tree)
                        # generate an extended timestamp sequence
                        extended_timestamp_sequence = [t for t in timestamps] + [trigger_timestamp]
                        logging.info("extended_timestamp_sequence = %s" % extended_timestamp_sequence)
                        # get the assignment of atoms/expressions to measurements from formula_tree
                        measurements = formula_tree.get_measurements_for_variable_index(variable_index)
                        logging.info("measurements = %s" % measurements)
                        # instantiate new formula tree with the extended timestamp sequence, and the measurements
                        # associated with variables from the old formula tree
                        extended_formula_tree = FormulaTree(extended_timestamp_sequence, constraint, variables, measurements)
                        logging.info("extended_formula_tree = %s" % str(extended_formula_tree))
                        # store the new formula tree
                        map_index_to_formula_trees[map_index].append(extended_formula_tree)
                        logging.info("New formula tree added to map_index_to_formula_trees")

        elif new_measurement["type"] == "measurement":
            logging.info("Received measurement instrument")
            # extract relevant values
            measurement = new_measurement["measurement"]
            map_index = new_measurement["map_index"]
            atom_index = new_measurement["atom_index"]
            subatom_index = new_measurement["subatom_index"]
            logging.info("  measurement = %s" % measurement)
            logging.info("  map_index =  %s" % map_index)
            logging.info("  atom_index = %s" % atom_index)
            logging.info("  subatom_index = %s" % subatom_index)
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
    
    # register verdicts generated by complete bindings
    logging.info("Constructing dictionary final_map_index_to_formulas_map to contain formula trees for complete bindings")
    final_map_index_to_formulas_map = {}
    for map_index in map_index_to_formula_trees:
        final_map_index_to_formulas_map[map_index] = []
        for formula_tree in map_index_to_formula_trees[map_index]:
            # to check for 'complete bindings', we check for timestamp sequences that have as
            # many elements as there are variables in the specification (since each timestamp corresponds
            # to an observation for a single variable)
            if len(formula_tree.get_timestamps()) == len(variables):
                logging.info("%s is associated with a complete binding" % formula_tree)
                final_map_index_to_formulas_map[map_index].append(formula_tree)
    
    # register the dictionary of verdicts
    logging.info("Registering complete verdicts from final_map_index_to_formulas_map")
    online_monitor_object.verdict_queue.put(final_map_index_to_formulas_map)

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
        logging.info("Initialising empty dictionary to store final formula trees")
        self._map_index_to_formula_trees = {}
        # set up queue for subprocess to read from
        logging.info("Initialising buffer queue for communication between monitored program")
        self.queue = Queue()
        # set up queue for subprocess to write verdicts to
        logging.info("Initialising verdict queue for final verdicts")
        self.verdict_queue = Queue()
        # set up the separate process
        logging.info("Instantiating process for monitoring")
        self.monitoring_process = Process(target=monitoring_process_function, args=(self, specification_file))
        # start the process
        logging.info("Starting monitoring subprocess")
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