"""Game tick system for OSRS simulation.

All game actions in OSRS resolve on tick boundaries.
Base tick duration is 0.6 seconds (600ms).
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Any
from enum import Enum
import heapq


# Base tick duration in seconds
TICK_DURATION = 0.6


class ActionPriority(Enum):
    """Priority levels for action processing within a tick."""
    HIGH = 0
    NORMAL = 1
    LOW = 2


@dataclass(order=True)
class Action:
    """An action scheduled to execute on a specific tick.

    Attributes:
        tick: The game tick when this action should execute.
        priority: Priority for ordering actions on the same tick.
        callback: Function to call when the action executes.
        name: Optional name for debugging.
        data: Optional data to pass to the callback.
    """
    tick: int
    priority: ActionPriority = field(compare=True, default=ActionPriority.NORMAL)
    callback: Callable[..., Any] = field(compare=False, default=lambda: None)
    name: str = field(compare=False, default="")
    data: Any = field(compare=False, default=None)

    def execute(self) -> Any:
        """Execute the action's callback."""
        if self.data is not None:
            return self.callback(self.data)
        return self.callback()


class ActionQueue:
    """Priority queue for scheduling and processing game actions."""

    def __init__(self):
        self._queue: list[tuple[int, int, int, Action]] = []
        self._counter = 0

    def schedule(
        self,
        tick: int,
        callback: Callable[..., Any],
        priority: ActionPriority = ActionPriority.NORMAL,
        name: str = "",
        data: Any = None
    ) -> Action:
        """Schedule an action to execute on a specific tick.

        Args:
            tick: The game tick when the action should execute.
            callback: Function to call when the action executes.
            priority: Priority for ordering actions on the same tick.
            name: Optional name for debugging.
            data: Optional data to pass to the callback.

        Returns:
            The scheduled Action object.
        """
        action = Action(
            tick=tick,
            priority=priority,
            callback=callback,
            name=name,
            data=data
        )
        heapq.heappush(
            self._queue,
            (tick, priority.value, self._counter, action)
        )
        self._counter += 1
        return action

    def get_actions_for_tick(self, tick: int) -> list[Action]:
        """Get all actions scheduled for a specific tick.

        Actions are returned in priority order and removed from the queue.
        """
        actions = []
        while self._queue and self._queue[0][0] == tick:
            _, _, _, action = heapq.heappop(self._queue)
            actions.append(action)
        return actions

    def peek_next_tick(self) -> Optional[int]:
        """Return the tick of the next scheduled action, or None if empty."""
        return self._queue[0][0] if self._queue else None

    def clear(self):
        """Remove all scheduled actions."""
        self._queue.clear()
        self._counter = 0

    def __len__(self) -> int:
        return len(self._queue)

    def __bool__(self) -> bool:
        return bool(self._queue)


class GameClock:
    """Manages game tick timing and action processing.

    The game clock tracks the current tick and processes actions
    scheduled in the action queue.
    """

    def __init__(self):
        self._tick = 0
        self._action_queue = ActionQueue()

    @property
    def tick(self) -> int:
        """Current game tick."""
        return self._tick

    @property
    def time_seconds(self) -> float:
        """Current time in seconds."""
        return self._tick * TICK_DURATION

    @property
    def action_queue(self) -> ActionQueue:
        """The action queue for scheduling."""
        return self._action_queue

    def schedule(
        self,
        delay_ticks: int,
        callback: Callable[..., Any],
        priority: ActionPriority = ActionPriority.NORMAL,
        name: str = "",
        data: Any = None
    ) -> Action:
        """Schedule an action to execute after a delay.

        Args:
            delay_ticks: Number of ticks from now to execute.
            callback: Function to call when the action executes.
            priority: Priority for ordering actions on the same tick.
            name: Optional name for debugging.
            data: Optional data to pass to the callback.

        Returns:
            The scheduled Action object.
        """
        return self._action_queue.schedule(
            tick=self._tick + delay_ticks,
            callback=callback,
            priority=priority,
            name=name,
            data=data
        )

    def advance(self) -> list[Any]:
        """Advance to the next tick and process all scheduled actions.

        Returns:
            List of results from executed action callbacks.
        """
        self._tick += 1
        actions = self._action_queue.get_actions_for_tick(self._tick)
        return [action.execute() for action in actions]

    def advance_to(self, target_tick: int) -> list[list[Any]]:
        """Advance to a specific tick, processing all actions along the way.

        Args:
            target_tick: The tick to advance to.

        Returns:
            List of results for each tick processed.
        """
        results = []
        while self._tick < target_tick:
            results.append(self.advance())
        return results

    def skip_to_next_action(self) -> Optional[list[Any]]:
        """Skip to the next tick with scheduled actions.

        Returns:
            Results from the executed actions, or None if no actions remain.
        """
        next_tick = self._action_queue.peek_next_tick()
        if next_tick is None:
            return None

        self._tick = next_tick - 1
        return self.advance()

    def reset(self):
        """Reset the clock to tick 0 and clear all actions."""
        self._tick = 0
        self._action_queue.clear()


def ticks_to_seconds(ticks: int) -> float:
    """Convert game ticks to seconds."""
    return ticks * TICK_DURATION


def seconds_to_ticks(seconds: float) -> int:
    """Convert seconds to game ticks (rounds down)."""
    return int(seconds / TICK_DURATION)


def ticks_per_hour() -> int:
    """Return the number of game ticks in one hour."""
    return seconds_to_ticks(3600)
