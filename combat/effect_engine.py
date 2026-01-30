"""Effect evaluation engine for OSRS passive effects.

This module handles detecting which effects are active based on equipment,
applying stacking rules, and resolving final modifiers for DPS calculations.
"""

from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

from .equipment import CombatStyle, Weapon
from .entities import MonsterStats
from .effects import (
    PassiveEffect,
    SetBonus,
    ActiveEffect,
    ResolvedModifiers,
    EffectModifier,
)
from .effect_definitions import (
    ALL_EFFECTS,
    ALL_SET_BONUSES,
    WEAPON_EFFECTS,
    STACKING_GROUPS,
)


@dataclass
class CombatContext:
    """Context information for effect evaluation.

    Encapsulates all the information needed to determine which effects
    are active and how they should be applied.

    Attributes:
        combat_style: The combat style being used.
        attack_type: The attack type (stab, slash, crush, ranged, magic).
        weapon_name: Name of the equipped weapon.
        equipped_items: List of all equipped item names.
        target: The target monster's stats.
        on_slayer_task: Whether the player is on a slayer task.
        in_wilderness: Whether the combat is in the wilderness.
        player_hp_percent: Player's current HP as percentage (0.0-1.0).
        player_max_hp: Player's maximum HP (for Dharok's calculation).
    """
    combat_style: CombatStyle
    attack_type: str
    weapon_name: str
    equipped_items: List[str]
    target: Optional[MonsterStats] = None
    on_slayer_task: bool = False
    in_wilderness: bool = False
    player_hp_percent: float = 1.0
    player_max_hp: int = 99


def get_target_attributes(target: Optional[MonsterStats]) -> List[str]:
    """Get all attributes of a target monster.

    Args:
        target: The target monster stats.

    Returns:
        List of attribute names.
    """
    if target is None:
        return []

    attributes = []
    if target.is_undead:
        attributes.append("undead")
    if target.is_demon:
        attributes.append("demon")
    if target.is_dragon:
        attributes.append("dragon")
    if target.is_kalphite:
        attributes.append("kalphite")
    if target.is_leafy:
        attributes.append("leafy")
    # Could add more like revenant, etc.
    return attributes


def detect_weapon_effects(
    weapon_name: str,
    context: CombatContext,
) -> List[ActiveEffect]:
    """Detect effects from the equipped weapon.

    Args:
        weapon_name: Name of the weapon.
        context: Combat context for condition checking.

    Returns:
        List of active effects from the weapon.
    """
    active = []
    weapon_lower = weapon_name.lower().replace(" ", "_").replace("'", "")

    # Check for weapon-specific effects
    for pattern, effect in WEAPON_EFFECTS.items():
        if pattern in weapon_lower or weapon_lower in pattern:
            # Check if effect applies to this combat style
            if not effect.applies_to_style(context.combat_style):
                continue

            # Check conditions
            target_attrs = get_target_attributes(context.target)
            target_size = context.target.tile_size if context.target else 1

            if effect.condition.is_met(
                target_attributes=target_attrs,
                on_slayer_task=context.on_slayer_task,
                in_wilderness=context.in_wilderness,
                player_hp_percent=context.player_hp_percent,
                target_size=target_size,
                attack_type=context.attack_type,
                weapon_name=weapon_name,
            ):
                active.append(ActiveEffect(
                    effect=effect,
                    source=weapon_name,
                    effective_proc_chance=effect.proc_chance,
                ))

    return active


