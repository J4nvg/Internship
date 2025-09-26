from scipy.odr import odr_error
from functools import cache
from board import Board
from drone import Drone, Swarm
import numpy as np
import sys, time
from game_config import HIDING_STRATEGY,WIDTH,HEIGHT,NUMBER_OF_DRONES_IN_SWARM,NUMBER_OF_RISK_LOCATIONS,RISKY_AREA_P,DRONE_SYMBOL,NUMBER_OF_HIDERS
import networkx as nx
from helpers import get_optimal_permutation_MD, mean_var, confidence_interval, min_max, get_all_stats, \
    get_whole_and_remainder
from tqdm import tqdm
import time
import pandas as pd
from itertools import cycle

@cache
def get_all_paths(width,height):
    board = Board(width=width, height=height, n_hiders=0, n_risks=0, takedown_chance=0)
    return dict(nx.all_pairs_shortest_path(board.graph))


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
        self.all_paths = None


    def set_board(self):
        self.board = Board(width=WIDTH, height=HEIGHT, n_hiders=NUMBER_OF_HIDERS,n_risks=NUMBER_OF_RISK_LOCATIONS, takedown_chance=RISKY_AREA_P)
        self.board.hide(hider = "#", tactic=HIDING_STRATEGY)
        if self.runs > 10:
            self.all_paths = get_all_paths(WIDTH, HEIGHT)
        # self.board.print_board()

    def save_data(self,i,steps,found,taken_down,filename=''):
        self.find_steps[i] = steps
        self.taken_down[i] = taken_down
        self.found[i] = found
        if filename != '':
            with open(filename,"a") as f:
                f.write(f"{i+1}. Steps: {steps}, Found: {found}, Taken down:{taken_down} \n")


    def start_main_sim_loop_single_tactic_metrics(self,plot_boards=False,tactic="ttbp"):

        match tactic:
            case "ttbp":
                strat = self.together_traverse_best_permutation
                tactic = "Together Traverse Best Permutation"
            case "dor":
                strat = self.divide_over_risks
                tactic = "divide_over_risks"
            case "rndm":
                strat = self.run_random_walk
                tactic = "random_walk"
            case "hs":
                strat = self.horizontal_scan_traversal_swarm
                tactic = "horizontal_scan_traversal"
            case "phs":
                strat = self.partitioned_horizontal_scan_traversal
                tactic = "partitioned_horizontal_scan_traversal"
            case "vs":
                strat = self.vertical_scan_traversal_swarm
                tactic = "vertical_scan_traversal"
            case _:
                raise ValueError("Invalid tactic")

        filename = ''

        if self.log:
            filename = str(time.time()).replace('.','')
            filename = f"./sim_logs/{tactic}_{filename}.txt"

        if not plot_boards:
            for i in tqdm(range(self.runs)):
                self.set_board()
                steps,found,taken_down = strat(plot_boards=plot_boards)
                self.save_data(i,steps,found,taken_down,filename)
        else:
            for i in range(self.runs):
                self.set_board()
                steps,found,taken_down = strat(plot_boards=plot_boards)
                self.save_data(i, steps, found, taken_down,filename)
        self.get_stats(tactic)

    def get_stats(self,tactic):

        print(f"Game stats for: {tactic}, nruns: {self.runs}")
        print(f"grid_w: {WIDTH}, grid_h {HEIGHT}, swarm_size {NUMBER_OF_DRONES_IN_SWARM}")
        # print("Hider candidate cells: ")
        # for cell in self.board.risks:
        #     print(f"{cell.loc}, Risk in cell: {cell.p:.2f}, Hiding chance: {cell.q:.2f} {"< Hidden here" if cell.contains_hider else ""}")


        metrics_find = get_all_stats(self.find_steps,self.runs)
        metrics_taken_down = get_all_stats(self.taken_down,self.runs)
        table = pd.DataFrame([metrics_find,metrics_taken_down], index=["find_steps","taken_down"])
        print("\n",table)


        print("\n Found percentage")
        found = self.found
        print(np.sum(found)/len(found)*100,"%")



        # epsilon = 0.01
        # numRuns = int(np.ceil((1.96 * np.std(self.find_steps) / epsilon) ** 2))
        # print("Minimum required simulations for find_steps:", numRuns)
        #
        # numRuns = int(np.ceil((1.96 * np.std(self.taken_down) / epsilon) ** 2))
        # print("Minimum required simulations for find_steps:", numRuns)

        return


    def run_random_walk(self, plot_boards=True, plot_interval=0.2):
        swarm = Swarm(self.board,size=NUMBER_OF_DRONES_IN_SWARM,symbol=DRONE_SYMBOL)
        found = False
        steps = 0
        for drone in swarm.swarm:
            if drone.move_next(swarm.swarm[0].start):
                found=True
        while (not found and not len(swarm.takenDown) == swarm.size):
            steps += 1
            for drone in swarm.swarm:
                if drone.random_move():
                    found = True
                    break
            if plot_boards:
                sys.stdout.write("\033[H\033[J")
                self.board.print_board()
                sys.stdout.flush()
                time.sleep(plot_interval)

        # print(f"Took {r} steps and target was", "found" if found else "not found", f", {len(swarm.takenDown)} drones were taken down.")
        return steps,found,len(swarm.takenDown)


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
            if (self.all_paths):
                new_route = self.all_paths[optimal_path_sequence[i]][optimal_path_sequence[i+1]]
            else:
                new_route = (nx.shortest_path(graph, source=optimal_path_sequence[i], target=optimal_path_sequence[i+1]))
            route.extend(new_route[1:])

        return self._run_traversal_loop_swarm(swarm, route, plot_boards, plot_interval, scanner_traversal=False)


    def divide_over_risks(self,plot_boards=True, plot_interval=0.2):
        swarm = Swarm(self.board,size=NUMBER_OF_DRONES_IN_SWARM,symbol=DRONE_SYMBOL)
        graph = self.board.graph
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")
        board = self.board

        if len(board.hider_candidates) == 0:
            return 0, 0 ,0

        sorted_risk_cells = sorted(board.hider_candidates, key=lambda cell: cell.p, reverse=True)
        ordered_risk_p = np.array([cell.p for cell in sorted_risk_cells])
        sorted_risk_cells = [cell.loc for cell in sorted_risk_cells]

        total_risk = np.sum(ordered_risk_p)
        proportional_risks = ordered_risk_p / total_risk

        n_drones = NUMBER_OF_DRONES_IN_SWARM

        allocations = proportional_risks * n_drones

        drone_assignments = np.floor(allocations).astype(int)


        remainder = n_drones - np.sum(drone_assignments)
        # Since floored we have a remainder

        fractional_parts = allocations - drone_assignments
        # get the fractional parts, i.e. 7.44 - floored = .44

        indices_for_remainder = np.argsort(fractional_parts)[::-1]
        # Sort such that we get the index for biggest fractional part in idx 0 of this list
        # Distribute remaining drones over these fractional parts
        # Alternative implementation: Distribute remainders over risk cells starting at the one with the highest risk.
        # Bc. highest fractional remainder does not necesarily mean highest risk


        for i in range(remainder):
            drone_assignments[indices_for_remainder[i]] += 1

        drone_pool = list(swarm.available)

        current_drone_idx = 0


        for i, num_to_assign in enumerate(drone_assignments):
            target_loc = sorted_risk_cells[i]

            chain = sorted_risk_cells[i:] + sorted_risk_cells[:i]
            drones_for_this_target = drone_pool[current_drone_idx : current_drone_idx + num_to_assign]

            current_drone_idx += num_to_assign

            c = 1
            for drone in drones_for_this_target:
                swarm.to_unavailable(drone)

                route = [drone.start]
                if plot_boards:
                    print(f"allocating {drone} to {target_loc}, {c}/{num_to_assign}, {ordered_risk_p[i]}")

                for checkpoint in chain:
                    if(self.all_paths):
                        new_route = self.all_paths[route[-1]][checkpoint]
                    else:
                        new_route = (nx.shortest_path(graph, source=route[-1], target=checkpoint))
                    route.extend(new_route[1:])
                drone.set_route(route)
                c+=1
        if plot_boards:
            time.sleep(2)
        return self._run_traversal_loop_individual(swarm,plot_boards, plot_interval)



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

    def partitioned_horizontal_scan_traversal(self, plot_boards=True, plot_interval=0.1):
        swarm = Swarm(self.board, size=NUMBER_OF_DRONES_IN_SWARM, symbol=DRONE_SYMBOL, init_strat="top-left")

        snake_route_start_odd_row = []
        snake_route_start_even_row = []

        for y in range(self.board.height):
            if y % 2:
                for x in range(self.board.width):
                    snake_route_start_even_row.append((x, y))
                for x in range(self.board.width - 1, -1, -1):
                    snake_route_start_odd_row.append((x, y))
            else:
                for x in range(self.board.width - 1, -1, -1):
                    snake_route_start_even_row.append((x, y))
                for x in range(self.board.width):
                    snake_route_start_odd_row.append((x, y))

        drone_start_rows = {}

        if swarm.size > self.board.height:
            drones_per_row, remainder_drones = get_whole_and_remainder(swarm.size, self.board.height)
            for y in range(self.board.height):
                num_drones_for_this_row = drones_per_row + 1 if y < remainder_drones else drones_per_row
                drone_start_rows[y] = num_drones_for_this_row
        else:
            rows_per_drone, remainder_rows = get_whole_and_remainder(self.board.height, swarm.size)
            current_row = 0
            for i in range(swarm.size):
                drone_start_rows[current_row] = 1
                spacing = rows_per_drone + 1 if i < remainder_rows else rows_per_drone
                current_row += spacing
                if current_row >= self.board.height:
                    current_row = self.board.height - 1

        drone_to_start_row = []
        for row, num_drones in drone_start_rows.items():
            for _ in range(num_drones):
                drone_to_start_row.append(row)
        for i, drone in enumerate(swarm.swarm):
            if i < len(drone_to_start_row):
                start_row = drone_to_start_row[i]

                if start_row % 2 != 0:
                    full_route = snake_route_start_even_row
                else:
                    full_route = snake_route_start_odd_row

                start_path_index = start_row * self.board.width
                start_path = [(0, y) for y in range(start_row + 1)]

                final_route = start_path + full_route[start_path_index:]
                drone.set_route(final_route)
                swarm.to_unavailable(drone)

        return self._run_traversal_loop_individual(swarm, plot_boards, plot_interval)

    def partitioned_vertical_scan_traversal(self, plot_boards=True, plot_interval=0.2):
        swarm = Swarm(self.board,size=NUMBER_OF_DRONES_IN_SWARM,symbol=DRONE_SYMBOL)
        cols_per_drone, remainder_cols = get_whole_and_remainder(self.board.width,NUMBER_OF_DRONES_IN_SWARM)


        pass



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
        steps = 1
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
            steps += 1
            if steps == len_route and scanner_traversal:
                # print("Nothing was found")
                break

        # print(f"Took {r} steps and target was", "found" if found else "not found",
        #       f"{len(swarm.takenDown)} drones were taken down.")

        # self.board.plot_drone_trajectory_animated(swarm=swarm,id=1)
        swarm.remove_swarm()
        return steps,found,len(swarm.takenDown)

    def _run_traversal_loop_individual(self,swarm,plot_boards=False,plot_interval=0.2):
        found = False
        steps = 1

        while not found and ( not len(swarm.takenDown) == swarm.size and not len(swarm.done) + len(swarm.takenDown) == swarm.size) :
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
            steps += 1

        # print(f"Took {r} steps and target was", "found" if found else "not found",
        #       f"{len(swarm.takenDown)} drones were taken down.")

        # self.board.plot_drone_trajectory_animated(swarm=swarm,id=1)
        # self.board.plot_risk_heatmap()
        swarm.remove_swarm()
        return steps,found,len(swarm.takenDown)


    # def run_dijkstraBased_strategy(self,plot_boards=True, plot_interval=0.2):
    #     swarm = self.swarm
    #     for i in range(self.runs):
    #         found = False
    #         r = 0
    #         while (not found and not len(swarm.takenDown) == swarm.size):
    #             for i in range(len(swarm.available)):
    #                 if not swarm.cell_probabilities:
    #                     break
    #                 target = swarm.cell_probabilities.popleft()
    #                 shortest_path = []
    #                 shortest_path_length = float("inf")
    #                 going = None
    #                 for drone in swarm.available:
    #                     drone_path = drone.get_route_to_goal(target)
    #                     drone_path_length = len(drone_path)
    #                     if drone_path_length < shortest_path_length:
    #                         # print("Enther the loop")
    #                         shortest_path = drone_path
    #                         shortest_path_length = drone_path_length
    #                         going = drone
    #                         # print(going.number," has shorter path to", target)
    #
    #                 print(going.number," Has now set target to: ", target)
    #                 going.set_route(shortest_path,route_length=shortest_path_length)
    #                 swarm.to_unavailable(going)
    #
    #             for drone in swarm.swarm:
    #                 if drone.move_next_from_route():
    #                     found = True
    #             if plot_boards:
    #                 sys.stdout.write("\033[H\033[J")
    #                 self.board.print_board()
    #                 sys.stdout.flush()
    #                 time.sleep(plot_interval)
    #
    #             if found:
    #                 break
    #             r+= 1
    #
    #         print(f"Took {r} steps and target was", "found" if found else "not found", f"{len(swarm.takenDown)} drones were taken down.")
    #     pass

    # def