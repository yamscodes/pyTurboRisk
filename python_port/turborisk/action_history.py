"""
TurboRisk - Python Port
Action History Module

This module handles recording and managing game action history.
Ported from ActionHistory.pas
"""

import json
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .globals import G, ActionKind, ActionField, ACTION_FIELD_COUNT, ACTION_KIND_COUNT


# =============================================================================
# Constants
# =============================================================================

# Field names for JSON serialization
FIELD_NAMES = [
    'kind',
    'turn',
    'player',
    'opponent',
    'from',
    'to',
    'armies',
    'attacker_loss',
    'defender_loss',
    'captured',
    'from_before',
    'to_before',
    'from_after',
    'to_after'
]

# Action field constants
ACTION_FIELD_CONSTANTS = [
    'AF_KIND',
    'AF_TURN',
    'AF_PLAYER',
    'AF_OPPONENT',
    'AF_FROM',
    'AF_TO',
    'AF_ARMIES',
    'AF_ATTACKER_LOSS',
    'AF_DEFENDER_LOSS',
    'AF_CAPTURED',
    'AF_FROM_BEFORE',
    'AF_TO_BEFORE',
    'AF_FROM_AFTER',
    'AF_TO_AFTER'
]

# Action kind constants
ACTION_KIND_CONSTANTS = [
    'AK_ASSIGNMENT',
    'AK_PLACEMENT',
    'AK_ATTACK',
    'AK_OCCUPATION',
    'AK_FORTIFICATION',
    'AK_TURN_START',
    'AK_TURN_END',
    'AK_REINFORCEMENT',
    'AK_CARD_TRADE',
    'AK_ELIMINATION',
    'AK_GAME_END'
]


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class ActionEvent:
    """Represents a single game action event"""
    # Using 1-indexed fields to match Pascal implementation
    kind: int = 0
    turn: int = 0
    player: int = 0
    opponent: int = 0
    from_terr: int = 0
    to_terr: int = 0
    armies: int = 0
    attacker_loss: int = 0
    defender_loss: int = 0
    captured: int = 0
    from_before: int = 0
    to_before: int = 0
    from_after: int = 0
    to_after: int = 0
    
    def to_list(self) -> List[int]:
        """Convert to list for storage"""
        return [
            self.kind,
            self.turn,
            self.player,
            self.opponent,
            self.from_terr,
            self.to_terr,
            self.armies,
            self.attacker_loss,
            self.defender_loss,
            self.captured,
            self.from_before,
            self.to_before,
            self.from_after,
            self.to_after
        ]
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for JSON serialization"""
        return {
            FIELD_NAMES[i]: getattr(self, attr) 
            for i, attr in enumerate([
                'kind', 'turn', 'player', 'opponent', 'from_terr', 'to_terr',
                'armies', 'attacker_loss', 'defender_loss', 'captured',
                'from_before', 'to_before', 'from_after', 'to_after'
            ])
        }
    
    @classmethod
    def from_list(cls, data: List[int]) -> 'ActionEvent':
        """Create from list"""
        if len(data) != ACTION_FIELD_COUNT:
            raise ValueError(f"Expected {ACTION_FIELD_COUNT} fields, got {len(data)}")
        return cls(
            kind=data[0],
            turn=data[1],
            player=data[2],
            opponent=data[3],
            from_terr=data[4],
            to_terr=data[5],
            armies=data[6],
            attacker_loss=data[7],
            defender_loss=data[8],
            captured=data[9],
            from_before=data[10],
            to_before=data[11],
            from_after=data[12],
            to_after=data[13]
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'ActionEvent':
        """Create from dictionary"""
        return cls(
            kind=data.get('kind', 0),
            turn=data.get('turn', 0),
            player=data.get('player', 0),
            opponent=data.get('opponent', 0),
            from_terr=data.get('from', 0),
            to_terr=data.get('to', 0),
            armies=data.get('armies', 0),
            attacker_loss=data.get('attacker_loss', 0),
            defender_loss=data.get('defender_loss', 0),
            captured=data.get('captured', 0),
            from_before=data.get('from_before', 0),
            to_before=data.get('to_before', 0),
            from_after=data.get('from_after', 0),
            to_after=data.get('to_after', 0)
        )


# =============================================================================
# Global State
# =============================================================================

class ActionHistoryState:
    """Global state for action history"""
    def __init__(self):
        self.events: List[ActionEvent] = []
        self.event_count: int = 0
        self.game_id: str = ""
        self.parent_game_id: str = ""
        self.game_metadata: str = ""
        self.log_file_name: str = ""
        self.log_segment_id: str = ""
        self.history_from_start: bool = True
        self.log_stream = None


# Create global instance
action_history = ActionHistoryState()


# =============================================================================
# Action History Functions
# =============================================================================

def unique_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())


def new_game_id():
    """Generate a new game ID"""
    action_history.game_id = unique_id()


def begin_action_history(metadata: str = ""):
    """
    Begin recording action history.
    Ported from BeginActionHistory in ActionHistory.pas
    """
    action_history.event_count = 0
    action_history.events = []
    action_history.parent_game_id = ""
    action_history.game_metadata = metadata
    action_history.history_from_start = True
    new_game_id()
    write_game_header()


def record_action(event: ActionEvent):
    """
    Record a game action.
    Ported from RecordAction in ActionHistory.pas
    """
    if not action_history.game_id:
        return
    
    validate_event(event)
    
    # Grow the list if needed
    if action_history.event_count == len(action_history.events):
        new_size = action_history.event_count * 2 + 128
        if new_size > (2**31 // 2) - 128:
            raise MemoryError("Action history capacity exceeded")
        action_history.events.extend([ActionEvent()] * 128)
    
    action_history.events[action_history.event_count] = event
    action_history.event_count += 1
    write_event(action_history.event_count)


def end_action_history(turn: int, winner: int, status: int):
    """
    End the action history.
    Ported from EndActionHistory in ActionHistory.pas
    """
    if not action_history.game_id:
        return
    
    # Check if already ended
    if action_history.event_count > 0:
        last_event = action_history.events[action_history.event_count - 1]
        if last_event.kind == ActionKind.AK_GAME_END.value:
            return
    
    # Create end game event
    event = ActionEvent()
    event.kind = ActionKind.AK_GAME_END.value
    event.turn = turn
    event.player = winner
    event.armies = status
    record_action(event)


def action_count() -> int:
    """Get the number of actions recorded"""
    return action_history.event_count


def action_value(index: int, field: int) -> int:
    """
    Get a specific field value from an action.
    Ported from ActionValue in ActionHistory.pas
    """
    if index < 1 or index > action_history.event_count:
        raise IndexError(f"Action index {index} is outside 1..{action_history.event_count}")
    if field < 1 or field > ACTION_FIELD_COUNT:
        raise IndexError(f"Action field {field} is outside 1..{ACTION_FIELD_COUNT}")
    
    # Convert to 0-indexed
    event = action_history.events[index - 1]
    event_list = event.to_list()
    return event_list[field - 1]


def validate_event(event: ActionEvent):
    """
    Validate an action event.
    Ported from ValidateEvent in ActionHistory.pas
    """
    event_list = event.to_list()
    for i, value in enumerate(event_list):
        if value < 0:
            raise ValueError(f"Negative action-history field {FIELD_NAMES[i]}")
    
    if (event.kind < 1 or event.kind > ACTION_KIND_COUNT or
        event.player > 10 or event.opponent > 10 or
        event.from_terr > 42 or event.to_terr > 42 or
        event.captured > 1):
        raise ValueError("Invalid action-history kind, player or territory")


def write_game_header():
    """Write game header to log"""
    if not action_history.log_stream or not action_history.game_id:
        return
    
    action_history.log_segment_id = unique_id()
    header = {
        'format': 'TurboRisk.actions',
        'version': 1,
        'type': 'game',
        'game': action_history.game_id,
        'segment': action_history.log_segment_id,
        'parent_game': action_history.parent_game_id,
        'history_from_start': action_history.history_from_start,
        'metadata': action_history.game_metadata
    }
    write_json_line(json.dumps(header))


def write_event(sequence: int):
    """Write an event to the log"""
    if not action_history.log_stream:
        return
    
    if sequence < 1 or sequence > action_history.event_count:
        return
    
    event = action_history.events[sequence - 1]
    event_dict = event.to_dict()
    event_dict['type'] = 'action'
    event_dict['game'] = action_history.game_id
    event_dict['segment'] = action_history.log_segment_id
    event_dict['sequence'] = sequence
    write_json_line(json.dumps(event_dict))


def write_json_line(line: str):
    """Write a JSON line to the log stream"""
    if not action_history.log_stream:
        return
    
    try:
        action_history.log_stream.write((line + '\n').encode('utf-8'))
        action_history.log_stream.flush()
    except Exception as e:
        action_history.log_stream = None
        action_history.log_file_name = ""
        raise IOError(f"Cannot write action log \"{action_history.log_file_name}\": {str(e)}")


def start_action_log(filename: str, include_current_history: bool = True):
    """
    Start logging actions to a file.
    Ported from StartActionLog in ActionHistory.pas
    """
    import os
    
    # Try to open the file
    try:
        # If file exists, read first line to check format
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                first_line = f.readline().strip()
            if first_line:
                try:
                    header = json.loads(first_line)
                    if header.get('type') == 'game':
                        # This is a continuation of an existing log
                        action_history.history_from_start = False
                        action_history.parent_game_id = header.get('game', '')
                except json.JSONDecodeError:
                    pass
        
        # Open in append mode
        action_history.log_file_name = filename
        action_history.log_stream = open(filename, 'a', encoding='utf-8')
        
        # If this is the start of history, write game header
        if action_history.history_from_start and action_history.game_id:
            write_game_header()
        
        # Write existing events if requested
        if include_current_history:
            for i in range(1, action_history.event_count + 1):
                write_event(i)
    except Exception as e:
        action_history.log_stream = None
        action_history.log_file_name = ""
        raise IOError(f"Cannot open action log \"{filename}\": {str(e)}")


def stop_action_log():
    """Stop logging actions"""
    if action_history.log_stream:
        try:
            action_history.log_stream.close()
        except:
            pass
        action_history.log_stream = None
    action_history.log_file_name = ""


def action_log_file_name() -> str:
    """Get the current action log filename"""
    return action_history.log_file_name


def save_action_history(ini_filename: str):
    """
    Save action history to an INI file.
    Ported from SaveActionHistory in ActionHistory.pas
    """
    import configparser
    
    config = configparser.ConfigParser()
    
    # Clear existing section
    if 'ActionHistory' in config:
        config.remove_section('ActionHistory')
    
    config['ActionHistory'] = {}
    config['ActionHistory']['Version'] = str(1)
    config['ActionHistory']['GameID'] = action_history.game_id
    config['ActionHistory']['FromStart'] = str(action_history.history_from_start)
    config['ActionHistory']['Count'] = str(action_history.event_count)
    
    # Save each event
    for i in range(1, action_history.event_count + 1):
        event = action_history.events[i - 1]
        config['ActionHistory'][f'Event{i}'] = json.dumps(event.to_dict())
    
    # Write to file
    with open(ini_filename, 'w') as f:
        config.write(f)


def load_action_history(ini_filename: str, metadata: str = ""):
    """
    Load action history from an INI file.
    Ported from LoadActionHistory in ActionHistory.pas
    """
    import configparser
    
    config = configparser.ConfigParser()
    config.read(ini_filename)
    
    if 'ActionHistory' not in config:
        raise ValueError("No ActionHistory section in INI file")
    
    # Check version
    version = config['ActionHistory'].getint('Version', 0)
    if version != 1:
        raise ValueError(f"Unsupported saved action-history version: {version}")
    
    # Load events
    count = config['ActionHistory'].getint('Count', 0)
    loaded_events = []
    
    for i in range(1, count + 1):
        event_str = config['ActionHistory'].get(f'Event{i}', '')
        if not event_str:
            raise ValueError(f"Missing event {i}")
        event_dict = json.loads(event_str)
        event = ActionEvent.from_dict(event_dict)
        validate_event(event)
        loaded_events.append(event)
    
    action_history.events = loaded_events
    action_history.event_count = count
    action_history.parent_game_id = config['ActionHistory'].get('GameID', '')
    action_history.history_from_start = config['ActionHistory'].getboolean('FromStart', False)
    action_history.game_metadata = metadata
    
    new_game_id()
    write_game_header()
    
    for i in range(1, action_history.event_count + 1):
        write_event(i)


# =============================================================================
# Convenience Functions
# =============================================================================

def record_game_action(kind: ActionKind, player: int, opponent: int, from_t: int, to_t: int,
                       armies: int, from_before: int = 0, to_before: int = 0,
                       attacker_loss: int = 0, defender_loss: int = 0, captured: int = 0):
    """
    Record a game action with all fields.
    This is a convenience function that creates an ActionEvent and records it.
    """
    event = ActionEvent()
    event.kind = kind.value
    event.turn = G.i_turn_counter
    event.player = player
    event.opponent = opponent
    event.from_terr = from_t
    event.to_terr = to_t
    event.armies = armies
    event.from_before = from_before
    event.to_before = to_before
    event.attacker_loss = attacker_loss
    event.defender_loss = defender_loss
    event.captured = captured
    
    # Set after values if from/to territories are valid
    if from_t > 0 and from_t <= 42:
        event.from_after = G.ar_territory[from_t].army
    if to_t > 0 and to_t <= 42:
        event.to_after = G.ar_territory[to_t].army
    
    record_action(event)


# =============================================================================
# Export all functions and classes
# =============================================================================

__all__ = [
    'ActionEvent',
    'ActionHistoryState',
    'action_history',
    'FIELD_NAMES',
    'ACTION_FIELD_CONSTANTS',
    'ACTION_KIND_CONSTANTS',
    'begin_action_history',
    'end_action_history',
    'record_action',
    'action_count',
    'action_value',
    'validate_event',
    'start_action_log',
    'stop_action_log',
    'action_log_file_name',
    'save_action_history',
    'load_action_history',
    'record_game_action',
]
