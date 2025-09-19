from board import Board
from drone import Drone, Swarm
import numpy as np
import sys, time
from game_config import HIDING_STRATEGY,WIDTH,HEIGHT,NUMBER_OF_DRONES_IN_SWARM,NUMBER_OF_RISK_LOCATIONS,RISKY_AREA_P,DRONE_SYMBOL,NUMBER_OF_HIDERS
from collections import deque
from itertools import permutations
import networkx as nx
from helpers import get_optimal_permutation_MD


class Simulation():

    def __init__(self,n_runs=1):
        self.runs = n_runs
        self.board= Board(width=WIDTH, height=HEIGHT, n_hiders=NUMBER_OF_HIDERS,n_risks=NUMBER_OF_RISK_LOCATIONS, takedown_chance=RISKY_AREA_P)
        self.swarm = Swarm(self.board,size=NUMBER_OF_DRONES_IN_SWARM,symbol=DRONE_SYMBOL)
        self.board.hide(hider = "#", tactic=HIDING_STRATEGY)
        self.board.print_board()
        self.board.plot_q_heatmap()
        self.rw_results = np.array(n_runs)


    def run_random_walk(self, plot_boards=True, plot_interval=0.2):
        swarm = self.swarm
        for i in range(self.runs):
            found = False
            r = 0
            while (not found and not len(swarm.takenDown) == swarm.size):
                r += 1
                for drone in swarm.swarm:
                    if drone.random_move():
                        found = True
                        break
                if plot_boards:
                    sys.stdout.write("\033[H\033[J")
                    self.board.print_board()
                    sys.stdout.flush()
                    time.sleep(plot_interval)
                # print(f"Step: {i}")
            if found:
                print("Target was found")
            print(f"Took {r} steps and target was", "found" if found else "not found", f", {len(swarm.takenDown)} drones were taken down.")

    def together_traverse_best_permutation(self,plot_boards=True, plot_interval=0.2):
        swarm = self.swarm
        graph = self.board.graph
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        board= self.board
        found = False
        r = 0
        if len(board.hider_candidates) == 0:
            return

        sample_drone = swarm.available[0]

        hider_candidate_locations = [cell.loc for cell in board.hider_candidates]

        optimal_path_sequence, shortest_total_distance = get_optimal_permutation_MD(
            sample_drone.start,
            hider_candidate_locations
        )

        route = []

        for i in range(len(optimal_path_sequence) - 1):
            new_route = (nx.shortest_path(graph, source=optimal_path_sequence[i], target=optimal_path_sequence[i+1]))
            route.extend(new_route[1:])


        for drone in swarm.swarm:
            drone.set_route(route)
            swarm.to_unavailable(drone)

        while not found and not len(swarm.takenDown) == swarm.size:

            for drone in swarm.swarm:
                if drone.move_next_from_route():
                    found = True
                    # print(f"\nTarget found by Drone {drone.number} at location {drone.current_loc}!")
            if plot_boards:
                sys.stdout.write("\033[H\033[J")
                self.board.print_board()
                sys.stdout.flush()
                time.sleep(plot_interval)

            if found:
                break
            r += 1


        print(f"Took {r} steps and target was", "found" if found else "not found",
              f"{len(swarm.takenDown)} drones were taken down.")


    def horizontal_scan_traversal_swarm(self,plot_boards=True, plot_interval=0.2):
        swarm = self.swarm
        pass

    def run_aStarBased_strategy(self,plot_boards=True, plot_interval=0.2):
        swarm = self.swarm
        for i in range(self.runs):
            found = False
            r = 0
            while (not found and not len(swarm.takenDown) == swarm.size):
                for i in range(len(swarm.available)):
                    if not swarm.cell_probabilities:
                        break
                    target = swarm.cell_probabilities.popleft()
                    shortest_path = []
                    shortest_path_length = float("inf")
                    going = None
                    for drone in swarm.available:
                        drone_path = drone.get_route_to_goal(target)
                        drone_path_length = len(drone_path)
                        if drone_path_length < shortest_path_length:
                            # print("Enther the loop")
                            shortest_path = drone_path
                            shortest_path_length = drone_path_length
                            going = drone
                            # print(going.number," has shorter path to", target)

                    print(going.number," Has now set target to: ", target)
                    going.set_route(shortest_path,route_length=shortest_path_length)
                    swarm.to_unavailable(going)

                for drone in swarm.swarm:
                    if drone.move_next_from_route():
                        found = True
                        # print(f"\nTarget found by Drone {drone.number} at location {drone.current_loc}!")
                if plot_boards:
                    sys.stdout.write("\033[H\033[J")
                    self.board.print_board()
                    sys.stdout.flush()
                    time.sleep(plot_interval)

                if found:
                    break
                r+= 1

            print(f"Took {r} steps and target was", "found" if found else "not found", f"{len(swarm.takenDown)} drones were taken down.")
        pass

    # def