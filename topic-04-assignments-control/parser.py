"""
parser.py -- implement simple parser for PMDAS expressions

Accept a string of tokens, return an AST expressed as a stack of dictionaries
"""

"""
    simple_expression = number | identifier | "(" expression ")" | "-" simple_expression
    factor = simple_expression;
    term = factor { "*"|"/" factor };
    math_expression = term { "+"|"-" term };
    relational_expression = math_expression { ("<" | ">" | "<=" | ">=" | "==" | "!=") math_expression };

    expression = relational_expression [ "=" relational_expression ]
    expression_list = "(" [ expression { "," expression } ] ")";
    print_statement = "print" 
    if_statement = "if" "(" expression ")" statement [ "else" statement ];
    while_statement = "while" "(" expression ")" statement;
    block_statement = "{" {";"} [ statement { ";" {";"} statement } {";"} ] "}";

    statement = if_statement | while_statement | print_statement | block_statement | expression;
    program = statement;
"""

from tokenizer import tokenize


def parse_simple_expression(tokens):
    """
    simple_expression = number | identifier | "(" expression ")" | "-" simple_expression
    """
    if tokens[0]["tag"] == "number":
        return tokens[0], tokens[1:]
    if tokens[0]["tag"] == "identifier":
        return tokens[0], tokens[1:]
    if tokens[0]["tag"] == "(":
        node, tokens = parse_expression(tokens[1:])
        assert tokens[0]["tag"] == ")", "Error: expected ')'"
        return node, tokens[1:]
    if tokens[0]["tag"] == "-":
        new_node, tokens = parse_simple_expression(tokens[1:])
        node = {"tag": "negate", "value": new_node}
        return node, tokens
    return node, tokens

    raise Exception("Error: unexpected token.")


def test_parse_simple_expression():
    """
    simple_expression = number | identifier | "(" expression ")" | "-" simple_expression
    """
    tokens = tokenize("2")
    ast, tokens = parse_simple_expression(tokens)
    assert ast["tag"] == "number"
    assert ast["value"] == 2
    tokens = tokenize("-2")
    ast, tokens = parse_simple_expression(tokens)
    assert ast == {
        "tag": "negate",
        "value": {"tag": "number", "value": 2, "position": 1},
    }
    tokens = tokenize("x")
    ast, tokens = parse_simple_expression(tokens)
    assert ast["tag"] == "identifier"
    assert ast["value"] == "x"


def parse_factor(tokens):
    """
    factor = simple_expression;
    """
    return parse_simple_expression(tokens)


def test_parse_factor():
    """
    factor = simple_expression;
    """
    tokens = tokenize("2")
    ast, tokens = parse_factor(tokens)
    tokens = tokenize("2")
    ast2, tokens2 = parse_simple_expression(tokens)
    assert ast == ast2


def parse_term(tokens):
    """
    term = factor { "*"|"/" factor };
    """
    node, tokens = parse_factor(tokens)
    while tokens[0]["tag"] in ["*", "/"]:
        operator = tokens[0]["tag"]
        new_node, tokens = parse_factor(tokens[1:])
        node = {"tag": operator, "left": node, "right": new_node}
    return node, tokens


def test_parse_term():
    """
    term = factor { "*"|"/" factor };
    """
    tokens = tokenize("2")
    ast, tokens = parse_term(tokens)
    assert ast["tag"] == "number"
    assert ast["value"] == 2
    tokens = tokenize("2*2")
    ast, tokens = parse_term(tokens)
    assert ast == {
        "tag": "*",
        "left": {"tag": "number", "value": 2, "position": 0},
        "right": {"tag": "number", "value": 2, "position": 2},
    }


def parse_math_expression(tokens):
    """
    math_expression = term { "+"|"-" term };
    """
    node, tokens = parse_term(tokens)
    while tokens[0]["tag"] in ["+", "-"]:
        operator = tokens[0]["tag"]
        new_node, tokens = parse_term(tokens[1:])
        node = {"tag": operator, "left": node, "right": new_node}
    return node, tokens


