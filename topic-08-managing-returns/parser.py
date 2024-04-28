from tokenizer import tokenize

grammar = """
arithmetic_factor = <number> | <boolean> | <identifier> [ expression_list ] | "(" expression ")" | "-" arithmetic_factor | function_expression;
arithmetic_term = arithmetic_factor { ("*" | "/") arithmetic_factor };
arithmetic_expression = arithmetic_term { ("+" | "-") arithmetic_term };
relational_expression = arithmetic_expression { ("<" | ">" | "<=" | ">=" | "==" | "!=") arithmetic_expression };
logical_factor = relational_expression | "!" logical_factor;
logical_term = logical_factor { "&&" logical_factor };
logical_expression = logical_term { "||" logical_term };
function_expression = "function" identifier_list block_statement;
expression = logical_expression;
identifier_list = "(" [ <identifier> { "," <identifier> ] } ")";
expression_list = "(" [ expression { "," expression } ] ")";
assignment = <identifier> "=" expression;
block_statement = "{" {";"} [ statement { ";" {";"} statement } {";"} ] "}";
if_statement = "if" "(" expression ")" statement "else" statement;
while_statement = "while" "(" expression ")" statement;
return_statement = "return" [ expression ];
print_statement = "print" expression_list;
function_statement = "function" <identifier> identifier_list block_statement;
statement = block_statement | if_statement | while_statement |  function_statement | return_statement | print_statement | assignment | expression;
program = statement
"""

""" 
AST FORMAT

{ "tag":"<op>","left":<expression_node>, "right":<expression_node>}
{ "tag":"negate/not","value":<expression_node>}
{ "tag":"=", "target":<node>, "value":<expression_node>}
{ "tag":"if", "condition":<expression_node>, 
    "then":<statement_node>,
    "else":<statement_node>}
{ "tag":"while", "condition":<expression_node>, 
    "do":<statement_node>}

"""


def t(code):
    return tokenize(code) + [{"tag": None}]


def parse_arithmetic_factor(tokens):
    """
    arithmetic_factor = <number> | <boolean> | <identifier> [ expression_list ] | "(" expression ")" | "-" arithmetic_factor | function_expression;
    """
    token = tokens[0]
    tag = token["tag"]
    if tag == "<number>":
        return {"tag": "<number>", "value": token["value"]}, tokens[1:]
    if tag == "<boolean>":
        return {"tag": "<boolean>", "value": token["value"]}, tokens[1:]
    if tag == "<identifier>":
        node = {"tag": "<identifier>", "value": token["value"]}
        tokens = tokens[1:]
        if tokens[0]["tag"] == "(":
            arguments, tokens = parse_expression_list(tokens)
            node = {
                "tag": "<function_call>",
                "identifier": node,
                "arguments": arguments
            }
        return node, tokens
    if tag == "(":
        node, tokens = parse_relational_expression(tokens[1:])
        if tokens[0]["tag"] != ")":
            raise Exception("Expected ')'")
        return node, tokens[1:]
    if tag == "-":
        node, tokens = parse_arithmetic_factor(tokens[1:])
        return {"tag": "negate", "value": node}, tokens
    if tag == "function":
        return parse_function_expression(tokens)

    raise Exception(f"Unexpected token: {tokens[0]}")


def test_parse_arithmetic_factor():
    """
    arithmetic_factor = <number> | <boolean> | <identifier> [ expression_list ] | "(" expression ")" | "-" arithmetic_factor | function_expression;
    """
    assert parse_arithmetic_factor(t("1"))[0] == {"tag": "<number>", "value": 1}
    assert parse_arithmetic_factor(t("1.2"))[0] == {"tag": "<number>", "value": 1.2}
    assert parse_arithmetic_factor(t("true"))[0] == {"tag": "<boolean>", "value": 1}
    assert parse_arithmetic_factor(t("false"))[0] == {"tag": "<boolean>", "value": 0}
    assert parse_arithmetic_factor(t("x"))[0] == {"tag": "<identifier>", "value": "x"}
    ast = parse_arithmetic_factor(t("x()"))[0]
    assert ast == {
        "tag": "<function_call>",
        "identifier": {"tag": "<identifier>", "value": "x"},
        "arguments": None,
    }
    ast = parse_arithmetic_factor(t("x(1)"))[0]
    assert ast == {
        "tag": "<function_call>",
        "identifier": {"tag": "<identifier>", "value": "x"},
        "arguments": {"tag": "<number>", "value": 1},
    }
    ast = parse_arithmetic_factor(t("x(1,2+3)"))[0]
    assert ast == {
        "tag": "<function_call>",
        "identifier": {"tag": "<identifier>", "value": "x"},
        "arguments": {
            "tag": "<number>",
            "value": 1,
            "next": {
                "tag": "+",
                "left": {"tag": "<number>", "value": 2},
                "right": {"tag": "<number>", "value": 3},
            },
        },
    }

    assert parse_arithmetic_factor(t("-1"))[0] == {
        "tag": "negate",
        "value": {"tag": "<number>", "value": 1},
    }


