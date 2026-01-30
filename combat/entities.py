"""Monster and boss definitions for OSRS combat."""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from data_loader.monster_loader import MonsterLoader

# External loader for dynamic monster data
_external_loader: Optional["MonsterLoader"] = None


def set_monster_loader(loader: "MonsterLoader") -> None:
    """Set an external monster loader for dynamic data.

    Args:
        loader: MonsterLoader instance to use for lookups.
    """
    global _external_loader
    _external_loader = loader


def get_monster_loader() -> Optional["MonsterLoader"]:
    """Get the current external monster loader.

    Returns:
        The MonsterLoader instance, or None if not set.
    """
    return _external_loader


@dataclass
class MonsterStats:
    """Stats for an NPC/monster.

    Defence bonuses are used to calculate the NPC's defence roll against
    specific attack styles. Magic level is used for the magic defence roll.
    """
    name: str
    hitpoints: int

    # Combat levels
    defence_level: int = 1
    magic_level: int = 1

    # Defence bonuses
    stab_defence: int = 0
    slash_defence: int = 0
    crush_defence: int = 0
    ranged_defence: int = 0
    magic_defence: int = 0

    # Combat stats (for reference)
    attack_level: int = 1
    strength_level: int = 1
    ranged_level: int = 1
    max_hit: int = 0

    # Special properties
    is_undead: bool = False
    is_demon: bool = False
    is_dragon: bool = False
    is_kalphite: bool = False
    is_leafy: bool = False
    slayer_category: Optional[str] = None
    tile_size: int = 1  # For scythe calculations

    def get_defence_bonus(self, attack_style: str) -> int:
        """Get defence bonus for a specific attack style.

        Args:
            attack_style: One of 'stab', 'slash', 'crush', 'ranged', 'magic'.

        Returns:
            The defence bonus value.
        """
        bonuses = {
            "stab": self.stab_defence,
            "slash": self.slash_defence,
            "crush": self.crush_defence,
            "ranged": self.ranged_defence,
            "magic": self.magic_defence,
        }
        return bonuses.get(attack_style.lower(), 0)


# =============================================================================
# Boss Definitions
# =============================================================================

