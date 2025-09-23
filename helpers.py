from itertools import permutations
import numpy as np
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


# A = (0,0)
# B = (2,3)
# C = (1,1)
# D = (4,1)
# #
# print(list(permutations([A,B,C,D])))
# print(get_optimal_permutations_MD(list(permutations([A,B,C,D]))))
#
# print(manhattan_distance((0,0),(1,1)))
# print(manhattan_distance((1,1),(2,4)))
#
# print(total_manhattan_distance_list([(0,0),(1,1),(2,4)]))
