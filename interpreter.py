# interpreter.py
# Simple Bangla mini-language interpreter (no external libs).
# Usage: python3 interpreter.py path/to/file.blg
# Features:
#  - keywords: 'ধারণ' (declare/let), 'মুদ্রণ' (print)
#  - assignment: x = expr;
#  - expr: integers, variables, + - * /, parentheses
#  - comments: // ... (single line)
# Notes: file must be UTF-8 encoded.

import sys
import ast
import operator
import re

if len(sys.argv) >= 2:
    path = sys.argv[1]
    text = open(path, encoding='utf-8').read()
else:
    text = sys.stdin.read()

# remove CRLF -> LF
text = text.replace('\r\n', '\n').replace('\r', '\n')

# remove lines that start with // or trailing comments
def strip_comments(src):
    out_lines = []
    for line in src.splitlines():
        idx = line.find('//')
        if idx != -1:
            line = line[:idx]
        out_lines.append(line)
    return '\n'.join(out_lines)

text = strip_comments(text)

# split into statements by ';' but keep parentheses content unaffected:
# a simple approach: split on semicolons (;) — users must end statements with ;
stmts = [s.strip() for s in text.split(';') if s.strip()]

# symbol table (variable names can be Bangla or latin)
symbols = {}

# safe eval using ast
ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.floordiv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}

ALLOWED_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

def eval_expr(expr_src):
    # parse expression into AST and evaluate only allowed nodes
    try:
        node = ast.parse(expr_src, mode='eval').body
    except Exception as e:
        raise ValueError("Invalid expression: " + str(e))

    def _eval(node):
        if isinstance(node, ast.Constant):  # Python 3.8+
            if isinstance(node.value, (int,)):
                return node.value
            else:
                raise ValueError("Only integer constants allowed")
        if isinstance(node, ast.Num):  # older
            return node.n
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in ALLOWED_BINOPS:
                # guard division by zero
                if op_type in (ast.Div, ast.FloorDiv) and right == 0:
                    raise ValueError("Division by zero")
                return ALLOWED_BINOPS[op_type](left, right)
            else:
                raise ValueError("Operator not allowed")
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type in ALLOWED_UNARYOPS:
                val = _eval(node.operand)
                return ALLOWED_UNARYOPS[op_type](val)
            else:
                raise ValueError("Unary operator not allowed")
        if isinstance(node, ast.Name):
            # variable reference (Bangla or latin)
            name = node.id
            return symbols.get(name, 0)
        if isinstance(node, ast.Call):
            raise ValueError("Function calls not allowed")
        raise ValueError("Invalid expression element: " + type(node).__name__)

    return _eval(node)

# parse statements
for s in stmts:
    # skip empty
    if not s.strip():
        continue
    # ধারা(ণ) declaration: startswith 'ধারণ'
    if s.startswith('ধারণ') or s.startswith('ধারণ'.strip()):
        # pattern: ধারণ <id> = <expr>
        m = re.match(r'^\s*ধারণ\s+([^\s=]+)\s*(=\s*(.+))?$',
                     s, flags=re.UNICODE)
        if not m:
            sys.stderr.write("Syntax Error in declaration: " + s + "\n")
            continue
        name = m.group(1)
        expr = m.group(3)
        if expr is None:
            symbols[name] = 0
        else:
            try:
                val = eval_expr(expr)
                symbols[name] = int(val)
            except Exception as e:
                sys.stderr.write("Error evaluating declaration expr: " + str(e) + "\n")
        continue

    # print: মুদ্রণ(expr)
    if s.startswith('মুদ্রণ'):
        m = re.match(r'^\s*মুদ্রণ\s*\(\s*(.+)\s*\)\s*$', s, flags=re.UNICODE)
        if not m:
            sys.stderr.write("Syntax Error in মুদ্রণ: " + s + "\n")
            continue
        expr = m.group(1)
        try:
            val = eval_expr(expr)
            sys.stdout.write(str(int(val)) + "\n")
        except Exception as e:
            sys.stderr.write("Error in মুদ্রণ expr: " + str(e) + "\n")
        continue

    # assignment: <id> = <expr>
    m = re.match(r'^\s*([^\s=]+)\s*=\s*(.+)$', s, flags=re.UNICODE)
    if m:
        name = m.group(1)
        expr = m.group(2)
        try:
            val = eval_expr(expr)
            symbols[name] = int(val)
        except Exception as e:
            sys.stderr.write("Error in assignment: " + str(e) + "\n")
        continue

    # unknown statement
    sys.stderr.write("Unknown statement: " + s + "\n")
