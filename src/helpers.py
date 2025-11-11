from itertools import permutations, combinations
import numpy as np
from scipy.stats import binomtest
import networkx as nx
import numpy.typing as npt
from typing import Union

type point = tuple[int, int]

Numeric = Union[np.floating, float, int]

def manhattan_distance(p1: point, p2: point) -> int:
    """
    :param p1: point one (tuple[int, int])
    :param p2: point two (tuple[int, int])
    :return: int, distance between p1 and p2
    """
    x1, y1 = p1
    x2, y2 = p2
    return abs(x1 - x2) + abs(y1 - y2)


def total_manhattan_distance_list(list_of_points: list[point]) -> int:
    """
    :param list_of_points: list of points, list[tuple[int, int]]
    :return: int, total manhattan distance of all points in the list
    """
    tot: int = 0
    for i in range(len(list_of_points) - 1):
        tot += manhattan_distance(list_of_points[i], list_of_points[i + 1])
    return tot


def get_optimal_permutation_md(start_point: point, target_points: list[point]) -> tuple[list[point] | None, Numeric]:
    """
    :param start_point: start point (tuple[int, int])
    :param target_points: end point (tuple[int, int])
    :return: tuple[list[point] | None, float | int], minimal manhattan distance permutation of points to traverse and shortest distance int
    """
    shortest_distance: float = float("inf")
    optimal_permutation = None

    for perm_of_targets in permutations(target_points):
        current_path = [start_point] + list(perm_of_targets)
        tot_dist = total_manhattan_distance_list(current_path)
        # print(f"dist:{tot_dist}, for {current_path}")
        if tot_dist < shortest_distance:
            shortest_distance = tot_dist
            optimal_permutation = current_path
            # print(f"optimal_permutation:{optimal_permutation}")
    return optimal_permutation, shortest_distance


def confidence_interval(mean: Numeric, var: Numeric, n_runs: int) -> tuple[np.floating, np.floating]:
    """
    Symmetric confidence interval
    :param mean: float, distribution mean
    :param var: float, distribution variance
    :param n_runs: int, number of runs
    :return: tuple[np.floating, np.floating], confidence interval
    """
    zalpha2 = 1.96
    half_width = zalpha2 * np.sqrt(var) / np.sqrt(n_runs)
    ci = (mean - half_width, mean + half_width)
    return ci


def mean_var(array: npt.NDArray[np.floating]) -> tuple[np.floating, np.floating]:
    """
    :param array: numpy array
    :return: tuple[np.floating, np.floating], mean and variance
    """
    return np.mean(array), np.var(array)


def min_max(array: npt.NDArray[np.floating]) -> tuple[np.floating, np.floating]:
    """
    :param array: numpy array
    :return: tuple[np.floating, np.floating], min and max
    """
    return np.min(array), np.max(array)


def get_all_stats(array: npt.NDArray[np.floating], n_runs: int) -> dict[str, np.floating]:
    """
    :param array: numpy array
    :param n_runs: int, number of runs
    :return:  dict[str, np.floating], metric and value: min, max ,mean ,variance ,ci_lower ,ci_upper ,half_width
    """
    mi, ma = min_max(array)
    mu, var = mean_var(array)
    ci = confidence_interval(mu, var, n_runs)
    return {
        "min": mi,
        "max": ma,
        "mean": mu,
        "var": var,
        "ci_lower": ci[0],
        "ci_upper": ci[1],
        "Half_width": ci[1] - mu,
    }


def get_all_stats_binom(array: npt.NDArray[Numeric], n_runs: int) -> dict[str, np.floating | str]:
    """
    :param array: numpy array
    :param n_runs: int, number of runs
    :return:  dict[str, np.floating], metric and value: min, max ,mean ,variance ,ci_lower ,ci_upper ,half_width
    """
    k = int(array.sum())
    n = n_runs
    result = binomtest(k=k, n=n)
    p_all_hiders_found = result.statistic

    ci = result.proportion_ci()
    return {
        "min": 'NA',
        "max": 'NA',
        "mean": p_all_hiders_found,
        "var": 'NA',
        "ci_lower": ci.low,
        "ci_upper": ci.high,
        "Half_width": 'NA',
    }


