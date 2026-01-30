"""Core DPS calculation formulas for OSRS combat.

All formulas are based on the OSRS Wiki DPS calculator mechanics.
See: https://oldschool.runescape.wiki/w/Damage_per_second/Melee
"""

import math
from dataclasses import dataclass
from typing import Tuple, Optional


def effective_level(
    base_level: int,
    boost: int = 0,
    prayer_multiplier: float = 1.0,
    style_bonus: int = 0,
    void_multiplier: float = 1.0
) -> int:
    """Calculate the effective level for attack or strength.

    Args:
        base_level: Base skill level (1-99).
        boost: Level boost from potions (e.g., +19 from super combat).
        prayer_multiplier: Multiplier from active prayer (e.g., 1.23 for Piety strength).
        style_bonus: Bonus from attack style (+0 to +3).
        void_multiplier: Multiplier from void equipment (1.0, 1.1, or 1.125).

    Returns:
        The effective level after all modifiers.

    Formula: floor((base + boost) * prayer_mult) + style_bonus + 8, then * void_mult
    """
    # Apply prayer multiplier first
    level_with_prayer = math.floor((base_level + boost) * prayer_multiplier)

    # Add style bonus and the constant +8
    level_with_style = level_with_prayer + style_bonus + 8

    # Apply void multiplier last
    return math.floor(level_with_style * void_multiplier)


def max_hit_melee(
    effective_strength: int,
    strength_bonus: int,
    gear_multiplier: float = 1.0
) -> int:
    """Calculate maximum melee hit.

    Args:
        effective_strength: Effective strength level.
        strength_bonus: Strength bonus from equipment.
        gear_multiplier: Multiplier from gear effects (e.g., slayer helm 7/6).

    Returns:
        Maximum hit value.

    Formula: floor((Eff_Str * (Str_Bonus + 64) + 320) / 640) * gear_mult
    """
    base_max = math.floor((effective_strength * (strength_bonus + 64) + 320) / 640)
    return math.floor(base_max * gear_multiplier)


def max_hit_ranged(
    effective_ranged_strength: int,
    ranged_strength_bonus: int,
    gear_multiplier: float = 1.0
) -> int:
    """Calculate maximum ranged hit.

    Uses the same formula as melee.

    Args:
        effective_ranged_strength: Effective ranged level (for strength).
        ranged_strength_bonus: Ranged strength bonus from equipment.
        gear_multiplier: Multiplier from gear effects.

    Returns:
        Maximum hit value.
    """
    base_max = math.floor(
        (effective_ranged_strength * (ranged_strength_bonus + 64) + 320) / 640
    )
    return math.floor(base_max * gear_multiplier)


def max_hit_magic(
    base_max: int,
    magic_damage_bonus: float = 0.0,
    gear_multiplier: float = 1.0
) -> int:
    """Calculate maximum magic hit.

    Magic max hit is typically determined by the spell/staff used,
    then modified by magic damage bonus and gear effects.

    Args:
        base_max: Base max hit from spell/staff.
        magic_damage_bonus: Magic damage bonus as a decimal (e.g., 0.15 for 15%).
        gear_multiplier: Multiplier from gear effects.

    Returns:
        Maximum hit value.
    """
    with_bonus = math.floor(base_max * (1 + magic_damage_bonus))
    return math.floor(with_bonus * gear_multiplier)


def attack_roll(
    effective_attack: int,
    attack_bonus: int,
    gear_multiplier: float = 1.0
) -> int:
    """Calculate the attack roll.

    Args:
        effective_attack: Effective attack level.
        attack_bonus: Attack bonus from equipment for the relevant style.
        gear_multiplier: Multiplier from gear effects.

    Returns:
        Attack roll value.

    Formula: Eff_Atk * (Atk_Bonus + 64) * gear_mult
    """
    base_roll = effective_attack * (attack_bonus + 64)
    return math.floor(base_roll * gear_multiplier)


