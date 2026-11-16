"""
Basic tests for the TurboRisk Python port
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from turborisk.globals import G, VERSION, MAXTERRITORIES, MAXPLAYERS, GameState, ContinentID
from turborisk.territory import setup_territories, is_adjacent
from turborisk.exp_subr import t_name, t_owner, t_armies, p_me, p_name


class TestGlobals(unittest.TestCase):
    """Test the globals module"""
    
    def test_version(self):
        """Test that version is correct"""
        self.assertEqual(VERSION, '2.1.2')
    
    def test_constants(self):
        """Test that constants are defined"""
        self.assertEqual(MAXTERRITORIES, 42)
        self.assertEqual(MAXPLAYERS, 10)
    
    def test_global_state(self):
        """Test that global state is initialized"""
        self.assertIsInstance(G, object)
        self.assertEqual(G.game_state, GameState.STOPPED)


class TestTerritory(unittest.TestCase):
    """Test the territory module"""
    
    def test_territory_names(self):
        """Test that territories are set up correctly"""
        self.assertEqual(t_name(1), 'Alaska')
        self.assertEqual(t_name(2), 'Northwest Territory')
        self.assertEqual(t_name(42), 'New Guinea')
    
    def test_territory_owners(self):
        """Test that territory owners are initially 0"""
        self.assertEqual(t_owner(1), 0)
        self.assertEqual(t_owner(2), 0)
    
    def test_adjacency(self):
        """Test that adjacency is correct"""
        # Alaska (1) should be adjacent to Northwest Territory (2)
        self.assertTrue(is_adjacent(1, 2))
        # Alaska (1) should be adjacent to Koryak (37)
        self.assertTrue(is_adjacent(1, 37))
        # Alaska (1) should NOT be adjacent to Brazil (12)
        self.assertFalse(is_adjacent(1, 12))


class TestExpSubr(unittest.TestCase):
    """Test the external subroutines"""
    
    def test_t_name(self):
        """Test TName function"""
        self.assertEqual(t_name(1), 'Alaska')
        self.assertEqual(t_name(999), '?')
    
    def test_t_owner(self):
        """Test TOwner function"""
        self.assertEqual(t_owner(1), 0)
        self.assertEqual(t_owner(999), -1)
    
    def test_t_armies(self):
        """Test TArmies function"""
        self.assertEqual(t_armies(1), 0)
        self.assertEqual(t_armies(999), -1)


if __name__ == '__main__':
    unittest.main()