def detect_item_effects(
    equipped_items: List[str],
    context: CombatContext,
) -> List[ActiveEffect]:
    """Detect effects from individual equipped items.

    Args:
        equipped_items: List of equipped item names.
        context: Combat context for condition checking.

    Returns:
        List of active effects from equipment.
    """
    active = []
    target_attrs = get_target_attributes(context.target)
    target_size = context.target.tile_size if context.target else 1

    # Get the set of effect IDs that are weapon effects (to skip them)
    weapon_effect_ids = {eff.id for eff in WEAPON_EFFECTS.values()}
    # Get the set of effect IDs that are set bonus effects (handled by detect_set_bonuses)
    set_effect_ids = {sb.effect.id for sb in ALL_SET_BONUSES.values()}

    for effect_id, effect in ALL_EFFECTS.items():
        # Skip weapon effects (handled separately by detect_weapon_effects)
        if effect_id in weapon_effect_ids:
            continue
        # Skip set bonus effects (handled separately by detect_set_bonuses)
        if effect_id in set_effect_ids:
            continue
        # Skip SET-type effects entirely - they require all pieces and should
        # only be detected via SetBonus entries in detect_set_bonuses
        from .effects import SourceType
        if effect.source_type == SourceType.SET:
            continue

        # Check if any equipped item provides this effect
        has_item = any(effect.is_from_item(item) for item in equipped_items)
        if not has_item:
            continue

        # Check if effect applies to this combat style
        if not effect.applies_to_style(context.combat_style):
            continue

        # Check conditions
        if effect.condition.is_met(
            target_attributes=target_attrs,
            on_slayer_task=context.on_slayer_task,
            in_wilderness=context.in_wilderness,
            player_hp_percent=context.player_hp_percent,
            target_size=target_size,
            attack_type=context.attack_type,
            weapon_name=context.weapon_name,
        ):
            active.append(ActiveEffect(
                effect=effect,
                source=effect.name,
                effective_proc_chance=effect.proc_chance,
            ))

    return active


def detect_set_bonuses(
    equipped_items: List[str],
    context: CombatContext,
) -> List[ActiveEffect]:
    """Detect active set bonuses.

    Args:
        equipped_items: List of equipped item names.
        context: Combat context for condition checking.

    Returns:
        List of active set bonus effects.
    """
    active = []
    target_attrs = get_target_attributes(context.target)
    target_size = context.target.tile_size if context.target else 1

    for set_id, set_bonus in ALL_SET_BONUSES.items():
        # Check if set is active
        if not set_bonus.is_active(equipped_items):
            continue

        effect = set_bonus.effect

        # Check if effect applies to this combat style
        if not effect.applies_to_style(context.combat_style):
            continue

        # Check conditions
        if effect.condition.is_met(
            target_attributes=target_attrs,
            on_slayer_task=context.on_slayer_task,
            in_wilderness=context.in_wilderness,
            player_hp_percent=context.player_hp_percent,
            target_size=target_size,
            attack_type=context.attack_type,
            weapon_name=context.weapon_name,
        ):
            pieces = set_bonus.get_piece_count(equipped_items)
            active.append(ActiveEffect(
                effect=effect,
                source=f"{set_bonus.name} ({pieces}/{len(set_bonus.required_items)})",
                effective_proc_chance=effect.proc_chance,
            ))

    return active


def get_active_effects(context: CombatContext) -> List[ActiveEffect]:
    """Get all active effects for the current combat context.

    This is the main entry point for effect detection. It combines effects
    from the weapon, individual items, and set bonuses.

    Args:
        context: Combat context with all relevant information.

    Returns:
        List of all active effects (before stacking resolution).
    """
    active = []

    # Detect weapon effects
    active.extend(detect_weapon_effects(context.weapon_name, context))

    # Detect individual item effects
    active.extend(detect_item_effects(context.equipped_items, context))

    # Detect set bonuses
    active.extend(detect_set_bonuses(context.equipped_items, context))

    return active


def resolve_stacking(effects: List[ActiveEffect]) -> List[ActiveEffect]:
    """Apply stacking rules to resolve conflicting effects.

    Effects in the same stacking group don't stack - only the highest
    priority effect in each group applies.

    Args:
        effects: List of active effects.

    Returns:
        List of effects after stacking resolution.
    """
    # Group effects by their stacking group
    by_group: Dict[str, List[ActiveEffect]] = {}
    no_group: List[ActiveEffect] = []

    for eff in effects:
        if eff.stacking_group:
            if eff.stacking_group not in by_group:
                by_group[eff.stacking_group] = []
            by_group[eff.stacking_group].append(eff)
        else:
            no_group.append(eff)

    # For each stacking group, keep only highest priority
    resolved = list(no_group)
    for group, group_effects in by_group.items():
        # Sort by priority (descending) and take the first
        group_effects.sort(key=lambda e: e.stacking_priority, reverse=True)
        resolved.append(group_effects[0])

    return resolved


