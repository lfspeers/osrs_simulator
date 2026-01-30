"""Definitions for all OSRS passive effects and set bonuses.

This module contains all effect definitions as code rather than JSON/data files.
Effects are organized by priority/type and include all necessary data for
accurate DPS calculations.
"""

from typing import Dict, List

from .equipment import CombatStyle
from .effects import (
    PassiveEffect,
    SetBonus,
    EffectCondition,
    EffectModifier,
    SourceType,
)


# =============================================================================
# Stacking Groups
# =============================================================================

STACKING_GROUPS: Dict[str, List[str]] = {
    # Salve amulet and slayer helm/black mask don't stack - salve takes priority
    # Note: Black mask is the base component of slayer helm, same effect
    # Note: Salve amulet (neck slot) CAN stack with void (different slots)
    "slayer_undead": [
        "salve_ei",      # Priority 5 (highest) - 20% all styles vs undead
        "salve_e",       # Priority 4 - 20% melee vs undead
        "salve",         # Priority 3 - 15% melee vs undead
        "slayer_helm_i", # Priority 2 - 16.67% all styles on task
        "slayer_helm",   # Priority 1 (lowest) - 16.67% melee on task
        # Note: black_mask and black_mask_i are included in slayer_helm source_items
        # so they activate the same effect - no separate entry needed
    ],

    # Void sets are mutually exclusive - can only wear one void helm type
    # All void sets require the same body/legs/gloves, only helm differs
    "void_set": [
        "elite_void_ranged",  # Priority 5 (highest) - 12.5% damage
        "elite_void_mage",    # Priority 4 - 2.5% damage
        "void_ranged",        # Priority 3 - 10% acc, 10% damage
        "void_melee",         # Priority 2 - 10% acc, 10% damage
        "void_mage",          # Priority 1 (lowest) - 45% acc only
    ],

    # NOTE: Equipment slot constraints (enforced by game, no stacking group needed):
    # - Void helm, Slayer helm, and Crystal helm all use the HEAD slot
    # - You cannot wear more than one at a time
    #
    # IMPORTANT STACKING INTERACTIONS:
    # - Void + Salve amulet: CAN stack (different slots: head vs neck)
    # - Void + Slayer helm: CANNOT stack (same slot: head) - enforced by equipment
    # - Salve + Slayer helm: DO NOT stack bonuses (slayer_undead group)
    #
    # CRYSTAL ARMOR (individual piece bonuses, +5% acc/dmg each with crystal bow/bofa):
    # - Crystal body + Crystal legs + Slayer helm: CAN stack (+10% from armor + 16.67% from helm)
    # - Crystal body + Crystal legs + Salve: CAN stack (+10% from armor + 20% from salve)
    # - Full crystal (helm+body+legs): +15% total, but helm conflicts with slayer helm
}


# =============================================================================
# Priority 1: Basic Equipment Effects (Port from GearModifiers)
# =============================================================================

VOID_MELEE = PassiveEffect(
    id="void_melee",
    name="Void Knight Melee",
    source_type=SourceType.SET,
    source_items=["void_melee_helm", "void_knight_top", "void_knight_robe", "void_knight_gloves"],
    combat_styles=[CombatStyle.MELEE],
    modifier=EffectModifier(accuracy_mult=1.10, damage_mult=1.10),
    stacking_group="void_set",
    stacking_priority=2,
    description="+10% accuracy and damage for melee",
)

