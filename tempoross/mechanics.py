"""Phase logic, attacks, and point system for Tempoross."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable
import random

from .entities import Tempoross, Cannon, FishingSpot, SpiritPool, Mast, Totem


class Phase(Enum):
    """Game phases for Tempoross fight."""
    PHASE_1 = auto()  # Surfaced - fish and attack
    PHASE_2 = auto()  # Submerged - drain essence
    VICTORY = auto()  # Essence depleted
    DEFEAT = auto()   # Failed 3 cycles or everyone dead


class StormIntensity(Enum):
    """Storm intensity levels affecting attack frequency."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @property
    def wave_chance(self) -> float:
        """Chance per tick of a wave attack."""
        return {
            StormIntensity.LOW: 0.01,
            StormIntensity.MEDIUM: 0.02,
            StormIntensity.HIGH: 0.03,
        }[self]

    @property
    def fire_chance(self) -> float:
        """Chance per tick of a fire starting."""
        return {
            StormIntensity.LOW: 0.005,
            StormIntensity.MEDIUM: 0.01,
            StormIntensity.HIGH: 0.02,
        }[self]

    @property
    def damage_chance(self) -> float:
        """Chance per tick of mast damage."""
        return {
            StormIntensity.LOW: 0.005,
            StormIntensity.MEDIUM: 0.01,
            StormIntensity.HIGH: 0.015,
        }[self]


class PointAction(Enum):
    """Actions that award points in Tempoross."""
    FISH = ("fishing", 5)
    COOK = ("cooking", 10)
    DEPOSIT_RAW = ("deposit_raw", 20)
    DEPOSIT_COOKED = ("deposit_cooked", 65)
    DEPOSIT_CRYSTALLISED = ("deposit_crystallised", 20)
    REPAIR = ("repair", 40)
    DOUSE_FIRE = ("douse_fire", 40)
    SURVIVE_WAVE = ("survive_wave", 10)
    SPIRIT_HARPOON = ("spirit_harpoon", 55)

    def __init__(self, action_name: str, points: int):
        self.action_name = action_name
        self.point_value = points


@dataclass
class PointTracker:
    """Tracks points earned during a Tempoross game."""
    fish_caught: int = 0
    fish_cooked: int = 0
    raw_deposited: int = 0
    cooked_deposited: int = 0
    crystallised_deposited: int = 0
    repairs: int = 0
    fires_doused: int = 0
    waves_survived: int = 0
    spirit_harpoons: int = 0

    def add(self, action: PointAction, count: int = 1):
        """Add points for an action."""
        if action == PointAction.FISH:
            self.fish_caught += count
        elif action == PointAction.COOK:
            self.fish_cooked += count
        elif action == PointAction.DEPOSIT_RAW:
            self.raw_deposited += count
        elif action == PointAction.DEPOSIT_COOKED:
            self.cooked_deposited += count
        elif action == PointAction.DEPOSIT_CRYSTALLISED:
            self.crystallised_deposited += count
        elif action == PointAction.REPAIR:
            self.repairs += count
        elif action == PointAction.DOUSE_FIRE:
            self.fires_doused += count
        elif action == PointAction.SURVIVE_WAVE:
            self.waves_survived += count
        elif action == PointAction.SPIRIT_HARPOON:
            self.spirit_harpoons += count

    @property
    def total(self) -> int:
        """Calculate total points."""
        return (
            self.fish_caught * PointAction.FISH.point_value +
            self.fish_cooked * PointAction.COOK.point_value +
            self.raw_deposited * PointAction.DEPOSIT_RAW.point_value +
            self.cooked_deposited * PointAction.DEPOSIT_COOKED.point_value +
            self.crystallised_deposited * PointAction.DEPOSIT_CRYSTALLISED.point_value +
            self.repairs * PointAction.REPAIR.point_value +
            self.fires_doused * PointAction.DOUSE_FIRE.point_value +
            self.waves_survived * PointAction.SURVIVE_WAVE.point_value +
            self.spirit_harpoons * PointAction.SPIRIT_HARPOON.point_value
        )

    def calculate_permits(self) -> int:
        """Calculate reward permits from points.

        Formula: 1 + floor((points - 2000) / 700) if points >= 2000
        """
        points = self.total
        if points < 2000:
            return 0
        return 1 + (points - 2000) // 700


