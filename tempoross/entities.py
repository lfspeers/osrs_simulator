"""Tempoross boss and game entities."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class SpotType(Enum):
    """Types of fishing spots in the arena."""
    NORMAL = "normal"
    DOUBLE = "double"  # Has 50% chance for bonus fish


@dataclass
class FishingSpot:
    """A fishing spot in the Tempoross arena.

    Attributes:
        spot_type: Whether this is a normal or double-catch spot.
        active: Whether the spot is currently fishable.
        fish_remaining: Number of fish before spot moves (if applicable).
    """
    spot_type: SpotType = SpotType.NORMAL
    active: bool = True
    fish_remaining: Optional[int] = None

    @property
    def double_catch_chance(self) -> float:
        """Chance to catch a second fish."""
        return 0.5 if self.spot_type == SpotType.DOUBLE else 0.0


@dataclass
class SpiritPool:
    """Spirit pool for draining Tempoross essence during Phase 2.

    Fishing the spirit pool deals essence damage and awards points.
    """
    active: bool = True

    # Points per successful harpoon action
    POINTS_PER_ACTION = 55


@dataclass
class Cannon:
    """Harpoonfish cannon for damaging Tempoross.

    Players load fish into cannons to deal energy damage.
    """
    loaded_raw: int = 0
    loaded_cooked: int = 0
    max_capacity: int = 40  # Approximate capacity

    # Damage values
    RAW_DAMAGE = 10
    COOKED_DAMAGE = 15

    @property
    def total_loaded(self) -> int:
        """Total fish loaded in cannon."""
        return self.loaded_raw + self.loaded_cooked

    @property
    def available_space(self) -> int:
        """Space remaining in cannon."""
        return max(0, self.max_capacity - self.total_loaded)

    def load(self, raw: int = 0, cooked: int = 0) -> tuple[int, int]:
        """Load fish into the cannon.

        Args:
            raw: Number of raw fish to load.
            cooked: Number of cooked fish to load.

        Returns:
            Tuple of (raw_loaded, cooked_loaded) - actual amounts loaded.
        """
        space = self.available_space
        raw_to_load = min(raw, space)
        space -= raw_to_load
        cooked_to_load = min(cooked, space)

        self.loaded_raw += raw_to_load
        self.loaded_cooked += cooked_to_load
        return raw_to_load, cooked_to_load

    def fire(self) -> int:
        """Fire the cannon and return total damage dealt."""
        damage = (self.loaded_raw * self.RAW_DAMAGE +
                  self.loaded_cooked * self.COOKED_DAMAGE)
        self.loaded_raw = 0
        self.loaded_cooked = 0
        return damage

    def clear(self):
        """Clear all loaded fish."""
        self.loaded_raw = 0
        self.loaded_cooked = 0


@dataclass
class Mast:
    """Mast that can be damaged by storms and repaired.

    Repairing masts awards points.
    """
    damaged: bool = False

    # Points for repairing
    REPAIR_POINTS = 40


@dataclass
class Totem:
    """Totem pole that can catch fire during storms.

    Dousing fires awards points.
    """
    on_fire: bool = False

    # Points for dousing
    DOUSE_POINTS = 40


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * t


@dataclass
class Tempoross:
    """The Tempoross boss entity.

    Tempoross has two resource pools:
    - Energy: Depleted by cannon attacks in Phase 1
    - Essence: Depleted by spirit pool fishing in Phase 2

    Both scale based on player count.

    Solo values (from wiki):
    - Energy: ~266 (about 18 cooked fish at 15 damage each)
    - Essence: ~250 (about 25 successful spirit pool attacks)
    """
    # Pool values
    energy: float = 0
    max_energy: float = 0
    essence: float = 0
    max_essence: float = 0

    # Solo base values (wiki: ~266 energy, ~250 essence for solo)
    SOLO_BASE_ENERGY = 266.0
    SOLO_BASE_ESSENCE = 250.0

    # Scaling constants (per player for mass games)
    SOLO_ENERGY_PER_PLAYER = 2600
    MASS_ENERGY_PER_PLAYER = 1800  # At 40 players
    SOLO_ESSENCE_PER_PLAYER = 2500
    MASS_ESSENCE_PER_PLAYER = 1700  # At 40 players

    # Energy regeneration per tick during Phase 2
    ENERGY_REGEN_PER_TICK = 3  # Slower regen for balanced gameplay

    # Thresholds
    ENRAGE_CYCLES = 3  # Number of failed cycles before enrage

    def __post_init__(self):
        # Initialize to max if not set
        if self.energy == 0 and self.max_energy > 0:
            self.energy = self.max_energy
        if self.essence == 0 and self.max_essence > 0:
            self.essence = self.max_essence

    @classmethod
    def for_players(cls, num_players: int) -> "Tempoross":
        """Create a Tempoross scaled for the given number of players.

        Args:
            num_players: Number of players (1-40).

        Returns:
            Tempoross instance with scaled pools.

        For solo play, uses wiki-based values (~266 energy, ~250 essence).
        For mass games, scales with player count.
        """
        num_players = max(1, min(40, num_players))

        if num_players == 1:
            # Solo values from wiki
            return cls(
                energy=cls.SOLO_BASE_ENERGY,
                max_energy=cls.SOLO_BASE_ENERGY,
                essence=cls.SOLO_BASE_ESSENCE,
                max_essence=cls.SOLO_BASE_ESSENCE
            )

        # Linear interpolation based on player count for mass games
        # t=0 for 2 players, t=1 for 40 players
        t = (num_players - 2) / 38 if num_players > 2 else 0

        energy_per_player = lerp(
            cls.SOLO_ENERGY_PER_PLAYER,
            cls.MASS_ENERGY_PER_PLAYER,
            t
        )
        essence_per_player = lerp(
            cls.SOLO_ESSENCE_PER_PLAYER,
            cls.MASS_ESSENCE_PER_PLAYER,
            t
        )

        total_energy = num_players * energy_per_player
        total_essence = num_players * essence_per_player

        return cls(
            energy=total_energy,
            max_energy=total_energy,
            essence=total_essence,
            max_essence=total_essence
        )

    @property
    def energy_percent(self) -> float:
        """Current energy as percentage of max."""
        return (self.energy / self.max_energy * 100) if self.max_energy > 0 else 0

    @property
    def essence_percent(self) -> float:
        """Current essence as percentage of max."""
        return (self.essence / self.max_essence * 100) if self.max_essence > 0 else 0

    @property
    def is_submerged(self) -> bool:
        """Whether Tempoross is submerged (energy depleted)."""
        return self.energy <= 0

    @property
    def is_defeated(self) -> bool:
        """Whether Tempoross is defeated (essence depleted)."""
        return self.essence <= 0

    def deal_energy_damage(self, damage: float) -> float:
        """Deal damage to energy pool.

        Args:
            damage: Amount of damage to deal.

        Returns:
            Actual damage dealt (may be less if energy depleted).
        """
        actual = min(damage, self.energy)
        self.energy -= actual
        return actual

    def deal_essence_damage(self, damage: float) -> float:
        """Deal damage to essence pool.

        Args:
            damage: Amount of damage to deal.

        Returns:
            Actual damage dealt (may be less if essence depleted).
        """
        actual = min(damage, self.essence)
        self.essence -= actual
        return actual

    def regenerate_energy(self, ticks: int = 1) -> float:
        """Regenerate energy during Phase 2.

        Args:
            ticks: Number of ticks to regenerate.

        Returns:
            Amount of energy regenerated.
        """
        regen = min(
            self.ENERGY_REGEN_PER_TICK * ticks,
            self.max_energy - self.energy
        )
        self.energy += regen
        return regen

    def reset_energy(self):
        """Reset energy to full (at start of new cycle)."""
        self.energy = self.max_energy
