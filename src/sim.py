from functools import cache
from .board import Board
from .drone import  Swarm
import numpy as np
import sys
from game_config import HIDING_STRATEGY,SUCCESS_PROBABILITIES_CHOSEN,Pi_DICT,WIDTH, NUMBER_OF_DRONES_IN_SWARM, DRONE_SYMBOL, NUMBER_OF_HIDER_CANDIDATES,N_HIDERS
import networkx as nx
from .helpers import get_optimal_permutation_md, get_all_stats, get_whole_and_remainder, get_all_stats_binom, \
    route_interpolator, best_route_discount_distance, route_interpolator_avoid_nodes, manhattan_distance, \
    lidbetter_dynamic_route_interpolator
from tqdm import tqdm
import time
import pandas as pd
import os
import csv
from collections import deque
import heapq

@cache
def get_all_paths(width, height):
    board = Board(width=width, n_hider_candidates=0, n_hiders=0,hiding_strategy=HIDING_STRATEGY,success_probabilities=Pi_DICT["SUCCESS_PROBABILITIES_INITIAL"])
    return dict(nx.all_pairs_shortest_path(board.graph))

class Simulation():
    def __init__(self, n_runs=1, log=False, width=WIDTH, n_hiders=N_HIDERS,n_hider_candidates=NUMBER_OF_HIDER_CANDIDATES,swarm_size=NUMBER_OF_DRONES_IN_SWARM,hiding_strategy=HIDING_STRATEGY,success_p=SUCCESS_PROBABILITIES_CHOSEN):
        self.runs = n_runs

        self.pi_dict = Pi_DICT
        self.success_probabilities = self.pi_dict[success_p]

        self.n_hiders = n_hiders
        self.n_hider_candidates = n_hider_candidates
        self.swarm_size = swarm_size
        self.hiding_strategy = hiding_strategy
        self.width = width

        self.board = Board(width=width, n_hider_candidates=n_hider_candidates,n_hiders=n_hiders,hiding_strategy=hiding_strategy,success_probabilities=self.success_probabilities)
        self.swarm = Swarm(self.board, size=swarm_size, symbol=DRONE_SYMBOL)

        self.log = log
        # self.board.plot_q_heatmap()
        self.steps = np.zeros(n_runs)

        self.taken_down = np.zeros(n_runs)

        self.all_found = np.zeros(n_runs)

        self.frac_area_covered = np.zeros(n_runs)
        self.hider_frac_found = np.zeros(n_runs)

        self.mean_distance_travelled = np.zeros(n_runs)

        self.total_distance_covered = np.zeros(n_runs)

        self.file_name = ''
        self.log_dir = f"./data/sim_logs/{success_p}"
        self.res_dir = f"./data/sim_results/{success_p}"

        self.all_paths = None
        if self.runs > 10:
            self.all_paths = get_all_paths(width, width)


    def save_data(self, i, steps, all_found, taken_down, unique_cells_covered, mean_distance_travelled, total_distance_covered,hider_frac_found, filename=''):
        self.steps[i] = steps

        self.taken_down[i] = taken_down

        all_found = int(all_found)
        self.all_found[i] = all_found
        frac_area_covered = unique_cells_covered / (self.board.width * self.board.height)
        self.frac_area_covered[i] = frac_area_covered

        self.mean_distance_travelled[i] = mean_distance_travelled

        self.total_distance_covered[i] = total_distance_covered

        self.hider_frac_found[i] = hider_frac_found

        if self.log:
            with open(f"{self.log_dir}/{filename}", "a", newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                data_row = [
                    i + 1,
                    steps,
                    all_found,
                    taken_down,
                    frac_area_covered,
                    mean_distance_travelled,
                    total_distance_covered,
                    hider_frac_found
                ]

                writer.writerow(data_row)

    def start_main_sim_loop_single_tactic_metrics(self, plot_boards=False, plot_hm=False, plot_interval=0.2, tactic="ttbp"):

        tactic_map = {
            "ttbp": (self.together_traverse_best_permutation,"together_traverse_best_permutation"),
            "dor": (self.divide_over_risks,"divide_over_risks"),
            "rndm": (self.run_random_walk,"random_walk"),
            "hs": (self.horizontal_scan_traversal_swarm,"horizontal_scan_traversal"),
            "phs": (self.partitioned_horizontal_scan_traversal,"partitioned_horizontal_scan_traversal"),
            "sp": (self.spiral_traversal_swarm,"spiral_traversal_swarm"),
            "lb": (self.lidbetter_swarm,"lidbetter"),
            "toq": (self.traverse_ordered_qa,"traverse_ordered_qa"),
            "tpq": (self.traverse_weighted_qa,"traverse_p_qa"),
            "dd": (self.discounted_distance,"discounted_distance"),
            "ddr": (self.discounted_distance_rev,"discounted_distance_reverse"),
            "sl": (self.shared_list,"shared_list"),
            "sl_heap": (self.shared_list_heap,"shared_list_heap"),
        }

        if tactic not in tactic_map:
            raise ValueError(f"Invalid tactic: {tactic}")
        strat,tactic = tactic_map[tactic]


        filename = f"T-{tactic}-W-{self.width}-HS-{self.hiding_strategy}-D-{self.swarm_size}-C-{self.n_hider_candidates}-H-{self.n_hiders}-RUNS-{self.runs}.csv"
        self.file_name = filename

        fieldnames = [
            "i", "steps", "all_found", "taken_down",
            "frac_area_covered", "mean_distance_travelled",
            "total_distance_covered", "hider_frac_found"
        ]
        if self.log:
            os.makedirs(self.log_dir, exist_ok=True)

            file_path = os.path.join(self.log_dir, filename)

            if os.path.exists(file_path):
                os.remove(file_path)

            with open(file_path, "a", newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(fieldnames)

        iterator = tqdm(range(self.runs)) if not plot_boards else range(self.runs)
        for i in iterator:
            self.board.reset()
            self.swarm.reset()

            steps, all_found, taken_down,frac_found = strat(plot_boards=plot_boards, plot_hm=plot_hm, plot_interval=plot_interval)

            distance_travelled = np.array([d.steps_taken for d in self.swarm.swarm])
            unique_cells_covered = len(self.swarm.visited_cells)
            # for j, drone in enumerate(self.swarm.swarm):
            #     history = drone.route_history_counter
            #     distance_travelled[j] = len(history)
            #     for cell in history:
            #         unique_cells_covered.add(cell)

            self.save_data(i=i, steps=steps, all_found=all_found, taken_down=taken_down,
                           unique_cells_covered=unique_cells_covered,
                           mean_distance_travelled=np.mean(distance_travelled),
                           total_distance_covered=np.sum(distance_travelled),
                           hider_frac_found=frac_found, filename=filename)

        self.generate_stats(tactic)

    def generate_stats(self, tactic):

        print(f"Game stats for: {tactic}, nruns: {self.runs}")
        print(f"grid_w: {self.width}, grid_h {self.width}, swarm_size {self.swarm_size}")
        metrics_find = get_all_stats(self.steps, self.runs)

        metrics_taken_down = get_all_stats(self.taken_down, self.runs)

        metrics_frac_area_covered = get_all_stats(self.frac_area_covered, self.runs)

        metrics_mean_distance_travelled = get_all_stats(self.mean_distance_travelled, self.runs)

        total_distance_covered = get_all_stats(self.total_distance_covered, self.runs)

        metrics_frac_found = get_all_stats(self.hider_frac_found, self.runs)

        metrics_all_found = get_all_stats_binom(self.all_found, self.runs)

        table = pd.DataFrame(
            [metrics_find, metrics_taken_down, metrics_frac_area_covered, metrics_mean_distance_travelled,total_distance_covered,metrics_frac_found,metrics_all_found],
            index=["steps", "taken_down", "area_covered", "mean_distance_travelled","total_distance_covered","hider_frac_found","all_found"])
        pd.set_option('display.max_rows', len(table))

        print("\n", table)
        pd.reset_option('display.max_rows')

        if self.log:
            os.makedirs(self.res_dir, exist_ok=True)
            table.to_csv(f"{self.res_dir}/{self.file_name}", sep='\t', encoding='utf-8', header=True)

        epsilon = 0.01
        numRuns = int(np.ceil((1.96 * np.std(self.steps) / epsilon) ** 2))
        print("Minimum required simulations for steps:", numRuns)

        numRuns = int(np.ceil((1.96 * np.std(self.taken_down) / epsilon) ** 2))
        print("Minimum required simulations for taken_down:", numRuns)

        return

    def run_random_walk(self, plot_boards=False, plot_hm=False, plot_interval=0.2):
        swarm = self.swarm
        n_found = 0
        n_hiders = self.board.n_hiders
        all_found = False
        steps = 1
        for drone in swarm.swarm:
            if drone.move_next(swarm.swarm[0].start)[0]:
                n_found += 1
                all_found = True if n_found == n_hiders else False
        max_steps = self.board.width**2 * 10 # = 4000 for 20x20, while results stabilize after 2k
        while not all_found and not len(swarm.takenDown) == swarm.size and not steps > max_steps:
            steps += 1
            for drone in swarm.swarm:
                if drone.random_move(self.board)[0]:
                    n_found += 1
                    all_found = True if n_found == n_hiders else False
                    if all_found:
                        break
            if plot_boards:
                sys.stdout.write("\033[H\033[J")
                self.board.print_board(plot_hm)
                sys.stdout.flush()
                time.sleep(plot_interval)

        # print(f"Took {r} steps and target was", "found" if found else "not found", f", {len(swarm.takenDown)} drones were taken down.")
        return steps, all_found, len(swarm.takenDown), n_found/n_hiders

    def together_traverse_best_permutation(self, plot_boards=False, plot_hm=False, plot_interval=0.2):
        swarm = self.swarm
        graph = self.board.graph
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        board = self.board
        if len(board.hider_candidates) == 0:
            return

        sample_drone = swarm.swarm[0]

        hider_candidate_locations = [cell.loc for cell in board.hider_candidates]

        optimal_path_sequence, shortest_total_distance = get_optimal_permutation_md(sample_drone.start,
                                                                                    hider_candidate_locations)
        route = route_interpolator(optimal_path_sequence,sample_drone.start,graph,self.all_paths)

        return self._run_traversal_loop_swarm(swarm, route, plot_boards,plot_hm, plot_interval, terminate_after_route=False)

    def divide_over_risks(self, plot_boards=False, plot_hm=False, plot_interval=0.2):
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
        # Bc. highest fractional remainder does not necessarily mean highest risk

        for i in range(remainder):
            drone_assignments[indices_for_remainder[i]] += 1

        drone_pool = list(swarm.swarm)

        current_drone_idx = 0

        for i, num_to_assign in enumerate(drone_assignments):
            target_loc = sorted_risk_cells[i]

            chain = sorted_risk_cells[i:] + sorted_risk_cells[:i]
            drones_for_this_target = drone_pool[current_drone_idx: current_drone_idx + num_to_assign]

            current_drone_idx += num_to_assign

            c = 1
            for drone in drones_for_this_target:

                if plot_boards:
                    print(f"allocating {drone} to {target_loc}, {c}/{num_to_assign}, {ordered_risk_p[i]}")

                route = route_interpolator(visit_order=chain,start=drone.start,graph=graph,all_paths=self.all_paths)

                drone.set_route(route)
                c += 1
        if plot_boards:
            time.sleep(2)
        return self._run_traversal_loop_individual(swarm, plot_boards,plot_hm, plot_interval)

    def horizontal_scan_traversal_swarm(self, plot_boards=False, plot_hm=False, plot_interval=0.1):
        swarm = self.swarm
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        if not "hs" in self.board.route_cache:

            route = [swarm.swarm[0].start]

            for y in range(self.board.height):
                if y % 2:
                    for x in range(self.board.width - 1, -1, -1):
                        route.append((x, y))
                else:
                    for x in range(self.board.width):
                        route.append((x, y))
            self.board.route_cache["hs"] = route
        else:
            route = self.board.route_cache["hs"]

        return self._run_traversal_loop_swarm(swarm, route,plot_boards,plot_hm, plot_interval, terminate_after_route=True)

    def partitioned_horizontal_scan_traversal(self, plot_boards=False, plot_hm=False, plot_interval=0.2):
        swarm = self.swarm

        if not "snake_odd" in self.board.route_cache:
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
            self.board.route_cache["snake_odd"] = snake_route_start_odd_row
            self.board.route_cache["snake_even"] = snake_route_start_even_row
        else:
            snake_route_start_odd_row = self.board.route_cache["snake_odd"]
            snake_route_start_even_row = self.board.route_cache["snake_even"]

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

        return self._run_traversal_loop_individual(swarm,plot_boards,plot_hm, plot_interval)

    def spiral_traversal_swarm(self, plot_boards=False, plot_hm=False, plot_interval=0.1):
        swarm = self.swarm
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        if not "sp" in self.board.route_cache:
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

            self.board.route_cache["sp"] = route

        route = self.board.route_cache["sp"]

        return self._run_traversal_loop_swarm(
            swarm, route,plot_boards,plot_hm, plot_interval, terminate_after_route=True
        )

    def lidbetter_swarm(self, plot_boards=False, plot_hm=False, plot_interval=0.2):
        """
        A subset of possible hiding locations is chosen by the q_a formula, the rest of the cells are explored uniformly at random.

        """
        swarm = self.swarm
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")
        visit_cells_order = []

        board = self.board
        rng = board.rng
        q_a_subset,q_a_values = board.qa
        chosen_subset = rng.choice(q_a_subset, p=q_a_values)
        visit_cells_order.extend([cell.loc for cell in chosen_subset])
        all_candidates_set = set(board.hider_candidates)
        chosen_subset_set = set(chosen_subset)

        remaining_cells_list = list(all_candidates_set - chosen_subset_set)
        rng.shuffle(remaining_cells_list)

        visit_cells_order.extend([cell.loc for cell in remaining_cells_list])

        start = swarm.swarm[0].start

        # route = route_interpolator(visit_cells_order,start,board.graph,self.all_paths) old method
        route = lidbetter_dynamic_route_interpolator(visit_cells_order,start,board.graph,self.all_paths)

        return self._run_traversal_loop_swarm(
            swarm, route,plot_boards,plot_hm, plot_interval, terminate_after_route=False
        )

    def traverse_ordered_qa(self, plot_boards=False, plot_hm=False, plot_interval=0.2):
        """
        Order q_a descending, assign the highest subset to drone 1, 2nd highest subset to drone 2, etc. and wrap around.
        :return:
        """
        swarm = self.swarm
        graph = self.board.graph
        board = self.board
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        q_a_subset,q_a_values = board.qa

        zipped_list = list(zip(q_a_values, q_a_subset))
        sorted_pairs = sorted(zipped_list, key=lambda x: x[0],reverse=True)
        q_a_values_sorted, q_a_subset_sorted = zip(*sorted_pairs)
        # q_a_values = list(q_a_values_sorted)
        q_a_subset = list(q_a_subset_sorted)

        start = swarm.swarm[0].start
        num_subsets = len(q_a_subset)

        # print("Q_A_VALUES")
        # print([f"{x:.2f}" for x in q_a_values])
        # print("Q_A_subsets")
        # print([[cell.loc for cell in subset] for subset in q_a_subset])
        # print("\n")

        # assigns route drone 1 to q_a_subset[0], [1], [2], ..., q_a_subset[n]
        # assigns route drone 2 to q_a_subset[1], [2], [n], ..., q_a_subset[0] etc.
        for i, drone in enumerate(swarm.swarm):
            visit_cells_order = [start]
            start_index = i % num_subsets  # i.e. wraps around
            for j in range(num_subsets):
                current_idx = (start_index + j) % num_subsets # i.e. wraps around
                subset = q_a_subset[current_idx]
                for cell in subset:
                    visit_cells_order.append(cell.loc)

            fullroute = route_interpolator(visit_cells_order,start,graph,self.all_paths)
            # print(f"allocating {drone} to visit order {visit_cells_order}")
            drone.set_route(fullroute)
        # if plot_boards:
        #     time.sleep(2)
        return self._run_traversal_loop_individual(swarm,plot_boards,plot_hm, plot_interval)

    def traverse_weighted_qa(self, plot_boards=False, plot_hm=False, plot_interval=0.2):
        """
        Assign subset A with weight Q_a to a drone, rest of the locations uniform at random, for each drone in the swarm
        """
        swarm = self.swarm
        graph = self.board.graph
        board = self.board
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")

        rng = board.rng

        q_a_subset, q_a_values = board.qa
        # print("Q_A_VALUES")
        # print([f"{x:.2f}" for x in q_a_values])
        # print("Q_A_subsets")
        # print([[cell.loc for cell in subset] for subset in q_a_subset])
        # print("\n")

        start = swarm.swarm[0].start
        # selecting and adding a weighted-random subset, and then adding all remaining candidate cells in a shuffled (uniform random) order.
        # i.e. lidbetter but independent per drone
        for drone in swarm.swarm:
            visit_cells_order = [start]

            chosen_subset = rng.choice(q_a_subset, p=q_a_values)
            visit_cells_order.extend([cell.loc for cell in chosen_subset])
            all_candidates_set = set(board.hider_candidates)
            chosen_subset_set = set(chosen_subset)

            remaining_cells_list = list(all_candidates_set - chosen_subset_set)
            rng.shuffle(remaining_cells_list)
            visit_cells_order.extend([cell.loc for cell in remaining_cells_list])

            fullroute = route_interpolator(visit_cells_order, start, graph, self.all_paths)

            drone.set_route(fullroute)

        return self._run_traversal_loop_individual(swarm,plot_boards,plot_hm, plot_interval)

    def discounted_distance(self, plot_boards=False, plot_hm=False, plot_interval=0.2):
        """
        Set the 'optimal' permutation of routes based on: sum of distance * 1-p_i over all candidate points
        """
        swarm = self.swarm
        graph = self.board.graph
        board = self.board
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")
        start_loc = swarm.swarm[0].start
        start_cell = graph.nodes[start_loc]['cell']

        visit_cells_order = best_route_discount_distance(board.hider_candidates, start_cell)
        fullroute = route_interpolator(visit_cells_order,start_loc,graph,self.all_paths)

        return self._run_traversal_loop_swarm(swarm, fullroute,plot_boards,plot_hm, plot_interval, terminate_after_route=True)

    def discounted_distance_rev(self, plot_boards=False, plot_hm=False, plot_interval=0.2):
        """
        Set the 'optimal' permutation of routes based on: sum of distance * p_i over all candidate points
        """
        swarm = self.swarm
        graph = self.board.graph
        board = self.board
        if not swarm.same_start:
            raise Exception(f"together_to_candidates not implemented yet for {swarm.init_strat}")
        start_loc = swarm.swarm[0].start
        start_cell = graph.nodes[start_loc]['cell']

        visit_cells_order = best_route_discount_distance(board.hider_candidates, start_cell, rev=True)
        fullroute = route_interpolator(visit_cells_order,start_loc,graph,self.all_paths)

        return self._run_traversal_loop_swarm(swarm, fullroute,plot_boards,plot_hm, plot_interval, terminate_after_route=True)

    def shared_list(self, plot_boards=False, plot_hm=False, plot_interval=0.2):
        """
        Drones in swarm have a shared goal list and can communicate what has been explored and when one dies
        """
        swarm = self.swarm
        graph = self.board.graph

        board = self.board

        cells_to_visit_list = [hider.loc for hider in board.hider_candidates]
        cells_to_visit_deque = deque(cells_to_visit_list)

        mapping = {
            "to_visit" : deque(cells_to_visit_deque)
        }

        for drone in swarm.swarm:
            #Initialize the first n_hider_candidate drones with a goal
            if not mapping["to_visit"]:
                break

            first_goal = mapping["to_visit"].popleft()
            mapping[drone] = first_goal

            route = route_interpolator([first_goal], drone.start, graph, self.all_paths)
            drone.set_route(route)

        return self._run_traversal_loop_individual_shared_list(swarm,mapping,plot_boards,plot_hm, plot_interval)

    def shared_list_heap(self, plot_boards=False, plot_hm=False, plot_interval=0.2):
        """
        Drones in swarm have a shared goal list and can communicate what has been explored and when one dies

        """

        swarm = self.swarm
        graph = self.board.graph

        board = self.board

        cells_to_visit_heap = [(1 - cell.p, cell.loc) for cell in board.hider_candidates]
        heapq.heapify(cells_to_visit_heap)

        mapping = {
            "to_visit" : cells_to_visit_heap
        }

        for drone in swarm.swarm:
            #Initialize the first n_hider_candidate drones with a goal
            if not mapping["to_visit"]:
                break

            priority, first_goal = heapq.heappop(mapping["to_visit"])
            mapping[drone] = first_goal

            route = route_interpolator([first_goal], drone.start, graph, self.all_paths)
            drone.set_route(route)

        return self._run_traversal_loop_individual_shared_list(swarm,mapping,plot_boards,plot_hm, plot_interval,heaped=True)

    def _run_traversal_loop_swarm(self, swarm, route, plot_boards=False, plot_hm=False, plot_interval=0.2, terminate_after_route=False):
        n_found = 0
        n_hiders = self.board.n_hiders
        all_found = False
        steps = 1
        len_route = len(route)

        for drone in swarm.swarm:
            drone.set_route(route)

        while not all_found and not len(swarm.takenDown) == swarm.size:
            for drone in swarm.swarm:
                if drone.move_next_from_route()[0]:
                    n_found += 1
                    all_found = True if n_found == n_hiders else False
            if plot_boards:
                sys.stdout.write("\033[H\033[J") # Clear screen
                self.board.print_board(plot_hm)
                sys.stdout.flush()
                time.sleep(plot_interval)

            if all_found:
                break
            steps += 1
            if steps == len_route and terminate_after_route:
                break
        swarm.remove_swarm()
        return steps, all_found, len(swarm.takenDown),n_found/n_hiders

    def _run_traversal_loop_individual(self, swarm, plot_boards=False, plot_hm=False, plot_interval=0.2):
        n_found = 0
        n_hiders = self.board.n_hiders
        all_found = False
        steps = 1

        while not all_found and (not len(swarm.takenDown) == swarm.size and not len(swarm.done) + len(swarm.takenDown) == swarm.size):
            for drone in swarm.swarm:
                if drone.move_next_from_route()[0]:
                    n_found += 1
                    all_found = True if n_found == n_hiders else False
            if plot_boards:
                sys.stdout.write("\033[H\033[J")
                self.board.print_board(plot_hm)
                sys.stdout.flush()
                time.sleep(plot_interval)

            if all_found:
                break
            steps += 1
        swarm.remove_swarm()
        return steps, all_found, len(swarm.takenDown),n_found/n_hiders

    def _run_traversal_loop_individual_shared_list(self, swarm, mapping, plot_boards=False, plot_hm=False, plot_interval=0.2, heaped=False):

        n_found = 0
        n_hiders = self.board.n_hiders
        all_found = False
        steps = 1

        graph = self.board.graph
        to_visit = mapping["to_visit"]  # shared list
        visited_candidates = set({})
        idle = set({})

        swarm_set = set(swarm.swarm)
        for drone in swarm.swarm:
            if not drone in mapping:
                idle.add(drone)

        active = swarm_set - idle

        while not all_found and len(swarm.takenDown) < swarm.size:
            available = list(idle) # perhaps this can be improved
            # print(f"idle: {idle}")
            # print(f"active: {active}")
            # print(f"taken_down: {swarm.takenDown}")
            # print(f"complete swarm: {swarm.swarm}")
            # print(f"mapping: {mapping}")

            if (heaped):
                while available and to_visit:
                    # Pop the safest target available
                    priority, target_loc = heapq.heappop(to_visit)

                    # Find the drone that can reach this high-priority target fastest
                    closest_drone = None
                    min_dist = float('inf')

                    for d in available:
                        dist = manhattan_distance(target_loc, d.current_loc)
                        if dist < min_dist:
                            closest_drone = d
                            min_dist = dist

                    # Assign target
                    mapping[closest_drone] = target_loc

                    # Calculate route avoiding already searched nodes
                    route = route_interpolator_avoid_nodes(
                        [target_loc],
                        closest_drone.current_loc,
                        visited_candidates,
                        graph,
                        self.all_paths
                    )

                    closest_drone.set_route(route)

                    # Update sets
                    idle.remove(closest_drone)
                    available.remove(closest_drone)
                    active.add(closest_drone)

                    # Move Drones
                for drone in list(swarm.swarm):
                    if not drone.alive:
                        continue

                    found, is_down = drone.move_next_from_route()

                    # Case 1: Drone Taken Down
                    if is_down:
                        failed_goal = mapping.pop(drone, None)
                        active.remove(drone)

                        if failed_goal is not None:
                            # Re-insert failed goal into heap
                            # We need to look up the risk (p) again
                            cell_p = graph.nodes[failed_goal]['cell'].p
                            heapq.heappush(to_visit, (1 - cell_p, failed_goal))
                        continue

                    # Case 2: Hider Found
                    if found:
                        n_found += 1
                        all_found = n_found == n_hiders

                    # Case 3: Route Completed (Cell Searched)
                    if drone.route_length == 0:
                        finished_goal = mapping.pop(drone, None)
                        if finished_goal:
                            visited_candidates.add(finished_goal)

                        if drone in active:
                            active.remove(drone)
                            idle.add(drone)
                        if drone in swarm.temp_unavailable:
                            swarm.to_available(drone)
            else:
                for loc in list(to_visit):
                    if not available:
                        break

                    closest = None
                    dist = float('inf')

                    for d in available:
                        distance = manhattan_distance(loc,d.current_loc)
                        if distance < dist:
                            closest = d
                            dist = distance


                    goal = loc
                    mapping[closest] = goal

                    route = route_interpolator_avoid_nodes(
                        [goal],
                        closest.current_loc,
                        visited_candidates,
                        graph,
                        self.all_paths
                    )

                    closest.set_route(route)

                    idle.remove(closest)
                    active.add(closest)
                    available.remove(closest)
                    to_visit.remove(loc)


                for drone in list(swarm.swarm):
                    # Leave 'dead' drones
                    if not drone.alive:
                        continue

                    found, is_down = drone.move_next_from_route()

                    #Drone got taken down
                    if is_down:
    #                     print(f"drone in {drone.current_loc} is now down")
                        failed_goal = mapping.pop(drone, None)
    #                     print(f"adding {failed_goal} back to mapping")

                        active.remove(drone)
                        if failed_goal is not None:
                            to_visit.append(failed_goal)  # retry goal

                        continue

                    # Found a hider
                    if found:
                        n_found += 1
                        all_found = n_found == n_hiders

                    # End of route
                    if drone.route_length == 0:
    #                     print(f"{[drone]} ended route in {drone.current_loc}")
                        finished_goal = mapping.pop(drone, None)
                        visited_candidates.add(finished_goal)
                        if drone in active:
                            active.remove(drone)
                            idle.add(drone)
                        if drone in swarm.temp_unavailable:
                            swarm.to_available(drone)

            if plot_boards:
                sys.stdout.write("\033[H\033[J")
                self.board.print_board(plot_hm)
                sys.stdout.flush()
                time.sleep(plot_interval)

            if all_found:
                break

            steps += 1

        swarm.remove_swarm()
        return steps, all_found, len(swarm.takenDown),n_found/n_hiders