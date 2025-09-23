from board import Board
from drone import Drone, Swarm
import numpy as np
import sys, time
from game_config import HIDING_STRATEGY,WIDTH,HEIGHT,NUMBER_OF_DRONES_IN_SWARM,NUMBER_OF_RISK_LOCATIONS,RISKY_AREA_P,DRONE_SYMBOL,NUMBER_OF_HIDERS
import networkx as nx
from helpers import get_optimal_permutation_MD, mean_var, confidence_interval
from tqdm import tqdm
import time

class Simulation():

    def __init__(self,n_runs=1,log=False):
        self.runs = n_runs
        self.set_board()
        # self.swarm = Swarm(self.board,size=NUMBER_OF_DRONES_IN_SWARM,symbol=DRONE_SYMBOL)
        self.log = log
        # self.board.plot_q_heatmap()
        self.find_steps = np.zeros(n_runs)
        self.taken_down = np.zeros(n_runs)
        self.found = np.zeros(n_runs)

    def set_board(self):
        self.board = Board(width=WIDTH, height=HEIGHT, n_hiders=NUMBER_OF_HIDERS,n_risks=NUMBER_OF_RISK_LOCATIONS, takedown_chance=RISKY_AREA_P)
        self.board.hide(hider = "#", tactic=HIDING_STRATEGY)
        # self.board.print_board()

    def save_data(self,i,steps,found,taken_down,filename=''):
        self.find_steps[i] = steps
        self.taken_down[i] = taken_down
        self.found[i] = found
        if filename != '':
            with open(filename,"a") as f:
                f.write(f"{i+1}. Steps: {steps}, Found: {found}, Taken down:{taken_down} \n")


    def start_main_sim_loop_single_tactic_metrics(self,plot_boards=False):
        filename = ''
        if self.log:
            filename = str(time.time()).replace('.','')
            filename = f"./sim_logs/{filename}.txt"
        if not plot_boards:
            for i in tqdm(range(self.runs)):
                self.set_board()
                steps,found,taken_down = self.together_traverse_best_permutation(plot_boards=plot_boards)
                self.save_data(i,steps,found,taken_down,filename)
        else:
            for i in range(self.runs):
                self.set_board()
                steps,found,taken_down = self.together_traverse_best_permutation(plot_boards=plot_boards)
                self.save_data(i, steps, found, taken_down,filename)
        self.get_stats()

    def get_stats(self):
        findsteps_mu, findsteps_var = mean_var(self.find_steps)
        findsteps_ci = confidence_interval(findsteps_mu, findsteps_var,self.runs)

        print("Find steps mean:",findsteps_mu,"\n find steps var:",findsteps_var,"\n find steps ci:",findsteps_ci[0],findsteps_ci[1])
        print("Half width",findsteps_ci[1]-findsteps_mu)


        takendown_mu, takendown_var = mean_var(self.taken_down)
        takendown_ci = confidence_interval(takendown_mu, takendown_var,self.runs)
        print("\n Taken_down mean:",takendown_mu,"\n Taken_down var:",takendown_var,"\n Taken_down ci:",takendown_ci[0],takendown_ci[1])
        print("Half width",takendown_ci[1]-takendown_mu)
        return


    def run_random_walk(self, plot_boards=True, plot_interval=0.2):
        swarm = Swarm(self.board,size=NUMBER_OF_DRONES_IN_SWARM,symbol=DRONE_SYMBOL)
        found = False
        r = 0
        for drone in swarm.swarm:
            if drone.move_next(swarm.swarm[0].start):
                found=True
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
        # if found:
        #     print("Target was found")
        # print(f"Took {r} steps and target was", "found" if found else "not found", f", {len(swarm.takenDown)} drones were taken down.")
        return r,found,len(swarm.takenDown)


    def together_traverse_best_permutation(self,plot_boards=True, plot_interval=0.2):
        swarm = Swarm(self.board,size=NUMBER_OF_DRONES_IN_SWARM,symbol=DRONE_SYMBOL)
        graph = self.board.graph
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        board= self.board
        if len(board.hider_candidates) == 0:
            return

        sample_drone = swarm.available[0]

        hider_candidate_locations = [cell.loc for cell in board.hider_candidates]

        optimal_path_sequence, shortest_total_distance = get_optimal_permutation_MD(sample_drone.start,hider_candidate_locations)

        route = [sample_drone.start]

        for i in range(len(optimal_path_sequence) - 1):
            new_route = (nx.shortest_path(graph, source=optimal_path_sequence[i], target=optimal_path_sequence[i+1]))
            route.extend(new_route[1:])

        return self._run_traversal_loop_swarm(swarm, route, plot_boards, plot_interval, scanner_traversal=False)


    def horizontal_scan_traversal_swarm(self, plot_boards=True, plot_interval=0.2):
        swarm = Swarm(self.board,size=NUMBER_OF_DRONES_IN_SWARM,symbol=DRONE_SYMBOL)
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        route = [swarm.swarm[0].start]

        for y in range(self.board.height):
            if y % 2:
                for x in range(self.board.width - 1, -1, -1):
                    route.append((x, y))
            else:
                for x in range(self.board.width):
                    route.append((x, y))

        return self._run_traversal_loop_swarm(swarm,route,plot_boards,plot_interval,scanner_traversal=True)


    def vertical_scan_traversal_swarm(self,plot_boards=True, plot_interval=0.2):
        swarm = Swarm(self.board,size=NUMBER_OF_DRONES_IN_SWARM,symbol=DRONE_SYMBOL)
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        route = [swarm.swarm[0].start]

        for y in range(self.board.height):
            if y%2:
                for x in range(self.board.width-1,-1,-1):
                    route.append((y,x))
            else:
                for x in range(self.board.width):
                    route.append((y,x))

        return self._run_traversal_loop_swarm(swarm,route,plot_boards,plot_interval,scanner_traversal=True)

    def _run_traversal_loop_swarm(self,swarm,route,plot_boards=False,plot_interval=0.2,scanner_traversal=False):
        found = False
        r = 0
        len_route = len(route)

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
            if r == len_route and scanner_traversal:
                # print("Nothing was found")
                break

        # print(f"Took {r} steps and target was", "found" if found else "not found",
        #       f"{len(swarm.takenDown)} drones were taken down.")

        swarm.remove_swarm()
        return r,found,len(swarm.takenDown)


    def run_dijkstraBased_strategy(self,plot_boards=True, plot_interval=0.2):
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