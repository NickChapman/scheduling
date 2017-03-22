"""
Created by Nick Chapman
March 22, 2017
nlc35 at georgetown dot edu
"""

import sys
import re
import os
import queue
from collections import deque

# CONSTANTS and GLOBAL VALUES

allowed_algos = ["RR", "SJF", "SJR"]
global_average_burst_time = [0]
global_burst_count = [0]


# HELPERS

def print_states(*states):
    for state in states:
        print(state)


# PROGRAM CONTROL

def usage_error():
    print("You have called this program incorrectly!", file=sys.stderr)
    print("Usage: python <scheduling algorithm> [optional algorithm parameter] [verbose] <process time file n>*",
          file=sys.stderr)
    print(
        "Allowed scheduling algorithms:\n\tRR - Round Robin\n\tSJR - Shortest Job Remaining\n\tSJF - Shortest Job First",
        file=sys.stderr)
    exit(1)


def main():
    # Strip off the program name since we don't care about that
    arguments = sys.argv[1:]
    try:
        current_arg_num = 0
        algorithm = arguments[current_arg_num]
        if algorithm not in allowed_algos:
            usage_error()
        current_arg_num += 1
        if algorithm == "RR":
            time_quantum = int(arguments[current_arg_num])
            current_arg_num += 1
        if arguments[current_arg_num] == "verbose":
            verbose = True
            current_arg_num += 1
            process_files = arguments[current_arg_num:]
        else:
            verbose = False
            process_files = arguments[current_arg_num:]
        if len(process_files) == 0:
            print("You must specify at least one process file", file=sys.stderr)
            exit(1)
    except IndexError:
        usage_error()
    except ValueError:
        print("The time quantum must be an integer", file=sys.stderr)
        usage_error()
    except:
        print("An error has occurred. The likely cause is below.", file=sys.stderr)
        usage_error()
    # We have parsed the arguments without error
    processes = [Process(process_file) for process_file in process_files]
    # Check to make sure that none of the processes start out blocked since that would be an error
    for process in processes:
        if process.state_queue.peek()[0] == "I":
            print("Process " + str(process.process_number) + " starts in a blocked state which is nonsensical!")
            exit(1)
    if algorithm == "RR":
        round_robin(processes, time_quantum, verbose)
    elif algorithm == "SJF":
        shortest_job_first(processes, verbose)
    elif algorithm == "SJR":
        shortest_job_remaining(processes, verbose)
    else:
        # We have somehow reached an error state
        print("An error has occurred. The likely cause is below.", file=sys.stderr)
        usage_error()


# ALGORITHMS