def parse_arithmetic_term(tokens):
    """
    arithmetic_term = arithmetic_factor { ("*" | "/") arithmetic_factor };
    """
    node, tokens = parse_arithmetic_factor(tokens)
    while tokens[0]["tag"] in ["*", "/"]:
        tag = tokens[0]["tag"]
        next_node, tokens = parse_arithmetic_factor(tokens[1:])
        node = {"tag": tag, "left": node, "right": next_node}
    return node, tokens


def test_parse_arithmetic_term():
    """
    arithmetic_term = arithmetic_factor { ("*" | "/") arithmetic_factor };
    """
    assert parse_arithmetic_term(t("x"))[0] == {"tag": "<identifier>", "value": "x"}
    assert parse_arithmetic_term(t("x*y"))[0] == {
        "tag": "*",
        "left": {"tag": "<identifier>", "value": "x"},
        "right": {"tag": "<identifier>", "value": "y"},
    }
    assert parse_arithmetic_term(t("x/y"))[0] == {
        "tag": "/",
        "left": {"tag": "<identifier>", "value": "x"},
        "right": {"tag": "<identifier>", "value": "y"},
    }
    assert parse_arithmetic_term(t("x*y/z"))[0] == {
        "tag": "/",
        "left": {
            "tag": "*",
            "left": {"tag": "<identifier>", "value": "x"},
            "right": {"tag": "<identifier>", "value": "y"},
        },
        "right": {"tag": "<identifier>", "value": "z"},
    }


def parse_arithmetic_expression(tokens):
    """
    arithmetic_expression = arithmetic_term { ("+" | "-") arithmetic_term };
    """
    node, tokens = parse_arithmetic_term(tokens)
    while tokens[0]["tag"] in ["+", "-"]:
        tag = tokens[0]["tag"]
        next_node, tokens = parse_arithmetic_term(tokens[1:])
        node = {"tag": tag, "left": node, "right": next_node}
    return node, tokens


def test_parse_arithmetic_expression():
    """
    arithmetic_expression = arithmetic_term { ("+" | "-") arithmetic_term };
    """
    assert parse_arithmetic_expression(t("x"))[0] == {
        "tag": "<identifier>",
        "value": "x",
    }
    assert parse_arithmetic_expression(t("x*y"))[0] == {
        "tag": "*",
        "left": {"tag": "<identifier>", "value": "x"},
        "right": {"tag": "<identifier>", "value": "y"},
    }
    assert parse_arithmetic_expression(t("x+y"))[0] == {
        "tag": "+",
        "left": {"tag": "<identifier>", "value": "x"},
        "right": {"tag": "<identifier>", "value": "y"},
    }
    assert parse_arithmetic_expression(t("x-y"))[0] == {
        "tag": "-",
        "left": {"tag": "<identifier>", "value": "x"},
        "right": {"tag": "<identifier>", "value": "y"},
    }
    assert parse_arithmetic_expression(t("x+y-z"))[0] == {
        "tag": "-",
        "left": {
            "tag": "+",
            "left": {"tag": "<identifier>", "value": "x"},
            "right": {"tag": "<identifier>", "value": "y"},
        },
        "right": {"tag": "<identifier>", "value": "z"},
    }
    ast = parse_arithmetic_expression(t("x+y*z"))[0]
    assert ast == {
        "tag": "+",
        "left": {"tag": "<identifier>", "value": "x"},
        "right": {
            "tag": "*",
            "left": {"tag": "<identifier>", "value": "y"},
            "right": {"tag": "<identifier>", "value": "z"},
        },
    }
    ast = parse_arithmetic_expression(t("(x+y)*z"))[0]
    assert ast == {
        "tag": "*",
        "left": {
            "tag": "+",
            "left": {"tag": "<identifier>", "value": "x"},
            "right": {"tag": "<identifier>", "value": "y"},
        },
        "right": {"tag": "<identifier>", "value": "z"},
    }

