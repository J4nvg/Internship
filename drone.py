import numpy as np
import networkx as nx
from collections import deque
import sys, time

from helpers import manhattan_distance


class Swarm():
    def __init__(self,board,size,symbol='d', init_strat="top-left"):
        self.size = size
        self.board = board
        self.swarm = []
        self.available = []
        self.takenDown = []
        self.temp_unavailable = []
        self.symbol = symbol
        self.cell_probabilities = self.cells_by_probability()
        self.goal = self.cell_probabilities[0]
        self.init_strat = init_strat
        self.init_swarm(strat=init_strat)
        self.same_start = True

    def init_swarm(self, strat):
        self.swarm = [Drone(self.board,goal=self.goal,symbol=self.symbol,parent_swarm=self,num=i) for i in range(self.size)]

        if strat=="corner":
            corners = [(0,0),(self.board.width-1,0),(self.board.width-1,self.board.height-1),(0,self.board.height-1)]
            i = 0
            for drone in self.swarm:
                s = corners[i]
                drone.set_init_location(s)
                i+=1
                if i == 4:
                    i = 0
            self.same_start = False


        elif strat=="top-left":
            s = (0,0)
            for drone in self.swarm:
                drone.set_init_location(s)
            self.same_start = True
        else:
            raise Exception("not implemented yet;")
        self.available = [drone for drone in self.swarm]
        return


    def to_unavailable(self,drone):
        self.available.remove(drone)
        self.temp_unavailable.append(drone)
        return

    def to_available(self,drone):
        self.temp_unavailable.remove(drone)
        self.available.append(drone)
        return

    def cells_by_probability(self):
        graph = self.board.graph
        sort = sorted(graph.nodes, key = lambda node: graph.nodes[node]['cell'].q, reverse=True)
        return deque(sort)

    def drone_takedown(self,drone):
        self.takenDown.append(drone)
        return

    def remove_swarm(self):
        graph = self.board.graph
        for drone in self.swarm:
            current_node = drone.current_loc
            current_cell = graph.nodes[current_node]['cell']
            current_cell.remove_drone(self)
        print("All drones were removed.")


class Drone():
    def __init__(self,board,goal,symbol,parent_swarm, num=0):
        # self.max_x = board.width
        # self.max_y = board.height
        self.parent_swarm = parent_swarm

        self.goal = goal
        self.symbol = symbol
        self.board = board

        self.start = ()
        self.current_loc = ()

        self.route = deque([])
        self.route_history = []

        self.alive = True
        self.route_length = -1
        self.number = num



    def move_next(self,to_x_y):
        if not self.alive:
            return False

        graph = self.board.graph
        next_node = to_x_y
        next_cell = graph.nodes[next_node]['cell']
        target_found = next_cell.contains_hider

        current_node = self.current_loc

        if manhattan_distance(to_x_y,current_node) >1:
            raise Exception("Drone cannot skip cells........ Fatal error")

        current_cell = graph.nodes[current_node]['cell']

        current_cell.remove_drone(self)

        taken_down = np.random.choice([True, False], p=[next_cell.p,1-next_cell.p])
        if taken_down:
            self.alive = False
            self.parent_swarm.drone_takedown(self)
            self.parent_swarm.cell_probabilities.appendleft(self.goal)
            print(f"DRONE was taken down while entering {next_node} , on its way to {self.goal}")
            return False


        next_cell.add_drone(self)
        self.current_loc = next_node
        self.route_history.append(next_node)

        return target_found

    def move_next_from_route(self):
        if self.alive:
            if self.route_length == 1:
                to_x_y = self.route.popleft()
                self.route_length -= 1
                found= self.move_next(to_x_y)
                self.parent_swarm.to_available(self)
                # print(f"Drone {self.number} has become available again")
                return found
            else:
                to_x_y = self.route.popleft()
                self.route_length -= 1
                found= self.move_next(to_x_y)
                return found
        return False

    def set_init_location(self,loc):
        self.current_loc = loc
        self.route_history.append(loc)
        self.start = loc
        self.board.add_drone_to_board(self, s=loc)
        return

    def get_route_to_goal(self,goal):
        graph = self.board.graph
        source_node = self.current_loc
        self.goal = goal
        target_node = goal
        # print(f"Drone at {self.current_loc} finding path from graph node {source_node} to {target_node}")
        path = nx.shortest_path(graph, source=source_node, target=target_node)
        # print("Found path:", path)
        return deque(path)

    def set_route(self,path,route_length=-1):
        if route_length == -1:
            route_length = len(path)
        if(isinstance(path,list)):
            self.route = deque(path)
        elif(isinstance(path,deque)):
            self.route = path
        else:
            raise Exception("Path must be either a list or a deque")
        self.route_length = route_length
        return

    def random_move(self):
        graph = self.board.graph
        current_node = self.current_loc

        possible_moves = list(graph.neighbors(current_node))

        random_index = np.random.randint(0, len(possible_moves))
        random_move = possible_moves[random_index]

        return self.move_next(random_move)




    def __str__(self):
        return f'\x1b[1;32;40m{self.symbol}\x1b[0m'

    def __repr__(self):
        return f'{self.symbol} {self.loc}'

    # def greedy_move(self,graph,target_node):