def calculate_dharok_multiplier(
    player_hp_percent: float,
    player_max_hp: int = 99,
) -> float:
    """Calculate Dharok's damage multiplier based on missing HP.

    Formula: 1 + (max_hp - current_hp) / max_hp
           = 1 + (1 - hp_percent) = 2 - hp_percent

    At 1 HP with 99 max HP: 1 + 98/99 = ~1.99x damage

    Args:
        player_hp_percent: Current HP as percentage (0.0-1.0).
        player_max_hp: Maximum HP level.

    Returns:
        Damage multiplier.
    """
    # Current HP from percentage
    current_hp = max(1, int(player_hp_percent * player_max_hp))
    missing_hp = player_max_hp - current_hp
    return 1.0 + (missing_hp / player_max_hp)


def resolve_modifiers(
    effects: List[ActiveEffect],
    context: CombatContext,
) -> ResolvedModifiers:
    """Resolve all active effects into final modifiers.

    This applies stacking rules and combines all modifiers into
    a single ResolvedModifiers object ready for DPS calculation.

    Args:
        effects: List of active effects.
        context: Combat context for special calculations.

    Returns:
        ResolvedModifiers with all combined values.
    """
    # Apply stacking rules
    resolved_effects = resolve_stacking(effects)

    # Separate always-active effects from proc effects
    always_active = [e for e in resolved_effects if e.effective_proc_chance >= 1.0]
    proc_effects = [e for e in resolved_effects if e.effective_proc_chance < 1.0]

    # Separate effects by additive group
    additive_groups: Dict[str, List[ActiveEffect]] = {}
    multiplicative_effects: List[ActiveEffect] = []

    for eff in always_active:
        if eff.effect.additive_group:
            group = eff.effect.additive_group
            if group not in additive_groups:
                additive_groups[group] = []
            additive_groups[group].append(eff)
        else:
            multiplicative_effects.append(eff)

    # Start with base modifier
    combined = EffectModifier()

    # Combine multiplicative effects normally
    for eff in multiplicative_effects:
        combined = combined.combine(eff.modifier)

    # Combine additive groups: sum (bonus - 1) then add 1
    for group, group_effects in additive_groups.items():
        acc_bonus = sum(eff.modifier.accuracy_mult - 1.0 for eff in group_effects)
        dmg_bonus = sum(eff.modifier.damage_mult - 1.0 for eff in group_effects)

        # Create a modifier for this additive group's total
        group_modifier = EffectModifier(
            accuracy_mult=1.0 + acc_bonus,
            damage_mult=1.0 + dmg_bonus,
        )
        combined = combined.combine(group_modifier)

    # Handle Dharok's scaling
    if combined.scales_with_missing_hp:
        dharok_mult = calculate_dharok_multiplier(
            context.player_hp_percent,
            context.player_max_hp,
        )
        combined = EffectModifier(
            accuracy_mult=combined.accuracy_mult,
            damage_mult=combined.damage_mult * dharok_mult,
            double_accuracy_roll=combined.double_accuracy_roll,
            min_hit_percent=combined.min_hit_percent,
            max_hit_percent=combined.max_hit_percent,
            extra_hits=combined.extra_hits,
            scales_with_target_magic=combined.scales_with_target_magic,
            scales_with_missing_hp=False,  # Already applied
            ignores_defence=combined.ignores_defence,
            ignores_prayer=combined.ignores_prayer,
        )

    return ResolvedModifiers(
        accuracy_mult=combined.accuracy_mult,
        damage_mult=combined.damage_mult,
        double_accuracy_roll=combined.double_accuracy_roll,
        min_hit_percent=combined.min_hit_percent,
        max_hit_percent=combined.max_hit_percent,
        extra_hits=combined.extra_hits,
        scales_with_target_magic=combined.scales_with_target_magic,
        scales_with_missing_hp=combined.scales_with_missing_hp,
        ignores_defence=combined.ignores_defence,
        ignores_prayer=combined.ignores_prayer,
        active_effects=always_active,
        proc_effects=proc_effects,
    )