def round_robin(processes, time_quantum, verbose=False):
    # Push all of the processes into the start queue where they will wait until they're started
    start_queue = ProcessQueue()
    for process in processes:
        start_queue.push_back((process.start, process))

    # Sort processes based on start time
    start_queue = ProcessQueue(sorted(start_queue, key=lambda x: x[0]))
    process_queue = ProcessQueue()
    current_time = 0

    if verbose:
        print("Time 0: Waiting for first process to arrive")

    # Pull the first items out of the start queue
    while process_queue.empty:
        while start_queue.not_empty and start_queue.peek()[1].start == current_time:
            process_queue.push_back(start_queue.pop_front())
        if process_queue.empty:
            current_time += 1

    if verbose:
        print("Time " + str(current_time) + ": Process(es) have arrived")
        print("Current process queue: " + process_queue.single_line_string())
    if current_time != 0:
        print("Idle 0 " + str(current_time))

    # Begin RR loop
    blocked_count = 0  # Number of processes in a row that have been blocked
    last_execution_time = current_time
    while process_queue.not_empty or start_queue.not_empty:
        # See if we need to load something from the start queue
        if verbose:
            print("Time " + str(current_time) + ": Checking if process needs to be loaded from start queue...", end="")
        if process_queue.empty:
            # Need to load from start queue
            if verbose:
                print("yes")
                print("Time 0: Waiting for first process to arrive")

            # Pull the first items out of the start queue
            while process_queue.empty:
                while start_queue.not_empty and start_queue.peek()[1].start == current_time:
                    process_queue.push_back(start_queue.pop_front())
                if process_queue.empty:
                    current_time += 1

            if verbose:
                print("Time " + str(current_time) + ": Process(es) have arrived")
                print("Current process queue: " + process_queue.single_line_string())
        else:
            if verbose:
                print("no")
        start_time = current_time
        waiting_since, process = process_queue.pop_front()
        process_state = process.state_queue.pop_front()
        if process_state[0] == "B":
            blocked_count = 0
            # Check to see if we were idle for any period of time leading up to this
            if current_time - last_execution_time > 0:
                print("Idle " + str(last_execution_time) + " " + str(current_time))
            # We are in the middle of a burst
            if process_state[1] > time_quantum:
                process.state_queue.push_front(("B", process_state[1] - time_quantum))
                current_time += time_quantum
                print(str(process.process_number) + " " + str(start_time) + " " + str(current_time))
            elif process_state[1] == time_quantum:
                current_time += time_quantum
                print(str(process.process_number) + " " + str(start_time) + " " + str(current_time))
            else:
                # The whole burst isn't needed
                current_time += process_state[1]
                print(str(process.process_number) + " " + str(start_time) + " " + str(current_time))
            last_execution_time = current_time
            # If the process has more work to do put it back into the queue
            if process.state_queue.not_empty:
                process_queue.push_back((current_time, process))
            else:
                # The process has finished
                if verbose:
                    print("Time " + str(current_time) + ": " + str(process) + " finished")
        else:
            # First check to see if it has waited long enough to no longer be blocked
            if verbose:
                print("Time " + str(current_time) + ": Determining if " + str(process) + " is blocked...", end="")
            if current_time - waiting_since > process_state[1] and len(process.state_queue) > 0:
                # It became unblocked while waiting, but it back on the beginning of the queue
                process_queue.push_front((current_time, process))
                blocked_count = 0
                if verbose:
                    print("unblocked")
            elif current_time - waiting_since == process_state[1] and len(process.state_queue) > 0:
                # It is just this moment becoming unblocked, put it at the back of the queue
                process_queue.push_back((current_time, process))
                blocked_count = 0
                if verbose:
                    print("unblocked")
            elif current_time - waiting_since >= process_state[1] and len(process.state_queue) == 0:
                # The process finished on an IO request and do nothing
                if verbose:
                    print("unblocked and process finished")
            else:
                # It hasn't waited long enough and yields its turn
                if verbose:
                    print("blocked")
                # Put this state back into its state queue
                process.state_queue.push_front(process_state)
                process_queue.push_back((waiting_since, process))
                blocked_count += 1
                if blocked_count >= len(process_queue):
                    # All processes are blocked
                    current_time += 1
                    blocked_count = 0
        if start_queue.not_empty and start_time != current_time:
            # Check to see if any processes arrived while we were dealing with that process
            if verbose:
                print("Time " + str(current_time) + ": Checking to see if new processes arrived while running burst...",
                      end="")
            new_procs = False
            while start_queue.not_empty and start_queue.peek()[1].start <= current_time:
                process_queue.push_back(start_queue.pop_front())
                new_procs = True
            if verbose:
                if new_procs:
                    print("yes")
                else:
                    print("no")
            if verbose:
                print("Time " + str(current_time) + ": Current process queue: " + process_queue.single_line_string())
    print("end")


