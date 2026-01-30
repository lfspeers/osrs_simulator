#!/usr/bin/env python3
"""CLI entry point for OSRS simulator."""

import argparse
import sys
from typing import Optional

from core.player import PlayerConfig, HarpoonType, CombatStats
from core.hiscores import (
    HiscoresClient,
    AccountType,
    PlayerNotFoundError,
    RateLimitError,
    APIUnavailableError,
)
from tempoross.simulation import Simulation, run_monte_carlo, average_results, GameResult
from tempoross.optimizer import (
    Strategy,
    optimize,
    find_pareto_optimal,
    maximize_fishing_xp,
    maximize_total_xp,
    maximize_permits,
    maximize_points,
    maximize_efficiency,
)
from presets.tempoross import get_preset, list_presets, hiscores_to_player_config

# Combat imports
from combat import (
    CombatSetup,
    CombatResult,
    CombatCalculator,
    PotionBoost,
    quick_dps,
    simulate_kill,
    get_weapon,
    get_monster,
    get_prayer,
    get_spell,
    list_weapons,
    list_monsters,
    list_prayers,
    list_spells,
    AttackStyle,
    GearModifiers,
    Prayer,
    EquipmentStats,
    Spell,
    Spellbook,
    set_monster_loader,
    set_weapon_loader,
    WEAPONS,
    MONSTERS,
    SPELLS,
)
from combat.simulation import CombatStats as SimCombatStats
from combat.formulas import format_formula_breakdown
from combat.storage import SimulationStorage, SimulationResult, generate_simulation_id
from presets.combat import get_combat_preset, list_combat_presets, PRESETS
from dataclasses import asdict
from pathlib import Path
import time


def init_data_loaders():
    """Initialize external data loaders if data files exist."""
    data_dir = Path(__file__).parent / "data"
    if not data_dir.exists():
        return

    # Try to load monster data
    monsters_path = data_dir / "monsters.json"
    if monsters_path.exists():
        try:
            from data_loader.monster_loader import MonsterLoader
            loader = MonsterLoader(monsters_path)
            set_monster_loader(loader)
        except ImportError:
            pass

    # Try to load weapon data
    items_path = data_dir / "items.json"
    if items_path.exists():
        try:
            from data_loader.item_loader import WeaponLoader
            loader = WeaponLoader(items_path)
            set_weapon_loader(loader)
        except ImportError:
            pass


def parse_harpoon_type(value: str) -> HarpoonType:
    """Parse harpoon type from string."""
    mapping = {
        "regular": HarpoonType.REGULAR,
        "dragon": HarpoonType.DRAGON,
        "infernal": HarpoonType.INFERNAL,
        "crystal": HarpoonType.CRYSTAL,
    }
    if value.lower() not in mapping:
        raise argparse.ArgumentTypeError(
            f"Invalid harpoon type: {value}. "
            f"Choose from: {', '.join(mapping.keys())}"
        )
    return mapping[value.lower()]


