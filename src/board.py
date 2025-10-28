import time
from csv import excel
import numpy as np
from game_config import STATIC_P_p,STATIC_P
from .helpers import random_succes_p, get_q_A
from .sampler import Dist
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx



class Cell():
    def __init__(self,loc,q=0):
        """
        :param TUPLE loc: Initial (x,y) location of the cell
        :param FLOAT q: Initial hiding chance q of the cell, 0 by default
        """
        self.loc = loc
        self.p = 1 # success probability
        self.q = q # Hiding chance
        self.contains_hider = False
        self.found = False
        self.drone_container = set()
        self.is_hider_candidate = False

    def add_drone(self, drone):
        """
        Adds drone object to the set drone_containers
        :param drone:Drone object
        :return: None
        """
        self.drone_container.add(drone)
        return

    def after_cell_found(self):
        self.contains_hider = False
        self.found = True
        return

    def remove_drone(self,drone):
        """
        Removes drone object from the set drone_containers.
        :param drone: Drone object
        :return: None
        """
        self.drone_container.discard(drone)
        return

    def set_hider(self):
        """
        Puts contains_hider to true
        :return: None
        """
        self.contains_hider = True
        return

    def set_succes_p(self,p_i):
        """
        Sets the success probability of this cell
        :param FLOAT p_i: success probability
        :return: None
        """
        self.p = p_i

    def reset(self):
        """
        Resets all cells parameters to initial values
        :return: None
        """
        self.p = 1
        self.q = 0
        self.found = False
        self.is_hider_candidate = False
        self.contains_hider = False
        self.drone_container.clear()
        return

    def __str__(self):
        """
        Decides how to represent the cell on the printed representation of the board
        :return: Colored ■ for hider found, int amount of drones for length of the drone container, colored # if the cell contains a hider, colored C if cell is a hider candidate, . otherwise
        in that hierarchy
        """
        if self.found:
            return f"\x1b[3;33;43m□\x1b[0m"
        elif len(self.drone_container)>0 and self.contains_hider:
            return f"\x1b[3;33;43m■\x1b[0m"
        elif len(self.drone_container)>0:
            return f"{len(self.drone_container)}"
        elif self.contains_hider:
            return f"\x1b[6;30;42m#\x1b[0m"
        elif self.is_hider_candidate :
            return f"\x1b[6;30;42mC\x1b[0m"
        else:
            return '.'

