NX_CUGRAPH_AUTOCONFIG = True
from game_config import WIDTH
import os
import timeit
from src import Simulation
import argparse
"""
#TODO
    - Nieuwe strategieën implementeren
    - Plots maken

valid tactics:
["ttbp","rndm","hs","vs,"dor","phs"]

Swarm together:
"ttbp" - Together Traverse Best Permutation
"rndm" - Random walk
"hs" - Horizontal scan
"sp" - Spiraling scan

"vs" - Vertical scan

Swarm split:
"dor" - Divide over Risk
"phs" - Partitioned Horizontal scan
"""

tactic_abbr_full = {
    "ttbp":"together_traverse_best_permutation",
    "dor":"divide_over_risks",
    "rndm":"random_walk",
    "hs":"horizontal_scan_traversal",
    "phs":"partitioned_horizontal_scan_traversal",
    # "vs":"vertical_scan_traversal",
    "sp": "spiral_traversal_swarm"
}

def main():
    parser = argparse.ArgumentParser(description="Specify Simulation n_runs")
    parser.add_argument('--runs', type=int, default=1, help='Number of simulation runs.')
    args = parser.parse_args()

    print(f"Starting simulation with {args.runs} runs...")

    hiding_strategy_to_try = ["greedy","weighted","random"]

    n_hiders_to_try = [1,2,3,4,5]

    n_hider_candidates_to_try = [5]

    swarm_size_to_try = [1,5,10]

    searching_strategy_to_try = ["ttbp","dor","hs","phs","sp","rndm"]

    for strategy in searching_strategy_to_try:
        for hiding_strategy in hiding_strategy_to_try:
            for n_hider_candidates in n_hider_candidates_to_try:
                for n_hiders in n_hiders_to_try:
                    for swarm_size in swarm_size_to_try:
                        filename = f"T-{tactic_abbr_full[strategy]}-W-{20}-HS-{hiding_strategy}-D-{swarm_size}-C-{n_hider_candidates}-H-{n_hiders}-RUNS-{args.runs}.csv"
                        if os.path.exists(f"./data/sim_results/{filename}"):
                            print(f"skip {filename}")
                            continue
                        else:
                            sim = Simulation(n_runs=args.runs, log=True, width=WIDTH,n_hiders=n_hiders,n_hider_candidates=n_hider_candidates,swarm_size=swarm_size,hiding_strategy=hiding_strategy)
                            sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False, tactic=strategy)


if __name__ == "__main__":
    start_time = timeit.default_timer()
    main()
    end_time = timeit.default_timer()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")