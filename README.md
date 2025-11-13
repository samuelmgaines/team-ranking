# Ranking Algorithm

## Introduction

There are many ways to rank competitors using results from one-on-one games. Professional leagues such as the NFL and NBA use deterministic rules based on record, division standings, and head-to-head outcomes. Tennis uses a cumulative point system to determine ATP world rankings. College sports, however, typically rely on committees to make subjective decisions.

Committee-based systems generate controversy, yet relying solely on win–loss records is inadequate in some leagues because teams play vastly different schedules.

My view is that **the most important property of a ranking is consistency**—if competitor $A$ defeats competitor $B$, then $A$ should be ranked higher than $B$.

This document introduces a ranking system that **prioritizes consistency above all else**, and then enhances it with tunable parameters that address realistic edge cases. This remains a work in progress.

## The First Ranking System

### Competitors, Games, and Ranks

Suppose we have $n$ competitors labelled $c_1, c_2, ..., c_n$.

A **game** is an ordered pair $(c_i, c_j)$ indicating that $c_i$ defeated $c_j$. We treat the set of games $G$ as a **multiset**: the same match may appear multiple times, and each appearance contributes separately to totals.

Each competitor is assigned a unique integer rank from $1$ (best) to $n$ (worst). Thus,

-   $1 \leq r_i \leq n$ for all $i$,
-   $r_i \neq r_j$ for all $i \neq j$.

In other words, the rank vector $r = (r_1, ..., r_n)$ is a permutation of $\{1, ..., n\}$.

### First Mathematical Formulation

An **inconsistency** occurs when a lower-ranked competitor defeats a higher-ranked one. For a game $(c_i, c_j)$:

-   If the ranking agrees with the outcome ($r_i < r_j$), the inconsistency score is $0$.
-   If the ranking contradicts the result ($r_i > r_j$), the inconsistency score is $r_i - r_j$.

These cases can be written compactly as:

$$
max(0, r_i - r_j).
$$

The **total inconsistency score** is the sum of these values over all games. To prioritize consistency, we minimize this score subject to ranking constraints:

$$
\min \sum_{(c_i, c_j) \in G} \max(0, r_i - r_j)\\
\text{s.t. } r_i \neq r_j \text{ } \forall \text{ } i \neq j \\
r_i \in {1, ..., n} \text{ } \forall \text{ } i
\tag{1}
$$

This formulation is valid and captures the idea of minimizing ranking contradictions. However, it has some shortcomings, which motivate additional refinements.

## The Improved Ranking System

Optimization problem $(1)$ focuses solely on the **total magnitude** of inconsistencies. While this is desirable, it misses two features commonly valued in rankings:

1. Respecting head-to-head results, even when inconsistency magnitudes tie.

2. Considering strength of schedule, once consistency is maximized.

We address each separately.

### Respecting Head-To-Head Results

Consider three competitors $c_1$, $c_2$, and $c_3$:

-   $c_1$ beats $c_2$
-   $c_1$ loses to $c_3$

Suppose $c_1$ and $c_2$ are clearly above the rest. Under formulation $(1)$:

-   Ranking $c_1 = 1, c_2 = 2$ yields total inconsistency $r_3 - 1$.
-   Ranking $c_1 = 2, c_2 = 1$ yields total inconsistency $1 + (r_3 - 2) = r_3 - 1$.

Thus, both are equally consistent under $(1)$. But intuitively—and in common ranking systems—**if the magnitude ties, the ranking with fewer inconsistencies should be preferred**. In this example, $c_1$ should be ranked above $c_2$.

To accomplish this, we introduce a parameter $\alpha \geq 0$ that assigns an additional penalty per inconsistent game. Define:

$$
I(r_i, r_j, \alpha) =
\begin{cases}
    0 & \text{if } r_i < r_j,\\
    (r_i - r_j) + \alpha  & \text{if } r_i > r_j.
\end{cases}
\tag{2}
$$

Interpretation of $\alpha$:

-   $\alpha = 0$: pure magnitude—this recovers formulation $(1)$.
-   $\alpha = 1$: ties in magnitude are broken by counting inconsistencies.
-   $\alpha > 1$: strongly prioritizes minimizing the _number_ of inconsistencies.

Requiring $\alpha$ to be an integer ensures inconsistency scores remain integer-valued, which will be important later when we add a fractional tie-breaker.

### Considering Strength Of Schedule

