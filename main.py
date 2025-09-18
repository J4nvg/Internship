from time import time as timer
import numpy as np
import matplotlib.pyplot as plt
from board import Board
from drone import Drone, Swarm
from sim import Simulation

"""
Set of Assumptions:
Niet diagonaal

#TODO
    
    - R terug op minimap
    - Data verzamelen
    
    

"""


# def main():
#     start = timer()
#     # for i in range(10):
#     board= Board(width=WIDTH, height=HEIGHT,n_risks=NUMBER_OF_RISK_LOCATIONS, takedown_chance=RISKY_AREA_P)
#     swarm = Swarm(board,size=NUMBER_OF_DRONES_IN_SWARM,symbol=DRONE_SYMBOL)
#     # swarm.cells_by_probability()
#     board.hide(hider = "#",tactic="greedy")
#     # swarm.set_routes()
#     board.print_board()
#     swarm.start_random_walk(plot_boards=False)
#     # board.plot_graph()
#     print("Time taken to run program: ", timer() - start," s")
#     board.plot_q_heatmap()
#     board.plot_risk_heatmap()
#     board.plot_drone_trajectory_animated(swarm=swarm,id=2)



def main():
    sim = Simulation()
    # sim.run_random_walk(plot_boards=True)
    sim.run_aStarBased_strategy(plot_boards=True, plot_interval=.2 )



if __name__ == "__main__":
    main()