def parse_relational_expression(tokens):
    """
    relational_expression = arithmetic_expression { ("<" | ">" | "<=" | ">=" | "==" | "!=") arithmetic_expression };
    """
    node, tokens = parse_arithmetic_expression(tokens)
    while tokens[0]["tag"] in ["<", ">", "<=", ">=", "==", "!="]:
        tag = tokens[0]["tag"]
        next_node, tokens = parse_arithmetic_expression(tokens[1:])
        node = {"tag": tag, "left": node, "right": next_node}
    return node, tokens


def test_parse_relational_expression():
    """
    relational_expression = arithmetic_expression { ("<" | ">" | "<=" | ">=" | "==" | "!=") arithmetic_expression };
    """
    assert parse_relational_expression(t("x"))[0] == {
        "tag": "<identifier>",
        "value": "x",
    }
    for tag in ["<", ">", "<=", ">=", "==", "!="]:
        assert parse_relational_expression(t(f"x{tag}y"))[0] == {
            "tag": tag,
            "left": {"tag": "<identifier>", "value": "x"},
            "right": {"tag": "<identifier>", "value": "y"},
        }
    assert parse_relational_expression(t("x<y>z"))[0] == {
        "tag": ">",
        "left": {
            "tag": "<",
            "left": {"tag": "<identifier>", "value": "x"},
            "right": {"tag": "<identifier>", "value": "y"},
        },
        "right": {"tag": "<identifier>", "value": "z"},
    }


def parse_logical_factor(tokens):
    """
    logical_factor = relational_expression | "!" logical_factor;
    """
    token = tokens[0]
    if token["tag"] == "!":
        node, tokens = parse_logical_factor(tokens[1:])
        return {"tag": "not", "value": node}, tokens
    return parse_relational_expression(tokens)


def test_parse_logical_factor():
    """
    logical_factor = relational_expression | "!" logical_factor;
    """
    assert parse_logical_factor(t("x"))[0] == {"tag": "<identifier>", "value": "x"}

    assert parse_logical_factor(t("!x"))[0] == {
        "tag": "not",
        "value": {"tag": "<identifier>", "value": "x"},
    }


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


def test_parse_logical_term():
    """
    logical_term = logical_factor { "&&" logical_factor };
    """
    assert parse_logical_term(t("x"))[0] == {"tag": "<identifier>", "value": "x"}
    assert parse_logical_term(t("x&&y"))[0] == {
        "tag": "&&",
        "left": {"tag": "<identifier>", "value": "x"},
        "right": {"tag": "<identifier>", "value": "y"},
    }
    assert parse_logical_term(t("x&&y&&z"))[0] == {
        "tag": "&&",
        "left": {
            "tag": "&&",
            "left": {"tag": "<identifier>", "value": "x"},
            "right": {"tag": "<identifier>", "value": "y"},
        },
        "right": {"tag": "<identifier>", "value": "z"},
    }


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


def test_parse_logical_expression():
    """
    logical_expression = logical_term { "||" logical_term };
    """

    assert parse_logical_expression(t("x"))[0] == {"tag": "<identifier>", "value": "x"}
    assert parse_logical_expression(t("x||y"))[0] == {
        "tag": "||",
        "left": {"tag": "<identifier>", "value": "x"},
        "right": {"tag": "<identifier>", "value": "y"},
    }
    assert parse_logical_expression(t("x||y&&z"))[0] == {
        "tag": "||",
        "left": {"tag": "<identifier>", "value": "x"},
        "right": {
            "tag": "&&",
            "left": {"tag": "<identifier>", "value": "y"},
            "right": {"tag": "<identifier>", "value": "z"},
        },
    }


def parse_function_expression(tokens):
    """
    function_expression = "function" identifier_list block_statement;
    """
    assert tokens[0]["tag"] == "function"
    parameters, tokens = parse_identifier_list(tokens[1:])
    body, tokens = parse_block_statement(tokens)
    return {"tag": "function", "parameters": parameters, "body": body}, tokens


