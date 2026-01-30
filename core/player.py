"""Player stats, equipment, and inventory for OSRS simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.hiscores import PlayerHiscores


class HarpoonType(Enum):
    """Types of harpoons available for fishing."""
    REGULAR = "regular"
    DRAGON = "dragon"
    INFERNAL = "infernal"
    CRYSTAL = "crystal"

    @property
    def speed_modifier(self) -> int:
        """Tick reduction for fishing (0 = no bonus)."""
        if self in (HarpoonType.DRAGON, HarpoonType.INFERNAL):
            return 1  # 1 tick faster
        elif self == HarpoonType.CRYSTAL:
            return 1  # Same as dragon
        return 0

    @property
    def auto_cook_chance(self) -> float:
        """Chance to automatically cook fish (infernal only)."""
        if self == HarpoonType.INFERNAL:
            return 1/3
        return 0.0


@dataclass
class PlayerStats:
    """Player skill levels.

    Attributes:
        fishing: Fishing level (35-99 for Tempoross).
        cooking: Cooking level (1-99).
        construction: Construction level (for repair actions).
    """
    fishing: int = 35
    cooking: int = 1
    construction: int = 1

    def __post_init__(self):
        self.fishing = max(1, min(99, self.fishing))
        self.cooking = max(1, min(99, self.cooking))
        self.construction = max(1, min(99, self.construction))

    @property
    def can_enter_tempoross(self) -> bool:
        """Check if player meets minimum requirements for Tempoross."""
        return self.fishing >= 35


@dataclass
class Equipment:
    """Player equipment loadout.

    Attributes:
        harpoon: Type of harpoon equipped/in inventory.
        has_spirit_angler: Whether full spirit angler outfit is worn.
        has_imcando_hammer: Whether imcando hammer is equipped.
    """
    harpoon: HarpoonType = HarpoonType.REGULAR
    has_spirit_angler: bool = False
    has_imcando_hammer: bool = False

    @property
    def rope_required(self) -> bool:
        """Whether rope is needed to survive waves."""
        return not self.has_spirit_angler


@dataclass
class InventoryItem:
    """An item in the player's inventory."""
    name: str
    quantity: int = 1
    stackable: bool = False


class Inventory:
    """Player inventory management.

    Standard inventory has 28 slots. For Tempoross, players typically
    start with some required items (rope, hammer, buckets) and fill
    the rest with fish.
    """

    MAX_SLOTS = 28

    def __init__(self, reserved_slots: int = 0):
        """Initialize inventory.

        Args:
            reserved_slots: Number of slots reserved for equipment/tools.
        """
        self._items: list[Optional[InventoryItem]] = [None] * self.MAX_SLOTS
        self._reserved_slots = reserved_slots

    @property
    def available_slots(self) -> int:
        """Number of available slots for fish/items."""
        return self.MAX_SLOTS - self._reserved_slots - self.used_slots

    @property
    def used_slots(self) -> int:
        """Number of slots currently in use."""
        return sum(1 for item in self._items if item is not None)

    @property
    def fish_capacity(self) -> int:
        """Maximum fish the inventory can hold."""
        return self.MAX_SLOTS - self._reserved_slots

    def add_item(self, name: str, quantity: int = 1, stackable: bool = False) -> int:
        """Add items to inventory.

        Args:
            name: Item name.
            quantity: Number to add.
            stackable: Whether the item stacks.

        Returns:
            Number of items actually added.
        """
        if stackable:
            # Find existing stack or empty slot
            for i, item in enumerate(self._items):
                if item and item.name == name:
                    item.quantity += quantity
                    return quantity

            # Add new stack
            for i in range(self._reserved_slots, self.MAX_SLOTS):
                if self._items[i] is None:
                    self._items[i] = InventoryItem(name, quantity, True)
                    return quantity
            return 0

        # Non-stackable: need one slot per item
        added = 0
        for i in range(self._reserved_slots, self.MAX_SLOTS):
            if added >= quantity:
                break
            if self._items[i] is None:
                self._items[i] = InventoryItem(name, 1, False)
                added += 1
        return added

    def remove_item(self, name: str, quantity: int = 1) -> int:
        """Remove items from inventory.

        Args:
            name: Item name to remove.
            quantity: Number to remove.

        Returns:
            Number of items actually removed.
        """
        removed = 0
        for i in range(self.MAX_SLOTS - 1, -1, -1):
            if removed >= quantity:
                break
            item = self._items[i]
            if item and item.name == name:
                if item.stackable:
                    to_remove = min(item.quantity, quantity - removed)
                    item.quantity -= to_remove
                    removed += to_remove
                    if item.quantity <= 0:
                        self._items[i] = None
                else:
                    self._items[i] = None
                    removed += 1
        return removed

    def count_item(self, name: str) -> int:
        """Count total quantity of an item."""
        total = 0
        for item in self._items:
            if item and item.name == name:
                total += item.quantity if item.stackable else 1
        return total

    def has_item(self, name: str, quantity: int = 1) -> bool:
        """Check if inventory has at least the specified quantity."""
        return self.count_item(name) >= quantity

    def clear(self):
        """Remove all items from inventory."""
        self._items = [None] * self.MAX_SLOTS

    def clear_fish(self):
        """Remove all fish from inventory."""
        for i in range(self.MAX_SLOTS):
            item = self._items[i]
            if item and item.name in ("raw_harpoonfish", "cooked_harpoonfish", "crystallised_harpoonfish"):
                self._items[i] = None


