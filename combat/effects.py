"""Core dataclasses for the OSRS passive effects system.

This module provides the fundamental data structures for representing
equipment effects, set bonuses, and special weapon mechanics used in
DPS calculations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List

from .equipment import CombatStyle


class SourceType(Enum):
    """Type of item that provides an effect."""
    WEAPON = "weapon"
    ARMOR = "armor"
    SET = "set"
    AMULET = "amulet"
    AMMO = "ammo"
    RING = "ring"
    CAPE = "cape"


@dataclass
class EffectCondition:
    """Conditions under which an effect applies.

    Effects only activate when their conditions are met. Multiple conditions
    are combined with AND logic (all must be true).

    Attributes:
        vs_attribute: Target must have this attribute (e.g., "undead", "demon", "dragon").
        on_slayer_task: Player must be on a slayer task for the target.
        in_wilderness: Player must be in the wilderness.
        player_hp_below: Player HP must be below this percentage (0.0-1.0) for Dharok's.
        target_size_min: Target's tile size must be at least this value (for Scythe).
        using_attack_type: Only applies when using this attack type (for Inquisitor crush).
        using_specific_weapon: Only applies when using weapons matching these patterns.
    """
    vs_attribute: Optional[str] = None
    on_slayer_task: bool = False
    in_wilderness: bool = False
    player_hp_below: Optional[float] = None
    target_size_min: Optional[int] = None
    using_attack_type: Optional[str] = None  # "stab", "slash", "crush", etc.
    using_specific_weapon: Optional[List[str]] = None  # Weapon name patterns

    def is_met(
        self,
        target_attributes: Optional[List[str]] = None,
        on_slayer_task: bool = False,
        in_wilderness: bool = False,
        player_hp_percent: float = 1.0,
        target_size: int = 1,
        attack_type: Optional[str] = None,
        weapon_name: Optional[str] = None,
    ) -> bool:
        """Check if all conditions are met.

        Args:
            target_attributes: List of target's attributes (e.g., ["undead", "dragon"]).
            on_slayer_task: Whether player is on slayer task.
            in_wilderness: Whether player is in wilderness.
            player_hp_percent: Player's current HP as percentage (0.0-1.0).
            target_size: Target's tile size.
            attack_type: Current attack type being used.
            weapon_name: Current weapon name.

        Returns:
            True if all conditions are met.
        """
        target_attributes = target_attributes or []

        # Check vs_attribute
        if self.vs_attribute is not None:
            if self.vs_attribute not in target_attributes:
                return False

        # Check slayer task
        if self.on_slayer_task and not on_slayer_task:
            return False

        # Check wilderness
        if self.in_wilderness and not in_wilderness:
            return False

        # Check player HP (for effects that require low HP)
        if self.player_hp_below is not None:
            if player_hp_percent >= self.player_hp_below:
                return False

        # Check target size
        if self.target_size_min is not None:
            if target_size < self.target_size_min:
                return False

        # Check attack type
        if self.using_attack_type is not None:
            if attack_type is None or attack_type.lower() != self.using_attack_type.lower():
                return False

        # Check weapon name patterns (normalize underscores/spaces for matching)
        if self.using_specific_weapon is not None and weapon_name is not None:
            weapon_normalized = weapon_name.lower().replace("_", " ").replace("'", "")
            if not any(
                pattern.lower().replace("_", " ").replace("'", "") in weapon_normalized
                for pattern in self.using_specific_weapon
            ):
                return False

        return True


@dataclass
class EffectModifier:
    """Modifiers applied by an effect.

    Standard multipliers are applied to accuracy and damage calculations.
    Special mechanics provide unique behaviors for specific weapons.

    Attributes:
        accuracy_mult: Multiplier for attack roll (1.0 = no change).
        damage_mult: Multiplier for max hit (1.0 = no change).
        double_accuracy_roll: Roll accuracy twice, hit if either succeeds (Fang).
        min_hit_percent: Minimum hit as percentage of max hit (Fang: 0.15).
        max_hit_percent: Maximum hit as percentage of base max hit (Fang: 0.85).
        extra_hits: Additional hits as percentage of first hit (Scythe: [0.5, 0.25]).
        scales_with_target_magic: Damage/accuracy scale with target's magic (Twisted bow).
        scales_with_missing_hp: Damage scales with player's missing HP (Dharok's).
        ignores_defence: Attack ignores target's defence (Verac's).
        ignores_prayer: Attack ignores protection prayers (Verac's).
    """
    accuracy_mult: float = 1.0
    damage_mult: float = 1.0

    # Special mechanics
    double_accuracy_roll: bool = False
    min_hit_percent: Optional[float] = None
    max_hit_percent: Optional[float] = None
    extra_hits: Optional[List[float]] = None  # Multipliers for additional hits
    scales_with_target_magic: bool = False
    scales_with_missing_hp: bool = False
    ignores_defence: bool = False
    ignores_prayer: bool = False

    def combine(self, other: "EffectModifier") -> "EffectModifier":
        """Combine two modifiers (multiplicative for multipliers).

        Args:
            other: Another modifier to combine with.

        Returns:
            New EffectModifier with combined values.
        """
        return EffectModifier(
            accuracy_mult=self.accuracy_mult * other.accuracy_mult,
            damage_mult=self.damage_mult * other.damage_mult,
            double_accuracy_roll=self.double_accuracy_roll or other.double_accuracy_roll,
            min_hit_percent=self.min_hit_percent or other.min_hit_percent,
            max_hit_percent=self.max_hit_percent or other.max_hit_percent,
            extra_hits=self.extra_hits or other.extra_hits,
            scales_with_target_magic=self.scales_with_target_magic or other.scales_with_target_magic,
            scales_with_missing_hp=self.scales_with_missing_hp or other.scales_with_missing_hp,
            ignores_defence=self.ignores_defence or other.ignores_defence,
            ignores_prayer=self.ignores_prayer or other.ignores_prayer,
        )


@dataclass
class PassiveEffect:
    """Complete definition of a passive effect.

    Passive effects can come from weapons, armor, amulets, or set bonuses.
    Each effect has conditions that determine when it applies and modifiers
    that affect combat calculations.

    Attributes:
        id: Unique identifier for this effect.
        name: Human-readable name.
        source_type: Type of item that provides this effect.
        source_items: Item IDs/names that provide this effect.
        combat_styles: Which combat styles this effect applies to.
        condition: When this effect activates.
        modifier: What this effect does.
        proc_chance: Probability of effect triggering (1.0 = always, 0.25 = Barrows).
        stacking_group: Effects in the same group don't stack.
        stacking_priority: Higher priority wins when in same stacking group.
        description: Human-readable description of what this effect does.
    """
    id: str
    name: str
    source_type: SourceType
    source_items: List[str]
    combat_styles: List[CombatStyle]
    condition: EffectCondition = field(default_factory=EffectCondition)
    modifier: EffectModifier = field(default_factory=EffectModifier)
    proc_chance: float = 1.0
    stacking_group: Optional[str] = None
    stacking_priority: int = 0
    additive_group: Optional[str] = None  # Effects in same group stack additively
    description: str = ""

    def applies_to_style(self, style: CombatStyle) -> bool:
        """Check if this effect applies to a combat style.

        Args:
            style: The combat style to check.

        Returns:
            True if this effect applies to the given style.
        """
        return style in self.combat_styles

    def is_from_item(self, item_name: str) -> bool:
        """Check if this effect comes from a specific item.

        Args:
            item_name: Item name to check.

        Returns:
            True if this effect is provided by the item.
        """
        item_lower = item_name.lower()
        return any(
            source.lower() in item_lower or item_lower in source.lower()
            for source in self.source_items
        )


@dataclass
class SetBonus:
    """Set bonus that requires multiple pieces.

    Set bonuses activate when the player has equipped at least the minimum
    required number of pieces from the set.

    Attributes:
        id: Unique identifier for this set bonus.
        name: Human-readable name (e.g., "Dharok's Set").
        required_items: List of item names/IDs that make up the set.
        min_pieces: Minimum pieces required to activate.
        effect: The PassiveEffect granted by this set bonus.
    """
    id: str
    name: str
    required_items: List[str]
    min_pieces: int
    effect: PassiveEffect

    def is_active(self, equipped_items: List[str]) -> bool:
        """Check if the set bonus is active.

        Args:
            equipped_items: List of currently equipped item names.

        Returns:
            True if enough pieces are equipped.
        """
        equipped_lower = [item.lower() for item in equipped_items]
        count = sum(
            1 for req in self.required_items
            if any(req.lower() in eq or eq in req.lower() for eq in equipped_lower)
        )
        return count >= self.min_pieces

    def get_piece_count(self, equipped_items: List[str]) -> int:
        """Count how many pieces of the set are equipped.

        Args:
            equipped_items: List of currently equipped item names.

        Returns:
            Number of set pieces equipped.
        """
        equipped_lower = [item.lower() for item in equipped_items]
        return sum(
            1 for req in self.required_items
            if any(req.lower() in eq or eq in req.lower() for eq in equipped_lower)
        )


@dataclass
class ActiveEffect:
    """An effect that has been determined to be active in the current context.

    This is a runtime wrapper around PassiveEffect that indicates the effect
    is currently applicable based on equipment and conditions.

    Attributes:
        effect: The underlying PassiveEffect.
        source: What item/set activated this effect.
        effective_proc_chance: Actual proc chance after any modifications.
    """
    effect: PassiveEffect
    source: str
    effective_proc_chance: float = 1.0

    @property
    def modifier(self) -> EffectModifier:
        """Get the effect's modifier."""
        return self.effect.modifier

    @property
    def stacking_group(self) -> Optional[str]:
        """Get the effect's stacking group."""
        return self.effect.stacking_group

    @property
    def stacking_priority(self) -> int:
        """Get the effect's stacking priority."""
        return self.effect.stacking_priority


@dataclass
class ResolvedModifiers:
    """Final resolved modifiers after applying all active effects and stacking rules.

    This is the output of the effect resolution process and contains all
    the final values needed for DPS calculations.

    Attributes:
        accuracy_mult: Final accuracy multiplier.
        damage_mult: Final damage multiplier.
        double_accuracy_roll: Whether to use double accuracy roll.
        min_hit_percent: Minimum hit percentage (if any).
        max_hit_percent: Maximum hit percentage (if any).
        extra_hits: Extra hit multipliers (if any).
        scales_with_target_magic: Whether damage scales with target magic.
        scales_with_missing_hp: Whether damage scales with missing HP.
        ignores_defence: Whether attack ignores defence.
        ignores_prayer: Whether attack ignores protection prayers.
        active_effects: List of effects that contributed to these modifiers.
        proc_effects: List of effects that have < 1.0 proc chance.
    """
    accuracy_mult: float = 1.0
    damage_mult: float = 1.0
    double_accuracy_roll: bool = False
    min_hit_percent: Optional[float] = None
    max_hit_percent: Optional[float] = None
    extra_hits: Optional[List[float]] = None
    scales_with_target_magic: bool = False
    scales_with_missing_hp: bool = False
    ignores_defence: bool = False
    ignores_prayer: bool = False
    active_effects: List[ActiveEffect] = field(default_factory=list)
    proc_effects: List[ActiveEffect] = field(default_factory=list)

    def has_special_mechanics(self) -> bool:
        """Check if any special mechanics are active."""
        return (
            self.double_accuracy_roll or
            self.min_hit_percent is not None or
            self.extra_hits is not None or
            self.scales_with_target_magic or
            self.scales_with_missing_hp or
            self.ignores_defence
        )