Even after prioritizing consistency and inconsistency counts, multiple rankings may have identical inconsistency scores. To distinguish these, we incorporate a **strength of schedule (SOS)** measure.

#### Computing SOS

Critically, **We evaluate strength of schedule _only_ using consistent games.** Inconsistent games already affect the objective through inconsistency penalties.

For competitor $c_i$:

-   $W_i$: set of opponents that $c_i$ defeated in **consistent** games.
-   $L_i$: set of opponents that defeated $c_i$ in **consistent** games.

Define:

-   Quality of wins:
    $$
    Q_i^{\text{win}} = \sum_{c_j \in W_i} (n - r_j + 1)^k
    $$
-   Severity of losses:
    $$
    Q_i^{\text{loss}} = \sum_{c_j \in L_i} (r_j)^k
    $$

Let:

-   $Q_{\text{max}}^{\text{win}} = \max_{m} Q_m^{\text{win}}$ (maximum quality of wins among all competitors)

-   $Q_{\text{max}}^{\text{loss}} = \max_{m} Q_m^{\text{loss}}$ (maximum severity of losses among all competitors)

We then define:

$$
\text{SOS}_i = \lambda \cdot \frac{Q_i^\text{win}}{Q_\text{max}^\text{win} + \epsilon} - (1 - \lambda) \cdot \frac{Q_i^\text{loss}}{Q_\text{max}^\text{loss} + \epsilon}.
\tag{3}
$$

Here:

-   $\epsilon > 0$ ensures division remains well*defined \_and* keeps SOS strictly less than $1$ in magnitude, which will preserve consistency dominance.
-   $\lambda \in [0, 1]$ sets the win/loss weighting.
-   $k \geq 0$ controls the emphasis on opponent quality.

Parameter interpretations:

-   $\lambda = 1$: only wins influence SOS
-   $\lambda = 0$: only losses influence SOS
-   $\lambda = 0.5$: balanced wins and losses
-   $k = 0$: all wins and losses count equally
-   $k = 1$: linear emphasis on opponent rank
-   $k > 1$: rewards elite wins heavily and penalizes bad losses harshly

SOS behaves intuitively:

-   Adding a consistent win always increases $\text{SOS}_i$.
-   Adding a consistent loss always decreases $\text{SOS}_i$.

#### Using SOS as a tie-breaker

We incorporate strength of schedule using the term:

$$
\frac{2}{n(n+1)} \cdot \sum_{i=1}^n(\text{SOS}_i \cdot r_i).
$$

Multiplying by $r_i$ ensures:

-   Because the objective is minimized, a higher SOS is preferred when paired with a smaller $r_i$ (a better rank).
-   This aligns the minimization with the intuitive principle that stronger schedules should correspond to better ranks.

The scaling factor $\frac{2}{n(n+1)}$ ensures:

-   This term is strictly less than $1$ in magnitude.
-   Inconsistency scores—which are integers due to integer $\alpha$—always dominate SOS effects.

Thus, the system remains philosophically consistent: strength of schedule matters _only after_ consistency is maximized.

### Improved Mathematical Formulation

Combining everything, the final optimization problem is:

$$
\min \sum_{(c_i, c_j) \in G} I(r_i, r_j, \alpha) + \frac{2}{n(n+1)} \cdot \sum_{i=1}^n(\text{SOS}_i \cdot r_i)\\
\text{s.t. } r_i \neq r_j \text{ } \forall \text{ } i \neq j, \\
r_i \in {1, ..., n} \text{ } \forall \text{ } i.
\tag{4}
$$

Where:

-   $I$ is defined in $(2)$
-   $\text{SOS}_i$ is defined in $(3)$
-   $W_i = \{c_j : (c_i, c_j) \in G \text{ and } r_i < r_j\}$
-   $L_i = \{c_j : (c_j, c_i) \in G \text{ and } r_i > r_j\}$
-   $\alpha \geq 0$ is an integer
-   $\epsilon > 0, k \geq 0, \lambda \in [0, 1]$

This formulation:

-   **Minimizes inconsistency magnitude**
-   **Minimizes number of inconsistencies** (via $\alpha$)
-   **Breaks remaining ties using strength of schedule**, scaled so that consistency always dominates

Together, these components produce rankings that are consistent, interpretable, and tunably sensitive to quality of competition.

## The Computation

Description of how the ranking is actually computed.

TODO:

-   Make cooling rate a parameter
-   Make max window search a parameter
-   Output sliding passes actually used

## The Repository

Description of the parts of the repository and how to use it.
