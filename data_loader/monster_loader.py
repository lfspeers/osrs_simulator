"""Load monsters from JSON into MonsterStats dataclass."""
import json
from pathlib import Path
from typing import Optional, List, Dict

from combat.entities import MonsterStats


class MonsterLoader:
    """Loads monster data from JSON files into MonsterStats objects."""

    def __init__(self, data_path: Path = None):
        """Initialize the monster loader.

        Args:
            data_path: Path to monsters.json file.
                      Defaults to 'data/monsters.json' in project root.
        """
        if data_path is None:
            data_path = Path(__file__).parent.parent / "data" / "monsters.json"
        self.data_path = Path(data_path)
        self._cache: Dict[str, MonsterStats] = {}
        self._name_to_id: Dict[str, str] = {}
        self._raw_data: Dict[str, dict] = {}
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

        self._raw_data = data

        for mon_id, mon in data.items():
            name = mon.get("name", "Unknown")
            name_key = self._normalize_name(name)
            attrs = mon.get("attributes") or []

            stats = MonsterStats(
                name=name,
                hitpoints=mon.get("hitpoints", 1),
                defence_level=mon.get("defence_level", 1),
                magic_level=mon.get("magic_level", 1),
                stab_defence=mon.get("defence_stab", 0),
                slash_defence=mon.get("defence_slash", 0),
                crush_defence=mon.get("defence_crush", 0),
                ranged_defence=mon.get("defence_ranged", 0),
                magic_defence=mon.get("defence_magic", 0),
                attack_level=mon.get("attack_level", 1),
                strength_level=mon.get("strength_level", 1),
                ranged_level=mon.get("ranged_level", 1),
                max_hit=mon.get("max_hit") or 0,
                is_undead="undead" in attrs,
                is_demon="demon" in attrs,
                is_dragon="dragon" in attrs,
                is_kalphite="kalphite" in attrs,
                is_leafy="leafy" in attrs,
                slayer_category=mon.get("slayer_monster") if mon.get("slayer_monster") else None,
                tile_size=mon.get("size", 1),
            )

            # Store by normalized name, handling duplicates by keeping highest HP version
            if name_key not in self._cache or stats.hitpoints > self._cache[name_key].hitpoints:
                self._cache[name_key] = stats
                self._name_to_id[name_key] = mon_id

        self._loaded = True

    def _normalize_name(self, name: str) -> str:
        """Normalize a monster name to a lookup key.

        Args:
            name: The raw monster name.

        Returns:
            Normalized key (lowercase, underscores, no apostrophes).
        """
        return name.lower().replace(" ", "_").replace("'", "").replace("-", "_")

    def get(self, name: str) -> Optional[MonsterStats]:
        """Get a monster by name.

        Args:
            name: The monster name (case-insensitive, spaces/underscores OK).

        Returns:
            MonsterStats object, or None if not found.
        """
        self._load()
        key = self._normalize_name(name)
        return self._cache.get(key)

    def list_all(self) -> List[str]:
        """List all monster names.

        Returns:
            Sorted list of monster key names.
        """
        self._load()
        return sorted(self._cache.keys())

    def get_bosses(self, min_hp: int = 200) -> List[str]:
        """Get monsters with high HP (bosses).

        Args:
            min_hp: Minimum hitpoints to be considered a boss.

        Returns:
            List of boss key names.
        """
        self._load()
        return sorted([k for k, v in self._cache.items() if v.hitpoints >= min_hp])

    def get_by_attribute(self, attribute: str) -> List[str]:
        """Get monsters with a specific attribute.

        Args:
            attribute: Attribute to filter by (undead, demon, dragon, kalphite, leafy).

        Returns:
            List of matching monster key names.
        """
        self._load()
        attr_map = {
            "undead": lambda m: m.is_undead,
            "demon": lambda m: m.is_demon,
            "dragon": lambda m: m.is_dragon,
            "kalphite": lambda m: m.is_kalphite,
            "leafy": lambda m: m.is_leafy,
        }
        if attribute not in attr_map:
            return []
        return sorted([k for k, v in self._cache.items() if attr_map[attribute](v)])

    def get_by_slayer_category(self, category: str) -> List[str]:
        """Get monsters in a slayer category.

        Args:
            category: Slayer category to filter by (string name like "dragon", "demon").

        Returns:
            List of matching monster key names.
        """
        self._load()
        return sorted([
            k for k, v in self._cache.items()
            if v.slayer_category and isinstance(v.slayer_category, str)
            and v.slayer_category.lower() == category.lower()
        ])

    def count(self) -> int:
        """Get total number of loaded monsters.

        Returns:
            Number of monsters in cache.
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
