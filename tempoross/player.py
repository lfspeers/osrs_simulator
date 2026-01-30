"""Tempoross-specific player actions and mechanics."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import random

from core.player import PlayerConfig, Inventory, HarpoonType
from core.tick import GameClock
from .mechanics import TemporossGame, PointAction, Phase


class ActionType(Enum):
    """Types of actions a player can perform in Tempoross."""
    IDLE = auto()
    FISHING = auto()
    COOKING = auto()
    LOADING_CANNON = auto()
    REPAIRING = auto()
    DOUSING = auto()
    TETHERING = auto()
    SPIRIT_HARPOON = auto()
    MOVING = auto()


class FishType(Enum):
    """Types of fish in Tempoross."""
    RAW = "raw_harpoonfish"
    COOKED = "cooked_harpoonfish"
    CRYSTALLISED = "crystallised_harpoonfish"


@dataclass
class CatchRateCalculator:
    """Calculate fishing catch rates based on player stats."""

    # Base catch rate constants
    BASE_RATE = 170
    MAX_RATE = 255
    RATE_DENOMINATOR = 256

    @classmethod
    def get_success_chance(cls, fishing_level: int, harpoon_type: HarpoonType) -> float:
        """Calculate chance to catch a fish per attempt.

        Formula: success_chance = (170 + 85 * (level-1)/98) / 256

        At level 35: ~78% success
        At level 99: 100% success
        """
        level = max(1, min(99, fishing_level))

        # Base success rate scales with level
        rate = cls.BASE_RATE + (cls.MAX_RATE - cls.BASE_RATE) * (level - 1) / 98
        base_chance = rate / cls.RATE_DENOMINATOR

        # Harpoon doesn't affect catch rate, only speed
        return min(1.0, base_chance)

    @classmethod
    def get_ticks_per_attempt(cls, harpoon_type: HarpoonType) -> int:
        """Get number of ticks per fishing attempt.

        Base: 5 ticks
        Dragon/Infernal/Crystal: 4 ticks
        """
        base_ticks = 5
        return base_ticks - harpoon_type.speed_modifier


@dataclass
class TemporossPlayer:
    """A player participating in the Tempoross minigame.

    Handles player actions, inventory, and state during the game.
    """
    config: PlayerConfig
    inventory: Inventory = field(default_factory=Inventory)

    # Current state
    current_action: ActionType = ActionType.IDLE
    action_ticks_remaining: int = 0

    # Statistics
    total_fish_caught: int = 0
    total_fish_cooked: int = 0

    # Random number generator
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self):
        # Initialize inventory with reserved slots for tools
        reserved = self.config.get_reserved_slots()
        self.inventory = Inventory(reserved_slots=reserved)

    @property
    def raw_fish_count(self) -> int:
        """Number of raw fish in inventory."""
        return self.inventory.count_item(FishType.RAW.value)

    @property
    def cooked_fish_count(self) -> int:
        """Number of cooked fish in inventory."""
        return self.inventory.count_item(FishType.COOKED.value)

    @property
    def crystallised_fish_count(self) -> int:
        """Number of crystallised fish in inventory."""
        return self.inventory.count_item(FishType.CRYSTALLISED.value)

    @property
    def total_fish_count(self) -> int:
        """Total fish in inventory."""
        return self.raw_fish_count + self.cooked_fish_count + self.crystallised_fish_count

    @property
    def is_busy(self) -> bool:
        """Check if player is currently performing an action."""
        return self.action_ticks_remaining > 0

    @property
    def inventory_full(self) -> bool:
        """Check if inventory is full."""
        return self.inventory.available_slots <= 0

    def start_fishing(self, double_spot: bool = False) -> int:
        """Start fishing action.

        Args:
            double_spot: Whether fishing at a double-catch spot.

        Returns:
            Number of ticks until action completes.
        """
        ticks = CatchRateCalculator.get_ticks_per_attempt(self.config.harpoon_type)
        self.current_action = ActionType.FISHING
        self.action_ticks_remaining = ticks
        return ticks

    def process_fishing_tick(self, game: TemporossGame, double_spot: bool = False) -> int:
        """Process a fishing tick.

        Returns:
            Number of fish caught this tick (0, 1, or 2).
        """
        if self.current_action != ActionType.FISHING:
            return 0

        self.action_ticks_remaining -= 1

        if self.action_ticks_remaining > 0:
            return 0

        # Attempt complete - check for catch
        fish_caught = 0

        if self.inventory_full:
            self.current_action = ActionType.IDLE
            return 0

        success_chance = CatchRateCalculator.get_success_chance(
            self.config.fishing_level,
            self.config.harpoon_type
        )

        if self.rng.random() < success_chance:
            # Check for infernal harpoon auto-cook
            if (self.config.harpoon_type == HarpoonType.INFERNAL and
                    self.rng.random() < self.config.harpoon_type.auto_cook_chance):
                self.inventory.add_item(FishType.COOKED.value)
                game.xp.add_cooking_xp()
                game.points.add(PointAction.COOK)
                self.total_fish_cooked += 1
            else:
                self.inventory.add_item(FishType.RAW.value)

            game.xp.add_fishing_xp(self.config.fishing_level)
            game.points.add(PointAction.FISH)
            fish_caught += 1
            self.total_fish_caught += 1

            # Double catch chance
            if double_spot and self.rng.random() < 0.5 and not self.inventory_full:
                self.inventory.add_item(FishType.RAW.value)
                game.xp.add_fishing_xp(self.config.fishing_level)
                game.points.add(PointAction.FISH)
                fish_caught += 1
                self.total_fish_caught += 1

        self.current_action = ActionType.IDLE
        return fish_caught

    def start_cooking(self) -> int:
        """Start cooking action.

        Returns:
            Number of ticks until action completes (0 if no fish).
        """
        if self.raw_fish_count == 0:
            return 0

        self.current_action = ActionType.COOKING
        self.action_ticks_remaining = 3  # Cooking takes 3 ticks
        return 3

    def process_cooking_tick(self, game: TemporossGame) -> bool:
        """Process a cooking tick.

        Returns:
            True if cooking completed this tick.
        """
        if self.current_action != ActionType.COOKING:
            return False

        self.action_ticks_remaining -= 1

        if self.action_ticks_remaining > 0:
            return False

        # Cook one fish
        if self.inventory.remove_item(FishType.RAW.value):
            self.inventory.add_item(FishType.COOKED.value)
            game.xp.add_cooking_xp()
            game.points.add(PointAction.COOK)
            self.total_fish_cooked += 1

        self.current_action = ActionType.IDLE
        return True

    def deposit_fish(self, game: TemporossGame, cannon_index: int = 0) -> tuple[int, int]:
        """Deposit all fish into a cannon.

        Args:
            game: The game instance.
            cannon_index: Which cannon to load.

        Returns:
            Tuple of (raw_deposited, cooked_deposited).
        """
        raw = self.raw_fish_count
        cooked = self.cooked_fish_count

        raw_loaded, cooked_loaded = game.load_cannon(cannon_index, raw, cooked)

        if raw_loaded > 0:
            self.inventory.remove_item(FishType.RAW.value, raw_loaded)
        if cooked_loaded > 0:
            self.inventory.remove_item(FishType.COOKED.value, cooked_loaded)

        return raw_loaded, cooked_loaded

    def repair_mast(self, game: TemporossGame, mast_index: int) -> bool:
        """Attempt to repair a mast.

        Args:
            game: The game instance.
            mast_index: Which mast to repair.

        Returns:
            True if repair was successful.
        """
        self.current_action = ActionType.REPAIRING
        self.action_ticks_remaining = 2  # Repair takes ~2 ticks

        return game.repair_mast(mast_index)

    def douse_fire(self, game: TemporossGame, totem_index: int) -> bool:
        """Attempt to douse a fire.

        Args:
            game: The game instance.
            totem_index: Which totem to douse.

        Returns:
            True if dousing was successful.
        """
        self.current_action = ActionType.DOUSING
        self.action_ticks_remaining = 2  # Dousing takes ~2 ticks

        return game.douse_fire(totem_index)

    def harpoon_spirit_pool(self, game: TemporossGame) -> float:
        """Attack a spirit pool during Phase 2.

        Args:
            game: The game instance.

        Returns:
            Damage dealt to essence pool.
        """
        if game.phase != Phase.PHASE_2:
            return 0.0

        self.current_action = ActionType.SPIRIT_HARPOON
        ticks = CatchRateCalculator.get_ticks_per_attempt(self.config.harpoon_type)
        self.action_ticks_remaining = ticks

        # Calculate damage based on success
        success_chance = CatchRateCalculator.get_success_chance(
            self.config.fishing_level,
            self.config.harpoon_type
        )

        if self.rng.random() < success_chance:
            damage = 10.0  # Base damage per successful harpoon
            return game.harpoon_spirit_pool(damage)

        return 0.0

    def tick(self, game: TemporossGame, double_spot: bool = False):
        """Process one game tick for this player.

        This handles ongoing action completion.
        """
        if self.current_action == ActionType.FISHING:
            self.process_fishing_tick(game, double_spot)
        elif self.current_action == ActionType.COOKING:
            self.process_cooking_tick(game)
        elif self.action_ticks_remaining > 0:
            self.action_ticks_remaining -= 1
            if self.action_ticks_remaining <= 0:
                self.current_action = ActionType.IDLE

    def reset(self):
        """Reset player state for a new game."""
        self.inventory.clear_fish()
        self.current_action = ActionType.IDLE
        self.action_ticks_remaining = 0
        self.total_fish_caught = 0
        self.total_fish_cooked = 0
