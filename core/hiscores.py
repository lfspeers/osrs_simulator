"""OSRS Hiscores API client for looking up player stats."""

import time
import urllib.request
import urllib.parse
import urllib.error
import json
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, List, Any


class HiscoresError(Exception):
    """Base exception for hiscores API errors."""
    pass


class PlayerNotFoundError(HiscoresError):
    """Raised when the requested player does not exist."""
    pass


class RateLimitError(HiscoresError):
    """Raised when the API rate limit is exceeded."""
    pass


class APIUnavailableError(HiscoresError):
    """Raised when the hiscores API is unavailable."""
    pass


class AccountType(Enum):
    """OSRS account types with their hiscores endpoint identifiers."""
    NORMAL = "hiscore_oldschool"
    IRONMAN = "hiscore_oldschool_ironman"
    HARDCORE_IRONMAN = "hiscore_oldschool_hardcore_ironman"
    ULTIMATE_IRONMAN = "hiscore_oldschool_ultimate"

    @property
    def display_name(self) -> str:
        """Human-readable account type name."""
        names = {
            AccountType.NORMAL: "normal",
            AccountType.IRONMAN: "ironman",
            AccountType.HARDCORE_IRONMAN: "hardcore ironman",
            AccountType.ULTIMATE_IRONMAN: "ultimate ironman",
        }
        return names[self]


@dataclass
class SkillData:
    """Data for a single skill from the hiscores."""
    name: str
    rank: int
    level: int
    xp: int


@dataclass
class ActivityData:
    """Data for a single activity/boss from the hiscores."""
    name: str
    rank: int
    score: int


# Skill names in the order they appear in the API response
SKILL_NAMES = [
    "Overall", "Attack", "Defence", "Strength", "Hitpoints", "Ranged",
    "Prayer", "Magic", "Cooking", "Woodcutting", "Fletching", "Fishing",
    "Firemaking", "Crafting", "Smithing", "Mining", "Herblore", "Agility",
    "Thieving", "Slayer", "Farming", "Runecraft", "Hunter", "Construction"
]

# Activity names in the order they appear in the API response
ACTIVITY_NAMES = [
    "League Points", "Deadman Points", "Bounty Hunter - Hunter",
    "Bounty Hunter - Rogue", "Bounty Hunter (Legacy) - Hunter",
    "Bounty Hunter (Legacy) - Rogue", "Clue Scrolls (all)", "Clue Scrolls (beginner)",
    "Clue Scrolls (easy)", "Clue Scrolls (medium)", "Clue Scrolls (hard)",
    "Clue Scrolls (elite)", "Clue Scrolls (master)", "LMS - Rank",
    "PvP Arena - Rank", "Soul Wars Zeal", "Rifts closed", "Colosseum Glory",
    "Abyssal Sire", "Alchemical Hydra", "Artio", "Barrows Chests",
    "Bryophyta", "Callisto", "Cal'varion", "Cerberus", "Chambers of Xeric",
    "Chambers of Xeric: Challenge Mode", "Chaos Elemental", "Chaos Fanatic",
    "Commander Zilyana", "Corporeal Beast", "Crazy Archaeologist",
    "Dagannoth Prime", "Dagannoth Rex", "Dagannoth Supreme", "Deranged Archaeologist",
    "Duke Sucellus", "General Graardor", "Giant Mole", "Grotesque Guardians",
    "Hespori", "Kalphite Queen", "King Black Dragon", "Kraken", "Kree'Arra",
    "K'ril Tsutsaroth", "Lunar Chests", "Mimic", "Nex", "Nightmare",
    "Phosani's Nightmare", "Obor", "Phantom Muspah", "Sarachnis", "Scorpia",
    "Scurrius", "Skotizo", "Sol Heredit", "Spindel", "Tempoross",
    "The Gauntlet", "The Corrupted Gauntlet", "The Hueycoatl", "The Leviathan",
    "The Whisperer", "Theatre of Blood", "Theatre of Blood: Hard Mode",
    "Thermonuclear Smoke Devil", "Tombs of Amascut", "Tombs of Amascut: Expert Mode",
    "TzKal-Zuk", "TzTok-Jad", "Vardorvis", "Venenatis", "Vet'ion", "Vorkath",
    "Wintertodt", "Zalcano", "Zulrah"
]