def shortest_job_first(processes, verbose=False):
    current_time = 0
    # Push all of the processes into the start queue where they will wait until they're started
    start_state = StartPool()
    for process in processes:
        start_state.add(process)

    # Create our states used for the actual running of the algorithm
    ready_state = ReadyPool()
    blocked_state = BlockedPool()

    if verbose:
        print("Time 0: Waiting for first process to arrive")
    while ready_state.empty:
        # We need to go and get some processes
        ready_processes = start_state.get_ready_processes(current_time)
        if not ready_processes:
            # There are no ready processes in this case
            current_time += 1
        else:
            for process in ready_processes:
                process.start_process()
                ready_state.add(process)
    if verbose:
        print("Time " + str(current_time) + ": Process(es) have arrived")
        print_states(start_state, ready_state, blocked_state)

    if current_time != 0:
        print("Idle 0 " + str(current_time))

    # Begin main loop
    last_execution_time = current_time
    while ready_state.not_empty or blocked_state.not_empty or start_state.not_empty:
        start_time = current_time
        # Let's first see if we have something that we can run
        if verbose:
            print("Time " + str(current_time) + ": checking if any processes are ready...", end="")
        if ready_state.not_empty:
            # We can run something
            process = ready_state.get_next_ready_process()
            if verbose:
                print("yes. Running " + str(process))
            if last_execution_time != current_time:
                print("Idle " + str(last_execution_time) + " " + str(current_time))
            burst_time = process.run_full_burst()
            # Update the blocked state to reflect this burst happening
            if verbose:
                print("Time " + str(current_time) + ": Updating blocked state to reflect completion of burst")
            ready_processes = blocked_state.update(burst_time)
            if verbose:
                print("Time " + str(current_time) + ": Adding " + str(
                    len(ready_processes)) + " process(es) to the ready state")
            for ready_process in ready_processes:
                if ready_process.state_queue.empty:
                    if verbose:
                        print("Time " + str(current_time) + ": " + str(ready_process) + " finished")
                else:
                    ready_state.add(ready_process)
            current_time += burst_time
            last_execution_time = current_time
            print(str(process.process_number) + " " + str(start_time) + " " + str(current_time))
            # Now put the process into the appropriate pool or let it die since it is finished
            if process.state_queue.empty:
                # The process has finished everything it needs to do
                if verbose:
                    print("Time " + str(current_time) + ": " + str(process) + " finished")
            elif process.state_queue.peek()[0] == "B":
                # Another burst is queued up for some reason (this is dumb but whatever)
                if verbose:
                    print("Time " + str(current_time) + ": " + str(process) + " moved to ready state")
                ready_state.add(process)
            else:
                # It must now be blocked
                if verbose:
                    print("Time " + str(current_time) + ": " + str(process) + " moved to blocked state")
                blocked_state.add(process)
            if verbose:
                print("Time " + str(current_time) + ":")
                print_states(start_state, ready_state, blocked_state)
        else:
            # If we reach here that means nothing is ready yet
            # Let's update the blocked pool and see if something comes out
            if verbose:
                print("no")
                print_states(start_state, ready_state, blocked_state)
            current_time += 1
            if verbose:
                print("Time " + str(current_time) + ": Updating blocked state for timestep of 1")
            ready_processes = blocked_state.update(1)
            if verbose:
                print("Time " + str(current_time) + ": Adding " + str(
                    len(ready_processes)) + " process(es) to the ready state")
            for ready_process in ready_processes:
                if ready_process.state_queue.empty:
                    if verbose:
                        print("Time " + str(current_time) + ": " + str(ready_process) + " finished")
                else:
                    ready_state.add(ready_process)
            if verbose:
                print("Time " + str(current_time) + ":")
                print_states(start_state, ready_state, blocked_state)
        # Finally check whether we need to add in any potentially started states
        if start_state.not_empty:
            if verbose:
                print("Time " + str(current_time) + ": Checking if any new processes started...", end="")
            ready_processes = start_state.get_ready_processes(current_time)
            if not ready_processes:
                if verbose:
                    print("no")
            else:
                if verbose:
                    print("yes")
                    print("Time " + str(current_time) + ": Adding " + str(
                        len(ready_processes)) + " process(es) to ready state")
                for process in ready_processes:
                    process.start_process()
                    ready_state.add(process)
                if verbose:
                    print("Time " + str(current_time) + ":")
                    print_states(start_state, ready_state, blocked_state)
    print("end")


