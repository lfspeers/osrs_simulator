"""Equipment, weapons, and gear modifiers for OSRS combat."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from data_loader.item_loader import WeaponLoader, ItemLoader
    from data_loader.spell_loader import Spell, Spellbook
    from .entities import MonsterStats
    from .simulation import CombatStats, CombatResult, PotionBoost
    from .prayers import Prayer

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


class EquipmentSlot(Enum):
    """Equipment slot types matching OSRS/RuneLite."""
    HEAD = "head"
    CAPE = "cape"
    NECK = "neck"
    AMMO = "ammo"
    WEAPON = "weapon"
    BODY = "body"
    SHIELD = "shield"
    LEGS = "legs"
    HANDS = "hands"
    FEET = "feet"
    RING = "ring"


# =============================================================================
# Slot-Specific Item Classes
# =============================================================================
# Each item is tied to a specific equipment slot. This provides type safety
# and allows slot-specific attributes (e.g., weapons have attack_speed).

@dataclass
class SlotItem:
    """Base class for equipped items. Each subclass is tied to a specific slot.

    Attributes:
        name: Item name (e.g., 'Dragon hunter crossbow').
        item_id: OSRS item ID (for RuneLite integration).
        stats: Equipment stats provided by this item.
    """
    SLOT: EquipmentSlot = None  # Override in subclasses

    name: str = ""
    item_id: int = 0
    stats: "EquipmentStats" = field(default_factory=lambda: EquipmentStats())

    @property
    def slot(self) -> EquipmentSlot:
        """Get the slot this item belongs to."""
        return self.SLOT


@dataclass
class HeadItem(SlotItem):
    """Head slot item (helmets, masks, hats)."""
    SLOT: EquipmentSlot = field(default=EquipmentSlot.HEAD, init=False, repr=False)


@dataclass
class CapeItem(SlotItem):
    """Cape slot item (capes, cloaks)."""
    SLOT: EquipmentSlot = field(default=EquipmentSlot.CAPE, init=False, repr=False)


@dataclass
class NeckItem(SlotItem):
    """Neck slot item (amulets, necklaces)."""
    SLOT: EquipmentSlot = field(default=EquipmentSlot.NECK, init=False, repr=False)


@dataclass
class AmmoItem(SlotItem):
    """Ammo slot item (arrows, bolts, darts, blessing).

    Attributes:
        is_enchanted: Whether this is enchanted ammo.
        enchant_proc_chance: Base proc chance for enchanted effect.
        enchant_proc_chance_diary: Proc chance with Kandarin hard diary.
    """
    SLOT: EquipmentSlot = field(default=EquipmentSlot.AMMO, init=False, repr=False)

    is_enchanted: bool = False
    enchant_proc_chance: float = 0.0
    enchant_proc_chance_diary: float = 0.0


@dataclass
class WeaponItem(SlotItem):
    """Weapon slot item (main-hand weapons).

    Attributes:
        attack_speed: Weapon attack speed in ticks.
        attack_type: Primary attack type (stab, slash, crush, ranged, magic).
        combat_style: Combat style category (melee, ranged, magic).
        is_two_handed: Whether weapon requires both hands.
        base_magic_max_hit: Base max hit for powered staves.
        special_attack_cost: Special attack energy cost (0-100).
    """
    SLOT: EquipmentSlot = field(default=EquipmentSlot.WEAPON, init=False, repr=False)

    attack_speed: int = 4
    attack_type: "AttackType" = None
    combat_style: "CombatStyle" = None
    is_two_handed: bool = False
    base_magic_max_hit: int = 0
    special_attack_cost: int = 0


@dataclass
class BodyItem(SlotItem):
    """Body slot item (platebodies, chainbodies, robes)."""
    SLOT: EquipmentSlot = field(default=EquipmentSlot.BODY, init=False, repr=False)


@dataclass
class ShieldItem(SlotItem):
    """Shield slot item (shields, defenders, books, off-hands)."""
    SLOT: EquipmentSlot = field(default=EquipmentSlot.SHIELD, init=False, repr=False)


@dataclass
class LegsItem(SlotItem):
    """Legs slot item (platelegs, plateskirts, robes)."""
    SLOT: EquipmentSlot = field(default=EquipmentSlot.LEGS, init=False, repr=False)


@dataclass
class HandsItem(SlotItem):
    """Hands slot item (gloves, vambraces, bracers)."""
    SLOT: EquipmentSlot = field(default=EquipmentSlot.HANDS, init=False, repr=False)


@dataclass
class FeetItem(SlotItem):
    """Feet slot item (boots)."""
    SLOT: EquipmentSlot = field(default=EquipmentSlot.FEET, init=False, repr=False)


@dataclass
class RingItem(SlotItem):
    """Ring slot item."""
    SLOT: EquipmentSlot = field(default=EquipmentSlot.RING, init=False, repr=False)


# Type alias for any slot item
EquippedItem = SlotItem

# Mapping from slot to item class
SLOT_ITEM_CLASSES: Dict[EquipmentSlot, type] = {
    EquipmentSlot.HEAD: HeadItem,
    EquipmentSlot.CAPE: CapeItem,
    EquipmentSlot.NECK: NeckItem,
    EquipmentSlot.AMMO: AmmoItem,
    EquipmentSlot.WEAPON: WeaponItem,
    EquipmentSlot.BODY: BodyItem,
    EquipmentSlot.SHIELD: ShieldItem,
    EquipmentSlot.LEGS: LegsItem,
    EquipmentSlot.HANDS: HandsItem,
    EquipmentSlot.FEET: FeetItem,
    EquipmentSlot.RING: RingItem,
}

# RuneLite Inventory Setups equipment slot order (positional array indices)
# Order: head(0), cape(1), neck(2), weapon(3), body(4), shield(5),
#        legs(6), hands(7), feet(8), ring(9), ammo(10)
RUNELITE_SLOT_ORDER: List[EquipmentSlot] = [
    EquipmentSlot.HEAD,    # 0
    EquipmentSlot.CAPE,    # 1
    EquipmentSlot.NECK,    # 2
    EquipmentSlot.WEAPON,  # 3
    EquipmentSlot.BODY,    # 4
    EquipmentSlot.SHIELD,  # 5
    EquipmentSlot.LEGS,    # 6
    EquipmentSlot.HANDS,   # 7
    EquipmentSlot.FEET,    # 8
    EquipmentSlot.RING,    # 9
    EquipmentSlot.AMMO,    # 10
]


def create_slot_item(slot: EquipmentSlot, **kwargs) -> SlotItem:
    """Factory function to create the correct item type for a slot.

    Args:
        slot: The equipment slot.
        **kwargs: Arguments passed to the item constructor.

    Returns:
        A slot-specific item instance.
    """
    item_class = SLOT_ITEM_CLASSES.get(slot, SlotItem)
    return item_class(**kwargs)


@dataclass
class EquipmentLoadout:
    """A complete equipment setup with items in each slot.

    This structure is compatible with RuneLite's Inventory Setups plugin.
    Equipment stats are automatically calculated from equipped items.
    Each slot accepts only items of the correct type.

    Attributes:
        name: Loadout name (e.g., 'Vorkath DHCB').
        head: Helmet/mask slot (HeadItem).
        cape: Cape/cloak slot (CapeItem).
        neck: Amulet/necklace slot (NeckItem).
        ammo: Ammunition slot (AmmoItem).
        weapon: Main weapon slot (WeaponItem).
        body: Body armour slot (BodyItem).
        shield: Shield/off-hand slot (ShieldItem).
        legs: Leg armour slot (LegsItem).
        hands: Gloves slot (HandsItem).
        feet: Boots slot (FeetItem).
        ring: Ring slot (RingItem).
    """
    name: str = ""
    head: Optional[HeadItem] = None
    cape: Optional[CapeItem] = None
    neck: Optional[NeckItem] = None
    ammo: Optional[AmmoItem] = None
    weapon: Optional[WeaponItem] = None
    body: Optional[BodyItem] = None
    shield: Optional[ShieldItem] = None
    legs: Optional[LegsItem] = None
    hands: Optional[HandsItem] = None
    feet: Optional[FeetItem] = None
    ring: Optional[RingItem] = None

    def get_slot(self, slot: EquipmentSlot) -> Optional[SlotItem]:
        """Get the item in a specific slot."""
        return getattr(self, slot.value, None)

    def set_slot(self, slot: EquipmentSlot, item: Optional[SlotItem]) -> None:
        """Set an item in a specific slot.

        Args:
            slot: The equipment slot.
            item: The item to equip (must match slot type or be None).

        Raises:
            TypeError: If item type doesn't match the slot.
        """
        if item is not None and item.SLOT != slot:
            raise TypeError(
                f"Cannot equip {type(item).__name__} in {slot.value} slot. "
                f"Expected {SLOT_ITEM_CLASSES[slot].__name__}."
            )
        setattr(self, slot.value, item)

    def get_all_items(self) -> List[SlotItem]:
        """Get all equipped items (non-None slots)."""
        items = []
        for slot in EquipmentSlot:
            item = self.get_slot(slot)
            if item is not None:
                items.append(item)
        return items

    def get_item_names(self) -> List[str]:
        """Get names of all equipped items (for effect detection)."""
        return [item.name.lower().replace(" ", "_").replace("'", "")
                for item in self.get_all_items()]

    def get_total_stats(self) -> "EquipmentStats":
        """Calculate total equipment stats from all equipped items."""
        total = EquipmentStats()
        for item in self.get_all_items():
            if item.stats:
                total = total + item.stats
        return total

    def is_two_handed(self) -> bool:
        """Check if the equipped weapon is two-handed."""
        return self.weapon is not None and self.weapon.is_two_handed

    @classmethod
    def from_dict(
        cls,
        data: Dict,
        item_loader: "ItemLoader" = None
    ) -> "EquipmentLoadout":
        """Create loadout from a dictionary (e.g., RuneLite export).

        Supports multiple formats:

        1. RuneLite Inventory Setups plugin format (nested):
        {
            "setup": {
                "name": "Setup Name",
                "eq": [{"id": 12345}, {"id": 67890}, null, ...]
            }
        }

        2. Simple positional array format:
        {
            "name": "Setup Name",
            "equipment": [
                {"id": 12345, "name": "Item Name", "quantity": 1},
                {"id": -1, "name": "", "quantity": 0},
                ...
            ]
        }

        3. Explicit slot format:
        {
            "name": "Setup Name",
            "equipment": [
                {"id": 12345, "name": "Item Name", "slot": "HEAD"},
                ...
            ]
        }

        Args:
            data: Dictionary containing equipment data.
            item_loader: Optional ItemLoader to auto-populate equipment stats
                        from items.json using item IDs. Required for format 1
                        to determine item slots and names.

        Returns:
            EquipmentLoadout with items (and stats if item_loader provided).
        """
        # Handle nested RuneLite Inventory Setups format: {"setup": {"eq": [...], "name": ...}}
        if "setup" in data:
            setup = data["setup"]
            name = setup.get("name", "")
            equipment_list = setup.get("eq", [])
            # This format requires item_loader to determine slots
            return cls._from_id_list(equipment_list, name, item_loader)

        loadout = cls(name=data.get("name", ""))
        equipment_list = data.get("equipment", [])

        # Detect format: if first item has "slot" key, use explicit format
        # Otherwise use RuneLite positional format
        uses_explicit_slots = any(
            item_data.get("slot") for item_data in equipment_list if item_data
        )

        if uses_explicit_slots:
            # Explicit slot format
            for item_data in equipment_list:
                if not item_data:
                    continue

                slot_name = item_data.get("slot", "").lower()
                if not slot_name:
                    continue

                try:
                    slot = EquipmentSlot(slot_name)
                except ValueError:
                    continue

                # Skip empty items (id -1 or no name)
                item_id = item_data.get("id", 0)
                item_name = item_data.get("name", "")
                if item_id == -1 or not item_name:
                    continue

                # Look up stats from database if loader provided
                stats = EquipmentStats()
                if item_loader and item_id > 0:
                    stats = item_loader.get_by_id(item_id) or EquipmentStats()

                item = create_slot_item(
                    slot,
                    name=item_name,
                    item_id=item_id,
                    stats=stats,
                )
                loadout.set_slot(slot, item)
        else:
            # RuneLite positional array format
            for index, item_data in enumerate(equipment_list):
                if not item_data:
                    continue
                if index >= len(RUNELITE_SLOT_ORDER):
                    break

                # Skip empty items (id -1 is RuneLite's empty placeholder)
                item_id = item_data.get("id", 0)
                item_name = item_data.get("name", "")
                if item_id == -1 or not item_name:
                    continue

                slot = RUNELITE_SLOT_ORDER[index]

                # Look up stats from database if loader provided
                stats = EquipmentStats()
                if item_loader and item_id > 0:
                    stats = item_loader.get_by_id(item_id) or EquipmentStats()

                item = create_slot_item(
                    slot,
                    name=item_name,
                    item_id=item_id,
                    stats=stats,
                )
                loadout.set_slot(slot, item)

        return loadout

    @classmethod
    def _from_id_list(
        cls,
        id_list: List,
        name: str,
        item_loader: "ItemLoader"
    ) -> "EquipmentLoadout":
        """Create loadout from a list of item IDs (RuneLite eq format).

        This method looks up each item's slot from the database, filtering
        out non-equipment items automatically.

        Args:
            id_list: List of dicts with "id" key, or None for empty slots.
            name: Loadout name.
            item_loader: ItemLoader instance (required for slot/name lookups).

        Returns:
            EquipmentLoadout with equipment items only.
        """
        loadout = cls(name=name)

        if not item_loader:
            # Can't determine slots without item_loader
            return loadout

        for item_data in id_list:
            if not item_data:
                continue

            item_id = item_data.get("id", 0)
            if item_id <= 0:
                continue

            # Look up the item's slot from database
            slot = item_loader.get_slot(item_id)
            if slot is None:
                # Not an equipment item, skip it
                continue

            # Get item name and stats from database
            item_name = item_loader.get_name(item_id) or f"Item {item_id}"
            stats = item_loader.get_by_id(item_id) or EquipmentStats()

            # Build kwargs for the slot item
            kwargs = {
                "name": item_name,
                "item_id": item_id,
                "stats": stats,
            }

            # Add weapon-specific attributes if this is a weapon slot
            if slot == EquipmentSlot.WEAPON:
                attack_speed = item_loader.get_attack_speed(item_id)
                if attack_speed:
                    kwargs["attack_speed"] = attack_speed
                kwargs["is_two_handed"] = item_loader.is_two_handed(item_id)

                # Determine combat style from stats
                if stats.ranged_attack > 0 and stats.ranged_attack >= stats.magic_attack:
                    kwargs["attack_type"] = AttackType.RANGED
                    kwargs["combat_style"] = CombatStyle.RANGED
                elif stats.magic_attack > 0:
                    kwargs["attack_type"] = AttackType.MAGIC
                    kwargs["combat_style"] = CombatStyle.MAGIC
                else:
                    # Pick best melee type
                    best = max(stats.stab_attack, stats.slash_attack, stats.crush_attack)
                    if best == stats.stab_attack:
                        kwargs["attack_type"] = AttackType.STAB
                    elif best == stats.slash_attack:
                        kwargs["attack_type"] = AttackType.SLASH
                    else:
                        kwargs["attack_type"] = AttackType.CRUSH
                    kwargs["combat_style"] = CombatStyle.MELEE

            item = create_slot_item(slot, **kwargs)
            loadout.set_slot(slot, item)

        return loadout

    @classmethod
    def from_runelite_json(
        cls,
        json_str: str,
        item_loader: "ItemLoader" = None
    ) -> "EquipmentLoadout":
        """Create loadout from RuneLite Inventory Setups JSON string.

        Args:
            json_str: JSON string exported from RuneLite.
            item_loader: Optional ItemLoader to auto-populate equipment stats
                        from items.json using item IDs.

        Returns:
            EquipmentLoadout instance with stats (if item_loader provided).
        """
        import json
        data = json.loads(json_str)
        return cls.from_dict(data, item_loader=item_loader)

    def to_dict(self) -> Dict:
        """Export loadout to dictionary format."""
        equipment = []
        for slot in EquipmentSlot:
            item = self.get_slot(slot)
            if item:
                equipment.append({
                    "id": item.item_id,
                    "name": item.name,
                    "slot": slot.value.upper(),
                })
        return {
            "name": self.name,
            "equipment": equipment,
        }


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
        attack_speed=5,  # Default 5-tick; 4-tick with standard spells (handled in calculation)
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


# =============================================================================
# Autocast Spellbook Registry
# =============================================================================
# Maps weapon names (normalized) to the list of spellbooks they can autocast.
# Powered staves (Trident, Sang, Shadow) are NOT in this registry - they use
# their built-in spell via base_magic_max_hit.

def _get_autocast_spellbooks() -> Dict[str, List["Spellbook"]]:
    """Get the autocast spellbook registry.

    Returns a dictionary mapping weapon names to lists of spellbooks they can
    autocast. This is a function to avoid circular imports.
    """
    from data_loader.spell_loader import Spellbook

    return {
        # Standard only - Special spells
        "ibans_staff": [Spellbook.STANDARD],

        # Standard + Arceuus
        "slayers_staff": [Spellbook.STANDARD, Spellbook.ARCEUUS],
        "slayers_staff_e": [Spellbook.STANDARD, Spellbook.ARCEUUS],
        "staff_of_the_dead": [Spellbook.STANDARD, Spellbook.ARCEUUS],
        "toxic_staff_of_the_dead": [Spellbook.STANDARD, Spellbook.ARCEUUS],
        "staff_of_light": [Spellbook.STANDARD],
        "staff_of_balance": [Spellbook.STANDARD],

        # Standard + Ancient
        "ancient_staff": [Spellbook.STANDARD, Spellbook.ANCIENTS],
        "master_wand": [Spellbook.STANDARD, Spellbook.ANCIENTS],
        "kodai_wand": [Spellbook.STANDARD, Spellbook.ANCIENTS],
        "nightmare_staff": [Spellbook.STANDARD, Spellbook.ANCIENTS],
        "harmonised_nightmare_staff": [Spellbook.STANDARD, Spellbook.ANCIENTS],
        "eldritch_nightmare_staff": [Spellbook.STANDARD, Spellbook.ANCIENTS],
        "volatile_nightmare_staff": [Spellbook.STANDARD, Spellbook.ANCIENTS],

        # All three spellbooks
        "ahrims_staff": [Spellbook.STANDARD, Spellbook.ANCIENTS, Spellbook.ARCEUUS],
        "blue_moon_spear": [Spellbook.STANDARD, Spellbook.ANCIENTS, Spellbook.ARCEUUS],

        # Basic staves/wands (Standard elemental spells only)
        "staff_of_air": [Spellbook.STANDARD],
        "staff_of_water": [Spellbook.STANDARD],
        "staff_of_earth": [Spellbook.STANDARD],
        "staff_of_fire": [Spellbook.STANDARD],
        "mystic_air_staff": [Spellbook.STANDARD],
        "mystic_water_staff": [Spellbook.STANDARD],
        "mystic_earth_staff": [Spellbook.STANDARD],
        "mystic_fire_staff": [Spellbook.STANDARD],
        "mud_battlestaff": [Spellbook.STANDARD],
        "lava_battlestaff": [Spellbook.STANDARD],
        "steam_battlestaff": [Spellbook.STANDARD],
        "smoke_battlestaff": [Spellbook.STANDARD],
        "mist_battlestaff": [Spellbook.STANDARD],
        "dust_battlestaff": [Spellbook.STANDARD],
    }


def _get_best_autocast_spell(
    weapon_name: str,
    magic_level: int,
    spellbook: "Spellbook" = None
) -> Optional["Spell"]:
    """Get the strongest spell a weapon can autocast at the given magic level.

    For weapons that support autocasting, this returns the highest-damage spell
    available based on:
    1. The spellbooks the weapon can autocast
    2. The player's magic level
    3. An optional spellbook filter

    Args:
        weapon_name: Name of the weapon (normalized or display name).
        magic_level: Player's magic level.
        spellbook: Optional filter to a specific spellbook. If None, checks
                   all spellbooks the weapon can autocast.

    Returns:
        The strongest available Spell, or None if:
        - The weapon is a powered staff (uses built-in spell)
        - The weapon cannot autocast any spells
        - No spells are available at the player's magic level
    """
    from data_loader.spell_loader import Spellbook, get_strongest_spell

    # Normalize weapon name
    weapon_key = weapon_name.lower().replace(" ", "_").replace("'", "")

    # Get spellbooks this weapon can autocast
    autocast_registry = _get_autocast_spellbooks()
    weapon_spellbooks = autocast_registry.get(weapon_key)

    if weapon_spellbooks is None:
        # Weapon not in registry - likely a powered staff or can't autocast
        return None

    # If a specific spellbook is requested, check if weapon supports it
    if spellbook is not None:
        if spellbook not in weapon_spellbooks:
            return None
        return get_strongest_spell(magic_level, spellbook)

    # Find the strongest spell across all supported spellbooks
    best_spell = None
    for book in weapon_spellbooks:
        spell = get_strongest_spell(magic_level, book)
        if spell is not None:
            if best_spell is None or spell.base_max_hit > best_spell.base_max_hit:
                best_spell = spell

    return best_spell


# =============================================================================
# Ammo Definitions
# =============================================================================

@dataclass
class Ammo:
    """Ammunition stats for ranged weapons.

    Attributes:
        name: Display name.
        ranged_strength: Ranged strength bonus.
        ranged_attack: Ranged attack bonus (some ammo has this).
        is_enchanted: Whether this is an enchanted bolt/arrow.
        enchant_proc_chance: Base proc chance for enchanted effect.
        enchant_proc_chance_diary: Proc chance with Kandarin hard diary.
    """
    name: str
    ranged_strength: int
    ranged_attack: int = 0
    is_enchanted: bool = False
    enchant_proc_chance: float = 0.0
    enchant_proc_chance_diary: float = 0.0


AMMO: Dict[str, Ammo] = {
    # -------------------------------------------------------------------------
    # Arrows
    # -------------------------------------------------------------------------
    "bronze_arrow": Ammo(name="Bronze arrow", ranged_strength=7),
    "iron_arrow": Ammo(name="Iron arrow", ranged_strength=10),
    "steel_arrow": Ammo(name="Steel arrow", ranged_strength=16),
    "mithril_arrow": Ammo(name="Mithril arrow", ranged_strength=22),
    "adamant_arrow": Ammo(name="Adamant arrow", ranged_strength=31),
    "rune_arrow": Ammo(name="Rune arrow", ranged_strength=49),
    "amethyst_arrow": Ammo(name="Amethyst arrow", ranged_strength=55),
    "dragon_arrow": Ammo(name="Dragon arrow", ranged_strength=60),

    # -------------------------------------------------------------------------
    # Bolts (unenchanted)
    # -------------------------------------------------------------------------
    "bronze_bolts": Ammo(name="Bronze bolts", ranged_strength=10),
    "iron_bolts": Ammo(name="Iron bolts", ranged_strength=46),
    "steel_bolts": Ammo(name="Steel bolts", ranged_strength=64),
    "mithril_bolts": Ammo(name="Mithril bolts", ranged_strength=82),
    "adamant_bolts": Ammo(name="Adamant bolts", ranged_strength=100),
    "runite_bolts": Ammo(name="Runite bolts", ranged_strength=115),
    "dragon_bolts": Ammo(name="Dragon bolts", ranged_strength=122),

    # -------------------------------------------------------------------------
    # Enchanted Bolts (gem-tipped)
    # -------------------------------------------------------------------------
    "opal_bolts_e": Ammo(
        name="Opal bolts (e)", ranged_strength=14,
        is_enchanted=True, enchant_proc_chance=0.05, enchant_proc_chance_diary=0.075,
    ),
    "jade_bolts_e": Ammo(
        name="Jade bolts (e)", ranged_strength=28,
        is_enchanted=True, enchant_proc_chance=0.06, enchant_proc_chance_diary=0.11,
    ),
    "pearl_bolts_e": Ammo(
        name="Pearl bolts (e)", ranged_strength=48,
        is_enchanted=True, enchant_proc_chance=0.06, enchant_proc_chance_diary=0.11,
    ),
    "topaz_bolts_e": Ammo(
        name="Topaz bolts (e)", ranged_strength=66,
        is_enchanted=True, enchant_proc_chance=0.04, enchant_proc_chance_diary=0.06,
    ),
    "sapphire_bolts_e": Ammo(
        name="Sapphire bolts (e)", ranged_strength=83,
        is_enchanted=True, enchant_proc_chance=0.05, enchant_proc_chance_diary=0.075,
    ),
    "emerald_bolts_e": Ammo(
        name="Emerald bolts (e)", ranged_strength=85,
        is_enchanted=True, enchant_proc_chance=0.55, enchant_proc_chance_diary=0.575,  # 55% base
    ),
    "ruby_bolts_e": Ammo(
        name="Ruby bolts (e)", ranged_strength=103,
        is_enchanted=True, enchant_proc_chance=0.06, enchant_proc_chance_diary=0.11,
    ),
    "diamond_bolts_e": Ammo(
        name="Diamond bolts (e)", ranged_strength=105,
        is_enchanted=True, enchant_proc_chance=0.10, enchant_proc_chance_diary=0.15,
    ),
    "dragonstone_bolts_e": Ammo(
        name="Dragonstone bolts (e)", ranged_strength=117,
        is_enchanted=True, enchant_proc_chance=0.06, enchant_proc_chance_diary=0.11,
    ),
    "onyx_bolts_e": Ammo(
        name="Onyx bolts (e)", ranged_strength=120,
        is_enchanted=True, enchant_proc_chance=0.11, enchant_proc_chance_diary=0.165,
    ),

    # Dragon gem-tipped bolts
    "opal_dragon_bolts_e": Ammo(
        name="Opal dragon bolts (e)", ranged_strength=14 + 108,
        is_enchanted=True, enchant_proc_chance=0.05, enchant_proc_chance_diary=0.075,
    ),
    "jade_dragon_bolts_e": Ammo(
        name="Jade dragon bolts (e)", ranged_strength=28 + 94,
        is_enchanted=True, enchant_proc_chance=0.06, enchant_proc_chance_diary=0.11,
    ),
    "pearl_dragon_bolts_e": Ammo(
        name="Pearl dragon bolts (e)", ranged_strength=48 + 74,
        is_enchanted=True, enchant_proc_chance=0.06, enchant_proc_chance_diary=0.11,
    ),
    "topaz_dragon_bolts_e": Ammo(
        name="Topaz dragon bolts (e)", ranged_strength=66 + 56,
        is_enchanted=True, enchant_proc_chance=0.04, enchant_proc_chance_diary=0.06,
    ),
    "sapphire_dragon_bolts_e": Ammo(
        name="Sapphire dragon bolts (e)", ranged_strength=83 + 39,
        is_enchanted=True, enchant_proc_chance=0.05, enchant_proc_chance_diary=0.075,
    ),
    "emerald_dragon_bolts_e": Ammo(
        name="Emerald dragon bolts (e)", ranged_strength=85 + 37,
        is_enchanted=True, enchant_proc_chance=0.55, enchant_proc_chance_diary=0.575,
    ),
    "ruby_dragon_bolts_e": Ammo(
        name="Ruby dragon bolts (e)", ranged_strength=103 + 19,
        is_enchanted=True, enchant_proc_chance=0.06, enchant_proc_chance_diary=0.11,
    ),
    "diamond_dragon_bolts_e": Ammo(
        name="Diamond dragon bolts (e)", ranged_strength=105 + 17,
        is_enchanted=True, enchant_proc_chance=0.10, enchant_proc_chance_diary=0.15,
    ),
    "dragonstone_dragon_bolts_e": Ammo(
        name="Dragonstone dragon bolts (e)", ranged_strength=117 + 5,
        is_enchanted=True, enchant_proc_chance=0.06, enchant_proc_chance_diary=0.11,
    ),
    "onyx_dragon_bolts_e": Ammo(
        name="Onyx dragon bolts (e)", ranged_strength=120 + 2,
        is_enchanted=True, enchant_proc_chance=0.11, enchant_proc_chance_diary=0.165,
    ),

    # -------------------------------------------------------------------------
    # Darts
    # -------------------------------------------------------------------------
    "bronze_dart": Ammo(name="Bronze dart", ranged_strength=1, ranged_attack=0),
    "iron_dart": Ammo(name="Iron dart", ranged_strength=3, ranged_attack=2),
    "steel_dart": Ammo(name="Steel dart", ranged_strength=4, ranged_attack=3),
    "mithril_dart": Ammo(name="Mithril dart", ranged_strength=7, ranged_attack=4),
    "adamant_dart": Ammo(name="Adamant dart", ranged_strength=10, ranged_attack=6),
    "rune_dart": Ammo(name="Rune dart", ranged_strength=14, ranged_attack=7),
    "amethyst_dart": Ammo(name="Amethyst dart", ranged_strength=18, ranged_attack=6),
    "dragon_dart": Ammo(name="Dragon dart", ranged_strength=20, ranged_attack=7),

    # -------------------------------------------------------------------------
    # Thrown Weapons / Javelins
    # -------------------------------------------------------------------------
    "dragon_javelin": Ammo(name="Dragon javelin", ranged_strength=150),
    "amethyst_javelin": Ammo(name="Amethyst javelin", ranged_strength=135),
    "rune_javelin": Ammo(name="Rune javelin", ranged_strength=124),

    # -------------------------------------------------------------------------
    # Special Ammo
    # -------------------------------------------------------------------------
    "broad_bolts": Ammo(name="Broad bolts", ranged_strength=100),
    "amethyst_broad_bolts": Ammo(name="Amethyst broad bolts", ranged_strength=115),
}


def get_ammo(name: str) -> Optional[Ammo]:
    """Get ammo by its key name.

    Args:
        name: The ammo's key name (e.g., 'dragon_arrow').

    Returns:
        The Ammo object, or None if not found.
    """
    normalized = name.lower().replace(" ", "_").replace("'", "").replace("(", "").replace(")", "")
    if normalized in AMMO:
        return AMMO[normalized]
    return None


def list_ammo() -> List[str]:
    """List all available ammo names.

    Returns:
        List of ammo key names.
    """
    return list(AMMO.keys())


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


def extract_equippable_ids(
    data: Dict,
    item_loader: "ItemLoader"
) -> List[int]:
    """Extract all equippable item IDs from a RuneLite setup.

    Parses both equipped items (eq) and inventory items (inv), returning
    only items that are actually equippable.

    Args:
        data: RuneLite setup dictionary (with "setup" key or raw format).
        item_loader: ItemLoader instance for checking if items are equippable.

    Returns:
        List of unique equippable item IDs.
    """
    item_ids = set()

    # Handle nested format
    if "setup" in data:
        setup = data["setup"]
        arrays_to_check = [
            setup.get("eq", []),
            setup.get("inv", []),
        ]
    else:
        arrays_to_check = [data.get("equipment", [])]

    for item_list in arrays_to_check:
        for item_data in item_list:
            if not item_data:
                continue
            item_id = item_data.get("id", 0)
            if item_id <= 0:
                continue
            # Only include if it's equippable
            if item_loader.get_slot(item_id) is not None:
                item_ids.add(item_id)

    return list(item_ids)


def format_loadout_summary(
    loadout: "EquipmentLoadout",
    combat_result: "CombatResult" = None,
    width: int = 60
) -> str:
    """Format a loadout's stats as a readable summary in an ASCII box.

    Displays equipment in a visual layout similar to the in-game
    equipment screen. Optionally includes DPS calculation results.

    Args:
        loadout: The equipment loadout to summarize.
        combat_result: Optional CombatResult to display DPS info.
        width: Width of the box (default 60).

    Returns:
        Formatted string with equipment and stats in an ASCII box.
    """
    inner = width - 4  # Account for "| " and " |"

    def line(text: str) -> str:
        return f"| {text:<{inner}} |"

    def center_line(text: str) -> str:
        return f"| {text:^{inner}} |"

    def divider() -> str:
        return f"+{'-' * (width - 2)}+"

    def get_item_name(slot: EquipmentSlot, max_len: int = 14) -> str:
        item = loadout.get_slot(slot)
        if item:
            name = item.name
            if len(name) > max_len:
                return name[:max_len-1] + "."
            return name
        return ""

    def slot_box(slot: EquipmentSlot) -> str:
        """Create a mini box for a slot."""
        name = get_item_name(slot, 14)
        return f"[{name:^14}]"

    def empty_box() -> str:
        return " " * 16

    lines = []

    # Top border with title
    title = f" {loadout.name or 'Loadout'} "
    padding = width - 2 - len(title)
    left_pad = padding // 2
    right_pad = padding - left_pad
    lines.append(f"+{'-' * left_pad}{title}{'-' * right_pad}+")

    # Equipment visual layout (like in-game)
    # Row 1: Head (center)
    head = slot_box(EquipmentSlot.HEAD)
    lines.append(center_line(head))

    # Row 2: Cape, Neck, Ammo
    cape = slot_box(EquipmentSlot.CAPE)
    neck = slot_box(EquipmentSlot.NECK)
    ammo = slot_box(EquipmentSlot.AMMO)
    row2 = f"{cape}  {neck}  {ammo}"
    lines.append(center_line(row2))

    # Row 3: Weapon, Body, Shield
    weapon = slot_box(EquipmentSlot.WEAPON)
    body = slot_box(EquipmentSlot.BODY)
    shield = slot_box(EquipmentSlot.SHIELD)
    row3 = f"{weapon}  {body}  {shield}"
    lines.append(center_line(row3))

    # Row 4: Legs (center)
    legs = slot_box(EquipmentSlot.LEGS)
    row4 = f"{empty_box()}  {legs}  {empty_box()}"
    lines.append(center_line(row4))

    # Row 5: Hands, Feet
    hands = slot_box(EquipmentSlot.HANDS)
    feet = slot_box(EquipmentSlot.FEET)
    row5 = f"{hands}  {empty_box()}  {feet}"
    lines.append(center_line(row5))

    # Row 6: Ring (center)
    ring = slot_box(EquipmentSlot.RING)
    row6 = f"{empty_box()}  {ring}  {empty_box()}"
    lines.append(center_line(row6))

    # Equipment list (full names)
    lines.append(divider())
    lines.append(line("  EQUIPMENT LIST"))
    lines.append(divider())

    slot_order = [
        (EquipmentSlot.HEAD, "Head"),
        (EquipmentSlot.CAPE, "Cape"),
        (EquipmentSlot.NECK, "Neck"),
        (EquipmentSlot.AMMO, "Ammo"),
        (EquipmentSlot.WEAPON, "Weapon"),
        (EquipmentSlot.BODY, "Body"),
        (EquipmentSlot.SHIELD, "Shield"),
        (EquipmentSlot.LEGS, "Legs"),
        (EquipmentSlot.HANDS, "Hands"),
        (EquipmentSlot.FEET, "Feet"),
        (EquipmentSlot.RING, "Ring"),
    ]

    for slot, slot_name in slot_order:
        item = loadout.get_slot(slot)
        if item:
            lines.append(line(f"  {slot_name:<7} {item.name}"))

    # Stats section
    stats = loadout.get_total_stats()
    lines.append(divider())

    # Headers
    lines.append(line("  ATTACK          DEFENCE          OTHER"))
    lines.append(divider())
    lines.append(line(f"  Stab:   {stats.stab_attack:+4d}      Stab:   {stats.stab_defence:+4d}      Melee Str:  {stats.melee_strength:+4d}"))
    lines.append(line(f"  Slash:  {stats.slash_attack:+4d}      Slash:  {stats.slash_defence:+4d}      Ranged Str: {stats.ranged_strength:+4d}"))
    lines.append(line(f"  Crush:  {stats.crush_attack:+4d}      Crush:  {stats.crush_defence:+4d}      Magic Dmg:  {stats.magic_damage:+.1%}"))
    lines.append(line(f"  Ranged: {stats.ranged_attack:+4d}      Ranged: {stats.ranged_defence:+4d}      Prayer:     {stats.prayer:+4d}"))
    lines.append(line(f"  Magic:  {stats.magic_attack:+4d}      Magic:  {stats.magic_defence:+4d}"))

    # DPS section (optional)
    if combat_result:
        lines.append(divider())
        lines.append(line("  DPS CALCULATION"))
        lines.append(divider())
        lines.append(line(f"  DPS:        {combat_result.dps:.2f}"))
        lines.append(line(f"  Max Hit:    {combat_result.max_hit}"))
        lines.append(line(f"  Hit Chance: {combat_result.hit_chance:.1%}"))
        lines.append(line(f"  Atk Speed:  {combat_result.attack_speed_ticks} ticks ({combat_result.attack_speed_seconds:.1f}s)"))
        if combat_result.weapon_name:
            lines.append(line(f"  Weapon:     {combat_result.weapon_name}"))
        if combat_result.spell_used:
            lines.append(line(f"  Spell:      {combat_result.spell_used}"))

    # Bottom border
    lines.append(f"+{'-' * (width - 2)}+")

    return "\n".join(lines)


def optimize_loadouts(
    available_item_ids: List[int],
    attack_types: List[AttackType],
    item_loader: "ItemLoader",
    exclude_slots: List[EquipmentSlot] = None,
) -> Dict[AttackType, "EquipmentLoadout"]:
    """Find optimal gear for multiple attack styles.

    Args:
        available_item_ids: List of item IDs the player has access to.
        attack_types: List of attack types to optimize for.
        item_loader: ItemLoader instance with loaded items.json.
        exclude_slots: Slots to leave empty.

    Returns:
        Dictionary mapping each attack type to its optimal loadout.
    """
    results = {}
    for attack_type in attack_types:
        results[attack_type] = optimize_loadout(
            available_item_ids, attack_type, item_loader, exclude_slots
        )
    return results


def calculate_optimization_score(item_data: Dict, attack_type: AttackType) -> float:
    """Calculate optimization score for an item based on attack type.

    The score combines attack bonus with strength bonus for the given style.

    Args:
        item_data: Full item data dictionary from items.json.
        attack_type: The attack type to optimize for.

    Returns:
        Optimization score (higher is better).
    """
    equip = item_data.get("equipment") or {}

    if attack_type == AttackType.STAB:
        return equip.get("attack_stab", 0) + equip.get("melee_strength", 0)
    elif attack_type == AttackType.SLASH:
        return equip.get("attack_slash", 0) + equip.get("melee_strength", 0)
    elif attack_type == AttackType.CRUSH:
        return equip.get("attack_crush", 0) + equip.get("melee_strength", 0)
    elif attack_type == AttackType.RANGED:
        return equip.get("attack_ranged", 0) + equip.get("ranged_strength", 0)
    elif attack_type == AttackType.MAGIC:
        # Convert magic damage percentage to comparable value
        return equip.get("attack_magic", 0) + equip.get("magic_damage", 0) * 100
    return 0


def optimize_loadout_dps(
    available_item_ids: List[int],
    target: "MonsterStats",
    player_stats: "CombatStats",
    item_loader: "ItemLoader",
    prayer: "Prayer" = None,
    potion: "PotionBoost" = None,
    attack_style: AttackStyle = None,
    on_slayer_task: bool = False,
    spell: "Spell" = None,
    spellbook: "Spellbook" = None,
) -> tuple:
    """Find optimal gear for maximum DPS against a specific target.

    Uses a greedy slot-by-slot optimization approach:
    1. Find the best weapon first (most impactful slot)
    2. For each remaining slot, pick the item that maximizes DPS

    This accounts for:
    - Monster defences (different monsters weak to different styles)
    - Special weapon effects (Dragon Hunter Lance vs dragons, etc.)
    - Player stats, prayers, and potions
    - Set bonuses and passive effects
    - Autocast spell selection for magic weapons

    Args:
        available_item_ids: List of item IDs the player has access to.
        target: The monster to optimize DPS against.
        player_stats: Player's combat stats.
        item_loader: ItemLoader instance with loaded items.json.
        prayer: Prayer to use (defaults to best prayer for weapon style).
        potion: Potion boost (defaults to best potion for weapon style).
        attack_style: Attack style override (defaults to style matching weapon).
        on_slayer_task: Whether on a slayer task for this monster.
        spell: Explicit spell to use (for magic weapons). If None, auto-selects
               the best spell the weapon can autocast.
        spellbook: Restrict spell auto-selection to a specific spellbook.

    Returns:
        Tuple of (best_loadout, combat_result) where combat_result includes
        DPS, max hit, hit chance, spell_used, etc.

    Example:
        >>> from data_loader import ItemLoader
        >>> from combat import CombatStats, get_monster, PIETY, PotionBoost
        >>> item_loader = ItemLoader()
        >>> player_stats = CombatStats(attack=99, strength=99, defence=99)
        >>> target = get_monster("vorkath")
        >>> best_loadout, result = optimize_loadout_dps(
        ...     available_item_ids=[26382, 27745, 22978],
        ...     target=target,
        ...     player_stats=player_stats,
        ...     item_loader=item_loader,
        ...     prayer=PIETY,
        ... )
        >>> print(f"DPS: {result.dps:.2f}")
    """
    from collections import defaultdict
    from .simulation import CombatSetup, CombatCalculator, CombatStats, PotionBoost as PotBoost
    from .prayers import Prayer as Pr, PIETY, RIGOUR, AUGURY
    from .entities import MonsterStats

    # Group items by slot
    slot_items: Dict[EquipmentSlot, List[int]] = defaultdict(list)
    for item_id in available_item_ids:
        slot = item_loader.get_slot(item_id)
        if slot is not None:
            slot_items[slot].append(item_id)

    # Phase 1: Find the best weapon
    best_weapon_id = None
    best_weapon_dps = -1.0
    best_weapon_style = None

    for item_id in slot_items.get(EquipmentSlot.WEAPON, []):
        loadout = _create_loadout_with_weapon(item_id, item_loader)
        if loadout.weapon is None:
            continue

        # Determine prayer and potion for this weapon's style
        weapon_style = loadout.weapon.combat_style
        test_prayer = prayer
        test_potion = potion
        test_attack_style = attack_style

        if test_prayer is None:
            if weapon_style == CombatStyle.MELEE:
                test_prayer = PIETY
            elif weapon_style == CombatStyle.RANGED:
                test_prayer = RIGOUR
            else:
                test_prayer = AUGURY

        if test_potion is None:
            if weapon_style == CombatStyle.MELEE:
                test_potion = PotBoost.super_combat()
            elif weapon_style == CombatStyle.RANGED:
                test_potion = PotBoost.divine_ranging()
            else:
                test_potion = PotBoost.saturated_heart()

        if test_attack_style is None:
            if weapon_style == CombatStyle.MELEE:
                test_attack_style = AttackStyle.AGGRESSIVE
            elif weapon_style == CombatStyle.RANGED:
                test_attack_style = AttackStyle.RAPID
            else:
                test_attack_style = AttackStyle.AUTOCAST

        result = _calculate_loadout_dps(
            loadout, target, player_stats, item_loader,
            test_prayer, test_potion, test_attack_style, on_slayer_task,
            spell, spellbook
        )

        if result.dps > best_weapon_dps:
            best_weapon_dps = result.dps
            best_weapon_id = item_id
            best_weapon_style = weapon_style

    # If no weapon found, return empty result
    if best_weapon_id is None:
        empty_loadout = EquipmentLoadout(name="No weapons available")
        from .simulation import CombatResult
        return empty_loadout, CombatResult(
            dps=0.0, max_hit=0, hit_chance=0.0, attack_roll=0, defence_roll=0
        )

    # Phase 2: Optimize other slots with best weapon locked in
    current_loadout = _create_loadout_with_weapon(best_weapon_id, item_loader)
    current_loadout.name = f"Optimized for {target.name}"

    # Determine final prayer, potion, attack style based on best weapon
    if prayer is None:
        if best_weapon_style == CombatStyle.MELEE:
            prayer = PIETY
        elif best_weapon_style == CombatStyle.RANGED:
            prayer = RIGOUR
        else:
            prayer = AUGURY

    if potion is None:
        if best_weapon_style == CombatStyle.MELEE:
            potion = PotBoost.super_combat()
        elif best_weapon_style == CombatStyle.RANGED:
            potion = PotBoost.divine_ranging()
        else:
            potion = PotBoost.saturated_heart()

    if attack_style is None:
        if best_weapon_style == CombatStyle.MELEE:
            attack_style = AttackStyle.AGGRESSIVE
        elif best_weapon_style == CombatStyle.RANGED:
            attack_style = AttackStyle.RAPID
        else:
            attack_style = AttackStyle.AUTOCAST

    # Slot optimization order (weapon already done)
    slot_order = [
        EquipmentSlot.BODY,
        EquipmentSlot.LEGS,
        EquipmentSlot.HEAD,
        EquipmentSlot.HANDS,
        EquipmentSlot.FEET,
        EquipmentSlot.CAPE,
        EquipmentSlot.NECK,
        EquipmentSlot.RING,
        EquipmentSlot.SHIELD,
        EquipmentSlot.AMMO,
    ]

    # Skip shield if weapon is two-handed
    if current_loadout.is_two_handed():
        slot_order = [s for s in slot_order if s != EquipmentSlot.SHIELD]

    for slot in slot_order:
        if slot not in slot_items or not slot_items[slot]:
            continue

        best_slot_dps = -1.0
        best_slot_item_id = None
        current_dps = _calculate_loadout_dps(
            current_loadout, target, player_stats, item_loader,
            prayer, potion, attack_style, on_slayer_task,
            spell, spellbook
        ).dps

        for item_id in slot_items[slot]:
            # Skip two-handed check for shield slot
            if slot == EquipmentSlot.SHIELD and current_loadout.is_two_handed():
                continue

            test_loadout = _copy_loadout(current_loadout)
            _add_item_to_loadout(test_loadout, item_id, item_loader)

            result = _calculate_loadout_dps(
                test_loadout, target, player_stats, item_loader,
                prayer, potion, attack_style, on_slayer_task,
                spell, spellbook
            )

            if result.dps > best_slot_dps:
                best_slot_dps = result.dps
                best_slot_item_id = item_id

        # Only add item if it improves DPS (or if slot was empty)
        if best_slot_item_id is not None and best_slot_dps >= current_dps:
            _add_item_to_loadout(current_loadout, best_slot_item_id, item_loader)

    # Calculate final result
    final_result = _calculate_loadout_dps(
        current_loadout, target, player_stats, item_loader,
        prayer, potion, attack_style, on_slayer_task,
        spell, spellbook
    )

    return current_loadout, final_result


def _create_loadout_with_weapon(
    weapon_id: int,
    item_loader: "ItemLoader"
) -> EquipmentLoadout:
    """Create an empty loadout with just a weapon equipped.

    Args:
        weapon_id: The weapon item ID.
        item_loader: ItemLoader for looking up item data.

    Returns:
        EquipmentLoadout with only the weapon slot filled.
    """
    loadout = EquipmentLoadout()

    item_data = item_loader.get_item_data(weapon_id)
    if not item_data:
        return loadout

    stats = item_loader.get_by_id(weapon_id) or EquipmentStats()
    name = item_data.get("name", "")
    weap = item_data.get("weapon") or {}
    equip = item_data.get("equipment") or {}

    # Determine attack type and combat style
    attack_type = AttackType.SLASH
    combat_style = CombatStyle.MELEE

    if stats.ranged_attack > 0 and stats.ranged_attack >= stats.magic_attack:
        attack_type = AttackType.RANGED
        combat_style = CombatStyle.RANGED
    elif stats.magic_attack > 0:
        attack_type = AttackType.MAGIC
        combat_style = CombatStyle.MAGIC
    else:
        # Pick best melee type
        best = max(stats.stab_attack, stats.slash_attack, stats.crush_attack)
        if best == stats.stab_attack:
            attack_type = AttackType.STAB
        elif best == stats.slash_attack:
            attack_type = AttackType.SLASH
        else:
            attack_type = AttackType.CRUSH

    # Check if this is a powered staff with a built-in spell max hit
    # Look up in hardcoded WEAPONS dictionary first
    weapon_key = name.lower().replace(" ", "_").replace("'", "")
    base_magic_max_hit = 0
    if weapon_key in WEAPONS:
        base_magic_max_hit = WEAPONS[weapon_key].base_magic_max_hit

    weapon_item = WeaponItem(
        name=name,
        item_id=weapon_id,
        stats=stats,
        attack_speed=weap.get("attack_speed", 4),
        attack_type=attack_type,
        combat_style=combat_style,
        is_two_handed=equip.get("slot") == "2h",
        base_magic_max_hit=base_magic_max_hit,
    )

    loadout.weapon = weapon_item
    return loadout


def _add_item_to_loadout(
    loadout: EquipmentLoadout,
    item_id: int,
    item_loader: "ItemLoader"
) -> None:
    """Add an item to a loadout in-place.

    Args:
        loadout: The loadout to modify.
        item_id: The item ID to add.
        item_loader: ItemLoader for looking up item data.
    """
    slot = item_loader.get_slot(item_id)
    if slot is None:
        return

    item_data = item_loader.get_item_data(item_id)
    if not item_data:
        return

    stats = item_loader.get_by_id(item_id) or EquipmentStats()
    name = item_data.get("name", "")

    kwargs = {
        "name": name,
        "item_id": item_id,
        "stats": stats,
    }

    item = create_slot_item(slot, **kwargs)
    loadout.set_slot(slot, item)


def _copy_loadout(loadout: EquipmentLoadout) -> EquipmentLoadout:
    """Create a shallow copy of a loadout.

    Args:
        loadout: The loadout to copy.

    Returns:
        A new EquipmentLoadout with the same items.
    """
    new_loadout = EquipmentLoadout(name=loadout.name)
    for slot in EquipmentSlot:
        item = loadout.get_slot(slot)
        if item is not None:
            new_loadout.set_slot(slot, item)
    return new_loadout


def _detect_gear_modifiers(
    loadout: EquipmentLoadout,
    target: "MonsterStats"
) -> GearModifiers:
    """Detect special gear effects from equipped items.

    Args:
        loadout: The equipment loadout.
        target: The target monster.

    Returns:
        GearModifiers with detected effects.
    """
    item_names = [name.lower() for name in loadout.get_item_names()]

    # Void set detection
    void_melee = _has_void_melee(item_names)
    void_ranged = _has_void_ranged(item_names)
    void_magic = _has_void_magic(item_names)
    elite_void = _has_elite_void(item_names)

    # Slayer helm detection
    slayer_helm = any("slayer_helmet" in name or "black_mask" in name for name in item_names)
    slayer_helm_imbued = any(
        "slayer_helmet_(i)" in name or "slayer_helmet_i" in name or
        "black_mask_(i)" in name or "black_mask_i" in name
        for name in item_names
    )

    # Salve amulet detection (check if target is undead)
    is_undead = target.is_undead if target else False
    salve = any("salve_amulet" in name and "(e)" not in name and "ei" not in name for name in item_names)
    salve_e = any("salve_amulet(e)" in name or "salve_amulet_e" in name for name in item_names)
    salve_ei = any("salve_amulet(ei)" in name or "salve_amulet_ei" in name for name in item_names)

    # Dragon hunter detection (check if target is dragon)
    is_dragon = target.is_dragon if target else False
    dhl = any("dragon_hunter_lance" in name for name in item_names)
    dhcb = any("dragon_hunter_crossbow" in name for name in item_names)

    # Set bonuses
    inquisitor = _has_inquisitor_set(item_names)
    obsidian = _has_obsidian_set(item_names)

    return GearModifiers(
        void_melee=void_melee,
        void_ranged=void_ranged,
        void_magic=void_magic,
        elite_void=elite_void,
        slayer_helm=slayer_helm,
        slayer_helm_imbued=slayer_helm_imbued,
        salve_amulet=salve and is_undead,
        salve_amulet_e=salve_e and is_undead,
        salve_amulet_ei=salve_ei and is_undead,
        dragon_hunter_lance=dhl and is_dragon,
        dragon_hunter_crossbow=dhcb and is_dragon,
        inquisitor_set=inquisitor,
        obsidian_set=obsidian,
    )


def _has_void_melee(item_names: List[str]) -> bool:
    """Check for melee void set."""
    has_helm = any("void_melee_helm" in name for name in item_names)
    has_top = any("void_knight_top" in name or "elite_void_top" in name for name in item_names)
    has_robe = any("void_knight_robe" in name or "elite_void_robe" in name for name in item_names)
    has_gloves = any("void_knight_gloves" in name for name in item_names)
    return has_helm and has_top and has_robe and has_gloves


def _has_void_ranged(item_names: List[str]) -> bool:
    """Check for ranged void set."""
    has_helm = any("void_ranger_helm" in name for name in item_names)
    has_top = any("void_knight_top" in name or "elite_void_top" in name for name in item_names)
    has_robe = any("void_knight_robe" in name or "elite_void_robe" in name for name in item_names)
    has_gloves = any("void_knight_gloves" in name for name in item_names)
    return has_helm and has_top and has_robe and has_gloves


def _has_void_magic(item_names: List[str]) -> bool:
    """Check for magic void set."""
    has_helm = any("void_mage_helm" in name for name in item_names)
    has_top = any("void_knight_top" in name or "elite_void_top" in name for name in item_names)
    has_robe = any("void_knight_robe" in name or "elite_void_robe" in name for name in item_names)
    has_gloves = any("void_knight_gloves" in name for name in item_names)
    return has_helm and has_top and has_robe and has_gloves


def _has_elite_void(item_names: List[str]) -> bool:
    """Check for elite void pieces."""
    has_elite_top = any("elite_void_top" in name for name in item_names)
    has_elite_robe = any("elite_void_robe" in name for name in item_names)
    return has_elite_top and has_elite_robe


def _has_inquisitor_set(item_names: List[str]) -> bool:
    """Check for full Inquisitor's set."""
    has_helm = any("inquisitors_great_helm" in name or "inquisitor's_great_helm" in name for name in item_names)
    has_body = any("inquisitors_hauberk" in name or "inquisitor's_hauberk" in name for name in item_names)
    has_legs = any("inquisitors_plateskirt" in name or "inquisitor's_plateskirt" in name for name in item_names)
    return has_helm and has_body and has_legs


