"""
Module to contain the logic for performing online monitoring of an instrumented Python 3 program with respect to an iCFTL specification.
"""

#from multiprocessing import Process, Queue
from threading import Thread
from queue import Queue
import datetime
import logging
import json
from flask import g

from VyPR.Instrumentation.prepare import prepare_specification
from VyPR.Monitoring.formula_trees import FormulaTree

def monitoring_process_function(online_monitor_object, specification_file):
    """
    Consume measurements from online_monitor_object.queue.
    """
    # configure logging
    # FORMAT = '[%(asctime)-15s] [%(funcName)30s] %(message)s'
    # logging.basicConfig(format=FORMAT, filename=f"logs/monitoring/{datetime.datetime.now()}", filemode="a", level=logging.DEBUG)

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
        elif new_measurement["type"] == "get_intermediate_verdicts":
            # push the verdicts so far to the queue
            logging.info("Constructing dictionary final_map_index_to_formulas_map to contain formula trees for (complete or partial) bindings")
            final_map_index_to_formulas_map = {}
            for map_index in map_index_to_formula_trees:
                final_map_index_to_formulas_map[map_index] = []
                for formula_tree in map_index_to_formula_trees[map_index]:
                    final_map_index_to_formulas_map[map_index].append(formula_tree)
            # register the dictionary of verdicts
            logging.info("Registering complete verdicts from final_map_index_to_formulas_map")
            online_monitor_object.verdict_queue.put(final_map_index_to_formulas_map)
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
    
    # register verdicts generated by complete or partial bindings
    logging.info("Constructing dictionary final_map_index_to_formulas_map to contain formula trees for (complete or partial) bindings")
    final_map_index_to_formulas_map = {}
    for map_index in map_index_to_formula_trees:
        final_map_index_to_formulas_map[map_index] = []
        for formula_tree in map_index_to_formula_trees[map_index]:
            final_map_index_to_formulas_map[map_index].append(formula_tree)
    
    # register the dictionary of verdicts
    logging.info("Registering complete verdicts from final_map_index_to_formulas_map")
    online_monitor_object.verdict_queue.put(final_map_index_to_formulas_map)

    logging.info("Ending VyPR monitoring process.")

def verdicts_to_dictionary(verdicts):
    """
    Translate FormulaTree instances into a dictionary.
    """
    verdict_dict_list = []
    for map_index in verdicts:
        for formula_tree in verdicts[map_index]:
            verdict_entry = {"timestamp_sequence": [], "configuration": None, "observations": None}
            iso_timestamp_sequence = list(map(lambda ts : ts.isoformat(), formula_tree.get_timestamps()))
            verdict_entry["timestamp_sequence"] = iso_timestamp_sequence
            verdict_entry["configuration"] = formula_tree.get_configuration()
            verdict_entry["observations"] = formula_tree.get_measurements_dictionary()
            verdict_dict_list.append(verdict_entry)
    return verdict_dict_list

class OnlineMonitor():
    """
    Class to model an online monitoring mechanism.
    """

    def __init__(self, specification_file: str, flask_obj=None, monitor_per_request=False):
        """
        Given a specification file, read in the specification
        and set up the necessary monitor state ready to receive information from instruments,
        and set up the queue that will be used by instruments to pass measurements
        to the monitoring algorithm.

        A separate thread is started to run the monitoring loop.  This loop takes measurements
        from a queue.  These measurements are added to the queue by instruments that fire
        during a run of the monitored program.

        flask_obj is an instance of a Flask application object.  We use this to attach
        end-points to control VyPR's monitoring thread.
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

        # check to see if we're using flask
        if not flask_obj:
            # no flask, so we assume we're not dealing with a web service
            # set up the monitoring thread to run globally
            self.monitoring_process = Thread(target=monitoring_process_function, args=(self, specification_file))
            # start the process
            self.monitoring_process.start()
        else:

            # add end-points to flask_obj, depending on how monitoring will be performed
            if monitor_per_request:
                # if the monitor_per_request flag is True, we will need to instantiate a new monitoring thread
                # and tear it down per HTTP request
                @flask_obj.before_request
                def start_monitor():
                    # set request time
                    g.start_time = datetime.datetime.now()
                    # set up the monitoring process/thread
                    self.monitoring_process = Thread(target=monitoring_process_function, args=(self, specification_file))
                    # start the process/thread
                    logging.info(f"Starting monitoring thread for request at time {g.start_time.isoformat()}")
                    self.monitoring_process.start()
                    # attach self to g
                    g.vypr = self
                
                @flask_obj.after_request
                def stop_monitor(response):
                    # end the monitoring process
                    logging.info(f"Stopping monitoring thread that began at time {g.start_time}")
                    # send signal to end monitoring, join the thread and get verdicts
                    self.end_monitoring()
                    # get verdicts
                    verdicts = self.get_verdicts()
                    # translate dictionary form of verdicts
                    verdict_dictionary = verdicts_to_dictionary(verdicts)
                    # write verdicts to file (temporary)
                    with open(f"verdicts-{datetime.datetime.now().isoformat()}.json", "w") as h:
                        h.write(json.dumps(verdict_dictionary))
                    return response
            else:
                # if the monitoring_per_request flag is False, we will only use a single monitoring thread
                # across all executions
                # in this case, the vypr/get_verdicts and vypr/end_monitoring end-points are set,
                # since verdicts will be obtained by querying the monitoring thread and monitoring
                # will have to be ended by user intervention (since it is not ended when requests end).

                # set up the monitoring thread to run globally
                self.monitoring_process = Thread(target=monitoring_process_function, args=(self, specification_file))
                # start the process
                self.monitoring_process.start()

                # before every request, attach self to g
                @flask_obj.before_request
                def attach_to_g():
                    # attach self to g
                    g.vypr = self

                @flask_obj.route("/vypr/get_verdicts/")
                def get_verdicts():
                    # check to see if the monitoring process/thread is still running
                    if self.monitoring_process:
                        # send signal for verdict collection
                        self.send_verdict_collection_signal()
                        # get verdicts
                        verdicts = self.get_verdicts()
                        # translate dictionary form of verdicts
                        verdict_dictionary = verdicts_to_dictionary(verdicts)
                        return json.dumps(verdict_dictionary)
                    else:
                        return "VyPR monitoring is no longer running."
                
                @flask_obj.route("/vypr/end_monitoring/")
                def end_monitoring():
                    # check to see if the monitoring process/thread is still running
                    if self.monitoring_process:
                        # send signal to end monitoring
                        self.end_monitoring()
                        # get verdicts
                        verdicts = self.get_verdicts()
                        # translate dictionary form of verdicts
                        verdict_dictionary = verdicts_to_dictionary(verdicts)
                        return json.dumps(verdict_dictionary)
                    else:
                        return "VyPR monitoring is no longer running."

    
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
    
    def send_verdict_collection_signal(self):
        # send signal
        self.queue.put({"type": "get_intermediate_verdicts"})
        # register the verdicts
        self.register_verdicts()
    
    def end_monitoring(self):
        # send signal
        self.queue.put({"type": "stop_signal"})
        # join the process
        self.monitoring_process.join()
        # set process to None
        self.monitoring_process = None
        # register verdicts
        self.register_verdicts()