@dataclass
class XPTracker:
    """Tracks XP earned during a Tempoross game."""
    fishing_xp: float = 0.0
    cooking_xp: float = 0.0

    # Cooking XP per fish
    COOKING_XP_PER_FISH = 10.0

    def add_fishing_xp(self, level: int, count: int = 1):
        """Add fishing XP based on player level.

        XP formula for levels 35-99:
        xp = floor((450 + (1000-450) * (level-35) / (99-35))) / 100

        This gives approximately:
        - Level 35: 4.5 XP
        - Level 99: 10.0 XP

        Note: Wiki says 65 base XP at level 35, scaling to 142 at level 99
        Using wiki values instead.
        """
        # Wiki-based XP values (interpolated)
        base_xp = 65.0
        max_xp = 142.0
        level = max(35, min(99, level))

        xp = base_xp + (max_xp - base_xp) * (level - 35) / (99 - 35)
        self.fishing_xp += xp * count

    def add_cooking_xp(self, count: int = 1):
        """Add cooking XP for cooking fish."""
        self.cooking_xp += self.COOKING_XP_PER_FISH * count


@dataclass
class TemporossGame:
    """Game state manager for a Tempoross encounter.

    Tracks phase, boss state, hazards, and player actions.
    """
    # Boss
    boss: Tempoross = field(default_factory=lambda: Tempoross.for_players(1))

    # Game objects
    cannons: list[Cannon] = field(default_factory=lambda: [Cannon(), Cannon()])
    fishing_spots: list[FishingSpot] = field(default_factory=list)
    spirit_pools: list[SpiritPool] = field(default_factory=list)
    masts: list[Mast] = field(default_factory=lambda: [Mast(), Mast()])
    totems: list[Totem] = field(default_factory=lambda: [Totem(), Totem(), Totem(), Totem()])

    # Tracking
    points: PointTracker = field(default_factory=PointTracker)
    xp: XPTracker = field(default_factory=XPTracker)

    # State
    phase: Phase = Phase.PHASE_1
    cycles_failed: int = 0
    storm_intensity: StormIntensity = StormIntensity.LOW
    current_tick: int = 0
    num_players: int = 1

    # Random number generator for deterministic simulation
    rng: random.Random = field(default_factory=random.Random)

    @classmethod
    def create(
        cls,
        num_players: int = 1,
        seed: Optional[int] = None
    ) -> "TemporossGame":
        """Create a new game instance.

        Args:
            num_players: Number of players in the game.
            seed: Optional random seed for deterministic simulation.
        """
        rng = random.Random(seed)
        boss = Tempoross.for_players(num_players)

        return cls(
            boss=boss,
            num_players=num_players,
            rng=rng,
            fishing_spots=[FishingSpot(), FishingSpot()],
            spirit_pools=[SpiritPool(), SpiritPool()],
        )

    def tick(self):
        """Process one game tick."""
        self.current_tick += 1

        if self.phase == Phase.PHASE_1:
            self._tick_phase_1()
        elif self.phase == Phase.PHASE_2:
            self._tick_phase_2()

    def _tick_phase_1(self):
        """Process Phase 1 (surfaced) tick."""
        # Check for phase transition
        if self.boss.is_submerged:
            self.phase = Phase.PHASE_2
            return

        # Storm attacks based on intensity
        self._process_storm_attacks()

    def _tick_phase_2(self):
        """Process Phase 2 (submerged) tick."""
        # Check for victory
        if self.boss.is_defeated:
            self.phase = Phase.VICTORY
            return

        # Regenerate energy
        self.boss.regenerate_energy()

        # Check for failed cycle (energy full)
        if self.boss.energy >= self.boss.max_energy:
            self.cycles_failed += 1
            if self.cycles_failed >= self.boss.ENRAGE_CYCLES:
                self.phase = Phase.DEFEAT
            else:
                # Start new cycle
                self.phase = Phase.PHASE_1
                self._increase_storm_intensity()

    def _process_storm_attacks(self):
        """Process random storm attacks."""
        # Wave attack
        if self.rng.random() < self.storm_intensity.wave_chance:
            pass  # Waves are handled by player survival checks

        # Fire on totems
        for totem in self.totems:
            if not totem.on_fire and self.rng.random() < self.storm_intensity.fire_chance:
                totem.on_fire = True

        # Mast damage
        for mast in self.masts:
            if not mast.damaged and self.rng.random() < self.storm_intensity.damage_chance:
                mast.damaged = True

    def _increase_storm_intensity(self):
        """Increase storm intensity after failed cycle."""
        if self.storm_intensity == StormIntensity.LOW:
            self.storm_intensity = StormIntensity.MEDIUM
        elif self.storm_intensity == StormIntensity.MEDIUM:
            self.storm_intensity = StormIntensity.HIGH

    def fire_cannons(self) -> int:
        """Fire all loaded cannons at Tempoross.

        Returns:
            Total damage dealt.
        """
        total_damage = 0
        for cannon in self.cannons:
            damage = cannon.fire()
            self.boss.deal_energy_damage(damage)
            total_damage += damage
        return total_damage

    def load_cannon(
        self,
        cannon_index: int,
        raw: int = 0,
        cooked: int = 0
    ) -> tuple[int, int]:
        """Load fish into a cannon.

        Args:
            cannon_index: Which cannon to load (0 or 1).
            raw: Number of raw fish.
            cooked: Number of cooked fish.

        Returns:
            Tuple of (raw_loaded, cooked_loaded).
        """
        if cannon_index < 0 or cannon_index >= len(self.cannons):
            return 0, 0

        raw_loaded, cooked_loaded = self.cannons[cannon_index].load(raw, cooked)

        # Award points for depositing
        if raw_loaded > 0:
            self.points.add(PointAction.DEPOSIT_RAW, raw_loaded)
        if cooked_loaded > 0:
            self.points.add(PointAction.DEPOSIT_COOKED, cooked_loaded)

        return raw_loaded, cooked_loaded

    def repair_mast(self, mast_index: int) -> bool:
        """Repair a damaged mast.

        Returns:
            True if repair was successful.
        """
        if mast_index < 0 or mast_index >= len(self.masts):
            return False

        mast = self.masts[mast_index]
        if not mast.damaged:
            return False

        mast.damaged = False
        self.points.add(PointAction.REPAIR)
        return True

    def douse_fire(self, totem_index: int) -> bool:
        """Douse a fire on a totem.

        Returns:
            True if dousing was successful.
        """
        if totem_index < 0 or totem_index >= len(self.totems):
            return False

        totem = self.totems[totem_index]
        if not totem.on_fire:
            return False

        totem.on_fire = False
        self.points.add(PointAction.DOUSE_FIRE)
        return True

    def harpoon_spirit_pool(self, damage: float = 10.0) -> float:
        """Attack a spirit pool with harpoon during Phase 2.

        Args:
            damage: Amount of essence damage to deal.

        Returns:
            Actual damage dealt.
        """
        if self.phase != Phase.PHASE_2:
            return 0.0

        actual = self.boss.deal_essence_damage(damage)
        if actual > 0:
            self.points.add(PointAction.SPIRIT_HARPOON)
        return actual

    def get_hazard_count(self) -> tuple[int, int]:
        """Get count of active hazards.

        Returns:
            Tuple of (damaged_masts, fires).
        """
        damaged = sum(1 for m in self.masts if m.damaged)
        fires = sum(1 for t in self.totems if t.on_fire)
        return damaged, fires

    @property
    def is_game_over(self) -> bool:
        """Check if game has ended."""
        return self.phase in (Phase.VICTORY, Phase.DEFEAT)

    @property
    def is_victory(self) -> bool:
        """Check if game ended in victory."""
        return self.phase == Phase.VICTORY
