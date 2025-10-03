import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from itertools import count
import matplotlib
path = Path.cwd() / "sim_logs" / "together_traverse_best_permutation.csv"

x_vals = []
y_vals = []

index = count()
print(pd.read_csv(path))

def animate(i):
    data = pd.read_csv(path, header=1)

    x = data['i']
    y1 = data['frac_area_covered']


    running_mean = y1.expanding().mean()

    plt.cla()

    plt.plot(x, y1, label='Fraction of Area Covered')

    plt.plot(x, running_mean, label='Running Mean of Area Covered', linestyle='--')

    plt.legend(loc='upper left')

    plt.tight_layout()




ani = FuncAnimation(plt.gcf(), animate, interval=1000)

plt.tight_layout()
plt.show()