# ../gungame/plugins/custom/gg_ffa_bots/gg_ffa_bots.py

"""Plugin that causes bots to attack teammates."""

# =============================================================================
# >> IMPORTS
# =============================================================================
# Python
import binascii
import json

# Source.Python
from core import GAME_NAME, PLATFORM
from entities.entity import Entity
from memory import Convention, DataType, find_binary, make_object
from memory.hooks import PreHook
from players.entity import Player

# GunGame
from gungame.core.paths import GUNGAME_DATA_PATH

# Plugin
from .info import info

# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
_data_file = GUNGAME_DATA_PATH / info.name + ".json"
with _data_file.open() as _open_file:
    _data = json.load(_open_file).get(GAME_NAME, {}).get(PLATFORM, {})
if not _data:
    msg = f'Game "{GAME_NAME}" on platform "{PLATFORM}" not currently supported'
    raise NotImplementedError(msg)

if PLATFORM == "windows":
    for _key, _value in _data.items():
        _data[_key] = binascii.unhexlify(_value.replace(" ", ""))

server = find_binary("server")

GetTeamNumber = server[_data["GetTeamNumber"]].make_function(
    Convention.THISCALL,
    [DataType.POINTER],
    DataType.INT,
)

InSameTeam = server[_data["InSameTeam"]].make_function(
    Convention.THISCALL,
    [DataType.POINTER, DataType.POINTER],
    DataType.BOOL,
)

OnAudibleEvent = server[_data["OnAudibleEvent"]].make_function(
    Convention.THISCALL,
    [
        DataType.POINTER,
        DataType.POINTER,
        DataType.POINTER,
        DataType.FLOAT,
        DataType.INT,
        DataType.BOOL,
        DataType.BOOL,
        DataType.POINTER,
    ],
    DataType.VOID,
)

OnPlayerRadio = server[_data["OnPlayerRadio"]].make_function(
    Convention.THISCALL,
    [DataType.POINTER, DataType.POINTER],
    DataType.VOID,
)

_hacked_teams = {}


# =============================================================================
# >> FUNCTION HOOKS
# =============================================================================
@PreHook(OnAudibleEvent)
def _pre_on_audible_event(stack_data):
    """Store the opposite team for later retrieval."""
    other = stack_data[2]
    if not other:
        return

    entity = make_object(Entity, other)
    team_number = entity.team_index
    entity2 = make_object(Entity, stack_data[0])
    if entity2.team_index == team_number:
        _hacked_teams[other] = 5 - team_number


@PreHook(GetTeamNumber)
def _pre_get_team_number(stack_data):
    """Retrieve the opposite team from above and return that value."""
    pointer = stack_data[0]
    return _hacked_teams.pop(pointer, None)


@PreHook(InSameTeam)
def _pre_in_same_team(stack_data):
    """Return False for bots from InSameTeam."""
    other = stack_data[1]
    if stack_data[0] == other:
        return None

    entity = make_object(Entity, other)
    if entity.classname != "player":
        return None

    player = Player(entity.index)
    if player.is_fake_client():
        return False

    return None


@PreHook(OnPlayerRadio)
def _pre_on_player_radio(stack_data):
    """Return 0 when radio commands are issued."""
    return 0