def defence_roll_npc(
    defence_level: int,
    style_defence_bonus: int,
    magic_level: int = 0,
    is_magic_attack: bool = False
) -> int:
    """Calculate an NPC's defence roll.

    Args:
        defence_level: NPC's defence level.
        style_defence_bonus: NPC's defence bonus against the attack style.
        magic_level: NPC's magic level (used for magic defence).
        is_magic_attack: Whether the incoming attack is magic.

    Returns:
        Defence roll value.

    Formula: (Def_Level + 9) * (Style_Def_Bonus + 64)
    For magic: uses NPC's magic level instead of defence level
    """
    if is_magic_attack:
        # Magic defence uses magic level
        return (magic_level + 9) * (style_defence_bonus + 64)
    else:
        return (defence_level + 9) * (style_defence_bonus + 64)


def hit_chance(attack_roll: int, defence_roll: int) -> float:
    """Calculate the probability of hitting.

    Args:
        attack_roll: The attacker's attack roll.
        defence_roll: The defender's defence roll.

    Returns:
        Hit probability as a float between 0 and 1.

    Formula:
        if attack_roll > defence_roll:
            1 - (defence_roll + 2) / (2 * (attack_roll + 1))
        else:
            attack_roll / (2 * (defence_roll + 1))
    """
    if attack_roll > defence_roll:
        return 1 - (defence_roll + 2) / (2 * (attack_roll + 1))
    else:
        return attack_roll / (2 * (defence_roll + 1))


def calculate_dps(
    hit_chance: float,
    max_hit: int,
    attack_speed_ticks: int
) -> float:
    """Calculate damage per second.

    Args:
        hit_chance: Probability of hitting (0-1).
        max_hit: Maximum hit value.
        attack_speed_ticks: Attack speed in game ticks.

    Returns:
        Damage per second.

    Formula: hit_chance * (max_hit + 1) / 2 / attack_speed_seconds
    Where attack_speed_seconds = attack_speed_ticks * 0.6
    """
    if attack_speed_ticks <= 0:
        return 0.0

    # Average damage when hitting: (0 + max_hit) / 2 = max_hit / 2
    # But since we can hit 0 to max_hit inclusive, it's (max_hit + 1) / 2
    # Actually, average hit is max_hit / 2 since damage is uniform [0, max_hit]
    # The +1 comes from the inclusive range
    average_damage = max_hit / 2.0

    # Damage per attack = hit_chance * average_damage
    damage_per_attack = hit_chance * average_damage

    # Convert ticks to seconds (1 tick = 0.6 seconds)
    attack_speed_seconds = attack_speed_ticks * 0.6

    return damage_per_attack / attack_speed_seconds


def calculate_kill_time(
    dps: float,
    hitpoints: int
) -> float:
    """Calculate average time to kill a target.

    Args:
        dps: Damage per second.
        hitpoints: Target's hitpoints.

    Returns:
        Average kill time in seconds.
    """
    if dps <= 0:
        return float('inf')
    return hitpoints / dps


def calculate_kills_per_hour(
    kill_time_seconds: float,
    overhead_seconds: float = 0.0
) -> float:
    """Calculate kills per hour.

    Args:
        kill_time_seconds: Average time to kill one target.
        overhead_seconds: Additional time per kill (banking, walking, etc.).

    Returns:
        Expected kills per hour.
    """
    total_time = kill_time_seconds + overhead_seconds
    if total_time <= 0:
        return 0.0
    return 3600 / total_time


def osmumtens_fang_hit_chance(attack_roll: int, defence_roll: int) -> float:
    """Calculate hit chance for Osmumten's Fang.

    The Fang has a special accuracy mechanic that rolls accuracy twice.

    Args:
        attack_roll: The attacker's attack roll.
        defence_roll: The defender's defence roll.

    Returns:
        Hit probability as a float between 0 and 1.
    """
    # Normal hit chance
    base_chance = hit_chance(attack_roll, defence_roll)

    # Fang rolls twice: hits if either roll succeeds
    # P(hit) = 1 - P(miss twice) = 1 - (1 - base)^2
    miss_chance = 1 - base_chance
    return 1 - (miss_chance * miss_chance)


def osmumtens_fang_max_hit(base_max_hit: int) -> Tuple[int, int]:
    """Calculate Osmumten's Fang min and max hit.

    The Fang has a special damage distribution:
    - Minimum hit is 15% of max hit
    - Maximum hit is 85% of max hit

    Args:
        base_max_hit: The calculated base max hit.

    Returns:
        Tuple of (min_hit, max_hit) for the Fang.
    """
    min_hit = math.floor(base_max_hit * 0.15)
    max_hit = math.floor(base_max_hit * 0.85)
    return (min_hit, max_hit)


