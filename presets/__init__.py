"""Equipment presets for OSRS minigame simulations.

This package provides preset equipment configurations since the OSRS Hiscores API
only returns skill levels and activity scores - not equipment or items.
"""

from dataclasses import dataclass
from typing import Dict, Any

from core.player import HarpoonType


@dataclass
class EquipmentPreset:
    """Base class for equipment presets."""
    name: str
    description: str
    harpoon: HarpoonType
    has_spirit_angler: bool
    has_imcando_hammer: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "harpoon": self.harpoon.value,
            "has_spirit_angler": self.has_spirit_angler,
            "has_imcando_hammer": self.has_imcando_hammer,
        }


__all__ = ["EquipmentPreset"]
