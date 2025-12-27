########################
#   General settings   #
########################


### General board settings ###
WIDTH = 20 # Square board

### General P_i settings ###
# If len(p_settings_list) < n_hider_candidates it should be with replacement to avoid errors
# Success P settings

# OPTIONS: "SUCCESS_PROBABILITIES_INITIAL" | "SUCCESS_PROBABILITIES_HIGH_VAR" | "SUCCESS_PROBABILITIES_LOW_VAR" | "SUCCESS_PROBABILITIES_SKEWED"
SUCCESS_PROBABILITIES_CHOSEN = "SUCCESS_PROBABILITIES_HIGH_VAR"
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


#########################
#   Printing settings   #
#########################

plot_hm = False # Turn this to true to change the plotting mode from original to heatmap mode


########################
#   only for main.py   #
########################

### Hider Settings ###
NUMBER_OF_HIDER_CANDIDATES = 5
N_HIDERS = 2
HIDING_STRATEGY = 'greedy' # random | greedy | weighted  | int | list of ints

### Drone settings ###
NUMBER_OF_DRONES_IN_SWARM = 5

########################
#    Rename mapping    #
########################

rename_map = {
    "together_traverse_best_permutation":"Shortest_path_tour",
    "divide_over_risks":"Proportional_risk_split",
    "random_walk":"random_walk",
    "horizontal_scan_traversal":"Horizontal_scan",
    "partitioned_horizontal_scan_traversal":"Partitioned_horizontal_scan",
    "spiral_traversal_swarm":"Inward_spiral",
    "lidbetter":"Lidbetter",
    "traverse_ordered_qa":"Ranked_qa_subset",
    "traverse_p_qa":"Weighted_q_a_subset_sampling",
    "discounted_distance":"Risk_weighted_tour",
    "discounted_distance_reverse":"Success_weighted_tour",
    "shared_list":"Dynamic_task_queue",
}
