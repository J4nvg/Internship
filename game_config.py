########################
#   General settings   #
########################
### General board settings ###
WIDTH = 20 # Square board

### General P_i settings ###
SUCCES_PROBABILITIES = [1/3,2/3,3/4,4/5,9/10,95/100]

### General Drone settings ###
DRONE_SYMBOL = 'X'


########################
#   only for main.py   #
########################

### Hider Settings ###
NUMBER_OF_HIDER_CANDIDATES = 5
N_HIDERS = 2
HIDING_STRATEGY = 'weighted' # random | greedy | weighted  | int | list of ints

### Drone settings ###
NUMBER_OF_DRONES_IN_SWARM = 10





### Deprecated ###
#if static Risk:
STATIC_P = False
STATIC_P_p = .3  # Takedown chance