def parse_account_type(value: str) -> AccountType:
    """Parse account type from string."""
    mapping = {
        "normal": AccountType.NORMAL,
        "ironman": AccountType.IRONMAN,
        "hardcore": AccountType.HARDCORE_IRONMAN,
        "hardcore_ironman": AccountType.HARDCORE_IRONMAN,
        "ultimate": AccountType.ULTIMATE_IRONMAN,
        "ultimate_ironman": AccountType.ULTIMATE_IRONMAN,
    }
    if value.lower() not in mapping:
        raise argparse.ArgumentTypeError(
            f"Invalid account type: {value}. "
            f"Choose from: normal, ironman, hardcore, ultimate"
        )
    return mapping[value.lower()]


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="tempoross",
        description="Tempoross minigame simulator and optimizer"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Common player arguments
    player_args = argparse.ArgumentParser(add_help=False)
    player_args.add_argument(
        "--fishing-level", "-f",
        type=int,
        default=70,
        help="Fishing level (35-99, default: 70)"
    )
    player_args.add_argument(
        "--cooking-level", "-c",
        type=int,
        default=70,
        help="Cooking level (1-99, default: 70)"
    )
    player_args.add_argument(
        "--harpoon", "-H",
        type=parse_harpoon_type,
        default=HarpoonType.DRAGON,
        help="Harpoon type: regular, dragon, infernal, crystal (default: dragon)"
    )
    player_args.add_argument(
        "--spirit-angler",
        action="store_true",
        help="Has full spirit angler outfit"
    )
    player_args.add_argument(
        "--imcando-hammer",
        action="store_true",
        help="Has imcando hammer equipped"
    )

    # Simulate command
    sim_parser = subparsers.add_parser(
        "simulate",
        parents=[player_args],
        help="Run a simulation with specific strategy"
    )
    sim_parser.add_argument(
        "--strategy", "-s",
        choices=["no-cook", "full-cook", "firefighting", "balanced", "custom"],
        default="balanced",
        help="Strategy preset (default: balanced)"
    )
    sim_parser.add_argument(
        "--cook-ratio",
        type=float,
        help="Custom cook ratio (0.0-1.0)"
    )
    sim_parser.add_argument(
        "--num-players", "-n",
        type=int,
        default=1,
        help="Number of players (default: 1)"
    )
    sim_parser.add_argument(
        "--simulations",
        type=int,
        default=10,
        help="Number of Monte Carlo simulations (default: 10)"
    )
    sim_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility"
    )
    sim_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )

    # Optimize command
    opt_parser = subparsers.add_parser(
        "optimize",
        parents=[player_args],
        help="Find optimal strategy for objective"
    )
    opt_parser.add_argument(
        "--objective", "-o",
        choices=["fishing-xp", "total-xp", "permits", "points", "efficiency"],
        default="permits",
        help="Objective to maximize (default: permits)"
    )
    opt_parser.add_argument(
        "--simulations",
        type=int,
        default=10,
        help="Simulations per strategy (default: 10)"
    )
    opt_parser.add_argument(
        "--resolution",
        type=int,
        default=5,
        help="Grid resolution (default: 5)"
    )
    opt_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility"
    )

    # Benchmark command
    bench_parser = subparsers.add_parser(
        "benchmark",
        parents=[player_args],
        help="Benchmark against wiki expected values"
    )
    bench_parser.add_argument(
        "--compare-wiki",
        action="store_true",
        help="Compare results with wiki benchmarks"
    )

    # Pareto command
    pareto_parser = subparsers.add_parser(
        "pareto",
        parents=[player_args],
        help="Find Pareto-optimal strategies"
    )
    pareto_parser.add_argument(
        "--simulations",
        type=int,
        default=10,
        help="Simulations per strategy (default: 10)"
    )
    pareto_parser.add_argument(
        "--resolution",
        type=int,
        default=5,
        help="Grid resolution (default: 5)"
    )

    # Combat command
    combat_parser = subparsers.add_parser(
        "combat",
        help="Combat DPS calculator"
    )
    combat_subparsers = combat_parser.add_subparsers(dest="combat_command", help="Combat command")

    # Combat DPS subcommand
    combat_dps_parser = combat_subparsers.add_parser(
        "dps",
        help="Calculate DPS against a target"
    )
    combat_dps_parser.add_argument(
        "username",
        nargs="?",
        help="Player username to look up stats (optional)"
    )
    combat_dps_parser.add_argument(
        "--weapon", "-w",
        required=True,
        help="Weapon to use (e.g., ghrazi_rapier, abyssal_whip)"
    )
    combat_dps_parser.add_argument(
        "--target", "-t",
        required=True,
        help="Target monster (e.g., vorkath, general_graardor)"
    )
    combat_dps_parser.add_argument(
        "--prayer", "-p",
        default="none",
        help="Prayer to use (e.g., piety, rigour, augury)"
    )
    combat_dps_parser.add_argument(
        "--attack",
        type=int,
        default=99,
        help="Attack level (default: 99)"
    )
    combat_dps_parser.add_argument(
        "--strength",
        type=int,
        default=99,
        help="Strength level (default: 99)"
    )
    combat_dps_parser.add_argument(
        "--ranged",
        type=int,
        default=99,
        help="Ranged level (default: 99)"
    )
    combat_dps_parser.add_argument(
        "--magic",
        type=int,
        default=99,
        help="Magic level (default: 99)"
    )
    combat_dps_parser.add_argument(
        "--slayer-task",
        action="store_true",
        help="On slayer task (enables slayer helm bonus)"
    )
    combat_dps_parser.add_argument(
        "--slayer-helm",
        action="store_true",
        help="Wearing slayer helm (imbued)"
    )
    combat_dps_parser.add_argument(
        "--salve",
        choices=["none", "salve", "salve_e", "salve_ei"],
        default="none",
        help="Salve amulet variant (for undead)"
    )
    combat_dps_parser.add_argument(
        "--void",
        choices=["none", "melee", "ranged", "magic", "elite_melee", "elite_ranged", "elite_magic"],
        default="none",
        help="Void equipment type"
    )
    combat_dps_parser.add_argument(
        "--potion",
        choices=["none", "super_combat", "ranging", "divine_ranging", "imbued_heart", "saturated_heart"],
        default="super_combat",
        help="Potion boost (default: super_combat)"
    )
    combat_dps_parser.add_argument(
        "--account-type", "-a",
        type=parse_account_type,
        default=None,
        help="Account type for hiscores lookup"
    )
    combat_dps_parser.add_argument(
        "--preset", "-P",
        help="Equipment preset (e.g., max_melee_stab). Use 'combat list presets' to see options."
    )
    combat_dps_parser.add_argument(
        "--melee-strength",
        type=int,
        help="Melee strength bonus from gear"
    )
    combat_dps_parser.add_argument(
        "--ranged-attack",
        type=int,
        help="Ranged attack bonus from gear"
    )
    combat_dps_parser.add_argument(
        "--ranged-strength",
        type=int,
        help="Ranged strength bonus from gear"
    )
    combat_dps_parser.add_argument(
        "--magic-attack",
        type=int,
        help="Magic attack bonus from gear"
    )
    combat_dps_parser.add_argument(
        "--magic-damage",
        type=float,
        help="Magic damage bonus (decimal, e.g., 0.15 for 15%%)"
    )
    combat_dps_parser.add_argument(
        "--show-formula", "-F",
        action="store_true",
        help="Show the DPS calculation formula with values"
    )

    # Combat list subcommand
    combat_list_parser = combat_subparsers.add_parser(
        "list",
        help="List available weapons or monsters"
    )
    combat_list_parser.add_argument(
        "category",
        choices=["weapons", "monsters", "prayers", "presets", "spells"],
        help="Category to list"
    )
    combat_list_parser.add_argument(
        "--style",
        choices=["melee", "ranged", "magic"],
        help="Filter by combat style (for weapons)"
    )
    combat_list_parser.add_argument(
        "--category-filter",
        help="Filter monsters by category (e.g., 'bosses', 'demon', slayer category)"
    )

    # Combat data subcommand
    combat_data_parser = combat_subparsers.add_parser(
        "data",
        help="Manage OSRS data from osrsreboxed-db"
    )
    combat_data_subparsers = combat_data_parser.add_subparsers(dest="data_action")

    # combat data fetch
    data_fetch_parser = combat_data_subparsers.add_parser(
        "fetch",
        help="Download latest OSRS data from osrsreboxed-db"
    )

    # combat data stats
    data_stats_parser = combat_data_subparsers.add_parser(
        "stats",
        help="Show statistics about loaded data"
    )

    # Combat simulate subcommand
    combat_sim_parser = combat_subparsers.add_parser(
        "simulate",
        help="Monte Carlo kill simulation"
    )
    combat_sim_parser.add_argument(
        "username",
        nargs="?",
        help="Player username to look up stats (optional)"
    )
    combat_sim_parser.add_argument(
        "--weapon", "-w",
        required=True,
        help="Weapon to use"
    )
    combat_sim_parser.add_argument(
        "--target", "-t",
        required=True,
        help="Target monster"
    )
    combat_sim_parser.add_argument(
        "--prayer", "-p",
        default="none",
        help="Prayer to use"
    )
    combat_sim_parser.add_argument(
        "--kills", "-k",
        type=int,
        default=1000,
        help="Number of kills to simulate (default: 1000)"
    )
    combat_sim_parser.add_argument(
        "--attack",
        type=int,
        default=99,
        help="Attack level"
    )
    combat_sim_parser.add_argument(
        "--strength",
        type=int,
        default=99,
        help="Strength level"
    )
    combat_sim_parser.add_argument(
        "--ranged",
        type=int,
        default=99,
        help="Ranged level"
    )
    combat_sim_parser.add_argument(
        "--magic",
        type=int,
        default=99,
        help="Magic level"
    )
    combat_sim_parser.add_argument(
        "--potion",
        choices=["none", "super_combat", "ranging", "divine_ranging", "imbued_heart", "saturated_heart"],
        default="super_combat",
        help="Potion boost"
    )
    combat_sim_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility"
    )
    combat_sim_parser.add_argument(
        "--account-type", "-a",
        type=parse_account_type,
        default=None,
        help="Account type for hiscores lookup"
    )
    combat_sim_parser.add_argument(
        "--save",
        action="store_true",
        help="Save simulation results to disk"
    )
    combat_sim_parser.add_argument(
        "--preset", "-P",
        help="Equipment preset"
    )
    combat_sim_parser.add_argument(
        "--melee-strength",
        type=int,
        help="Melee strength bonus from gear"
    )
    combat_sim_parser.add_argument(
        "--ranged-strength",
        type=int,
        help="Ranged strength bonus from gear"
    )

    # Lookup command
    lookup_parser = subparsers.add_parser(
        "lookup",
        help="Look up player stats from OSRS Hiscores"
    )
    lookup_parser.add_argument(
        "username",
        help="Player username to look up"
    )
    lookup_parser.add_argument(
        "--account-type", "-a",
        type=parse_account_type,
        default=None,
        help="Account type: normal, ironman, hardcore, ultimate (default: auto-detect)"
    )
    lookup_parser.add_argument(
        "--preset", "-p",
        choices=["budget", "mid", "angler", "optimal"],
        default="mid",
        help="Equipment preset (default: mid)"
    )
    lookup_parser.add_argument(
        "--simulate", "-s",
        action="store_true",
        help="Run simulation after lookup"
    )
    lookup_parser.add_argument(
        "--strategy",
        choices=["no-cook", "full-cook", "firefighting", "balanced"],
        default="balanced",
        help="Strategy for simulation (default: balanced)"
    )
    lookup_parser.add_argument(
        "--simulations",
        type=int,
        default=10,
        help="Number of simulations (default: 10)"
    )
    # Equipment override flags
    lookup_parser.add_argument(
        "--harpoon", "-H",
        type=parse_harpoon_type,
        default=None,
        help="Override harpoon type: regular, dragon, infernal, crystal"
    )
    lookup_parser.add_argument(
        "--spirit-angler",
        action="store_true",
        default=None,
        help="Has full spirit angler outfit"
    )
    lookup_parser.add_argument(
        "--no-spirit-angler",
        action="store_true",
        help="Does not have spirit angler outfit"
    )
    lookup_parser.add_argument(
        "--imcando-hammer",
        action="store_true",
        default=None,
        help="Has imcando hammer equipped"
    )
    lookup_parser.add_argument(
        "--no-imcando-hammer",
        action="store_true",
        help="Does not have imcando hammer"
    )
    lookup_parser.add_argument(
        "--refresh", "-r",
        action="store_true",
        help="Force refresh from API (bypass cache)"
    )

    return parser


