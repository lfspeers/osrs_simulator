"""Combat equipment presets for common setups."""

from dataclasses import dataclass
from typing import Dict, Optional

from combat.equipment import (
    Weapon,
    EquipmentStats,
    GearModifiers,
    get_weapon,
)


@dataclass
class CombatPreset:
    """A complete combat equipment preset."""
    name: str
    description: str
    weapon_name: str
    equipment_stats: EquipmentStats
    gear_modifiers: GearModifiers

    @property
    def weapon(self) -> Optional[Weapon]:
        """Get the weapon for this preset."""
        return get_weapon(self.weapon_name)


# BiS (Best in Slot) melee gear stats (excluding weapon)
BIS_MELEE_STATS = EquipmentStats(
    stab_attack=0,
    slash_attack=0,
    crush_attack=0,
    melee_strength=82,  # Torva + Ferocious + Infernal + Primordial + Berserker
    prayer=6,
)

# BiS ranged gear stats (excluding weapon)
BIS_RANGED_STATS = EquipmentStats(
    ranged_attack=57,  # Masori + Zaryte + Pegasian + Archers
    ranged_strength=44,  # Dragon arrows / Ruby bolts (e)
    prayer=6,
)

# BiS magic gear stats (excluding weapon)
BIS_MAGIC_STATS = EquipmentStats(
    magic_attack=136,  # Ancestral + Occult + Tormented + Eternal
    magic_damage=0.21,  # Occult + Tormented
    prayer=6,
)


PRESETS: Dict[str, CombatPreset] = {
    # -------------------------------------------------------------------------
    # Melee Presets
    # -------------------------------------------------------------------------
    "max_melee_stab": CombatPreset(
        name="Max Melee (Stab)",
        description="BiS melee with Ghrazi rapier",
        weapon_name="ghrazi_rapier",
        equipment_stats=BIS_MELEE_STATS,
        gear_modifiers=GearModifiers(),
    ),
    "max_melee_slash": CombatPreset(
        name="Max Melee (Slash)",
        description="BiS melee with Blade of saeldor",
        weapon_name="blade_of_saeldor",
        equipment_stats=BIS_MELEE_STATS,
        gear_modifiers=GearModifiers(),
    ),
    "max_melee_crush": CombatPreset(
        name="Max Melee (Crush)",
        description="BiS melee with Inquisitor's mace",
        weapon_name="inquisitors_mace",
        equipment_stats=BIS_MELEE_STATS,
        gear_modifiers=GearModifiers(inquisitor_set=True),
    ),
    "dragon_hunter_lance": CombatPreset(
        name="Dragon Hunter Lance",
        description="BiS for dragons with DHL",
        weapon_name="dragon_hunter_lance",
        equipment_stats=BIS_MELEE_STATS,
        gear_modifiers=GearModifiers(dragon_hunter_lance=True),
    ),
    "scythe": CombatPreset(
        name="Scythe of Vitur",
        description="BiS for large targets",
        weapon_name="scythe_of_vitur",
        equipment_stats=BIS_MELEE_STATS,
        gear_modifiers=GearModifiers(),
    ),
    "fang": CombatPreset(
        name="Osmumten's Fang",
        description="High accuracy stab weapon",
        weapon_name="osmumtens_fang",
        equipment_stats=BIS_MELEE_STATS,
        gear_modifiers=GearModifiers(),
    ),

    # -------------------------------------------------------------------------
    # Ranged Presets
    # -------------------------------------------------------------------------
    "max_ranged_tbow": CombatPreset(
        name="Max Ranged (Twisted Bow)",
        description="BiS ranged with Twisted bow",
        weapon_name="twisted_bow",
        equipment_stats=BIS_RANGED_STATS,
        gear_modifiers=GearModifiers(),
    ),
    "max_ranged_bofa": CombatPreset(
        name="Max Ranged (Bow of Faerdhinen)",
        description="BiS ranged with crystal bow",
        weapon_name="bow_of_faerdhinen",
        equipment_stats=BIS_RANGED_STATS,
        gear_modifiers=GearModifiers(),
    ),
    "dragon_hunter_crossbow": CombatPreset(
        name="Dragon Hunter Crossbow",
        description="BiS for dragons at range",
        weapon_name="dragon_hunter_crossbow",
        equipment_stats=EquipmentStats(
            ranged_attack=57,
            ranged_strength=122,  # Ruby dragon bolts (e)
        ),
        gear_modifiers=GearModifiers(dragon_hunter_crossbow=True),
    ),
    "blowpipe": CombatPreset(
        name="Toxic Blowpipe",
        description="Fast ranged DPS",
        weapon_name="toxic_blowpipe",
        equipment_stats=EquipmentStats(
            ranged_attack=57,
            ranged_strength=40,  # Dragon darts
        ),
        gear_modifiers=GearModifiers(),
    ),

    # -------------------------------------------------------------------------
    # Magic Presets
    # -------------------------------------------------------------------------
    "max_magic_shadow": CombatPreset(
        name="Max Magic (Shadow)",
        description="BiS magic with Tumeken's shadow",
        weapon_name="tumekens_shadow",
        equipment_stats=BIS_MAGIC_STATS,
        gear_modifiers=GearModifiers(),
    ),
    "max_magic_sang": CombatPreset(
        name="Max Magic (Sanguinesti)",
        description="BiS magic with Sang staff",
        weapon_name="sanguinesti_staff",
        equipment_stats=BIS_MAGIC_STATS,
        gear_modifiers=GearModifiers(),
    ),
    "trident": CombatPreset(
        name="Trident of the Swamp",
        description="Standard magic DPS",
        weapon_name="trident_of_the_swamp",
        equipment_stats=BIS_MAGIC_STATS,
        gear_modifiers=GearModifiers(),
    ),

    # -------------------------------------------------------------------------
    # Void Presets
    # -------------------------------------------------------------------------
    "void_melee": CombatPreset(
        name="Elite Void Melee",
        description="Elite void with rapier",
        weapon_name="ghrazi_rapier",
        equipment_stats=EquipmentStats(melee_strength=50),  # Void has lower str bonus
        gear_modifiers=GearModifiers(void_melee=True, elite_void=True),
    ),
    "void_ranged": CombatPreset(
        name="Elite Void Ranged",
        description="Elite void with blowpipe",
        weapon_name="toxic_blowpipe",
        equipment_stats=EquipmentStats(ranged_attack=30, ranged_strength=40),
        gear_modifiers=GearModifiers(void_ranged=True, elite_void=True),
    ),

    # -------------------------------------------------------------------------
    # Slayer Presets
    # -------------------------------------------------------------------------
    "slayer_melee": CombatPreset(
        name="Slayer Melee",
        description="BiS melee on slayer task",
        weapon_name="ghrazi_rapier",
        equipment_stats=BIS_MELEE_STATS,
        gear_modifiers=GearModifiers(slayer_helm_imbued=True),
    ),
    "slayer_ranged": CombatPreset(
        name="Slayer Ranged",
        description="BiS ranged on slayer task",
        weapon_name="bow_of_faerdhinen",
        equipment_stats=BIS_RANGED_STATS,
        gear_modifiers=GearModifiers(slayer_helm_imbued=True),
    ),
}


def get_combat_preset(name: str) -> Optional[CombatPreset]:
    """Get a combat preset by name.

    Args:
        name: Preset key name.

    Returns:
        CombatPreset, or None if not found.
    """
    return PRESETS.get(name.lower().replace(" ", "_"))


def list_combat_presets() -> list[str]:
    """List all available combat preset names."""
    return list(PRESETS.keys())