@dataclass
class PlayerHiscores:
    """Complete hiscores data for a player."""
    username: str
    account_type: AccountType
    skills: Dict[str, SkillData] = field(default_factory=dict)
    activities: Dict[str, ActivityData] = field(default_factory=dict)

    @property
    def fishing_level(self) -> int:
        """Get the player's fishing level."""
        skill = self.skills.get("Fishing")
        return skill.level if skill else 1

    @property
    def cooking_level(self) -> int:
        """Get the player's cooking level."""
        skill = self.skills.get("Cooking")
        return skill.level if skill else 1

    @property
    def construction_level(self) -> int:
        """Get the player's construction level."""
        skill = self.skills.get("Construction")
        return skill.level if skill else 1

    @property
    def tempoross_kc(self) -> int:
        """Get the player's Tempoross kill count."""
        activity = self.activities.get("Tempoross")
        return activity.score if activity and activity.score > 0 else 0


# Default characters folder location
DEFAULT_CHARACTERS_DIR = Path(__file__).parent.parent / "characters"


class HiscoresClient:
    """Client for the OSRS Hiscores API with persistent character storage."""

    BASE_URL = "https://secure.runescape.com/m={account_type}/index_lite.json?player={username}"
    USER_AGENT = "OSRS-Tempoross-Simulator/1.0"

    def __init__(self, characters_dir: Optional[Path] = None):
        """Initialize the client.

        Args:
            characters_dir: Path to characters folder. Defaults to ./characters/
        """
        self._characters_dir = characters_dir or DEFAULT_CHARACTERS_DIR
        self._characters_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, dict] = {}  # In-memory cache for current session

    def _get_character_file(self, username: str) -> Path:
        """Get the path to a character's JSON file."""
        safe_name = username.lower().replace(" ", "_")
        return self._characters_dir / f"{safe_name}.json"

    def _load_character(self, username: str) -> Optional[dict]:
        """Load character data from disk."""
        char_file = self._get_character_file(username)
        if not char_file.exists():
            return None

        try:
            with open(char_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _save_character(self, username: str, data: dict) -> None:
        """Save character data to disk."""
        char_file = self._get_character_file(username)
        try:
            with open(char_file, "w") as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass  # Silently fail if we can't write

    def _hiscores_to_dict(self, hiscores: PlayerHiscores) -> dict:
        """Convert PlayerHiscores to a JSON-serializable dict."""
        return {
            "username": hiscores.username,
            "account_type": hiscores.account_type.value,
            "skills": {
                name: {"name": s.name, "rank": s.rank, "level": s.level, "xp": s.xp}
                for name, s in hiscores.skills.items()
            },
            "activities": {
                name: {"name": a.name, "rank": a.rank, "score": a.score}
                for name, a in hiscores.activities.items()
            },
        }

    def _dict_to_hiscores(self, data: dict) -> PlayerHiscores:
        """Convert a cached dict back to PlayerHiscores."""
        skills = {
            name: SkillData(**s) for name, s in data.get("skills", {}).items()
        }
        activities = {
            name: ActivityData(**a) for name, a in data.get("activities", {}).items()
        }

        # Find the account type enum
        account_type_value = data.get("account_type", "hiscore_oldschool")
        account_type = AccountType.NORMAL
        for at in AccountType:
            if at.value == account_type_value:
                account_type = at
                break

        return PlayerHiscores(
            username=data.get("username", "Unknown"),
            account_type=account_type,
            skills=skills,
            activities=activities,
        )

    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self._cache.clear()

    def delete_character(self, username: str) -> bool:
        """Delete a character's saved data."""
        char_file = self._get_character_file(username)
        if char_file.exists():
            char_file.unlink()
            return True
        return False

    def get_saved_players(self) -> List[str]:
        """Get list of saved player names."""
        players = []
        if self._characters_dir.exists():
            for f in self._characters_dir.glob("*.json"):
                players.append(f.stem.replace("_", " "))
        return sorted(players)

    def lookup(
        self,
        username: str,
        account_type: AccountType = AccountType.NORMAL,
        force_refresh: bool = False
    ) -> PlayerHiscores:
        """Look up a player's hiscores data.

        Args:
            username: The player's username.
            account_type: The type of account to look up.
            force_refresh: If True, bypass saved data and fetch fresh from API.

        Returns:
            PlayerHiscores object with the player's data.

        Raises:
            PlayerNotFoundError: If the player does not exist on the hiscores.
            RateLimitError: If the API rate limit is exceeded.
            APIUnavailableError: If the API is unavailable.
        """
        # Check saved character data (unless force refresh)
        if not force_refresh:
            saved_data = self._load_character(username)
            if saved_data:
                # Check if account type matches
                saved_account_type = saved_data.get("account_type")
                if saved_account_type == account_type.value:
                    return self._dict_to_hiscores(saved_data)

        # Build URL
        url = self.BASE_URL.format(
            account_type=account_type.value,
            username=urllib.parse.quote(username)
        )

        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": self.USER_AGENT}
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise PlayerNotFoundError(f"Player '{username}' not found on {account_type.display_name} hiscores")
            elif e.code == 429:
                raise RateLimitError("Hiscores API rate limit exceeded. Please try again later.")
            else:
                raise APIUnavailableError(f"Hiscores API returned error {e.code}")
        except urllib.error.URLError as e:
            raise APIUnavailableError(f"Failed to connect to hiscores API: {e.reason}")
        except json.JSONDecodeError:
            raise APIUnavailableError("Invalid response from hiscores API")

        # Parse response
        hiscores = self._parse_response(username, account_type, data)

        # Save character data (with timestamp for reference)
        char_data = self._hiscores_to_dict(hiscores)
        char_data["last_updated"] = time.time()
        self._save_character(username, char_data)

        return hiscores

    def _parse_response(self, username: str, account_type: AccountType, data: dict) -> PlayerHiscores:
        """Parse the JSON response into a PlayerHiscores object."""
        skills: Dict[str, SkillData] = {}
        activities: Dict[str, ActivityData] = {}

        # Parse skills
        if "skills" in data:
            for skill_data in data["skills"]:
                skill = SkillData(
                    name=skill_data.get("name", "Unknown"),
                    rank=skill_data.get("rank", -1),
                    level=skill_data.get("level", 1),
                    xp=skill_data.get("xp", 0)
                )
                skills[skill.name] = skill

        # Parse activities
        if "activities" in data:
            for activity_data in data["activities"]:
                activity = ActivityData(
                    name=activity_data.get("name", "Unknown"),
                    rank=activity_data.get("rank", -1),
                    score=activity_data.get("score", -1)
                )
                activities[activity.name] = activity

        return PlayerHiscores(
            username=username,
            account_type=account_type,
            skills=skills,
            activities=activities
        )

    def lookup_multiple_types(self, username: str, force_refresh: bool = False) -> Optional[PlayerHiscores]:
        """Try to look up a player across multiple account types.

        Tries normal account first, then ironman variants.

        Args:
            username: The player's username.
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            PlayerHiscores for the first matching account type, or None if not found.
        """
        account_types = [
            AccountType.NORMAL,
            AccountType.IRONMAN,
            AccountType.HARDCORE_IRONMAN,
            AccountType.ULTIMATE_IRONMAN,
        ]

        for account_type in account_types:
            try:
                return self.lookup(username, account_type, force_refresh=force_refresh)
            except PlayerNotFoundError:
                continue

        return None


# Module-level client instance for convenience
_default_client: Optional[HiscoresClient] = None


def get_client() -> HiscoresClient:
    """Get the default HiscoresClient instance."""
    global _default_client
    if _default_client is None:
        _default_client = HiscoresClient()
    return _default_client


def lookup(username: str, account_type: AccountType = AccountType.NORMAL) -> PlayerHiscores:
    """Convenience function to look up a player using the default client."""
    return get_client().lookup(username, account_type)
