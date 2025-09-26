##############################################



# Square board:
square_size = 20


WIDTH, HEIGHT = square_size,square_size  # Let's keep it square


### Drone settings ###
NUMBER_OF_DRONES_IN_SWARM = 10
DRONE_SYMBOL = 'X'

### Risk Settings ###

STATIC_RISK = False
RISKY_AREA_P = .3  # Takedown chance

#if not static risk:
RISK_CHANCES = [1/10,1/9,1/8,1/7,1/6,1/5,1/4,1/3]
# RISK_CHANCES = [.9]


### Hider Settings ###
NUMBER_OF_HIDERS = 5
HIDING_STRATEGY = "weighted" # greedy | weighted | debug_corner


#Depricated
FULL_BOARD_HIDING = False


#full board risk apart from hiding
RANDOM_RISK_ALLOCATION = False
RISKY_AREA_FRAC = 0.1
NUMBER_OF_RISK_LOCATIONS = round(WIDTH*HEIGHT*RISKY_AREA_FRAC)

##############################################