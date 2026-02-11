import ply.lex as lex
import ply.yacc as yacc
import json
import itertools

# ============================================================
# LEXER
# ============================================================

tokens = (
    'AND', 'OR', 'NOT', 'XOR',
    'TRUE', 'FALSE',
    'LPAREN', 'RPAREN',
    'VAR'
)

t_AND = r'AND'
t_OR = r'OR'
t_NOT = r'NOT'
t_XOR = r'XOR'
t_TRUE = r'TRUE'
t_FALSE = r'FALSE'
t_LPAREN = r'\('
t_RPAREN = r'\)'

t_ignore = ' \t'

def t_VAR(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    keywords = {
        'AND': 'AND',
        'OR': 'OR',
        'NOT': 'NOT',
        'XOR': 'XOR',
        'TRUE': 'TRUE',
        'FALSE': 'FALSE'
    }
    t.type = keywords.get(t.value, 'VAR')
    return t

def t_error(t):
    raise SyntaxError(f"Caractère invalide: {t.value[0]}")

lexer = lex.lex()

# ============================================================
# PARSER
# ============================================================

precedence = (
    ('left', 'OR'),
    ('left', 'XOR'),
    ('left', 'AND'),
    ('right', 'NOT'),
)

# OR
def p_expression_or(p):
    'expression : expression OR expression'
    p[0] = {"type": "OR", "left": p[1], "right": p[3]}

# XOR
def p_expression_xor(p):
    'expression : expression XOR expression'
    p[0] = {"type": "XOR", "left": p[1], "right": p[3]}

# AND
def p_expression_and(p):
    'expression : expression AND expression'
    p[0] = {"type": "AND", "left": p[1], "right": p[3]}

# NOT
def p_expression_not(p):
    'expression : NOT expression'
    p[0] = {"type": "NOT", "operand": p[2]}

# Parenthèses
def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

# Variable
def p_expression_var(p):
    'expression : VAR'
    p[0] = {"type": "VAR", "name": p[1]}

# Constantes
def p_expression_true(p):
    'expression : TRUE'
    p[0] = {"type": "CONST", "value": True}

def p_expression_false(p):
    'expression : FALSE'
    p[0] = {"type": "CONST", "value": False}

def p_error(p):
    if p:
        raise SyntaxError(f"Erreur syntaxique sur '{p.value}'")
    else:
        raise SyntaxError("Fin d'entrée inattendue")

parser = yacc.yacc()

# ============================================================
# PARSE
# ============================================================

def parse_logic(text):
    return parser.parse(text)

# ============================================================
# ÉVALUATION LOGIQUE
# ============================================================

def evaluate(node, context=None):
    if context is None:
        context = {}

    t = node["type"]

    if t == "CONST":
        return node["value"]

    if t == "VAR":
        if node["name"] not in context:
            raise ValueError(f"Variable non définie: {node['name']}")
        return context[node["name"]]

    if t == "NOT":
        return not evaluate(node["operand"], context)

    if t == "AND":
        return evaluate(node["left"], context) and evaluate(node["right"], context)

    if t == "OR":
        return evaluate(node["left"], context) or evaluate(node["right"], context)

    if t == "XOR":
        return evaluate(node["left"], context) ^ evaluate(node["right"], context)

    raise ValueError(f"Type inconnu: {t}")

# ============================================================
# EXPORT GRAPHVIZ
# ============================================================

def to_graphviz(tree):
    counter = itertools.count()
    lines = ["digraph LogicTree {"]

    def visit(node):
        node_id = f"n{next(counter)}"
        label = node["type"]

        if node["type"] == "VAR":
            label = node["name"]
        elif node["type"] == "CONST":
            label = str(node["value"])

        lines.append(f'{node_id} [label="{label}"];')

        if node["type"] in ("AND", "OR", "XOR"):
            left_id = visit(node["left"])
            right_id = visit(node["right"])
            lines.append(f"{node_id} -> {left_id};")
            lines.append(f"{node_id} -> {right_id};")

        elif node["type"] == "NOT":
            child_id = visit(node["operand"])
            lines.append(f"{node_id} -> {child_id};")

        return node_id

    visit(tree)
    lines.append("}")
    return "\n".join(lines)

# ============================================================
# EXEMPLE
# ============================================================

if __name__ == "__main__":
    expr = "A AND (B XOR TRUE) OR NOT FALSE"

    tree = parse_logic(expr)

    print("JSON:")
    print(json.dumps(tree, indent=2))

    print("\nÉvaluation avec A=True, B=False:")
    result = evaluate(tree, {"A": True, "B": False})
    print(result)

    print("\nGraphviz DOT:")
    dot = to_graphviz(tree)
    print(dot)

    # Pour générer une image :
    with open("tree.dot", "w") as f:
        f.write(dot)
    # puis :
    # dot -Tpng tree.dot -o tree.png