MONSTERS: Dict[str, MonsterStats] = {
    # -------------------------------------------------------------------------
    # God Wars Dungeon
    # -------------------------------------------------------------------------
    "general_graardor": MonsterStats(
        name="General Graardor",
        hitpoints=255,
        defence_level=250,
        magic_level=80,
        stab_defence=90,
        slash_defence=130,
        crush_defence=90,
        ranged_defence=70,
        magic_defence=-18,  # Very weak to magic
        attack_level=280,
        strength_level=350,
        max_hit=60,
        tile_size=3,
    ),
    "commander_zilyana": MonsterStats(
        name="Commander Zilyana",
        hitpoints=255,
        defence_level=300,
        magic_level=300,
        stab_defence=80,
        slash_defence=100,
        crush_defence=100,
        ranged_defence=80,
        magic_defence=150,
        attack_level=300,
        strength_level=300,
        max_hit=31,
        tile_size=2,
    ),
    "kril_tsutsaroth": MonsterStats(
        name="K'ril Tsutsaroth",
        hitpoints=255,
        defence_level=270,
        magic_level=220,
        stab_defence=140,
        slash_defence=90,
        crush_defence=90,
        ranged_defence=95,
        magic_defence=55,
        attack_level=280,
        strength_level=280,
        max_hit=49,
        is_demon=True,
        slayer_category="demon",
        tile_size=3,
    ),
    "kreearra": MonsterStats(
        name="Kree'arra",
        hitpoints=255,
        defence_level=260,
        magic_level=200,
        stab_defence=60,
        slash_defence=120,
        crush_defence=60,
        ranged_defence=200,
        magic_defence=200,
        attack_level=250,
        ranged_level=250,
        max_hit=71,
        tile_size=3,
    ),

    # -------------------------------------------------------------------------
    # Dragons
    # -------------------------------------------------------------------------
    "vorkath": MonsterStats(
        name="Vorkath",
        hitpoints=750,
        defence_level=214,
        magic_level=150,
        stab_defence=26,
        slash_defence=108,
        crush_defence=108,
        ranged_defence=26,
        magic_defence=240,
        attack_level=560,
        strength_level=308,
        ranged_level=308,
        max_hit=32,
        is_dragon=True,
        is_undead=True,
        slayer_category="dragon",
        tile_size=5,
    ),
    "king_black_dragon": MonsterStats(
        name="King Black Dragon",
        hitpoints=255,
        defence_level=240,
        magic_level=240,
        stab_defence=70,
        slash_defence=90,
        crush_defence=90,
        ranged_defence=70,
        magic_defence=60,
        attack_level=240,
        strength_level=240,
        max_hit=25,
        is_dragon=True,
        slayer_category="dragon",
        tile_size=5,
    ),

    # -------------------------------------------------------------------------
    # Zulrah
    # -------------------------------------------------------------------------
    "zulrah_green": MonsterStats(
        name="Zulrah (Green/Ranged)",
        hitpoints=500,
        defence_level=300,
        magic_level=300,
        stab_defence=50,
        slash_defence=50,
        crush_defence=50,
        ranged_defence=0,
        magic_defence=300,  # Immune to magic
        ranged_level=300,
        max_hit=41,
        tile_size=4,
    ),
    "zulrah_blue": MonsterStats(
        name="Zulrah (Blue/Magic)",
        hitpoints=500,
        defence_level=300,
        magic_level=300,
        stab_defence=0,
        slash_defence=0,
        crush_defence=0,
        ranged_defence=300,  # Immune to ranged
        magic_defence=50,
        attack_level=300,
        max_hit=41,
        tile_size=4,
    ),
    "zulrah_red": MonsterStats(
        name="Zulrah (Red/Melee)",
        hitpoints=500,
        defence_level=300,
        magic_level=300,
        stab_defence=50,
        slash_defence=50,
        crush_defence=50,
        ranged_defence=0,
        magic_defence=50,
        attack_level=300,
        strength_level=300,
        max_hit=41,
        tile_size=4,
    ),

    # -------------------------------------------------------------------------
    # Other Bosses
    # -------------------------------------------------------------------------
    "kalphite_queen": MonsterStats(
        name="Kalphite Queen",
        hitpoints=255,  # Per phase
        defence_level=300,
        magic_level=300,
        stab_defence=0,
        slash_defence=0,
        crush_defence=0,
        ranged_defence=0,
        magic_defence=0,
        attack_level=280,
        strength_level=280,
        ranged_level=280,
        max_hit=31,
        is_kalphite=True,
        slayer_category="kalphite",
        tile_size=5,
    ),
    "corporeal_beast": MonsterStats(
        name="Corporeal Beast",
        hitpoints=2000,
        defence_level=310,
        magic_level=350,
        stab_defence=100,
        slash_defence=200,
        crush_defence=200,
        ranged_defence=200,
        magic_defence=200,
        attack_level=320,
        strength_level=320,
        max_hit=51,
        tile_size=5,
    ),
    "abyssal_sire": MonsterStats(
        name="Abyssal Sire",
        hitpoints=400,
        defence_level=250,
        magic_level=200,
        stab_defence=20,
        slash_defence=60,
        crush_defence=60,
        ranged_defence=50,
        magic_defence=100,
        attack_level=220,
        strength_level=220,
        max_hit=40,
        is_demon=True,
        slayer_category="abyssal demon",
        tile_size=4,
    ),
    "cerberus": MonsterStats(
        name="Cerberus",
        hitpoints=600,
        defence_level=100,
        magic_level=220,
        stab_defence=100,
        slash_defence=100,
        crush_defence=100,
        ranged_defence=100,
        magic_defence=100,
        attack_level=220,
        strength_level=220,
        max_hit=23,
        is_demon=True,
        slayer_category="hellhound",
        tile_size=5,
    ),
    "alchemical_hydra": MonsterStats(
        name="Alchemical Hydra",
        hitpoints=1100,  # Total across phases
        defence_level=180,
        magic_level=1,
        stab_defence=0,
        slash_defence=0,
        crush_defence=0,
        ranged_defence=0,
        magic_defence=0,
        attack_level=180,
        ranged_level=180,
        max_hit=28,
        slayer_category="hydra",
        tile_size=4,
    ),

    # -------------------------------------------------------------------------
    # Raids
    # -------------------------------------------------------------------------
    "great_olm_head": MonsterStats(
        name="Great Olm (Head)",
        hitpoints=800,  # Scales with party
        defence_level=175,
        magic_level=250,
        stab_defence=50,
        slash_defence=50,
        crush_defence=50,
        ranged_defence=50,
        magic_defence=50,
        tile_size=5,
    ),
    "verzik_p2": MonsterStats(
        name="Verzik Vitur P2",
        hitpoints=2050,
        defence_level=200,
        magic_level=350,
        stab_defence=10,
        slash_defence=60,
        crush_defence=60,
        ranged_defence=10,
        magic_defence=150,
        attack_level=250,
        strength_level=250,
        ranged_level=250,
        max_hit=66,
        tile_size=4,
    ),

    # -------------------------------------------------------------------------
    # Slayer Monsters
    # -------------------------------------------------------------------------
    "abyssal_demon": MonsterStats(
        name="Abyssal Demon",
        hitpoints=150,
        defence_level=135,
        magic_level=1,
        stab_defence=20,
        slash_defence=20,
        crush_defence=20,
        ranged_defence=20,
        magic_defence=0,
        attack_level=97,
        strength_level=67,
        max_hit=8,
        is_demon=True,
        slayer_category="abyssal demon",
    ),
    "kraken": MonsterStats(
        name="Kraken",
        hitpoints=255,
        defence_level=255,
        magic_level=255,
        stab_defence=0,
        slash_defence=0,
        crush_defence=0,
        ranged_defence=0,
        magic_defence=0,
        attack_level=204,
        max_hit=28,
        slayer_category="cave kraken",
        tile_size=4,
    ),
    "thermonuclear_smoke_devil": MonsterStats(
        name="Thermonuclear Smoke Devil",
        hitpoints=240,
        defence_level=180,
        magic_level=170,
        stab_defence=10,
        slash_defence=60,
        crush_defence=60,
        ranged_defence=10,
        magic_defence=200,
        attack_level=180,
        strength_level=180,
        max_hit=28,
        slayer_category="smoke devil",
        tile_size=3,
    ),

    # -------------------------------------------------------------------------
    # Wilderness Bosses
    # -------------------------------------------------------------------------
    "callisto": MonsterStats(
        name="Callisto",
        hitpoints=255,
        defence_level=440,
        magic_level=175,
        stab_defence=50,
        slash_defence=135,
        crush_defence=135,
        ranged_defence=200,
        magic_defence=135,
        attack_level=350,
        strength_level=350,
        max_hit=60,
        tile_size=3,
    ),
    "vetion": MonsterStats(
        name="Vet'ion",
        hitpoints=255,  # Per phase
        defence_level=395,
        magic_level=175,
        stab_defence=150,
        slash_defence=150,
        crush_defence=0,  # Weak to crush
        ranged_defence=200,
        magic_defence=200,
        attack_level=280,
        strength_level=280,
        max_hit=50,
        is_undead=True,
        tile_size=3,
    ),
    "venenatis": MonsterStats(
        name="Venenatis",
        hitpoints=255,
        defence_level=490,
        magic_level=275,
        stab_defence=125,
        slash_defence=125,
        crush_defence=125,
        ranged_defence=125,
        magic_defence=200,
        attack_level=278,
        strength_level=255,
        max_hit=50,
        tile_size=3,
    ),
}


