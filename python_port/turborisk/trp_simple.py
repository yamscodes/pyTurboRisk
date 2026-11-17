"""
TurboRisk - Python Port
Simple TRP Script Interpreter

This module provides a simple interpreter for TRP scripts that can handle
the specific syntax used in TurboRisk TRP files. It uses a pragmatic approach
by translating the most common TRP constructs to Python and executing them.
"""

import re
import os
from typing import Dict, List, Optional, Any, Callable
from .exp_subr import TRP_FUNCTIONS
from .globals import G


class TRPSimpleError(Exception):
    """Exception raised when a TRP script has an error"""
    pass


class TRPSimpleContext:
    """Execution context for TRP scripts"""
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.output_params: Dict[str, Any] = {}
        self.player_id: int = 0
        
    def set_variable(self, name: str, value: Any):
        """Set a variable value"""
        self.variables[name] = value
        
    def get_variable(self, name: str) -> Any:
        """Get a variable value"""
        if name in self.variables:
            return self.variables[name]
        # Check output parameters
        if name in self.output_params:
            return self.output_params[name]
        # Check TRP functions
        if name in TRP_FUNCTIONS:
            return TRP_FUNCTIONS[name]
        # Check globals
        if hasattr(G, name):
            return getattr(G, name)
        raise TRPSimpleError(f"Variable '{name}' not found")
    
    def set_player(self, player_id: int):
        """Set the current player"""
        self.player_id = player_id
        G.i_turn = player_id