def osmumtens_fang_average_damage(min_hit: int, max_hit: int) -> float:
    """Calculate average damage for Osmumten's Fang.

    Since damage is uniform between min and max:
    average = (min + max) / 2

    Args:
        min_hit: Minimum hit value.
        max_hit: Maximum hit value.

    Returns:
        Average damage per successful hit.
    """
    return (min_hit + max_hit) / 2.0


def scythe_hit_chance_and_damage(
    attack_roll: int,
    defence_roll: int,
    max_hit: int,
    target_size: int = 1
) -> Tuple[float, float]:
    """Calculate Scythe of Vitur expected damage.

    The Scythe hits up to 3 times per attack:
    - Hit 1: 100% damage
    - Hit 2: 50% damage (only on 2x2+ targets)
    - Hit 3: 25% damage (only on 3x3+ targets)

    Args:
        attack_roll: The attacker's attack roll.
        defence_roll: The defender's defence roll.
        max_hit: Maximum hit for the first hit.
        target_size: Target size in tiles (1, 2, or 3+).

    Returns:
        Tuple of (hit_chance, average_damage_per_attack).
    """
    base_hit_chance = hit_chance(attack_roll, defence_roll)

    # Each hit has independent accuracy
    avg_damage = base_hit_chance * (max_hit / 2.0)

    if target_size >= 2:
        # Second hit does 50% damage
        second_max = math.floor(max_hit * 0.5)
        avg_damage += base_hit_chance * (second_max / 2.0)

    if target_size >= 3:
        # Third hit does 25% damage
        third_max = math.floor(max_hit * 0.25)
        avg_damage += base_hit_chance * (third_max / 2.0)

    return (base_hit_chance, avg_damage)


@dataclass
class FormulaBreakdown:
    """Stores intermediate values for formula display.

    This allows showing the user exactly how the DPS was calculated,
    with all values substituted into the formulas.
    """
    # Combat style
    combat_style: str  # "melee", "ranged", or "magic"

    # Effective level components
    base_level: int
    boost: int
    prayer_mult: float
    style_bonus: int
    void_mult: float
    effective_attack: int
    effective_strength: int

    # Max hit components
    strength_bonus: int
    gear_mult_damage: float
    max_hit: int

    # Attack roll components
    attack_bonus: int
    gear_mult_accuracy: float
    attack_roll: int

    # Defence roll components
    defence_level: int
    defence_bonus: int
    defence_roll: int

    # Final calculations
    hit_chance: float
    attack_speed_ticks: int
    dps: float

    # Optional: for magic
    base_magic_max: int = 0
    magic_damage_bonus: float = 0.0


