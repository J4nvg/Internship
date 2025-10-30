from game_config import WIDTH

NX_CUGRAPH_AUTOCONFIG = True
import timeit
from src import Simulation
import argparse
"""
#TODO
    - Nieuwe strategieën implementeren
    - Plots maken

    "ttbp":"together_traverse_best_permutation",
    "dor":"divide_over_risks",
    "rndm":"random_walk",
    "hs":"horizontal_scan_traversal",
    "phs":"partitioned_horizontal_scan_traversal",
    "sp": "spiral_traversal_swarm",
    "lb": "lidbetter",
    "toq": "traverse_ordered_qa",
    "tpq":"traverse_weighted_qa",
    "dd":"discounted_distance",
"""


def main():
    runs = 100_000

    print(f"Starting simulation with {runs} runs...")

    hiding_strategy_to_try = ["greedy","weighted","random"]

    n_hiders_to_try = [1,2,3,4,5]

    n_hider_candidates_to_try = [5]

    swarm_size_to_try = [1,5,10]

    searching_strategy_to_try = ["ttbp"]

    for strategy in searching_strategy_to_try:
        for hiding_strategy in hiding_strategy_to_try:
            for n_hider_candidates in n_hider_candidates_to_try:
                for n_hiders in n_hiders_to_try:
                    for swarm_size in swarm_size_to_try:
                        sim = Simulation(n_runs=runs, log=True, width=WIDTH,n_hiders=n_hiders,n_hider_candidates=n_hider_candidates,swarm_size=swarm_size,hiding_strategy=hiding_strategy)
                        sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False, tactic=strategy)


if __name__ == "__main__":
    start_time = timeit.default_timer()
    main()
    end_time = timeit.default_timer()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")