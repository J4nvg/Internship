from csv import excel
import numpy as np

from drone import Drone
from game_config import RANDOM_RISK_ALLOCATION,FULL_BOARD_HIDING, RISKY_AREA_P
from sampler import Dist
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx

class Cell():
    def __init__(self,loc,q):
        self.loc = loc
        self.p = 0 # Take down chance
        self.q = q # Hiding chance
        self.contains_hider = False
        self.drone_container = set()

    def add_drone(self, drone):
        self.drone_container.add(drone)
        return

    def remove_drone(self,drone):
        self.drone_container.discard(drone)
        return

    def set_hider(self):
        self.contains_hider = True
        return

    def set_hiding_chance(self,q):
        self.q = q
        return


    def set_risk(self,p_i):
        self.p = p_i
        return

    def __str__(self):
        n_drones = len(self.drone_container)
        if n_drones>0 and self.contains_hider:
            return f"\x1b[3;33;43m■\x1b[0m"
        elif n_drones>0:
            return f"{n_drones}"
        elif self.contains_hider:
            return f"\x1b[6;30;42m#\x1b[0m"
        elif self.p >0 :
            return f"\x1b[6;30;42mR\x1b[0m"
        else:
            return ' '

class Board():
    def __init__(self,width=10,height=10,n_hiders=3,n_risks = 10,takedown_chance = .5 , dirichlet_alpha=2, id=1):

        self.width = width
        self.height = height

        if FULL_BOARD_HIDING:
            self.dist = Dist(size=width*height,alpha=dirichlet_alpha)
        else:
            self.dist = Dist(size=n_hiders,alpha=dirichlet_alpha)




        self.board = self.create_board()

        self.hider_candidates = set()
        self.hider = ()
        if not FULL_BOARD_HIDING:
            self.set_hider_candidates(n_hiders)

        self.id = id

        if RANDOM_RISK_ALLOCATION:
            self.risks = set()
            self.set_spread_over_board_risks(n=n_risks,p=takedown_chance)

        self.graph = self.to_graph()


    def create_board(self):
        """
        Generates the grid as a numpy array filled with Cell objects,
        q_i will be sampled from dirichlet distribution
        :return:
        """
        if FULL_BOARD_HIDING:
            board = np.array([[Cell(loc=(x, y), q=self.dist.sample()) for x in range(self.width)] for y in range(self.height)],dtype=object)
        else:
            board = np.array([[Cell(loc=(x, y), q=0) for x in range(self.width)] for y in range(self.height)],dtype=object)
        return board

    def to_graph(self):

        G = nx.grid_2d_graph(self.height, self.width)
        for y in range(self.height):
            for x in range(self.width):
                node = (x, y)
                G.nodes[node]['cell'] = self.board[y, x]
        return G

    def add_drone_to_board(self,drone,s):
        x,y = s
        print(f"Placing drone on (x:{x},y:{y})")
        self.board[y,x].add_drone(drone)
        return

    def set_spread_over_board_risks(self,n,p):
        flat_cells = self.board.flatten()
        for i in range(n):
            available_cells = [cell for cell in flat_cells if cell not in self.risks]
            if available_cells:
                cell = np.random.choice(available_cells)
                self.risks.add(cell)
                cell.set_risk(p)
            else:
                print("No more available locations to add a risk.")
                return False
        return

    def set_hider_candidates(self,n):
        flat_cells = self.board.flatten()
        for i in range(n):
            available_cells = [cell for cell in flat_cells if cell not in self.hider_candidates]
            if available_cells:
                cell = np.random.choice(available_cells)
                self.hider_candidates.add(cell)
                cell.set_hiding_chance(self.dist.sample())
                cell.set_risk(RISKY_AREA_P)
        return

    def hide(self,hider,tactic="greedy"):

        flat = self.board.flatten()
        qs = np.array([cell.q for cell in flat])
        chosen_cell = None
        if tactic == "greedy":
            #     Return cell with highest probability
            index = np.argmax(qs)
            chosen_cell = flat[index]
            chosen_cell.set_hider()
            print(f"{hider} in cell {chosen_cell.loc} with {chosen_cell.q}")

        elif tactic == "weighted":
            chosen_cell = np.random.choice(flat,p=qs)
            chosen_cell.set_hider()
            print(f"{hider} in cell {chosen_cell.loc} with {chosen_cell.q} even though max q was {np.max(qs)}")
        self.hider = chosen_cell.loc


    def plot_q_heatmap(self):
        qs = np.array([[cell.q for cell in row] for row in self.board])
        sns.heatmap(qs, annot=True, cmap="crest", fmt=".2f", cbar=True)
        plt.title("Heatmap of q_i values")
        plt.xlabel("X coordinate")
        plt.ylabel("Y coordinate")
        plt.show()

    def plot_risk_heatmap(self):
        ps = np.array([[cell.p for cell in row] for row in self.board])
        sns.heatmap(ps, annot=True, cmap="crest", fmt=".2f", cbar=True)
        plt.title("Visualising high risk area")
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

        # Create line and marker objects for each drone, initially with no data.
        lines = []
        markers = []
        for i, drone in enumerate(swarm.swarm):
            color = colorList[i % len(colorList)]
            # The line object will draw the path
            line, = ax.plot([], [], lw=2, color=color, label=f'Drone {i + 1}')
            lines.append(line)
            # The marker object will be a dot at the drone's current position
            marker, = ax.plot([], [], marker='o', markersize=8, color=color)
            markers.append(marker)

        ax.legend()

        # Find the length of the longest route to determine the number of frames.
        max_frames = 0
        if swarm.swarm:
            max_frames = max(len(drone.route_history) for drone in swarm.swarm if drone.route_history)

        def update(frame):
            # For each frame, update the data for each drone's line and marker.
            for i, drone in enumerate(swarm.swarm):
                if frame < len(drone.route_history):
                    # Get the path up to the current frame.
                    route_up_to_frame = drone.route_history[:frame + 1]

                    # Unzip coordinates for plotting
                    x_data, y_data = zip(*route_up_to_frame)

                    # Update the line plot data (the path)
                    lines[i].set_data(x_data, y_data)

                    # Update the marker's position (the "head" of the drone)
                    # We take the last point from the path up to the current frame.
                    markers[i].set_data([x_data[-1]], [y_data[-1]])

            # Return all the artists that were modified
            return lines + markers

        # Create the animation.
        ani = animation.FuncAnimation(fig=fig, func=update, frames=max_frames,
                                      interval=100, blit=True, repeat=False)
        plt.gca().invert_yaxis()
        plt.show()
        ani.save(f"./plots/drone_trajectory_{id}.gif", writer="pillow")

