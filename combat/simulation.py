"""Combat simulation and DPS calculation for OSRS."""

import math
import random
from dataclasses import dataclass, field
from typing import Optional, Tuple, List

from .formulas import (
    effective_level,
    max_hit_melee,
    max_hit_ranged,
    max_hit_magic,
    attack_roll,
    defence_roll_npc,
    hit_chance,
    calculate_dps,
    calculate_kill_time,
    calculate_kills_per_hour,
    osmumtens_fang_hit_chance,
    osmumtens_fang_max_hit,
    osmumtens_fang_average_damage,
    scythe_hit_chance_and_damage,
    twisted_bow_multiplier,
    twisted_bow_effective_accuracy,
    twisted_bow_max_hit,
    FormulaBreakdown,
    format_formula_breakdown,
)
from .equipment import (
    Weapon,
    EquipmentStats,
    GearModifiers,
    AttackStyle,
    AttackType,
    CombatStyle,
    get_weapon,
    WEAPONS,
)
from .entities import MonsterStats, get_monster, MONSTERS
from .prayers import Prayer, get_prayer
from .effects import ResolvedModifiers, ActiveEffect
from .effect_engine import EffectEngine, CombatContext, format_active_effects
from data_loader.spell_loader import Spell


@dataclass
class PotionBoost:
    """Potion stat boosts."""
    attack: int = 0
    strength: int = 0
    defence: int = 0
    ranged: int = 0
    magic: int = 0

    @classmethod
    def super_combat(cls, base_level: int = 99) -> "PotionBoost":
        """Super combat potion boost (+5 + 15%)."""
        boost = 5 + math.floor(base_level * 0.15)
        return cls(attack=boost, strength=boost, defence=boost)

    @classmethod
    def super_attack(cls, base_level: int = 99) -> "PotionBoost":
        """Super attack potion boost (+5 + 15%)."""
        boost = 5 + math.floor(base_level * 0.15)
        return cls(attack=boost)

    @classmethod
    def super_strength(cls, base_level: int = 99) -> "PotionBoost":
        """Super strength potion boost (+5 + 15%)."""
        boost = 5 + math.floor(base_level * 0.15)
        return cls(strength=boost)

    @classmethod
    def ranging_potion(cls, base_level: int = 99) -> "PotionBoost":
        """Ranging potion boost (+4 + 10%)."""
        boost = 4 + math.floor(base_level * 0.10)
        return cls(ranged=boost)

    @classmethod
    def divine_ranging(cls, base_level: int = 99) -> "PotionBoost":
        """Divine ranging potion boost (+5 + 15%)."""
        boost = 5 + math.floor(base_level * 0.15)
        return cls(ranged=boost)

    @classmethod
    def imbued_heart(cls, base_level: int = 99) -> "PotionBoost":
        """Imbued heart boost (+1 + 10%)."""
        boost = 1 + math.floor(base_level * 0.10)
        return cls(magic=boost)

    @classmethod
    def saturated_heart(cls, base_level: int = 99) -> "PotionBoost":
        """Saturated heart boost (+4 + 10%)."""
        boost = 4 + math.floor(base_level * 0.10)
        return cls(magic=boost)


@dataclass
class CombatStats:
    """Player combat stats."""
    attack: int = 99
    strength: int = 99
    defence: int = 99
    ranged: int = 99
    magic: int = 99
    hitpoints: int = 99
    prayer: int = 99


