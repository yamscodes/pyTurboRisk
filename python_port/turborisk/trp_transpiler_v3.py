"""
TurboRisk - Python Port
TRP to Python Transpiler - Version 3

This is an improved version that properly handles procedure boundaries and
complex Pascal syntax in TRP scripts.
"""

import re
import os
from typing import Dict, List, Optional, Tuple, Any
from .exp_subr import TRP_FUNCTIONS


class TRPTranspilerV3:
    """Improved transpiler for TRP scripts to Python with proper block parsing"""
    
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
    
    def find_matching_end(self, script: str, start_pos: int) -> int:
        """Find the matching 'end' for a procedure/function body starting at start_pos
        
        In Pascal, procedures/functions end with 'end;' (or just 'end' at the end of the file).
        The body may contain nested begin/end blocks.
        
        Returns the position right after the matching 'end' or 'end;' statement.
        """
        depth = 0
        i = start_pos
        
        while i < len(script):
            # Skip whitespace
            while i < len(script) and script[i] in [' ', '\t', '\n', '\r']:
                i += 1
            
            if i >= len(script):
                return len(script)
            
            # Check for 'begin' - this increases depth
            if i + 4 < len(script) and script[i:i+5].lower() == 'begin':
                # Check it's a standalone word
                next_char = script[i+5] if i+5 < len(script) else ''
                if (not next_char.isalnum() or next_char == '_'):
                    depth += 1
                    i += 5
                    continue
            
            # Check for 'end' - this decreases depth or returns if at depth 1
            if i + 2 < len(script) and script[i:i+3].lower() == 'end':
                # Check it's a standalone word
                next_char = script[i+3] if i+3 < len(script) else ''
                if (not next_char.isalnum() or next_char == '_'):
                    if depth == 0:
                        # Found the matching end for the procedure/function (no begin was found)
                        # Skip past the 'end' and any semicolon
                        j = i + 3
                        if j < len(script) and script[j] == ';':
                            j += 1
                        return j
                    elif depth == 1:
                        # Found the matching end for the outermost begin
                        # Skip past the 'end' and any semicolon
                        j = i + 3
                        if j < len(script) and script[j] == ';':
                            j += 1
                        return j
                    else:
                        # Nested end, decrease depth
                        depth -= 1
                        i += 3
                        continue
            
            # Check for nested procedure/function declarations
            if i + 8 < len(script) and script[i:i+9].lower() == 'procedure':
                # Found a nested procedure - skip it entirely
                j = i + 9
                # Find the end of the declaration (look for ';')
                while j < len(script) and script[j] != ';':
                    j += 1
                if j < len(script):
                    j += 1  # Skip the semicolon
                # Recursively find the matching end for this nested procedure
                end_pos = self.find_matching_end(script, j)
                if end_pos > i:
                    i = end_pos
                    continue
            
            if i + 7 < len(script) and script[i:i+8].lower() == 'function':
                # Found a nested function - skip it entirely
                j = i + 8
                # Find the end of the declaration (look for ';')
                while j < len(script) and script[j] != ';':
                    j += 1
                if j < len(script):
                    j += 1  # Skip the semicolon
                # Recursively find the matching end for this nested function
                end_pos = self.find_matching_end(script, j)
                if end_pos > i:
                    i = end_pos
                    continue
            
            # Move to next character
            i += 1
        
        return len(script)
    
    def parse_procedures(self, script: str) -> List[Dict]:
        """Parse all procedures from the script with proper body extraction"""
        procedures = []
        
        # Pattern to match procedure/function declarations
        decl_pattern = r'(procedure|function)\s+(\w+)\s*(?:\((.*?)\))?\s*(?::\s*(\w+))?\s*;'
        
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
            
            # Find the matching end for this procedure
            body_start = match.end()
            body_end = self.find_matching_end(script, body_start)
            
            # Extract the body
            body = script[body_start:body_end]
            
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
        
        Returns: List of cleaned lines
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
            
            # Check for var section start (case-insensitive)
            if line.lower() == 'var' or line.lower().startswith('var '):
                in_var_section = True
                continue
            
            # In var section - skip all variable declarations until we hit 'begin'
            if in_var_section:
                if line.lower() == 'begin':
                    in_var_section = False
                continue
            
            # Track block depth
            stripped_line = line.rstrip(';').strip()
            if stripped_line.lower() == 'begin':
                block_depth += 1
                continue
            if stripped_line.lower() in ['end', 'end.']:
                if block_depth > 0:
                    block_depth -= 1
                continue
            
            # Remove inline ' begin' or 'begin ' from statements
            line_lower = line.lower()
            if ' begin ' in line_lower or line_lower.endswith(' begin'):
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
            elif line_lower.startswith('end else if'):
                # Convert 'end else if' to 'elif'
                line = 'elif ' + line[11:].strip()
                if block_depth > 0:
                    block_depth -= 1
            elif line_lower.startswith('end else'):
                line = 'else: ' + line[9:].strip()
                if block_depth > 0:
                    block_depth -= 1
            
            # Convert standalone 'else if' to 'elif'
            elif line_lower.startswith('else if'):
                line = 'elif ' + line[8:].strip()
            elif line_lower.startswith('else '):
                # Convert 'else statement' to 'else:' on one line
                # The statement will be on the next line
                line = 'else:'
            elif line.lower() == 'else':
                line = 'else:'
            
            # Remove inline ' end' or 'end ' from statements
            if ' end ' in line_lower or line_lower.endswith(' end'):
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
            
            # Clean up the line
            if line:
                cleaned_lines.append(line)
        
        # Second pass: join multi-line conditions and split complex single-line statements
        final_lines = []
        i = 0
        while i < len(cleaned_lines):
            line = cleaned_lines[i]
            
            # Check if this line should be joined with the previous line (multi-line condition)
            if final_lines:
                prev_line = final_lines[-1]
                line_lower = line.lower()
                prev_lower = prev_line.lower()
                
                # Join if this line starts with a logical operator
                if (line_lower.startswith('and ') or line_lower.startswith('or ') or line_lower.startswith('not ') or
                    line_lower.startswith('= ') or line_lower.startswith('<> ') or line_lower.startswith('>=') or 
                    line_lower.startswith('<=') or line_lower.startswith('> ') or line_lower.startswith('< ')):
                    # Only join if previous line is part of a condition
                    if not (prev_lower.endswith('then') or prev_lower.endswith('do') or 
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
            
            # Split complex single-line statements with nested control structures
            # This is done recursively - if a line contains control structures, split them
            def split_complex_line(line_str, indent_level=0):
                """Recursively split lines with nested control structures"""
                lines = []
                
                # Check for if ... then ... else ... (must be checked first!)
                if_else_match = re.match(r'^(if\s+.+?\s+then\s+.+?\s+else\s+.+)$', line_str, re.IGNORECASE)
                if if_else_match:
                    # Don't split if-then-else, let translate_statement handle it
                    return [line_str]
                
                # Check for if ... then for ... do
                if_match_for = re.match(r'^(if\s+.+?\s+then\s+for\s+.+?\s+do\s+.+)$', line_str, re.IGNORECASE)
                if if_match_for:
                    if_part = line_str[:line_str.lower().find(' then ')] + ':'
                    for_part = line_str[line_str.lower().find(' then ') + 6:]
                    lines.append(if_part)
                    lines.extend(split_complex_line(for_part, indent_level + 1))
                    return lines
                
                # Check for if ... then while ... do
                if_match_while = re.match(r'^(if\s+.+?\s+then\s+while\s+.+?\s+do\s+.+)$', line_str, re.IGNORECASE)
                if if_match_while:
                    if_part = line_str[:line_str.lower().find(' then ')] + ':'
                    while_part = line_str[line_str.lower().find(' then ') + 6:]
                    lines.append(if_part)
                    lines.extend(split_complex_line(while_part, indent_level + 1))
                    return lines
                
                # Check for for ... do if ... then (with or without body after then)
                for_match_if = re.match(r'^(for\s+.+?\s+do\s+if\s+.+?\s+then.*)$', line_str, re.IGNORECASE)
                if for_match_if:
                    for_part = line_str[:line_str.lower().find(' do ')] + ':'
                    if_part = line_str[line_str.lower().find(' do ') + 4:]
                    lines.append(for_part)
                    lines.extend(split_complex_line(if_part, indent_level + 1))
                    return lines
                
                # Check for for ... do while ... do
                for_match_while = re.match(r'^(for\s+.+?\s+do\s+while\s+.+?\s+do\s+.+)$', line_str, re.IGNORECASE)
                if for_match_while:
                    for_part = line_str[:line_str.lower().find(' do ')] + ':'
                    while_part = line_str[line_str.lower().find(' do ') + 4:]
                    lines.append(for_part)
                    lines.extend(split_complex_line(while_part, indent_level + 1))
                    return lines
                
                # Check for if ... then (with something after then, but not containing else)
                # Only split if there's no 'else' in the line
                if ' else ' not in line_str.lower() and ' else' not in line_str.lower():
                    if_match = re.match(r'^(if\s+.+?\s+then\s+.+)$', line_str, re.IGNORECASE)
                    if if_match:
                        if_part = line_str[:line_str.lower().find(' then ')] + ':'
                        then_part = line_str[line_str.lower().find(' then ') + 6:]
                        lines.append(if_part)
                        lines.extend(split_complex_line(then_part, indent_level + 1))
                        return lines
                
                # Check for for ... do (with something after do, but not containing else)
                if ' else ' not in line_str.lower() and ' else' not in line_str.lower():
                    for_match = re.match(r'^(for\s+.+?\s+do\s+.+)$', line_str, re.IGNORECASE)
                    if for_match:
                        for_part = line_str[:line_str.lower().find(' do ')] + ':'
                        do_part = line_str[line_str.lower().find(' do ') + 4:]
                        lines.append(for_part)
                        lines.extend(split_complex_line(do_part, indent_level + 1))
                        return lines
                
                # Check for while ... do (with something after do)
                while_match = re.match(r'^(while\s+.+?\s+do\s+.+)$', line_str, re.IGNORECASE)
                if while_match:
                    while_part = line_str[:line_str.lower().find(' do ')] + ':'
                    do_part = line_str[line_str.lower().find(' do ') + 4:]
                    lines.append(while_part)
                    lines.extend(split_complex_line(do_part, indent_level + 1))
                    return lines
                
                # Base case: no more splitting needed
                return [line_str]
            
            # Use the recursive splitter
            split_lines = split_complex_line(line)
            final_lines.extend(split_lines)
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
        
        # Replace Pascal operators with Python operators (case-insensitive)
        for op, py_op in self.operator_map.items():
            if op not in [':=', '=']:  # Skip = and := since we already handled them
                # Use case-insensitive replacement for operators
                import re
                expr = re.sub(re.escape(op), py_op, expr, flags=re.IGNORECASE)
        
        # Translate function calls
        expr = self.translate_function_calls(expr)
        
        return expr
    
    def translate_function_calls(self, expr: str) -> str:
        """Translate function calls from TRP to Python"""
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
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            # Determine if this line starts a new block
            # Check for block-starting statements (end with : but are not else/elif)
            is_block_start = line_stripped.endswith(':') and not line_lower.startswith(('else:', 'elif'))
            # Check for single-line if statements (if ...: body) - these don't create a new block
            is_single_line_if = line_lower.startswith('if ') and ':' in line_stripped and not line_stripped.endswith(':')
            # Check for single-line elif statements (elif ...: body) - these don't create a new block
            is_single_line_elif = line_lower.startswith('elif ') and ':' in line_stripped and not line_stripped.endswith(':')
            is_elif = line_lower.startswith('elif ')
            is_else = line_lower.startswith('else:')
            
            # For elif/else, pop the current indent level and use the parent level
            # This applies to all elif/else statements, whether block-starting or single-line
            if is_elif or is_else:
                if len(indent_stack) > 1:
                    indent_stack.pop()
            
            # Get current indent level
            current_indent = indent_stack[-1]
            
            # Add indentation
            indented_line = ' ' * (current_indent * 4) + line_stripped
            indented_lines.append(indented_line)
            
            # Check if this is an elif/else with no body (next line is also an else/elif or end of block)
            # Only for block-starting elif/else
            if (is_elif and line_stripped.endswith(':')) or is_else:
                # Check if the next line is also an else/elif or end of block
                if i + 1 < len(lines):
                    next_line_lower = lines[i + 1].strip().lower()
                    if next_line_lower.startswith('else:') or next_line_lower.startswith('elif '):
                        # This elif/else has no body, add a pass statement
                        pass_line = ' ' * ((current_indent + 1) * 4) + 'pass'
                        indented_lines.append(pass_line)
            
            # Update indent stack
            # Single-line if/elif statements don't create a new block, so don't push to stack
            if is_block_start:
                indent_stack.append(current_indent + 1)
            elif is_elif and line_stripped.endswith(':'):
                # Block-starting elif needs indentation for its body
                indent_stack.append(current_indent + 1)
            elif is_else:
                # else needs indentation for its body
                indent_stack.append(current_indent + 1)
            # Note: is_single_line_if and is_single_line_elif don't push to stack because they're single lines
        
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
        
        # Handle if ... : statements (created during splitting)
        if_match_colon = re.match(r'if\s+(.+?)\s*:\s*$', statement, re.IGNORECASE)
        if if_match_colon:
            condition = self.translate_expression(if_match_colon.group(1))
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
        
        # Handle for loops (with do)
        for_match = re.match(r'for\s+(\w+)\s*:=\s*(\S+)\s+to\s+(\S+)\s+do', statement, re.IGNORECASE)
        if for_match:
            var_name = for_match.group(1)
            start = for_match.group(2)
            end = for_match.group(3)
            return f'{' '* indent}for {var_name} in range({start}, {end} + 1):'
        
        # Handle for loops without do (split lines)
        for_match_no_do = re.match(r'for\s+(\w+)\s*:=\s*(\S+)\s+to\s+(\S+)\s*:', statement, re.IGNORECASE)
        if for_match_no_do:
            var_name = for_match_no_do.group(1)
            start = for_match_no_do.group(2)
            end = for_match_no_do.group(3)
            return f'{' '* indent}for {var_name} in range({start}, {end} + 1):'
        
        # Handle for loops with downto (with do)
        for_down_match = re.match(r'for\s+(\w+)\s*:=\s*(\S+)\s+downto\s+(\S+)\s+do', statement, re.IGNORECASE)
        if for_down_match:
            var_name = for_down_match.group(1)
            start = for_down_match.group(2)
            end = for_down_match.group(3)
            return f'{' '* indent}for {var_name} in range({start}, {end} - 1, -1):'
        
        # Handle for loops with downto without do (split lines)
        for_down_match_no_do = re.match(r'for\s+(\w+)\s*:=\s*(\S+)\s+downto\s+(\S+)\s*:', statement, re.IGNORECASE)
        if for_down_match_no_do:
            var_name = for_down_match_no_do.group(1)
            start = for_down_match_no_do.group(2)
            end = for_down_match_no_do.group(3)
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
        
        # Handle exit - in Pascal, exit exits the current procedure, so use return
        if statement.lower().startswith('exit'):
            return f'{' '* indent}return'
        
        # Handle else
        if statement.lower() == 'else':
            return f'{' '* indent}else:'
        
        # Handle function calls - replace all function calls in the statement
        if '(' in statement and ')' in statement:
            # Find all function calls and translate them
            func_call_pattern = r'(\w+)\s*\(([^)]*)\)'
            matches = list(re.finditer(func_call_pattern, statement))
            if matches:
                # Replace all function calls from right to left to preserve positions
                for match in reversed(matches):
                    func_name = match.group(1)
                    args = match.group(2)
                    translated_call = self.translate_expression(match.group(0))
                    statement = statement[:match.start()] + translated_call + statement[match.end():]
                # After replacing function calls, translate the entire statement as an expression
                # to handle assignments and other operators
                translated = self.translate_expression(statement)
                return f'{' '* indent}{translated}'
        
        # Default: return the translated expression
        return f'{' '* indent}{self.translate_expression(statement)}'
    
    def transpile_procedure(self, proc_info: Dict) -> str:
        """Transpile a single procedure with proper indentation"""
        name = proc_info['name']
        params = proc_info['params']
        body = proc_info['body']
        is_function = proc_info.get('is_function', False)
        
        # Identify var parameters
        var_params = [p['name'] for p in params if p.get('is_var', False)]
        
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
        
        # Replace var parameter usage with list indexing
        # For var parameters, we use list indexing: var_param[0]
        # This handles both assignments (var_param = value) and reads (if var_param > 0)
        if var_params:
            for i, line in enumerate(translated_lines):
                for var_param in var_params:
                    # Replace all occurrences of var_param with var_param[0]
                    # Use word boundaries to avoid replacing partial matches
                    # Replace standalone var_param (not part of a larger word)
                    # This handles: assignments (var_param =), reads (var_param >), etc.
                    translated_lines[i] = re.sub(
                        rf'\b{var_param}\b',
                        f'{var_param}[0]',
                        translated_lines[i]
                    )
        
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
        self.transpiler = TRPTranspilerV3()
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
