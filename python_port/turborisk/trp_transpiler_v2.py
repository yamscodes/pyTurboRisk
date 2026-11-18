"""
TurboRisk - Python Port
TRP to Python Transpiler - Version 2

This is an improved version of the TRP transpiler that handles more Pascal syntax
and produces cleaner Python code. It specifically targets the TRP scripts used
in TurboRisk, which use a limited subset of Pascal.
"""

import re
import os
from typing import Dict, List, Optional, Tuple, Any
from .exp_subr import TRP_FUNCTIONS


class TRPTranspilerV2:
    """Improved transpiler for TRP scripts to Python"""
    
    def __init__(self):
        # Type mappings
        self.type_map = {
            'integer': 'int',
            'longint': 'int', 
            'int64': 'int',
            'double': 'float',
            'real': 'float',
            'string': 'str',
            'ansistring': 'str',
            'boolean': 'bool',
            'char': 'str',
            'byte': 'int',
            'word': 'int',
        }
        
        # Operator mappings
        self.operator_map = {
            ':=': '=',
            '<>': '!=',
            'div': '//',
            'mod': '%',
            'and': 'and',
            'or': 'or', 
            'not': 'not',
            'xor': '^',
        }
        
        # Built-in functions that need special handling
        self.builtin_funcs = {
            'abs', 'sqrt', 'sin', 'cos', 'tan', 'random', 'trunc', 'round',
            'frac', 'int', 'odd', 'pred', 'succ', 'chr', 'ord', 'upcase',
            'downcase', 'length', 'pos', 'copy', 'concat', 'delete', 'insert'
        }
    
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
        
        # Pattern to match procedure/function declarations
        decl_pattern = r'(procedure|function)\s+(\w+)\s*\((.*?)\)\s*(?::\s*(\w+))?\s*;'
        
        # Find all declarations
        decl_matches = list(re.finditer(decl_pattern, script, re.IGNORECASE))
        
        # Sort by position
        decl_matches.sort(key=lambda m: m.start())
        
        # Extract procedure bodies
        for i, match in enumerate(decl_matches):
            is_function = match.group(1).lower() == 'function'
            name = match.group(2)
            params_str = match.group(3)
            return_type = match.group(4) if is_function else None
            
            # Find the next declaration or end of script
            next_start = decl_matches[i + 1].start() if i + 1 < len(decl_matches) else len(script)
            
            # Extract the body
            body_start = match.end()
            body = script[body_start:next_start]
            
            # Parse parameters
            params = self.parse_parameters(params_str)
            
            procedures.append({
                'name': name,
                'params': params,
                'body': body,
                'is_function': is_function,
                'return_type': return_type
            })
        
        return procedures
    
    def parse_parameters(self, params_str: str) -> List[Dict]:
        """Parse procedure/function parameters"""
        params = []
        if not params_str:
            return params
        
        for param in params_str.split(';'):
            param = param.strip()
            if not param:
                continue
            
            # Check for var/const/out parameters
            is_var = False
            is_const = False
            if param.startswith('var '):
                is_var = True
                param = param[4:].strip()
            elif param.startswith('const '):
                is_const = True
                param = param[6:].strip()
            
            # Split by colon to get name and type
            parts = param.split(':')
            if len(parts) >= 2:
                # Handle multiple parameter names (e.g., "A, B: integer")
                names = [n.strip() for n in parts[0].split(',')]
                param_type = parts[1].strip()
                
                for name in names:
                    params.append({
                        'name': name,
                        'type': self.type_map.get(param_type.lower(), param_type),
                        'is_var': is_var,
                        'is_const': is_const
                    })
        
        return params
    
    def clean_body(self, body: str) -> List[str]:
        """Clean up the procedure body by removing declarations and structure keywords
        
        Returns: List of cleaned lines with block structure markers
        """
        lines = body.split('\n')
        cleaned_lines = []
        in_var_section = False
        block_depth = 0
        
        # First pass: remove comments, var sections, begin/end, etc.
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip comments
            if line.startswith('//'):
                continue
            
            # Check for var section start
            if line == 'var' or line.startswith('var '):
                in_var_section = True
                continue
            
            # In var section - skip all variable declarations until we hit 'begin'
            if in_var_section:
                if line == 'begin':
                    in_var_section = False
                continue
            
            # Track block depth
            stripped_line = line.rstrip(';').strip()
            if stripped_line == 'begin':
                block_depth += 1
                continue
            if stripped_line in ['end', 'end.']:
                if block_depth > 0:
                    block_depth -= 1
                continue
            
            # Remove inline ' begin' or 'begin ' from statements
            if ' begin ' in line or line.endswith(' begin'):
                line = line.replace(' begin', '').replace('begin ', '')
                line = line.strip()
                if not line:
                    continue
                block_depth += 1  # This statement starts a block
            
            # Skip procedure/function declarations (nested)
            if re.match(r'(procedure|function)\s+\w+', line, re.IGNORECASE):
                continue
            
            # Remove trailing semicolons
            if line.endswith(';'):
                line = line[:-1].strip()
            
            # Remove 'end else' patterns and convert to 'else:'
            if line.lower() == 'end else':
                line = 'else:'
                if block_depth > 0:
                    block_depth -= 1
            elif line.lower().startswith('end else if'):
                # Convert 'end else if' to 'elif'
                line = 'elif ' + line[11:].strip()
                if block_depth > 0:
                    block_depth -= 1
            elif line.lower().startswith('end else'):
                line = 'else: ' + line[9:].strip()
                if block_depth > 0:
                    block_depth -= 1
            
            # Convert standalone 'else if' to 'elif'
            elif line.lower().startswith('else if'):
                line = 'elif ' + line[8:].strip()
            elif line.lower() == 'else':
                line = 'else:'
            
            # Remove inline ' end' or 'end ' from statements
            if ' end ' in line or line.endswith(' end'):
                line = line.replace(' end', '').replace('end ', '')
                line = line.strip()
                if not line:
                    continue
                if block_depth > 0:
                    block_depth -= 1
            
            # Skip variable declarations (lines with type annotations like "T: integer")
            # Check if this looks like a variable declaration (identifier: type)
            if ':' in line:
                # Split on the first colon
                parts = line.split(':', 1)
                if len(parts) == 2:
                    var_part = parts[0].strip()
                    type_part = parts[1].strip().split(';')[0].strip()
                    
                    # Check if the type is a known Pascal type
                    if type_part.lower() in self.type_map:
                        continue
                    # Also check if it's a comma-separated list of variables
                    if all(t.lower() in self.type_map for t in type_part.split(',')):
                        continue
            
            # Clean up the line and add block depth info
            if line:
                # Add block depth marker (for debugging)
                # line = f'[D{block_depth}] {line}'
                cleaned_lines.append((line, block_depth))
        
        # Second pass: join multi-line conditions
        final_lines = []
        i = 0
        while i < len(cleaned_lines):
            line, depth = cleaned_lines[i]
            
            # Check if this line should be joined with the previous line (multi-line condition)
            if final_lines:
                prev_line = final_lines[-1]
                
                # Join if this line starts with a logical operator
                if (line.startswith('and ') or line.startswith('or ') or line.startswith('not ') or
                    line.startswith('= ') or line.startswith('<> ') or line.startswith('>=') or 
                    line.startswith('<=') or line.startswith('> ') or line.startswith('< ')):
                    # Only join if previous line is part of a condition
                    if not (prev_line.endswith('then') or prev_line.endswith('do') or 
                            ':=' in prev_line or prev_line.endswith(':')):
                        final_lines.pop()
                        combined = prev_line + ' ' + line
                        final_lines.append(combined)
                        i += 1
                        continue
                
                # Join if this line starts with '(' and previous line ends with 'or' or 'and'
                if line.startswith('(') and (prev_line.rstrip().endswith('or') or prev_line.rstrip().endswith('and')):
                    final_lines.pop()
                    combined = prev_line + ' ' + line
                    final_lines.append(combined)
                    i += 1
                    continue
                
            
            final_lines.append(line)
            i += 1
        
        return final_lines
    
    def translate_expression(self, expr: str) -> str:
        """Translate a TRP expression to Python"""
        expr = expr.strip()
        
        # Use a temporary marker for assignment to avoid confusion
        # Step 1: Replace := with a temporary marker
        expr = expr.replace(':=', '__ASSIGN__')
        
        # Step 2: Replace = with == (comparison)
        # But we need to be careful not to replace = in >=, <=, <>, ==, etc.
        # We'll use a temporary marker approach for these as well
        expr = expr.replace('>=', '__GE__')
        expr = expr.replace('<=', '__LE__')
        expr = expr.replace('<>', '__NE__')
        expr = expr.replace('=', '==')
        expr = expr.replace('__GE__', '>=')
        expr = expr.replace('__LE__', '<=')
        expr = expr.replace('__NE__', '!=')
        
        # Step 3: Replace the temporary marker with = (assignment)
        expr = expr.replace('__ASSIGN__', '=')
        
        # Replace Pascal operators with Python operators
        for op, py_op in self.operator_map.items():
            if op not in [':=', '=']:  # Skip = and := since we already handled them
                expr = expr.replace(op, py_op)
        
        # Translate function calls
        expr = self.translate_function_calls(expr)
        
        # Handle boolean operators
        expr = expr.replace(' and ', ' and ')
        expr = expr.replace(' or ', ' or ')
        expr = expr.replace(' not ', ' not ')
        
        return expr
    
    def translate_function_calls(self, expr: str) -> str:
        """Translate function calls from TRP to Python"""
        def translate_call(match):
            func_name = match.group(1)
            args = match.group(2)
            
            # Check if it's a TRP API function
            if func_name in TRP_FUNCTIONS:
                return f'{func_name}({args})'
            
            # Check if it's a built-in function
            if func_name.lower() in self.builtin_funcs:
                return f'{func_name}({args})'
            
            # Otherwise, keep as-is
            return match.group(0)
        
        # Match function calls - handle nested parentheses
        def find_matching_paren(s, start):
            depth = 1
            for i in range(start + 1, len(s)):
                if s[i] == '(':
                    depth += 1
                elif s[i] == ')':
                    depth -= 1
                    if depth == 0:
                        return i
            return len(s) - 1
        
        i = 0
        result = []
        while i < len(expr):
            if expr[i] == '(':
                # Find the matching closing parenthesis
                j = find_matching_paren(expr, i)
                result.append(expr[i:j+1])
                i = j + 1
            elif re.match(r'\w', expr[i]):
                # Find the function name
                match = re.match(r'\w+', expr[i:])
                if match:
                    func_name = match.group(0)
                    # Check if it's followed by '('
                    if i + len(func_name) < len(expr) and expr[i + len(func_name)] == '(':
                        # Find the matching ')'
                        j = find_matching_paren(expr, i + len(func_name))
                        args = expr[i + len(func_name) + 1:j]
                        # Translate the function call
                        if func_name in TRP_FUNCTIONS:
                            result.append(f'{func_name}({args})')
                        elif func_name.lower() in self.builtin_funcs:
                            result.append(f'{func_name}({args})')
                        else:
                            result.append(expr[i:j+1])
                        i = j + 1
                    else:
                        result.append(func_name)
                        i += len(func_name)
                else:
                    result.append(expr[i])
                    i += 1
            else:
                result.append(expr[i])
                i += 1
        
        return ''.join(result)
    
    def add_indentation(self, lines: List[str]) -> List[str]:
        """Add proper indentation to translated lines"""
        indented_lines = []
        indent_stack = [1]  # Stack of indent levels, start with 1 (inside function)
        
        for i, line in enumerate(lines):
            if not line:
                continue
            
            line_lower = line.lower().strip()
            
            # Determine if this line starts a new block
            # Check for block-starting statements (end with : but are not else/elif)
            is_block_start = line_lower.endswith(':') and not line_lower.startswith(('else:', 'elif'))
            # Also check for single-line if statements (if ...: body)
            is_single_line_if = line_lower.startswith('if ') and ':' in line_lower and not line_lower.endswith(':')
            is_elif = line_lower.startswith('elif ')
            is_else = line_lower.startswith('else:')
            
            # For elif/else, pop the current indent level and use the parent level
            if is_elif or is_else:
                if len(indent_stack) > 1:
                    indent_stack.pop()
            
            # Get current indent level
            current_indent = indent_stack[-1]
            
            # Add indentation
            indented_line = ' ' * (current_indent * 4) + line
            indented_lines.append(indented_line)
            
            # Check if this is an elif/else with no body (next line is else or end of block)
            if is_elif or is_else:
                # Check if the next line is also an else/elif or end of block
                if i + 1 < len(lines):
                    next_line_lower = lines[i + 1].lower().strip()
                    if next_line_lower.startswith('else:') or next_line_lower.startswith('elif '):
                        # This elif/else has no body, add a pass statement
                        pass_line = ' ' * ((current_indent + 1) * 4) + 'pass'
                        indented_lines.append(pass_line)
            
            # Update indent stack
            if is_block_start or is_single_line_if:
                indent_stack.append(current_indent + 1)
            elif is_elif or is_else:
                # elif/else are at the same level as if, but their body needs indentation
                indent_stack.append(current_indent + 1)
        
        return indented_lines
    
    def translate_statement(self, statement: str, indent: int = 0) -> str:
        """Translate a single TRP statement to Python"""
        statement = statement.strip()
        
        # Skip empty statements
        if not statement:
            return ''
        
        # Handle if-then-else if-then-else statements (single line) - check first
        if_elif_else_match = re.match(r'if\s+(.+?)\s+then\s+(.+?)\s+else\s+if\s+(.+?)\s+then\s+(.+)', statement, re.IGNORECASE)
        if if_elif_else_match:
            condition1 = self.translate_expression(if_elif_else_match.group(1))
            then_part1 = self.translate_expression(if_elif_else_match.group(2))
            condition2 = self.translate_expression(if_elif_else_match.group(3))
            then_part2 = self.translate_expression(if_elif_else_match.group(4))
            return f'{' '* indent}if {condition1}: {then_part1}\n{' '* indent}elif {condition2}: {then_part2}'
        
        # Handle if-then-else statements (single line) - check first
        if_else_single_match = re.match(r'if\s+(.+?)\s+then\s+(.+?)\s+else\s+(.+)', statement, re.IGNORECASE)
        if if_else_single_match:
            condition = self.translate_expression(if_else_single_match.group(1))
            then_part = if_else_single_match.group(2).strip()
            else_part = if_else_single_match.group(3).strip()
            
            # Check if both parts are assignments to the same variable
            then_assign = re.match(r'(\w+)\s*:=\s*(.+)', then_part)
            else_assign = re.match(r'(\w+)\s*:=\s*(.+)', else_part)
            
            if then_assign and else_assign and then_assign.group(1) == else_assign.group(1):
                # Both are assignments to the same variable, use ternary
                var_name = then_assign.group(1)
                then_expr = self.translate_expression(then_assign.group(2))
                else_expr = self.translate_expression(else_assign.group(2))
                return f'{' '* indent}{var_name} = {then_expr} if {condition} else {else_expr}'
            else:
                # Not assignments or different variables, use regular if-else
                then_expr = self.translate_expression(then_part)
                else_expr = self.translate_expression(else_part)
                return f'{' '* indent}{then_expr} if {condition} else {else_expr}'
        
        # Handle if-then statements (with optional then-part)
        # This handles both 'if condition then' and 'if condition then statement'
        if_match = re.match(r'if\s+(.+?)\s+then', statement, re.IGNORECASE)
        if if_match:
            condition = self.translate_expression(if_match.group(1))
            # Check if there's more after 'then'
            remaining = statement[if_match.end():].strip()
            if remaining:
                # Single-line if statement
                then_expr = self.translate_expression(remaining)
                return f'{' '* indent}if {condition}: {then_expr}'
            else:
                # Block if statement
                return f'{' '* indent}if {condition}:'
        
        # Handle elif-then statements (from end else if)
        elif_match = re.match(r'elif\s+(.+?)\s+then', statement, re.IGNORECASE)
        if elif_match:
            condition = self.translate_expression(elif_match.group(1))
            # Check if there's more after 'then'
            remaining = statement[elif_match.end():].strip()
            if remaining:
                # Single-line elif statement
                then_expr = self.translate_expression(remaining)
                return f'{' '* indent}elif {condition}: {then_expr}'
            else:
                # Block elif statement
                return f'{' '* indent}elif {condition}:'
        
        # Handle if-then-else statements (single line)
        if_else_match = re.match(r'if\s+(.+?)\s+then\s+(.+?)\s+else\s+(.+)', statement, re.IGNORECASE)
        if if_else_match:
            condition = self.translate_expression(if_else_match.group(1))
            then_part = self.translate_expression(if_else_match.group(2))
            else_part = self.translate_expression(if_else_match.group(3))
            return f'{' '* indent}if {condition}: {then_part} else: {else_part}'
        
        # Handle for loops
        for_match = re.match(r'for\s+(\w+)\s*:=\s*(\S+)\s+to\s+(\S+)\s+do', statement, re.IGNORECASE)
        if for_match:
            var_name = for_match.group(1)
            start = for_match.group(2)
            end = for_match.group(3)
            return f'{' '* indent}for {var_name} in range({start}, {end} + 1):'
        
        # Handle for loops with downto
        for_down_match = re.match(r'for\s+(\w+)\s*:=\s*(\S+)\s+downto\s+(\S+)\s+do', statement, re.IGNORECASE)
        if for_down_match:
            var_name = for_down_match.group(1)
            start = for_down_match.group(2)
            end = for_down_match.group(3)
            return f'{' '* indent}for {var_name} in range({start}, {end} - 1, -1):'
        
        # Handle while loops
        while_match = re.match(r'while\s+(.+?)\s+do', statement, re.IGNORECASE)
        if while_match:
            condition = self.translate_expression(while_match.group(1))
            return f'{' '* indent}while {condition}:'
        
        # Handle repeat-until loops
        if statement.lower() == 'repeat':
            return f'{' '* indent}while True:'
        
        until_match = re.match(r'until\s+(.+)', statement, re.IGNORECASE)
        if until_match:
            condition = self.translate_expression(until_match.group(1))
            return f'{' '* indent}if not {condition}: break'
        
        # Handle assignments
        assign_match = re.match(r'(\w+)\s*:=\s*(.+)', statement)
        if assign_match:
            var_name = assign_match.group(1)
            expr = self.translate_expression(assign_match.group(2))
            return f'{' '* indent}{var_name} = {expr}'
        
        # Handle compound assignments
        op_assign_match = re.match(r'(\w+)\s*([+\-*/%])=\s*(.+)', statement)
        if op_assign_match:
            var_name = op_assign_match.group(1)
            op = op_assign_match.group(2)
            expr = op_assign_match.group(3)
            return f'{' '* indent}{var_name} {op}= {expr}'
        
        # Handle inc/dec
        inc_match = re.match(r'inc\s*\((\w+)\)', statement, re.IGNORECASE)
        if inc_match:
            var_name = inc_match.group(1)
            return f'{' '* indent}{var_name} += 1'
        
        dec_match = re.match(r'dec\s*\((\w+)\)', statement, re.IGNORECASE)
        if dec_match:
            var_name = dec_match.group(1)
            return f'{' '* indent}{var_name} -= 1'
        
        # Handle break
        if statement.lower() == 'break':
            return f'{' '* indent}break'
        
        # Handle continue
        if statement.lower() == 'continue':
            return f'{' '* indent}continue'
        
        # Handle exit
        if statement.lower().startswith('exit'):
            return f'{' '* indent}break'
        
        # Handle else
        if statement.lower() == 'else':
            return f'{' '* indent}else:'
        
        # Handle function calls
        if '(' in statement and ')' in statement:
            # Try to find a function call
            func_call_pattern = r'(\w+)\s*\(([^)]*)\)'
            match = re.search(func_call_pattern, statement)
            if match:
                func_name = match.group(1)
                args = match.group(2)
                translated_call = self.translate_expression(match.group(0))
                # Replace the function call in the statement
                statement = statement[:match.start()] + translated_call + statement[match.end():]
                return f'{' '* indent}{statement}'
        
        # Default: return the translated expression
        return f'{' '* indent}{self.translate_expression(statement)}'
    
    def transpile_procedure(self, proc_info: Dict) -> str:
        """Transpile a single procedure with proper indentation"""
        name = proc_info['name']
        params = proc_info['params']
        body = proc_info['body']
        is_function = proc_info.get('is_function', False)
        
        # Build parameter list for Python
        param_list = []
        for param in params:
            param_list.append(param['name'])
        
        # Build the function definition
        if is_function:
            func_def = f'def {name}({', '.join(param_list)}):'
        else:
            func_def = f'def {name}({', '.join(param_list)}):'
        
        # Clean the body
        cleaned_lines = self.clean_body(body)
        
        # First, translate all statements without indentation
        translated_lines = []
        for line in cleaned_lines:
            translated = self.translate_statement(line, indent=0)
            if translated:
                translated_lines.append(translated.strip())
        
        # Now add proper indentation
        indented_lines = self.add_indentation(translated_lines)
        
        # Join the lines with proper indentation
        body_code = '\n'.join(indented_lines)
        
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
        
        # Add helper functions
        python_code.append('# Helper functions for TRP compatibility')
        python_code.append('')
        
        # Add procedures
        for proc_info in procedures:
            transpiled = self.transpile_procedure(proc_info)
            python_code.append(transpiled)
            python_code.append('')
        
        return '\n'.join(python_code)