@dataclass
class CombatSetup:
    """Complete combat setup for DPS calculation."""
    # Player stats
    stats: CombatStats = field(default_factory=CombatStats)

    # Equipment
    weapon: Optional[Weapon] = None
    equipment_stats: EquipmentStats = field(default_factory=EquipmentStats)
    gear_modifiers: GearModifiers = field(default_factory=GearModifiers)

    # Combat settings
    attack_style: AttackStyle = AttackStyle.AGGRESSIVE
    prayer: Prayer = Prayer.NONE
    potion: PotionBoost = field(default_factory=PotionBoost)

    # Target
    target: Optional[MonsterStats] = None
    on_slayer_task: bool = False

    # New fields for passive effects system
    equipped_items: List[str] = field(default_factory=list)  # For set/item effect detection
    in_wilderness: bool = False  # For wilderness weapon effects
    player_hp_percent: float = 1.0  # For Dharok's (0.0-1.0, where 1.0 = full HP)

    # Target stat modifiers (for DWH, BGS, Arclight specs, etc.)
    # These are reductions applied to the target's base stats
    target_defence_reduction: float = 0.0  # 0.0-1.0, e.g., 0.3 for one DWH spec
    target_magic_reduction: float = 0.0    # 0.0-1.0, for vulnerability etc.

    # Spell for autocast magic weapons (non-powered staves)
    spell: Optional[Spell] = None

    def __post_init__(self):
        # If weapon provided, add its stats to equipment stats
        if self.weapon:
            self.equipment_stats = self.equipment_stats + self.weapon.stats
        # Auto-add weapon to equipped items if not already present
        if self.weapon and self.weapon.name:
            weapon_key = self.weapon.name.lower().replace(" ", "_").replace("'", "")
            if weapon_key not in [item.lower().replace(" ", "_").replace("'", "") for item in self.equipped_items]:
                self.equipped_items = list(self.equipped_items) + [weapon_key]


@dataclass
class CombatResult:
    """Results of a DPS calculation."""
    dps: float
    max_hit: int
    hit_chance: float
    attack_roll: int
    defence_roll: int

    # Weapon info
    weapon_name: str = ""
    attack_speed_ticks: int = 4

    # Formula breakdown (populated when track_formula=True)
    formula_breakdown: Optional[FormulaBreakdown] = None

    # Active effects (populated when use_effects=True)
    active_effects: Optional[ResolvedModifiers] = None

    # Spell used (for autocast magic weapons)
    spell_used: Optional[str] = None

    # Derived values
    @property
    def attack_speed_seconds(self) -> float:
        """Attack speed in seconds."""
        return self.attack_speed_ticks * 0.6

    @property
    def damage_per_attack(self) -> float:
        """Expected damage per attack."""
        return self.hit_chance * (self.max_hit / 2.0)

    def calculate_kill_time(self, hitpoints: int) -> float:
        """Calculate average time to kill a target with given HP."""
        if self.dps <= 0:
            return float('inf')
        return hitpoints / self.dps

    def calculate_kills_per_hour(self, hitpoints: int, overhead_seconds: float = 0.0) -> float:
        """Calculate kills per hour."""
        kill_time = self.calculate_kill_time(hitpoints)
        total_time = kill_time + overhead_seconds
        if total_time <= 0:
            return 0.0
        return 3600 / total_time


