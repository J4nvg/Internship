import timeit
from sim import Simulation

"""
Set of Assumptions:
Niet diagonaal

#TODO
    - Nieuwe strategieën implementeren
        - verdeelde Horizontal scan, vertical scan
        - Verdeeld naar locaties
    - Data naar log txt schrijven
    - Plots maken
    - E.v.t. realtime plots

"""


def main():

    sim = Simulation(n_runs=1_000,log=False)
    sim.start_main_sim_loop_single_tactic_metrics(plot_boards=True)



if __name__ == "__main__":
    # timeit.timeit("main()",number=10)
    main()
