"""
TurboRisk - Python Port
TRP Scripting Engine

This module provides a Python-based interpreter for TRP (TurboRisk Program) scripts.
Instead of porting the entire PascalScript library, this module provides a simplified
interpreter that can execute TRP scripts by translating them to Python and executing
them in a controlled environment.

Ported from PascalScript/ directory (simplified implementation)
"""

import re
import ast
import sys
import traceback
from typing import Dict, Any, Optional, List, Tuple, Callable
from .globals import G, MAXTERRITORIES, MAXPLAYERS
from .exp_subr import TRP_FUNCTIONS


class TRPError(Exception):
    """Exception raised when a TRP script has an error"""
    def __init__(self, message: str, line: int = 0, procedure: str = ""):
        self.message = message
        self.line = line
        self.procedure = procedure
        super().__init__(f"TRP Error in {procedure} (line {line}): {message}")


class TRPContext:
    """Context for executing a TRP script"""
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.procedures: Dict[str, Callable] = {}
        self.current_procedure: str = ""
        self.current_line: int = 0
        self.player_id: int = 0
        
    def set_variable(self, name: str, value: Any):
        """Set a variable in the context"""
        self.variables[name] = value
        
    def get_variable(self, name: str) -> Any:
        """Get a variable from the context"""
        if name in self.variables:
            return self.variables[name]
        # Try to get from TRP functions
        if name in TRP_FUNCTIONS:
            return TRP_FUNCTIONS[name]
        # Try to get from globals
        if hasattr(G, name):
            return getattr(G, name)
        raise TRPError(f"Variable '{name}' not found", self.current_line, self.current_procedure)
    
    def set_player(self, player_id: int):
        """Set the current player for the context"""
        self.player_id = player_id
        G.i_turn = player_id