@dataclass
class PlayerConfig:
    """Complete player configuration for simulation.

    This combines stats and equipment into a single configuration
    object that can be passed to the simulator.
    """
    fishing_level: int = 35
    cooking_level: int = 1
    harpoon_type: HarpoonType = HarpoonType.REGULAR
    has_spirit_angler: bool = False
    has_imcando_hammer: bool = False

    def __post_init__(self):
        self.fishing_level = max(35, min(99, self.fishing_level))
        self.cooking_level = max(1, min(99, self.cooking_level))

    @property
    def stats(self) -> PlayerStats:
        """Get PlayerStats object."""
        return PlayerStats(
            fishing=self.fishing_level,
            cooking=self.cooking_level
        )

    @property
    def equipment(self) -> Equipment:
        """Get Equipment object."""
        return Equipment(
            harpoon=self.harpoon_type,
            has_spirit_angler=self.has_spirit_angler,
            has_imcando_hammer=self.has_imcando_hammer
        )

    def get_reserved_slots(self) -> int:
        """Calculate inventory slots reserved for tools.

        Typical setup:
        - Rope (1 slot) if no spirit angler
        - Hammer (1 slot) if no imcando hammer
        - Buckets (4 slots) for firefighting
        """
        slots = 0
        if not self.has_spirit_angler:
            slots += 1  # Rope
        if not self.has_imcando_hammer:
            slots += 1  # Hammer
        slots += 4  # Buckets for fires
        return slots


@dataclass
class CombatStats:
    """Player combat skill levels for DPS calculations.

    Attributes:
        attack: Attack level (1-99).
        strength: Strength level (1-99).
        defence: Defence level (1-99).
        ranged: Ranged level (1-99).
        magic: Magic level (1-99).
        hitpoints: Hitpoints level (10-99).
        prayer: Prayer level (1-99).
    """
    attack: int = 1
    strength: int = 1
    defence: int = 1
    ranged: int = 1
    magic: int = 1
    hitpoints: int = 10
    prayer: int = 1

    def __post_init__(self):
        self.attack = max(1, min(99, self.attack))
        self.strength = max(1, min(99, self.strength))
        self.defence = max(1, min(99, self.defence))
        self.ranged = max(1, min(99, self.ranged))
        self.magic = max(1, min(99, self.magic))
        self.hitpoints = max(10, min(99, self.hitpoints))
        self.prayer = max(1, min(99, self.prayer))

    @classmethod
    def from_hiscores(cls, hiscores: "PlayerHiscores") -> "CombatStats":
        """Create CombatStats from PlayerHiscores data.

        Args:
            hiscores: PlayerHiscores object from the hiscores API.

        Returns:
            CombatStats with the player's combat levels.
        """
        def get_level(skill_name: str, default: int = 1) -> int:
            skill = hiscores.skills.get(skill_name)
            return skill.level if skill else default

        return cls(
            attack=get_level("Attack"),
            strength=get_level("Strength"),
            defence=get_level("Defence"),
            ranged=get_level("Ranged"),
            magic=get_level("Magic"),
            hitpoints=get_level("Hitpoints", 10),
            prayer=get_level("Prayer"),
        )

    @classmethod
    def maxed(cls) -> "CombatStats":
        """Create CombatStats with all levels at 99."""
        return cls(
            attack=99,
            strength=99,
            defence=99,
            ranged=99,
            magic=99,
            hitpoints=99,
            prayer=99,
        )

    @property
    def combat_level(self) -> int:
        """Calculate the player's combat level.

        Uses the OSRS combat level formula:
        base = 0.25 * (defence + hitpoints + floor(prayer/2))
        melee = 0.325 * (attack + strength)
        ranged = 0.325 * floor(ranged * 1.5)
        magic = 0.325 * floor(magic * 1.5)
        combat_level = floor(base + max(melee, ranged, magic))
        """
        import math

        base = 0.25 * (self.defence + self.hitpoints + math.floor(self.prayer / 2))
        melee = 0.325 * (self.attack + self.strength)
        ranged = 0.325 * math.floor(self.ranged * 1.5)
        magic = 0.325 * math.floor(self.magic * 1.5)

        return math.floor(base + max(melee, ranged, magic))
