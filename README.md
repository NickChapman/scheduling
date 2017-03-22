This program was built and tested using python 3.5.2, no guarantees are made about whether it will run on any other version. 

To run this program refer to the following:

```
Usage: python <scheduling algorithm> [optional algorithm parameter] [verbose] <process time file n>*
```

NB: If your default version of python 2, you will need to use:

```
Usage: python3 <scheduling algorithm> [optional algorithm parameter] [verbose] <process time file n>*
```

Allowed scheduling algorithms:
 * `RR` - Round Robin
     * Requires the optional algorithm parameter which is the time quantum (must be an integer)
 * `SJR` - Shortest Job Remaining
 * `SJF` - Shortest Job First