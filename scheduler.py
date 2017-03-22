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

# CONSTANTS

allowed_algos = ["RR", "SJF", "SJR"]
global_average_burst_time = 0
burst_count = 0


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

    # Pull the first items out of the start queue
    while process_queue.empty:
        while start_queue.not_empty and start_queue.peek()[1].start == current_time:
            process_queue.push_back(start_queue.popleft())
        current_time += 1

    # Begin RR loop
    while process_queue.not_empty:
        start_time = current_time
        process = process_queue.pop_front()
        process_state = process.state_queue.pop_front()
        if process_state[0] == "B":
            # We are in the middle of a burst
            if process_state[1] > time_quantum:
                process.state_queue.push_front(("B", process_state[1] - time_quantum))
                current_time += time_quantum

                print(str(process.process_number) + " " + str(start_time) + " " + str(current_time))
            elif process_state[1] == time_quantum:

        # If nothing new has shown up while we finished processing this
        process_queue.push_back((current_time, process))

    print(process_queue.single_line_string())
    print("end")



def shortest_job_first(processes, verbose=False):
    return


def shortest_job_remaining(processes, verbose=False):
    return


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
        if global_average_burst_time != 0:
            self.average_burst_time = global_average_burst_time
            self.burst_count = 1

    def __lt__(self, other):
        return self.process_number < other.process_number

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Process " + str(self.process_number)


class ProcessPen:
    def __init__(self):
        self.processes = {}

    def get(self, key):
        if key in self.processes:
            return self.processes[key]
        else:
            return None

    def add(self, process):
        process_state = process.state_queue.peek()[1]
        if process_state in self.processes:
            self.processes[process_state].append(process)
        else:
            self.processes[process_state] = [process]

    def update(self, time):
        """Subtracts this amount of time from each process' first state
        Returns all of the processes that have changed states during this time
        """
        pass


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
        temp = ProcessQueue()
        for i in range(len(self)):
            print(self[i])

    def single_line_string(self):
        s = "["
        for i in range(len(self)):
            s += str(self[i][1]) + ", "
        s = s[:-2]
        s += "]"
        return s


if __name__ == "__main__":
    main()