class Board():
    def __init__(self,width,n_hider_candidates,n_hiders,hiding_strategy, dirichlet_alpha=2, idd=1):
        """
        :param INT width: size of the SQUARE board
        :param INT n_hider_candidates: Amount of possible hiding spots
        """
        self.rng = np.random.default_rng()

        self.da = dirichlet_alpha

        self.width = width
        self.height = width

        self.qa = None

        self.hiding_strategy = hiding_strategy
        self.n_hider_candidates = n_hider_candidates
        self.n_hiders = n_hiders
        self.hider_candidates = set({})
        self.hiders = set({})

        if n_hider_candidates>0:
            self.dist = Dist(size=n_hider_candidates,alpha=dirichlet_alpha)

        self.board = self.create_board()

        if n_hider_candidates >0:
            self.set_hider_candidates(n_hider_candidates)

        self.id = idd
        self.graph = self.to_graph()

        self.neighbor_cache = {
            node: list(self.graph[node]) for node in self.graph
        }

        self.route_cache = {
        }

    def reset(self):
        """
        Clears the board, makes sure board is ready for reinitialization
        :return: none
        """
        # self.plot_p_heatmap()
        # self.plot_q_heatmap()
        hiding_strategy = self.hiding_strategy
        self.hider_candidates.clear()
        self.hiders.clear()

        for cell in self.board.flat:
            cell.reset()

        if self.n_hider_candidates>0:
            self.dist = Dist(size=self.n_hider_candidates,alpha=self.da)
            self.set_hider_candidates(self.n_hider_candidates)


        self.hide(tactic=hiding_strategy)


    def create_board(self):
        """
        Generates the grid as a numpy array filled with Cell objects
        :return: Board as 2d numpy array with cell objects
        # """
        board = np.array([[Cell(loc=(x, y), q=0) for x in range(self.width)] for y in range(self.height)],dtype=object)
        return board

    def to_graph(self):
        """
        Turns board into NetworkX graph
        :return: NetworkX graph conversion of the board
        """
        G = nx.grid_2d_graph(self.height, self.width)
        for y in range(self.height):
            for x in range(self.width):
                node = (x, y)
                G.nodes[node]['cell'] = self.board[y, x]
        return G

    def add_drone_to_board(self,drone,s):
        """
        Adds the drone object to location s on the board
        :param drone: Drone object
        :param s: Location of the drone object
        :return: None
        """
        x,y = s
        # print(f"Placing drone on (x:{x},y:{y})")
        target_cell =  self.board[y,x]
        target_cell.add_drone(drone)
        return

    def set_hider_candidates(self,n):
        """
        Opens n locations as possible hiding locations
        :param n: the amount of hiding locations
        :return: none
        """
        flat_cells = self.board.flatten()
        for i in range(n):
            available_cells = [cell for cell in flat_cells if cell not in self.hider_candidates]
            if available_cells:
                cell = self.rng.choice(available_cells)
                self.hider_candidates.add(cell)
                cell.is_hider_candidate = True

                if self.hiding_strategy == "random":
                    cell.q = self.dist.sample()

                if STATIC_P:
                    cell.set_succes_p(STATIC_P_p)
                else:
                    cell.set_succes_p(random_succes_p())
        return

    def hide(self,tactic="random"):
        """
        Puts n hiders in opened hiding locations / hider candidates
        :param tactic: Tactic that hider follows when placing hiders in candidate hider cells
        :return: Returns none
        """

        if self.n_hider_candidates <=0:
            return
        chosen_cell = None

        if tactic == "weighted" or tactic == 'greedy':
            q_a = get_q_A(self.hider_candidates,self.n_hiders)
            q_list, subset_list = list(q_a.values()), list(q_a.keys())

            self.qa = (subset_list, q_list)

            if tactic == 'weighted':
                chosen_subset = self.rng.choice(subset_list, p=q_list)

            elif tactic == 'greedy':
                chosen_subset = subset_list[np.argmax(q_list)]

            for subset in subset_list:
                for cell in subset:
                    cell.q = q_a[subset]

            for cell in chosen_subset:
                cell.set_hider()
                self.hider = cell.loc
                self.hiders.add(cell.loc)


            #     print("\n","printing the chosen cell")
            #     print(cell.loc, cell.p, cell.q,"\n")


            # print("cell p and cell q for cell in all subsets: \n")
            # for subset in subset_list:
            #     for cell in subset:
            #         print("loc",cell.loc)
            #         print("p",cell.p)
            #         print("q",cell.q,'\n')
            # time.sleep(10)

        else:
            flat = self.board.flatten()
            if tactic == "random":
                qs = np.array([cell.q for cell in flat])
                # chosen_cell = np.random.choice(flat,p=qs)
                n = 0
                while(n < self.n_hiders):
                    cell = self.rng.choice(flat,p=qs)
                    if cell.loc in self.hiders:
                        continue
                    else:
                        cell.set_hider()
                        self.hider = cell.loc
                        self.hiders.add(cell.loc)
                        n+=1

            elif isinstance(tactic,list):
                for i in tactic:
                    chosen_cell = flat[i]
                    cell = chosen_cell
                    cell.set_hider()
                    self.hiders.add(chosen_cell)


            elif isinstance(tactic,int):
                chosen_cell = flat[tactic]
                chosen_cell.set_hider()
                self.hiders.add(chosen_cell)

        return

    def get_neighbors(self,current_loc):
        return self.neighbor_cache[current_loc]

    def plot_q_heatmap(self):
        qs = np.array([[cell.q for cell in row] for row in self.board])
        sns.heatmap(qs, annot=True, cmap="crest", fmt=".2f", cbar=True)
        plt.title("Heatmap of q_i values")
        plt.xlabel("X coordinate")
        plt.ylabel("Y coordinate")
        plt.show()
        plt.close()

    def plot_p_heatmap(self):
        ps = np.array([[cell.p for cell in row] for row in self.board])
        sns.heatmap(ps, annot=True, cmap="crest", fmt=".2f", cbar=True)
        plt.title("Visualising high p area")
        plt.xlabel("X coordinate")
        plt.ylabel("Y coordinate")
        plt.show()

    def print_board(self):
        horizontal_line = "== " * (self.width + 1)
        print(f" {horizontal_line}")
        for row in self.board:
            row_str = "  ".join(str(cell) for cell in row)
            print(f'‖  {row_str}  ‖')
        print(f" {horizontal_line}")

    def plot_graph(self):

        pos = {(y, x): (x, -y) for y, x in self.graph.nodes()}
        node_colors = {}
        node_labels = {}
        for node in self.graph.nodes():
            cell = self.graph.nodes[node]['cell']
            if cell.p > 0:
                node_colors[node] = 'red'  # Risk nodes are red
                node_labels[node] = f"R\np={cell.p:.1f}"
            elif len(cell.drone_container) > 0:
                node_colors[node] = 'skyblue'  # Drones/hiders are blue
                node_labels[node] = str(len(cell.drone_container))
            else:
                node_colors[node] = 'lightgray'  # Empty cells are gray
                node_labels[node] = f"q={cell.q:.2f}"

        plt.figure(figsize=(12, 12))
        plt.title("Board as a Graph")


        nx.draw(self.graph,
                pos=pos,
                with_labels=False,
                node_size=1500,
                node_color=list(node_colors.values()),
                edge_color='gray')

        nx.draw_networkx_labels(self.graph,
                                pos,
                                labels=node_labels,
                                font_size=8,
                                font_color='black')

        plt.show()
        plt.close()

    def plot_drone_trajectory_animated(self, swarm,id=1):
        fig, ax = plt.subplots()
        ax.set_title('Drone Path')
        ax.set_xlim(0, self.width+0)
        ax.set_ylim(0, self.height+0)
        ax.set_xlabel('X-axis')
        ax.set_ylabel('Y-axis')
        ax.grid(True)
        h_x, h_y = self.hider
        ax.plot(h_x, h_y, marker='*', markersize=15, color='gold', linestyle='none', label='Target')

        colorList = ['red', 'green', 'blue', 'lime']

        lines = []
        markers = []
        for i, drone in enumerate(swarm.swarm):
            color = colorList[i % len(colorList)]
            line, = ax.plot([], [], lw=2, color=color, label=f'Drone {i + 1}')
            lines.append(line)
            marker, = ax.plot([], [], marker='o', markersize=8, color=color)
            markers.append(marker)

        ax.legend()

        max_frames = 0
        if swarm.swarm:
            max_frames = max(len(drone.route_history) for drone in swarm.swarm if drone.route_history)

        def update(frame):
            for i, drone in enumerate(swarm.swarm):
                if frame < len(drone.route_history):
                    route_up_to_frame = drone.route_history[:frame + 1]

                    x_data, y_data = zip(*route_up_to_frame)

                    lines[i].set_data(x_data, y_data)

                    markers[i].set_data([x_data[-1]], [y_data[-1]])

            return lines + markers

        # Create the animation.
        ani = animation.FuncAnimation(fig=fig, func=update, frames=max_frames,
                                      interval=100, blit=True, repeat=False)
        plt.gca().invert_yaxis()
        plt.show()
        ani.save(f"./plots/drone_trajectory_{id}.gif", writer="pillow")
        plt.close()