def shortest_job_remaining(processes, verbose=False):
    current_time = 0
    # Push all of the processes into the start queue where they will wait until they're started
    start_state = StartPool()
    for process in processes:
        start_state.add(process)

    # Create our states used for the actual running of the algorithm
    ready_state = ReadyPool()
    blocked_state = BlockedPool()

    if verbose:
        print("Time 0: Waiting for first process to arrive")
    while ready_state.empty:
        # We need to go and get some processes
        ready_processes = start_state.get_ready_processes(current_time)
        if not ready_processes:
            # There are no ready processes in this case
            current_time += 1
        else:
            for process in ready_processes:
                process.start_process()
                ready_state.add(process)
    if verbose:
        print("Time " + str(current_time) + ": Process(es) have arrived")
        print_states(start_state, ready_state, blocked_state)

    if current_time != 0:
        print("Idle 0 " + str(current_time))

    # Begin main loop
    last_execution_time = current_time
    while ready_state.not_empty or blocked_state.not_empty or start_state.not_empty:
        start_time = current_time
        # Let's see if anything can run
        if verbose:
            print("Time " + str(current_time) + ": checking if any processes are ready...", end="")
        if ready_state.not_empty:
            # We can run something
            process = ready_state.get_next_ready_process()
            if verbose:
                print("yes. Running " + str(process))
            # Check if we were idle and if we were then print that
            if last_execution_time - current_time != 0:
                print("Idle " + str(last_execution_time) + " " + str(current_time))
            # We are going to run this process 1 time step at a time to see if anything better comes along
            changed = False
            while not changed:
                burst_completed = process.run_partial_burst(1)
                current_time += 1
                last_execution_time = current_time
                if burst_completed:
                    changed = True
                    break
                else:
                    # Put the process back into the ready state
                    ready_state.add(process)
                # Update the time by 1 and update the ready state from the blocked and start states
                if verbose:
                    print("Time " + str(
                        current_time) + ": Checking if any processes need to move from blocked to ready...", end="")
                ready_processes = blocked_state.update(1)
                if ready_processes:
                    if verbose:
                        print("yes")
                        print("Time " + str(current_time) + ": Adding " + str(len(ready_processes)) + " to ready state")
                    for ready_process in ready_processes:
                        ready_state.add(ready_process)
                else:
                    if verbose:
                        print("no")
                if verbose:
                    print("Time " + str(
                        current_time) + ": Checking if any processes need to move from start to ready...", end="")
                ready_processes = start_state.get_ready_processes(current_time)
                if ready_processes:
                    if verbose:
                        print("yes")
                        print("Time " + str(current_time) + ": Adding " + str(len(ready_processes)) + " to ready state")
                    for ready_process in ready_processes:
                        ready_process.start_process()
                        ready_state.add(ready_process)
                else:
                    if verbose:
                        print("no")
                if verbose:
                    print("Time " + str(current_time) + ":")
                    print_states(start_state, ready_state, blocked_state)
                    print("Time " + str(current_time) + ": Checking if we continue with same process as before...",
                          end="")
                new_process = ready_state.get_next_ready_process()
                if new_process.process_number != process.process_number:
                    changed = True
                    # Put it back in the pool to get out in a second
                    ready_state.add(new_process)
                    if verbose:
                        print("no")
                else:
                    if verbose:
                        print("yes")
                    process = new_process
            print(str(process.process_number) + " " + str(start_time) + " " + str(current_time))
            if process.state_queue.empty:
                if verbose:
                    print("Time " + str(current_time) + ": " + str(process) + " finished")
            else:
                if process.state_queue.peek()[0] == "B":
                    if verbose:
                        print("Time " + str(current_time) + ": Moving " + str(process) + " to ready state")
                    ready_state.add(process)
                else:
                    if verbose:
                        print("Time " + str(current_time) + ": Moving " + str(process) + " to blocked state")
                    blocked_state.add(process)
        else:
            # The ready state is empty so we need to step in time and see if we can free anything
            current_time += 1
            if verbose:
                print("Time " + str(
                    current_time) + ": Checking if any processes need to move from blocked to ready...", end="")
            ready_processes = blocked_state.update(1)
            if ready_processes:
                if verbose:
                    print("yes")
                    print("Time " + str(current_time) + ": Adding " + str(len(ready_processes)) + " to ready state")
                for ready_process in ready_processes:
                    ready_state.add(ready_process)
            else:
                if verbose:
                    print("no")
            if verbose:
                print("Time " + str(
                    current_time) + ": Checking if any processes need to move from start to ready...", end="")
            ready_processes = start_state.get_ready_processes(current_time)
            if ready_processes:
                if verbose:
                    print("yes")
                    print("Time " + str(current_time) + ": Adding " + str(len(ready_processes)) + " to ready state")
                for ready_process in ready_processes:
                    ready_process.start_process()
                    ready_state.add(ready_process)
            else:
                if verbose:
                    print("no")
            if verbose:
                print("Time " + str(current_time) + ":")
                print_states(start_state, ready_state, blocked_state)

    print("end")