class CombatCalculator:
    """Calculator for OSRS combat DPS."""

    def __init__(self, setup: CombatSetup, use_effects: bool = False):
        """Initialize with a combat setup.

        Args:
            setup: The complete combat setup.
            use_effects: If True, use the new passive effects system.
                        If False (default), use legacy GearModifiers for
                        backwards compatibility.
        """
        self.setup = setup
        self.use_effects = use_effects
        self._effect_engine = EffectEngine() if use_effects else None
        self._resolved_modifiers: Optional[ResolvedModifiers] = None

    def _get_effect_modifiers(self) -> ResolvedModifiers:
        """Get resolved modifiers from the effect system.

        Returns:
            ResolvedModifiers with all active effects applied.
        """
        if self._resolved_modifiers is not None:
            return self._resolved_modifiers

        weapon = self.setup.weapon
        target = self.setup.target

        context = CombatContext(
            combat_style=weapon.combat_style if weapon else CombatStyle.MELEE,
            attack_type=weapon.attack_type.value if weapon else "slash",
            weapon_name=weapon.name if weapon else "",
            equipped_items=self.setup.equipped_items,
            target=target,
            on_slayer_task=self.setup.on_slayer_task,
            in_wilderness=self.setup.in_wilderness,
            player_hp_percent=self.setup.player_hp_percent,
            player_max_hp=self.setup.stats.hitpoints,
        )

        self._resolved_modifiers = self._effect_engine.get_modifiers(context)
        return self._resolved_modifiers

    def calculate(self, track_formula: bool = False) -> CombatResult:
        """Calculate DPS for the current setup.

        Args:
            track_formula: If True, include formula breakdown in result.

        Returns:
            CombatResult with all calculated values.
        """
        weapon = self.setup.weapon
        if weapon is None:
            return CombatResult(
                dps=0.0,
                max_hit=0,
                hit_chance=0.0,
                attack_roll=0,
                defence_roll=0,
            )

        # Dispatch based on combat style
        if weapon.combat_style == CombatStyle.MELEE:
            return self._calculate_melee(track_formula)
        elif weapon.combat_style == CombatStyle.RANGED:
            return self._calculate_ranged(track_formula)
        else:
            return self._calculate_magic(track_formula)

    def _calculate_melee(self, track_formula: bool = False) -> CombatResult:
        """Calculate melee DPS."""
        setup = self.setup
        weapon = setup.weapon
        stats = setup.stats
        prayer = setup.prayer
        style = setup.attack_style
        target = setup.target

        # Get modifiers from either effect system or legacy GearModifiers
        if self.use_effects:
            modifiers = self._get_effect_modifiers()
            accuracy_mult = modifiers.accuracy_mult
            damage_mult = modifiers.damage_mult
            # In effect system, void is included in the modifiers
            void_accuracy = 1.0
            void_damage = 1.0
        else:
            # Legacy: get gear multipliers
            vs_undead = target.is_undead if target else False
            vs_dragon = target.is_dragon if target else False
            on_task = setup.on_slayer_task

            accuracy_mult = setup.gear_modifiers.get_accuracy_multiplier(
                CombatStyle.MELEE, weapon.attack_type,
                vs_undead=vs_undead, vs_dragon=vs_dragon, on_slayer_task=on_task
            )
            damage_mult = setup.gear_modifiers.get_damage_multiplier(
                CombatStyle.MELEE, weapon.attack_type,
                vs_undead=vs_undead, vs_dragon=vs_dragon, on_slayer_task=on_task
            )

            # Void multipliers
            void_accuracy = 1.1 if setup.gear_modifiers.void_melee else 1.0
            void_damage = 1.1 if setup.gear_modifiers.void_melee else 1.0
            modifiers = None

        # Effective levels
        eff_attack = effective_level(
            base_level=stats.attack,
            boost=setup.potion.attack,
            prayer_multiplier=prayer.attack_multiplier,
            style_bonus=style.attack_bonus,
            void_multiplier=void_accuracy
        )

        eff_strength = effective_level(
            base_level=stats.strength,
            boost=setup.potion.strength,
            prayer_multiplier=prayer.strength_multiplier,
            style_bonus=style.strength_bonus,
            void_multiplier=void_damage
        )

        # Attack bonus from equipment
        equip_attack_bonus = setup.equipment_stats.get_attack_bonus(weapon.attack_type)
        strength_bonus = setup.equipment_stats.melee_strength

        # Calculate attack roll
        atk_roll = attack_roll(eff_attack, equip_attack_bonus, accuracy_mult)

        # Calculate max hit
        max_dmg = max_hit_melee(eff_strength, strength_bonus, damage_mult)

        # Defence roll (with optional reduction from DWH/BGS specs)
        def_roll = 0
        def_bonus = 0
        def_level = 0
        if target:
            def_bonus = target.get_defence_bonus(weapon.attack_type.value)
            def_level = target.defence_level
            # Apply defence reduction (e.g., from DWH spec)
            if setup.target_defence_reduction > 0:
                def_level = max(0, int(def_level * (1 - setup.target_defence_reduction)))
            def_roll = defence_roll_npc(def_level, def_bonus)

        # Hit chance
        accuracy = hit_chance(atk_roll, def_roll)

        # Special weapon handling
        attack_speed = weapon.attack_speed
        avg_damage = max_dmg / 2.0

        # Handle special mechanics from effect system
        if self.use_effects and modifiers:
            # Osmumten's Fang: double accuracy roll, min/max hit
            if modifiers.double_accuracy_roll:
                accuracy = osmumtens_fang_hit_chance(atk_roll, def_roll)
            if modifiers.min_hit_percent is not None and modifiers.max_hit_percent is not None:
                min_hit = math.floor(max_dmg * modifiers.min_hit_percent)
                max_hit = math.floor(max_dmg * modifiers.max_hit_percent)
                avg_damage = osmumtens_fang_average_damage(min_hit, max_hit)
                max_dmg = max_hit

            # Scythe: extra hits based on target size
            if modifiers.extra_hits and target:
                accuracy, avg_damage = scythe_hit_chance_and_damage(
                    atk_roll, def_roll, max_dmg, target.tile_size
                )
        else:
            # Legacy: handle special weapons by name
            if weapon.name == "Osmumten's fang":
                accuracy = osmumtens_fang_hit_chance(atk_roll, def_roll)
                min_hit, max_hit = osmumtens_fang_max_hit(max_dmg)
                avg_damage = osmumtens_fang_average_damage(min_hit, max_hit)
                max_dmg = max_hit

            if weapon.name == "Scythe of vitur" and target:
                accuracy, avg_damage = scythe_hit_chance_and_damage(
                    atk_roll, def_roll, max_dmg, target.tile_size
                )

        # DPS calculation
        dps = accuracy * avg_damage / (attack_speed * 0.6)

        # Build formula breakdown if requested
        breakdown = None
        if track_formula:
            breakdown = FormulaBreakdown(
                combat_style="melee",
                base_level=stats.attack,
                boost=setup.potion.attack,
                prayer_mult=prayer.attack_multiplier,
                style_bonus=style.attack_bonus,
                void_mult=void_accuracy,
                effective_attack=eff_attack,
                effective_strength=eff_strength,
                strength_bonus=strength_bonus,
                gear_mult_damage=damage_mult,
                max_hit=max_dmg,
                attack_bonus=equip_attack_bonus,
                gear_mult_accuracy=accuracy_mult,
                attack_roll=atk_roll,
                defence_level=def_level,
                defence_bonus=def_bonus,
                defence_roll=def_roll,
                hit_chance=accuracy,
                attack_speed_ticks=attack_speed,
                dps=dps,
            )

        return CombatResult(
            dps=dps,
            max_hit=max_dmg,
            hit_chance=accuracy,
            attack_roll=atk_roll,
            defence_roll=def_roll,
            weapon_name=weapon.name,
            attack_speed_ticks=attack_speed,
            formula_breakdown=breakdown,
            active_effects=modifiers if self.use_effects else None,
        )

    def _calculate_ranged(self, track_formula: bool = False) -> CombatResult:
        """Calculate ranged DPS."""
        setup = self.setup
        weapon = setup.weapon
        stats = setup.stats
        prayer = setup.prayer
        style = setup.attack_style
        target = setup.target

        # Get modifiers from either effect system or legacy GearModifiers
        if self.use_effects:
            modifiers = self._get_effect_modifiers()
            accuracy_mult = modifiers.accuracy_mult
            damage_mult = modifiers.damage_mult
            void_accuracy = 1.0
            void_damage = 1.0
        else:
            # Legacy: get gear multipliers
            vs_undead = target.is_undead if target else False
            vs_dragon = target.is_dragon if target else False
            on_task = setup.on_slayer_task

            accuracy_mult = setup.gear_modifiers.get_accuracy_multiplier(
                CombatStyle.RANGED, AttackType.RANGED,
                vs_undead=vs_undead, vs_dragon=vs_dragon, on_slayer_task=on_task
            )
            damage_mult = setup.gear_modifiers.get_damage_multiplier(
                CombatStyle.RANGED, AttackType.RANGED,
                vs_undead=vs_undead, vs_dragon=vs_dragon, on_slayer_task=on_task
            )

            # Void multipliers
            void_accuracy = 1.1 if setup.gear_modifiers.void_ranged else 1.0
            void_damage = 1.1 if setup.gear_modifiers.void_ranged else 1.0
            if setup.gear_modifiers.elite_void and setup.gear_modifiers.void_ranged:
                void_damage += 0.025
            modifiers = None

        # Effective ranged level
        style_atk_bonus = style.attack_bonus if style.combat_style == CombatStyle.RANGED else 0
        style_str_bonus = style.strength_bonus if style.combat_style == CombatStyle.RANGED else 0

        eff_ranged = effective_level(
            base_level=stats.ranged,
            boost=setup.potion.ranged,
            prayer_multiplier=prayer.ranged_attack_multiplier,
            style_bonus=style_atk_bonus,
            void_multiplier=void_accuracy
        )

        eff_ranged_str = effective_level(
            base_level=stats.ranged,
            boost=setup.potion.ranged,
            prayer_multiplier=prayer.ranged_strength_multiplier,
            style_bonus=style_str_bonus,
            void_multiplier=void_damage
        )

        # Attack and strength bonuses from equipment
        ranged_attack_bonus = setup.equipment_stats.ranged_attack
        ranged_strength_bonus = setup.equipment_stats.ranged_strength

        # Calculate attack roll
        atk_roll = attack_roll(eff_ranged, ranged_attack_bonus, accuracy_mult)

        # Calculate max hit
        max_dmg = max_hit_ranged(eff_ranged_str, ranged_strength_bonus, damage_mult)

        # Defence roll (with optional reduction from DWH/BGS specs)
        def_roll = 0
        def_level = 0
        def_bonus = 0
        if target:
            def_level = target.defence_level
            # Apply defence reduction (e.g., from DWH spec)
            if setup.target_defence_reduction > 0:
                def_level = max(0, int(def_level * (1 - setup.target_defence_reduction)))
            def_bonus = target.ranged_defence
            def_roll = defence_roll_npc(def_level, def_bonus)

        # Hit chance
        accuracy = hit_chance(atk_roll, def_roll)

        # Handle Twisted Bow scaling
        if self.use_effects and modifiers and modifiers.scales_with_target_magic:
            # Twisted bow: scale with target's magic level
            target_magic = target.magic_level if target else 1
            tbow_acc_mult, tbow_dmg_mult = twisted_bow_multiplier(target_magic)
            # Apply tbow multipliers on top of base attack roll and max hit
            atk_roll = math.floor(atk_roll * tbow_acc_mult)
            max_dmg = math.floor(max_dmg * tbow_dmg_mult)
            accuracy = hit_chance(atk_roll, def_roll)
        elif weapon.name == "Twisted bow" and target:
            # Legacy: handle Twisted bow by name
            target_magic = target.magic_level
            tbow_acc_mult, tbow_dmg_mult = twisted_bow_multiplier(target_magic)
            atk_roll = math.floor(atk_roll * tbow_acc_mult)
            max_dmg = math.floor(max_dmg * tbow_dmg_mult)
            accuracy = hit_chance(atk_roll, def_roll)

        # Attack speed
        attack_speed = weapon.attack_speed

        # DPS calculation
        dps = calculate_dps(accuracy, max_dmg, attack_speed)

        # Build formula breakdown if requested
        breakdown = None
        if track_formula:
            breakdown = FormulaBreakdown(
                combat_style="ranged",
                base_level=stats.ranged,
                boost=setup.potion.ranged,
                prayer_mult=prayer.ranged_attack_multiplier,
                style_bonus=style_atk_bonus,
                void_mult=void_accuracy,
                effective_attack=eff_ranged,
                effective_strength=eff_ranged_str,
                strength_bonus=ranged_strength_bonus,
                gear_mult_damage=damage_mult,
                max_hit=max_dmg,
                attack_bonus=ranged_attack_bonus,
                gear_mult_accuracy=accuracy_mult,
                attack_roll=atk_roll,
                defence_level=def_level,
                defence_bonus=def_bonus,
                defence_roll=def_roll,
                hit_chance=accuracy,
                attack_speed_ticks=attack_speed,
                dps=dps,
            )

        return CombatResult(
            dps=dps,
            max_hit=max_dmg,
            hit_chance=accuracy,
            attack_roll=atk_roll,
            defence_roll=def_roll,
            weapon_name=weapon.name,
            attack_speed_ticks=attack_speed,
            formula_breakdown=breakdown,
            active_effects=modifiers if self.use_effects else None,
        )

    def _calculate_magic(self, track_formula: bool = False) -> CombatResult:
        """Calculate magic DPS."""
        setup = self.setup
        weapon = setup.weapon
        stats = setup.stats
        prayer = setup.prayer
        target = setup.target

        # Get modifiers from either effect system or legacy GearModifiers
        if self.use_effects:
            modifiers = self._get_effect_modifiers()
            accuracy_mult = modifiers.accuracy_mult
            damage_mult = modifiers.damage_mult
            void_accuracy = 1.0
            void_damage = 1.0
        else:
            # Legacy: get gear multipliers
            vs_undead = target.is_undead if target else False
            on_task = setup.on_slayer_task

            accuracy_mult = setup.gear_modifiers.get_accuracy_multiplier(
                CombatStyle.MAGIC, AttackType.MAGIC,
                vs_undead=vs_undead, on_slayer_task=on_task
            )
            damage_mult = setup.gear_modifiers.get_damage_multiplier(
                CombatStyle.MAGIC, AttackType.MAGIC,
                vs_undead=vs_undead, on_slayer_task=on_task
            )

            # Void multipliers
            void_accuracy = 1.45 if setup.gear_modifiers.void_magic else 1.0
            void_damage = 1.0
            if setup.gear_modifiers.elite_void and setup.gear_modifiers.void_magic:
                void_damage = 1.025
            modifiers = None

        # Effective magic level
        eff_magic = effective_level(
            base_level=stats.magic,
            boost=setup.potion.magic,
            prayer_multiplier=prayer.magic_attack_multiplier,
            style_bonus=0,  # Magic typically doesn't have style bonus
            void_multiplier=void_accuracy,
            is_magic=True  # Magic uses +9 constant instead of +8
        )

        # Attack bonus from equipment
        magic_attack_bonus = setup.equipment_stats.magic_attack

        # Calculate attack roll
        atk_roll = attack_roll(eff_magic, magic_attack_bonus, accuracy_mult)

        # Max hit from spell/staff
        # Priority: 1) Explicit spell, 2) Powered staff built-in, 3) Zero (no spell)
        spell_used = None
        if setup.spell:
            base_max = setup.spell.base_max_hit
            spell_used = setup.spell.name
        elif weapon.base_magic_max_hit > 0:
            base_max = weapon.base_magic_max_hit  # Powered staff (Trident, Sang, Shadow)
        else:
            base_max = 0  # No spell configured

        magic_damage_bonus = setup.equipment_stats.magic_damage
        max_dmg = max_hit_magic(base_max, magic_damage_bonus, damage_mult * void_damage)

        # Defence roll (uses magic level for magic defence, with optional reductions)
        def_roll = 0
        def_level = 0
        def_bonus = 0
        if target:
            def_level = target.magic_level  # Magic uses magic level for defence
            actual_def_level = target.defence_level
            # Apply magic reduction (e.g., from vulnerability)
            if setup.target_magic_reduction > 0:
                def_level = max(0, int(def_level * (1 - setup.target_magic_reduction)))
            # Apply defence reduction (e.g., from DWH spec)
            if setup.target_defence_reduction > 0:
                actual_def_level = max(0, int(actual_def_level * (1 - setup.target_defence_reduction)))
            def_bonus = target.magic_defence
            def_roll = defence_roll_npc(
                actual_def_level,
                def_bonus,
                def_level,
                is_magic_attack=True
            )

        # Hit chance
        accuracy = hit_chance(atk_roll, def_roll)

        # Attack speed
        attack_speed = weapon.attack_speed

        # DPS calculation
        dps = calculate_dps(accuracy, max_dmg, attack_speed)

        # Build formula breakdown if requested
        breakdown = None
        if track_formula:
            breakdown = FormulaBreakdown(
                combat_style="magic",
                base_level=stats.magic,
                boost=setup.potion.magic,
                prayer_mult=prayer.magic_attack_multiplier,
                style_bonus=0,
                void_mult=void_accuracy,
                effective_attack=eff_magic,
                effective_strength=eff_magic,  # Magic uses same level
                strength_bonus=0,
                gear_mult_damage=damage_mult * void_damage,
                max_hit=max_dmg,
                attack_bonus=magic_attack_bonus,
                gear_mult_accuracy=accuracy_mult,
                attack_roll=atk_roll,
                defence_level=def_level,
                defence_bonus=def_bonus,
                defence_roll=def_roll,
                hit_chance=accuracy,
                attack_speed_ticks=attack_speed,
                dps=dps,
                base_magic_max=base_max,
                magic_damage_bonus=magic_damage_bonus,
            )

        return CombatResult(
            dps=dps,
            max_hit=max_dmg,
            hit_chance=accuracy,
            attack_roll=atk_roll,
            defence_roll=def_roll,
            weapon_name=weapon.name,
            attack_speed_ticks=attack_speed,
            formula_breakdown=breakdown,
            active_effects=modifiers if self.use_effects else None,
            spell_used=spell_used,
        )


