##############################################
# Square board:
square_size = 10


WIDTH, HEIGHT = square_size, square_size  # Let's keep it square for now too


### Drone settings ###
NUMBER_OF_DRONES_IN_SWARM = 2
DRONE_SYMBOL = 'X'

### Risk Settings ###

RISKY_AREA_P = .1  # Takedown chance

RANDOM_RISK_ALLOCATION = False
RISKY_AREA_FRAC = 0.1
NUMBER_OF_RISK_LOCATIONS = round(WIDTH*HEIGHT*RISKY_AREA_FRAC)

### Hider Settings ###
FULL_BOARD_HIDING = False
NUMBER_OF_HIDERS = 3
HIDING_STRATEGY = "weighted" # greedy | weighted


##############################################