class TRPSimpleInterpreter:
    """Simple interpreter for TRP scripts"""
    
    def __init__(self):
        self.context = TRPSimpleContext()
        self.lines: List[str] = []
        self.current_line: int = 0
        self.procedure_start: Dict[str, int] = {}
        self.procedure_end: Dict[str, int] = {}
        self.metadata: Dict[str, str] = {}
        
    def load_from_file(self, filename: str) -> bool:
        """Load a TRP script from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                script = f.read()
            return self.load_script(script)
        except Exception as e:
            return False
    
    def load_script(self, script: str) -> bool:
        """Load and parse a TRP script"""
        try:
            # Extract metadata
            self.metadata = self.extract_metadata(script)
            
            # Remove comments
            script = self.remove_comments(script)
            
            # Split into lines
            self.lines = [line.strip() for line in script.split('\n') if line.strip()]
            
            # Find procedure boundaries
            self.find_procedures()
            
            return True
        except Exception as e:
            return False
    
    def extract_metadata(self, script: str) -> Dict[str, str]:
        """Extract metadata from the script header"""
        metadata = {}
        match = re.search(r'\{(.*?)\}', script, re.DOTALL)
        if match:
            meta_text = match.group(1)
            for line in meta_text.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        return metadata
    
    def remove_comments(self, script: str) -> str:
        """Remove all comments from the script"""
        script = re.sub(r'//.*', '', script)
        script = re.sub(r'\{.*?\}', '', script, flags=re.DOTALL)
        return script
    
    def find_procedures(self):
        """Find all procedures in the script"""
        proc_pattern = r'procedure\s+(\w+)\s*\(.*?\)\s*;'
        
        stack = []
        current_proc = None
        
        for i, line in enumerate(self.lines):
            # Check for procedure declaration
            match = re.match(proc_pattern, line, re.IGNORECASE)
            if match:
                current_proc = match.group(1)
                self.procedure_start[current_proc] = i
                stack.append(current_proc)
                continue
            
            # Check for begin
            if line == 'begin':
                continue
            
            # Check for end
            if line in ['end', 'end.']:
                if stack:
                    proc = stack.pop()
                    self.procedure_end[proc] = i
                continue
        
    def get_procedure_lines(self, proc_name: str) -> List[str]:
        """Get the lines for a procedure"""
        start = self.procedure_start.get(proc_name)
        end = self.procedure_end.get(proc_name)
        
        if start is None or end is None:
            return []
        
        return self.lines[start + 1:end]
    
    def execute_procedure(self, proc_name: str, args: List[Any] = None) -> Optional[List[Any]]:
        """Execute a procedure"""
        if args is None:
            args = []
        
        # Get procedure lines
        lines = self.get_procedure_lines(proc_name)
        if not lines:
            return None
        
        # Reset context
        self.context = TRPSimpleContext()
        self.context.player_id = G.i_turn
        
        # Parse parameters from the first line (var declarations)
        param_decls = []
        code_lines = []
        in_var_decl = False
        
        for line in lines:
            if line.startswith('var '):
                in_var_decl = True
                continue
            if in_var_decl:
                if line == 'begin' or ':' in line:
                    if ':' in line:
                        # Parse variable declaration
                        parts = line.split(':')
                        if len(parts) >= 2:
                            var_names = [n.strip() for n in parts[0].split(',')]
                            for var_name in var_names:
                                param_decls.append(var_name)
                    continue
                else:
                    in_var_decl = False
            
            if line in ['begin', 'end', 'end.']:
                continue
            
            code_lines.append(line)
        
        # Set up output parameters (var parameters)
        for i, arg in enumerate(args):
            if i < len(param_decls):
                param_name = param_decls[i]
                # Check if it's an output parameter (var)
                # For now, assume all parameters that are passed by reference are output
                self.context.output_params[param_name] = arg
                self.context.variables[param_name] = arg
        
        # Execute each line
        for line in code_lines:
            self.execute_line(line)
        
        # Return output parameters
        output = []
        for param_name in param_decls:
            if param_name in self.context.variables:
                output.append(self.context.variables[param_name])
            elif param_name in self.context.output_params:
                output.append(self.context.output_params[param_name])
            else:
                output.append(0)
        
        return output
    
    def execute_line(self, line: str):
        """Execute a single line of TRP code"""
        line = line.strip()
        
        # Skip empty lines
        if not line:
            return
        
        # Handle if statements
        if_match = re.match(r'if\s+(.+?)\s+then', line)
        if if_match:
            condition = if_match.group(1)
            if self.evaluate_expression(condition):
                # Execute the next line (the then part)
                pass  # Handled by the caller
            else:
                # Skip to else or end
                pass  # Need to implement this
            return
        
        # Handle for loops
        for_match = re.match(r'for\s+(\w+)\s*:=\s*(\d+)\s+to\s+(\d+)\s+do', line)
        if for_match:
            var_name = for_match.group(1)
            start = int(for_match.group(2))
            end = int(for_match.group(3))
            # Execute the loop
            for i in range(start, end + 1):
                self.context.set_variable(var_name, i)
                # Execute the loop body (next lines until 'end')
                # This requires tracking the loop body
            return
        
        # Handle repeat-until loops
        repeat_match = re.match(r'repeat', line)
        if repeat_match:
            # Start a repeat-until loop
            # This requires tracking the loop
            return
        
        until_match = re.match(r'until\s+(.+)', line)
        if until_match:
            condition = until_match.group(1)
            if not self.evaluate_expression(condition):
                # Continue the loop
                pass
            return
        
        # Handle assignments
        assign_match = re.match(r'(\w+)\s*:=\s*(.+)', line)
        if assign_match:
            var_name = assign_match.group(1)
            expr = assign_match.group(2)
            value = self.evaluate_expression(expr)
            self.context.set_variable(var_name, value)
            # If it's an output parameter, update it
            if var_name in self.context.output_params:
                self.context.output_params[var_name] = value
            return
        
        # Handle inc/dec
        inc_match = re.match(r'inc\s*\((\w+)\)', line)
        if inc_match:
            var_name = inc_match.group(1)
            value = self.context.get_variable(var_name)
            self.context.set_variable(var_name, value + 1)
            if var_name in self.context.output_params:
                self.context.output_params[var_name] = value + 1
            return
        
        dec_match = re.match(r'dec\s*\((\w+)\)', line)
        if dec_match:
            var_name = dec_match.group(1)
            value = self.context.get_variable(var_name)
            self.context.set_variable(var_name, value - 1)
            if var_name in self.context.output_params:
                self.context.output_params[var_name] = value - 1
            return
        
        # Handle break
        if line == 'break':
            raise TRPSimpleError("break not supported in simple interpreter")
        
        # Handle function calls (procedure calls)
        func_call_match = re.match(r'(\w+)\s*\((.*)\)', line)
        if func_call_match:
            func_name = func_call_match.group(1)
            args_str = func_call_match.group(2)
            
            # Parse arguments
            args = []
            if args_str:
                for arg in args_str.split(','):
                    arg = arg.strip()
                    if arg:
                        args.append(self.evaluate_expression(arg))
            
            # Execute the function
            if func_name in TRP_FUNCTIONS:
                result = TRP_FUNCTIONS[func_name](*args)
                # If it's a function that returns a value, we might need to handle it
                # For now, just execute it
            else:
                # It might be a user-defined procedure
                pass
            return
        
        # Handle else
        if line == 'else':
            return
        
        # Handle compound statements with semicolon
        if line.endswith(';'):
            line = line[:-1].strip()
            self.execute_line(line)
            return
        
        # Default: try to evaluate as an expression
        try:
            value = self.evaluate_expression(line)
            # If it's a standalone expression, we might need to do something with it
        except:
            pass
    
    def evaluate_expression(self, expr: str) -> Any:
        """Evaluate a TRP expression"""
        expr = expr.strip()
        
        # Handle simple variables
        if re.match(r'^\w+$', expr):
            return self.context.get_variable(expr)
        
        # Handle numeric literals
        if re.match(r'^-?\d+$', expr):
            return int(expr)
        
        # Handle floating point literals
        if re.match(r'^-?\d+\.\d+$', expr):
            return float(expr)
        
        # Handle boolean literals
        if expr.lower() == 'true':
            return True
        if expr.lower() == 'false':
            return False
        
        # Handle arithmetic expressions
        # Try to parse as a simple arithmetic expression
        try:
            # Replace Pascal operators with Python operators
            expr = expr.replace('<>', '!=')
            expr = expr.replace('div', '//')
            expr = expr.replace('mod', '%')
            expr = expr.replace('and', ' and ')
            expr = expr.replace('or', ' or ')
            expr = expr.replace('not', ' not ')
            
            # Replace variable names with their values
            for var_name in self.context.variables:
                # Use regex to replace whole words only
                expr = re.sub(r'\b' + var_name + r'\b', str(self.context.variables[var_name]), expr)
            
            # Evaluate the expression
            return eval(expr, {"__builtins__": {}}, {
                'abs': abs,
                'min': min,
                'max': max,
                'round': round
            })
        except:
            # If eval fails, try to handle function calls
            func_call_match = re.match(r'(\w+)\s*\((.*)\)', expr)
            if func_call_match:
                func_name = func_call_match.group(1)
                args_str = func_call_match.group(2)
                
                # Parse arguments
                args = []
                if args_str:
                    for arg in args_str.split(','):
                        arg = arg.strip()
                        if arg:
                            args.append(self.evaluate_expression(arg))
                
                # Execute the function
                if func_name in TRP_FUNCTIONS:
                    return TRP_FUNCTIONS[func_name](*args)
            
            # If all else fails, return the expression as-is
            return expr


# Create a global interpreter instance
TRPInterpreter = TRPSimpleInterpreter()


def load_trp_file(filename: str) -> bool:
    """Load a TRP file"""
    return TRPInterpreter.load_from_file(filename)


def execute_trp_procedure(proc_name: str, args: List[Any] = None) -> Optional[List[Any]]:
    """Execute a TRP procedure"""
    return TRPInterpreter.execute_procedure(proc_name, args)