def get_player_config(args) -> PlayerConfig:
    """Create PlayerConfig from parsed arguments."""
    return PlayerConfig(
        fishing_level=args.fishing_level,
        cooking_level=args.cooking_level,
        harpoon_type=args.harpoon,
        has_spirit_angler=args.spirit_angler,
        has_imcando_hammer=args.imcando_hammer,
    )


def get_strategy(args) -> Strategy:
    """Create Strategy from parsed arguments."""
    if args.strategy == "no-cook":
        strategy = Strategy.no_cook()
    elif args.strategy == "full-cook":
        strategy = Strategy.full_cook()
    elif args.strategy == "firefighting":
        strategy = Strategy.firefighting()
    elif args.strategy == "balanced":
        strategy = Strategy.balanced()
    else:
        strategy = Strategy()

    # Override with custom values if provided
    if hasattr(args, "cook_ratio") and args.cook_ratio is not None:
        strategy.cook_ratio = args.cook_ratio

    return strategy


def get_objective(name: str):
    """Get objective function by name."""
    objectives = {
        "fishing-xp": maximize_fishing_xp,
        "total-xp": maximize_total_xp,
        "permits": maximize_permits,
        "points": maximize_points,
        "efficiency": maximize_efficiency,
    }
    return objectives[name]


def cmd_simulate(args):
    """Run simulation command."""
    player = get_player_config(args)
    strategy = get_strategy(args)

    print(f"Running {args.simulations} simulations...")
    print(f"Player: Level {player.fishing_level} Fishing, {player.harpoon_type.value} harpoon")
    print(f"Strategy: cook_ratio={strategy.cook_ratio:.1%}, fire_mgmt={strategy.fire_management}")
    print()

    results = run_monte_carlo(
        player_config=player,
        strategy=strategy,
        num_players=args.num_players,
        num_simulations=args.simulations,
        seed=args.seed,
    )

    avg = average_results(results)

    print("=== Average Results ===")
    print(f"Game Time: {avg.game_time_minutes:.1f} minutes ({avg.ticks_elapsed} ticks)")
    print(f"Points: {avg.points:,}")
    print(f"Permits: {avg.permits}")
    print()
    print(f"Fishing XP: {avg.fishing_xp:,.0f}")
    print(f"Cooking XP: {avg.cooking_xp:,.0f}")
    print()
    print("=== Hourly Rates ===")
    print(f"Games/hr: {avg.games_per_hour:.1f}")
    print(f"Fishing XP/hr: {avg.fishing_xp_per_hour:,.0f}")
    print(f"Cooking XP/hr: {avg.cooking_xp_per_hour:,.0f}")
    print(f"Total XP/hr: {avg.total_xp_per_hour:,.0f}")
    print(f"Permits/hr: {avg.permits_per_hour:.1f}")

    if args.verbose:
        print()
        print("=== Detailed Breakdown ===")
        print(f"Fish caught: {avg.fish_caught}")
        print(f"Fish cooked: {avg.fish_cooked}")
        print(f"Raw deposited: {avg.raw_deposited}")
        print(f"Cooked deposited: {avg.cooked_deposited}")
        print(f"Repairs: {avg.repairs}")
        print(f"Fires doused: {avg.fires_doused}")
        print(f"Spirit harpoons: {avg.spirit_harpoons}")
        print(f"Victory rate: {sum(1 for r in results if r.victory)/len(results):.0%}")


