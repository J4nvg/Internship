########################
#   General settings   #
########################

### General board settings ###
WIDTH = 20 # Square board

### General P_i settings ###
# If len(p_settings_list) < n_hider_candidates it should be with replacement to avoid errors
# Success P settings

# OPTIONS: "SUCCESS_PROBABILITIES_INITIAL" | "SUCCESS_PROBABILITIES_HIGH_VAR" | "SUCCESS_PROBABILITIES_LOW_VAR" | "SUCCESS_PROBABILITIES_SKEWED"
SUCCESS_PROBABILITIES_CHOSEN = "SUCCESS_PROBABILITIES_LOW_VAR"
Pi_DICT = {
    # Initial settings, before adding multiple sets
                # 1       2       3       4       5       6
    "SUCCESS_PROBABILITIES_INITIAL":
        {"p": [   1/3,    2/3,    3/4,    4/5,    9/10,   95/100],
         "WITH_REPLACEMENT": True
         },

    "SUCCESS_PROBABILITIES_HIGH_VAR":
        {
                # 1       2       3       4       5
        "p": [  0.10,   0.30,   0.60,   0.80,   0.95],
        "WITH_REPLACEMENT": False
        },

    "SUCCESS_PROBABILITIES_LOW_VAR":
                # 1       2       3       4       5
        {"p": [  0.60,   0.62,   0.64,   0.66,   0.68],
         "WITH_REPLACEMENT": False
         },

    "SUCCESS_PROBABILITIES_SKEWED":
                # 1       2       3       4       5
        {"p": [  0.60,    0.62,   0.64,   0.66,   0.10],
         "WITH_REPLACEMENT": False
         },
}


### General Drone settings ###
DRONE_SYMBOL = 'X'



########################
#   only for main.py   #
########################

### Hider Settings ###
NUMBER_OF_HIDER_CANDIDATES = 5
N_HIDERS = 2
HIDING_STRATEGY = 'greedy' # random | greedy | weighted  | int | list of ints

### Drone settings ###
NUMBER_OF_DRONES_IN_SWARM = 1

