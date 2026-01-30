"""Tempoross equipment presets.

Since the OSRS Hiscores API cannot detect what equipment a player has,
these presets provide common equipment configurations for Tempoross.
"""

from typing import Dict

from core.player import HarpoonType, PlayerConfig
from core.hiscores import PlayerHiscores
from presets import EquipmentPreset


# Tempoross equipment presets
TEMPOROSS_PRESETS: Dict[str, EquipmentPreset] = {
    "budget": EquipmentPreset(
        name="Budget",
        description="Basic setup with regular harpoon",
        harpoon=HarpoonType.REGULAR,
        has_spirit_angler=False,
        has_imcando_hammer=False,
    ),
    "mid": EquipmentPreset(
        name="Mid-tier",
        description="Dragon harpoon, no special gear",
        harpoon=HarpoonType.DRAGON,
        has_spirit_angler=False,
        has_imcando_hammer=False,
    ),
    "angler": EquipmentPreset(
        name="Spirit Angler",
        description="Crystal harpoon with spirit angler outfit",
        harpoon=HarpoonType.CRYSTAL,
        has_spirit_angler=True,
        has_imcando_hammer=False,
    ),
    "optimal": EquipmentPreset(
        name="Optimal",
        description="Best-in-slot: infernal harpoon, spirit angler, imcando hammer",
        harpoon=HarpoonType.INFERNAL,
        has_spirit_angler=True,
        has_imcando_hammer=True,
    ),
}


def get_preset(name: str) -> EquipmentPreset:
    """Get a Tempoross equipment preset by name.

    Args:
        name: Preset name (budget, mid, angler, optimal).

    Returns:
        The requested equipment preset.

    Raises:
        ValueError: If the preset name is not recognized.
    """
    preset = TEMPOROSS_PRESETS.get(name.lower())
    if preset is None:
        valid = ", ".join(TEMPOROSS_PRESETS.keys())
        raise ValueError(f"Unknown preset '{name}'. Valid presets: {valid}")
    return preset


def list_presets() -> Dict[str, EquipmentPreset]:
    """Get all available Tempoross presets."""
    return TEMPOROSS_PRESETS.copy()


def hiscores_to_player_config(
    hiscores: PlayerHiscores,
    preset: str = "mid"
) -> PlayerConfig:
    """Convert hiscores data to a PlayerConfig using an equipment preset.

    Args:
        hiscores: Player hiscores data from the API.
        preset: Name of the equipment preset to use.

    Returns:
        PlayerConfig ready for simulation.
    """
    equipment = get_preset(preset)

    # If fishing level is below 35, use 35 (minimum for Tempoross)
    fishing_level = max(35, hiscores.fishing_level)

    return PlayerConfig(
        fishing_level=fishing_level,
        cooking_level=hiscores.cooking_level,
        harpoon_type=equipment.harpoon,
        has_spirit_angler=equipment.has_spirit_angler,
        has_imcando_hammer=equipment.has_imcando_hammer,
    )
