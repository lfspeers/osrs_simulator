"""Combat spells for magic DPS calculations.

This module provides spell definitions and utilities for magic combat calculations.
For the full spell database, see data_loader.spell_loader.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict
import math


class Spellbook(Enum):
    """Spellbook types."""
    STANDARD = "standard"
    ANCIENTS = "ancients"


@dataclass
class Spell:
    """A combat spell with its properties."""
    name: str
    spellbook: Spellbook
    magic_level: int
    base_max_hit: int
    is_multi_target: bool = False

    def get_max_hit(self, magic_damage_bonus: float = 0.0) -> int:
        """Calculate max hit with magic damage bonus.

        Args:
            magic_damage_bonus: Decimal magic damage bonus (e.g., 0.15 for 15%).

        Returns:
            The maximum hit with the bonus applied.
        """
        return math.floor(self.base_max_hit * (1 + magic_damage_bonus))


# Import the full spell database from data_loader
# This allows the combat module to use spells without requiring data_loader as a hard dependency
try:
    from data_loader.spell_loader import (
        SPELLS,
        STANDARD_SPELLS,
        ANCIENT_SPELLS,
        get_spell,
        list_spells,
        list_by_level,
        get_strongest_spell,
    )
except ImportError:
    # Fallback to basic spell definitions if data_loader is not available
    STANDARD_SPELLS: Dict[str, Spell] = {
        "fire_surge": Spell("Fire Surge", Spellbook.STANDARD, 95, 24),
        "fire_wave": Spell("Fire Wave", Spellbook.STANDARD, 75, 20),
        "fire_blast": Spell("Fire Blast", Spellbook.STANDARD, 59, 16),
        "fire_bolt": Spell("Fire Bolt", Spellbook.STANDARD, 35, 12),
        "fire_strike": Spell("Fire Strike", Spellbook.STANDARD, 13, 8),
        "iban_blast": Spell("Iban Blast", Spellbook.STANDARD, 50, 25),
        "magic_dart": Spell("Magic Dart", Spellbook.STANDARD, 50, 10),
        "crumble_undead": Spell("Crumble Undead", Spellbook.STANDARD, 39, 15),
    }

    ANCIENT_SPELLS: Dict[str, Spell] = {
        "ice_barrage": Spell("Ice Barrage", Spellbook.ANCIENTS, 94, 30, is_multi_target=True),
        "ice_burst": Spell("Ice Burst", Spellbook.ANCIENTS, 70, 22, is_multi_target=True),
        "ice_blitz": Spell("Ice Blitz", Spellbook.ANCIENTS, 82, 26),
        "ice_rush": Spell("Ice Rush", Spellbook.ANCIENTS, 58, 16),
        "blood_barrage": Spell("Blood Barrage", Spellbook.ANCIENTS, 92, 29, is_multi_target=True),
        "blood_burst": Spell("Blood Burst", Spellbook.ANCIENTS, 68, 21, is_multi_target=True),
        "shadow_barrage": Spell("Shadow Barrage", Spellbook.ANCIENTS, 88, 28, is_multi_target=True),
        "smoke_barrage": Spell("Smoke Barrage", Spellbook.ANCIENTS, 86, 27, is_multi_target=True),
    }

    SPELLS: Dict[str, Spell] = {**STANDARD_SPELLS, **ANCIENT_SPELLS}

    def get_spell(name: str) -> Optional[Spell]:
        """Get a spell by name."""
        key = name.lower().replace(" ", "_").replace("'", "")
        return SPELLS.get(key)

    def list_spells(spellbook: Optional[Spellbook] = None) -> List[str]:
        """List all spell names."""
        if spellbook is None:
            return sorted(SPELLS.keys())
        elif spellbook == Spellbook.STANDARD:
            return sorted(STANDARD_SPELLS.keys())
        elif spellbook == Spellbook.ANCIENTS:
            return sorted(ANCIENT_SPELLS.keys())
        return []

    def list_by_level(max_level: int) -> List[str]:
        """List spells available at a given magic level."""
        return sorted([k for k, v in SPELLS.items() if v.magic_level <= max_level])

    def get_strongest_spell(magic_level: int, spellbook: Optional[Spellbook] = None) -> Optional[Spell]:
        """Get the strongest spell available at a given level."""
        if spellbook is None:
            source = SPELLS
        elif spellbook == Spellbook.STANDARD:
            source = STANDARD_SPELLS
        elif spellbook == Spellbook.ANCIENTS:
            source = ANCIENT_SPELLS
        else:
            return None
        available = [s for s in source.values() if s.magic_level <= magic_level]
        if not available:
            return None
        return max(available, key=lambda s: s.base_max_hit)
