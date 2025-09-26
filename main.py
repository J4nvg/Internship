import timeit
from sim import Simulation

"""
Set of Assumptions:
- Niet diagonaal bewegen
- Swarm weet hiding chances niet
- Swarm weet mogelijke hiding spots wel

- Weet swarm risks [???]

#TODO
    - Nieuwe strategieën implementeren
        - verdeelde Horizontal scan, vertical scan
        - Verdeeld naar locaties
    - Plots maken
    - E.v.t. realtime plots




valid tactics:
"ttbp" - Together Traverse Best Permutation
"dor" - Divide over Risk
"rndm" - Random walk
"hs" - Horizontal scan
"vs" - Vertical scan


"""


def main():

    sim = Simulation(n_runs=10,log=False)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=True ,tactic="dor")



if __name__ == "__main__":
    # timeit.timeit("main()",number=10)
    main()
