"""OSRS Combat DPS Simulator.

This module provides tools for calculating combat DPS (damage per second)
for tick-perfect scenarios in Old School RuneScape.

Example usage:
    from combat import quick_dps, CombatSetup, CombatCalculator

    # Quick calculation
    result = quick_dps(
        weapon_name="ghrazi_rapier",
        monster_name="vorkath",
        prayer_name="piety"
    )
    print(f"DPS: {result.dps:.2f}")

    # Detailed setup
    from combat.equipment import get_weapon
    from combat.entities import get_monster
    from combat.prayers import PIETY

    setup = CombatSetup(
        weapon=get_weapon("abyssal_whip"),
        target=get_monster("general_graardor"),
        prayer=PIETY,
    )
    calc = CombatCalculator(setup)
    result = calc.calculate()
"""

# Core types
from .equipment import (
    AttackType,
    AttackStyle,
    CombatStyle,
    EquipmentSlot,
    EquippedItem,
    EquipmentLoadout,
    EquipmentStats,
    Weapon,
    GearModifiers,
    get_weapon,
    list_weapons,
    WEAPONS,
    Ammo,
    get_ammo,
    list_ammo,
    AMMO,
)

from .prayers import (
    Prayer,
    PrayerBonus,
    get_prayer,
    list_prayers,
    PIETY,
    RIGOUR,
    AUGURY,
    EAGLE_EYE,
)

from .entities import (
    MonsterStats,
    get_monster,
    list_monsters,
    get_dragons,
    get_undead,
    get_demons,
    set_monster_loader,
    get_monster_loader,
    MONSTERS,
)

from .equipment import (
    set_weapon_loader,
    get_weapon_loader,
)

from .spells import (
    Spell,
    Spellbook,
    get_spell,
    list_spells,
    SPELLS,
)

from .simulation import (
    CombatStats,
    CombatSetup,
    CombatResult,
    CombatCalculator,
    PotionBoost,
    quick_dps,
    simulate_kill,
)

from .formulas import (
    effective_level,
    max_hit_melee,
    max_hit_ranged,
    max_hit_magic,
    attack_roll,
    defence_roll_npc,
    hit_chance,
    calculate_dps,
    calculate_kill_time,
    calculate_kills_per_hour,
    FormulaBreakdown,
    format_formula_breakdown,
)

from .storage import (
    SimulationResult,
    SimulationStorage,
    generate_simulation_id,
)

# New passive effects system
from .effects import (
    PassiveEffect,
    SetBonus,
    EffectCondition,
    EffectModifier,
    ActiveEffect,
    ResolvedModifiers,
    SourceType,
)

from .effect_engine import (
    EffectEngine,
    CombatContext,
    format_active_effects,
    get_active_effects,
    resolve_modifiers,
)

from .effect_definitions import (
    ALL_EFFECTS,
    ALL_SET_BONUSES,
    WEAPON_EFFECTS,
    STACKING_GROUPS,
    get_effect,
    get_set_bonus,
    list_effects,
    list_set_bonuses,
)

__all__ = [
    # Equipment
    "AttackType",
    "AttackStyle",
    "CombatStyle",
    "EquipmentSlot",
    "EquippedItem",
    "EquipmentLoadout",
    "EquipmentStats",
    "Weapon",
    "GearModifiers",
    "get_weapon",
    "list_weapons",
    "set_weapon_loader",
    "get_weapon_loader",
    "WEAPONS",
    # Ammo
    "Ammo",
    "get_ammo",
    "list_ammo",
    "AMMO",
    # Prayers
    "Prayer",
    "PrayerBonus",
    "get_prayer",
    "list_prayers",
    "PIETY",
    "RIGOUR",
    "AUGURY",
    "EAGLE_EYE",
    # Entities
    "MonsterStats",
    "get_monster",
    "list_monsters",
    "get_dragons",
    "get_undead",
    "get_demons",
    "set_monster_loader",
    "get_monster_loader",
    "MONSTERS",
    # Spells
    "Spell",
    "Spellbook",
    "get_spell",
    "list_spells",
    "SPELLS",
    # Simulation
    "CombatStats",
    "CombatSetup",
    "CombatResult",
    "CombatCalculator",
    "PotionBoost",
    "quick_dps",
    "simulate_kill",
    # Formulas
    "effective_level",
    "max_hit_melee",
    "max_hit_ranged",
    "max_hit_magic",
    "attack_roll",
    "defence_roll_npc",
    "hit_chance",
    "calculate_dps",
    "calculate_kill_time",
    "calculate_kills_per_hour",
    "FormulaBreakdown",
    "format_formula_breakdown",
    # Storage
    "SimulationResult",
    "SimulationStorage",
    "generate_simulation_id",
    # Passive Effects System
    "PassiveEffect",
    "SetBonus",
    "EffectCondition",
    "EffectModifier",
    "ActiveEffect",
    "ResolvedModifiers",
    "SourceType",
    "EffectEngine",
    "CombatContext",
    "format_active_effects",
    "get_active_effects",
    "resolve_modifiers",
    "ALL_EFFECTS",
    "ALL_SET_BONUSES",
    "WEAPON_EFFECTS",
    "STACKING_GROUPS",
    "get_effect",
    "get_set_bonus",
    "list_effects",
    "list_set_bonuses",
]
