"""Combat simulation result storage.

Provides persistence for simulation results, following the pattern
established in core/hiscores.py for character data storage.
"""

import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, List, Dict, Any


# Default storage directory relative to project root
DEFAULT_SIMULATIONS_DIR = Path(__file__).parent.parent / "simulations"


@dataclass
class SimulationResult:
    """A saved combat simulation result.

    Contains all the information needed to reproduce or analyze
    a simulation run.
    """
    # Identification
    id: str  # Timestamp-based unique ID
    timestamp: float  # Unix timestamp when simulation was run

    # Setup info
    username: Optional[str]  # Player username if looked up
    weapon_name: str
    target_name: str
    prayer_name: str
    potion_name: str

    # Player stats used
    attack: int
    strength: int
    defence: int
    ranged: int
    magic: int

    # Equipment stats (as dict for JSON serialization)
    equipment_stats: Dict[str, Any] = field(default_factory=dict)

    # Gear modifiers active
    gear_modifiers: Dict[str, bool] = field(default_factory=dict)

    # Simulation parameters
    num_kills: int = 0
    random_seed: Optional[int] = None

    # Results
    avg_kill_time: float = 0.0
    std_dev: float = 0.0
    min_time: float = 0.0
    max_time: float = 0.0
    kills_per_hour: float = 0.0

    # DPS calculation results
    dps: float = 0.0
    max_hit: int = 0
    hit_chance: float = 0.0
    attack_roll: int = 0
    defence_roll: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationResult":
        """Create a SimulationResult from a dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class SimulationStorage:
    """Manager for saving and loading simulation results.

    Stores results as JSON files in a dedicated directory.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize the storage manager.

        Args:
            storage_dir: Directory to store simulation files.
                         Defaults to ./simulations/
        """
        self._storage_dir = storage_dir or DEFAULT_SIMULATIONS_DIR
        self._storage_dir.mkdir(exist_ok=True)

    def _get_filepath(self, sim_id: str) -> Path:
        """Get the file path for a simulation ID."""
        return self._storage_dir / f"sim_{sim_id}.json"

    def save(self, result: SimulationResult) -> Path:
        """Save a simulation result to disk.

        Args:
            result: The SimulationResult to save.

        Returns:
            Path to the saved file.
        """
        filepath = self._get_filepath(result.id)

        with open(filepath, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        return filepath

    def load(self, sim_id: str) -> Optional[SimulationResult]:
        """Load a simulation result by ID.

        Args:
            sim_id: The simulation ID (timestamp-based).

        Returns:
            SimulationResult if found, None otherwise.
        """
        filepath = self._get_filepath(sim_id)

        if not filepath.exists():
            return None

        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return SimulationResult.from_dict(data)
        except (json.JSONDecodeError, IOError, TypeError):
            return None

    def delete(self, sim_id: str) -> bool:
        """Delete a simulation result.

        Args:
            sim_id: The simulation ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        filepath = self._get_filepath(sim_id)

        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def list_all(self) -> List[str]:
        """List all saved simulation IDs.

        Returns:
            List of simulation IDs (without the 'sim_' prefix).
        """
        if not self._storage_dir.exists():
            return []

        return sorted([
            f.stem.replace("sim_", "")
            for f in self._storage_dir.glob("sim_*.json")
        ], reverse=True)  # Most recent first

    def list_recent(self, count: int = 10) -> List[SimulationResult]:
        """List the most recent simulation results.

        Args:
            count: Number of results to return.

        Returns:
            List of SimulationResult objects.
        """
        sim_ids = self.list_all()[:count]
        results = []

        for sim_id in sim_ids:
            result = self.load(sim_id)
            if result:
                results.append(result)

        return results

    def get_storage_dir(self) -> Path:
        """Get the storage directory path."""
        return self._storage_dir


def generate_simulation_id() -> str:
    """Generate a unique simulation ID based on timestamp.

    Returns:
        String ID in format: timestamp (e.g., "1706644800")
    """
    return str(int(time.time()))
