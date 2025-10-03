# Drone swarm simulation environment
___ 
## Use:
Run directly from command line:
```sh
main.py --plot --tactic <tactic> --runs <nruns> --log
```
| CMD               |                    Explanation                    |
|:------------------|:-------------------------------------------------:|
| --plot            |  Enables printed visualisation simulation runs.   |
| --tactic <tactic> |      Specify which searching tactic to use.       |
| --runs <nruns>    |      Specify the amount of simulation runs.       |
| --log             | Enables logging to csv file in sim_logs directory |
| --plotspeed       | increase plot interval time must be > 0           | 


## List of available tactics:

| Name                                  | Abbreviation |
|:--------------------------------------|-------------:|
| Together Traverse to Best Permutation |     **ttbp** |
| Divide Over Risks                     |      **dor** |
| Partitioned Horizontal Scan           |      **phs** |
| Horizontal Scan                       |       **hs** |
| Vertical Scan                         |       **vs** |
| Random                                |     **rndm** |

