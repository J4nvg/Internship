# Simple drone swarm simulator in adversarial hide & seek environment
<p align="center">
<img src="img/PHS.png" width="400" >
</p>

---

## 📚 Table of Contents
- [Todo](#todo)
- [Game Info](#game-info)
  - [Hider](#hider)
  - [Risks](#risks)
  - [Swarm & Drones](#swarm--drones)
- [Usage](#use)
- [List of Available Tactics](#list-of-available-tactics)
- [Recommended Use](#recommended-use)
- [Searching Policies](#searching-policies)
  - [Divide over risk](#divide-over-risk)
  - [Lidbetter](#lidbetter)
  - [Together traverse best permutation](#together-traverse-best-permutation)
  - [Traverse ordered q_A](#traverse-ordered-q_a)
  - [Traverse P q_A](#traverse-p-q_a)
  - [Discounted Distance](#discounted-distance)
  - [Discounted Distance Reverse](#discounted-distance-reverse)
  - [Horizontal scan traversal](#horizontal-scan-traversal)
  - [Partitioned horizontal scan traversal](#partitioned-horizontal-scan-traversal)
  - [Spiral scan traversal](#spiral-scan-traversal)
  - [Random Walk](#random-walk)
  - [Shared list](#shared-list)
- [About Dirichlet Dist](#about-the-dirichlet-distribution-alpha-value)
---

# Todo
 - [ ] Refactor code with typing

---

## Game info

### Hider

The game features **n** static hiders, which can be placed in one of
$M_{hider\_candidates} == |S|$ locations, denoted as the set **S**.
Both the number of hiders and the number of candidate locations are configurable in the `game_config` file.

> **Note:** Setting more than 10 hider candidates significantly impacts simulation speed for the **TTBP** tactic, due to the combinatorial explosion in possible hiding permutations.

At initialization, candidate cells are randomly selected from the grid and assigned hiding probabilities **q<sub>i</sub>**, based on the chosen hiding strategy.

---

#### Hiding Strategies

**Greedy**
: The hider(s) select the subset of candidate cells with the highest **q<sub>A</sub>** values.
The probabilities **q<sub>A</sub>** are derived following Lidbetter (2020) [^1], which provides the optimal hiding strategy for this class of Search and Rescue games.

**Weighted**
: The hider(s) select a subset of candidate cells according to the probability distribution over **S**, defined by **q<sub>A</sub>**.
As in the Greedy strategy, **q<sub>A</sub>** is based on Lidbetter (2020) [^1].

**Random**
: The hider(s) select one or more candidate cells **i ∈ S**, where probabilities **q<sub>i</sub>** are drawn from a Dirichlet distribution, ensuring

$$
\sum_{i=1}^{m_{\text{hider candidate}}} q_i = 1.
$$

**Integer or List of Integers**
: The hider(s) select one or more integer indices of the flattened board array directly.
This option is primarily intended for debugging purposes.

---

#### Theorem 3 of Lidbetter (2020)

In the Search and Rescue game, it is optimal for the Hider to choose each subset
( A \in S^{(k)} ) with probability

$$
q_A = \lambda_k \prod_{i \in A} \frac{1 - p_i}{p_i},
$$

where

$$
\lambda_k = \left( \sum_{B \in S^{(k)}} \prod_{i \in B} \frac{1 - p_i}{p_i} \right)^{-1}.
$$

---

### Risks

Each hider_candidate cell $i, i \in S$, has a probability $p_i$., which is the probability that the Searcher is not taken down / captured when searching location $i$, we refer to this as the _success probability_ of location $i$</br>
This means that if the drone enters the cell, and is taken down or captured, it will not be able to find the hider even if the hider is located in the cell that the drone just entered.

The success probabilities `game_config` file:

```python
SUCCES_PROBABILITIES = [1/3,2/3,3/4,4/5,9/10,95/100]
```

For each hider candidate a random sample is *drawn with replacement* from this `SUCCES_PROBABILITIES` list.

---

### Swarm & Drones

The swarm operates in a square grid environment which can be dynamically assigned in the `game_config`.
The first game-step or simulation step is the swarm entering the grid on position x,y = 0,0; </br> The swarm operates under the following restrictions and assumptions:

* Drones in a swarm **cannot move diagonally**;
* Drones in a swarm **know possible hiding 'candidates'** (cells where the hider might be hidden);
* Drones in a swarm **are aware of the success probabilities** the hiding candidates have ($p_i$).
* Drones in a swarm **Do not have access to the cell's hiding chances** the hiding candidates have (**q<sub>i</sub>**);
* If a drone enters / expands a hider candidate cell that contains the hider *and* the drone does not get taken down, then it has certainly found the hider. i.e.
  $P( \text{Found Hider} |  \text{Hider in cell} \land \text{not taken down}) = 1$
* If a drone enters / expands a hider candidate cell that contains the hider *and* the drone *does* get taken down, then it has not found the hider.

---

## Use:

Run directly from command line:

```sh
main.py --plot --tactic <tactic> --runs <nruns> --log
```

| CMD               |                    Explanation                    |
| :---------------- | :-----------------------------------------------: |
| --plot            |   Enables printed visualisation simulation runs.  |
| --tactic <tactic> |       Specify which searching tactic to use.      |
| --runs <nruns>    |       Specify the amount of simulation runs.      |
| --log             | Enables logging to csv file in sim_logs directory |
| --plotspeed       |      increase plot interval time must be > 0      |

---

## List of available tactics:

| Name                                     | Abbreviation |
| :--------------------------------------- | -----------: |
| 1. Together Traverse to Best Permutation |     **ttbp** |
| 2. Divide Over Risks                     |      **dor** |
| 3. Partitioned Horizontal Scan           |      **phs** |
| 4. Horizontal Scan                       |       **hs** |
| 5. Spiral Scan                           |       **sp** |
| 6. Random                                |     **rndm** |
| 7. Lidbetter                             |       **lb** |
| 8. Traverse ordered $Q_a$                |      **toq** |
| 9. Traverse weighted $Q_a$               |      **tpq** |
| 10. Discounted Distance                  |       **dd** |
| 11. Discounted Distance reverse          |      **ddr** |
| 12. Shared list                          |       **sl** |

---

## Recommended use:

Using --plot drastically slows down the simulation speed, as every step in the simulation something will be printed to console. Hence, the advise is to only use this when you want to visualise what is going on for demonstration or debugging purpose.

The simulation environment uses the NetworkX module as a backbone for calculating shortest paths, one can enable
RAPIDS nx-cugraph to make sure NetworkX is brought to full potential, this is a GPU Accelerated NetworkX Backend.
You can remove this line from main.py or simply put it to False if you don't want to deal with installing NX_CUGRAPH.

```python
NX_CUGRAPH_AUTOCONFIG=True
```

In terms of efficiency it does not make a big difference anyway, as with the current implementation the complete set of all shortest routes is only calculated once and then cached. Thus theoretically the main optimization that can be done here is with the initialization of the simulation.
More about NX_CUGRAPH:
[https://rapids.ai/nx-cugraph/](https://rapids.ai/nx-cugraph/)

---

# Searching policies

### Divide over risk

This strategy allocates the drone swarm to candidate locations proportionally to the risk associated with each location, defined as `1 - probability of success`. The goal is to send the largest groups of drones to the highest-risk locations first.

First, all candidate locations are sorted by risk. Then, a fractional number of drones is calculated for each location based on its proportional risk (e.g., 7.44 drones for location A, 2.56 for B). The algorithm assigns the *floor* of this number to each location (7 to A, 2 to B). The remaining drones (the "remainder") are then assigned one by one to the locations with the largest fractional parts (B would get the first remainder, as 0.56  > 0.44).

In the routing phase, all drones are assigned to visit all candidate locations. Each drone group's route is a `visit_order` list that is rotated to start with that group's primary assigned target. For example, if the ordered risk locations are `[A, B, C]`:

* Group A (highest risk): `[A, B, C]`
* Group B (mid risk): `[B, C, A]`
* Group C (low risk): `[C, A, B]`

---

### Lidbetter

In this searching strategy the cells are explored based on the optimal searching strategy given by Lidbetter 2020. A subset of possible hiding locations is chosen with probability $q_A$, after searching those, the remaining possible hiding locations are chosen uniformly at random. The swarm traverses all cells together.

$$
q_A = \lambda_k \prod_{i \in A} \frac{1 - p_i}{p_i}, \quad \text{where} \quad
\lambda_k = \left( \sum_{B \in S^{(k)}} \prod_{i \in B} \frac{1 - p_i}{p_i} \right)^{-1}.
$$

---

### Together traverse best permutation

This strategy calculates the optimal permutation of cells to visit, such that the total distance traveled is minimized. Given that the environment is a grid that does not allow diagonal movement, the Manhattan distance formula is used to calculate the distance:
$|x_1-x_2| + |y_1-y_2|$. The simulated implementation brute forces all options, and does not use any of the Traveling Salesman Problem optimizations. The swarm traverses all cells together.

---

### Traverse ordered $q_A$

This strategy assigns each drone to a different subset $A \in S^{(k)}$ based on the $q_A$ values from the Lidbetter equation above. All subsets are sorted in descending order by $q_A$, creating an ordered list where index 0 corresponds to the highest-value subset.

Drones are assigned sequentially: drone 1 receives the subset at index 0 (highest $q_A$), drone 2 receives index 1, and so on. If the number of drones exceeds the number of subsets, the assignment wraps around. For example, with 4 drones and 3 subsets, drone 4 would be assigned the subset at index 0 again.

After receiving its primary subset, each drone visits those cells first, then visits all remaining candidate locations in order of the list, wrapping around if the list gets exhausted.

---

### Traverse P $q_A$

This strategy independently samples a subset $A \in S^{(k)}$ for each drone according to the distribution $q_A$. This becomes its first objective, after which it traverses all remaining candidate cells in uniform random order, covering all possible hiding locations.

Whereas the Lidbetter policy has the swarm collectively choose a single subset according to $q_A$ and then visit the remainder uniformly at random together, this variant applies the same distribution per drone.

---

### Discounted Distance

This strategy selects the permutation of candidate cells that minimizes the total travel costs over the entire route, i.e., it takes the permutation whose total cost is minimal under the cost function below. Given consecutive cells $p_1=(x_1,y_1)$ and $p_2=(x_2,y_2)$:

$$
cost(p_1,p_2) = \left(|x_1-x_2|+|y_1-y_2|\right)\times \left(1-P_{p2}\right)
$$

The total route cost is the sum of these costs, and the implementation brute-forces all permutations to find the minimum-sum one with the swarm traversing together.

---

### Discounted Distance Reverse

This policy is almost identical to the previous one, yet now the discount factor is $P_{p2}$, yielding:

$$
cost(p_1,p_2) = (|x_1-x_2|+|y_1-y_2| ) \times  P_{p2}
$$

The simulated implementation brute forces all options, and does not use any of the Traveling Salesman Problem optimizations. The swarm traverses all cells together.

---

### Horizontal scan traversal

In this searching strategy drones collectively traverse the complete grid starting from top-left and ending on the bottom-left. This is done in the order: left to right, down, right to left, down, repeat. Thus making a 'snake-like' movement pattern.

---

### Partitioned horizontal scan traversal

This searching strategy is similar to the horizontal scan, yet drones now independently traverse the grid from top-left to bottom-left. They start at the top left, but divide themselves (as evenly as possible) over the vertical axis. Effectively scanning the board in partitions, making the same snake-like pattern, but starting at different parts of the board.

---

### Spiral scan traversal

In this searching strategy drones collectively traverse the grid in a spiraling pattern. Moving together from top left to bottom left, to bottom right, top right, back to the top left and going inwards right before the first cell. Continuing this movement until all cells have been expanded.

---

### Random Walk

In this search policy every drone can, at each time step *t*, independently choose to move in one of the North, East, South, West directions in uniform random order, restricted by the bounds of the grid.

---

### Shared list

Different from the other policies that are given an initial route and then fly it, this searching strategy dynamically assigns new locations—allowing the drones to communicate during the mission.

Let $S$ be the set of possible hiding locations. Initially, up to $\min(swarm_size, |S|)$ drones are assigned to hiding locations from $S$, leaving the remaining drones idle. The active and idle states are tracked, along with a 'to search' queue and a set of successfully searched locations. When a drone is assigned a location, that location is removed from the 'to search' queue.

If a drone dies during route traversal or while searching a location, that location is appended back to the 'to search' queue. The closest idle agent (measured by Manhattan distance) is then assigned this target. The route given to this reassigned agent avoids successfully searched locations.

When a drone successfully completes its route and searches a location, that location is added to the successfully searched set, and the drone returns to the idle state where it can be reassigned to remaining locations in the queue.

Note that there is no priority given to cells with a higher $1- p_i$ such that these are searched first. This could be a future improvement such that smaller sized swarms are more successful.

---

###### About the Dirichlet distribution alpha value:

In the implementation the definition of the Dirichlet distribution alpha is slightly adjusted.
The main code shows alpha as a scalar to control spread, in the 'Dist' class alpha is adjusted to be a 1-dimensional array filled with the scalar value.
By default, the alpha scalar is set to 2.
Meaning that with two hider candidates the resulting hiding probabilities, q<sub>1</sub> and q<sub>2</sub>, will be approximately 0.5 each.
If one wants to preserve an even distribution as the number of hider candidates increases, alpha should scale with it.
If alpha is kept fixed instead the resulting distribution becomes more spread out.

---

[^1]: Lidbetter T (2020) *Search and rescue in the face of uncertain threats*, European Journal of Operational Research 285(3):1153–1160.
    [https://doi.org/10.1016/j.ejor.2020.02.029](https://doi.org/10.1016/j.ejor.2020.02.029)

