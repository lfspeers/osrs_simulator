"""Strategy optimization for Tempoross."""

from dataclasses import dataclass, field
from typing import Callable, Optional, Any
import itertools

from core.player import PlayerConfig


@dataclass
class Strategy:
    """Strategy parameters for Tempoross gameplay.

    Attributes:
        cook_ratio: Fraction of fish to cook (0.0 = never, 1.0 = always).
        fire_management: Whether to prioritize extinguishing fires.
        spirit_pool_threshold: Energy % to start attacking spirit pool.
        extend_game: Whether to try extending the game for more points.
    """
    cook_ratio: float = 0.0
    fire_management: bool = True
    spirit_pool_threshold: float = 0.0
    extend_game: bool = False

    def __post_init__(self):
        self.cook_ratio = max(0.0, min(1.0, self.cook_ratio))
        self.spirit_pool_threshold = max(0.0, min(1.0, self.spirit_pool_threshold))

    @classmethod
    def no_cook(cls) -> "Strategy":
        """Strategy optimized for fishing XP (no cooking)."""
        return cls(
            cook_ratio=0.0,
            fire_management=False,
            spirit_pool_threshold=0.0,
            extend_game=False
        )

    @classmethod
    def full_cook(cls) -> "Strategy":
        """Strategy that cooks all fish for more points."""
        return cls(
            cook_ratio=1.0,
            fire_management=True,
            spirit_pool_threshold=0.3,
            extend_game=False
        )

    @classmethod
    def firefighting(cls) -> "Strategy":
        """Strategy focused on points from firefighting."""
        return cls(
            cook_ratio=1.0,
            fire_management=True,
            spirit_pool_threshold=0.3,
            extend_game=True
        )

    @classmethod
    def balanced(cls) -> "Strategy":
        """Balanced strategy for decent XP and permits."""
        return cls(
            cook_ratio=0.5,
            fire_management=True,
            spirit_pool_threshold=0.2,
            extend_game=False
        )


@dataclass
class OptimizationResult:
    """Result from strategy optimization."""
    best_strategy: Strategy
    best_score: float
    best_result: Any  # GameResult
    all_results: list[tuple[Strategy, float, Any]] = field(default_factory=list)


def optimize(
    player_config: PlayerConfig,
    objective: Callable[[Any], float],
    constraints: Optional[dict] = None,
    num_simulations: int = 10,
    grid_resolution: int = 5,
    seed: Optional[int] = None
) -> tuple[Strategy, Any]:
    """Find optimal strategy for a given objective function.

    Uses grid search over strategy parameter space, running
    Monte Carlo simulations at each point.

    Args:
        player_config: Player stats and equipment.
        objective: Function that takes GameResult and returns score to maximize.
        constraints: Optional dict of parameter constraints.
        num_simulations: Simulations per strategy point.
        grid_resolution: Number of points per parameter dimension.
        seed: Optional random seed.

    Returns:
        Tuple of (best_strategy, best_game_result).

    Examples:
        # Maximize fishing XP per hour
        optimize(player, lambda r: r.fishing_xp_per_hour)

        # Maximize permits per hour
        optimize(player, lambda r: r.permits_per_hour)

        # Maximize points per tick
        optimize(player, lambda r: r.points_per_tick)

        # Maximize XP with minimum permit constraint
        optimize(player, lambda r: r.fishing_xp_per_hour if r.permits >= 5 else 0)
    """
    # Import here to avoid circular dependency
    from .simulation import Simulation, run_monte_carlo, average_results

    # Generate parameter grid
    cook_ratios = [i / (grid_resolution - 1) for i in range(grid_resolution)]
    fire_management_options = [True, False]
    spirit_thresholds = [i / (grid_resolution - 1) for i in range(grid_resolution)]
    extend_options = [True, False]

    # Apply constraints if provided
    if constraints:
        if "cook_ratio" in constraints:
            cook_ratios = [constraints["cook_ratio"]]
        if "fire_management" in constraints:
            fire_management_options = [constraints["fire_management"]]
        if "spirit_pool_threshold" in constraints:
            spirit_thresholds = [constraints["spirit_pool_threshold"]]
        if "extend_game" in constraints:
            extend_options = [constraints["extend_game"]]

    best_strategy = None
    best_score = float("-inf")
    best_result = None

    # Grid search
    for cook, fire, spirit, extend in itertools.product(
        cook_ratios, fire_management_options, spirit_thresholds, extend_options
    ):
        strategy = Strategy(
            cook_ratio=cook,
            fire_management=fire,
            spirit_pool_threshold=spirit,
            extend_game=extend
        )

        # Run simulations
        results = run_monte_carlo(
            player_config=player_config,
            strategy=strategy,
            num_simulations=num_simulations,
            seed=seed
        )
        avg_result = average_results(results)

        # Evaluate objective
        score = objective(avg_result)

        if score > best_score:
            best_score = score
            best_strategy = strategy
            best_result = avg_result

    return best_strategy, best_result


