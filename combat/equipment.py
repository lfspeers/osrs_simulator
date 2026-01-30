"""Equipment, weapons, and gear modifiers for OSRS combat."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from data_loader.item_loader import WeaponLoader

# External loader for dynamic weapon data
_external_loader: Optional["WeaponLoader"] = None


def set_weapon_loader(loader: "WeaponLoader") -> None:
    """Set an external weapon loader for dynamic data.

    Args:
        loader: WeaponLoader instance to use for lookups.
    """
    global _external_loader
    _external_loader = loader


def get_weapon_loader() -> Optional["WeaponLoader"]:
    """Get the current external weapon loader.

    Returns:
        The WeaponLoader instance, or None if not set.
    """
    return _external_loader


class AttackType(Enum):
    """Attack style types."""
    STAB = "stab"
    SLASH = "slash"
    CRUSH = "crush"
    RANGED = "ranged"
    MAGIC = "magic"


class CombatStyle(Enum):
    """Combat style categories."""
    MELEE = "melee"
    RANGED = "ranged"
    MAGIC = "magic"


class AttackStyle(Enum):
    """Attack style options that affect bonuses."""
    # Melee styles
    ACCURATE = ("accurate", 3, 0, CombatStyle.MELEE)      # +3 attack
    AGGRESSIVE = ("aggressive", 0, 3, CombatStyle.MELEE)  # +3 strength
    DEFENSIVE = ("defensive", 0, 0, CombatStyle.MELEE)    # +3 defence (invisible)
    CONTROLLED = ("controlled", 1, 1, CombatStyle.MELEE)  # +1 to each

    # Ranged styles
    RANGED_ACCURATE = ("accurate", 3, 0, CombatStyle.RANGED)
    RAPID = ("rapid", 0, 0, CombatStyle.RANGED)           # -1 tick attack speed
    LONGRANGE = ("longrange", 0, 0, CombatStyle.RANGED)   # +3 defence

    # Magic styles
    MAGIC_ACCURATE = ("accurate", 3, 0, CombatStyle.MAGIC)
    AUTOCAST = ("autocast", 0, 0, CombatStyle.MAGIC)
    DEFENSIVE_AUTOCAST = ("defensive autocast", 0, 0, CombatStyle.MAGIC)

    def __init__(self, display_name: str, attack_bonus: int, strength_bonus: int, style: CombatStyle):
        self.display_name = display_name
        self.attack_bonus = attack_bonus
        self.strength_bonus = strength_bonus
        self.combat_style = style


@dataclass
class EquipmentStats:
    """Equipment stat bonuses."""
    # Attack bonuses
    stab_attack: int = 0
    slash_attack: int = 0
    crush_attack: int = 0
    magic_attack: int = 0
    ranged_attack: int = 0

    # Defence bonuses
    stab_defence: int = 0
    slash_defence: int = 0
    crush_defence: int = 0
    magic_defence: int = 0
    ranged_defence: int = 0

    # Other bonuses
    melee_strength: int = 0
    ranged_strength: int = 0
    magic_damage: float = 0.0  # As decimal, e.g., 0.15 for 15%
    prayer: int = 0

    def get_attack_bonus(self, attack_type: AttackType) -> int:
        """Get attack bonus for a specific attack type."""
        bonuses = {
            AttackType.STAB: self.stab_attack,
            AttackType.SLASH: self.slash_attack,
            AttackType.CRUSH: self.crush_attack,
            AttackType.RANGED: self.ranged_attack,
            AttackType.MAGIC: self.magic_attack,
        }
        return bonuses.get(attack_type, 0)

    def get_strength_bonus(self, combat_style: CombatStyle) -> int:
        """Get strength bonus for a combat style."""
        if combat_style == CombatStyle.MELEE:
            return self.melee_strength
        elif combat_style == CombatStyle.RANGED:
            return self.ranged_strength
        else:
            return 0

    def __add__(self, other: "EquipmentStats") -> "EquipmentStats":
        """Add two equipment stats together."""
        return EquipmentStats(
            stab_attack=self.stab_attack + other.stab_attack,
            slash_attack=self.slash_attack + other.slash_attack,
            crush_attack=self.crush_attack + other.crush_attack,
            magic_attack=self.magic_attack + other.magic_attack,
            ranged_attack=self.ranged_attack + other.ranged_attack,
            stab_defence=self.stab_defence + other.stab_defence,
            slash_defence=self.slash_defence + other.slash_defence,
            crush_defence=self.crush_defence + other.crush_defence,
            magic_defence=self.magic_defence + other.magic_defence,
            ranged_defence=self.ranged_defence + other.ranged_defence,
            melee_strength=self.melee_strength + other.melee_strength,
            ranged_strength=self.ranged_strength + other.ranged_strength,
            magic_damage=self.magic_damage + other.magic_damage,
            prayer=self.prayer + other.prayer,
        )


@dataclass
class Weapon:
    """A weapon with its stats and attack properties."""
    name: str
    attack_speed: int  # In game ticks
    attack_type: AttackType
    combat_style: CombatStyle
    stats: EquipmentStats = field(default_factory=EquipmentStats)
    # Special properties
    is_two_handed: bool = False
    base_magic_max_hit: int = 0  # For magic weapons (tridents, etc.)
    special_attack_cost: int = 0  # Special attack energy cost (0-100)

    @property
    def attack_speed_seconds(self) -> float:
        """Attack speed in seconds."""
        return self.attack_speed * 0.6


@dataclass
class GearModifiers:
    """Multiplicative bonuses from special gear effects."""
    # Void equipment
    void_melee: bool = False      # 1.1x accuracy and damage
    void_ranged: bool = False     # 1.1x accuracy, 1.125x damage
    void_magic: bool = False      # 1.45x accuracy, no damage bonus
    elite_void: bool = False      # +2.5% damage to ranged/magic void

    # Slayer bonuses
    slayer_helm: bool = False     # 7/6 accuracy and damage on task
    slayer_helm_imbued: bool = False  # Same but for ranged/magic too

    # Salve amulet (mutually exclusive with slayer helm)
    salve_amulet: bool = False    # 7/6 accuracy and damage vs undead
    salve_amulet_e: bool = False  # 1.2x accuracy and damage vs undead
    salve_amulet_ei: bool = False # 1.2x for ranged/magic too

    # Dragon hunter gear
    dragon_hunter_lance: bool = False     # 1.2x accuracy and damage vs dragons
    dragon_hunter_crossbow: bool = False  # 1.3x accuracy, 1.25x damage vs dragons

    # Other
    inquisitor_set: bool = False  # 2.5% accuracy and damage with crush
    obsidian_set: bool = False    # 10% accuracy and damage with obsidian weapons

    def get_accuracy_multiplier(
        self,
        combat_style: CombatStyle,
        attack_type: AttackType,
        vs_undead: bool = False,
        vs_dragon: bool = False,
        on_slayer_task: bool = False
    ) -> float:
        """Calculate the total accuracy multiplier from gear effects.

        Note: Salve amulet and slayer helm do NOT stack - salve takes priority.
        """
        multiplier = 1.0

        # Void bonuses
        if combat_style == CombatStyle.MELEE and self.void_melee:
            multiplier *= 1.1
        elif combat_style == CombatStyle.RANGED and self.void_ranged:
            multiplier *= 1.1
        elif combat_style == CombatStyle.MAGIC and self.void_magic:
            multiplier *= 1.45

        # Salve amulet (takes priority over slayer helm)
        if vs_undead:
            if self.salve_amulet_ei and combat_style in (CombatStyle.RANGED, CombatStyle.MAGIC):
                multiplier *= 1.2
            elif self.salve_amulet_e:
                multiplier *= 1.2
            elif self.salve_amulet:
                multiplier *= 7/6
        elif on_slayer_task:
            # Slayer helm only if not using salve
            if self.slayer_helm_imbued:
                multiplier *= 7/6
            elif self.slayer_helm and combat_style == CombatStyle.MELEE:
                multiplier *= 7/6

        # Dragon hunter gear
        if vs_dragon:
            if self.dragon_hunter_lance and combat_style == CombatStyle.MELEE:
                multiplier *= 1.2
            elif self.dragon_hunter_crossbow and combat_style == CombatStyle.RANGED:
                multiplier *= 1.3

        # Inquisitor's set (crush only)
        if self.inquisitor_set and attack_type == AttackType.CRUSH:
            multiplier *= 1.025

        # Obsidian set
        if self.obsidian_set:
            multiplier *= 1.1

        return multiplier

    def get_damage_multiplier(
        self,
        combat_style: CombatStyle,
        attack_type: AttackType,
        vs_undead: bool = False,
        vs_dragon: bool = False,
        on_slayer_task: bool = False
    ) -> float:
        """Calculate the total damage multiplier from gear effects."""
        multiplier = 1.0

        # Void bonuses
        if combat_style == CombatStyle.MELEE and self.void_melee:
            multiplier *= 1.1
        elif combat_style == CombatStyle.RANGED and self.void_ranged:
            base_bonus = 1.1
            if self.elite_void:
                base_bonus += 0.025
            multiplier *= base_bonus
        elif combat_style == CombatStyle.MAGIC and self.void_magic and self.elite_void:
            multiplier *= 1.025

        # Salve amulet (takes priority over slayer helm)
        if vs_undead:
            if self.salve_amulet_ei and combat_style in (CombatStyle.RANGED, CombatStyle.MAGIC):
                multiplier *= 1.2
            elif self.salve_amulet_e:
                multiplier *= 1.2
            elif self.salve_amulet:
                multiplier *= 7/6
        elif on_slayer_task:
            if self.slayer_helm_imbued:
                multiplier *= 7/6
            elif self.slayer_helm and combat_style == CombatStyle.MELEE:
                multiplier *= 7/6

        # Dragon hunter gear
        if vs_dragon:
            if self.dragon_hunter_lance and combat_style == CombatStyle.MELEE:
                multiplier *= 1.2
            elif self.dragon_hunter_crossbow and combat_style == CombatStyle.RANGED:
                multiplier *= 1.25

        # Inquisitor's set
        if self.inquisitor_set and attack_type == AttackType.CRUSH:
            multiplier *= 1.025

        # Obsidian set
        if self.obsidian_set:
            multiplier *= 1.1

        return multiplier


# =============================================================================
# Weapon Definitions
# =============================================================================

WEAPONS: Dict[str, Weapon] = {
    # -------------------------------------------------------------------------
    # Melee Weapons
    # -------------------------------------------------------------------------
    "ghrazi_rapier": Weapon(
        name="Ghrazi rapier",
        attack_speed=4,
        attack_type=AttackType.STAB,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=94, melee_strength=89),
    ),
    "blade_of_saeldor": Weapon(
        name="Blade of saeldor",
        attack_speed=4,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(slash_attack=94, melee_strength=89),
    ),
    "abyssal_whip": Weapon(
        name="Abyssal whip",
        attack_speed=4,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(slash_attack=82, melee_strength=82),
    ),
    "dragon_scimitar": Weapon(
        name="Dragon scimitar",
        attack_speed=4,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(slash_attack=67, melee_strength=66),
    ),
    "osmumtens_fang": Weapon(
        name="Osmumten's fang",
        attack_speed=5,
        attack_type=AttackType.STAB,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=105, melee_strength=103),
    ),
    "scythe_of_vitur": Weapon(
        name="Scythe of vitur",
        attack_speed=5,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(slash_attack=110, melee_strength=75),
        is_two_handed=True,
    ),
    "dragon_hunter_lance": Weapon(
        name="Dragon hunter lance",
        attack_speed=4,
        attack_type=AttackType.STAB,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=85, slash_attack=65, crush_attack=65, melee_strength=70),
    ),
    "abyssal_bludgeon": Weapon(
        name="Abyssal bludgeon",
        attack_speed=4,
        attack_type=AttackType.CRUSH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(crush_attack=102, melee_strength=85),
        is_two_handed=True,
    ),
    "inquisitors_mace": Weapon(
        name="Inquisitor's mace",
        attack_speed=4,
        attack_type=AttackType.CRUSH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(crush_attack=95, melee_strength=89, prayer=2),
    ),
    "saradomin_godsword": Weapon(
        name="Saradomin godsword",
        attack_speed=6,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(slash_attack=132, crush_attack=80, melee_strength=132),
        is_two_handed=True,
        special_attack_cost=50,
    ),
    "armadyl_godsword": Weapon(
        name="Armadyl godsword",
        attack_speed=6,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(slash_attack=132, crush_attack=80, melee_strength=132),
        is_two_handed=True,
        special_attack_cost=50,
    ),

    # -------------------------------------------------------------------------
    # Ranged Weapons
    # -------------------------------------------------------------------------
    "toxic_blowpipe": Weapon(
        name="Toxic blowpipe",
        attack_speed=3,  # Rapid
        attack_type=AttackType.RANGED,
        combat_style=CombatStyle.RANGED,
        stats=EquipmentStats(ranged_attack=30, ranged_strength=20),  # Base stats, scales with darts
        is_two_handed=True,
    ),
    "twisted_bow": Weapon(
        name="Twisted bow",
        attack_speed=5,  # Rapid
        attack_type=AttackType.RANGED,
        combat_style=CombatStyle.RANGED,
        stats=EquipmentStats(ranged_attack=70, ranged_strength=20),  # Scales with magic level
        is_two_handed=True,
    ),
    "bow_of_faerdhinen": Weapon(
        name="Bow of faerdhinen",
        attack_speed=4,  # Rapid
        attack_type=AttackType.RANGED,
        combat_style=CombatStyle.RANGED,
        stats=EquipmentStats(ranged_attack=128, ranged_strength=106),
        is_two_handed=True,
    ),
    "zaryte_crossbow": Weapon(
        name="Zaryte crossbow",
        attack_speed=5,  # Rapid
        attack_type=AttackType.RANGED,
        combat_style=CombatStyle.RANGED,
        stats=EquipmentStats(ranged_attack=110, ranged_strength=0),  # Bolt provides str
        is_two_handed=True,
    ),
    "dragon_hunter_crossbow": Weapon(
        name="Dragon hunter crossbow",
        attack_speed=5,  # Rapid
        attack_type=AttackType.RANGED,
        combat_style=CombatStyle.RANGED,
        stats=EquipmentStats(ranged_attack=95, ranged_strength=0),
        is_two_handed=True,
    ),
    "armadyl_crossbow": Weapon(
        name="Armadyl crossbow",
        attack_speed=5,  # Rapid
        attack_type=AttackType.RANGED,
        combat_style=CombatStyle.RANGED,
        stats=EquipmentStats(ranged_attack=100, ranged_strength=0, prayer=1),
        is_two_handed=True,
    ),

    # -------------------------------------------------------------------------
    # Magic Weapons
    # -------------------------------------------------------------------------
    "trident_of_the_swamp": Weapon(
        name="Trident of the swamp",
        attack_speed=4,
        attack_type=AttackType.MAGIC,
        combat_style=CombatStyle.MAGIC,
        stats=EquipmentStats(magic_attack=25, magic_damage=0.0),  # Damage scales with magic level
        is_two_handed=True,
        base_magic_max_hit=31,  # At 99 magic
    ),
    "sanguinesti_staff": Weapon(
        name="Sanguinesti staff",
        attack_speed=4,
        attack_type=AttackType.MAGIC,
        combat_style=CombatStyle.MAGIC,
        stats=EquipmentStats(magic_attack=25, magic_damage=0.0),
        is_two_handed=True,
        base_magic_max_hit=34,  # At 99 magic
    ),
    "tumekens_shadow": Weapon(
        name="Tumeken's shadow",
        attack_speed=5,
        attack_type=AttackType.MAGIC,
        combat_style=CombatStyle.MAGIC,
        stats=EquipmentStats(magic_attack=35, magic_damage=0.0),  # Triples gear bonuses
        is_two_handed=True,
        base_magic_max_hit=43,  # At 99 magic with 3x multiplier
    ),
    "harmonised_nightmare_staff": Weapon(
        name="Harmonised nightmare staff",
        attack_speed=4,  # Standard spells at 4 tick instead of 5
        attack_type=AttackType.MAGIC,
        combat_style=CombatStyle.MAGIC,
        stats=EquipmentStats(magic_attack=16, magic_damage=0.15),
        is_two_handed=True,
    ),
    "kodai_wand": Weapon(
        name="Kodai wand",
        attack_speed=5,  # Standard cast speed
        attack_type=AttackType.MAGIC,
        combat_style=CombatStyle.MAGIC,
        stats=EquipmentStats(magic_attack=28, magic_damage=0.15),
    ),

    # -------------------------------------------------------------------------
    # Demon Slaying Weapons
    # -------------------------------------------------------------------------
    "arclight": Weapon(
        name="Arclight",
        attack_speed=4,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=38, slash_attack=75, crush_attack=-2, melee_strength=72),
    ),
    "darklight": Weapon(
        name="Darklight",
        attack_speed=4,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=30, slash_attack=70, crush_attack=-2, melee_strength=67),
    ),
    "silverlight": Weapon(
        name="Silverlight",
        attack_speed=4,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=8, slash_attack=13, crush_attack=-2, melee_strength=9),
    ),

    # -------------------------------------------------------------------------
    # Barrows Weapons
    # -------------------------------------------------------------------------
    "dharoks_greataxe": Weapon(
        name="Dharok's greataxe",
        attack_speed=7,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=-4, slash_attack=103, crush_attack=95, melee_strength=105),
        is_two_handed=True,
    ),
    "veracs_flail": Weapon(
        name="Verac's flail",
        attack_speed=4,
        attack_type=AttackType.CRUSH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=68, slash_attack=-2, crush_attack=82, melee_strength=72, prayer=6),
    ),
    "guthans_warspear": Weapon(
        name="Guthan's warspear",
        attack_speed=5,
        attack_type=AttackType.STAB,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=75, slash_attack=75, crush_attack=75, melee_strength=75),
        is_two_handed=True,
    ),
    "torags_hammers": Weapon(
        name="Torag's hammers",
        attack_speed=5,
        attack_type=AttackType.CRUSH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=-4, slash_attack=-4, crush_attack=85, melee_strength=72),
    ),
    "ahrims_staff": Weapon(
        name="Ahrim's staff",
        attack_speed=4,
        attack_type=AttackType.MAGIC,
        combat_style=CombatStyle.MAGIC,
        stats=EquipmentStats(magic_attack=15, magic_damage=0.05, crush_attack=65, melee_strength=50),
        is_two_handed=True,
    ),
    "karils_crossbow": Weapon(
        name="Karil's crossbow",
        attack_speed=4,
        attack_type=AttackType.RANGED,
        combat_style=CombatStyle.RANGED,
        stats=EquipmentStats(ranged_attack=84, ranged_strength=55),
        is_two_handed=True,
    ),

    # -------------------------------------------------------------------------
    # Keris Weapons
    # -------------------------------------------------------------------------
    "keris_partisan": Weapon(
        name="Keris partisan",
        attack_speed=4,
        attack_type=AttackType.STAB,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=78, slash_attack=-2, crush_attack=-2, melee_strength=72),
    ),
    "keris_partisan_of_breaching": Weapon(
        name="Keris partisan of breaching",
        attack_speed=4,
        attack_type=AttackType.STAB,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=78, slash_attack=-2, crush_attack=-2, melee_strength=72),
    ),

    # -------------------------------------------------------------------------
    # Leaf-bladed Weapons
    # -------------------------------------------------------------------------
    "leaf_bladed_battleaxe": Weapon(
        name="Leaf-bladed battleaxe",
        attack_speed=5,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=-2, slash_attack=92, crush_attack=72, melee_strength=92),
    ),
    "leaf_bladed_sword": Weapon(
        name="Leaf-bladed sword",
        attack_speed=4,
        attack_type=AttackType.STAB,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=67, slash_attack=62, crush_attack=-2, melee_strength=50),
    ),

    # -------------------------------------------------------------------------
    # Obsidian Weapons
    # -------------------------------------------------------------------------
    "toktz_xil_ak": Weapon(
        name="Toktz-xil-ak",
        attack_speed=4,
        attack_type=AttackType.SLASH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=40, slash_attack=60, crush_attack=-2, melee_strength=60),
    ),
    "tzhaar_ket_om": Weapon(
        name="Tzhaar-ket-om",
        attack_speed=7,
        attack_type=AttackType.CRUSH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=-4, slash_attack=-4, crush_attack=100, melee_strength=100),
        is_two_handed=True,
    ),
    "toktz_xil_ek": Weapon(
        name="Toktz-xil-ek",
        attack_speed=4,
        attack_type=AttackType.STAB,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=41, slash_attack=25, crush_attack=-4, melee_strength=49),
    ),
    "obsidian_maul": Weapon(
        name="Tzhaar-ket-om",  # Alias
        attack_speed=7,
        attack_type=AttackType.CRUSH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=-4, slash_attack=-4, crush_attack=100, melee_strength=100),
        is_two_handed=True,
    ),

    # -------------------------------------------------------------------------
    # Wilderness Weapons (Revenants)
    # -------------------------------------------------------------------------
    "viggoras_chainmace": Weapon(
        name="Viggora's chainmace",
        attack_speed=4,
        attack_type=AttackType.CRUSH,
        combat_style=CombatStyle.MELEE,
        stats=EquipmentStats(stab_attack=31, slash_attack=12, crush_attack=72, melee_strength=72),
    ),
    "craws_bow": Weapon(
        name="Craw's bow",
        attack_speed=5,
        attack_type=AttackType.RANGED,
        combat_style=CombatStyle.RANGED,
        stats=EquipmentStats(ranged_attack=75, ranged_strength=60),
        is_two_handed=True,
    ),
    "thammarons_sceptre": Weapon(
        name="Thammaron's sceptre",
        attack_speed=4,
        attack_type=AttackType.MAGIC,
        combat_style=CombatStyle.MAGIC,
        stats=EquipmentStats(magic_attack=20, magic_damage=0.0),
        base_magic_max_hit=25,
    ),

    # -------------------------------------------------------------------------
    # Smoke Battlestaff
    # -------------------------------------------------------------------------
    "smoke_battlestaff": Weapon(
        name="Smoke battlestaff",
        attack_speed=5,
        attack_type=AttackType.MAGIC,
        combat_style=CombatStyle.MAGIC,
        stats=EquipmentStats(magic_attack=17, magic_damage=0.10),
    ),
}


def get_weapon(name: str) -> Optional[Weapon]:
    """Get a weapon by its key name.

    Looks up weapons in the following order:
    1. Hardcoded WEAPONS dictionary (curated data)
    2. External loader (osrsreboxed-db data if loaded)

    Args:
        name: The weapon's key name (e.g., 'ghrazi_rapier').

    Returns:
        The Weapon object, or None if not found.
    """
    normalized = name.lower().replace(" ", "_").replace("'", "")

    # Try hardcoded weapons first (they have curated data)
    if normalized in WEAPONS:
        return WEAPONS[normalized]

    # Fall back to external loader
    if _external_loader is not None:
        return _external_loader.get(name)

    return None


def list_weapons(combat_style: Optional[CombatStyle] = None) -> List[str]:
    """List all available weapon names.

    If an external loader is set, combines weapons from both sources.

    Args:
        combat_style: Filter by combat style, or None for all weapons.

    Returns:
        List of weapon key names.
    """
    # Get hardcoded weapons
    if combat_style is None:
        weapons = set(WEAPONS.keys())
    else:
        weapons = {
            name for name, weapon in WEAPONS.items()
            if weapon.combat_style == combat_style
        }

    # Add from external loader if available
    if _external_loader is not None and _external_loader.is_loaded():
        if combat_style is None:
            weapons.update(_external_loader.list_all())
        else:
            weapons.update(_external_loader.list_by_style(combat_style))

    return sorted(weapons)
