# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OSRS Simulator - A Python application for Old School RuneScape with two main features:
1. **Tempoross Minigame Simulator** - Tick-accurate simulation and strategy optimization
2. **Combat DPS Calculator** - Damage-per-second calculations with external data integration

## Running Commands

```bash
# Tempoross simulation
python main.py simulate --fishing-level 99 --strategy balanced --simulations 10

# Combat DPS calculation
python main.py combat dps --weapon ghrazi_rapier --target vorkath --prayer piety

# Fetch OSRS data from osrsreboxed-db (GitHub)
python main.py combat data fetch

# Show loaded data statistics
python main.py combat data stats

# List available items
python main.py combat list weapons --style melee
python main.py combat list monsters --category-filter bosses
python main.py combat list spells

# Player hiscores lookup
python main.py lookup username --simulate --strategy balanced

# Strategy optimization
python main.py optimize --objective permits --simulations 10
```

## Architecture

### Module Structure

- **`core/`** - Game fundamentals: tick system (0.6s/tick), player config, OSRS Hiscores API client
- **`tempoross/`** - Minigame simulation: tick-accurate game loop, phase mechanics, strategy optimizer
- **`combat/`** - DPS system: formulas from OSRS Wiki, equipment stats, prayers, monsters, spells
- **`data_loader/`** - External data: fetches from osrsreboxed-db, loads into dataclasses
- **`presets/`** - Pre-configured equipment sets for Tempoross and combat
- **`data/`** - JSON data files (items.json, monsters.json) - gitignored, re-fetchable

### Data Flow

**Combat DPS:**
```
CombatSetup (stats, weapon, target, prayer, potion)
    ↓
External loaders (optional): set_monster_loader(), set_weapon_loader()
    ↓
CombatCalculator.calculate() → CombatResult (DPS, max hit, hit chance)
```

**External Data Integration:**
- `data_loader/fetcher.py` downloads from GitHub raw URLs
- Loaders (`MonsterLoader`, `WeaponLoader`) parse JSON into dataclasses
- Combat module functions (`get_weapon`, `get_monster`) check external loader first, fall back to hardcoded
- Data files are large (~15MB items, ~9MB monsters) and excluded from git

### Key Patterns

- **Tick-based simulation**: `GameClock` with `ActionQueue` schedules actions at specific ticks
- **Lazy loading**: Data loaders use `_load()` pattern - data parsed on first access
- **Dual data sources**: Hardcoded definitions for curated data, external JSON for comprehensive coverage
- **Formula tracking**: Pass `track_formula=True` to get detailed calculation breakdowns

## Data Sources

- **osrsreboxed-db**: https://github.com/0xNeffarion/osrsreboxed-db - OSRS cache-derived JSON
- **OSRS Hiscores**: Official API for player stats (with caching in `.hiscores_cache.json`)

## Current Data Coverage

After running `combat data fetch`:
- 400+ monsters (45 bosses, dragons, demons, undead, etc.)
- 993 weapons (melee, ranged, magic)
- 42 combat spells (Standard and Ancient Magicks)