def get_whole_and_remainder(a: int, b: int) -> tuple[int,int]:
    """
    :param a: int, a numerator
    :param b: int, b denominator
    :return: tuple[int, int], whole and remainder
    """
    whole = a // b
    remainder = a % b
    return whole, remainder


def random_success_p(p_dist_list:list[Numeric]) -> Numeric:
    return np.random.choice(p_dist_list)


def get_q_A(possible_hiding_spots, k):
    if k > len(possible_hiding_spots):
        raise Exception("Invalid k")
    mapped = {cell: (1 - cell.p) / cell.p for cell in possible_hiding_spots}
    B = set(combinations(possible_hiding_spots, k))

    subset_products = []
    for subset in B:
        prod = 1
        for item in subset:
            prod *= mapped[item]  # Mapped item = (1 - p) / p
        subset_products.append(prod)

    lambda_k = 1 / sum(subset_products)
    final_q_a = {}

    for prod, subset in zip(subset_products, B):
        final_q_a[subset] = lambda_k * prod

    return final_q_a


def route_interpolator(visit_order: list[point], start: point, graph: nx.Graph, all_paths) -> list[point]:
    """
    :param visit_order: list of points, list[tuple[int, int]]
    :param start: point (tuple[int, int]), start point
    :param graph: networkx graph (nx.Graph)
    :param all_paths: dictionary of cached paths
    :return: list[point], route path, interpolation of the visit_order
    """
    route = [start]
    current_loc = route[0]
    for next_waypoint in visit_order:
        if current_loc == next_waypoint:
            continue
        if all_paths:
            new_route = all_paths[current_loc][next_waypoint]
        else:
            new_route = (
                nx.shortest_path(graph, source=current_loc, target=next_waypoint))

        route.extend(new_route[1:])
        current_loc = next_waypoint

    return route


def route_interpolator_avoid_nodes(visit_order: list[point], start: point,to_avoid:set[point], graph: nx.Graph, all_paths) -> list[point]:
    route = [start]
    current_loc = start

    for next_waypoint in visit_order:
        if current_loc == next_waypoint:
            continue

        penalty = graph.number_of_nodes() + 1
        def custom_weight_function(u,v,data):
            if v == next_waypoint:
                return 1

            if v in to_avoid:
                return penalty

            return 1
        new_route = nx.shortest_path(
            graph,
            source=current_loc,
            target=next_waypoint,
            weight=custom_weight_function,
        )

        route.extend(new_route[1:])
        current_loc = next_waypoint

    return route


def discounted_distance(p1: point, p2: point, p2p: int, rev: bool) -> Numeric:
    """
    :param p1: point one, tuple[int, int]
    :param p2: point two, tuple[int, int]
    :param p2p: int, probability of success point two
    :param rev: bool, whether to discount by p2p (True) or by 1 - p2p (False)
    :return: Numeric, distance p1 to p2 discounted by p2p (or 1 - p2p)
    """
    d = manhattan_distance(p1, p2)
    if rev:
        r = d * p2p
    else:
        r = d * (1 - p2p)
    return r


def total_discounted_distance(list_of_cells, rev):
    tot = 0
    for i in range(len(list_of_cells) - 1):
        tot += discounted_distance(list_of_cells[i].loc, list_of_cells[i + 1].loc, list_of_cells[i + 1].p, rev)
    return tot


def best_route_discount_distance(hider_candidates, start_location, rev=False):
    permutation_list = permutations(hider_candidates)
    shortest_distance = float("inf")
    optimal_permutation = None
    for perm_of_targets in permutation_list:
        current_path = [start_location] + list(perm_of_targets)
        tot_dist = total_discounted_distance(current_path, rev)
        # print(f"dist:{tot_dist}, for {current_path}")
        if tot_dist < shortest_distance:
            shortest_distance = tot_dist
            optimal_permutation = current_path
    optimal_permutation = [cell.loc for cell in optimal_permutation]
    # print(f"optimal_permutation:{optimal_permutation}")
    return optimal_permutation

#Testing code
# class P_item():
#     def __init__(self,p,name):
#         self.p = p
#         self.name = name
#     def __repr__(self):
#         return self.name
# #
# B = P_item(0.8,'B')
# D = P_item(0.7,'D')
# F = P_item(0.9,'F')
#
#
# H = P_item(0.6,'H')
# J = P_item(0.5,'J')
#
#

# print(get_q_A([B,D,F],3))
