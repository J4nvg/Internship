NX_CUGRAPH_AUTOCONFIG=True
import timeit
from sim import Simulation
import argparse


"""


#TODO
    - Nieuwe strategieën implementeren
        - ++Verdeeld naar locaties
        
    - Plots maken
    - E.v.t. realtime plots


valid tactics:

["ttbp","rndm","hs","vs,"dor","phs"]
Swarm together:
"ttbp" - Together Traverse Best Permutation
"rndm" - Random walk
"hs" - Horizontal scan
"vs" - Vertical scan

Swarm split:
"dor" - Divide over Risk
"phs" - Partitioned Horizontal scan
"""


def main():
    parser = argparse.ArgumentParser(description="Specify Simulation Tactic")

    parser.add_argument("--plot", action='store_true', help="plots boards to visualise the simulation run")
    parser.add_argument("--tactic",required=False,type=str,choices=["ttbp","rndm","hs","vs","dor","phs"], help="Tactic to use")
    parser.add_argument('--runs',type=int,default=1,help='Number of simulation runs.')
    parser.add_argument( '--log', action='store_true',help='Enable logging to CSV.')
    parser.add_argument( '--plotspeed',default=.2, type=float,help='increase or decrease plotting speed, 0 < speed < 1')
    args = parser.parse_args()


    print(f"Starting simulation for tactic: {args.tactic} with {args.runs} runs...")
    sim = Simulation(n_runs=args.runs, log=args.log)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=args.plot,plot_interval=args.plotspeed, tactic="phs")
    sim = Simulation(n_runs=args.runs, log=args.log)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=args.plot,plot_interval=args.plotspeed, tactic="dor")
    sim = Simulation(n_runs=args.runs, log=args.log)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=args.plot,plot_interval=args.plotspeed, tactic="ttbp")
    sim = Simulation(n_runs=args.runs, log=args.log)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=args.plot,plot_interval=.05, tactic="hs")
    sim = Simulation(n_runs=args.runs, log=args.log)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=args.plot,plot_interval=args.plotspeed, tactic="ttbp")
    sim = Simulation(n_runs=args.runs, log=args.log)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=args.plot,plot_interval=.05, tactic="rndm")



if __name__ == "__main__":
    start_time = timeit.default_timer()
    main()
    end_time = timeit.default_timer()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")