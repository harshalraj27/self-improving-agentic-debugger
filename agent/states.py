from enum import Enum, auto, unique


@unique
class State(Enum):
    READY =  auto()
    OBSERVED = auto()
    EVALUATED = auto()
    ACTION_SELECTED = auto()
    ACTED = auto()
    TERMINATED = auto()

states = {
    State.READY: State.OBSERVED,
    State.OBSERVED: State.EVALUATED,
    State.EVALUATED: State.ACTION_SELECTED,
    State.ACTION_SELECTED: State.ACTED,
    State.ACTED: State.READY
}

def get_next_state(state: State):
    try:
        return states.get(state)
    except KeyError:
        return "PROCESS TERMINATED"
