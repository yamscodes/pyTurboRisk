"""
TurboRisk - Python Port
TRP to Python Transpiler

This module provides a transpiler that converts TRP (TurboRisk Program) scripts
to Python code. The transpiled Python code can then be executed directly.

This is a more practical approach than creating a full interpreter, as it
allows us to leverage Python's execution engine while providing the TRP API.
"""

import re
import os
from typing import Dict, List, Optional, Tuple
from .exp_subr import TRP_FUNCTIONS


class TRPTranspiler:
    """Transpiler for TRP scripts to Python"""
    
    def __init__(self):
        pass
    
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
        # Remove // comments
        script = re.sub(r'//.*', '', script)
        # Remove {} comments
        script = re.sub(r'\{.*?\}', '', script, flags=re.DOTALL)
        return script
    
    def parse_procedures(self, script: str) -> List[Dict]:
        """Parse all procedures from the script"""
        procedures = []
        
        # Pattern to match procedure declarations
        # procedure Name(var Param: Type; Param2: Type);
        proc_pattern = r'procedure\s+(\w+)\s*\((.*?)\)\s*;'
        
        # Pattern to match function declarations
        func_pattern = r'function\s+(\w+)\s*\((.*?)\)\s*:\s*(\w+)\s*;'
        
        # Find all procedure declarations
        proc_matches = list(re.finditer(proc_pattern, script, re.IGNORECASE))
        func_matches = list(re.finditer(func_pattern, script, re.IGNORECASE))
        
        # Combine all matches
        all_matches = proc_matches + func_matches
        all_matches.sort(key=lambda m: m.start())
        
        # Extract procedure/function bodies
        for i, match in enumerate(all_matches):
            name = match.group(1)
            params_str = match.group(2)
            is_function = 'function' in match.group(0).lower()
            return_type = match.group(3) if is_function else None
            
            # Find the next match or end of script
            end_pos = all_matches[i + 1].start() if i + 1 < len(all_matches) else len(script)
            
            # Extract the body between the declaration and the next declaration
            body_start = match.end()
            body = script[body_start:end_pos]
            
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
            
            procedures.append({
                'name': name,
                'params': params,
                'body': body,
                'is_function': is_function,
                'return_type': return_type
            })
        
        return procedures
    
    def translate_type(self, trp_type: str) -> str:
        """Translate TRP type to Python type"""
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
    
    def translate_expression(self, expr: str) -> str:
        """Translate a TRP expression to Python"""
        # Replace Pascal operators with Python operators
        for op, py_op in [(':=', '='), ('<>', '!='), ('div', '//'), ('mod', '%')]:
            expr = expr.replace(op, py_op)
        
        # Translate function calls
        def translate_func_call(match):
            func_name = match.group(1)
            args = match.group(2)
            
            # Check if it's a TRP API function
            if func_name in TRP_FUNCTIONS:
                return f'{func_name}({args})'
            
            # Check if it's a built-in Pascal function
            if func_name.lower() in ['abs', 'sqrt', 'sin', 'cos', 'tan', 'random', 'trunc', 'round']:
                return f'{func_name}({args})'
            
            # Otherwise, keep as-is
            return match.group(0)
        
        expr = re.sub(r'\b(\w+)\s*\(([^)]*)\)', translate_func_call, expr)
        
        # Handle boolean operators
        expr = expr.replace(' and ', ' and ')
        expr = expr.replace(' or ', ' or ')
        expr = expr.replace(' not ', ' not ')
        
        return expr
    
    def translate_statement(self, statement: str) -> str:
        """Translate a single TRP statement to Python"""
        statement = statement.strip()
        
        # Skip empty statements
        if not statement:
            return ''
        
        # Handle variable declarations
        if statement.startswith('var '):
            return ''  # Handled separately
        
        # Handle begin/end
        if statement == 'begin':
            return ''
        if statement in ['end', 'end.']:
            return ''
        
        # Handle if statements
        if_match = re.match(r'if\s+(.+?)\s+then', statement)
        if if_match:
            condition = self.translate_expression(if_match.group(1))
            return f'if {condition}:'
        
        # Handle for loops
        for_match = re.match(r'for\s+(\w+)\s*:=\s*(\d+)\s+to\s+(\d+)\s+do', statement)
        if for_match:
            var_name = for_match.group(1)
            start = for_match.group(2)
            end = for_match.group(3)
            return f'for {var_name} in range({start}, {end} + 1):'
        
        # Handle for loops with downto
        for_down_match = re.match(r'for\s+(\w+)\s*:=\s*(\d+)\s+downto\s+(\d+)\s+do', statement)
        if for_down_match:
            var_name = for_down_match.group(1)
            start = for_down_match.group(2)
            end = for_down_match.group(3)
            return f'for {var_name} in range({start}, {end} - 1, -1):'
        
        # Handle while loops
        while_match = re.match(r'while\s+(.+?)\s+do', statement)
        if while_match:
            condition = self.translate_expression(while_match.group(1))
            return f'while {condition}:'
        
        # Handle repeat-until loops
        repeat_match = re.match(r'repeat', statement)
        if repeat_match:
            return 'while True:'
        
        until_match = re.match(r'until\s+(.+)', statement)
        if until_match:
            condition = self.translate_expression(until_match.group(1))
            return f'if not {condition}: break'
        
        # Handle assignments
        assign_match = re.match(r'(\w+)\s*:=\s*(.+)', statement)
        if assign_match:
            var_name = assign_match.group(1)
            expr = self.translate_expression(assign_match.group(2))
            return f'{var_name} = {expr}'
        
        # Handle compound assignments with operators
        op_assign_match = re.match(r'(\w+)\s*([+\-*/])=\s*(.+)', statement)
        if op_assign_match:
            var_name = op_assign_match.group(1)
            op = op_assign_match.group(2)
            expr = op_assign_match.group(3)
            return f'{var_name} {op}= {expr}'
        
        # Handle inc/dec
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
        
        # Handle continue
        if statement == 'continue':
            return 'continue'
        
        # Handle exit
        if statement.startswith('exit'):
            return 'break'
        
        # Handle else
        if statement == 'else':
            return 'else:'
        
        # Handle function calls with semicolon
        func_call_match = re.match(r'(\w+)\s*\((.*)\)\s*;', statement)
        if func_call_match:
            return self.translate_expression(func_call_match.group(0))
        
        # Handle function calls without semicolon
        func_call_match2 = re.match(r'(\w+)\s*\((.*)\)', statement)
        if func_call_match2:
            return self.translate_expression(func_call_match2.group(0))
        
        # Default: return the statement as-is
        return statement
    
    def extract_body(self, body: str) -> List[str]:
        """Extract and translate statements from a procedure body"""
        lines = body.split('\n')
        statements = []
        
        for line in lines:
            line = line.strip()
            translated = self.translate_statement(line)
            if translated:
                statements.append(translated)
        
        return statements
    
    def transpile_procedure(self, proc_info: Dict) -> str:
        """Transpile a single procedure"""
        name = proc_info['name']
        params = proc_info['params']
        body = proc_info['body']
        is_function = proc_info.get('is_function', False)
        
        # Build parameter list
        param_defs = []
        for param in params:
            param_defs.append(param['name'])
        
        # Build the function definition
        if is_function:
            func_def = f'def {name}({', '.join(param_defs)}):'
        else:
            func_def = f'def {name}({', '.join(param_defs)}):'
        
        # Extract and translate the body
        statements = self.extract_body(body)
        
        # Indent the body
        body_code = '\n'.join(f'    {stmt}' for stmt in statements)
        
        return f'{func_def}\n{body_code}'
    
    def transpile(self, script: str) -> str:
        """Transpile a complete TRP script to Python"""
        # Extract metadata
        metadata = self.extract_metadata(script)
        
        # Remove comments
        script = self.remove_comments(script)
        
        # Parse procedures
        procedures = self.parse_procedures(script)
        
        # Generate Python code
        python_code = []
        
        # Add imports
        python_code.append('from turborisk.exp_subr import *')
        python_code.append('from turborisk.globals import G')
        python_code.append('')
        
        # Add metadata as comments
        if metadata:
            python_code.append('# TRP Script Metadata:')
            for key, value in metadata.items():
                python_code.append(f'# {key}: {value}')
            python_code.append('')
        
        # Add procedures
        for proc_info in procedures:
            transpiled = self.transpile_procedure(proc_info)
            python_code.append(transpiled)
            python_code.append('')
        
        return '\n'.join(python_code)


