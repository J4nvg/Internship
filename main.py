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

    sim = Simulation(n_runs=1_000,log=False)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False,tactic="ttbp")
    sim = Simulation(n_runs=1_000,log=False)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False,tactic="hs")
    sim = Simulation(n_runs=1_000,log=False)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False,tactic="phs")
    sim = Simulation(n_runs=1_000,log=False)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False,tactic="dor")
    sim = Simulation(n_runs=1_000,log=False)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=False,tactic="rndm")


if __name__ == "__main__":
    # timeit.timeit("main()",number=10)
    main()