def test_parse_math_expression():
    """
    math_expression = term { "+"|"-" term };
    """
    tokens = tokenize("2")
    ast, tokens = parse_term(tokens)
    assert ast == {"tag": "number", "value": 2, "position": 0}
    ast, tokens = parse_math_expression(tokenize("2+3"))
    assert ast == {
        "tag": "+",
        "left": {"tag": "number", "value": 2, "position": 0},
        "right": {"tag": "number", "value": 3, "position": 2},
    }
    ast, tokens = parse_math_expression(tokenize("1+2+3"))
    assert ast == {
        "tag": "+",
        "left": {
            "tag": "+",
            "left": {"tag": "number", "value": 1, "position": 0},
            "right": {"tag": "number", "value": 2, "position": 2},
        },
        "right": {"tag": "number", "value": 3, "position": 4},
    }
    ast, tokens = parse_math_expression(tokenize("x+y+z"))
    assert ast == {
        "tag": "+",
        "left": {
            "tag": "+",
            "left": {"tag": "identifier", "value": "x", "position": 0},
            "right": {"tag": "identifier", "value": "y", "position": 2},
        },
        "right": {"tag": "identifier", "value": "z", "position": 4},
    }
    ast, tokens = parse_math_expression(tokenize("3-2"))
    assert ast == {
        "tag": "-",
        "left": {"tag": "number", "value": 3, "position": 0},
        "right": {"tag": "number", "value": 2, "position": 2},
    }
    ast, tokens = parse_math_expression(tokenize("1+2*3"))
    assert ast == {
        "tag": "+",
        "left": {"tag": "number", "value": 1, "position": 0},
        "right": {
            "tag": "*",
            "left": {"tag": "number", "value": 2, "position": 2},
            "right": {"tag": "number", "value": 3, "position": 4},
        },
    }
    ast, tokens = parse_math_expression(tokenize("(1+2)*3"))
    assert ast == {
        "tag": "*",
        "left": {
            "tag": "+",
            "left": {"tag": "number", "value": 1, "position": 1},
            "right": {"tag": "number", "value": 2, "position": 3},
        },
        "right": {"tag": "number", "value": 3, "position": 6},
    }
    ast, tokens = parse_math_expression(tokenize("-(1+2)*-3"))
    assert ast == {
        "tag": "*",
        "left": {
            "tag": "negate",
            "value": {
                "tag": "+",
                "left": {"tag": "number", "value": 1, "position": 2},
                "right": {"tag": "number", "value": 2, "position": 4},
            },
        },
        "right": {
            "tag": "negate",
            "value": {"tag": "number", "value": 3, "position": 8},
        },
    }


def parse_relational_expression(tokens):
    """
    relational_expression = arithmetic_expression { ("<" | ">" | "<=" | ">=" | "==" | "!=") arithmetic_expression };
    """
    node, tokens = parse_math_expression(tokens)
    while tokens[0]["tag"] in ["<", ">", "<=", ">=", "==", "!="]:
        tag = tokens[0]["tag"]
        next_node, tokens = parse_math_expression(tokens[1:])
        node = {"tag": tag, "left": node, "right": next_node}
    return node, tokens


def parse_logical_factor(tokens):
    """
    logical_factor = relational_expression | "!" logical_factor;
    """
    token = tokens[0]
    if token["tag"] == "!":
        node, tokens = parse_logical_factor(tokens[1:])
        return {"tag": "not", "value": node}, tokens
    return parse_relational_expression(tokens)


def parse_logical_term(tokens):
    """
    logical_term = logical_factor { "&&" logical_factor };
    """
    node, tokens = parse_logical_factor(tokens)
    while tokens[0]["tag"] == "&&":
        tag = tokens[0]["tag"]
        next_node, tokens = parse_logical_factor(tokens[1:])
        node = {"tag": tag, "left": node, "right": next_node}
    return node, tokens


