"""
End-to-end game flow tests
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from turborisk import setup_territories
from turborisk.globals import G, GameState
from turborisk.territory import claim_territory
from turborisk.game_logic import new_game_setup, supervisor


class TestGameFlow(unittest.TestCase):
    """Test end-to-end game flow"""
    
    def setUp(self):
        """Set up before each test"""
        # Reset global state
        setup_territories()
    
    def test_territory_setup(self):
        """Test that territories are set up correctly"""
        setup_territories()
        
        # Check that all territories are initialized
        for i in range(1, 43):
            self.assertIsNotNone(G.ar_territory[i])
            self.assertTrue(G.ar_territory[i].name != "")
        
        # Check some specific territories
        self.assertEqual(G.ar_territory[1].name, 'Alaska')
        self.assertEqual(G.ar_territory[42].name, 'New Guinea')
    
    def test_claim_territory(self):
        """Test claiming a territory"""
        setup_territories()
        
        # Claim territory 1 for player 1
        claim_territory(1, 1)
        
        # Check that it was claimed
        self.assertEqual(G.ar_territory[1].owner, 1)
        self.assertEqual(G.ar_territory[1].army, 1)
        self.assertEqual(G.ar_player[1].territ, 1)
        self.assertEqual(G.ar_player[1].army, 1)
    
    def test_new_game_setup(self):
        """Test new game setup"""
        setup_territories()
        
        # Set up a simple game with 2 players
        G.ar_player[1].active = True
        G.ar_player[1].computer = False
        G.ar_player[1].name = "Player 1"
        
        G.ar_player[2].active = True
        G.ar_player[2].computer = True
        G.ar_player[2].name = "Player 2"
        
        new_game_setup()
        
        # Check game state
        self.assertEqual(G.game_state, GameState.ASSIGNING)
        self.assertEqual(G.i_turn, 1)
        self.assertEqual(G.i_turn_counter, 1)
        
        # Check that all territories are unowned
        for i in range(1, 43):
            self.assertEqual(G.ar_territory[i].owner, 0)
            self.assertEqual(G.ar_territory[i].army, 0)
    
    def test_supervisor_initial_state(self):
        """Test that supervisor can be called without crashing"""
        setup_territories()
        
        # Set up a simple game
        G.ar_player[1].active = True
        G.ar_player[1].computer = False
        G.ar_player[1].name = "Player 1"
        
        G.ar_player[2].active = True
        G.ar_player[2].computer = True
        G.ar_player[2].name = "Player 2"
        
        new_game_setup()
        
        # Set first player as computer for testing
        G.ar_player[1].computer = True
        G.b_human_turn = False
        G.i_turn = 1  # Make sure we start with player 1
        
        # Set a flag to stop the supervisor after one iteration
        # This prevents the infinite loop in the test
        G.b_stop_asap = True
        
        # Run supervisor - it should exit immediately due to b_stop_asap
        supervisor()
        
        # Check that supervisor exited cleanly
        # b_stop_asap should have been reset
        self.assertFalse(G.b_stop_asap)
        # game_state should be STOPPED after cleanup
        self.assertEqual(G.game_state, GameState.STOPPED)


if __name__ == '__main__':
    unittest.main()
