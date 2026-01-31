"""Equipment, weapons, and gear modifiers for OSRS combat."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from data_loader.item_loader import WeaponLoader, ItemLoader

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


def format_loadout_summary(loadout: "EquipmentLoadout", width: int = 60) -> str:
    """Format a loadout's stats as a readable summary in an ASCII box.

    Displays equipment in a visual layout similar to the in-game
    equipment screen.

    Args:
        loadout: The equipment loadout to summarize.
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
