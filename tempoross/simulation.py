"""Game loop simulator for Tempoross."""

from dataclasses import dataclass, field
from typing import Optional
import random

from core.player import PlayerConfig
from core.tick import GameClock, ticks_per_hour, TICK_DURATION
from .entities import Tempoross
from .mechanics import TemporossGame, Phase, PointAction
from .player import TemporossPlayer, ActionType, FishType
from .optimizer import Strategy


@dataclass
class GameResult:
    """Results from a single Tempoross game simulation.

    Contains all relevant statistics and derived rates.
    """
    ticks_elapsed: int = 0
    fishing_xp: float = 0.0
    cooking_xp: float = 0.0
    points: int = 0
    permits: int = 0

    # Additional stats
    fish_caught: int = 0
    fish_cooked: int = 0
    raw_deposited: int = 0
    cooked_deposited: int = 0
    repairs: int = 0
    fires_doused: int = 0
    spirit_harpoons: int = 0
    cycles_completed: int = 0
    victory: bool = False

    @property
    def game_time_seconds(self) -> float:
        """Game duration in seconds."""
        return self.ticks_elapsed * TICK_DURATION

    @property
    def game_time_minutes(self) -> float:
        """Game duration in minutes."""
        return self.game_time_seconds / 60

    @property
    def games_per_hour(self) -> float:
        """Estimated games that can be played per hour.

        Includes ~30 seconds for lobby/loading.
        """
        if self.ticks_elapsed == 0:
            return 0.0
        game_time = self.game_time_seconds + 30  # Add lobby time
        return 3600 / game_time

    @property
    def fishing_xp_per_hour(self) -> float:
        """Fishing XP per hour."""
        return self.fishing_xp * self.games_per_hour

    @property
    def cooking_xp_per_hour(self) -> float:
        """Cooking XP per hour."""
        return self.cooking_xp * self.games_per_hour

    @property
    def total_xp_per_hour(self) -> float:
        """Total XP per hour (fishing + cooking)."""
        return self.fishing_xp_per_hour + self.cooking_xp_per_hour

    @property
    def permits_per_hour(self) -> float:
        """Reward permits per hour."""
        return self.permits * self.games_per_hour

    @property
    def points_per_tick(self) -> float:
        """Points earned per game tick."""
        if self.ticks_elapsed == 0:
            return 0.0
        return self.points / self.ticks_elapsed

    def __str__(self) -> str:
        return (
            f"GameResult(\n"
            f"  Time: {self.game_time_minutes:.1f} min ({self.ticks_elapsed} ticks)\n"
            f"  Points: {self.points} ({self.permits} permits)\n"
            f"  Fishing XP: {self.fishing_xp:.0f} ({self.fishing_xp_per_hour:.0f}/hr)\n"
            f"  Cooking XP: {self.cooking_xp:.0f} ({self.cooking_xp_per_hour:.0f}/hr)\n"
            f"  Permits/hr: {self.permits_per_hour:.1f}\n"
            f"  Victory: {self.victory}\n"
            f")"
        )