class TRPModule:
    """A module that loads and executes transpiled TRP scripts"""
    
    def __init__(self):
        self.transpiler = TRPTranspiler()
        self.modules = {}
        self.compiled_modules = {}
        
    def load_from_file(self, filename: str) -> bool:
        """Load a TRP script from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                script = f.read()
            return self.load_script(script, filename)
        except Exception as e:
            print(f"Error loading TRP file: {e}")
            return False
    
    def load_script(self, script: str, name: str = None) -> bool:
        """Load and transpile a TRP script"""
        try:
            # Extract metadata to get the program name
            metadata = self.transpiler.extract_metadata(script)
            if name is None:
                name = metadata.get('Program', 'Unknown')
            
            # Transpile to Python
            python_code = self.transpiler.transpile(script)
            
            # Compile the code
            try:
                compiled = compile(python_code, f'<trp_{name}>', 'exec')
            except SyntaxError as e:
                print(f"Syntax error in transpiled code: {e}")
                print(f"Line {e.lineno}: {e.text}")
                return False
            
            # Store the compiled code
            self.compiled_modules[name] = {
                'code': compiled,
                'metadata': metadata,
                'python_code': python_code
            }
            
            return True
        except Exception as e:
            print(f"Error transpiling TRP script: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_module(self, name: str):
        """Get a loaded module"""
        if name in self.compiled_modules:
            return self.compiled_modules[name]
        return None
    
    def execute_procedure(self, module_name: str, procedure_name: str, args: list = None):
        """Execute a procedure from a loaded module"""
        if args is None:
            args = []
        
        module_info = self.get_module(module_name)
        if not module_info:
            print(f"Module '{module_name}' not found")
            return None
        
        # Create a namespace for the module
        namespace = {}
        
        # Execute the compiled code in the namespace
        try:
            exec(module_info['code'], namespace)
        except Exception as e:
            print(f"Error executing module '{module_name}': {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # Get the procedure
        if procedure_name in namespace:
            proc = namespace[procedure_name]
            try:
                return proc(*args)
            except Exception as e:
                print(f"Error executing procedure '{procedure_name}': {e}")
                import traceback
                traceback.print_exc()
                return None
        else:
            print(f"Procedure '{procedure_name}' not found in module '{module_name}'")
            return None


# Create a global TRP module manager
TRPManager = TRPModule()


def load_trp_script(filename: str) -> bool:
    """Load a TRP script from a file"""
    return TRPManager.load_from_file(filename)


def execute_trp_procedure(module_name: str, procedure_name: str, args: list = None):
    """Execute a TRP procedure"""
    return TRPManager.execute_procedure(module_name, procedure_name, args)
