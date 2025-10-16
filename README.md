# Simple drone swarm simulator in adversarial hide & seek environment
<p align="center">
<img src="img/PHS.png" width="400" >
</p>


---
# Todo
-[X] P<sub>i</sub> = Succes probability instead of risk probability
-[X] Implement optimal hiding strategy (Lidbetter)
-[X] Multiple hiders
-[ ] Find_steps == Time, change names
-[ ] more Plots
-[ ] Nieuwe strategieën
-[ ] Update readme.
___
## Game info


### Hider

The game features **n** static hiders, which can be placed in one of
**m<sub>hider_candidate</sub>** locations, denoted as the set **S**.
Both the number of hiders and the number of candidate locations are configurable in the `game_config` file.

> **Note:** Setting more than 10 hider candidates significantly impacts simulation speed for the **TTBP** tactic, due to the combinatorial explosion in possible hiding permutations.

At initialization, candidate cells are randomly selected from the grid and assigned hiding probabilities **q<sub>i</sub>**, based on the chosen hiding strategy.

---

#### Hiding Strategies

**Greedy**
: The hider(s) select the subset of candidate cells with the highest **q<sub>A</sub>** values.
The probabilities **q<sub>A</sub>** are derived following Lidbetter (2020) [^1], which provides the optimal hiding strategy for this class of Search and Rescue games.

**Weighted**
: The hider(s) select a subset of candidate cells according to the probability distribution over **S**, defined by **q<sub>i</sub>**.
As in the Greedy strategy, **q<sub>i</sub>** is based on Lidbetter (2020) [^1].

**Random**
: The hider(s) select one or more candidate cells **i ∈ S**, where probabilities **q<sub>i</sub>** are drawn from a Dirichlet distribution, ensuring
$$
\sum_{i=1}^{m_{\text{hider_candidate}}} q_i = 1.
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

[^1]: Lidbetter, T. (2020). *Search and Rescue Games*. **Operations Research**, 68(1), 203–214.

### Risks

Each hider_candidate cell $i, i \in S$, has a probability $p_i$., which is the probability that the Searcher is not taken down / captured when searching location $i$, we refer to this as the _success probability_ of location $i$</br>
This means that if the drone enters the cell, and is taken down or captured, it will not be able to find the hider even if the hider is located in the cell that the drone just entered.

The success probabilities `game_config` file:

```python
SUCCES_PROBABILITIES = [1/10,1/9,1/8,1/7,1/6,1/5,1/4,1/3]
```
For each hider candidate a random sample is *drawn with replacement* from this `SUCCES_PROBABILITIES` list.


### Swarm & Drones
The swarm operates in a square grid environment which can be dynamically assigned in the `game_config`.
The first game-step or simulation step is the swarm entering the grid on position x,y = 0,0;
</br> The swarm operates under the following restrictions and assumptions:
- Drones in a swarm **cannot move diagonally**;
- Drones in a swarm **know possible hiding 'candidates'** (cells where the hider might be hidden);
- Drones in a swarm **are aware of the success probabilities** the hiding candidates have ($p_i$).
- Drones in a swarm **are not aware of the hiding chances** the hiding candidates have (**q<sub>i</sub>**);
- If a drone enters / expands a hider candidate cell that contains the hider _and_ the drone does not get taken down, then it has certainly found the hider. i.e. 
$P( \text{Found Hider} |  \text{Hider in cell} \land \text{not taken down}) = 1$  
- If a drone enters / expands a hider candidate cell that contains the hider _and_ the drone *does* get taken down, then it has not found the hider. 


___ 

## Use:
Run directly from command line:

```sh
main.py --plot --tactic <tactic> --runs <nruns> --log
```
| CMD               |                    Explanation                    |
|:------------------|:-------------------------------------------------:|
| --plot            |  Enables printed visualisation simulation runs.   |
| --tactic <tactic> |      Specify which searching tactic to use.       |
| --runs <nruns>    |      Specify the amount of simulation runs.       |
| --log             | Enables logging to csv file in sim_logs directory |
| --plotspeed       | increase plot interval time must be > 0           | 

## List of available tactics:

| Name                                  | Abbreviation |
|:--------------------------------------|-------------:|
| Together Traverse to Best Permutation |     **ttbp** |
| Divide Over Risks                     |      **dor** |
| Partitioned Horizontal Scan           |      **phs** |
| Horizontal Scan                       |       **hs** |
| Vertical Scan                         |       **vs** |
| Random                                |     **rndm** |



### Recommended use:
Using --plot drastically slows down the simulation speed, as every step in the simulation something will be printed to console. Hence, the advise is to only use this when you want to visualise what is going on for demonstration or debugging purpose.


The simulation environment uses the NetworkX module as a backbone for calculating shortest paths, one can enable  
RAPIDS nx-cugraph to make sure NetworkX is brought to full potential, this is a GPU Accelerated NetworkX Backend.
You can remove this line from main.py or simply put it to False if you don't want to deal with installing NX_CUGRAPH. 
```python
NX_CUGRAPH_AUTOCONFIG=True
```
In terms of efficiency it does not make a big difference anyway, as with the current implementation the complete set of all shortest routes is only calculated once and then cached. Thus theoretically the main optimization that can be done here is with the initialization of the simulation.  
More about NX_CUGRAPH:
https://rapids.ai/nx-cugraph/




###### About the dirichlet distribution alpha value:
In the implementation the definition of the dirichlet distribution alpha is slightly adjusted. 
The main code shows alpha as a scalar to control spread, in the 'Dist' class alpha is adjusted to be a 1-dimensional array filled with the scalar value. 
By default, the alpha scalar is set to 2. 
Meaning that with two hider candidates the resulting hiding probabilities, q<sub>1</sub> and q<sub>2</sub>, will be approximately 0.5 each. 
If one want to preserve an even distribution as the number of hider candidates increases, alpha should scale with it. 
If alpha is kept fixed instead the resulting distribution becomes more spread out.


---
[^1]: Lidbetter T (2020) Search and rescue in the face of uncertain threats, European Journal of Operational Research 285(3):1153–1160.
https://doi.org/10.1016/j.ejor.2020.02.029