def _has_obsidian_set(item_names: List[str]) -> bool:
    """Check for full Obsidian armour set with obsidian weapon."""
    has_helm = any("obsidian_helmet" in name for name in item_names)
    has_body = any("obsidian_platebody" in name for name in item_names)
    has_legs = any("obsidian_platelegs" in name for name in item_names)
    has_weapon = any(
        "toktz" in name or "tzhaar" in name or "obsidian" in name
        for name in item_names
        if "helmet" not in name and "platebody" not in name and "platelegs" not in name
    )
    return has_helm and has_body and has_legs and has_weapon


def _calculate_loadout_dps(
    loadout: EquipmentLoadout,
    target: "MonsterStats",
    player_stats: "CombatStats",
    item_loader: "ItemLoader",
    prayer: "Prayer",
    potion: "PotionBoost",
    attack_style: AttackStyle,
    on_slayer_task: bool,
    spell: "Spell" = None,
    spellbook: "Spellbook" = None,
) -> "CombatResult":
    """Calculate DPS for a loadout against a target.

    Args:
        loadout: The equipment loadout.
        target: The target monster.
        player_stats: Player's combat stats.
        item_loader: ItemLoader (unused but kept for consistency).
        prayer: Prayer to use.
        potion: Potion boost.
        attack_style: Attack style.
        on_slayer_task: Whether on slayer task.
        spell: Explicit spell override for magic weapons.
        spellbook: Restrict autocast selection to a specific spellbook.

    Returns:
        CombatResult with DPS and other stats.
    """
    from .simulation import CombatSetup, CombatCalculator, CombatResult
    from data_loader.spell_loader import Spellbook

    if loadout.weapon is None:
        return CombatResult(
            dps=0.0, max_hit=0, hit_chance=0.0, attack_roll=0, defence_roll=0
        )

    weapon_name = loadout.weapon.name
    weapon_key = weapon_name.lower().replace(" ", "_").replace("'", "")
    attack_speed = loadout.weapon.attack_speed
    base_magic_max_hit = getattr(loadout.weapon, 'base_magic_max_hit', 0)

    # For magic weapons without a built-in spell (not powered staves),
    # auto-select the best spell if none is explicitly provided
    selected_spell = spell
    if loadout.weapon.combat_style == CombatStyle.MAGIC and base_magic_max_hit == 0:
        if selected_spell is None:
            selected_spell = _get_best_autocast_spell(
                weapon_name,
                player_stats.magic,
                spellbook
            )

        # Harmonised Nightmare Staff: 4-tick attack speed for standard spells
        if (weapon_key == "harmonised_nightmare_staff" and
                selected_spell is not None and
                selected_spell.spellbook == Spellbook.STANDARD):
            attack_speed = 4

    # Build Weapon object from WeaponItem
    weapon = Weapon(
        name=loadout.weapon.name,
        attack_speed=attack_speed,
        attack_type=loadout.weapon.attack_type,
        combat_style=loadout.weapon.combat_style,
        stats=EquipmentStats(),  # Don't include weapon stats here - they're added separately
        is_two_handed=loadout.weapon.is_two_handed,
        base_magic_max_hit=base_magic_max_hit,
    )

    # Get total equipment stats (includes weapon stats)
    equipment_stats = loadout.get_total_stats()

    # Detect gear modifiers
    gear_modifiers = _detect_gear_modifiers(loadout, target)

    # Get item names for effect detection
    equipped_items = loadout.get_item_names()

    setup = CombatSetup(
        stats=player_stats,
        weapon=weapon,
        equipment_stats=equipment_stats,
        gear_modifiers=gear_modifiers,
        attack_style=attack_style,
        prayer=prayer,
        potion=potion,
        target=target,
        on_slayer_task=on_slayer_task,
        equipped_items=equipped_items,
        spell=selected_spell,
    )

    calculator = CombatCalculator(setup, use_effects=False)
    return calculator.calculate()


