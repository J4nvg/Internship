from scipy.stats import dirichlet
import numpy as np
class Dist():
    def __init__(self, size, alpha):
        self.alpha = np.full(size, alpha)  # symmetric Dirichlet
        self.values = dirichlet.rvs(self.alpha, size=1)[0]
        self.size = size
        self.i = size-1
        self.c = 0
    def sample(self):
        if self.i >= 0:
            val = self.values[self.i]
            self.i -= 1
            # print(f"{self.c}. sampled {val}, index = {self.i}, size={self.size}")
            self.c+=1
            return val
        else:
            raise Exception(f"Something went wrong when sampling numbers {self.i} {self.size}")