def format_formula_breakdown(fb: FormulaBreakdown) -> str:
    """Format the formula breakdown for display.

    Args:
        fb: FormulaBreakdown with all intermediate values.

    Returns:
        Multi-line string showing the calculation steps.
    """
    lines = [
        "=== DPS Formula Breakdown ===",
        "",
    ]

    # Effective level calculation
    if fb.combat_style == "melee":
        lines.extend([
            "1. EFFECTIVE ATTACK LEVEL:",
            f"   = floor((base + boost) * prayer) + style + 8",
            f"   = floor(({fb.base_level} + {fb.boost}) * {fb.prayer_mult:.3f}) + {fb.style_bonus} + 8",
            f"   = {fb.effective_attack}",
            "",
            "2. EFFECTIVE STRENGTH LEVEL:",
            f"   = floor((base + boost) * prayer) + style + 8",
            f"   = {fb.effective_strength}",
            "",
        ])
    elif fb.combat_style == "ranged":
        lines.extend([
            "1. EFFECTIVE RANGED LEVEL:",
            f"   = floor((base + boost) * prayer) + style + 8",
            f"   = floor(({fb.base_level} + {fb.boost}) * {fb.prayer_mult:.3f}) + {fb.style_bonus} + 8",
            f"   = {fb.effective_attack} (for accuracy)",
            f"   = {fb.effective_strength} (for damage)",
            "",
        ])
    else:  # magic
        lines.extend([
            "1. EFFECTIVE MAGIC LEVEL:",
            f"   = floor((base + boost) * prayer) + style + 8",
            f"   = floor(({fb.base_level} + {fb.boost}) * {fb.prayer_mult:.3f}) + {fb.style_bonus} + 8",
            f"   = {fb.effective_attack}",
            "",
        ])

    # Max hit calculation
    if fb.combat_style in ("melee", "ranged"):
        style_name = "MELEE" if fb.combat_style == "melee" else "RANGED"
        str_name = "Str" if fb.combat_style == "melee" else "Ranged Str"
        lines.extend([
            f"{'3' if fb.combat_style == 'melee' else '2'}. MAX HIT ({style_name}):",
            f"   = floor((Eff_{str_name} * ({str_name}_Bonus + 64) + 320) / 640) * gear_mult",
            f"   = floor(({fb.effective_strength} * ({fb.strength_bonus} + 64) + 320) / 640) * {fb.gear_mult_damage:.3f}",
            f"   = {fb.max_hit}",
            "",
        ])
    else:  # magic
        lines.extend([
            "2. MAX HIT (MAGIC):",
            f"   = floor(base_max * (1 + magic_dmg_bonus)) * gear_mult",
            f"   = floor({fb.base_magic_max} * (1 + {fb.magic_damage_bonus:.3f})) * {fb.gear_mult_damage:.3f}",
            f"   = {fb.max_hit}",
            "",
        ])

    # Attack roll
    step = "4" if fb.combat_style == "melee" else "3"
    atk_name = "Atk" if fb.combat_style == "melee" else ("Ranged" if fb.combat_style == "ranged" else "Magic")
    lines.extend([
        f"{step}. ATTACK ROLL:",
        f"   = Eff_{atk_name} * ({atk_name}_Bonus + 64) * gear_mult",
        f"   = {fb.effective_attack} * ({fb.attack_bonus} + 64) * {fb.gear_mult_accuracy:.3f}",
        f"   = {fb.attack_roll:,}",
        "",
    ])

    # Defence roll
    step = "5" if fb.combat_style == "melee" else "4"
    if fb.combat_style == "magic":
        lines.extend([
            f"{step}. DEFENCE ROLL (vs Magic):",
            f"   = (Magic_Level + 9) * (Magic_Def_Bonus + 64)",
            f"   = ({fb.defence_level} + 9) * ({fb.defence_bonus} + 64)",
            f"   = {fb.defence_roll:,}",
            "",
        ])
    else:
        lines.extend([
            f"{step}. DEFENCE ROLL:",
            f"   = (Def_Level + 9) * (Style_Def_Bonus + 64)",
            f"   = ({fb.defence_level} + 9) * ({fb.defence_bonus} + 64)",
            f"   = {fb.defence_roll:,}",
            "",
        ])

    # Hit chance
    step = "6" if fb.combat_style == "melee" else "5"
    lines.append(f"{step}. HIT CHANCE:")
    if fb.attack_roll > fb.defence_roll:
        lines.extend([
            f"   (Attack roll > Defence roll)",
            f"   = 1 - (def_roll + 2) / (2 * (atk_roll + 1))",
            f"   = 1 - ({fb.defence_roll} + 2) / (2 * ({fb.attack_roll} + 1))",
        ])
    else:
        lines.extend([
            f"   (Attack roll <= Defence roll)",
            f"   = atk_roll / (2 * (def_roll + 1))",
            f"   = {fb.attack_roll} / (2 * ({fb.defence_roll} + 1))",
        ])
    lines.extend([
        f"   = {fb.hit_chance:.4f} ({fb.hit_chance*100:.2f}%)",
        "",
    ])

    # DPS
    step = "7" if fb.combat_style == "melee" else "6"
    attack_speed_seconds = fb.attack_speed_ticks * 0.6
    lines.extend([
        f"{step}. DPS:",
        f"   = hit_chance * (max_hit / 2) / attack_speed_seconds",
        f"   = {fb.hit_chance:.4f} * ({fb.max_hit} / 2) / {attack_speed_seconds:.1f}",
        f"   = {fb.dps:.4f}",
    ])

    return "\n".join(lines)