class Simulation:
    """Tick-accurate Tempoross game simulator.

    Simulates a complete game with configurable strategy and
    player setup.
    """

    # Game constants
    MAX_TICKS = 2000  # ~20 minutes max game length (safety limit)
    DEPOSIT_TICKS = 2  # Ticks to deposit fish
    MOVE_TICKS = 3  # Ticks to move between locations

    def __init__(
        self,
        player_config: PlayerConfig,
        strategy: Strategy,
        num_players: int = 1,
        seed: Optional[int] = None
    ):
        """Initialize simulation.

        Args:
            player_config: Player stats and equipment.
            strategy: Strategy parameters.
            num_players: Number of players in the game.
            seed: Optional random seed for reproducibility.
        """
        self.player_config = player_config
        self.strategy = strategy
        self.num_players = num_players
        self.seed = seed

        self.rng = random.Random(seed)
        self.game: Optional[TemporossGame] = None
        self.player: Optional[TemporossPlayer] = None
        self.clock: Optional[GameClock] = None

        # Track when we last fired cannons
        self._last_cannon_fire_tick = 0
        self._cannon_fire_cooldown = 5  # Min ticks between checking cannon

    def run(self) -> GameResult:
        """Run a complete game simulation.

        Returns:
            GameResult with all statistics.
        """
        # Initialize game state
        self.game = TemporossGame.create(self.num_players, self.seed)
        self.player = TemporossPlayer(self.player_config)
        self.player.rng = self.rng
        self.clock = GameClock()
        self._last_cannon_fire_tick = 0

        # Run game loop
        while not self.game.is_game_over and self.clock.tick < self.MAX_TICKS:
            self._simulate_tick()

        # Compile results
        return self._compile_results()

    def _simulate_tick(self):
        """Simulate a single game tick."""
        self.clock.advance()
        self.game.tick()

        # Process player action
        if self.player.is_busy:
            self.player.tick(self.game)
        else:
            self._decide_action()

        # Auto-fire cannons when loaded and in Phase 1
        if self.game.phase == Phase.PHASE_1:
            self._check_and_fire_cannons()

    def _check_and_fire_cannons(self):
        """Check if cannons should be fired."""
        if self.clock.tick - self._last_cannon_fire_tick < self._cannon_fire_cooldown:
            return

        total_loaded = sum(c.total_loaded for c in self.game.cannons)
        if total_loaded >= 10:  # Fire when we have a decent amount loaded
            damage = self.game.fire_cannons()
            if damage > 0:
                self._last_cannon_fire_tick = self.clock.tick

    def _decide_action(self):
        """Decide and start the next player action based on strategy."""
        game = self.game
        player = self.player
        strategy = self.strategy

        # Check for hazards first if fire management enabled
        if strategy.fire_management:
            damaged_masts, fires = game.get_hazard_count()

            if fires > 0:
                # Find first fire and douse it
                for i, totem in enumerate(game.totems):
                    if totem.on_fire:
                        player.douse_fire(game, i)
                        return

            if damaged_masts > 0:
                # Find first damaged mast and repair it
                for i, mast in enumerate(game.masts):
                    if mast.damaged:
                        player.repair_mast(game, i)
                        return

        # Phase-specific logic
        if game.phase == Phase.PHASE_1:
            self._phase_1_action()
        elif game.phase == Phase.PHASE_2:
            self._phase_2_action()

    def _phase_1_action(self):
        """Decide action during Phase 1 (surfaced)."""
        player = self.player
        game = self.game
        strategy = self.strategy

        # Check if we should cook
        should_cook = (
            strategy.cook_ratio > 0 and
            player.raw_fish_count > 0 and
            self.rng.random() < strategy.cook_ratio
        )

        # If inventory full, deposit and fire cannons
        if player.inventory_full:
            raw, cooked = player.deposit_fish(game)
            # Fire cannons after depositing
            game.fire_cannons()
            self._last_cannon_fire_tick = self.clock.tick
            return

        # If we have enough fish and want to deposit
        if player.total_fish_count >= player.inventory.fish_capacity * 0.7:
            # Cook remaining raw fish if strategy says so
            if should_cook and player.raw_fish_count > 0:
                player.start_cooking()
                return

            # Otherwise deposit
            raw, cooked = player.deposit_fish(game)
            return

        # Cook if strategy dictates and we have raw fish
        if should_cook and player.raw_fish_count > 0:
            player.start_cooking()
            return

        # Default: fish
        player.start_fishing()

    def _phase_2_action(self):
        """Decide action during Phase 2 (submerged)."""
        player = self.player
        game = self.game
        strategy = self.strategy

        # Always attack spirit pool during Phase 2 to drain essence
        player.harpoon_spirit_pool(game)

    def _compile_results(self) -> GameResult:
        """Compile simulation results into GameResult."""
        game = self.game
        player = self.player
        points = game.points

        return GameResult(
            ticks_elapsed=self.clock.tick,
            fishing_xp=game.xp.fishing_xp,
            cooking_xp=game.xp.cooking_xp,
            points=points.total,
            permits=points.calculate_permits(),
            fish_caught=points.fish_caught,
            fish_cooked=points.fish_cooked,
            raw_deposited=points.raw_deposited,
            cooked_deposited=points.cooked_deposited,
            repairs=points.repairs,
            fires_doused=points.fires_doused,
            spirit_harpoons=points.spirit_harpoons,
            cycles_completed=game.cycles_failed + (1 if game.is_victory else 0),
            victory=game.is_victory
        )


def run_monte_carlo(
    player_config: PlayerConfig,
    strategy: Strategy,
    num_players: int = 1,
    num_simulations: int = 100,
    seed: Optional[int] = None
) -> list[GameResult]:
    """Run multiple simulations and return all results.

    Args:
        player_config: Player stats and equipment.
        strategy: Strategy parameters.
        num_players: Number of players in the game.
        num_simulations: Number of games to simulate.
        seed: Base random seed (incremented for each sim).

    Returns:
        List of GameResult objects.
    """
    results = []
    base_seed = seed if seed is not None else random.randint(0, 2**32)

    for i in range(num_simulations):
        sim = Simulation(
            player_config=player_config,
            strategy=strategy,
            num_players=num_players,
            seed=base_seed + i
        )
        results.append(sim.run())

    return results


def average_results(results: list[GameResult]) -> GameResult:
    """Calculate average across multiple game results.

    Args:
        results: List of GameResult objects.

    Returns:
        GameResult with averaged values.
    """
    if not results:
        return GameResult()

    n = len(results)
    return GameResult(
        ticks_elapsed=int(sum(r.ticks_elapsed for r in results) / n),
        fishing_xp=sum(r.fishing_xp for r in results) / n,
        cooking_xp=sum(r.cooking_xp for r in results) / n,
        points=int(sum(r.points for r in results) / n),
        permits=int(sum(r.permits for r in results) / n),
        fish_caught=int(sum(r.fish_caught for r in results) / n),
        fish_cooked=int(sum(r.fish_cooked for r in results) / n),
        raw_deposited=int(sum(r.raw_deposited for r in results) / n),
        cooked_deposited=int(sum(r.cooked_deposited for r in results) / n),
        repairs=int(sum(r.repairs for r in results) / n),
        fires_doused=int(sum(r.fires_doused for r in results) / n),
        spirit_harpoons=int(sum(r.spirit_harpoons for r in results) / n),
        cycles_completed=int(sum(r.cycles_completed for r in results) / n),
        victory=sum(1 for r in results if r.victory) > n // 2
    )