class TRPModuleManager:
    """Manager for loading and executing TRP modules"""
    
    def __init__(self):
        self.transpiler = TRPTranspilerV2()
        self.modules = {}
        self.compiled_code = {}
        
    def load_from_file(self, filename: str) -> Tuple[bool, str]:
        """Load a TRP script from a file
        
        Returns: (success, message)
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                script = f.read()
            return self.load_script(script, filename)
        except Exception as e:
            return False, f"Error loading file: {str(e)}"
    
    def load_script(self, script: str, name: str = None) -> Tuple[bool, str]:
        """Load and transpile a TRP script
        
        Returns: (success, message)
        """
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
                return False, f"Syntax error in transpiled code: {e}\nLine {e.lineno}: {e.text}"
            
            # Store the compiled code
            self.compiled_code[name] = {
                'code': compiled,
                'metadata': metadata,
                'python_code': python_code
            }
            
            return True, f"Successfully transpiled {name}"
        except Exception as e:
            import traceback
            return False, f"Error transpiling TRP script: {e}\n{traceback.format_exc()}"
    
    def get_module(self, name: str) -> Optional[Dict]:
        """Get a loaded module"""
        return self.compiled_code.get(name)
    
    def execute_procedure(self, module_name: str, procedure_name: str, args: List[Any] = None) -> Tuple[bool, Any]:
        """Execute a procedure from a loaded module
        
        Returns: (success, result)
        """
        if args is None:
            args = []
        
        module_info = self.get_module(module_name)
        if not module_info:
            return False, f"Module '{module_name}' not found"
        
        # Create a namespace for the module
        namespace = {}
        
        # Execute the compiled code in the namespace
        try:
            exec(module_info['code'], namespace)
        except Exception as e:
            import traceback
            return False, f"Error executing module '{module_name}': {e}\n{traceback.format_exc()}"
        
        # Get the procedure
        if procedure_name in namespace:
            proc = namespace[procedure_name]
            try:
                result = proc(*args)
                return True, result
            except Exception as e:
                import traceback
                return False, f"Error executing procedure '{procedure_name}': {e}\n{traceback.format_exc()}"
        else:
            return False, f"Procedure '{procedure_name}' not found in module '{module_name}'"
    
    def list_procedures(self, module_name: str) -> List[str]:
        """List all procedures in a module"""
        module_info = self.get_module(module_name)
        if not module_info:
            return []
        
        namespace = {}
        try:
            exec(module_info['code'], namespace)
        except:
            return []
        
        # Filter out built-in functions
        procedures = []
        for name, obj in namespace.items():
            if callable(obj) and not name.startswith('_'):
                procedures.append(name)
        
        return procedures


# Create a global module manager
TRPManager = TRPModuleManager()


def load_trp_script(filename: str) -> Tuple[bool, str]:
    """Load a TRP script from a file
    
    Returns: (success, message)
    """
    return TRPManager.load_from_file(filename)


def execute_trp_procedure(module_name: str, procedure_name: str, args: List[Any] = None) -> Tuple[bool, Any]:
    """Execute a TRP procedure
    
    Returns: (success, result)
    """
    return TRPManager.execute_procedure(module_name, procedure_name, args)


def list_trp_procedures(module_name: str) -> List[str]:
    """List all procedures in a TRP module"""
    return TRPManager.list_procedures(module_name)
