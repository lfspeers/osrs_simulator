"""Fetch OSRS data from osrsreboxed-db."""
import json
import time
from pathlib import Path
from typing import Dict, Any

import requests

# Primary URLs from GitHub raw (more reliable)
ITEMS_URL = "https://raw.githubusercontent.com/0xNeffarion/osrsreboxed-db/master/docs/items-complete.json"
MONSTERS_URL = "https://raw.githubusercontent.com/0xNeffarion/osrsreboxed-db/master/docs/monsters-complete.json"

# Fallback URLs from osrsbox.com
ITEMS_URL_FALLBACK = "https://www.osrsbox.com/osrsbox-db/items-complete.json"
MONSTERS_URL_FALLBACK = "https://www.osrsbox.com/osrsbox-db/monsters-complete.json"


class OSRSDataFetcher:
    """Fetches and manages OSRS data from osrsreboxed-db."""

    def __init__(self, data_dir: Path = None):
        """Initialize the data fetcher.

        Args:
            data_dir: Directory to store downloaded data files.
                     Defaults to 'data/' in the project root.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def _download_json(self, url: str, verbose: bool = False) -> Dict[str, Any]:
        """Download and parse a large JSON file with streaming.

        Args:
            url: URL to download from.
            verbose: If True, print progress information.

        Returns:
            Parsed JSON data.
        """
        # Stream the response to handle large files
        resp = requests.get(url, timeout=300, stream=True)
        resp.raise_for_status()

        # Get content length if available
        content_length = resp.headers.get('content-length')
        if content_length and verbose:
            size_mb = int(content_length) / (1024 * 1024)
            print(f"  Downloading {size_mb:.1f} MB...")

        # Collect all chunks
        chunks = []
        downloaded = 0
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                chunks.append(chunk)
                downloaded += len(chunk)

        # Combine and decode
        content = b''.join(chunks)
        return json.loads(content.decode('utf-8'))

    def fetch_items(self, verbose: bool = False) -> Dict[str, Any]:
        """Fetch and filter combat-relevant items (weapons, armour).

        Args:
            verbose: If True, print progress information.

        Returns:
            Dictionary of item_id -> item data for combat items.
        """
        if verbose:
            print("Fetching items from osrsreboxed-db...")

        all_items = self._download_json(ITEMS_URL, verbose)

        if verbose:
            print(f"  Downloaded {len(all_items)} total items")

        # Filter to equipable combat items only
        combat_items = {}
        valid_slots = {
            "weapon", "2h", "shield", "head", "body", "legs",
            "hands", "feet", "cape", "neck", "ring", "ammo"
        }

        for item_id, item in all_items.items():
            # Include if it's a weapon
            if item.get("equipable_weapon"):
                combat_items[item_id] = item
                continue

            # Include if it's equipable in a combat-relevant slot
            equipment = item.get("equipment")
            if equipment and equipment.get("slot") in valid_slots:
                combat_items[item_id] = item

        if verbose:
            print(f"  Filtered to {len(combat_items)} combat items")

        return combat_items

    def fetch_monsters(self, verbose: bool = False) -> Dict[str, Any]:
        """Fetch all attackable monsters.

        Args:
            verbose: If True, print progress information.

        Returns:
            Dictionary of monster_id -> monster data for attackable monsters.
        """
        if verbose:
            print("Fetching monsters from osrsreboxed-db...")

        all_monsters = self._download_json(MONSTERS_URL, verbose)

        if verbose:
            print(f"  Downloaded {len(all_monsters)} total monsters")

        # Filter to attackable monsters with hitpoints
        combat_monsters = {}
        for mon_id, mon in all_monsters.items():
            if mon.get("hitpoints") and mon["hitpoints"] > 0:
                combat_monsters[mon_id] = mon

        if verbose:
            print(f"  Filtered to {len(combat_monsters)} attackable monsters")

        return combat_monsters

    def save_data(self, verbose: bool = True) -> Dict[str, Any]:
        """Fetch and save all data to JSON files.

        Args:
            verbose: If True, print progress information.

        Returns:
            Metadata dictionary with version info and counts.
        """
        items = self.fetch_items(verbose=verbose)
        monsters = self.fetch_monsters(verbose=verbose)

        # Save items
        items_path = self.data_dir / "items.json"
        with open(items_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        if verbose:
            print(f"Saved items to {items_path}")

        # Save monsters
        monsters_path = self.data_dir / "monsters.json"
        with open(monsters_path, "w", encoding="utf-8") as f:
            json.dump(monsters, f, indent=2)
        if verbose:
            print(f"Saved monsters to {monsters_path}")

        # Save metadata
        metadata = {
            "version": "1.0.0",
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "osrsreboxed-db",
            "item_count": len(items),
            "monster_count": len(monsters),
        }
        metadata_path = self.data_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        if verbose:
            print(f"Saved metadata to {metadata_path}")
            print()
            print(f"Data fetch complete!")
            print(f"  Items: {len(items)}")
            print(f"  Monsters: {len(monsters)}")

        return metadata

    def get_metadata(self) -> Dict[str, Any]:
        """Load metadata from saved file.

        Returns:
            Metadata dictionary, or empty dict if not found.
        """
        metadata_path = self.data_dir / "metadata.json"
        if not metadata_path.exists():
            return {}
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def has_data(self) -> bool:
        """Check if data files exist.

        Returns:
            True if both items.json and monsters.json exist.
        """
        items_path = self.data_dir / "items.json"
        monsters_path = self.data_dir / "monsters.json"
        return items_path.exists() and monsters_path.exists()
