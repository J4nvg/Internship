NX_CUGRAPH_AUTOCONFIG=True
import timeit
from sim import Simulation

"""
Set of Assumptions:
- Niet diagonaal bewegen
- Swarm weet hiding chances niet
- Swarm weet mogelijke hiding spots wel
- Swarm weet risicos

#TODO
    - Nieuwe strategieën implementeren
        - ++Verdeeld naar locaties
        
    - Plots maken
    - E.v.t. realtime plots
    
    -Stats:
        - Total distance covered


valid tactics:

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

    #
    # n_runs = 2
    # sim = Simulation(n_runs=n_runs,log=True)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=True, plot_interval=.2,tactic="ttbp")
    #
    # sim = Simulation(n_runs=n_runs,log=True)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=True, plot_interval=.03,tactic="hs")
    #
    # sim = Simulation(n_runs=n_runs,log=True)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=True,tactic="phs")
    #
    # sim = Simulation(n_runs=n_runs,log=True)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=True,tactic="dor")
    # sim = Simulation(n_runs=n_runs,log=True)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=True,plot_interval=.05,tactic="rndm")

## Get results
    n_runs = 10
    sim = Simulation(n_runs=n_runs,log=False)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False, plot_interval=.2,tactic="ttbp")
    sim = Simulation(n_runs=n_runs,log=False)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False, plot_interval=.05,tactic="hs")
    # sim = Simulation(n_runs=n_runs,log=False)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False,tactic="phs")
    #
    # sim = Simulation(n_runs=n_runs,log=False)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False,tactic="dor")
    # sim = Simulation(n_runs=n_runs,log=False)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False,plot_interval=.05,tactic="rndm")


if __name__ == "__main__":
    start_time = timeit.default_timer()
    main()
    end_time = timeit.default_timer()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")