def parse_logical_expression(tokens):
    """
    logical_expression = logical_term { "||" logical_term };
    """
    node, tokens = parse_logical_term(tokens)
    while tokens[0]["tag"] == "||":
        tag = tokens[0]["tag"]
        next_node, tokens = parse_logical_term(tokens[1:])
        node = {"tag": tag, "left": node, "right": next_node}
    return node, tokens


def parse_expression(tokens):
    """
    expression = math_expression [ "=" math_expression ]
    """
    ast, tokens = parse_logical_expression(tokens)
    if tokens[0]["tag"] == "=":
        operator = tokens[0]["tag"]
        value_ast, tokens = parse_math_expression(tokens[1:])
        ast = {"tag": operator, "target": ast, "value": value_ast}
    return ast, tokens


def test_parse_expression():
    """
    expression = math_expression [ "=" math_expression ]
    """
    for expr in ["2", "2+2", "2*2", "i"]:
        tokens = tokenize(expr)
        ast1, _ = parse_math_expression(tokens)
        ast2, _ = parse_expression(tokens)
        assert ast1 == ast2
        tokens = tokenize(f"  {expr}")
        ref_ast, _ = parse_expression(tokens)
        tokens = tokenize(f"i={expr}")
        ast, _ = parse_expression(tokens)
        assert ast["tag"] == "="
        assert ast["target"] == {"tag": "identifier", "value": "i", "position": 0}
        assert ast["value"] == ref_ast
    tokens = tokenize(f"i+2+3+4=i")
    ast, _ = parse_expression(tokens)
    assert ast == {
        "tag": "=",
        "target": {
            "tag": "+",
            "left": {
                "tag": "+",
                "left": {
                    "tag": "+",
                    "left": {"tag": "identifier", "value": "i", "position": 0},
                    "right": {"tag": "number", "value": 2, "position": 2},
                },
                "right": {"tag": "number", "value": 3, "position": 4},
            },
            "right": {"tag": "number", "value": 4, "position": 6},
        },
        "value": {"tag": "identifier", "value": "i", "position": 8},
    }


def parse_expression_list(tokens):
    """
    expression_list = "(" [ expression { "," expression } ] ")";
    """
    assert tokens[0]["tag"] == "("
    tokens = tokens[1:]
    first_node = None
    if tokens[0]["tag"] != ")":
        node, tokens = parse_expression(tokens)
        first_node = node
        while tokens[0]["tag"] != ")":
            assert tokens[0]["tag"] == ","
            tokens = tokens[1:]
            node["next"], tokens = parse_expression(tokens)
            node = node["next"]
    assert tokens[0]["tag"] == ")"
    tokens = tokens[1:]
    return first_node, tokens


def test_parse_expression_list():
    ast, tokens = parse_expression_list(tokenize("()"))
    assert ast == None
    ast, tokens = parse_expression_list(tokenize("(1)"))
    assert ast == {"tag": "number", "value": 1, "position": 1}
    ast, tokens = parse_expression_list(tokenize("(1,2,3)"))
    assert ast == {
        "tag": "number",
        "value": 1,
        "position": 1,
        "next": {
            "tag": "number",
            "value": 2,
            "position": 3,
            "next": {"tag": "number", "value": 3, "position": 5},
        },
    }


def parse_if_statement(tokens):
    """
    if_statement = "if" "(" expression ")" statement [ "else" statement ];
    """
    assert tokens[0]["tag"] == "if"
    tokens = tokens[1:]
    assert tokens[0]["tag"] == "("
    tokens = tokens[1:]
    condition, tokens = parse_expression(tokens)
    assert tokens[0]["tag"] == ")"
    tokens = tokens[1:]
    then_statement, tokens = parse_statement(tokens)
    node = {"tag": "if", "condition": condition, "then": then_statement}
    if tokens[0]["tag"] == "else":
        tokens = tokens[1:]
        else_statement, tokens = parse_statement(tokens)
        node["else"] = else_statement
    return node, tokens