def optimize_loadout(
    available_item_ids: List[int],
    attack_type: AttackType,
    item_loader: "ItemLoader",
    exclude_slots: List[EquipmentSlot] = None,
) -> EquipmentLoadout:
    """Find optimal gear from available items for a given attack style.

    For each equipment slot, selects the item with the highest combined
    attack and strength bonus for the specified attack type.

    Args:
        available_item_ids: List of item IDs the player has access to.
        attack_type: The attack type to optimize for (STAB, SLASH, CRUSH, RANGED, MAGIC).
        item_loader: ItemLoader instance with loaded items.json.
        exclude_slots: Slots to leave empty (e.g., shield for 2H weapons).

    Returns:
        EquipmentLoadout with optimal items for each slot.

    Example:
        >>> item_loader = ItemLoader()
        >>> my_items = [26382, 27745, 27748, 24423]  # Crystal armor pieces
        >>> optimal = optimize_loadout(my_items, AttackType.RANGED, item_loader)
        >>> print(f"Total ranged attack: {optimal.get_total_stats().ranged_attack}")
    """
    from collections import defaultdict

    exclude_slots = exclude_slots or []

    # Group items by slot with their scores
    # Dict[slot, List[Tuple[item_id, item_data, score]]]
    slot_candidates: Dict[EquipmentSlot, List] = defaultdict(list)

    for item_id in available_item_ids:
        item_data = item_loader.get_item_data(item_id)
        if not item_data:
            continue

        # Skip non-equipable items
        if not item_data.get("equipable_by_player"):
            continue

        slot = item_loader.get_slot(item_id)
        if slot is None or slot in exclude_slots:
            continue

        # Calculate score for this attack type
        score = calculate_optimization_score(item_data, attack_type)
        slot_candidates[slot].append((item_id, item_data, score))

    # Build the loadout by selecting the best item for each slot
    loadout = EquipmentLoadout(name=f"Optimized ({attack_type.value})")

    for slot in EquipmentSlot:
        if slot not in slot_candidates or slot in exclude_slots:
            continue

        # Sort by score descending, pick the best
        candidates = sorted(slot_candidates[slot], key=lambda x: x[2], reverse=True)
        if not candidates:
            continue

        best_id, best_data, _ = candidates[0]
        stats = item_loader.get_by_id(best_id) or EquipmentStats()

        # Build kwargs for the slot item
        kwargs = {
            "name": best_data.get("name", ""),
            "item_id": best_id,
            "stats": stats,
        }

        # Add weapon-specific attributes if this is a weapon slot
        if slot == EquipmentSlot.WEAPON:
            weap = best_data.get("weapon") or {}
            kwargs["attack_speed"] = weap.get("attack_speed", 4)
            kwargs["is_two_handed"] = item_loader.is_two_handed(best_id)

            # Determine attack type and combat style
            equip = best_data.get("equipment") or {}
            if equip.get("attack_ranged", 0) > 0:
                kwargs["attack_type"] = AttackType.RANGED
                kwargs["combat_style"] = CombatStyle.RANGED
            elif equip.get("attack_magic", 0) > 0:
                kwargs["attack_type"] = AttackType.MAGIC
                kwargs["combat_style"] = CombatStyle.MAGIC
            else:
                kwargs["attack_type"] = attack_type
                kwargs["combat_style"] = CombatStyle.MELEE

        item = create_slot_item(slot, **kwargs)
        loadout.set_slot(slot, item)

    return loadout