# PROCESS CLASS

class Process:
    def __init__(self, process_file):
        self.validate_process_file_name(process_file)
        self.process_file = process_file
        self.state_queue = ProcessQueue()
        process_filename = os.path.split(process_file)[1]
        self.process_number = re.search('\d+', process_filename).group()
        # If this is the very start of the simulation assume everyone is going to run forever
        # We'll check to see if we can do better when we start them
        self.average_burst_time = float("inf")
        self.burst_count = 0
        self.partial_burst_time = 0
        with open(self.process_file, 'r') as f:
            try:
                self.start = -1
                for line in f.readlines():
                    if line.strip() == "":
                        continue
                    line_parts = line.split()
                    if line_parts[0] == "start":
                        self.start = int(line_parts[1])
                    elif line_parts[0] == "end":
                        # We're done in this case
                        pass
                    else:
                        self.state_queue.push_back((line_parts[0], int(line_parts[1])))
                if self.start == -1:
                    raise ValueError()
                if len(self.state_queue) == 0:
                    print("The process file \"" + process_file + "\" is empty.", file=sys.stderr)
                    raise ValueError()
            except:
                print("An error occurred while loading the process file \"" + process_file + "\"", file=sys.stderr)
                exit(1)

    @staticmethod
    def validate_process_file_name(process_file):
        path, filename = os.path.split(process_file)
        file_pattern = re.compile('process-\d+\.txt')
        if len(file_pattern.findall(filename)) == 0:
            print("Process files must have names of the format `process-N.txt`", file=sys.stderr)
            exit(1)
        if not os.path.isfile(process_file):
            print("The process file \"" + process_file + "\" could not be found.", file=sys.stderr)

    def start_process(self):
        if global_average_burst_time[0] != 0:
            self.average_burst_time = global_average_burst_time[0]
            self.burst_count = 1
        else:
            # This will only be triggered by the first things ever run and it won't matter
            # run_full_burst will correctly update them
            self.average_burst_time = 100

    def run_full_burst(self):
        burst_time = self.state_queue.pop_front()[1]
        self.average_burst_time = ((self.average_burst_time * self.burst_count) + burst_time) / (self.burst_count + 1)
        self.burst_count += 1
        global_average_burst_time[0] = ((global_average_burst_time[0] * global_burst_count[0]) + burst_time) / (
            global_burst_count[0] + 1)
        global_burst_count[0] += 1
        return burst_time

    @property
    def average_burst_remaining(self):
        return self.average_burst_time - self.partial_burst_time

    def run_partial_burst(self, time):
        # Runs the top burst in its state_queue for the specified time
        # Returns False when it finishes a burst, True when it doesn't
        state = self.state_queue.pop_front()
        # Check if stepping forward this amount of time will finish the burst
        if state[1] - time <= 0:
            # This partial burst will finish this thing
            self.partial_burst_time += state[1]
            self.average_burst_time = ((self.average_burst_time * self.burst_count) + self.partial_burst_time) / (
                self.burst_count + 1)
            self.burst_count += 1
            global_average_burst_time[0] = ((global_average_burst_time[0] * global_burst_count[
                0]) + self.partial_burst_time) / (global_burst_count[0] + 1)
            global_burst_count[0] += 1
            self.partial_burst_time = 0
            return True
        else:
            # We won't finish the burst in this partial run so put the burst back into the queue for a later time
            self.partial_burst_time += time
            self.state_queue.push_front((state[0], state[1] - time))
            return False

    def __lt__(self, other):
        return self.process_number < other.process_number

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Process " + str(self.process_number)


