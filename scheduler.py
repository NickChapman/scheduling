"""
Created by Nick Chapman
March 22, 2017
nlc35 at georgetown dot edu
"""

import sys
import re
import os

# CONSTANTS

allowed_algos = ["RR", "SJF", "SJR"]


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
        algorithm = arguments[0]
        if algorithm not in allowed_algos:
            usage_error()
        if algorithm == "RR":
            time_quantum = int(arguments[1])
        if arguments[2] == "verbose":
            verbose = True
            process_files = arguments[3:]
        else:
            verbose = False
            process_files = arguments[2:]
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
        round_robin(processes)
    elif algorithm == "SJF":
        shortest_job_first(processes)
    elif algorithm == "SJR":
        shortest_job_remaining(processes)
    else:
        # We have somehow reached an error state
        print("An error has occurred. The likely cause is below.", file=sys.stderr)
        usage_error()


# ALGORITHMS


def round_robin(processes):
    return


def shortest_job_first(processes):
    return


def shortest_job_remaining(processes):
    return


# PROCESS CLASS

class Process:
    def __init__(self, process_file):
        self.validate_process_file_name(process_file)
        self.process_file = process_file

    @staticmethod
    def validate_process_file_name(process_file):
        path, filename = os.path.split(process_file)
        file_pattern = re.compile('process-\d+\.txt')
        if len(file_pattern.findall(filename)) == 0:
            print("Process files must have names of the format `process-N.txt`", file=sys.stderr)
            exit(1)
        if not os.path.isfile(process_file):
            print("The process file \"" + process_file + "\" could not be found.", file=sys.stderr)


if __name__ == "__main__":
    main()
