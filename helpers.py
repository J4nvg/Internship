from itertools import permutations
import numpy as np
from game_config import RISK_CHANCES


def manhattan_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return abs(x1 - x2) + abs(y1 - y2)


def total_manhattan_distance_list(list_of_points):
    tot = 0
    for i in range(len(list_of_points)-1):
        tot += manhattan_distance(list_of_points[i], list_of_points[i+1])
    return tot


def get_optimal_permutation_MD(start_point, target_points):
    shortest_distance = float("inf")
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


def confidence_interval(mean, var, Nruns):
    zalpha2 = 1.96
    half_width = zalpha2 * np.sqrt(var)/np.sqrt(Nruns)
    ci = (mean - half_width, mean + half_width)
    return ci

def mean_var(array):
    return np.mean(array), np.var(array)

def min_max(array):
    return np.min(array), np.max(array)

def get_all_stats(array,Nruns):
    mi,ma = min_max(array)
    mu,var = mean_var(array)
    ci = confidence_interval(mu, var, Nruns)
    return {
            "min": mi,
            "max": ma,
            "mean": mu,
            "var": var,
            "ci_lower": ci[0],
            "ci_upper": ci[1],
            "Half_width": ci[1]-mu,
        }


def get_whole_and_remainder(size,divided_by):
    whole = size // divided_by
    remainder = size % divided_by
    return whole,remainder


def random_risk():
    return np.random.choice(RISK_CHANCES)