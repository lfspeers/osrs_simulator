"""Load weapons from JSON into Weapon dataclass."""
import json
from pathlib import Path
from typing import Optional, List, Dict

from combat.equipment import (
    Weapon,
    EquipmentStats,
    AttackType,
    CombatStyle,
)


class WeaponLoader:
    """Loads weapon data from JSON files into Weapon objects."""

    # Map osrsreboxed weapon_type to our AttackType and CombatStyle
    WEAPON_TYPE_MAP = {
        # Melee weapons
        "stab_sword": (AttackType.STAB, CombatStyle.MELEE),
        "slash_sword": (AttackType.SLASH, CombatStyle.MELEE),
        "2h_sword": (AttackType.SLASH, CombatStyle.MELEE),
        "axe": (AttackType.SLASH, CombatStyle.MELEE),
        "pickaxe": (AttackType.STAB, CombatStyle.MELEE),
        "blunt": (AttackType.CRUSH, CombatStyle.MELEE),
        "bludgeon": (AttackType.CRUSH, CombatStyle.MELEE),
        "spear": (AttackType.STAB, CombatStyle.MELEE),
        "spiked": (AttackType.CRUSH, CombatStyle.MELEE),
        "scythe": (AttackType.SLASH, CombatStyle.MELEE),
        "whip": (AttackType.SLASH, CombatStyle.MELEE),
        "claw": (AttackType.SLASH, CombatStyle.MELEE),
        "polearm": (AttackType.SLASH, CombatStyle.MELEE),
        "polestaff": (AttackType.CRUSH, CombatStyle.MELEE),
        "banner": (AttackType.STAB, CombatStyle.MELEE),
        "bulwark": (AttackType.CRUSH, CombatStyle.MELEE),
        # Ranged weapons
        "bow": (AttackType.RANGED, CombatStyle.RANGED),
        "crossbow": (AttackType.RANGED, CombatStyle.RANGED),
        "thrown": (AttackType.RANGED, CombatStyle.RANGED),
        "chinchompas": (AttackType.RANGED, CombatStyle.RANGED),
        "gun": (AttackType.RANGED, CombatStyle.RANGED),
        # Magic weapons
        "staff": (AttackType.CRUSH, CombatStyle.MAGIC),  # Staffs crush by default, magic when casting
        "powered_staff": (AttackType.MAGIC, CombatStyle.MAGIC),
        "bladed_staff": (AttackType.SLASH, CombatStyle.MAGIC),
        # Special
        "unarmed": (AttackType.CRUSH, CombatStyle.MELEE),
        "salamander": (AttackType.SLASH, CombatStyle.MELEE),  # Can be any style
    }

    def __init__(self, data_path: Path = None):
        """Initialize the weapon loader.

        Args:
            data_path: Path to items.json file.
                      Defaults to 'data/items.json' in project root.
        """
        if data_path is None:
            data_path = Path(__file__).parent.parent / "data" / "items.json"
        self.data_path = Path(data_path)
        self._cache: Dict[str, Weapon] = {}
        self._name_to_id: Dict[str, str] = {}
        self._loaded = False

    def _load(self):
        """Load data from JSON file into cache."""
        if self._loaded:
            return

        if not self.data_path.exists():
            self._loaded = True
            return

        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item_id, item in data.items():
            # Only load actual weapons
            if not item.get("equipable_weapon"):
                continue

            equip = item.get("equipment") or {}
            weap = item.get("weapon") or {}

            name = item.get("name", "Unknown")
            name_key = self._normalize_name(name)

            # Determine attack type and combat style
            weapon_type = weap.get("weapon_type", "")
            attack_type, combat_style = self.WEAPON_TYPE_MAP.get(
                weapon_type, (AttackType.CRUSH, CombatStyle.MELEE)
            )

            # Determine best attack type based on highest attack bonus
            stab = equip.get("attack_stab", 0)
            slash = equip.get("attack_slash", 0)
            crush = equip.get("attack_crush", 0)
            ranged = equip.get("attack_ranged", 0)
            magic = equip.get("attack_magic", 0)

            # For melee weapons, pick the best attack style
            if combat_style == CombatStyle.MELEE:
                max_bonus = max(stab, slash, crush)
                if max_bonus == stab:
                    attack_type = AttackType.STAB
                elif max_bonus == slash:
                    attack_type = AttackType.SLASH
                else:
                    attack_type = AttackType.CRUSH

            # Magic damage is stored as percentage (e.g., 15 for 15%)
            magic_damage = equip.get("magic_damage", 0)
            if magic_damage:
                magic_damage = magic_damage / 100.0

            stats = EquipmentStats(
                stab_attack=stab,
                slash_attack=slash,
                crush_attack=crush,
                magic_attack=magic,
                ranged_attack=ranged,
                stab_defence=equip.get("defence_stab", 0),
                slash_defence=equip.get("defence_slash", 0),
                crush_defence=equip.get("defence_crush", 0),
                magic_defence=equip.get("defence_magic", 0),
                ranged_defence=equip.get("defence_ranged", 0),
                melee_strength=equip.get("melee_strength", 0),
                ranged_strength=equip.get("ranged_strength", 0),
                magic_damage=magic_damage,
                prayer=equip.get("prayer", 0),
            )

            weapon = Weapon(
                name=name,
                attack_speed=weap.get("attack_speed", 4),
                attack_type=attack_type,
                combat_style=combat_style,
                stats=stats,
                is_two_handed=equip.get("slot") == "2h",
            )

            # Store by normalized name, keeping higher tier versions
            # (determined by melee/ranged strength or magic attack)
            if name_key not in self._cache:
                self._cache[name_key] = weapon
                self._name_to_id[name_key] = item_id
            else:
                existing = self._cache[name_key]
                new_power = max(stats.melee_strength, stats.ranged_strength, stats.magic_attack)
                old_power = max(
                    existing.stats.melee_strength,
                    existing.stats.ranged_strength,
                    existing.stats.magic_attack
                )
                if new_power > old_power:
                    self._cache[name_key] = weapon
                    self._name_to_id[name_key] = item_id

        self._loaded = True

    def _normalize_name(self, name: str) -> str:
        """Normalize a weapon name to a lookup key.

        Args:
            name: The raw weapon name.

        Returns:
            Normalized key (lowercase, underscores, no apostrophes).
        """
        return name.lower().replace(" ", "_").replace("'", "").replace("-", "_")

    def get(self, name: str) -> Optional[Weapon]:
        """Get a weapon by name.

        Args:
            name: The weapon name (case-insensitive, spaces/underscores OK).

        Returns:
            Weapon object, or None if not found.
        """
        self._load()
        key = self._normalize_name(name)
        return self._cache.get(key)

    def list_all(self) -> List[str]:
        """List all weapon names.

        Returns:
            Sorted list of weapon key names.
        """
        self._load()
        return sorted(self._cache.keys())

    def list_by_style(self, style: CombatStyle) -> List[str]:
        """List weapons by combat style.

        Args:
            style: CombatStyle to filter by.

        Returns:
            Sorted list of matching weapon key names.
        """
        self._load()
        return sorted([
            k for k, v in self._cache.items()
            if v.combat_style == style
        ])

    def list_by_type(self, attack_type: AttackType) -> List[str]:
        """List weapons by attack type.

        Args:
            attack_type: AttackType to filter by.

        Returns:
            Sorted list of matching weapon key names.
        """
        self._load()
        return sorted([
            k for k, v in self._cache.items()
            if v.attack_type == attack_type
        ])

    def count(self) -> int:
        """Get total number of loaded weapons.

        Returns:
            Number of weapons in cache.
        """
        self._load()
        return len(self._cache)

    def is_loaded(self) -> bool:
        """Check if data has been loaded.

        This will trigger a lazy load if not already done.

        Returns:
            True if data file exists and was loaded with entries.
        """
        self._load()
        return len(self._cache) > 0