def test_parse_if_statement():
    """
    if_statement = "if" "(" expression ")" statement [ "else" statement ];
    """
    ast, tokens = parse_if_statement(tokenize("if(1)print(1)"))
    assert ast == {
        "tag": "if",
        "condition": {"tag": "number", "value": 1, "position": 3},
        "then": {
            "tag": "print",
            "arguments": {"tag": "number", "value": 1, "position": 11},
        },
    }
    ast, tokens = parse_if_statement(tokenize("if(1) print(1) else print(2)"))
    assert ast == {
        "tag": "if",
        "condition": {"tag": "number", "value": 1, "position": 3},
        "then": {
            "tag": "print",
            "arguments": {"tag": "number", "value": 1, "position": 12},
        },
        "else": {
            "tag": "print",
            "arguments": {"tag": "number", "value": 2, "position": 26},
        },
    }


def parse_while_statement(tokens):
    """
    while_statement = "while" "(" expression ")" statement;
    """
    assert tokens[0]["tag"] == "while"
    tokens = tokens[1:]
    assert tokens[0]["tag"] == "("
    tokens = tokens[1:]
    condition, tokens = parse_expression(tokens)
    assert tokens[0]["tag"] == ")"
    tokens = tokens[1:]
    do_statement, tokens = parse_statement(tokens)
    node = {"tag": "while", "condition": condition, "do": do_statement}
    return node, tokens


def test_parse_while_statement():
    """
    while_statement = "while" "(" expression ")" statement;
    """
    ast, tokens = parse_while_statement(tokenize("while(1)print(1)"))
    assert ast == {
        "tag": "while",
        "condition": {"tag": "number", "value": 1, "position": 6},
        "do": {
            "tag": "print",
            "arguments": {"tag": "number", "value": 1, "position": 14},
        },
    }


def parse_print_statement(tokens):
    """
    print_statement = "print" expression_list
    """
    assert tokens[0]["tag"] == "print"
    tokens = tokens[1:]
    arguments, tokens = parse_expression_list(tokens)
    return {"tag": "print", "arguments": arguments}, tokens


def test_parse_print_statement():
    ast, tokens = parse_print_statement(tokenize("print(4)"))
    assert ast == {
        "tag": "print",
        "arguments": {"tag": "number", "value": 4, "position": 6},
    }
    ast, tokens = parse_print_statement(tokenize("print(1,2,3)"))
    assert ast == {
        "tag": "print",
        "arguments": {
            "tag": "number",
            "value": 1,
            "position": 6,
            "next": {
                "tag": "number",
                "value": 2,
                "position": 8,
                "next": {"tag": "number", "value": 3, "position": 10},
            },
        },
    }


def parse_block_statement(tokens):
    """
    block_statement = "{" {";"} [ statement { ";" {";"} statement } {";"} ] "}";
    """
    assert tokens[0]["tag"] == "{"
    tokens = tokens[1:]
    node = {"tag": "block"}
    first_node = node
    while tokens[0]["tag"] == ";":
        tokens = tokens[1:]
    if tokens[0]["tag"] != "}":
        statement, tokens = parse_statement(tokens)
        node["statement"] = statement
        while tokens[0]["tag"] == ";":
            while tokens[0]["tag"] == ";":
                tokens = tokens[1:]
            if tokens[0]["tag"] != "}":
                statement, tokens = parse_statement(tokens)
                node["next"] = {"tag": "block", "statement": statement}
                node = node["next"]
            assert tokens[0]["tag"] in [";", "}"]
    assert tokens[0]["tag"] == "}"
    tokens = tokens[1:]
    return first_node, tokens


def depo(x):
    for key in x:
        if key == "position":
            x[key] = 0
        if type(x[key]) is dict:
            x[key] = depo(x[key])
    return x