def test_parse_function_expression():
    """
    function_expression = "function" identifier_list block_statement;
    """
    ast = parse_function_expression(t("function() {return 1}"))[0]
    assert ast == {
        "tag": "function",
        "parameters": None,
        "body": {
            "tag": "block",
            "statement": {"tag": "return", "value": {"tag": "<number>", "value": 1}},
        },
    }
    ast = parse_function_expression(t("function(x,y) {return x*y}"))[0]
    assert ast == {
        "tag": "function",
        "parameters": {
            "tag": "<identifier>",
            "value": "x",
            "next": {"tag": "<identifier>", "value": "y"},
        },
        "body": {
            "tag": "block",
            "statement": {
                "tag": "return",
                "value": {
                    "tag": "*",
                    "left": {"tag": "<identifier>", "value": "x"},
                    "right": {"tag": "<identifier>", "value": "y"},
                },
            },
        },
    }


def parse_expression(tokens):
    """
    expression = logical_expression;
    """
    return parse_logical_expression(tokens)


def test_parse_expression():
    """
    expression = logical_expression;
    """
    for e in ["x", "x+x", "x||y&&z"]:
        assert parse_expression(t(e))[0] == parse_logical_expression(t(e))[0]


def parse_identifier_list(tokens):
    """
    identifier_list = "(" [ <identifier> { "," <identifier> ] } ")";
    """
    assert tokens[0]["tag"] == "("
    tokens = tokens[1:]
    first_node = None
    if tokens[0]["tag"] != ")":
        assert tokens[0]["tag"] == "<identifier>"
        node = {"tag": "<identifier>", "value": tokens[0]["value"]}
        tokens = tokens[1:]
        first_node = node
        while tokens[0]["tag"] == ",":
            tokens = tokens[1:]
            assert tokens[0]["tag"] == "<identifier>"
            node["next"] = {"tag": "<identifier>", "value": tokens[0]["value"]}
            tokens = tokens[1:]
            node = node["next"]
    assert tokens[0]["tag"] == ")"
    tokens = tokens[1:]
    return first_node, tokens


