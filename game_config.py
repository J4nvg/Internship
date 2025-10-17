##############################################
# Square board:
WIDTH = 20


### Drone settings ###
NUMBER_OF_DRONES_IN_SWARM = 10

DRONE_SYMBOL = 'X'

### Risk Settings ###

#if not static risk:
SUCCES_PROBABILITIES = [1/3,2/3,3/4,4/5,9/10,95/100]

STATIC_P = False
STATIC_P_p = .3  # Takedown chance

### Hider Settings ###
NUMBER_OF_HIDER_CANDIDATES = 5
N_HIDERS = 2
HIDING_STRATEGY = 'greedy' # random | greedy | weighted  | int | list of ints