def find_pareto_optimal(
    player_config: PlayerConfig,
    objectives: list[Callable[[Any], float]],
    num_simulations: int = 10,
    grid_resolution: int = 5,
    seed: Optional[int] = None
) -> list[tuple[Strategy, Any, list[float]]]:
    """Find Pareto-optimal strategies for multiple objectives.

    A strategy is Pareto-optimal if no other strategy is better
    in all objectives simultaneously.

    Args:
        player_config: Player stats and equipment.
        objectives: List of objective functions to maximize.
        num_simulations: Simulations per strategy point.
        grid_resolution: Number of points per parameter dimension.
        seed: Optional random seed.

    Returns:
        List of (strategy, result, scores) tuples on Pareto frontier.
    """
    from .simulation import run_monte_carlo, average_results

    # Generate all strategies
    cook_ratios = [i / (grid_resolution - 1) for i in range(grid_resolution)]
    fire_management_options = [True, False]
    spirit_thresholds = [i / (grid_resolution - 1) for i in range(grid_resolution)]
    extend_options = [True, False]

    all_points = []

    for cook, fire, spirit, extend in itertools.product(
        cook_ratios, fire_management_options, spirit_thresholds, extend_options
    ):
        strategy = Strategy(
            cook_ratio=cook,
            fire_management=fire,
            spirit_pool_threshold=spirit,
            extend_game=extend
        )

        results = run_monte_carlo(
            player_config=player_config,
            strategy=strategy,
            num_simulations=num_simulations,
            seed=seed
        )
        avg_result = average_results(results)

        scores = [obj(avg_result) for obj in objectives]
        all_points.append((strategy, avg_result, scores))

    # Find Pareto frontier
    pareto_optimal = []
    for i, (strat_i, result_i, scores_i) in enumerate(all_points):
        is_dominated = False
        for j, (strat_j, result_j, scores_j) in enumerate(all_points):
            if i == j:
                continue
            # Check if j dominates i
            if all(sj >= si for sj, si in zip(scores_j, scores_i)) and \
               any(sj > si for sj, si in zip(scores_j, scores_i)):
                is_dominated = True
                break
        if not is_dominated:
            pareto_optimal.append((strat_i, result_i, scores_i))

    return pareto_optimal


# Preset objective functions
def maximize_fishing_xp(result) -> float:
    """Objective: maximize fishing XP per hour."""
    return result.fishing_xp_per_hour


def maximize_total_xp(result) -> float:
    """Objective: maximize total XP per hour."""
    return result.total_xp_per_hour


def maximize_permits(result) -> float:
    """Objective: maximize permits per hour."""
    return result.permits_per_hour


def maximize_points(result) -> float:
    """Objective: maximize points per game."""
    return result.points


def maximize_efficiency(result) -> float:
    """Objective: maximize points per tick."""
    return result.points_per_tick


def minimize_game_time(result) -> float:
    """Objective: minimize game time (maximize negative time)."""
    return -result.game_time_minutes