def cmd_optimize(args):
    """Run optimization command."""
    player = get_player_config(args)
    objective = get_objective(args.objective)

    print(f"Optimizing for: {args.objective}")
    print(f"Player: Level {player.fishing_level} Fishing, {player.harpoon_type.value} harpoon")
    print(f"Grid resolution: {args.resolution}, Simulations: {args.simulations}")
    print()
    print("Searching strategy space...")

    best_strategy, best_result = optimize(
        player_config=player,
        objective=objective,
        num_simulations=args.simulations,
        grid_resolution=args.resolution,
        seed=args.seed,
    )

    print()
    print("=== Optimal Strategy Found ===")
    print(f"Cook ratio: {best_strategy.cook_ratio:.0%}")
    print(f"Fire management: {best_strategy.fire_management}")
    print(f"Spirit pool threshold: {best_strategy.spirit_pool_threshold:.0%}")
    print(f"Extend game: {best_strategy.extend_game}")
    print()
    print("=== Expected Results ===")
    print(f"Points: {best_result.points:,}")
    print(f"Permits: {best_result.permits}")
    print(f"Fishing XP/hr: {best_result.fishing_xp_per_hour:,.0f}")
    print(f"Cooking XP/hr: {best_result.cooking_xp_per_hour:,.0f}")
    print(f"Permits/hr: {best_result.permits_per_hour:.1f}")


def cmd_benchmark(args):
    """Run benchmark command."""
    player = get_player_config(args)

    # Wiki benchmarks (approximate)
    benchmarks = [
        ("Solo no-cook", Strategy.no_cook(), 50, 60, 100000),  # permits_min, permits_max, xp_hr
        ("Solo cook + fires", Strategy.firefighting(), 75, 85, 60000),
        ("Balanced", Strategy.balanced(), 60, 75, 80000),
    ]

    print("=== Benchmark Results ===")
    print(f"Player: Level {player.fishing_level} Fishing")
    print()

    for name, strategy, wiki_permits_min, wiki_permits_max, wiki_xp in benchmarks:
        results = run_monte_carlo(
            player_config=player,
            strategy=strategy,
            num_simulations=20,
        )
        avg = average_results(results)

        permits_ok = wiki_permits_min <= avg.permits_per_hour <= wiki_permits_max * 1.2
        xp_ok = avg.fishing_xp_per_hour >= wiki_xp * 0.5

        print(f"{name}:")
        print(f"  Permits/hr: {avg.permits_per_hour:.1f} (wiki: {wiki_permits_min}-{wiki_permits_max}) {'OK' if permits_ok else 'CHECK'}")
        print(f"  Fishing XP/hr: {avg.fishing_xp_per_hour:,.0f} (wiki: ~{wiki_xp:,}) {'OK' if xp_ok else 'CHECK'}")
        print()


def cmd_pareto(args):
    """Run Pareto optimization command."""
    player = get_player_config(args)

    objectives = [maximize_fishing_xp, maximize_permits]
    objective_names = ["Fishing XP/hr", "Permits/hr"]

    print("Finding Pareto-optimal strategies...")
    print(f"Objectives: {', '.join(objective_names)}")
    print()

    pareto_set = find_pareto_optimal(
        player_config=player,
        objectives=objectives,
        num_simulations=args.simulations,
        grid_resolution=args.resolution,
    )

    print(f"Found {len(pareto_set)} Pareto-optimal strategies:")
    print()
    print(f"{'Strategy':<40} {'Fishing XP/hr':>15} {'Permits/hr':>12}")
    print("-" * 70)

    for strategy, result, scores in sorted(pareto_set, key=lambda x: -x[2][0]):
        desc = f"cook={strategy.cook_ratio:.0%}, fire={strategy.fire_management}"
        print(f"{desc:<40} {scores[0]:>15,.0f} {scores[1]:>12.1f}")


