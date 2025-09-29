NX_CUGRAPH_AUTOCONFIG=True
import timeit
from sim import Simulation
"""
Set of Assumptions:
- Niet diagonaal bewegen
- Swarm weet hiding chances niet
- Swarm weet mogelijke hiding spots wel

#TODO
    - Nieuwe strategieën implementeren
        - verdeelde Horizontal scan, vertical scan
        - ++Verdeeld naar locaties
    - Plots maken
    - E.v.t. realtime plots
    
    -Stats:
        - Total area of map covered
        - Total distance covered
        - Mean distance per drone covered
        -  


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
    n_runs = 5
    # sim = Simulation(n_runs=n_runs,log=False)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=True,tactic="ttbp")
    # sim = Simulation(n_runs=n_runs,log=False)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=True,tactic="hs")
    # sim = Simulation(n_runs=n_runs,log=False)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=True,tactic="phs")
    sim = Simulation(n_runs=n_runs,log=False)

    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False,tactic="dor")
    # sim = Simulation(n_runs=5,log=False)
    # sim.start_main_sim_loop_single_tactic_metrics(plot_boards=True,tactic="rndm")


if __name__ == "__main__":
    # timeit.timeit("main()",number=10)
    main()
