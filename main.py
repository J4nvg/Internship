import sys

NX_CUGRAPH_AUTOCONFIG=True
import timeit
from src import Simulation
import argparse
from src.constants import tactic_abbr_full

"""
#TODO
- Shared list approach
- Dashboard such that it becomes a web app
"""

def checkforerrors():
    hiding_strategy_to_try = ["greedy","weighted","random"]

    n_hiders_to_try = [1,2,5]

    n_hider_candidates_to_try = [5]

    swarm_size_to_try = [1,5,10]

    searching_strategy_to_try = tactic_abbr_full.keys()

    for strategy in searching_strategy_to_try:
        for hiding_strategy in hiding_strategy_to_try:
            for n_hider_candidates in n_hider_candidates_to_try:
                for n_hiders in n_hiders_to_try:
                    for swarm_size in swarm_size_to_try:
                        sim = Simulation(n_runs=1000, log=False, width=20,n_hiders=n_hiders,n_hider_candidates=n_hider_candidates,swarm_size=swarm_size,hiding_strategy=hiding_strategy)
                        sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False, tactic=strategy)





def main():
    parser = argparse.ArgumentParser(description="Specify Simulation Tactic")


    tactics = tactic_abbr_full.keys()

    parser.add_argument("--plot", action='store_true', help="plots boards to visualise the simulation run")
    parser.add_argument("--tactic",required=False,type=str,choices=tactics, help="Tactic to use")
    parser.add_argument('--runs',type=int,default=1,help='Number of simulation runs.')
    parser.add_argument( '--log', action='store_true',help='Enable logging to CSV.', default=False)
    parser.add_argument( '--plotspeed',default=.2, type=float,help='increase or decrease plotting speed, 0 < speed < 1')
    parser.add_argument( '--health',default=.01, action='store_true',help='check for simulation health, maybe errors got introduced')
    args = parser.parse_args()

    if args.health:
        try:
            checkforerrors()
            print("Health check successful")
            sys.exit(0)
        except Exception as e:
            print("Something went wrong during the health check",e)


    print(f"Starting simulation for tactic: {args.tactic} with {args.runs} runs...")
    sim = Simulation(n_runs=args.runs, log=args.log)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=args.plot,plot_interval=args.plotspeed, tactic=args.tactic)

    # sim = Simulation(n_runs=1_000, log=False)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False,plot_interval=0.1, tactic="rndm")





if __name__ == "__main__":
    start_time = timeit.default_timer()
    main()
    end_time = timeit.default_timer()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")