def cmd_lookup(args):
    """Run hiscores lookup command."""
    import time
    from datetime import datetime

    client = HiscoresClient()
    force_refresh = getattr(args, 'refresh', False)

    # Check if we have saved data
    saved_data = client._load_character(args.username)
    saved_time = saved_data.get("last_updated") if saved_data else None

    if force_refresh:
        print(f"Refreshing '{args.username}' from API...")
    elif saved_data:
        print(f"Loading '{args.username}' from saved data...")
    else:
        print(f"Looking up '{args.username}'...")
    print()

    try:
        if args.account_type:
            hiscores = client.lookup(args.username, args.account_type, force_refresh=force_refresh)
        else:
            hiscores = client.lookup_multiple_types(args.username, force_refresh=force_refresh)
            if hiscores is None:
                print(f"Error: Player '{args.username}' not found on any hiscores.")
                sys.exit(1)

    except PlayerNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except RateLimitError as e:
        print(f"Error: {e}")
        print("Please try again later.")
        sys.exit(1)
    except APIUnavailableError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Check if data was loaded from saved file or freshly fetched
    new_saved_data = client._load_character(args.username)
    new_saved_time = new_saved_data.get("last_updated") if new_saved_data else None
    from_saved = saved_time is not None and new_saved_time == saved_time

    # Display player info with save status
    if from_saved and saved_time:
        last_updated = datetime.fromtimestamp(saved_time)
        date_str = last_updated.strftime("%Y-%m-%d %H:%M")
        print(f"=== {hiscores.username} ({hiscores.account_type.display_name}) [saved {date_str}] ===")
    else:
        print(f"=== {hiscores.username} ({hiscores.account_type.display_name}) [updated now] ===")
    print(f"Fishing: {hiscores.fishing_level}")
    print(f"Cooking: {hiscores.cooking_level}")
    print(f"Construction: {hiscores.construction_level}")
    print(f"Tempoross KC: {hiscores.tempoross_kc}")
    print()

    # Get base preset and apply overrides
    preset = get_preset(args.preset)

    # Determine final equipment values
    harpoon = args.harpoon if args.harpoon is not None else preset.harpoon

    # Spirit angler: --spirit-angler sets True, --no-spirit-angler sets False, otherwise use preset
    if args.spirit_angler:
        has_spirit_angler = True
    elif args.no_spirit_angler:
        has_spirit_angler = False
    else:
        has_spirit_angler = preset.has_spirit_angler

    # Imcando hammer: same logic
    if args.imcando_hammer:
        has_imcando_hammer = True
    elif args.no_imcando_hammer:
        has_imcando_hammer = False
    else:
        has_imcando_hammer = preset.has_imcando_hammer

    # Check if any overrides were applied
    has_overrides = (
        args.harpoon is not None or
        args.spirit_angler or
        args.no_spirit_angler or
        args.imcando_hammer or
        args.no_imcando_hammer
    )

    # Display equipment info
    if has_overrides:
        print(f"Equipment: {preset.name} preset + overrides")
    else:
        print(f"Equipment preset: {preset.name}")
    print(f"  - Harpoon: {harpoon.value}")
    print(f"  - Spirit Angler: {'Yes' if has_spirit_angler else 'No'}")
    print(f"  - Imcando Hammer: {'Yes' if has_imcando_hammer else 'No'}")

    # Check fishing level for simulation
    actual_fishing = hiscores.fishing_level
    if actual_fishing < 35:
        print()
        print(f"Note: Fishing level {actual_fishing} is below 35. Using level 35 for simulation.")

    # Run simulation if requested
    if args.simulate:
        print()
        print("=" * 40)

        # Create player config with overrides applied
        player = PlayerConfig(
            fishing_level=max(35, hiscores.fishing_level),
            cooking_level=hiscores.cooking_level,
            harpoon_type=harpoon,
            has_spirit_angler=has_spirit_angler,
            has_imcando_hammer=has_imcando_hammer,
        )

        # Get strategy
        if args.strategy == "no-cook":
            strategy = Strategy.no_cook()
        elif args.strategy == "full-cook":
            strategy = Strategy.full_cook()
        elif args.strategy == "firefighting":
            strategy = Strategy.firefighting()
        else:
            strategy = Strategy.balanced()

        print(f"Running {args.simulations} simulations...")
        print(f"Strategy: {args.strategy}")
        print()

        results = run_monte_carlo(
            player_config=player,
            strategy=strategy,
            num_players=1,
            num_simulations=args.simulations,
        )

        avg = average_results(results)

        print("=== Simulation Results ===")
        print(f"Points: {avg.points:,}")
        print(f"Permits: {avg.permits}")
        print()
        print(f"Fishing XP/hr: {avg.fishing_xp_per_hour:,.0f}")
        print(f"Cooking XP/hr: {avg.cooking_xp_per_hour:,.0f}")
        print(f"Permits/hr: {avg.permits_per_hour:.1f}")


def get_potion_boost(potion_name: str, base_level: int = 99) -> PotionBoost:
    """Get potion boost by name."""
    if potion_name == "none":
        return PotionBoost()
    elif potion_name == "super_combat":
        return PotionBoost.super_combat(base_level)
    elif potion_name == "ranging":
        return PotionBoost.ranging_potion(base_level)
    elif potion_name == "divine_ranging":
        return PotionBoost.divine_ranging(base_level)
    elif potion_name == "imbued_heart":
        return PotionBoost.imbued_heart(base_level)
    elif potion_name == "saturated_heart":
        return PotionBoost.saturated_heart(base_level)
    return PotionBoost()


