import numpy as np
from collections import deque
import random
from .helpers import manhattan_distance


class Swarm():
    def __init__(self,board,size,symbol='d', init_strat="top-left"):
        self.size = size
        self.board = board
        self.swarm = []

        self.done = set({})
        self.available = set({})
        self.temp_unavailable = set({})
        self.takenDown = []


        self.symbol = symbol

        self.init_strat = init_strat
        self.init_swarm(strat=init_strat)
        self.same_start = True

    def init_swarm(self, strat):
        self.swarm = [Drone(self.board,goal=(),symbol=self.symbol,parent_swarm=self,num=i) for i in range(self.size)]

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

    def reset(self):
        self.done.clear()
        self.takenDown.clear()
        self.temp_unavailable.clear()

        for drone in self.swarm:
            if self.board.graph.has_node(drone.current_loc):
                self.board.graph.nodes[drone.current_loc]['cell'].remove_drone(drone)
            drone.reset()
            self.board.add_drone_to_board(drone, drone.start)

        self.available = set([drone for drone in self.swarm])


    def to_unavailable(self,drone):
        self.available.remove(drone)
        self.temp_unavailable.add(drone)
        return

    def to_available(self,drone):
        self.temp_unavailable.remove(drone)
        self.available.add(drone)
        return

    def drone_takedown(self,drone):
        self.takenDown.append(drone)
        return

    def remove_swarm(self):
        graph = self.board.graph
        for drone in self.swarm:
            current_node = drone.current_loc
            current_cell = graph.nodes[current_node]['cell']
            current_cell.remove_drone(drone)
        # print("All drones were removed.")


class Drone():
    def __init__(self,board,goal,symbol,parent_swarm, num=0):

        self.parent_swarm = parent_swarm

        self.goal = goal
        self.symbol = symbol
        self.board = board

        self.rng = np.random.default_rng()

        self.start = ()
        self.current_loc = ()
        self.done = False

        self.route = deque([])
        self.route_history = []

        self.available = True
        self.alive = True
        self.route_length = -1
        self.number = num


    def reset(self):
        self.current_loc = self.start
        self.route = deque([])

        self.route_history = []
        self.alive = True
        self.route_length = -1

        self.available = True

    def set_done(self):
        self.parent_swarm.done.add(self)
        return

    def remove_done(self):
        self.parent_swarm.done.remove(self)
        return

    def move_next(self,to_x_y):
        """
        :param to_x_y:
        :return: Tuple[Bool,Bool], If the hider was found and If the drone is down
        """
        if not self.alive:
            is_down = True
            found = False
            return found,is_down

        is_down = False
        graph = self.board.graph
        nodes = graph.nodes

        next_node = to_x_y
        next_cell = nodes[next_node]['cell']


        target_found = next_cell.contains_hider

        current_node = self.current_loc

        if manhattan_distance(to_x_y,current_node) >1:
            raise Exception("Drone cannot skip cells........ Fatal error")

        current_cell = nodes[current_node]['cell']

        current_cell.remove_drone(self)

        if self.rng.random() < (1 - next_cell.p):
            self.alive = False
            self.parent_swarm.drone_takedown(self)
            # print(f"{self} was taken down when going to {to_x_y}")
            is_down = True
            found = False
            return found,is_down


        next_cell.add_drone(self)
        self.current_loc = next_node
        self.route_history.append(next_node)

        if target_found:
            next_cell.after_cell_found()

        return target_found,is_down

    def move_next_from_route(self):
        """
        :return: Tuple[bool,bool], If the hider was found and If the drone is down
        """
        if not self.alive:
            return False,True

        if self.route_length <1:
            self.set_done()
            return False, False

        last_step = (self.route_length == 1)
        to_x_y = self.route.popleft()
        self.route_length -= 1
        found = self.move_next(to_x_y)

        if last_step:
            self.parent_swarm.to_available(self)
            self.available = True
        return found

    def set_init_location(self,loc):
        self.current_loc = loc
        self.route_history.append(loc)
        self.start = loc
        self.board.add_drone_to_board(self, s=loc)
        return

    def set_route(self,path,route_length=-1):
        if route_length == -1:
            route_length = len(path)
        self.route = deque(path)
        self.route_length = route_length

        self.parent_swarm.to_unavailable(self)
        self.available = False

        return

    def random_move(self,board):
        neighbors = board.get_neighbors(self.current_loc)
        next_node = random.choice(neighbors)
        return self.move_next(next_node)



    def __str__(self):
        return f'\x1b[1;32;40m{self.symbol}\x1b[0m'

    def __repr__(self):
        return f'{self.symbol}{self.number} {self.current_loc}'

    # def greedy_move(self,graph,target_node):

