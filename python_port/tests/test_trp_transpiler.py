"""
Tests for the TRP transpiler
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from turborisk.trp_transpiler_v3 import TRPTranspilerV3, TRPModuleManager


class TestTRPTranspiler(unittest.TestCase):
    """Test the TRP transpiler with various TRP scripts"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.transpiler = TRPTranspilerV3()
        self.module_manager = TRPModuleManager()
        
    def test_simple_trp(self):
        """Test transpiling simple.trp"""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'players', 'simple.trp')
        with open(script_path, 'r') as f:
            script = f.read()
        
        # Should not raise an exception
        python_code = self.transpiler.transpile(script)
        self.assertIsInstance(python_code, str)
        self.assertIn('def Assignment', python_code)
        self.assertIn('def Placement', python_code)
        self.assertIn('def Attack', python_code)
        self.assertIn('def Occupation', python_code)
        self.assertIn('def Fortification', python_code)
        
    def test_doomstack_current_trp(self):
        """Test transpiling doomstack-current.trp"""
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Doc', 'Tournament', 'bot-archive', 'doomstack', 'doomstack-current.trp')
        with open(script_path, 'r') as f:
            script = f.read()
        
        # Should not raise an exception
        python_code = self.transpiler.transpile(script)
        self.assertIsInstance(python_code, str)
        self.assertIn('def Defense', python_code)
        self.assertIn('def Assignment', python_code)
        
    def test_actuary_current_trp(self):
        """Test transpiling actuary-current.trp"""
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Doc', 'Tournament', 'bot-archive', 'actuary', 'actuary-current.trp')
        with open(script_path, 'r') as f:
            script = f.read()
        
        # Should not raise an exception
        python_code = self.transpiler.transpile(script)
        self.assertIsInstance(python_code, str)
        self.assertIn('def BuildOdds', python_code)
        self.assertIn('def Win', python_code)
        
    def test_metadata_extraction(self):
        """Test metadata extraction from TRP scripts"""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'players', 'simple.trp')
        with open(script_path, 'r') as f:
            script = f.read()
        
        metadata = self.transpiler.extract_metadata(script)
        self.assertIn('Program', metadata)
        self.assertEqual(metadata['Program'], 'Simple')
        self.assertIn('Author', metadata)
        self.assertEqual(metadata['Author'], 'Mario Ferrari')
        
    def test_comment_removal(self):
        """Test that comments are removed"""
        script = """
        // This is a comment
        procedure Test;
        var
          X: integer;
        begin
          X := 1; // inline comment
        end;
        """
        cleaned = self.transpiler.remove_comments(script)
        self.assertNotIn('// This is a comment', cleaned)
        self.assertNotIn('// inline comment', cleaned)
        
    def test_procedure_parsing(self):
        """Test procedure parsing"""
        script = """
        procedure Test(var X: integer);
        var
          Y: integer;
        begin
          Y := X + 1;
        end;
        """
        procedures = self.transpiler.parse_procedures(script)
        self.assertEqual(len(procedures), 1)
        self.assertEqual(procedures[0]['name'], 'Test')
        self.assertEqual(len(procedures[0]['params']), 1)
        self.assertEqual(procedures[0]['params'][0]['name'], 'X')
        self.assertEqual(procedures[0]['params'][0]['type'], 'int')
        self.assertTrue(procedures[0]['params'][0]['is_var'])
        
    def test_function_parsing(self):
        """Test function parsing"""
        script = """
        function Add(A, B: integer): integer;
        begin
          result := A + B;
        end;
        """
        procedures = self.transpiler.parse_procedures(script)
        self.assertEqual(len(procedures), 1)
        self.assertEqual(procedures[0]['name'], 'Add')
        self.assertTrue(procedures[0]['is_function'])
        self.assertEqual(procedures[0]['return_type'], 'integer')
        self.assertEqual(len(procedures[0]['params']), 2)
        
    def test_expression_translation(self):
        """Test expression translation"""
        tests = [
            ('A := B + C', 'A = B + C'),
            ('A := B + C * D', 'A = B + C * D'),
            ('A := B = C', 'A = B == C'),
            ('A := B <> C', 'A = B != C'),
            ('A := B >= C', 'A = B >= C'),
            ('A := B <= C', 'A = B <= C'),
            ('A := B div C', 'A = B // C'),
            ('A := B mod C', 'A = B % C'),
            ('A := not B', 'A = not B'),
            ('A := B and C', 'A = B and C'),
            ('A := B or C', 'A = B or C'),
        ]
        
        for input_expr, expected in tests:
            result = self.transpiler.translate_expression(input_expr)
            self.assertEqual(result.strip(), expected, f"Failed for: {input_expr}")
            
    def test_if_statement_translation(self):
        """Test if statement translation"""
        tests = [
            ('if A > B then X := 1', 'if A > B: X = 1'),
            ('if A > B then', 'if A > B:'),
        ]
        
        for input_stmt, expected in tests:
            result = self.transpiler.translate_statement(input_stmt)
            self.assertEqual(result.strip(), expected, f"Failed for: {input_stmt}")
            
    def test_for_loop_translation(self):
        """Test for loop translation"""
        tests = [
            ('for I := 1 to 10 do', 'for I in range(1, 10 + 1):'),
            ('for I := 10 downto 1 do', 'for I in range(10, 1 - 1, -1):'),
        ]
        
        for input_stmt, expected in tests:
            result = self.transpiler.translate_statement(input_stmt)
            self.assertEqual(result.strip(), expected, f"Failed for: {input_stmt}")
            
    def test_while_loop_translation(self):
        """Test while loop translation"""
        result = self.transpiler.translate_statement('while A < B do')
        self.assertEqual(result.strip(), 'while A < B:')
        
    def test_repeat_until_translation(self):
        """Test repeat-until loop translation"""
        # Test repeat
        result = self.transpiler.translate_statement('repeat')
        self.assertEqual(result.strip(), 'while True:')
        
        # Test until
        result = self.transpiler.translate_statement('until A > B')
        self.assertEqual(result.strip(), 'if not A > B: break')
        
    def test_module_manager(self):
        """Test the module manager"""
        script_path = os.path.join(os.path.dirname(__file__), '..', 'players', 'simple.trp')
        success, message = self.module_manager.load_from_file(script_path)
        self.assertTrue(success, f"Module manager failed: {message}")
        
    def test_all_players_trp_files(self):
        """Test transpiling all TRP files in the players directory"""
        players_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'players')
        if os.path.exists(players_dir):
            trp_files = [f for f in os.listdir(players_dir) if f.endswith('.trp')]
            
            for trp_file in trp_files:
                with self.subTest(trp_file=trp_file):
                    script_path = os.path.join(players_dir, trp_file)
                    with open(script_path, 'r') as f:
                        script = f.read()
                    
                    # Should not raise an exception
                    python_code = self.transpiler.transpile(script)
                    self.assertIsInstance(python_code, str)
                    self.assertGreater(len(python_code), 0)
        
    def test_bot_archive_trp_files(self):
        """Test transpiling TRP files from bot-archive"""
        bot_archive_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Doc', 'Tournament', 'bot-archive')
        if os.path.exists(bot_archive_dir):
            for root, dirs, files in os.walk(bot_archive_dir):
                for f in files:
                    if f.endswith('.trp'):
                        trp_file = os.path.relpath(os.path.join(root, f), bot_archive_dir)
                        with self.subTest(trp_file=trp_file):
                            script_path = os.path.join(root, f)
                            with open(script_path, 'r') as f:
                                script = f.read()
                            
                            # Should not raise an exception
                            python_code = self.transpiler.transpile(script)
                            self.assertIsInstance(python_code, str)
                            self.assertGreater(len(python_code), 0)
    
    def test_all_players_directory_trp_files(self):
        """Test transpiling all TRP files in python_port/players directory"""
        players_dir = os.path.join(os.path.dirname(__file__), '..', 'players')
        if os.path.exists(players_dir):
            trp_files = [f for f in os.listdir(players_dir) if f.endswith('.trp')]
            
            # Should have at least simple.trp
            self.assertGreaterEqual(len(trp_files), 1)
            
            for trp_file in trp_files:
                with self.subTest(trp_file=trp_file):
                    script_path = os.path.join(players_dir, trp_file)
                    with open(script_path, 'r') as f:
                        script = f.read()
                    
                    # Should not raise an exception
                    python_code = self.transpiler.transpile(script)
                    self.assertIsInstance(python_code, str)
                    self.assertGreater(len(python_code), 0)
                    # Should contain at least one function definition
                    self.assertIn('def ', python_code)


if __name__ == '__main__':
    unittest.main()
