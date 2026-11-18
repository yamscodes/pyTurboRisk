"""
Tests for the action_history module
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from turborisk.action_history import (
    ActionEvent, ActionKind, ActionField,
    begin_action_history, end_action_history, record_action, action_count,
    action_value, validate_event, start_action_log, stop_action_log,
    action_log_file_name, save_action_history, load_action_history,
    action_history
)


class TestActionEvent(unittest.TestCase):
    """Test ActionEvent class"""
    
    def test_create_default(self):
        """Test creating a default ActionEvent"""
        event = ActionEvent()
        self.assertEqual(event.kind, 0)
        self.assertEqual(event.turn, 0)
        self.assertEqual(event.player, 0)
    
    def test_create_with_values(self):
        """Test creating an ActionEvent with values"""
        event = ActionEvent(
            kind=ActionKind.AK_ASSIGNMENT.value,
            turn=1,
            player=1,
            armies=5
        )
        self.assertEqual(event.kind, ActionKind.AK_ASSIGNMENT.value)
        self.assertEqual(event.turn, 1)
        self.assertEqual(event.player, 1)
        self.assertEqual(event.armies, 5)
    
    def test_to_list(self):
        """Test converting ActionEvent to list"""
        event = ActionEvent(
            kind=1,
            turn=1,
            player=1,
            opponent=2,
            from_terr=5,
            to_terr=10,
            armies=3
        )
        lst = event.to_list()
        self.assertEqual(len(lst), 14)  # ACTION_FIELD_COUNT
        self.assertEqual(lst[0], 1)  # kind
        self.assertEqual(lst[1], 1)  # turn
        self.assertEqual(lst[2], 1)  # player
    
    def test_from_list(self):
        """Test creating ActionEvent from list"""
        lst = [1, 1, 1, 2, 5, 10, 3, 0, 0, 0, 0, 0, 0, 0]
        event = ActionEvent.from_list(lst)
        self.assertEqual(event.kind, 1)
        self.assertEqual(event.turn, 1)
        self.assertEqual(event.player, 1)
        self.assertEqual(event.opponent, 2)
    
    def test_to_dict(self):
        """Test converting ActionEvent to dict"""
        event = ActionEvent(
            kind=1,
            turn=1,
            player=1
        )
        d = event.to_dict()
        self.assertIn('kind', d)
        self.assertIn('turn', d)
        self.assertIn('player', d)
        self.assertEqual(d['kind'], 1)
    
    def test_from_dict(self):
        """Test creating ActionEvent from dict"""
        d = {
            'kind': 1,
            'turn': 1,
            'player': 1,
            'opponent': 2,
            'from': 5,
            'to': 10,
            'armies': 3
        }
        event = ActionEvent.from_dict(d)
        self.assertEqual(event.kind, 1)
        self.assertEqual(event.turn, 1)
        self.assertEqual(event.player, 1)
        self.assertEqual(event.opponent, 2)


class TestActionHistory(unittest.TestCase):
    """Test action history functions"""
    
    def setUp(self):
        """Reset action history before each test"""
        # Clear any existing state
        action_history.events = []
        action_history.event_count = 0
        action_history.game_id = ""
    
    def test_begin_action_history(self):
        """Test beginning action history"""
        begin_action_history("Test game")
        self.assertTrue(action_history.game_id != "")
        self.assertEqual(action_history.event_count, 0)
        self.assertEqual(action_history.game_metadata, "Test game")
    
    def test_record_action(self):
        """Test recording an action"""
        begin_action_history("Test game")
        event = ActionEvent()
        event.kind = ActionKind.AK_ASSIGNMENT.value
        event.turn = 1
        event.player = 1
        event.armies = 1
        
        record_action(event)
        self.assertEqual(action_count(), 1)
    
    def test_action_count(self):
        """Test action count"""
        begin_action_history("Test game")
        self.assertEqual(action_count(), 0)
        
        event = ActionEvent()
        event.kind = ActionKind.AK_ASSIGNMENT.value
        record_action(event)
        self.assertEqual(action_count(), 1)
        
        event2 = ActionEvent()
        event2.kind = ActionKind.AK_PLACEMENT.value
        record_action(event2)
        self.assertEqual(action_count(), 2)
    
    def test_action_value(self):
        """Test getting action value"""
        begin_action_history("Test game")
        event = ActionEvent()
        event.kind = ActionKind.AK_ASSIGNMENT.value
        event.turn = 5
        event.player = 1
        record_action(event)
        
        # Note: action_value uses 1-indexed fields
        self.assertEqual(action_value(1, 1), ActionKind.AK_ASSIGNMENT.value)  # AF_KIND
        self.assertEqual(action_value(1, 2), 5)  # AF_TURN
        self.assertEqual(action_value(1, 3), 1)  # AF_PLAYER
    
    def test_end_action_history(self):
        """Test ending action history"""
        begin_action_history("Test game")
        end_action_history(10, 1, 0)
        self.assertEqual(action_count(), 1)
        # Last event should be AK_GAME_END
        self.assertEqual(action_value(action_count(), 1), ActionKind.AK_GAME_END.value)
    
    def test_validate_event(self):
        """Test event validation"""
        # Valid event
        event = ActionEvent()
        event.kind = ActionKind.AK_ASSIGNMENT.value
        event.player = 1
        validate_event(event)  # Should not raise
        
        # Invalid: negative value
        event2 = ActionEvent()
        event2.kind = -1
        with self.assertRaises(ValueError):
            validate_event(event2)
        
        # Invalid: kind out of range
        event3 = ActionEvent()
        event3.kind = 99
        with self.assertRaises(ValueError):
            validate_event(event3)
    
    def test_action_kind_enum(self):
        """Test ActionKind enum values"""
        self.assertEqual(ActionKind.AK_ASSIGNMENT.value, 1)
        self.assertEqual(ActionKind.AK_PLACEMENT.value, 2)
        self.assertEqual(ActionKind.AK_ATTACK.value, 3)
        self.assertEqual(ActionKind.AK_OCCUPATION.value, 4)
        self.assertEqual(ActionKind.AK_FORTIFICATION.value, 5)
        self.assertEqual(ActionKind.AK_TURN_START.value, 6)
        self.assertEqual(ActionKind.AK_TURN_END.value, 7)
        self.assertEqual(ActionKind.AK_REINFORCEMENT.value, 8)
        self.assertEqual(ActionKind.AK_CARD_TRADE.value, 9)
        self.assertEqual(ActionKind.AK_ELIMINATION.value, 10)
        self.assertEqual(ActionKind.AK_GAME_END.value, 11)


if __name__ == '__main__':
    unittest.main()