VOID_RANGED = PassiveEffect(
    id="void_ranged",
    name="Void Knight Ranged",
    source_type=SourceType.SET,
    source_items=["void_ranger_helm", "void_knight_top", "void_knight_robe", "void_knight_gloves"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(accuracy_mult=1.10, damage_mult=1.10),
    stacking_group="void_set",
    stacking_priority=3,
    description="+10% accuracy and damage for ranged",
)

VOID_MAGIC = PassiveEffect(
    id="void_magic",
    name="Void Knight Magic",
    source_type=SourceType.SET,
    source_items=["void_mage_helm", "void_knight_top", "void_knight_robe", "void_knight_gloves"],
    combat_styles=[CombatStyle.MAGIC],
    modifier=EffectModifier(accuracy_mult=1.45, damage_mult=1.0),
    stacking_group="void_set",
    stacking_priority=1,
    description="+45% magic accuracy",
)

ELITE_VOID_RANGED = PassiveEffect(
    id="elite_void_ranged",
    name="Elite Void Knight Ranged",
    source_type=SourceType.SET,
    source_items=["void_ranger_helm", "elite_void_top", "elite_void_robe", "void_knight_gloves"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(accuracy_mult=1.10, damage_mult=1.125),
    stacking_group="void_set",
    stacking_priority=5,
    description="+10% accuracy, +12.5% damage for ranged",
)

ELITE_VOID_MAGIC = PassiveEffect(
    id="elite_void_magic",
    name="Elite Void Knight Magic",
    source_type=SourceType.SET,
    source_items=["void_mage_helm", "elite_void_top", "elite_void_robe", "void_knight_gloves"],
    combat_styles=[CombatStyle.MAGIC],
    modifier=EffectModifier(accuracy_mult=1.45, damage_mult=1.025),
    stacking_group="void_set",
    stacking_priority=4,
    description="+45% magic accuracy, +2.5% magic damage",
)

SLAYER_HELM = PassiveEffect(
    id="slayer_helm",
    name="Slayer Helmet",
    source_type=SourceType.ARMOR,
    source_items=["slayer_helmet", "black_mask"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(on_slayer_task=True),
    modifier=EffectModifier(accuracy_mult=7/6, damage_mult=7/6),
    stacking_group="slayer_undead",
    stacking_priority=1,
    description="7/6x (~16.67%) accuracy and damage on slayer task (melee only)",
)

SLAYER_HELM_IMBUED = PassiveEffect(
    id="slayer_helm_i",
    name="Slayer Helmet (i)",
    source_type=SourceType.ARMOR,
    source_items=["slayer_helmet_i", "black_mask_i"],
    combat_styles=[CombatStyle.MELEE, CombatStyle.RANGED, CombatStyle.MAGIC],
    condition=EffectCondition(on_slayer_task=True),
    modifier=EffectModifier(accuracy_mult=7/6, damage_mult=7/6),
    stacking_group="slayer_undead",
    stacking_priority=2,
    description="7/6x (~16.67%) accuracy and damage on slayer task (all styles)",
)

SALVE_AMULET = PassiveEffect(
    id="salve",
    name="Salve Amulet",
    source_type=SourceType.AMULET,
    source_items=["salve_amulet"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(vs_attribute="undead"),
    modifier=EffectModifier(accuracy_mult=7/6, damage_mult=7/6),
    stacking_group="slayer_undead",
    stacking_priority=3,
    description="7/6x (~16.67%) accuracy and damage vs undead (melee only)",
)

SALVE_AMULET_E = PassiveEffect(
    id="salve_e",
    name="Salve Amulet (e)",
    source_type=SourceType.AMULET,
    source_items=["salve_amulet_e"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(vs_attribute="undead"),
    modifier=EffectModifier(accuracy_mult=1.20, damage_mult=1.20),
    stacking_group="slayer_undead",
    stacking_priority=4,
    description="+20% accuracy and damage vs undead (melee only)",
)

SALVE_AMULET_EI = PassiveEffect(
    id="salve_ei",
    name="Salve Amulet (ei)",
    source_type=SourceType.AMULET,
    source_items=["salve_amulet_ei"],
    combat_styles=[CombatStyle.MELEE, CombatStyle.RANGED, CombatStyle.MAGIC],
    condition=EffectCondition(vs_attribute="undead"),
    modifier=EffectModifier(accuracy_mult=1.20, damage_mult=1.20),
    stacking_group="slayer_undead",
    stacking_priority=5,
    description="+20% accuracy and damage vs undead (all styles)",
)

DRAGON_HUNTER_LANCE = PassiveEffect(
    id="dh_lance",
    name="Dragon Hunter Lance",
    source_type=SourceType.WEAPON,
    source_items=["dragon_hunter_lance"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(vs_attribute="dragon"),
    modifier=EffectModifier(accuracy_mult=1.20, damage_mult=1.20),
    description="+20% accuracy and damage vs dragons",
)

DRAGON_HUNTER_CROSSBOW = PassiveEffect(
    id="dhcb",
    name="Dragon Hunter Crossbow",
    source_type=SourceType.WEAPON,
    source_items=["dragon_hunter_crossbow"],
    combat_styles=[CombatStyle.RANGED],
    condition=EffectCondition(vs_attribute="dragon"),
    modifier=EffectModifier(accuracy_mult=1.30, damage_mult=1.25),
    description="+30% accuracy, +25% damage vs dragons",
)

INQUISITOR_SET = PassiveEffect(
    id="inquisitor",
    name="Inquisitor's Armour",
    source_type=SourceType.SET,
    source_items=["inquisitor_helm", "inquisitor_hauberk", "inquisitor_plateskirt"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(using_attack_type="crush"),
    modifier=EffectModifier(accuracy_mult=1.025, damage_mult=1.025),
    description="+2.5% accuracy and damage with crush attacks",
)

OBSIDIAN_SET = PassiveEffect(
    id="obsidian",
    name="Obsidian Armour Set",
    source_type=SourceType.SET,
    source_items=["obsidian_helmet", "obsidian_platebody", "obsidian_platelegs"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(using_specific_weapon=["toktz", "tzhaar", "obsidian"]),
    modifier=EffectModifier(accuracy_mult=1.10, damage_mult=1.10),
    description="+10% accuracy and damage with obsidian weapons",
)


# =============================================================================
# Priority 2: Weapon Mechanics
# =============================================================================

OSMUMTENS_FANG = PassiveEffect(
    id="fang",
    name="Osmumten's Fang",
    source_type=SourceType.WEAPON,
    source_items=["osmumtens_fang", "osmumten's_fang"],
    combat_styles=[CombatStyle.MELEE],
    modifier=EffectModifier(
        double_accuracy_roll=True,
        min_hit_percent=0.15,
        max_hit_percent=0.85,
    ),
    description="Rolls accuracy twice (hit if either succeeds), damage range 15-85% of max",
)

SCYTHE_OF_VITUR = PassiveEffect(
    id="scythe",
    name="Scythe of Vitur",
    source_type=SourceType.WEAPON,
    source_items=["scythe_of_vitur"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(target_size_min=1),  # Always applies, size determines hits
    modifier=EffectModifier(extra_hits=[0.5, 0.25]),  # 2nd hit 50%, 3rd hit 25%
    description="Hits up to 3 times (100%/50%/25%) on large targets",
)

TWISTED_BOW = PassiveEffect(
    id="tbow",
    name="Twisted Bow",
    source_type=SourceType.WEAPON,
    source_items=["twisted_bow"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(scales_with_target_magic=True),
    description="Accuracy and damage scale with target's magic level",
)

KERIS_PARTISAN = PassiveEffect(
    id="keris",
    name="Keris Partisan",
    source_type=SourceType.WEAPON,
    source_items=["keris_partisan", "keris"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(vs_attribute="kalphite"),
    modifier=EffectModifier(damage_mult=1.33),
    proc_chance=1.0,  # The 33% bonus is always active vs kalphites
    description="+33% damage vs kalphites (+ 1/51 chance for triple damage)",
)

# Keris triple damage proc (separate effect for the 1/51 proc)
KERIS_TRIPLE_PROC = PassiveEffect(
    id="keris_triple",
    name="Keris Partisan (Triple)",
    source_type=SourceType.WEAPON,
    source_items=["keris_partisan", "keris"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(vs_attribute="kalphite"),
    modifier=EffectModifier(damage_mult=3.0),
    proc_chance=1/51,
    description="1/51 chance to deal triple damage vs kalphites",
)

ARCLIGHT = PassiveEffect(
    id="arclight",
    name="Arclight",
    source_type=SourceType.WEAPON,
    source_items=["arclight"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(vs_attribute="demon"),
    modifier=EffectModifier(accuracy_mult=1.70, damage_mult=1.70),
    description="+70% accuracy and damage vs demons",
)

DARKLIGHT = PassiveEffect(
    id="darklight",
    name="Darklight",
    source_type=SourceType.WEAPON,
    source_items=["darklight"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(vs_attribute="demon"),
    modifier=EffectModifier(accuracy_mult=1.75, damage_mult=1.75),
    description="+75% accuracy and damage vs demons (after upgrades)",
)

SILVERLIGHT = PassiveEffect(
    id="silverlight",
    name="Silverlight",
    source_type=SourceType.WEAPON,
    source_items=["silverlight"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(vs_attribute="demon"),
    modifier=EffectModifier(accuracy_mult=1.60, damage_mult=1.60),
    description="+60% accuracy and damage vs demons",
)

LEAF_BLADED_AXE = PassiveEffect(
    id="leaf_axe",
    name="Leaf-bladed Battleaxe",
    source_type=SourceType.WEAPON,
    source_items=["leaf-bladed_battleaxe", "leaf_bladed_battleaxe"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(vs_attribute="leafy"),
    modifier=EffectModifier(damage_mult=1.175),
    description="+17.5% damage vs leafy creatures",
)


# =============================================================================
# Priority 3: Barrows Set Effects (25% proc chance)
# =============================================================================

DHAROKS_SET_EFFECT = PassiveEffect(
    id="dharoks",
    name="Dharok's Set Effect",
    source_type=SourceType.SET,
    source_items=["dharoks_greataxe", "dharoks_helm", "dharoks_platebody", "dharoks_platelegs"],
    combat_styles=[CombatStyle.MELEE],
    modifier=EffectModifier(scales_with_missing_hp=True),
    proc_chance=1.0,  # Always active when set is worn
    description="Max hit scales with missing HP: base * (1 + (max_hp - current_hp) / max_hp)",
)

VERACS_SET_EFFECT = PassiveEffect(
    id="veracs",
    name="Verac's Set Effect",
    source_type=SourceType.SET,
    source_items=["veracs_flail", "veracs_helm", "veracs_brassard", "veracs_plateskirt"],
    combat_styles=[CombatStyle.MELEE],
    modifier=EffectModifier(ignores_defence=True, ignores_prayer=True, damage_mult=1.0),
    proc_chance=0.25,
    description="25% chance to ignore defence and protection prayers, +1 damage",
)

GUTHANS_SET_EFFECT = PassiveEffect(
    id="guthans",
    name="Guthan's Set Effect",
    source_type=SourceType.SET,
    source_items=["guthans_warspear", "guthans_helm", "guthans_platebody", "guthans_chainskirt"],
    combat_styles=[CombatStyle.MELEE],
    modifier=EffectModifier(),  # Heals damage dealt - doesn't affect DPS calc
    proc_chance=0.25,
    description="25% chance to heal for damage dealt",
)

KARILS_SET_EFFECT = PassiveEffect(
    id="karils",
    name="Karil's Set Effect",
    source_type=SourceType.SET,
    source_items=["karils_crossbow", "karils_coif", "karils_leathertop", "karils_leatherskirt"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(),  # Lowers agility - doesn't affect DPS calc
    proc_chance=0.25,
    description="25% chance to lower target's agility by 20%",
)

AHRIMS_SET_EFFECT = PassiveEffect(
    id="ahrims",
    name="Ahrim's Set Effect",
    source_type=SourceType.SET,
    source_items=["ahrims_staff", "ahrims_hood", "ahrims_robetop", "ahrims_robeskirt"],
    combat_styles=[CombatStyle.MAGIC],
    modifier=EffectModifier(),  # Lowers strength - doesn't affect DPS calc
    proc_chance=0.25,
    description="25% chance to lower target's strength by 5",
)

TORAGS_SET_EFFECT = PassiveEffect(
    id="torags",
    name="Torag's Set Effect",
    source_type=SourceType.SET,
    source_items=["torags_hammers", "torags_helm", "torags_platebody", "torags_platelegs"],
    combat_styles=[CombatStyle.MELEE],
    modifier=EffectModifier(),  # Lowers run energy - doesn't affect DPS calc
    proc_chance=0.25,
    description="25% chance to lower target's run energy by 20%",
)


# =============================================================================
# Priority 4: Enchanted Bolt Effects
# =============================================================================

RUBY_BOLTS_E = PassiveEffect(
    id="ruby_bolts_e",
    name="Ruby Bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["ruby_bolts_e", "ruby_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(),  # Special: 20% of target current HP (cap 100)
    proc_chance=0.06,  # 6% base, 11% with Kandarin diary
    description="6% chance to deal 20% of target's current HP (max 100)",
)

DIAMOND_BOLTS_E = PassiveEffect(
    id="diamond_bolts_e",
    name="Diamond Bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["diamond_bolts_e", "diamond_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(ignores_defence=True),
    proc_chance=0.10,  # 10% base, 15% with Kandarin diary
    description="10% chance to ignore target's defence",
)

DRAGONSTONE_BOLTS_E = PassiveEffect(
    id="dragonstone_bolts_e",
    name="Dragonstone Bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["dragonstone_bolts_e", "dragonstone_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(),  # Dragonfire damage
    proc_chance=0.06,  # 6% base, 11% with Kandarin diary
    description="6% chance to deal dragonfire damage",
)

ONYX_BOLTS_E = PassiveEffect(
    id="onyx_bolts_e",
    name="Onyx Bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["onyx_bolts_e", "onyx_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(damage_mult=1.20),  # +20% damage, heals 25%
    proc_chance=0.11,  # 11% base, 16.5% with Kandarin diary
    description="11% chance for +20% damage and heal 25% of damage dealt",
)

OPAL_BOLTS_E = PassiveEffect(
    id="opal_bolts_e",
    name="Opal Bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["opal_bolts_e", "opal_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(),  # +10% of ranged level
    proc_chance=0.05,  # 5% base, 7.5% with Kandarin diary
    description="5% chance for +10% of ranged level as bonus damage",
)


# =============================================================================
# Priority 5: Other Effects
# =============================================================================

BERSERKER_NECKLACE = PassiveEffect(
    id="berserker_neck",
    name="Berserker Necklace",
    source_type=SourceType.AMULET,
    source_items=["berserker_necklace"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(using_specific_weapon=["toktz", "tzhaar", "obsidian"]),
    modifier=EffectModifier(damage_mult=1.20),
    description="+20% damage with obsidian weapons",
)

# Crystal armor - each piece gives individual bonuses with crystal bow/bofa
# Bonuses stack ADDITIVELY: total +15% damage, +30% accuracy with all 3 pieces
# Body+legs can be worn with slayer helm or salve amulet
CRYSTAL_HELM = PassiveEffect(
    id="crystal_helm",
    name="Crystal Helm",
    source_type=SourceType.ARMOR,
    source_items=["crystal_helm"],
    combat_styles=[CombatStyle.RANGED],
    condition=EffectCondition(using_specific_weapon=["crystal_bow", "bow_of_faerdhinen"]),
    modifier=EffectModifier(accuracy_mult=1.05, damage_mult=1.025),
    additive_group="crystal_armor",
    description="+5% accuracy, +2.5% damage with crystal bow/bofa",
)

CRYSTAL_BODY = PassiveEffect(
    id="crystal_body",
    name="Crystal Body",
    source_type=SourceType.ARMOR,
    source_items=["crystal_body"],
    combat_styles=[CombatStyle.RANGED],
    condition=EffectCondition(using_specific_weapon=["crystal_bow", "bow_of_faerdhinen"]),
    modifier=EffectModifier(accuracy_mult=1.15, damage_mult=1.075),
    additive_group="crystal_armor",
    description="+15% accuracy, +7.5% damage with crystal bow/bofa",
)

CRYSTAL_LEGS = PassiveEffect(
    id="crystal_legs",
    name="Crystal Legs",
    source_type=SourceType.ARMOR,
    source_items=["crystal_legs"],
    combat_styles=[CombatStyle.RANGED],
    condition=EffectCondition(using_specific_weapon=["crystal_bow", "bow_of_faerdhinen"]),
    modifier=EffectModifier(accuracy_mult=1.10, damage_mult=1.05),
    additive_group="crystal_armor",
    description="+10% accuracy, +5% damage with crystal bow/bofa",
)

SMOKE_BATTLESTAFF = PassiveEffect(
    id="smoke_staff",
    name="Smoke Battlestaff",
    source_type=SourceType.WEAPON,
    source_items=["smoke_battlestaff"],
    combat_styles=[CombatStyle.MAGIC],
    modifier=EffectModifier(accuracy_mult=1.10, damage_mult=1.10),
    description="+10% accuracy and damage with standard spells",
)

# Wilderness weapons
CRAWS_BOW = PassiveEffect(
    id="craws_bow",
    name="Craw's Bow",
    source_type=SourceType.WEAPON,
    source_items=["craws_bow"],
    combat_styles=[CombatStyle.RANGED],
    condition=EffectCondition(in_wilderness=True),
    modifier=EffectModifier(accuracy_mult=1.50, damage_mult=1.50),
    description="+50% accuracy and damage in wilderness (when charged)",
)

VIGGORAS_CHAINMACE = PassiveEffect(
    id="viggoras",
    name="Viggora's Chainmace",
    source_type=SourceType.WEAPON,
    source_items=["viggoras_chainmace"],
    combat_styles=[CombatStyle.MELEE],
    condition=EffectCondition(in_wilderness=True),
    modifier=EffectModifier(accuracy_mult=1.50, damage_mult=1.50),
    description="+50% accuracy and damage in wilderness (when charged)",
)

THAMMARONS_SCEPTRE = PassiveEffect(
    id="thammarons",
    name="Thammaron's Sceptre",
    source_type=SourceType.WEAPON,
    source_items=["thammarons_sceptre"],
    combat_styles=[CombatStyle.MAGIC],
    condition=EffectCondition(in_wilderness=True),
    modifier=EffectModifier(accuracy_mult=1.50, damage_mult=1.50),
    description="+50% accuracy and damage in wilderness (when charged)",
)

AMULET_OF_AVARICE = PassiveEffect(
    id="avarice",
    name="Amulet of Avarice",
    source_type=SourceType.AMULET,
    source_items=["amulet_of_avarice"],
    combat_styles=[CombatStyle.MELEE, CombatStyle.RANGED, CombatStyle.MAGIC],
    condition=EffectCondition(in_wilderness=True, vs_attribute="revenant"),
    modifier=EffectModifier(accuracy_mult=1.20, damage_mult=1.20),
    description="+20% accuracy and damage vs revenants in wilderness",
)


# =============================================================================
# Enchanted Bolt Effects (proc-based)
# =============================================================================
# Note: These are proc effects with < 1.0 chance. The DPS calculation should
# factor in the expected damage increase from procs.

RUBY_BOLTS_E = PassiveEffect(
    id="ruby_bolts_e",
    name="Ruby bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["ruby_bolts_e", "ruby_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(damage_mult=1.0),  # Special: 20% of target current HP (capped 100)
    proc_chance=0.06,  # 6% base, 11% with Kandarin hard diary
    description="Blood Forfeit: 6% chance to deal 20% of target's current HP (max 100), costs 10% of your HP",
)

DIAMOND_BOLTS_E = PassiveEffect(
    id="diamond_bolts_e",
    name="Diamond bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["diamond_bolts_e", "diamond_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(ignores_defence=True),
    proc_chance=0.10,  # 10% base, 15% with diary
    description="Armour Piercing: 10% chance to ignore target's ranged defence",
)

ONYX_BOLTS_E = PassiveEffect(
    id="onyx_bolts_e",
    name="Onyx bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["onyx_bolts_e", "onyx_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(damage_mult=1.20),  # +20% damage on proc
    proc_chance=0.11,  # 11% base, 16.5% with diary
    description="Life Leech: 11% chance to deal +20% damage and heal 25% of damage dealt",
)

DRAGONSTONE_BOLTS_E = PassiveEffect(
    id="dragonstone_bolts_e",
    name="Dragonstone bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["dragonstone_bolts_e", "dragonstone_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(damage_mult=1.0),  # Adds dragonfire damage
    proc_chance=0.06,  # 6% base, 11% with diary
    description="Dragon's Breath: 6% chance to inflict dragonfire (damage based on ranged level)",
)

OPAL_BOLTS_E = PassiveEffect(
    id="opal_bolts_e",
    name="Opal bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["opal_bolts_e", "opal_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(damage_mult=1.0),  # Adds 10% of ranged level
    proc_chance=0.05,  # 5% base, 7.5% with diary
    description="Lucky Lightning: 5% chance to deal extra damage (10% of ranged level)",
)

PEARL_BOLTS_E = PassiveEffect(
    id="pearl_bolts_e",
    name="Pearl bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["pearl_bolts_e", "pearl_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(damage_mult=1.0),  # Extra water damage
    proc_chance=0.06,  # 6% base, 11% with diary
    description="Sea Curse: 6% chance to deal extra water damage (1/15 ranged level, 1/5 vs fiery)",
)

EMERALD_BOLTS_E = PassiveEffect(
    id="emerald_bolts_e",
    name="Emerald bolts (e)",
    source_type=SourceType.AMMO,
    source_items=["emerald_bolts_e", "emerald_dragon_bolts_e"],
    combat_styles=[CombatStyle.RANGED],
    modifier=EffectModifier(damage_mult=1.0),  # Applies poison
    proc_chance=0.55,  # 55% base, 57.5% with diary
    description="Magical Poison: 55% chance to inflict poison (5 damage)",
)


# =============================================================================
# Set Bonus Definitions
# =============================================================================

DHAROKS_SET = SetBonus(
    id="dharoks_set",
    name="Dharok's Set",
    required_items=["dharoks_greataxe", "dharoks_helm", "dharoks_platebody", "dharoks_platelegs"],
    min_pieces=4,
    effect=DHAROKS_SET_EFFECT,
)

VERACS_SET = SetBonus(
    id="veracs_set",
    name="Verac's Set",
    required_items=["veracs_flail", "veracs_helm", "veracs_brassard", "veracs_plateskirt"],
    min_pieces=4,
    effect=VERACS_SET_EFFECT,
)

GUTHANS_SET = SetBonus(
    id="guthans_set",
    name="Guthan's Set",
    required_items=["guthans_warspear", "guthans_helm", "guthans_platebody", "guthans_chainskirt"],
    min_pieces=4,
    effect=GUTHANS_SET_EFFECT,
)

KARILS_SET = SetBonus(
    id="karils_set",
    name="Karil's Set",
    required_items=["karils_crossbow", "karils_coif", "karils_leathertop", "karils_leatherskirt"],
    min_pieces=4,
    effect=KARILS_SET_EFFECT,
)

AHRIMS_SET = SetBonus(
    id="ahrims_set",
    name="Ahrim's Set",
    required_items=["ahrims_staff", "ahrims_hood", "ahrims_robetop", "ahrims_robeskirt"],
    min_pieces=4,
    effect=AHRIMS_SET_EFFECT,
)

TORAGS_SET = SetBonus(
    id="torags_set",
    name="Torag's Set",
    required_items=["torags_hammers", "torags_helm", "torags_platebody", "torags_platelegs"],
    min_pieces=4,
    effect=TORAGS_SET_EFFECT,
)

VOID_MELEE_SET = SetBonus(
    id="void_melee_set",
    name="Void Knight (Melee)",
    required_items=["void_melee_helm", "void_knight_top", "void_knight_robe", "void_knight_gloves"],
    min_pieces=4,
    effect=VOID_MELEE,
)

VOID_RANGED_SET = SetBonus(
    id="void_ranged_set",
    name="Void Knight (Ranged)",
    required_items=["void_ranger_helm", "void_knight_top", "void_knight_robe", "void_knight_gloves"],
    min_pieces=4,
    effect=VOID_RANGED,
)

VOID_MAGIC_SET = SetBonus(
    id="void_magic_set",
    name="Void Knight (Magic)",
    required_items=["void_mage_helm", "void_knight_top", "void_knight_robe", "void_knight_gloves"],
    min_pieces=4,
    effect=VOID_MAGIC,
)

ELITE_VOID_RANGED_SET = SetBonus(
    id="elite_void_ranged_set",
    name="Elite Void Knight (Ranged)",
    required_items=["void_ranger_helm", "elite_void_top", "elite_void_robe", "void_knight_gloves"],
    min_pieces=4,
    effect=ELITE_VOID_RANGED,
)

ELITE_VOID_MAGIC_SET = SetBonus(
    id="elite_void_magic_set",
    name="Elite Void Knight (Magic)",
    required_items=["void_mage_helm", "elite_void_top", "elite_void_robe", "void_knight_gloves"],
    min_pieces=4,
    effect=ELITE_VOID_MAGIC,
)

INQUISITOR_SET_BONUS = SetBonus(
    id="inquisitor_set",
    name="Inquisitor's Armour",
    required_items=["inquisitor_helm", "inquisitor_hauberk", "inquisitor_plateskirt"],
    min_pieces=3,
    effect=INQUISITOR_SET,
)

OBSIDIAN_SET_BONUS = SetBonus(
    id="obsidian_set",
    name="Obsidian Armour",
    required_items=["obsidian_helmet", "obsidian_platebody", "obsidian_platelegs"],
    min_pieces=3,
    effect=OBSIDIAN_SET,
)



# =============================================================================
# Collections for easy access
# =============================================================================

# All passive effects (individual items)
ALL_EFFECTS: Dict[str, PassiveEffect] = {
    # Void
    "void_melee": VOID_MELEE,
    "void_ranged": VOID_RANGED,
    "void_magic": VOID_MAGIC,
    "elite_void_ranged": ELITE_VOID_RANGED,
    "elite_void_magic": ELITE_VOID_MAGIC,
    # Slayer/Salve
    "slayer_helm": SLAYER_HELM,
    "slayer_helm_i": SLAYER_HELM_IMBUED,
    "salve": SALVE_AMULET,
    "salve_e": SALVE_AMULET_E,
    "salve_ei": SALVE_AMULET_EI,
    # Dragon hunter
    "dh_lance": DRAGON_HUNTER_LANCE,
    "dhcb": DRAGON_HUNTER_CROSSBOW,
    # Armor sets
    "inquisitor": INQUISITOR_SET,
    "obsidian": OBSIDIAN_SET,
    # Weapon mechanics
    "fang": OSMUMTENS_FANG,
    "scythe": SCYTHE_OF_VITUR,
    "tbow": TWISTED_BOW,
    "keris": KERIS_PARTISAN,
    "keris_triple": KERIS_TRIPLE_PROC,
    "arclight": ARCLIGHT,
    "darklight": DARKLIGHT,
    "silverlight": SILVERLIGHT,
    "leaf_axe": LEAF_BLADED_AXE,
    # Barrows
    "dharoks": DHAROKS_SET_EFFECT,
    "veracs": VERACS_SET_EFFECT,
    "guthans": GUTHANS_SET_EFFECT,
    "karils": KARILS_SET_EFFECT,
    "ahrims": AHRIMS_SET_EFFECT,
    "torags": TORAGS_SET_EFFECT,
    # Bolts
    "ruby_bolts_e": RUBY_BOLTS_E,
    "diamond_bolts_e": DIAMOND_BOLTS_E,
    "dragonstone_bolts_e": DRAGONSTONE_BOLTS_E,
    "onyx_bolts_e": ONYX_BOLTS_E,
    "opal_bolts_e": OPAL_BOLTS_E,
    # Other
    "berserker_neck": BERSERKER_NECKLACE,
    "crystal_helm": CRYSTAL_HELM,
    "crystal_body": CRYSTAL_BODY,
    "crystal_legs": CRYSTAL_LEGS,
    "smoke_staff": SMOKE_BATTLESTAFF,
    "craws_bow": CRAWS_BOW,
    "viggoras": VIGGORAS_CHAINMACE,
    "thammarons": THAMMARONS_SCEPTRE,
    "avarice": AMULET_OF_AVARICE,
    # Enchanted bolts
    "ruby_bolts_e": RUBY_BOLTS_E,
    "diamond_bolts_e": DIAMOND_BOLTS_E,
    "onyx_bolts_e": ONYX_BOLTS_E,
    "dragonstone_bolts_e": DRAGONSTONE_BOLTS_E,
    "opal_bolts_e": OPAL_BOLTS_E,
    "pearl_bolts_e": PEARL_BOLTS_E,
    "emerald_bolts_e": EMERALD_BOLTS_E,
}

# All set bonuses
ALL_SET_BONUSES: Dict[str, SetBonus] = {
    "dharoks_set": DHAROKS_SET,
    "veracs_set": VERACS_SET,
    "guthans_set": GUTHANS_SET,
    "karils_set": KARILS_SET,
    "ahrims_set": AHRIMS_SET,
    "torags_set": TORAGS_SET,
    "void_melee_set": VOID_MELEE_SET,
    "void_ranged_set": VOID_RANGED_SET,
    "void_magic_set": VOID_MAGIC_SET,
    "elite_void_ranged_set": ELITE_VOID_RANGED_SET,
    "elite_void_magic_set": ELITE_VOID_MAGIC_SET,
    "inquisitor_set": INQUISITOR_SET_BONUS,
    "obsidian_set": OBSIDIAN_SET_BONUS,
}

# Weapon-specific effects (auto-detected from weapon name)
WEAPON_EFFECTS: Dict[str, PassiveEffect] = {
    "osmumtens_fang": OSMUMTENS_FANG,
    "osmumten's_fang": OSMUMTENS_FANG,
    "scythe_of_vitur": SCYTHE_OF_VITUR,
    "twisted_bow": TWISTED_BOW,
    "dragon_hunter_lance": DRAGON_HUNTER_LANCE,
    "dragon_hunter_crossbow": DRAGON_HUNTER_CROSSBOW,
    "keris_partisan": KERIS_PARTISAN,
    "arclight": ARCLIGHT,
    "darklight": DARKLIGHT,
    "silverlight": SILVERLIGHT,
    "leaf-bladed_battleaxe": LEAF_BLADED_AXE,
    "leaf_bladed_battleaxe": LEAF_BLADED_AXE,
    "smoke_battlestaff": SMOKE_BATTLESTAFF,
    "craws_bow": CRAWS_BOW,
    "viggoras_chainmace": VIGGORAS_CHAINMACE,
    "thammarons_sceptre": THAMMARONS_SCEPTRE,
}


def get_effect(effect_id: str) -> PassiveEffect | None:
    """Get an effect by its ID.

    Args:
        effect_id: The effect's unique identifier.

    Returns:
        The PassiveEffect or None if not found.
    """
    return ALL_EFFECTS.get(effect_id)


def get_set_bonus(set_id: str) -> SetBonus | None:
    """Get a set bonus by its ID.

    Args:
        set_id: The set bonus's unique identifier.

    Returns:
        The SetBonus or None if not found.
    """
    return ALL_SET_BONUSES.get(set_id)


def list_effects() -> list[str]:
    """List all effect IDs."""
    return list(ALL_EFFECTS.keys())


def list_set_bonuses() -> list[str]:
    """List all set bonus IDs."""
    return list(ALL_SET_BONUSES.keys())
