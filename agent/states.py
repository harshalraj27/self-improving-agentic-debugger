from __future__ import annotations

from enum import Enum, auto, unique
from typing import Final


@unique
class State(Enum):
    READY = auto()
    OBSERVED = auto()
    EVALUATED = auto()
    ACTION_SELECTED = auto()
    ACTED = auto()
    TERMINATED = auto()


@unique
class TransitionEvent(Enum):
    SUCCESS = auto()
    CONTINUE = auto()
    HALT = auto()


_CYCLE_TRANSITIONS: Final[dict[State, State]] = {
    State.READY: State.OBSERVED,
    State.OBSERVED: State.EVALUATED,
    State.EVALUATED: State.ACTION_SELECTED,
    State.ACTION_SELECTED: State.ACTED,
    State.ACTED: State.READY,
}

_TERMINAL_EVENTS: Final[frozenset[TransitionEvent]] = frozenset(
    {TransitionEvent.SUCCESS, TransitionEvent.HALT}
)


def validate_and_get_next(
    current_state: State,
    event: TransitionEvent,
) -> State:
    if current_state is State.TERMINATED:
        raise ValueError(
            f"Illegal transition: {State.TERMINATED.name} is a sink state "
            f"and cannot transition on event {event.name}."
        )

    if event in _TERMINAL_EVENTS:
        return State.TERMINATED

    if event is not TransitionEvent.CONTINUE:
        raise ValueError(f"Unsupported transition event: {event!r}.")

    try:
        return _CYCLE_TRANSITIONS[current_state]
    except KeyError as exc:
        raise ValueError(
            f"Illegal CONTINUE transition from state {current_state.name}."
        ) from exc