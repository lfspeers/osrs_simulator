"""Combat spells for magic DPS calculations."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict
import math


class Spellbook(Enum):
    """Spellbook types."""
    STANDARD = "standard"
    ANCIENTS = "ancients"
    ARCEUUS = "arceuus"


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


# Standard Spellbook combat spells
STANDARD_SPELLS: Dict[str, Spell] = {
    # Strike spells
    "wind_strike": Spell("Wind Strike", Spellbook.STANDARD, 1, 2),
    "water_strike": Spell("Water Strike", Spellbook.STANDARD, 5, 4),
    "earth_strike": Spell("Earth Strike", Spellbook.STANDARD, 9, 6),
    "fire_strike": Spell("Fire Strike", Spellbook.STANDARD, 13, 8),

    # Bolt spells
    "wind_bolt": Spell("Wind Bolt", Spellbook.STANDARD, 17, 9),
    "water_bolt": Spell("Water Bolt", Spellbook.STANDARD, 23, 10),
    "earth_bolt": Spell("Earth Bolt", Spellbook.STANDARD, 29, 11),
    "fire_bolt": Spell("Fire Bolt", Spellbook.STANDARD, 35, 12),

    # Blast spells
    "wind_blast": Spell("Wind Blast", Spellbook.STANDARD, 41, 13),
    "water_blast": Spell("Water Blast", Spellbook.STANDARD, 47, 14),
    "earth_blast": Spell("Earth Blast", Spellbook.STANDARD, 53, 15),
    "fire_blast": Spell("Fire Blast", Spellbook.STANDARD, 59, 16),

    # Wave spells
    "wind_wave": Spell("Wind Wave", Spellbook.STANDARD, 62, 17),
    "water_wave": Spell("Water Wave", Spellbook.STANDARD, 65, 18),
    "earth_wave": Spell("Earth Wave", Spellbook.STANDARD, 70, 19),
    "fire_wave": Spell("Fire Wave", Spellbook.STANDARD, 75, 20),

    # Surge spells
    "wind_surge": Spell("Wind Surge", Spellbook.STANDARD, 81, 21),
    "water_surge": Spell("Water Surge", Spellbook.STANDARD, 85, 22),
    "earth_surge": Spell("Earth Surge", Spellbook.STANDARD, 90, 23),
    "fire_surge": Spell("Fire Surge", Spellbook.STANDARD, 95, 24),

    # Special standard spells
    "iban_blast": Spell("Iban Blast", Spellbook.STANDARD, 50, 25),
    "magic_dart": Spell("Magic Dart", Spellbook.STANDARD, 50, 10),  # Base, scales with magic level
    "crumble_undead": Spell("Crumble Undead", Spellbook.STANDARD, 39, 15),
    "flames_of_zamorak": Spell("Flames of Zamorak", Spellbook.STANDARD, 60, 20),
    "claws_of_guthix": Spell("Claws of Guthix", Spellbook.STANDARD, 60, 20),
    "saradomin_strike": Spell("Saradomin Strike", Spellbook.STANDARD, 60, 20),
}

# Ancient Magicks combat spells
ANCIENT_SPELLS: Dict[str, Spell] = {
    # Rush spells (single target)
    "smoke_rush": Spell("Smoke Rush", Spellbook.ANCIENTS, 50, 13),
    "shadow_rush": Spell("Shadow Rush", Spellbook.ANCIENTS, 52, 14),
    "blood_rush": Spell("Blood Rush", Spellbook.ANCIENTS, 56, 15),
    "ice_rush": Spell("Ice Rush", Spellbook.ANCIENTS, 58, 16),

    # Burst spells (multi-target)
    "smoke_burst": Spell("Smoke Burst", Spellbook.ANCIENTS, 62, 17, is_multi_target=True),
    "shadow_burst": Spell("Shadow Burst", Spellbook.ANCIENTS, 64, 18, is_multi_target=True),
    "blood_burst": Spell("Blood Burst", Spellbook.ANCIENTS, 68, 21, is_multi_target=True),
    "ice_burst": Spell("Ice Burst", Spellbook.ANCIENTS, 70, 22, is_multi_target=True),

    # Blitz spells (single target, stronger)
    "smoke_blitz": Spell("Smoke Blitz", Spellbook.ANCIENTS, 74, 23),
    "shadow_blitz": Spell("Shadow Blitz", Spellbook.ANCIENTS, 76, 24),
    "blood_blitz": Spell("Blood Blitz", Spellbook.ANCIENTS, 80, 25),
    "ice_blitz": Spell("Ice Blitz", Spellbook.ANCIENTS, 82, 26),

    # Barrage spells (multi-target, strongest)
    "smoke_barrage": Spell("Smoke Barrage", Spellbook.ANCIENTS, 86, 27, is_multi_target=True),
    "shadow_barrage": Spell("Shadow Barrage", Spellbook.ANCIENTS, 88, 28, is_multi_target=True),
    "blood_barrage": Spell("Blood Barrage", Spellbook.ANCIENTS, 92, 29, is_multi_target=True),
    "ice_barrage": Spell("Ice Barrage", Spellbook.ANCIENTS, 94, 30, is_multi_target=True),
}

# Arceuus Spellbook combat spells
ARCEUUS_SPELLS: Dict[str, Spell] = {
    "ghostly_grasp": Spell("Ghostly Grasp", Spellbook.ARCEUUS, 35, 12),
    "skeletal_grasp": Spell("Skeletal Grasp", Spellbook.ARCEUUS, 56, 17),
    "undead_grasp": Spell("Undead Grasp", Spellbook.ARCEUUS, 79, 24),
}

# Combined spell dictionary
SPELLS: Dict[str, Spell] = {**STANDARD_SPELLS, **ANCIENT_SPELLS, **ARCEUUS_SPELLS}


def get_spell(name: str) -> Optional[Spell]:
    """Get a spell by name.

    Args:
        name: The spell name (case-insensitive, spaces/underscores OK).

    Returns:
        Spell object, or None if not found.
    """
    key = name.lower().replace(" ", "_").replace("'", "")
    return SPELLS.get(key)


def list_spells(spellbook: Optional[Spellbook] = None) -> List[str]:
    """List all spell names.

    Args:
        spellbook: Optional filter by spellbook.

    Returns:
        Sorted list of spell key names.
    """
    if spellbook is None:
        return sorted(SPELLS.keys())
    elif spellbook == Spellbook.STANDARD:
        return sorted(STANDARD_SPELLS.keys())
    elif spellbook == Spellbook.ANCIENTS:
        return sorted(ANCIENT_SPELLS.keys())
    elif spellbook == Spellbook.ARCEUUS:
        return sorted(ARCEUUS_SPELLS.keys())
    return []


def list_by_level(max_level: int) -> List[str]:
    """List spells available at a given magic level.

    Args:
        max_level: Maximum magic level.

    Returns:
        Sorted list of spell key names available at that level.
    """
    return sorted([
        k for k, v in SPELLS.items()
        if v.magic_level <= max_level
    ])


def get_strongest_spell(magic_level: int, spellbook: Optional[Spellbook] = None) -> Optional[Spell]:
    """Get the strongest spell available at a given level.

    Args:
        magic_level: Player's magic level.
        spellbook: Optional filter by spellbook.

    Returns:
        The highest damage spell available, or None.
    """
    if spellbook is None:
        source = SPELLS
    elif spellbook == Spellbook.STANDARD:
        source = STANDARD_SPELLS
    elif spellbook == Spellbook.ANCIENTS:
        source = ANCIENT_SPELLS
    elif spellbook == Spellbook.ARCEUUS:
        source = ARCEUUS_SPELLS
    else:
        return None

    available = [
        spell for spell in source.values()
        if spell.magic_level <= magic_level
    ]

    if not available:
        return None

    return max(available, key=lambda s: s.base_max_hit)