class EffectEngine:
    """Main engine for evaluating passive effects.

    This class provides a convenient interface for detecting and resolving
    effects in combat calculations.

    Example:
        >>> engine = EffectEngine()
        >>> context = CombatContext(
        ...     combat_style=CombatStyle.MELEE,
        ...     attack_type="slash",
        ...     weapon_name="Scythe of vitur",
        ...     equipped_items=["scythe_of_vitur", "slayer_helmet_i"],
        ...     target=monster,
        ...     on_slayer_task=True,
        ... )
        >>> modifiers = engine.get_modifiers(context)
        >>> print(f"Accuracy: {modifiers.accuracy_mult:.2%}")
        >>> print(f"Damage: {modifiers.damage_mult:.2%}")
    """

    def get_active_effects(self, context: CombatContext) -> List[ActiveEffect]:
        """Get all active effects for a combat context.

        Args:
            context: Combat context.

        Returns:
            List of active effects before stacking resolution.
        """
        return get_active_effects(context)

    def get_modifiers(self, context: CombatContext) -> ResolvedModifiers:
        """Get resolved modifiers for a combat context.

        This is the main method to use when calculating DPS.

        Args:
            context: Combat context.

        Returns:
            ResolvedModifiers ready for DPS calculation.
        """
        effects = get_active_effects(context)
        return resolve_modifiers(effects, context)

    def get_modifiers_from_effects(
        self,
        effects: List[ActiveEffect],
        context: CombatContext,
    ) -> ResolvedModifiers:
        """Get resolved modifiers from a pre-computed effect list.

        Args:
            effects: Pre-computed list of active effects.
            context: Combat context.

        Returns:
            ResolvedModifiers ready for DPS calculation.
        """
        return resolve_modifiers(effects, context)


def format_active_effects(modifiers: ResolvedModifiers) -> str:
    """Format active effects for display.

    Args:
        modifiers: Resolved modifiers with active effects.

    Returns:
        Human-readable string describing active effects.
    """
    lines = []

    if modifiers.active_effects:
        lines.append("Active Effects:")
        for eff in modifiers.active_effects:
            mod = eff.modifier
            bonuses = []
            if mod.accuracy_mult != 1.0:
                bonuses.append(f"acc {mod.accuracy_mult:.2%}")
            if mod.damage_mult != 1.0:
                bonuses.append(f"dmg {mod.damage_mult:.2%}")
            if mod.double_accuracy_roll:
                bonuses.append("double acc roll")
            if mod.extra_hits:
                hits = "+".join(f"{h:.0%}" for h in mod.extra_hits)
                bonuses.append(f"extra hits: {hits}")

            bonus_str = ", ".join(bonuses) if bonuses else "special"
            lines.append(f"  - {eff.source}: {bonus_str}")

    if modifiers.proc_effects:
        lines.append("Proc Effects:")
        for eff in modifiers.proc_effects:
            lines.append(f"  - {eff.source}: {eff.effective_proc_chance:.1%} chance")

    if not modifiers.active_effects and not modifiers.proc_effects:
        lines.append("No passive effects active.")

    # Summary
    lines.append("")
    lines.append(f"Total Accuracy Multiplier: {modifiers.accuracy_mult:.2%}")
    lines.append(f"Total Damage Multiplier: {modifiers.damage_mult:.2%}")

    if modifiers.has_special_mechanics():
        lines.append("Special Mechanics:")
        if modifiers.double_accuracy_roll:
            lines.append("  - Double accuracy roll (hit if either succeeds)")
        if modifiers.min_hit_percent is not None:
            lines.append(f"  - Minimum hit: {modifiers.min_hit_percent:.0%} of max")
        if modifiers.max_hit_percent is not None:
            lines.append(f"  - Maximum hit: {modifiers.max_hit_percent:.0%} of base max")
        if modifiers.extra_hits:
            lines.append(f"  - Extra hits: {', '.join(f'{h:.0%}' for h in modifiers.extra_hits)}")
        if modifiers.scales_with_target_magic:
            lines.append("  - Scales with target's magic level")
        if modifiers.ignores_defence:
            lines.append("  - Can ignore target's defence")

    return "\n".join(lines)