def test_parse_block_statement():
    """
    block_statement = "{" {";"} [ statement { ";" {";"} statement } {";"} ] "}";
    """
    for code in ["{x=1}", "{x=1;}", "{x=1;;}", "{;;x=1;;}"]:
        ast = depo(parse_block_statement(tokenize(code))[0])
        assert ast == {
            "tag": "block",
            "statement": {
                "tag": "=",
                "target": {"tag": "identifier", "value": "x", "position": 0},
                "value": {"tag": "number", "value": 1, "position": 0},
            },
        }
    for code in ["{x=1;y=2}", "{x=1;y=2;}", "{x=1;;y=2;}", "{;x=1;;y=2;}"]:
        ast = parse_block_statement(tokenize(code))[0]
        ast = depo(ast)
        assert ast == {
            "tag": "block",
            "statement": {
                "tag": "=",
                "target": {"tag": "identifier", "value": "x", "position": 0},
                "value": {"tag": "number", "value": 1, "position": 0},
            },
            "next": {
                "tag": "block",
                "statement": {
                    "tag": "=",
                    "target": {"tag": "identifier", "value": "y", "position": 0},
                    "value": {"tag": "number", "value": 2, "position": 0},
                },
            },
        }

    ast = parse_block_statement(tokenize("{x=1;y=2;z=3}"))[0]
    ast = depo(ast)
    assert ast == {
        "tag": "block",
        "statement": {
            "tag": "=",
            "target": {"tag": "identifier", "value": "x", "position": 0},
            "value": {"tag": "number", "value": 1, "position": 0},
        },
        "next": {
            "tag": "block",
            "statement": {
                "tag": "=",
                "target": {"tag": "identifier", "value": "y", "position": 0},
                "value": {"tag": "number", "value": 2, "position": 0},
            },
            "next": {
                "tag": "block",
                "statement": {
                    "tag": "=",
                    "target": {"tag": "identifier", "value": "z", "position": 0},
                    "value": {"tag": "number", "value": 3, "position": 0},
                },
            },
        },
    }
    # ast = parse_block_statement(tokenize("{return 1}"))[0]
    # ast = depo(ast)
    # assert ast == {
    #     "tag": "block",
    #     "statement": {
    #         "tag": "return",
    #         "value": {"tag": "number", "value": 1, "position": 0},
    #     },
    # }
    assert (
        parse_block_statement(tokenize("{x=1;y=2}"))[0]
        == parse_block_statement(tokenize("{x=1;y=2;}"))[0]
    )


def parse_statement(tokens):
    """
    statement = if_statement | while_statement | print_statement | block_statement | expression;
    """
    tag = tokens[0]["tag"]
    if tag == "if":
        return parse_if_statement(tokens)
    if tag == "while":
        return parse_while_statement(tokens)
    if tag == "print":
        return parse_print_statement(tokens)
    if tag == "{":
        return parse_block_statement(tokens)
    return parse_expression(tokens)


def test_parse_statement():
    # print statement
    assert parse_statement(tokenize("print(4)")) == parse_print_statement(
        tokenize("print(4)")
    )

    # expression statements
    assert parse_statement(tokenize("5+3"))[0] == parse_expression(tokenize("5+3"))[0]

    # block statements
    assert (
        parse_statement(tokenize("{x=1;y=2}"))[0]
        == parse_block_statement(tokenize("{x=1;y=2}"))[0]
    )


def parse_program(tokens):
    """
    programs = statement;
    """
    return parse_statement(tokens)


def test_parse_program():
    # expression statements
    assert parse_program(tokenize("5+3"))[0] == parse_statement(tokenize("5+3"))[0]


def parse(tokens):
    ast, _ = parse_program(tokens)
    return ast


def test_parse():
    """
    expression = term { "+" term };
    """
    for expression in ["2", "2+2", "1+2+3"]:
        tokens = tokenize(expression)
        ast1 = parse(tokens)
        ast2, _ = parse_expression(tokens)
        assert str(ast1) == str(ast2)


if __name__ == "__main__":
    test_parse_simple_expression()
    test_parse_factor()
    test_parse_term()
    test_parse_math_expression()
    test_parse_expression()
    test_parse_expression_list()
    test_parse_if_statement()
    test_parse_while_statement()
    test_parse_print_statement()
    test_parse_block_statement()
    test_parse_statement()
    test_parse()
    print("done.")
