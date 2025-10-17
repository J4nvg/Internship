from scipy.odr import odr_error
from functools import cache
from .board import Board
from .drone import Drone, Swarm
import numpy as np
import sys, time
from game_config import HIDING_STRATEGY, WIDTH, NUMBER_OF_DRONES_IN_SWARM, DRONE_SYMBOL, NUMBER_OF_HIDER_CANDIDATES,N_HIDERS
import networkx as nx
from .helpers import get_optimal_permutation_MD, mean_var, confidence_interval, min_max, get_all_stats, \
    get_whole_and_remainder
from tqdm import tqdm
import time
import pandas as pd
import os


@cache
def get_all_paths(width, height):
    board = Board(width=width, n_hider_candidates=0, n_hiders=0,hiding_strategy=HIDING_STRATEGY)
    return dict(nx.all_pairs_shortest_path(board.graph))

class Simulation():
    def __init__(self, n_runs=1, log=False, width=WIDTH, n_hiders=N_HIDERS,n_hider_candidates=NUMBER_OF_HIDER_CANDIDATES,swarm_size=NUMBER_OF_DRONES_IN_SWARM,hiding_strategy=HIDING_STRATEGY):
        self.runs = n_runs

        self.n_hiders = n_hiders
        self.n_hider_candidates = n_hider_candidates
        self.swarm_size = swarm_size
        self.hiding_strategy = hiding_strategy
        self.width = width

        self.board = Board(width=width, n_hider_candidates=n_hider_candidates,n_hiders=n_hiders,hiding_strategy=hiding_strategy)
        self.swarm = Swarm(self.board, size=swarm_size, symbol=DRONE_SYMBOL)

        self.log = log
        # self.board.plot_q_heatmap()
        self.find_steps = np.zeros(n_runs)

        self.taken_down = np.zeros(n_runs)

        self.all_found = np.zeros(n_runs)

        self.frac_area_covered = np.zeros(n_runs)
        self.hider_frac_found = np.zeros(n_runs)

        self.mean_distance_travelled = np.zeros(n_runs)

        self.total_distance_covered = np.zeros(n_runs)

        self.file_name = ''
        self.log_dir = "./data/sim_logs/"
        self.res_dir = "./data/sim_results/"

        self.all_paths = None
        if self.runs > 10:
            self.all_paths = get_all_paths(width, width)

    def save_data(self, i, steps, all_found, taken_down, unique_cells_covered, mean_distance_travelled, total_distance_covered,hider_frac_found, filename=''):
        self.find_steps[i] = steps

        self.taken_down[i] = taken_down

        self.all_found[i] = all_found
        frac_area_covered = unique_cells_covered / (self.board.width * self.board.height)
        self.frac_area_covered[i] = frac_area_covered

        self.mean_distance_travelled[i] = mean_distance_travelled

        self.total_distance_covered[i] = total_distance_covered

        self.hider_frac_found[i] = hider_frac_found


        if filename != '':
            with open(f"{self.log_dir}/{filename}", "a") as f:
                f.write(f"{i + 1},{steps},{all_found},{taken_down},{frac_area_covered},{mean_distance_travelled},{total_distance_covered},{hider_frac_found}\n")

    def start_main_sim_loop_single_tactic_metrics(self, plot_boards=False, plot_interval=0.2, tactic="ttbp"):

        tactic_map = {
            "ttbp": (self.together_traverse_best_permutation,"together_traverse_best_permutation"),
            "dor": (self.divide_over_risks,"divide_over_risks"),
            "rndm": (self.run_random_walk,"random_walk"),
            "hs": (self.horizontal_scan_traversal_swarm,"horizontal_scan_traversal"),
            "phs": (self.partitioned_horizontal_scan_traversal,"partitioned_horizontal_scan_traversal"),
            "vs": (self.vertical_scan_traversal_swarm,"vertical_scan_traversal"),
            "sp": (self.spiral_traversal_swarm,"spiral_traversal_swarm"),
        }

        if tactic not in tactic_map:
            raise ValueError(f"Invalid tactic: {tactic}")
        strat,tactic = tactic_map[tactic]


        filename = f"T{tactic}_W{self.width}_D{self.swarm_size}_C{self.n_hider_candidates}_H{self.n_hiders}_RUNS{self.runs}.csv"
        self.file_name = filename
        if self.log:
            if os.path.exists(f"{self.log_dir}/{filename}"):
                    os.remove(f"{self.log_dir}/{filename}")
            with open(f"{self.log_dir}/{filename}", "a") as f:
                f.write(f"{tactic}\n")
                f.write(f"i,steps,all_found,taken_down,frac_area_covered,mean_distance_travelled,total_distance_covered,hider_frac_found\n")

        iterator = tqdm(range(self.runs)) if not plot_boards else range(self.runs)
        for i in iterator:
            self.board.reset()
            self.swarm.reset()

            steps, all_found, taken_down,frac_found = strat(plot_boards=plot_boards, plot_interval=plot_interval)

            unique_cells_covered = set({})
            distance_travelled = np.zeros(self.swarm.size)
            for j, drone in enumerate(self.swarm.swarm):
                history = drone.route_history
                distance_travelled[j] = len(history)
                for cell in history:
                    unique_cells_covered.add(cell)

            self.save_data(i=i, steps=steps, all_found=all_found, taken_down=taken_down,
                           unique_cells_covered=len(unique_cells_covered),
                           mean_distance_travelled=np.mean(distance_travelled), total_distance_covered=np.sum(distance_travelled),hider_frac_found=frac_found,filename=filename)

        self.generate_stats(tactic)

    def generate_stats(self, tactic):

        print(f"Game stats for: {tactic}, nruns: {self.runs}")
        print(f"grid_w: {self.width}, grid_h {self.width}, swarm_size {self.swarm_size}")
        metrics_find = get_all_stats(self.find_steps, self.runs)

        metrics_taken_down = get_all_stats(self.taken_down, self.runs)
        metrics_frac_area_covered = get_all_stats(self.frac_area_covered, self.runs)

        metrics_mean_distance_travelled = get_all_stats(self.mean_distance_travelled, self.runs)
        total_distance_covered = get_all_stats(self.total_distance_covered, self.runs)

        metrics_frac_found = get_all_stats(self.hider_frac_found, self.runs)

        table = pd.DataFrame(
            [metrics_find, metrics_taken_down, metrics_frac_area_covered, metrics_mean_distance_travelled,total_distance_covered,metrics_frac_found],
            index=["find_steps", "taken_down", "area_covered", "mean_distance_travelled","total_distance_covered","hider_frac_found"])
        pd.set_option('display.max_rows', len(table))

        print("\n", table)
        pd.reset_option('display.max_rows')

        print("\n All_found percentage")
        all_found = self.all_found
        all_found_percentage = np.sum(all_found) / len(all_found)
        print(f"{all_found_percentage:.2%}")

        if self.log:
            table.to_csv(f"{self.res_dir}/{self.file_name}", sep='\t', encoding='utf-8', header=True)
            with open(f"{self.res_dir}/{self.file_name}", "a") as f:
                f.write(f"Found\t{all_found_percentage:.2%}\n")


        self.all_metrics = (table,all_found_percentage)


        epsilon = 0.01
        numRuns = int(np.ceil((1.96 * np.std(self.find_steps) / epsilon) ** 2))
        print("Minimum required simulations for find_steps:", numRuns)

        numRuns = int(np.ceil((1.96 * np.std(self.taken_down) / epsilon) ** 2))
        print("Minimum required simulations for taken_down:", numRuns)

        return

    def run_random_walk(self, plot_boards=True, plot_interval=0.2):
        swarm = self.swarm
        n_found = 0
        n_hiders = self.board.n_hiders
        all_found = False
        steps = 1
        for drone in swarm.swarm:
            if drone.move_next(swarm.swarm[0].start):
                n_found += 1
                all_found = True if n_found == n_hiders else False
        while not all_found and not len(swarm.takenDown) == swarm.size:
            steps += 1
            for drone in swarm.swarm:
                if drone.random_move():
                    n_found += 1
                    all_found = True if n_found == n_hiders else False
                    if all_found:
                        break
            if plot_boards:
                sys.stdout.write("\033[H\033[J")
                self.board.print_board()
                sys.stdout.flush()
                time.sleep(plot_interval)

        # print(f"Took {r} steps and target was", "found" if found else "not found", f", {len(swarm.takenDown)} drones were taken down.")
        return steps, all_found, len(swarm.takenDown), n_found/n_hiders

    def together_traverse_best_permutation(self, plot_boards=True, plot_interval=0.2):
        swarm = self.swarm
        graph = self.board.graph
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        board = self.board
        if len(board.hider_candidates) == 0:
            return

        sample_drone = swarm.available[0]

        hider_candidate_locations = [cell.loc for cell in board.hider_candidates]

        optimal_path_sequence, shortest_total_distance = get_optimal_permutation_MD(sample_drone.start,
                                                                                    hider_candidate_locations)

        route = [sample_drone.start]

        for i in range(len(optimal_path_sequence) - 1):
            if (self.all_paths):
                new_route = self.all_paths[optimal_path_sequence[i]][optimal_path_sequence[i + 1]]
            else:
                new_route = (
                    nx.shortest_path(graph, source=optimal_path_sequence[i], target=optimal_path_sequence[i + 1]))
            route.extend(new_route[1:])

        return self._run_traversal_loop_swarm(swarm, route, plot_boards, plot_interval, scanner_traversal=False)

    def divide_over_risks(self, plot_boards=True, plot_interval=0.2):
        swarm = self.swarm
        graph = self.board.graph
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")
        board = self.board

        if len(board.hider_candidates) == 0:
            return 0, 0, 0

        sorted_risk_cells = sorted(board.hider_candidates, key=lambda cell: 1-cell.p, reverse=True)
        ordered_risk_p = np.array([1-cell.p for cell in sorted_risk_cells])
        sorted_risk_cells = [cell.loc for cell in sorted_risk_cells]

        total_risk = np.sum(ordered_risk_p)
        proportional_risks = ordered_risk_p / total_risk

        n_drones = self.swarm_size

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
            drones_for_this_target = drone_pool[current_drone_idx: current_drone_idx + num_to_assign]

            current_drone_idx += num_to_assign

            c = 1
            for drone in drones_for_this_target:
                swarm.to_unavailable(drone)

                route = [drone.start]
                if plot_boards:
                    print(f"allocating {drone} to {target_loc}, {c}/{num_to_assign}, {ordered_risk_p[i]}")

                for checkpoint in chain:
                    if (self.all_paths):
                        new_route = self.all_paths[route[-1]][checkpoint]
                    else:
                        new_route = (nx.shortest_path(graph, source=route[-1], target=checkpoint))
                    route.extend(new_route[1:])
                drone.set_route(route)
                c += 1
        if plot_boards:
            time.sleep(2)
        return self._run_traversal_loop_individual(swarm, plot_boards, plot_interval)

    def horizontal_scan_traversal_swarm(self, plot_boards=True, plot_interval=0.2):
        swarm = self.swarm
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

        return self._run_traversal_loop_swarm(swarm, route, plot_boards, plot_interval, scanner_traversal=True)

    def partitioned_horizontal_scan_traversal(self, plot_boards=True, plot_interval=0.2):
        swarm = self.swarm

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

    def vertical_scan_traversal_swarm(self, plot_boards=True, plot_interval=0.2):
        swarm = self.swarm
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        route = [swarm.swarm[0].start]

        for y in range(self.board.height):
            if y % 2:
                for x in range(self.board.width - 1, -1, -1):
                    route.append((y, x))
            else:
                for x in range(self.board.width):
                    route.append((y, x))

        return self._run_traversal_loop_swarm(swarm, route, plot_boards, plot_interval, scanner_traversal=True)

    def spiral_traversal_swarm(self, plot_boards=True, plot_interval=0.2):
        swarm = self.swarm
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        route = [swarm.swarm[0].start]

        h = self.board.height
        w = self.board.width

        top, bottom = 0, h - 1
        left, right = 0, w - 1


        while left <= right and top <= bottom:
            # left -> right along the current top row
            for x in range(left, right + 1):
                route.append((top, x))
            top += 1

            # top -> bottom along the current right column
            for y in range(top, bottom + 1):
                route.append((y, right))
            right -= 1

            # right -> left along the current bottom row (if remaining)
            if top <= bottom:
                for x in range(right, left - 1, -1):
                    route.append((bottom, x))
                bottom -= 1

            # bottom -> top along the current left column (if remaining)
            if left <= right:
                for y in range(bottom, top - 1, -1):
                    route.append((y, left))
                left += 1

        return self._run_traversal_loop_swarm(
            swarm, route, plot_boards, plot_interval, scanner_traversal=True
        )

    def _run_traversal_loop_swarm(self, swarm, route, plot_boards=False, plot_interval=0.2, scanner_traversal=False):
        n_found = 0
        n_hiders = self.board.n_hiders
        all_found = False
        steps = 1
        len_route = len(route)

        for drone in swarm.swarm:
            drone.set_route(route)
            swarm.to_unavailable(drone)

        while not all_found and not len(swarm.takenDown) == swarm.size:
            for drone in swarm.swarm:
                if drone.move_next_from_route():
                    n_found += 1
                    all_found = True if n_found == n_hiders else False
                    # print(f"\nTarget found by Drone {drone.number} at location {drone.current_loc}!")
            if plot_boards:
                sys.stdout.write("\033[H\033[J")
                self.board.print_board()
                sys.stdout.flush()
                time.sleep(plot_interval)

            if all_found:
                break
            steps += 1
            if steps == len_route and scanner_traversal:
                # print("Nothing was found")
                break

        # print(f"Took {r} steps and target was", "found" if found else "not found",
        #       f"{len(swarm.takenDown)} drones were taken down.")

        # self.board.plot_drone_trajectory_animated(swarm=swarm,id=1)
        swarm.remove_swarm()
        return steps, all_found, len(swarm.takenDown),n_found/n_hiders

    def _run_traversal_loop_individual(self, swarm, plot_boards=False, plot_interval=0.2):
        n_found = 0
        n_hiders = self.board.n_hiders
        all_found = False
        steps = 1

        while not all_found and (
                not len(swarm.takenDown) == swarm.size and not len(swarm.done) + len(swarm.takenDown) == swarm.size):
            for drone in swarm.swarm:
                if drone.move_next_from_route():
                    n_found += 1
                    all_found = True if n_found == n_hiders else False
                    # print(f"\nTarget found by Drone {drone.number} at location {drone.current_loc}!")
            if plot_boards:
                sys.stdout.write("\033[H\033[J")
                self.board.print_board()
                sys.stdout.flush()
                time.sleep(plot_interval)

            if all_found:
                break
            steps += 1

        # print(f"Took {r} steps and target was", "found" if found else "not found",
        #       f"{len(swarm.takenDown)} drones were taken down.")

        # self.board.plot_drone_trajectory_animated(swarm=swarm,id=1)
        # self.board.plot_risk_heatmap()
        swarm.remove_swarm()
        return steps, all_found, len(swarm.takenDown),n_found/n_hiders
