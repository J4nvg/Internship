import sys

NX_CUGRAPH_AUTOCONFIG=True
import timeit
from src import Simulation
import argparse
from src.constants import tactic_abbr_full

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

    parser.add_argument("--tactic",required=False,type=str,choices=tactics, help="Tactic to use")
    parser.add_argument("--plot", action='store_true', help="plots boards in original mode to visualise the simulation run")
    parser.add_argument("--plot_hm", action='store_true', help="plots boards in heatmap mode to visualise the simulation run")
    parser.add_argument('--runs',type=int,default=1,help='Number of simulation runs.')
    parser.add_argument( '--log', action='store_true',help='Enable logging to CSV.', default=False)
    parser.add_argument( '--plotspeed',default=.2, type=float,help='increase or decrease plotting speed, 0 < speed < 1')
    parser.add_argument( '--health',default=False, type=bool,help='check for simulation health, maybe errors got introduced')

    args = parser.parse_args()

    if args.health:
        try:
            checkforerrors()
            print("Health check successful")
            sys.exit(0)
        except Exception as e:
            print("Something went wrong during the health check",e)

    if args.runs >= 10000:
        start_time = timeit.default_timer()
        sim = Simulation(n_runs=1000, log=False)
        sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False, plot_hm=False,
                                                      plot_interval=args.plotspeed, tactic=args.tactic)
        end_time = timeit.default_timer()
        sys.stdout.write("\033[H\033[J")
        print(f" 1000 runs took {end_time - start_time} seconds")
        print(f"Expected duration for {args.runs} runs : {(end_time - start_time)/1000 * args.runs:.2f} seconds")

        print("Continue? [Y/n]...")
        yes_or_no = input()
        if yes_or_no == "n":
            sys.stdout.write("\033[H\033[J")
            sys.exit(0)

    print(f"Starting simulation for tactic: {args.tactic} with {args.runs} runs...")
    start_time = timeit.default_timer()
    sim = Simulation(n_runs=args.runs, log=args.log)

    if(args.plot_hm or args.plot):
        plot = True
    else:
        plot = False

    sys.stdout.write("\033[H\033[J")

    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=plot,plot_hm=args.plot_hm,plot_interval=args.plotspeed, tactic=args.tactic)
    end_time = timeit.default_timer()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")



if __name__ == "__main__":
    main()