class TRPParser:
    """Parser for TRP scripts"""
    
    def __init__(self):
        self.keywords = {
            'procedure', 'var', 'begin', 'end', 'if', 'then', 'else',
            'for', 'to', 'do', 'while', 'repeat', 'until', 'div', 'mod',
            'and', 'or', 'not', 'function', 'program', 'author', 'description'
        }
        self.operators = {'+', '-', '*', '/', '=', '<>', '<', '>', '<=', '>=', ':='}
        
    def extract_metadata(self, script: str) -> Dict[str, str]:
        """Extract metadata from the script header"""
        metadata = {}
        # Match metadata in curly braces at the beginning
        match = re.search(r'\{(.*?)\}', script, re.DOTALL)
        if match:
            meta_text = match.group(1)
            for line in meta_text.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        return metadata
    
    def parse_procedure_declaration(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a procedure declaration"""
        # Match: procedure Name(var Param: Type; Param2: Type);
        pattern = r'procedure\s+(\w+)\s*\((.*?)\)\s*;'
        match = re.match(pattern, line.strip())
        if not match:
            return None
        
        name = match.group(1)
        params_str = match.group(2)
        
        # Parse parameters
        params = []
        if params_str:
            for param in params_str.split(';'):
                param = param.strip()
                if param:
                    # Check for var parameter
                    is_var = False
                    if param.startswith('var '):
                        is_var = True
                        param = param[4:].strip()
                    
                    # Split name and type
                    parts = param.split(':')
                    if len(parts) == 2:
                        param_name = parts[0].strip()
                        param_type = parts[1].strip()
                        params.append({
                            'name': param_name,
                            'type': param_type,
                            'is_var': is_var
                        })
        
        return {
            'name': name,
            'params': params,
            'is_procedure': True
        }
    
    def parse_function_declaration(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a function declaration"""
        # Match: function Name(Param: Type): ReturnType;
        pattern = r'function\s+(\w+)\s*\((.*?)\)\s*:\s*(\w+)\s*;'
        match = re.match(pattern, line.strip())
        if not match:
            return None
        
        name = match.group(1)
        params_str = match.group(2)
        return_type = match.group(3)
        
        # Parse parameters
        params = []
        if params_str:
            for param in params_str.split(';'):
                param = param.strip()
                if param:
                    is_var = False
                    if param.startswith('var '):
                        is_var = True
                        param = param[4:].strip()
                    
                    parts = param.split(':')
                    if len(parts) == 2:
                        param_name = parts[0].strip()
                        param_type = parts[1].strip()
                        params.append({
                            'name': param_name,
                            'type': param_type,
                            'is_var': is_var
                        })
        
        return {
            'name': name,
            'params': params,
            'return_type': return_type,
            'is_function': True
        }
    
    def parse_variable_declaration(self, line: str) -> Optional[List[Dict[str, Any]]]:
        """Parse variable declarations"""
        # Match: var Name, Name2: Type;
        pattern = r'var\s+(.+?)\s*;'
        match = re.match(pattern, line.strip())
        if not match:
            return None
        
        decl = match.group(1)
        # Split by comma, then by colon
        parts = [p.strip() for p in decl.split(',')]
        
        variables = []
        for part in parts:
            if ':' in part:
                names, type_ = part.split(':', 1)
                names = [n.strip() for n in names.split(',')]
                type_ = type_.strip()
                for name in names:
                    variables.append({
                        'name': name,
                        'type': type_
                    })
        
        return variables


class TRPCompiler:
    """Compiler for TRP scripts - translates TRP to Python"""
    
    def __init__(self):
        self.parser = TRPParser()
        self.trp_functions = TRP_FUNCTIONS
        
    def map_type(self, trp_type: str) -> str:
        """Map TRP types to Python types"""
        type_map = {
            'integer': 'int',
            'longint': 'int',
            'int64': 'int',
            'double': 'float',
            'string': 'str',
            'boolean': 'bool',
            'ansistring': 'str'
        }
        return type_map.get(trp_type.lower(), 'Any')
    
    def translate_expression(self, expr: str, context: TRPContext) -> str:
        """Translate a TRP expression to Python"""
        # Replace TRP function calls with Python function calls
        for func_name in self.trp_functions:
            # Match function calls: FuncName(Param1, Param2)
            pattern = rf'\b{func_name}\s*\((.*?)\)'
            expr = re.sub(pattern, lambda m: f'{func_name}({m.group(1)})', expr)
        
        # Replace Pascal operators with Python operators
        expr = expr.replace(':=', '=')
        expr = expr.replace('<>', '!=')
        expr = expr.replace('div', '//')
        expr = expr.replace('mod', '%')
        expr = expr.replace('and', 'and')
        expr = expr.replace('or', 'or')
        expr = expr.replace('not', 'not')
        
        return expr
    
    def translate_statement(self, statement: str, context: TRPContext) -> str:
        """Translate a TRP statement to Python"""
        statement = statement.strip()
        
        # Handle empty statements
        if not statement or statement.startswith('//') or statement.startswith('{') or statement.startswith('}'):
            return ''
        
        # Handle variable declarations
        if statement.startswith('var '):
            return ''  # Handled separately
        
        # Handle if statements
        if_match = re.match(r'if\s+(.+?)\s+then', statement)
        if if_match:
            condition = self.translate_expression(if_match.group(1), context)
            return f'if {condition}:'
        
        # Handle for loops
        for_match = re.match(r'for\s+(\w+)\s*:=\s*(\d+)\s+to\s+(\d+)\s+do', statement)
        if for_match:
            var_name = for_match.group(1)
            start = for_match.group(2)
            end = for_match.group(3)
            return f'for {var_name} in range({start}, {end} + 1):'
        
        # Handle repeat-until loops
        repeat_match = re.match(r'repeat', statement)
        if repeat_match:
            return 'while True:'
        
        until_match = re.match(r'until\s+(.+)', statement)
        if until_match:
            condition = self.translate_expression(until_match.group(1), context)
            return f'if not {condition}: break'
        
        # Handle while loops
        while_match = re.match(r'while\s+(.+?)\s+do', statement)
        if while_match:
            condition = self.translate_expression(while_match.group(1), context)
            return f'while {condition}:'
        
        # Handle begin/end
        if statement == 'begin':
            return ''
        if statement == 'end':
            return ''
        if statement == 'end.':
            return ''
        
        # Handle procedure calls
        # Match: ProcedureName(Param1, Param2);
        proc_match = re.match(r'(\w+)\s*\((.*)\)\s*;', statement)
        if proc_match:
            proc_name = proc_match.group(1)
            params = proc_match.group(2)
            translated_params = self.translate_expression(params, context)
            return f'{proc_name}({translated_params})'
        
        # Handle assignments
        assign_match = re.match(r'(\w+)\s*:=\s*(.+)', statement)
        if assign_match:
            var_name = assign_match.group(1)
            expr = self.translate_expression(assign_match.group(2), context)
            return f'{var_name} = {expr}'
        
        # Handle increment/decrement
        inc_match = re.match(r'inc\s*\((\w+)\)', statement)
        if inc_match:
            var_name = inc_match.group(1)
            return f'{var_name} += 1'
        
        dec_match = re.match(r'dec\s*\((\w+)\)', statement)
        if dec_match:
            var_name = dec_match.group(1)
            return f'{var_name} -= 1'
        
        # Handle break
        if statement == 'break':
            return 'break'
        
        # Handle comments
        if statement.startswith('//'):
            return f'# {statement[2:]}'
        
        # Default: return the statement as-is
        return statement
    
    def compile_procedure(self, name: str, body: str, context: TRPContext) -> str:
        """Compile a single procedure"""
        lines = body.split('\n')
        python_lines = []
        
        for line in lines:
            line = line.strip()
            translated = self.translate_statement(line, context)
            if translated:
                python_lines.append(translated)
        
        return '\n'.join(python_lines)
    
    def compile_script(self, script: str) -> Dict[str, Any]:
        """Compile a TRP script"""
        metadata = self.parser.extract_metadata(script)
        
        # Remove metadata and comments
        script = re.sub(r'\{.*?\}', '', script, flags=re.DOTALL)
        script = re.sub(r'//.*', '', script)
        
        # Split into procedures
        procedures = {}
        current_procedure = None
        current_body = []
        in_procedure = False
        
        for line in script.split('\n'):
            line = line.strip()
            
            # Check for procedure declaration
            proc_decl = self.parser.parse_procedure_declaration(line)
            if proc_decl:
                if current_procedure:
                    procedures[current_procedure['name']] = {
                        'params': current_procedure['params'],
                        'body': '\n'.join(current_body)
                    }
                current_procedure = proc_decl
                current_body = []
                in_procedure = True
                continue
            
            # Check for function declaration
            func_decl = self.parser.parse_function_declaration(line)
            if func_decl:
                if current_procedure:
                    procedures[current_procedure['name']] = {
                        'params': current_procedure['params'],
                        'body': '\n'.join(current_body)
                    }
                current_procedure = func_decl
                current_body = []
                in_procedure = True
                continue
            
            # Check for variable declarations
            var_decl = self.parser.parse_variable_declaration(line)
            if var_decl:
                continue
            
            # Check for begin
            if line == 'begin':
                in_procedure = True
                continue
            
            # Check for end
            if line in ['end', 'end.']:
                if current_procedure:
                    procedures[current_procedure['name']] = {
                        'params': current_procedure.get('params', []),
                        'body': '\n'.join(current_body),
                        'is_function': current_procedure.get('is_function', False),
                        'return_type': current_procedure.get('return_type', None)
                    }
                    current_procedure = None
                    current_body = []
                    in_procedure = False
                continue
            
            # Add to current procedure body
            if in_procedure and current_procedure:
                current_body.append(line)
        
        # Add the last procedure
        if current_procedure:
            procedures[current_procedure['name']] = {
                'params': current_procedure.get('params', []),
                'body': '\n'.join(current_body),
                'is_function': current_procedure.get('is_function', False),
                'return_type': current_procedure.get('return_type', None)
            }
        
        return {
            'metadata': metadata,
            'procedures': procedures
        }


class TRPExec:
    """
    TRP Script Executor
    
    This class provides a Python-based execution environment for TRP scripts.
    It mimics the functionality of the PascalScript TPSExec class.
    """
    
    def __init__(self):
        self.compiler = TRPCompiler()
        self.context = TRPContext()
        self.current_script: Optional[Dict[str, Any]] = None
        self.exception_code: Optional[int] = None
        self.exception_message: str = ""
        
    def create_context(self):
        """Create a new execution context"""
        self.context = TRPContext()
        
    def set_player(self, player_id: int):
        """Set the current player for script execution"""
        self.context.set_player(player_id)
        
    def load_from_file(self, filename: str) -> bool:
        """Load a TRP script from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                script = f.read()
            return self.load_script(script)
        except Exception as e:
            self.exception_code = -1
            self.exception_message = str(e)
            return False
    
    def load_script(self, script: str) -> bool:
        """Load and compile a TRP script"""
        try:
            self.current_script = self.compiler.compile_script(script)
            return True
        except Exception as e:
            self.exception_code = -1
            self.exception_message = str(e)
            return False
    
    def get_procedure(self, name: str) -> Optional[Callable]:
        """Get a compiled procedure by name (case-insensitive)"""
        if not self.current_script:
            return None
        
        # Try exact match first
        if name in self.current_script['procedures']:
            proc_info = self.current_script['procedures'][name]
        else:
            # Try case-insensitive match
            name_upper = name.upper()
            name_lower = name.lower()
            found = None
            for key in self.current_script['procedures'].keys():
                if key.upper() == name_upper or key.lower() == name_lower:
                    found = key
                    break
            
            if not found:
                return None
            proc_info = self.current_script['procedures'][found]
        
        # Create a wrapper function that executes the procedure
        def procedure_wrapper(*args):
            # Set up the context
            self.context.current_procedure = name
            
            # Map parameters to context variables
            params = proc_info.get('params', [])
            for i, param in enumerate(params):
                if i < len(args):
                    # Handle var parameters (output parameters)
                    if param.get('is_var'):
                        # For var parameters, we need to be able to modify them
                        # Store the parameter reference
                        param_name = param['name']
                        # If it's a list (for passing by reference), use the first element
                        if isinstance(args[i], list):
                            self.context.set_variable(param_name, args[i][0])
                        else:
                            self.context.set_variable(param_name, args[i])
                    else:
                        # Regular parameter
                        self.context.set_variable(param['name'], args[i])
            
            # Execute the procedure body
            try:
                # Compile the body to Python code
                body = proc_info['body']
                
                # For now, use a simple execution approach
                # This will be enhanced with proper variable scoping
                if body.strip():
                    # Execute each line
                    for line in body.split('\n'):
                        line = line.strip()
                        if line:
                            translated = self.compiler.translate_statement(line, self.context)
                            if translated:
                                try:
                                    # Use exec with the context
                                    exec(translated, self.context.variables)
                                except Exception as e:
                                    raise TRPError(str(e), 0, name)
                
                # Return output parameters
                output_params = []
                for param in params:
                    if param.get('is_var'):
                        param_name = param['name']
                        if param_name in self.context.variables:
                            output_params.append(self.context.variables[param_name])
                        else:
                            output_params.append(0)
                    else:
                        output_params.append(None)
                
                # Return only the var parameters
                return tuple(output_params)
                
            except TRPError as e:
                self.exception_code = -1
                self.exception_message = str(e)
                raise
            except Exception as e:
                self.exception_code = -1
                self.exception_message = str(e)
                raise TRPError(str(e), 0, name)
        
        return procedure_wrapper
    
    def run_procedure(self, name: str, args: List[Any] = None) -> Optional[Tuple]:
        """Run a procedure by name"""
        if args is None:
            args = []
        
        proc = self.get_procedure(name)
        if proc:
            return proc(*args)
        return None
    
    def register_function(self, func: Callable, name: str):
        """Register a Python function as a TRP function"""
        self.context.variables[name] = func
        
    def register_delphi_function(self, func: Callable, name: str):
        """Register a Delphi-style function (alias for register_function)"""
        self.register_function(func, name)
    
    def cmd_err2(self, error_code: int, message: str):
        """Signal an error (mimics PascalScript CMD_Err2)"""
        self.exception_code = error_code
        self.exception_message = message
        
    @property
    def exception_code(self) -> Optional[int]:
        """Get the current exception code"""
        return self._exception_code
    
    @exception_code.setter
    def exception_code(self, value: Optional[int]):
        self._exception_code = value
    
    @property
    def exception_message(self) -> str:
        """Get the current exception message"""
        return self._exception_message
    
    @exception_message.setter
    def exception_message(self, value: str):
        self._exception_message = value


# Create a global TRP executor instance
ScriptExec = TRPExec()


def setup_trp_runtime():
    """Setup the TRP runtime environment"""
    # Register all TRP functions
    for func_name, func in TRP_FUNCTIONS.items():
        ScriptExec.register_function(func, func_name)
    
    # Also register them in the context
    for func_name, func in TRP_FUNCTIONS.items():
        ScriptExec.context.variables[func_name] = func


# Initialize the TRP runtime
setup_trp_runtime()