def build_equipment_stats(args) -> tuple:
    """Build equipment stats from preset and/or manual overrides.

    Returns:
        Tuple of (EquipmentStats, GearModifiers, preset_name or None).
    """
    stats = EquipmentStats()
    modifiers = GearModifiers()
    preset_name = None

    # Load from preset if specified
    preset_arg = getattr(args, 'preset', None)
    if preset_arg:
        preset = get_combat_preset(preset_arg)
        if preset is None:
            print(f"Error: Unknown preset '{preset_arg}'")
            print(f"Available presets: {', '.join(list_combat_presets()[:10])}...")
            sys.exit(1)
        stats = preset.equipment_stats
        modifiers = preset.gear_modifiers
        preset_name = preset.name

    # Apply manual overrides
    overrides = {}
    if getattr(args, 'melee_strength', None) is not None:
        overrides['melee_strength'] = args.melee_strength
    if getattr(args, 'ranged_attack', None) is not None:
        overrides['ranged_attack'] = args.ranged_attack
    if getattr(args, 'ranged_strength', None) is not None:
        overrides['ranged_strength'] = args.ranged_strength
    if getattr(args, 'magic_attack', None) is not None:
        overrides['magic_attack'] = args.magic_attack
    if getattr(args, 'magic_damage', None) is not None:
        overrides['magic_damage'] = args.magic_damage

    if overrides:
        # Create new stats with overrides
        stats = EquipmentStats(
            stab_attack=stats.stab_attack,
            slash_attack=stats.slash_attack,
            crush_attack=stats.crush_attack,
            magic_attack=overrides.get('magic_attack', stats.magic_attack),
            ranged_attack=overrides.get('ranged_attack', stats.ranged_attack),
            stab_defence=stats.stab_defence,
            slash_defence=stats.slash_defence,
            crush_defence=stats.crush_defence,
            magic_defence=stats.magic_defence,
            ranged_defence=stats.ranged_defence,
            melee_strength=overrides.get('melee_strength', stats.melee_strength),
            ranged_strength=overrides.get('ranged_strength', stats.ranged_strength),
            magic_damage=overrides.get('magic_damage', stats.magic_damage),
            prayer=stats.prayer,
        )

    return stats, modifiers, preset_name


def get_gear_modifiers(args) -> GearModifiers:
    """Build gear modifiers from args."""
    modifiers = GearModifiers()

    # Void equipment
    void_type = getattr(args, 'void', 'none')
    if void_type == "melee":
        modifiers.void_melee = True
    elif void_type == "ranged":
        modifiers.void_ranged = True
    elif void_type == "magic":
        modifiers.void_magic = True
    elif void_type == "elite_melee":
        modifiers.void_melee = True
        modifiers.elite_void = True
    elif void_type == "elite_ranged":
        modifiers.void_ranged = True
        modifiers.elite_void = True
    elif void_type == "elite_magic":
        modifiers.void_magic = True
        modifiers.elite_void = True

    # Slayer helm
    if getattr(args, 'slayer_helm', False):
        modifiers.slayer_helm_imbued = True

    # Salve amulet
    salve = getattr(args, 'salve', 'none')
    if salve == "salve":
        modifiers.salve_amulet = True
    elif salve == "salve_e":
        modifiers.salve_amulet_e = True
    elif salve == "salve_ei":
        modifiers.salve_amulet_ei = True

    return modifiers


def cmd_combat_dps(args):
    """Calculate combat DPS."""
    # Get weapon
    weapon = get_weapon(args.weapon)
    if weapon is None:
        print(f"Error: Unknown weapon '{args.weapon}'")
        print(f"Available weapons: {', '.join(list_weapons()[:10])}...")
        sys.exit(1)

    # Get monster
    monster = get_monster(args.target)
    if monster is None:
        print(f"Error: Unknown monster '{args.target}'")
        print(f"Available monsters: {', '.join(list_monsters()[:10])}...")
        sys.exit(1)

    # Get prayer
    prayer = get_prayer(args.prayer) or Prayer.NONE

    # Get stats - from hiscores or manual
    if args.username:
        client = HiscoresClient()
        try:
            if args.account_type:
                hiscores = client.lookup(args.username, args.account_type)
            else:
                hiscores = client.lookup_multiple_types(args.username)
                if hiscores is None:
                    print(f"Error: Player '{args.username}' not found.")
                    sys.exit(1)

            stats = SimCombatStats(
                attack=hiscores.skills.get("Attack", type("", (), {"level": 99})).level,
                strength=hiscores.skills.get("Strength", type("", (), {"level": 99})).level,
                ranged=hiscores.skills.get("Ranged", type("", (), {"level": 99})).level,
                magic=hiscores.skills.get("Magic", type("", (), {"level": 99})).level,
            )
            username = hiscores.username
        except (PlayerNotFoundError, RateLimitError, APIUnavailableError) as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        stats = SimCombatStats(
            attack=args.attack,
            strength=args.strength,
            ranged=args.ranged,
            magic=args.magic,
        )
        username = "Manual Stats"

    # Get potion boost
    potion = get_potion_boost(args.potion)

    # Get equipment stats from preset/overrides
    equipment_stats, preset_modifiers, preset_name = build_equipment_stats(args)

    # Get gear modifiers (merge preset modifiers with CLI flags)
    gear_modifiers = get_gear_modifiers(args)
    # Apply preset modifiers that aren't overridden by CLI
    if preset_modifiers.void_melee and not gear_modifiers.void_melee:
        gear_modifiers.void_melee = True
    if preset_modifiers.void_ranged and not gear_modifiers.void_ranged:
        gear_modifiers.void_ranged = True
    if preset_modifiers.void_magic and not gear_modifiers.void_magic:
        gear_modifiers.void_magic = True
    if preset_modifiers.elite_void:
        gear_modifiers.elite_void = True
    if preset_modifiers.slayer_helm_imbued and not gear_modifiers.slayer_helm_imbued:
        gear_modifiers.slayer_helm_imbued = True
    if preset_modifiers.inquisitor_set:
        gear_modifiers.inquisitor_set = True

    # Check for dragon hunter gear
    if "dragon_hunter" in args.weapon:
        if "lance" in args.weapon:
            gear_modifiers.dragon_hunter_lance = True
        elif "crossbow" in args.weapon:
            gear_modifiers.dragon_hunter_crossbow = True

    # Set up combat
    setup = CombatSetup(
        stats=stats,
        weapon=weapon,
        equipment_stats=equipment_stats,
        gear_modifiers=gear_modifiers,
        attack_style=AttackStyle.AGGRESSIVE,  # TODO: configurable
        prayer=prayer,
        potion=potion,
        target=monster,
        on_slayer_task=getattr(args, 'slayer_task', False),
    )

    # Calculate (with formula tracking if requested)
    calc = CombatCalculator(setup)
    track_formula = getattr(args, 'show_formula', False)
    result = calc.calculate(track_formula=track_formula)

    # Calculate kill time
    kill_time = result.calculate_kill_time(monster.hitpoints)

    # Output
    print(f"=== {username} vs {monster.name} ===")
    print(f"Weapon: {weapon.name} ({weapon.attack_speed} ticks)")
    print(f"Style: {setup.attack_style.display_name.title()}")
    print(f"Prayer: {prayer.name.replace('_', ' ').title()}")
    print(f"Potion: {args.potion.replace('_', ' ').title()}")
    if preset_name:
        print(f"Gear: {preset_name}")
    print()
    print(f"DPS: {result.dps:.2f}")
    print(f"Max Hit: {result.max_hit}")
    print(f"Hit Chance: {result.hit_chance:.1%}")
    print(f"Attack Roll: {result.attack_roll:,}")
    print(f"Defence Roll: {result.defence_roll:,}")
    print()
    print(f"Avg Kill Time: {kill_time:.1f} seconds")

    # Show formula breakdown if requested
    if track_formula and result.formula_breakdown:
        print()
        print(format_formula_breakdown(result.formula_breakdown))


