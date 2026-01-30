"""Prayer definitions and multipliers for OSRS combat."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class PrayerBonus:
    """Prayer stat multipliers."""
    attack: float = 1.0
    strength: float = 1.0
    defence: float = 1.0
    ranged_attack: float = 1.0
    ranged_strength: float = 1.0
    magic_attack: float = 1.0
    magic_defence: float = 1.0


class Prayer(Enum):
    """Combat prayers with their stat multipliers.

    Values are tuples of (attack_mult, strength_mult, defence_mult,
                          ranged_attack, ranged_strength,
                          magic_attack, magic_defence)
    """
    # No prayer active
    NONE = PrayerBonus()

    # -------------------------------------------------------------------------
    # Melee Prayers
    # -------------------------------------------------------------------------
    # Attack prayers
    CLARITY_OF_THOUGHT = PrayerBonus(attack=1.05)
    IMPROVED_REFLEXES = PrayerBonus(attack=1.10)
    INCREDIBLE_REFLEXES = PrayerBonus(attack=1.15)

    # Strength prayers
    BURST_OF_STRENGTH = PrayerBonus(strength=1.05)
    SUPERHUMAN_STRENGTH = PrayerBonus(strength=1.10)
    ULTIMATE_STRENGTH = PrayerBonus(strength=1.15)

    # Defence prayers
    THICK_SKIN = PrayerBonus(defence=1.05)
    ROCK_SKIN = PrayerBonus(defence=1.10)
    STEEL_SKIN = PrayerBonus(defence=1.15)

    # Combined melee prayers
    CHIVALRY = PrayerBonus(attack=1.15, strength=1.18, defence=1.20)
    PIETY = PrayerBonus(attack=1.20, strength=1.23, defence=1.25)

    # -------------------------------------------------------------------------
    # Ranged Prayers
    # -------------------------------------------------------------------------
    SHARP_EYE = PrayerBonus(ranged_attack=1.05, ranged_strength=1.05)
    HAWK_EYE = PrayerBonus(ranged_attack=1.10, ranged_strength=1.10)
    EAGLE_EYE = PrayerBonus(ranged_attack=1.15, ranged_strength=1.15)
    RIGOUR = PrayerBonus(ranged_attack=1.20, ranged_strength=1.23, defence=1.25)

    # -------------------------------------------------------------------------
    # Magic Prayers
    # -------------------------------------------------------------------------
    MYSTIC_WILL = PrayerBonus(magic_attack=1.05, magic_defence=1.05)
    MYSTIC_LORE = PrayerBonus(magic_attack=1.10, magic_defence=1.10)
    MYSTIC_MIGHT = PrayerBonus(magic_attack=1.15, magic_defence=1.15)
    AUGURY = PrayerBonus(magic_attack=1.25, magic_defence=1.25, defence=1.25)

    def __init__(self, bonus: PrayerBonus):
        self._bonus = bonus

    @property
    def attack_multiplier(self) -> float:
        """Melee attack multiplier."""
        return self._bonus.attack

    @property
    def strength_multiplier(self) -> float:
        """Melee strength multiplier."""
        return self._bonus.strength

    @property
    def defence_multiplier(self) -> float:
        """Defence multiplier."""
        return self._bonus.defence

    @property
    def ranged_attack_multiplier(self) -> float:
        """Ranged attack multiplier."""
        return self._bonus.ranged_attack

    @property
    def ranged_strength_multiplier(self) -> float:
        """Ranged strength multiplier."""
        return self._bonus.ranged_strength

    @property
    def magic_attack_multiplier(self) -> float:
        """Magic attack multiplier."""
        return self._bonus.magic_attack

    @property
    def magic_defence_multiplier(self) -> float:
        """Magic defence multiplier."""
        return self._bonus.magic_defence


# Prayer drain rates (points per minute at base drain)
PRAYER_DRAIN_RATES = {
    Prayer.NONE: 0,
    # Attack prayers
    Prayer.CLARITY_OF_THOUGHT: 3,
    Prayer.IMPROVED_REFLEXES: 6,
    Prayer.INCREDIBLE_REFLEXES: 12,
    # Strength prayers
    Prayer.BURST_OF_STRENGTH: 3,
    Prayer.SUPERHUMAN_STRENGTH: 6,
    Prayer.ULTIMATE_STRENGTH: 12,
    # Defence prayers
    Prayer.THICK_SKIN: 3,
    Prayer.ROCK_SKIN: 6,
    Prayer.STEEL_SKIN: 12,
    # Combined prayers
    Prayer.CHIVALRY: 24,
    Prayer.PIETY: 24,
    # Ranged prayers
    Prayer.SHARP_EYE: 3,
    Prayer.HAWK_EYE: 6,
    Prayer.EAGLE_EYE: 12,
    Prayer.RIGOUR: 24,
    # Magic prayers
    Prayer.MYSTIC_WILL: 3,
    Prayer.MYSTIC_LORE: 6,
    Prayer.MYSTIC_MIGHT: 12,
    Prayer.AUGURY: 24,
}


def get_prayer(name: str) -> Optional[Prayer]:
    """Get a prayer by name.

    Args:
        name: Prayer name (case-insensitive, spaces/underscores interchangeable).

    Returns:
        The Prayer enum value, or None if not found.
    """
    normalized = name.upper().replace(" ", "_").replace("-", "_")
    try:
        return Prayer[normalized]
    except KeyError:
        return None


def list_prayers() -> list[str]:
    """List all available prayer names."""
    return [p.name.lower() for p in Prayer if p != Prayer.NONE]


# Convenience aliases for common prayers
PIETY = Prayer.PIETY
RIGOUR = Prayer.RIGOUR
AUGURY = Prayer.AUGURY
EAGLE_EYE = Prayer.EAGLE_EYE