def simulate_kill(
    result: CombatResult,
    hitpoints: int,
    num_simulations: int = 1000,
    seed: Optional[int] = None
) -> Tuple[float, float, List[float]]:
    """Monte Carlo simulation of kill times.

    Args:
        result: CombatResult from DPS calculation.
        hitpoints: Target's hitpoints.
        num_simulations: Number of kills to simulate.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (average_time, std_dev, all_times).
    """
    if seed is not None:
        random.seed(seed)

    kill_times = []
    attack_interval = result.attack_speed_ticks * 0.6

    for _ in range(num_simulations):
        hp_remaining = hitpoints
        time_elapsed = 0.0

        while hp_remaining > 0:
            # Roll for hit
            if random.random() < result.hit_chance:
                # Hit - roll damage
                damage = random.randint(0, result.max_hit)
                hp_remaining -= damage

            time_elapsed += attack_interval

        kill_times.append(time_elapsed)

    avg_time = sum(kill_times) / len(kill_times)
    variance = sum((t - avg_time) ** 2 for t in kill_times) / len(kill_times)
    std_dev = math.sqrt(variance)

    return avg_time, std_dev, kill_times


def quick_dps(
    weapon_name: str,
    monster_name: str,
    attack_level: int = 99,
    strength_level: int = 99,
    ranged_level: int = 99,
    magic_level: int = 99,
    prayer_name: str = "none",
    potion: Optional[PotionBoost] = None,
    on_slayer_task: bool = False,
) -> Optional[CombatResult]:
    """Quick DPS calculation with minimal setup.

    Args:
        weapon_name: Weapon key name.
        monster_name: Monster key name.
        attack_level: Attack level (for melee).
        strength_level: Strength level (for melee).
        ranged_level: Ranged level.
        magic_level: Magic level.
        prayer_name: Prayer name.
        potion: Potion boost, or None for super combat/ranging.
        on_slayer_task: Whether on slayer task.

    Returns:
        CombatResult, or None if weapon/monster not found.
    """
    weapon = get_weapon(weapon_name)
    if weapon is None:
        return None

    monster = get_monster(monster_name)
    if monster is None:
        return None

    prayer = get_prayer(prayer_name) or Prayer.NONE

    # Default potion based on combat style
    if potion is None:
        if weapon.combat_style == CombatStyle.MELEE:
            potion = PotionBoost.super_combat()
        elif weapon.combat_style == CombatStyle.RANGED:
            potion = PotionBoost.divine_ranging()
        else:
            potion = PotionBoost.saturated_heart()

    # Determine attack style
    if weapon.combat_style == CombatStyle.MELEE:
        style = AttackStyle.AGGRESSIVE
    elif weapon.combat_style == CombatStyle.RANGED:
        style = AttackStyle.RAPID
    else:
        style = AttackStyle.AUTOCAST

    # For magic weapons without a built-in spell, auto-select best spell
    selected_spell = None
    if weapon.combat_style == CombatStyle.MAGIC and weapon.base_magic_max_hit == 0:
        from .equipment import _get_best_autocast_spell
        selected_spell = _get_best_autocast_spell(weapon.name, magic_level)

    stats = CombatStats(
        attack=attack_level,
        strength=strength_level,
        ranged=ranged_level,
        magic=magic_level,
    )

    setup = CombatSetup(
        stats=stats,
        weapon=weapon,
        attack_style=style,
        prayer=prayer,
        potion=potion,
        target=monster,
        on_slayer_task=on_slayer_task,
        spell=selected_spell,
    )

    calculator = CombatCalculator(setup)
    return calculator.calculate()
