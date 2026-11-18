"""
TurboRisk - Python Port
TRP Runtime Environment

This module provides a simple runtime environment for executing TRP scripts.
It uses the transpiler to convert TRP scripts to Python and executes them.
"""

import sys
import os
import traceback
from typing import Dict, Any, Optional, List, Tuple, Callable
from .globals import G
from .exp_subr import TRP_FUNCTIONS
from .trp_transpiler_v3 import TRPTranspilerV3


class TRPRuntime:
    """
    Runtime environment for TRP scripts.
    
    This class provides a simple interface for loading and executing TRP scripts.
    It handles the transpilation, compilation, and execution of TRP code.
    """
    
    def __init__(self):
        self.transpiler = TRPTranspilerV3()
        self.current_script: Optional[str] = None
        self.compiled_code: Optional[Any] = None
        self.namespace: Dict[str, Any] = {}
        self.player_id: int = 0
        self.exception_message: str = ""
        self.script_name: str = ""
        
    def create_context(self):
        """Create a new execution context"""
        self.namespace = {}
        self.exception_message = ""
        
    def set_player(self, player_id: int):
        """Set the current player for script execution"""
        self.player_id = player_id
        if hasattr(G, 'i_turn'):
            G.i_turn = player_id
        
    def load_from_file(self, filename: str) -> bool:
        """Load a TRP script from a file
        
        Returns: True if successful, False otherwise
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                script = f.read()
            return self.load_script(script, filename)
        except Exception as e:
            self.exception_message = f"Error loading file: {str(e)}"
            return False
    
    def load_script(self, script: str, name: str = None) -> bool:
        """Load and transpile a TRP script
        
        Args:
            script: The TRP script source code
            name: Optional name for the script
            
        Returns: True if successful, False otherwise
        """
        try:
            self.current_script = script
            
            # Extract metadata to get the program name
            metadata = self.transpiler.extract_metadata(script)
            if name is None:
                name = metadata.get('Program', 'Unknown')
            
            self.script_name = name
            
            # Transpile to Python
            python_code = self.transpiler.transpile(script)
            
            # Create the namespace with TRP functions and globals
            self.namespace = {}
            
            # Add all TRP functions
            for func_name, func in TRP_FUNCTIONS.items():
                self.namespace[func_name] = func
            
            # Add globals
            self.namespace['G'] = G
            
            # Compile the code
            try:
                self.compiled_code = compile(python_code, f'<trp_{name}>', 'exec')
            except SyntaxError as e:
                self.exception_message = f"Syntax error in transpiled code: {e}\nLine {e.lineno}: {e.text}"
                return False
            
            return True
            
        except Exception as e:
            self.exception_message = f"Error transpiling script: {str(e)}\n{traceback.format_exc()}"
            return False
    
    def run_procedure(self, name: str, args: List[Any] = None) -> Optional[Tuple]:
        """Run a procedure by name
        
        This method handles var parameters by wrapping them in lists.
        The transpiled code uses list indexing (param[0]) to access var parameters.
        After execution, the values are extracted from the lists.
        
        Args:
            name: The name of the procedure to run
            args: List of arguments to pass to the procedure
            
        Returns: Tuple of output parameter values, or None
        """
        if args is None:
            args = []
        
        if not self.compiled_code:
            self.exception_message = "No script loaded"
            return None
        
        try:
            # Create a new namespace for this execution
            exec_namespace = self.namespace.copy()
            
            # Execute the compiled code to define all procedures
            exec(self.compiled_code, exec_namespace)
            
            # Check if the procedure exists
            if name not in exec_namespace:
                # Try case-insensitive
                name_upper = name.upper()
                found = None
                for key in exec_namespace.keys():
                    if key.upper() == name_upper:
                        found = key
                        break
                
                if found is None:
                    self.exception_message = f"Procedure '{name}' not found"
                    return None
                name = found
            
            # Get the procedure
            proc = exec_namespace[name]
            
            if not callable(proc):
                self.exception_message = f"'{name}' is not a procedure"
                return None
            
            # Set the player in the namespace
            exec_namespace['PMe'] = self.player_id
            
            # For var parameters, wrap each argument in a list
            # The transpiled code uses param[0] to access the value
            wrapped_args = [[arg] for arg in args]
            
            # Execute the procedure
            result = proc(*wrapped_args)
            
            # Extract the values from the lists
            output_values = tuple(arg[0] for arg in wrapped_args)
            
            # If the procedure returns values, use them
            if result is not None:
                if isinstance(result, tuple):
                    return result + output_values
                else:
                    return (result,) + output_values
            
            # Return the output parameter values
            return output_values
            
        except Exception as e:
            self.exception_message = str(e)
            return None
    
    def run_procedure_with_output(self, name: str, output_param_count: int = 0) -> Optional[Tuple]:
        """Run a procedure and get output parameters
        
        This method is specifically designed for procedures with var parameters.
        It uses a dictionary to pass the parameters and extracts the values after execution.
        
        Args:
            name: The name of the procedure to run
            output_param_count: Number of output (var) parameters
            
        Returns: Tuple of output parameter values, or None
        """
        if not self.compiled_code:
            self.exception_message = "No script loaded"
            return None
        
        try:
            # Create a new namespace for this execution
            exec_namespace = self.namespace.copy()
            
            # Execute the compiled code to define all procedures
            exec(self.compiled_code, exec_namespace)
            
            # Check if the procedure exists
            if name not in exec_namespace:
                # Try case-insensitive
                name_upper = name.upper()
                found = None
                for key in exec_namespace.keys():
                    if key.upper() == name_upper:
                        found = key
                        break
                
                if found is None:
                    self.exception_message = f"Procedure '{name}' not found"
                    return None
                name = found
            
            # Get the procedure
            proc = exec_namespace[name]
            
            if not callable(proc):
                self.exception_message = f"'{name}' is not a procedure"
                return None
            
            # Set the player in the namespace
            exec_namespace['PMe'] = self.player_id
            
            # Create output parameters as lists (mutable)
            output_params = [[0] for _ in range(output_param_count)]
            
            # Execute the procedure
            # The procedure will modify the lists in place
            proc(*output_params)
            
            # Extract the values
            result = tuple(param[0] for param in output_params)
            
            return result
            
        except Exception as e:
            self.exception_message = str(e)
            return None


# Create a global TRP runtime instance
TRPRuntimeInstance = TRPRuntime()


# Alias for compatibility with existing code
ScriptExec = TRPRuntimeInstance


def setup_trp_runtime():
    """Setup the TRP runtime with all TRP functions"""
    # The TRP functions are already available through TRP_FUNCTIONS
    # and are automatically included in the namespace when loading scripts
    pass


# Initialize on import
setup_trp_runtime()