def cmd_combat_list(args):
    """List combat data."""
    if args.category == "weapons":
        from combat.equipment import CombatStyle
        style_filter = None
        if args.style:
            style_map = {
                "melee": CombatStyle.MELEE,
                "ranged": CombatStyle.RANGED,
                "magic": CombatStyle.MAGIC,
            }
            style_filter = style_map.get(args.style)

        weapons = list_weapons(style_filter)
        print(f"=== Available Weapons ({len(weapons)}) ===")
        for name in sorted(weapons):
            w = get_weapon(name)
            if w:
                print(f"  {name}: {w.name} ({w.attack_speed}t, {w.attack_type.value})")

    elif args.category == "monsters":
        category_filter = getattr(args, 'category_filter', None)
        monsters = list_monsters(category_filter)
        filter_desc = f" [{category_filter}]" if category_filter else ""
        print(f"=== Available Monsters{filter_desc} ({len(monsters)}) ===")
        for name in sorted(monsters):
            m = get_monster(name)
            if m:
                print(f"  {name}: {m.name} ({m.hitpoints} HP, {m.defence_level} def)")

    elif args.category == "prayers":
        prayers = list_prayers()
        print(f"=== Available Prayers ({len(prayers)}) ===")
        for name in prayers:
            p = get_prayer(name)
            if p:
                bonuses = []
                if p.attack_multiplier > 1:
                    bonuses.append(f"atk +{(p.attack_multiplier-1)*100:.0f}%")
                if p.strength_multiplier > 1:
                    bonuses.append(f"str +{(p.strength_multiplier-1)*100:.0f}%")
                if p.ranged_attack_multiplier > 1:
                    bonuses.append(f"rng +{(p.ranged_attack_multiplier-1)*100:.0f}%")
                if p.magic_attack_multiplier > 1:
                    bonuses.append(f"mag +{(p.magic_attack_multiplier-1)*100:.0f}%")
                bonus_str = ", ".join(bonuses) if bonuses else "none"
                print(f"  {name}: {bonus_str}")

    elif args.category == "presets":
        presets = list_combat_presets()
        print(f"=== Available Equipment Presets ({len(presets)}) ===")
        for name in sorted(presets):
            preset = get_combat_preset(name)
            if preset:
                print(f"  {name}: {preset.description}")

    elif args.category == "spells":
        spells = list_spells()
        print(f"=== Available Spells ({len(spells)}) ===")
        for name in sorted(spells):
            s = get_spell(name)
            if s:
                multi = " [AoE]" if s.is_multi_target else ""
                print(f"  {name}: {s.name} (lvl {s.magic_level}, max {s.base_max_hit}){multi}")


