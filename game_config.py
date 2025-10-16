##############################################
# Square board:
square_size = 5


WIDTH, HEIGHT = square_size,square_size  # Let's keep it square


### Drone settings ###
NUMBER_OF_DRONES_IN_SWARM = 2

DRONE_SYMBOL = 'X'

### Risk Settings ###

#if not static risk:
SUCCES_PROBABILITIES = [1/3,2/3,3/4,4/5,9/10,95/100]

STATIC_P = False
STATIC_P_p = .3  # Takedown chance

### Hider Settings ###
NUMBER_OF_HIDER_CANDIDATES = 5
N_HIDERS = 2
HIDING_STRATEGY = 'random' # random | greedy | weighted  | int | list of ints


##############################################