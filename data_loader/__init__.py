"""OSRS data loading module.

This module provides tools for fetching and loading OSRS combat data
from the osrsreboxed-db database.
"""

from .fetcher import OSRSDataFetcher
from .monster_loader import MonsterLoader
from .item_loader import WeaponLoader, ItemLoader
from .spell_loader import get_spell, list_spells, SPELLS

__all__ = [
    "OSRSDataFetcher",
    "MonsterLoader",
    "WeaponLoader",
    "ItemLoader",
    "get_spell",
    "list_spells",
    "SPELLS",
]
