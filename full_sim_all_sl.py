NX_CUGRAPH_AUTOCONFIG=True
from game_config import WIDTH,Pi_DICT
import os
import timeit
from src import Simulation,constants
import argparse

# tactic_abbr_full = constants.tactic_abbr_full

tactic_abbr_full = {
    # "ttbp":"together_traverse_best_permutation",
    # "dor":"divide_over_risks",
    # "rndm":"random_walk",
    # "hs":"horizontal_scan_traversal",
    # "phs":"partitioned_horizontal_scan_traversal",
    # "sp": "spiral_traversal_swarm",
    # "lb": "lidbetter",
    # "toq": "traverse_ordered_qa",
    # "tpq":"traverse_p_qa",
    # "dd":"discounted_distance",
    # "ddr":"discounted_distance_reverse",
    "sl":"shared_list",
    # "sl_heap":"shared_list_heap",
}

def main():

    tactics = tactic_abbr_full.keys()
    parser = argparse.ArgumentParser(description="Specify Simulation n_runs")
    # parser.add_argument('--runs', type=int, default=1, help='Number of simulation runs.')
    args = parser.parse_args()
    args.runs = 100_000

    print(f"Starting simulation with {args.runs} runs...")


    # probability_distributions = Pi_DICT.keys()
    
    probability_distributions = ["SUCCESS_PROBABILITIES_HIGH_VAR" ,"SUCCESS_PROBABILITIES_LOW_VAR","SUCCESS_PROBABILITIES_SKEWED"]
    
    hiding_strategy_to_try = ["greedy","weighted","random"]
    # hiding_strategy_to_try = ["greedy"]

    n_hiders_to_try = [1,2,3,4,5]

    n_hider_candidates_to_try = [5]

    swarm_size_to_try = [x for x in range(1,11)]

    for tactic in tactics:
        for p_dist in probability_distributions:
            for hiding_strategy in hiding_strategy_to_try:
                for n_hider_candidates in n_hider_candidates_to_try:
                    for n_hiders in n_hiders_to_try:
                        for swarm_size in swarm_size_to_try:
                            filename = f"T-{tactic_abbr_full[tactic]}-W-{20}-HS-{hiding_strategy}-D-{swarm_size}-C-{n_hider_candidates}-H-{n_hiders}-RUNS-{args.runs}.csv"
                            if os.path.exists(f"./data/sim_results/{p_dist}/{filename}"):
                                print(f"skip {filename}")
                                continue
                            else:
                                print(f"Starting P dist: {p_dist} Hiding strat: {hiding_strategy} n hider candidates:{n_hider_candidates} with {n_hiders} hiders and swarmsize: {swarm_size}")
                                sim = Simulation(n_runs=args.runs, log=True, width=WIDTH,n_hiders=n_hiders,n_hider_candidates=n_hider_candidates,swarm_size=swarm_size,hiding_strategy=hiding_strategy, success_p=p_dist)
                                sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False, tactic=tactic)


if __name__ == "__main__":
    start_time = timeit.default_timer()
    main()
    end_time = timeit.default_timer()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")