class ReadyPool:
    def __init__(self):
        self.processes = {}

    def get_next_ready_process(self):
        if self.empty:
            return None
        # Returns the next process by lowest burst time and then lowest process number within that burst time category
        shortest_burst_time = sorted(self.processes.keys())[0]
        process = sorted(self.processes[shortest_burst_time])[0]
        self.processes[shortest_burst_time].remove(process)
        if len(self.processes[shortest_burst_time]) == 0:
            del self.processes[shortest_burst_time]
        return process

    def add(self, process):
        burst_time = process.average_burst_remaining
        if burst_time in self.processes:
            self.processes[burst_time].add(process)
        else:
            self.processes[burst_time] = {process}

    @property
    def empty(self):
        return len(self.processes) == 0

    @property
    def not_empty(self):
        return not self.empty

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        s = "Ready state:"
        if len(self.processes) == 0:
            s += "\n\t **EMPTY**"
        else:
            for burst_time in self.processes:
                for process in self.processes[burst_time]:
                    s += "\n\t" + str(process) + ": " + str(burst_time)
        return s


class BlockedPool:
    def __init__(self):
        self.processes = []

    def add(self, process):
        self.processes.append(process)

    def update(self, time):
        ready_processes = []
        new_process_list = []
        for process in self.processes:
            if process.state_queue.peek()[1] - time <= 0:
                # The process is no longer blocked/waiting and should move out
                # We remove it's current blocked state
                process.state_queue.pop_front()
                ready_processes.append(process)
            else:
                process_state = process.state_queue.pop_front()
                process.state_queue.push_front((process_state[0], process_state[1] - time))
                new_process_list.append(process)
        self.processes = new_process_list
        return ready_processes

    @property
    def empty(self):
        return len(self.processes) == 0

    @property
    def not_empty(self):
        return not self.empty

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        s = "Blocked state:"
        if len(self.processes) == 0:
            s += "\n\t**EMPTY**"
        else:
            for process in self.processes:
                s += "\n\t" + str(process) + ": " + str(process.average_burst_time)
        return s


class StartPool:
    def __init__(self):
        self.processes = {}

    def add(self, process):
        if process.start in self.processes:
            self.processes.append(process)
        else:
            self.processes[process.start] = [process]

    def get_ready_processes(self, current_time):
        ready_processes = []
        for start_time in self.processes:
            if start_time <= current_time:
                ready_processes += self.processes[start_time]
        # Now we clean up the start times that are no longer relevant
        for start_time in list(self.processes.keys()):
            if start_time <= current_time:
                del self.processes[start_time]
        return ready_processes

    @property
    def empty(self):
        return len(self.processes) == 0

    @property
    def not_empty(self):
        return not self.empty

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        s = "Start State:"
        if len(self.processes) == 0:
            s += "\n\t**EMPTY**"
        else:
            for start_time in self.processes:
                for process in self.processes[start_time]:
                    s += "\n\t" + str(process) + ": " + str(process.average_burst_time)
        return s


class ProcessQueue(deque):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def peek(self):
        if len(self) == 0:
            return None
        process = self.pop_front()
        self.push_front(process)
        return process

    @property
    def empty(self):
        return len(self) == 0

    @property
    def not_empty(self):
        return not self.empty

    def pop_front(self):
        return self.popleft()

    def pop_back(self):
        return self.pop()

    def push_front(self, item):
        self.appendleft(item)

    def push_back(self, item):
        self.append(item)

    def print(self):
        for i in range(len(self)):
            print(self[i])

    def single_line_string(self):
        if len(self) == 0:
            return "[]"
        s = "["
        for i in range(len(self)):
            s += str(self[i][1]) + ", "
        s = s[:-2]
        s += "]"
        return s


if __name__ == "__main__":
    main()