def test_parse_identifier_list():
    """
    identifier_list = "(" [ <identifier> { "," <identifier> ] } ")";
    """
    tokens = tokenize("()")
    ast, tokens = parse_identifier_list(tokens)
    assert ast == None
    tokens = tokenize("(x)")
    ast, tokens = parse_identifier_list(tokens)
    assert ast == {"tag": "<identifier>", "value": "x"}
    tokens = tokenize("(x,y,z)")
    ast, tokens = parse_identifier_list(tokens)
    assert ast == {
        "tag": "<identifier>",
        "value": "x",
        "next": {
            "tag": "<identifier>",
            "value": "y",
            "next": {"tag": "<identifier>", "value": "z"},
        },
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
        while tokens[0]["tag"] == ",":
            tokens = tokens[1:]
            node["next"], tokens = parse_expression(tokens)
            node = node["next"]
    assert tokens[0]["tag"] == ")"
    tokens = tokens[1:]
    return first_node, tokens


def test_parse_expression_list():
    """
    expression_list = "(" [ expression { "," expression } ] ")";
    """
    tokens = tokenize("()")
    ast, tokens = parse_expression_list(tokens)
    assert ast == None
    tokens = tokenize("(1)")
    ast, tokens = parse_expression_list(tokens)
    assert ast == {"tag": "<number>", "value": 1}
    tokens = tokenize("(1,2,3)")
    ast, tokens = parse_expression_list(tokens)
    assert ast == {
        "tag": "<number>",
        "value": 1,
        "next": {
            "tag": "<number>",
            "value": 2,
            "next": {"tag": "<number>", "value": 3},
        },
    }


def parse_assignment(tokens):
    """
    assignment = <identifier> "=" expression;
    """
    if tokens[0]["tag"] != "<identifier>":
        raise Exception(f"Expected identifier: {tokens[0]}")
    identifier = {"tag": "<identifier>", "value": tokens[0]["value"]}
    tokens = tokens[1:]
    if tokens[0]["tag"] != "=":
        raise Exception(f"Expected '=': {tokens[0]}")
    expression, tokens = parse_expression(tokens[1:])
    return {"tag": "=", "target": identifier, "value": expression}, tokens


def test_parse_assignment():
    """
    assignment = <identifier> "=" expression;
    """
    ast = parse_assignment(t("x=5+3"))[0]
    assert ast == {
        "tag": "=",
        "target": {"tag": "<identifier>", "value": "x"},
        "value": {
            "tag": "+",
            "left": {"tag": "<number>", "value": 5},
            "right": {"tag": "<number>", "value": 3},
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


def test_parse_block_statement():
    """
    block_statement = "{" {";"} [ statement { ";" {";"} statement } {";"} ] "}";
    """
    for code in ["{x=1}", "{x=1;}", "{x=1;;}", "{;;x=1;;}"]:
        ast = parse_block_statement(t(code))[0]
        assert ast == {
            "tag": "block",
            "statement": {
                "tag": "=",
                "target": {"tag": "<identifier>", "value": "x"},
                "value": {"tag": "<number>", "value": 1},
            },
        }
    for code in ["{x=1;y=2}", "{x=1;y=2;}", "{x=1;;y=2;}", "{;x=1;;y=2;}"]:
        ast = parse_block_statement(t(code))[0]
        assert ast == {
            "tag": "block",
            "statement": {
                "tag": "=",
                "target": {"tag": "<identifier>", "value": "x"},
                "value": {"tag": "<number>", "value": 1},
            },
            "next": {
                "tag": "block",
                "statement": {
                    "tag": "=",
                    "target": {"tag": "<identifier>", "value": "y"},
                    "value": {"tag": "<number>", "value": 2},
                },
            },
        }
    ast = parse_block_statement(t("{x=1;y=2;z=3}"))[0]
    assert ast == {
        "tag": "block",
        "statement": {
            "tag": "=",
            "target": {"tag": "<identifier>", "value": "x"},
            "value": {"tag": "<number>", "value": 1},
        },
        "next": {
            "tag": "block",
            "statement": {
                "tag": "=",
                "target": {"tag": "<identifier>", "value": "y"},
                "value": {"tag": "<number>", "value": 2},
            },
            "next": {
                "tag": "block",
                "statement": {
                    "tag": "=",
                    "target": {"tag": "<identifier>", "value": "z"},
                    "value": {"tag": "<number>", "value": 3},
                },
            },
        },
    }
    ast = parse_block_statement(t("{return 1}"))[0]
    assert ast == {
        "tag": "block",
        "statement": {"tag": "return", "value": {"tag": "<number>", "value": 1}},
    }
    assert (
        parse_block_statement(t("{x=1;y=2}"))[0]
        == parse_block_statement(t("{x=1;y=2;}"))[0]
    )


def parse_if_statement(tokens):
    """
    if_statement = "if" "(" expression ")" statement "else" statement;
    """
    assert tokens[0]["tag"] == "if"
    tokens = tokens[1:]
    if tokens[0]["tag"] != "(":
        raise Exception(f"Expected '(': {tokens[0]}")
    condition, tokens = parse_expression(tokens[1:])
    if tokens[0]["tag"] != ")":
        raise Exception(f"Expected ')': {tokens[0]}")
    then_statement, tokens = parse_statement(tokens[1:])
    node = {
        "tag": "if",
        "condition": condition,
        "then": then_statement,
    }
    if tokens[0]["tag"] == "else":
        node["else"], tokens = parse_statement(tokens[1:])
    return node, tokens


def test_parse_if_statement():
    """
    if_statement = "if" "(" expression ")" statement "else" statement;
    """
    ast = parse_if_statement(t("if(1)x=1"))[0]
    assert ast == {
        "tag": "if",
        "condition": {"tag": "<number>", "value": 1},
        "then": {
            "tag": "=",
            "target": {"tag": "<identifier>", "value": "x"},
            "value": {"tag": "<number>", "value": 1},
        },
    }
    ast = parse_if_statement(t("if(1){x=1}"))[0]
    assert ast == {
        "tag": "if",
        "condition": {"tag": "<number>", "value": 1},
        "then": {
            "tag": "block",
            "statement": {
                "tag": "=",
                "target": {"tag": "<identifier>", "value": "x"},
                "value": {"tag": "<number>", "value": 1},
            },
        },
    }
    ast = parse_if_statement(t("if(1){x=1}else{x=3}"))[0]
    assert ast == {
        "tag": "if",
        "condition": {"tag": "<number>", "value": 1},
        "then": {
            "tag": "block",
            "statement": {
                "tag": "=",
                "target": {"tag": "<identifier>", "value": "x"},
                "value": {"tag": "<number>", "value": 1},
            },
        },
        "else": {
            "tag": "block",
            "statement": {
                "tag": "=",
                "target": {"tag": "<identifier>", "value": "x"},
                "value": {"tag": "<number>", "value": 3},
            },
        },
    }


def parse_while_statement(tokens):
    """
    while_statement = "while" "(" expression ")" statement;
    """
    assert tokens[0]["tag"] == "while"
    tokens = tokens[1:]
    if tokens[0]["tag"] != "(":
        raise Exception(f"Expected '(': {tokens[0]}")
    condition, tokens = parse_expression(tokens[1:])
    if tokens[0]["tag"] != ")":
        raise Exception(f"Expected '(': {tokens[0]}")
    statement, tokens = parse_statement(tokens[1:])
    return {"tag": "while", "condition": condition, "do": statement}, tokens


def test_parse_while_statement():
    """
    while_statement = "while" "(" expression ")" statement;
    """
    ast = parse_while_statement(t("while(1)x=1"))[0]
    assert ast == {
        "tag": "while",
        "condition": {"tag": "<number>", "value": 1},
        "do": {
            "tag": "=",
            "target": {"tag": "<identifier>", "value": "x"},
            "value": {"tag": "<number>", "value": 1},
        },
    }


def parse_return_statement(tokens):
    """
    return_statement = "return" [ expression ];
    """
    assert tokens[0]["tag"] == "return"
    tokens = tokens[1:]
    if tokens[0]["tag"] in ["}", ";", None]:
        value = None
        return {"tag": "return"}, tokens
    else:
        value, tokens = parse_expression(tokens)
        return {"tag": "return", "value": value}, tokens


def test_parse_return_statement():
    """
    return_statement = "return" [ expression ];
    """
    ast = parse_return_statement(t("return"))[0]
    assert ast == {"tag": "return"}
    ast = parse_return_statement(t("return}12"))[0]
    assert ast == {"tag": "return"}
    ast = parse_return_statement(t("return;34"))[0]
    assert ast == {"tag": "return"}
    ast = parse_return_statement(t("return 5"))[0]
    assert ast == {"tag": "return", "value": {"tag": "<number>", "value": 5}}
    ast = parse_return_statement(t("return (5)"))[0]
    assert ast == {"tag": "return", "value": {"tag": "<number>", "value": 5}}


def parse_print_statement(tokens):
    """
    print_statement = "print" expression_list;
    """
    assert tokens[0]["tag"] == "print"
    tokens = tokens[1:]
    arguments, tokens = parse_expression_list(tokens)
    return {"tag": "print", "arguments": arguments}, tokens


def test_parse_print_statement():
    """
    print_statement = "print" expression_list;
    """
    ast = parse_print_statement(t("print()"))[0]
    assert ast == {"tag": "print", "arguments": None}
    ast = parse_print_statement(t("print(1)"))[0]
    assert ast == {"tag": "print", "arguments": {"tag": "<number>", "value": 1}}
    ast = parse_print_statement(t("print(1,2+3)"))[0]
    assert ast == {
        "tag": "print",
        "arguments": {
            "tag": "<number>",
            "value": 1,
            "next": {
                "tag": "+",
                "left": {"tag": "<number>", "value": 2},
                "right": {"tag": "<number>", "value": 3},
            },
        },
    }


def parse_function_statement(tokens):
    """
    function_statement = "function" <identifier> identifier_list block_statement;
    """
    # rewrites the token stream as an assignment
    assert tokens[0]["tag"] == "function"
    function_token = tokens[0]
    assert tokens[1]["tag"] == "<identifier>"
    identifier_token = tokens[1]
    assignment_token = {"tag": "=", "position": function_token["position"]}
    tokens = [
        identifier_token,
        assignment_token,
        function_token,
    ] + tokens[2:]
    # parse the rewritten token stream as an assignment
    return parse_assignment(tokens)


def test_parse_function_statement():
    """
    function_statement = "function" <identifier> identifier_list block_statement;
    """
    assignment = t("sq = function(x) {return x*x;}")
    ast_assignment = parse_assignment(assignment)[0]
    statement = t("function sq(x) {return x*x;}")
    ast_statement = parse_function_statement(statement)[0]
    # assert parse_function_statement(statement)[0] == parse_assignment(assignment)[0]


def parse_statement(tokens):
    """
    statement = block_statement | if_statement | while_statement |  function_statement | return_statement |  assignment | expression;
    """
    tag = tokens[0]["tag"]
    # note: none of these consumes a token
    if tag == "if":
        return parse_if_statement(tokens)
    if tag == "while":
        return parse_while_statement(tokens)
    if tag == "function":
        if tokens[1]["tag"] == "<identifier>":
            return parse_function_statement(tokens)
    if tag == "return":
        return parse_return_statement(tokens)
    if tag == "print":
        return parse_print_statement(tokens)
    if tag == "{":
        return parse_block_statement(tokens)
    if tag == "<identifier>":
        # lookahead to next tag to check for assignment
        if tokens[1]["tag"] == "=":
            return parse_assignment(tokens)
    return parse_expression(tokens)


def test_parse_statement():
    """
    statement = block_statement | if_statement | while_statement |  function_statement | return_statement | print_statement | assignment | expression;
    """
    # block statement
    assert (
        parse_statement(t("{x=4;y=5;}"))[0] == parse_block_statement(t("{x=4;y=5;}"))[0]
    )
    # if statement
    assert parse_statement(t("if(1){x=3}"))[0] == parse_if_statement(t("if(1){x=3}"))[0]
    # while statement
    assert (
        parse_statement(t("while(1){x=3}"))[0]
        == parse_while_statement(t("while(1){x=3}"))[0]
    )
    # function_statement (syntactic sugar)
    assert (
        parse_statement(t("function sq(x) {return x}"))[0]
        == parse_function_statement(t("function sq(x) {return x}"))[0]
    )
    # verify standalone function expressions
    assert (
        parse_statement(t("function(x) {return x}"))[0]
        == parse_expression(t("function(x) {return x}"))[0]
    )
    # return statement
    assert (
        parse_statement(t("return 22;"))[0]
        == parse_return_statement(t("return 22;"))[0]
    )
    # print statement
    assert (
        parse_statement(t("print(1,2,3);"))[0]
        == parse_print_statement(t("print(1,2,3)"))[0]
    )
    # assignment statements
    assert parse_statement(t("x=5+3"))[0] == parse_assignment(t("x=5+3"))[0]
    # expression statements
    assert parse_statement(t("5+3"))[0] == parse_expression(t("5+3"))[0]


def parse(tokens):
    """
    program = statement
    """
    tokens.append({"tag": None})  # Sentinel to mark the end of input
    ast, _ = parse_statement(tokens)
    return ast


def test_parse():
    """
    program = statement
    """
    assert parse(tokenize("1 || 0 && 1")) == parse_statement(t("1 || 0 && 1"))[0]


def format(ast, indent=0):
    indentation = " " * indent
    if ast["tag"] in ["<number>", "<boolean>", "<identifier>"]:
        return indentation + str(ast["value"])
    result = indentation + ast["tag"]
    for attribute in [
        "left",
        "right",
        "target",
        "value",
        "while",
        "do",
        "if",
        "then",
        "else",
    ]:
        if attribute in ast:
            result = result + "\n" + format(ast[attribute], indent=indent + 4)
    return result


def test_format():
    tokens = tokenize("4-(2/1)")
    ast = parse(tokens)
    result = format(ast)
    assert result == "-\n    4\n    /\n        2\n        1"
    tokens = tokenize("4-(x/y)")
    ast = parse(tokens)
    result = format(ast)
    assert result == "-\n    4\n    /\n        x\n        y"
    tokens = tokenize("z=4-(x/y)")
    ast = parse(tokens)
    result = format(ast)
    assert (
        result == "=\n    z\n    -\n        4\n        /\n            x\n            y"
    )


if __name__ == "__main__":
    for f in [
        test_parse_arithmetic_factor,
        test_parse_arithmetic_term,
        test_parse_arithmetic_expression,
        test_parse_relational_expression,
        test_parse_logical_factor,
        test_parse_logical_term,
        test_parse_logical_expression,
        test_parse_function_expression,
        test_parse_expression,
        test_parse_identifier_list,
        test_parse_expression_list,
        test_parse_assignment,
        test_parse_block_statement,
        test_parse_if_statement,
        test_parse_while_statement,
        test_parse_return_statement,
        test_parse_print_statement,
        test_parse_function_statement,
        test_parse_statement,
        test_parse,
    ]:
        rule = f.__doc__.strip()
        print("testing", rule.split(" = ")[0])
        assert rule in grammar, f"rule [[[ {rule} ]]] not in grammar."
        grammar = grammar.replace(rule + "\n", "")
        f()
    if grammar.strip() != "":
        print(f"Untested grammar = [[[ {grammar} ]]]")
    print("testing format(ast)...")
    test_format()
    print("done.")
