"""
TurboRisk - Python Port
TRP Script Executor using Transpiler v3

This module provides execution of TRP scripts by transpiling them to Python
and executing them in a controlled environment.
"""

import sys
import os
import traceback
from typing import Dict, Any, Optional, List, Tuple, Callable
from .globals import G, MAXTERRITORIES, MAXPLAYERS
from .exp_subr import TRP_FUNCTIONS
from .trp_transpiler_v3 import TRPTranspilerV3


class TRPVar:
    """Wrapper class for TRP var parameters (pass-by-reference)"""
    def __init__(self, value: Any = 0):
        self.value = value
    
    def __repr__(self):
        return f"TRPVar({self.value})"
    
    def __str__(self):
        return str(self.value)
    
    def __int__(self):
        return int(self.value)
    
    def __float__(self):
        return float(self.value)
    
    def __bool__(self):
        return bool(self.value)
    
    def __eq__(self, other):
        if isinstance(other, TRPVar):
            return self.value == other.value
        return self.value == other
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __lt__(self, other):
        if isinstance(other, TRPVar):
            return self.value < other.value
        return self.value < other
    
    def __le__(self, other):
        if isinstance(other, TRPVar):
            return self.value <= other.value
        return self.value <= other
    
    def __gt__(self, other):
        if isinstance(other, TRPVar):
            return self.value > other.value
        return self.value > other
    
    def __ge__(self, other):
        if isinstance(other, TRPVar):
            return self.value >= other.value
        return self.value >= other
    
    def __add__(self, other):
        if isinstance(other, TRPVar):
            return TRPVar(self.value + other.value)
        return TRPVar(self.value + other)
    
    def __sub__(self, other):
        if isinstance(other, TRPVar):
            return TRPVar(self.value - other.value)
        return TRPVar(self.value - other)
    
    def __mul__(self, other):
        if isinstance(other, TRPVar):
            return TRPVar(self.value * other.value)
        return TRPVar(self.value * other)
    
    def __truediv__(self, other):
        if isinstance(other, TRPVar):
            return TRPVar(self.value / other.value)
        return TRPVar(self.value / other)
    
    def __floordiv__(self, other):
        if isinstance(other, TRPVar):
            return TRPVar(self.value // other.value)
        return TRPVar(self.value // other)
    
    def __mod__(self, other):
        if isinstance(other, TRPVar):
            return TRPVar(self.value % other.value)
        return TRPVar(self.value % other)
    
    def __iadd__(self, other):
        if isinstance(other, TRPVar):
            self.value += other.value
        else:
            self.value += other
        return self
    
    def __isub__(self, other):
        if isinstance(other, TRPVar):
            self.value -= other.value
        else:
            self.value -= other
        return self
    
    def __imul__(self, other):
        if isinstance(other, TRPVar):
            self.value *= other.value
        else:
            self.value *= other
        return self


class TRPExecutionError(Exception):
    """Exception raised when a TRP script execution fails"""
    def __init__(self, message: str, procedure: str = "", line: int = 0):
        self.message = message
        self.procedure = procedure
        self.line = line
        super().__init__(f"TRP Execution Error in {procedure} (line {line}): {message}")


class TRPExecutor:
    """
    Executor for TRP scripts that transpiles them to Python and executes them.
    
    This class provides a clean interface for loading and executing TRP scripts,
    handling parameter passing (including var parameters for output), and managing
    the execution context.
    """
    
    def __init__(self):
        self.transpiler = TRPTranspilerV3()
        self.current_script: Optional[str] = None
        self.compiled_code: Optional[Any] = None
        self.namespace: Dict[str, Any] = {}
        self.player_id: int = 0
        self.exception_message: str = ""
        self.loaded_script_name: str = ""
        
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
            
            self.loaded_script_name = name
            
            # Transpile to Python
            python_code = self.transpiler.transpile(script)
            
            # Create the namespace with TRP functions and globals
            self.namespace = {}
            
            # Add all TRP functions
            for func_name, func in TRP_FUNCTIONS.items():
                self.namespace[func_name] = func
            
            # Add globals
            self.namespace['G'] = G
            
            # Add TRPVar class for var parameters
            self.namespace['TRPVar'] = TRPVar
            
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
    
    def get_procedure(self, name: str) -> Optional[Callable]:
        """Get a procedure from the loaded script
        
        Args:
            name: The name of the procedure to get
            
        Returns: A callable that executes the procedure, or None if not found
        """
        if not self.compiled_code:
            return None
        
        # Execute the compiled code to define all procedures in the namespace
        try:
            exec(self.compiled_code, self.namespace)
        except Exception as e:
            self.exception_message = f"Error compiling script: {str(e)}"
            return None
        
        # Check if the procedure exists
        if name not in self.namespace:
            # Try case-insensitive
            name_upper = name.upper()
            found = None
            for key in self.namespace.keys():
                if key.upper() == name_upper:
                    found = key
                    break
            
            if found is None:
                self.exception_message = f"Procedure '{name}' not found"
                return None
            name = found
        
        # Get the procedure
        proc = self.namespace[name]
        
        if not callable(proc):
            self.exception_message = f"'{name}' is not a procedure"
            return None
        
        return proc
    
    def run_procedure(self, name: str, args: List[Any] = None) -> Optional[Tuple]:
        """Run a procedure by name
        
        Args:
            name: The name of the procedure to run
            args: List of arguments to pass to the procedure
            
        Returns: Tuple of output parameter values, or None
        """
        if args is None:
            args = []
        
        proc = self.get_procedure(name)
        if proc is None:
            return None
        
        try:
            # Set the player in the namespace
            self.namespace['PMe'] = self.player_id
            
            # Execute the procedure
            result = proc(*args)
            
            # If the procedure returns values, use them
            if result is not None:
                if isinstance(result, tuple):
                    return result
                else:
                    return (result,)
            
            return None
            
        except Exception as e:
            self.exception_message = str(e)
            return None
    
    def run_procedure_with_var_params(self, name: str, var_params: Dict[str, Any] = None, args: List[Any] = None) -> Tuple[Optional[Dict[str, Any]], bool]:
        """Run a procedure with var parameters (output parameters)
        
        This method handles var parameters specially. Var parameters are passed by reference
        in TRP, so this method wraps them in TRPVar objects and extracts the values after
        execution.
        
        Args:
            name: The name of the procedure to run
            var_params: Dictionary mapping parameter names to initial values
            args: Additional arguments (for non-var parameters)
            
        Returns: Tuple of (output_values, success) where output_values is a dict of var param names to values
        """
        if args is None:
            args = []
        if var_params is None:
            var_params = {}
        
        # Get procedure info to know which parameters are var parameters
        # For now, we'll use a simple approach: assume all var_params are var parameters
        # and wrap them in TRPVar
        
        # Build the argument list
        final_args = []
        for arg in args:
            final_args.append(arg)
        
        # Add var parameters as TRPVar objects
        for param_name, value in var_params.items():
            final_args.append(TRPVar(value))
        
        # Run the procedure
        result = self.run_procedure(name, final_args)
        
        if result is None:
            return None, False
        
        # Extract the values from TRPVar objects
        # The result might contain TRPVar objects or regular values
        output_values = {}
        
        # Check if any of the final_args are TRPVar and were modified
        for i, arg in enumerate(final_args):
            if isinstance(arg, TRPVar):
                # This was a var parameter
                param_name = list(var_params.keys())[i - len(args)]
                output_values[param_name] = arg.value
        
        return output_values, True
    
    def run_procedure_simple(self, name: str, output_param_count: int = 0) -> Optional[Tuple]:
        """Simple method to run a procedure and get output parameters
        
        This method assumes the procedure takes var parameters and returns their values.
        It's useful for procedures like Assignment(ToTerritory) where ToTerritory is an output.
        
        Args:
            name: The name of the procedure to run
            output_param_count: Number of output (var) parameters
            
        Returns: Tuple of output parameter values, or None
        """
        # Create TRPVar objects for output parameters
        output_params = [TRPVar(0) for _ in range(output_param_count)]
        
        # Run the procedure
        result = self.run_procedure(name, output_params)
        
        if result is None:
            return None
        
        # Extract values from TRPVar objects
        output_values = tuple(trp_var.value for trp_var in output_params)
        
        return output_values


# Create a global TRP executor instance
TRPExecutorInstance = TRPExecutor()


# Alias for compatibility with existing code
ScriptExec = TRPExecutorInstance


def setup_trp_executor():
    """Setup the TRP executor with all TRP functions"""
    # The TRP functions are already available through TRP_FUNCTIONS
    # and are automatically included in the namespace when loading scripts
    pass


# Initialize on import
setup_trp_executor()
