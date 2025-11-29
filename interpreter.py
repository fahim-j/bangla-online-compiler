import sys
import ast
import operator
import re

if len(sys.argv) >= 2:
    path = sys.argv[1]
    text = open(path, encoding='utf-8').read()
else:
    text = sys.stdin.read()

text = text.replace('\r\n', '\n').replace('\r', '\n')

def strip_comments(src):
    out_lines = []
    for line in src.splitlines():
        idx = line.find('//')
        if idx != -1:
            line = line[:idx]
        out_lines.append(line)
    return '\n'.join(out_lines)

text = strip_comments(text)
stmts = [s.strip() for s in text.split(';') if s.strip()]
symbols = {}

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
    try:
        node = ast.parse(expr_src, mode='eval').body
    except Exception as e:
        raise ValueError("Invalid expression: " + str(e))

    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int,)):
                return node.value
            else:
                raise ValueError("Only integer constants allowed")
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in ALLOWED_BINOPS:
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
            name = node.id
            return symbols.get(name, 0)
        raise ValueError("Invalid expression element: " + type(node).__name__)
    return _eval(node)

for s in stmts:
    if not s.strip():
        continue
    if s.startswith('ধারণ'):
        m = re.match(r'^\s*ধারণ\s+([^\s=]+)\s*(=\s*(.+))?$', s, flags=re.UNICODE)
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
    sys.stderr.write("Unknown statement: " + s + "\n")