def get_monster(name: str) -> Optional[MonsterStats]:
    """Get a monster by its key name.

    Looks up monsters in the following order:
    1. External loader (osrsreboxed-db data if loaded)
    2. Hardcoded MONSTERS dictionary

    Args:
        name: The monster's key name (e.g., 'vorkath', 'general_graardor').

    Returns:
        The MonsterStats object, or None if not found.
    """
    # Try external loader first (more comprehensive data)
    if _external_loader is not None:
        result = _external_loader.get(name)
        if result is not None:
            return result

    # Fall back to hardcoded monsters
    normalized = name.lower().replace(" ", "_").replace("'", "")
    return MONSTERS.get(normalized)


def list_monsters(category: Optional[str] = None) -> List[str]:
    """List all available monster names.

    If an external loader is set, combines monsters from both sources.

    Args:
        category: Filter by:
                 - 'bosses': high HP monsters (>= 200 HP)
                 - 'dragon', 'demon', 'undead', 'kalphite', 'leafy': by attribute
                 - Other strings: by slayer category
                 - None: all monsters

    Returns:
        List of monster key names.
    """
    # Attribute-based categories
    attribute_categories = {"dragon", "demon", "undead", "kalphite", "leafy"}

    # Get hardcoded monsters
    if category is None:
        monsters = set(MONSTERS.keys())
    elif category == "bosses":
        monsters = {name for name, m in MONSTERS.items() if m.hitpoints >= 200}
    elif category in attribute_categories:
        # Filter by attribute
        attr_check = {
            "dragon": lambda m: m.is_dragon,
            "demon": lambda m: m.is_demon,
            "undead": lambda m: m.is_undead,
            "kalphite": lambda m: m.is_kalphite,
            "leafy": lambda m: m.is_leafy,
        }
        check_fn = attr_check[category]
        monsters = {name for name, m in MONSTERS.items() if check_fn(m)}
    else:
        # Filter by slayer category
        monsters = {
            name for name, monster in MONSTERS.items()
            if monster.slayer_category == category
        }

    # Add from external loader if available
    if _external_loader is not None and _external_loader.is_loaded():
        if category is None:
            monsters.update(_external_loader.list_all())
        elif category == "bosses":
            monsters.update(_external_loader.get_bosses())
        elif category in attribute_categories:
            monsters.update(_external_loader.get_by_attribute(category))
        else:
            monsters.update(_external_loader.get_by_slayer_category(category))

    return sorted(monsters)


def get_dragons() -> List[str]:
    """Get all dragon monsters."""
    return [name for name, m in MONSTERS.items() if m.is_dragon]


def get_undead() -> List[str]:
    """Get all undead monsters."""
    return [name for name, m in MONSTERS.items() if m.is_undead]


def get_demons() -> List[str]:
    """Get all demon monsters."""
    return [name for name, m in MONSTERS.items() if m.is_demon]