def cmd_combat_simulate(args):
    """Run Monte Carlo combat simulation."""
    # Get weapon
    weapon = get_weapon(args.weapon)
    if weapon is None:
        print(f"Error: Unknown weapon '{args.weapon}'")
        sys.exit(1)

    # Get monster
    monster = get_monster(args.target)
    if monster is None:
        print(f"Error: Unknown monster '{args.target}'")
        sys.exit(1)

    # Get prayer
    prayer = get_prayer(args.prayer) or Prayer.NONE

    # Get stats
    if args.username:
        client = HiscoresClient()
        try:
            if args.account_type:
                hiscores = client.lookup(args.username, args.account_type)
            else:
                hiscores = client.lookup_multiple_types(args.username)
                if hiscores is None:
                    print(f"Error: Player '{args.username}' not found.")
                    sys.exit(1)

            stats = SimCombatStats(
                attack=hiscores.skills.get("Attack", type("", (), {"level": 99})).level,
                strength=hiscores.skills.get("Strength", type("", (), {"level": 99})).level,
                ranged=hiscores.skills.get("Ranged", type("", (), {"level": 99})).level,
                magic=hiscores.skills.get("Magic", type("", (), {"level": 99})).level,
            )
            username = hiscores.username
        except (PlayerNotFoundError, RateLimitError, APIUnavailableError) as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        stats = SimCombatStats(
            attack=args.attack,
            strength=args.strength,
            ranged=args.ranged,
            magic=args.magic,
        )
        username = None

    # Get potion boost
    potion = get_potion_boost(args.potion)

    # Get equipment stats from preset/overrides
    equipment_stats, preset_modifiers, preset_name = build_equipment_stats(args)

    # Set up combat
    setup = CombatSetup(
        stats=stats,
        weapon=weapon,
        equipment_stats=equipment_stats,
        gear_modifiers=preset_modifiers,
        attack_style=AttackStyle.AGGRESSIVE,
        prayer=prayer,
        potion=potion,
        target=monster,
    )

    # Calculate base DPS
    calc = CombatCalculator(setup)
    result = calc.calculate()

    display_name = username if username else "Manual Stats"
    print(f"=== {display_name} vs {monster.name} ({args.kills} kills) ===")
    print(f"Weapon: {weapon.name}")
    print(f"Prayer: {prayer.name.replace('_', ' ').title()}")
    if preset_name:
        print(f"Gear: {preset_name}")
    print()

    # Run simulation
    print(f"Simulating {args.kills} kills...")
    avg_time, std_dev, all_times = simulate_kill(
        result,
        monster.hitpoints,
        num_simulations=args.kills,
        seed=args.seed
    )

    # Statistics
    min_time = min(all_times)
    max_time = max(all_times)
    kills_per_hour = 3600 / avg_time if avg_time > 0 else 0

    print()
    print("=== Simulation Results ===")
    print(f"Average Kill Time: {avg_time:.1f}s")
    print(f"Std Deviation: {std_dev:.1f}s")
    print(f"Fastest Kill: {min_time:.1f}s")
    print(f"Slowest Kill: {max_time:.1f}s")
    print()
    print(f"Expected Kills/hr: {kills_per_hour:.1f}")
    print(f"Theoretical DPS: {result.dps:.2f}")

    # Save results if requested
    if getattr(args, 'save', False):
        storage = SimulationStorage()
        sim_result = SimulationResult(
            id=generate_simulation_id(),
            timestamp=time.time(),
            username=username,
            weapon_name=weapon.name,
            target_name=monster.name,
            prayer_name=args.prayer,
            potion_name=args.potion,
            attack=stats.attack,
            strength=stats.strength,
            defence=stats.defence,
            ranged=stats.ranged,
            magic=stats.magic,
            equipment_stats=asdict(equipment_stats),
            num_kills=args.kills,
            random_seed=args.seed,
            avg_kill_time=avg_time,
            std_dev=std_dev,
            min_time=min_time,
            max_time=max_time,
            kills_per_hour=kills_per_hour,
            dps=result.dps,
            max_hit=result.max_hit,
            hit_chance=result.hit_chance,
            attack_roll=result.attack_roll,
            defence_roll=result.defence_roll,
        )
        filepath = storage.save(sim_result)
        print()
        print(f"Results saved to: {filepath}")


def cmd_combat_data_fetch(args):
    """Fetch OSRS data from osrsreboxed-db."""
    from data_loader.fetcher import OSRSDataFetcher

    print("Fetching OSRS data from osrsreboxed-db...")
    print()

    fetcher = OSRSDataFetcher()
    try:
        metadata = fetcher.save_data(verbose=True)
        print()
        print("Data fetch complete! Run 'combat data stats' to see statistics.")
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)


def cmd_combat_data_stats(args):
    """Show statistics about loaded OSRS data."""
    from data_loader.fetcher import OSRSDataFetcher
    from data_loader.monster_loader import MonsterLoader
    from data_loader.item_loader import WeaponLoader

    fetcher = OSRSDataFetcher()

    if not fetcher.has_data():
        print("No data files found. Run 'combat data fetch' first.")
        sys.exit(1)

    metadata = fetcher.get_metadata()
    print("=== OSRS Data Statistics ===")
    print(f"Source: {metadata.get('source', 'unknown')}")
    print(f"Version: {metadata.get('version', 'unknown')}")
    print(f"Last Updated: {metadata.get('last_updated', 'unknown')}")
    print()

    # Load and count items
    data_dir = Path(__file__).parent / "data"
    monster_loader = MonsterLoader(data_dir / "monsters.json")
    weapon_loader = WeaponLoader(data_dir / "items.json")

    monster_count = monster_loader.count()
    boss_count = len(monster_loader.get_bosses())
    weapon_count = weapon_loader.count()

    print(f"Monsters: {monster_count:,} total ({boss_count:,} bosses)")
    print(f"Weapons: {weapon_count:,}")
    print()

    # Show some category breakdowns
    print("Monster Categories:")
    for attr in ["undead", "demon", "dragon", "kalphite"]:
        count = len(monster_loader.get_by_attribute(attr))
        if count > 0:
            print(f"  {attr.title()}: {count}")

    print()
    print("Weapon Styles:")
    from combat.equipment import CombatStyle
    for style in CombatStyle:
        count = len(weapon_loader.list_by_style(style))
        if count > 0:
            print(f"  {style.value.title()}: {count}")


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Initialize data loaders for combat commands
    if args.command == "combat":
        init_data_loaders()

    if args.command == "simulate":
        cmd_simulate(args)
    elif args.command == "optimize":
        cmd_optimize(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "pareto":
        cmd_pareto(args)
    elif args.command == "lookup":
        cmd_lookup(args)
    elif args.command == "combat":
        if args.combat_command == "dps":
            cmd_combat_dps(args)
        elif args.combat_command == "list":
            cmd_combat_list(args)
        elif args.combat_command == "simulate":
            cmd_combat_simulate(args)
        elif args.combat_command == "data":
            if args.data_action == "fetch":
                cmd_combat_data_fetch(args)
            elif args.data_action == "stats":
                cmd_combat_data_stats(args)
            else:
                print("Usage: python main.py combat data {fetch,stats}")
                sys.exit(1)
        else:
            print("Usage: python main.py combat {dps,list,simulate,data}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
