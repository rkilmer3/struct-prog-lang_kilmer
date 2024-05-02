def evaluate(ast, environment):

    # None
    if ast == None:
        return None, False

    # simple values
    if ast["tag"] == "<number>":
        assert type(ast["value"]) in [
            float,
            int,
        ], f"unexpected ast numeric value {ast['value']} type is a {type(ast['value'])}."
        return ast["value"], False

    if ast["tag"] == "<identifier>":
        assert type(ast["value"]) in [
            str
        ], f"unexpected ast identifer value {ast['value']} type is a {type(ast['value'])}."
        current_environment = environment
        while current_environment:
            if ast["value"] in current_environment:
                return current_environment[ast["value"]], False
            current_environment = current_environment.get("$parent", None)
        assert current_environment, f"undefined identifier {ast['value']} in expression"

    if ast["tag"] == "function":
        return ast, False

    if ast["tag"] == "<function_call>":
        assert "expression" in ast
        assert "arguments" in ast
        function, _ = evaluate(ast["expression"], environment)
        assert function["tag"] == "function"
        assert "parameters" in function
        assert "body" in function
        # match the parameters to arguments
        function_environment = {}
        parameters = function["parameters"]
        arguments = ast["arguments"]
        while parameters:
            assert arguments
            arg, _ = evaluate(arguments, environment)
            function_environment[parameters["value"]] = arg
            parameters = parameters.get("next", None)
            arguments = arguments.get("next", None)
        assert parameters == None
        assert arguments == None
        function_environment["$parent"] = environment
        result, returning = evaluate(function["body"], function_environment)
        return result, returning

    if ast["tag"] == "return":
        value, _ = evaluate(ast.get("value",None), environment)
        return value, True

    # unary operations
    if ast["tag"] == "negate":
        value, _ = evaluate(ast["value"], environment)
        return -value, False

    if ast["tag"] == "not":
        value, _ = evaluate(ast["value"], environment)
        if value:
            value = 0
        else:
            value = 1
        return value, False

    # binary operations
    if ast["tag"] == "+":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return left_value + right_value, False
    if ast["tag"] == "-":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return left_value - right_value, False
    if ast["tag"] == "*":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return left_value * right_value, False
    if ast["tag"] == "/":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        # Add error handling for division by zero
        if right_value == 0:
            raise Exception("Division by zero")
        return left_value / right_value, False
    if ast["tag"] == "*":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return left_value * right_value, False
    if ast["tag"] == "<":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return int(left_value < right_value), False
    if ast["tag"] == ">":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return int(left_value > right_value), False
    if ast["tag"] == "<=":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return int(left_value <= right_value), False
    if ast["tag"] == ">=":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return int(left_value >= right_value), False
    if ast["tag"] == "==":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return int(left_value == right_value), False
    if ast["tag"] == "!=":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return int(left_value != right_value), False
    if ast["tag"] == "&&":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return int(left_value and right_value), False
    if ast["tag"] == "||":
        left_value, _ = evaluate(ast["left"], environment)
        right_value, _ = evaluate(ast["right"], environment)
        return int(left_value or right_value), False

    if ast["tag"] == "block":
        value, returning = evaluate(ast["statement"], environment)
        if ast.get("next") and not returning:
            value, returning = evaluate(ast["next"], environment)
        if returning:
            return value, returning
        else:
            return None, False

    if ast["tag"] == "if":
        condition, _ = evaluate(ast["condition"], environment)
        if condition:
            value, returning = evaluate(ast["then"], environment)
            if returning:
                return value, returning
            else:
                return None, False
        else:
            if ast.get("else", None):
                value, returning = evaluate(ast["else"], environment)
                if returning:
                    return value, returning
                else:
                    return None, False
            return None, False

    if ast["tag"] == "while":
        condition, _ = evaluate(ast["condition"], environment)
        while condition:
            value, returning = evaluate(ast["do"], environment)
            if returning:
                return value, returning
            condition, _ = evaluate(ast["condition"], environment)
        return None, False

    if ast["tag"] == "print":
        argument = ast.get("arguments", None)
        while argument:
            value, _ = evaluate(argument, environment)
            print(value, end=" ")
            argument = argument.get("next", None)
        print()
        return None, False

    if ast["tag"] == "=":
        assert (
            ast["target"]["tag"] == "<identifier>"
        ), f"ERROR: Expecting identifier in assignment statement."
        identifier = ast["target"]["value"]
        assert ast["value"], f"ERROR: Expecting expression in assignment statement."
        value, _ = evaluate(ast["value"], environment)
        environment[identifier] = value
        return None, False
    raise Exception(f"Unknown operation: {ast['tag']}")


from tokenizer import tokenize
from parser import parse


def equals(code, environment, expected_result, expected_environment=None):
    result, returning = evaluate(parse(tokenize(code)), environment)
    assert (
        result == expected_result
    ), f"""ERROR: When executing-- 
    {[code]},
    --expected--
    {[expected_result]},
    --got--
    {[result]}."""
    if expected_environment:
        assert (
            environment == expected_environment
        ), f"""
        ERROR: When executing 
        {[code]}, 
        expected
        {[expected_environment]},\n got \n{[environment]}.
        """


def test_evaluate_single_value():
    print("test evaluate single value")
    equals("4", {}, 4, {})


def test_evaluate_single_identifier():
    print("test evaluate single identifier")
    equals("x", {"x": 3}, 3)
    equals("y", {"x": 3, "$parent": {"y": 4}}, 4)
    equals("z", {"x": 3, "$parent": {"y": 4, "$parent": {"z": 5}}}, 5)


def test_evaluate_simple_assignment():
    print("test evaluate simple assignment")
    equals("x=3", {}, None, {"x": 3})


def test_evaluate_simple_addition():
    print("test evaluate simple addition")
    equals("1 + 3", {}, 4)
    equals("1 + 4", {}, 5)


def test_evaluate_complex_expression():
    print("test evaluate complex expression")
    equals("(1+2)*(3+4)", {}, 21)


def test_evaluate_subtraction():
    print("test evaluate subtraction.")
    equals("11-5", {}, 6)


def test_evaluate_division():
    print("test evaluate division.")
    equals("15/5", {}, 3)


def test_evaluate_unary_operators():
    print("test evaluate unary operators.")
    equals("-5", {}, -5)
    equals("!0", {}, 1)
    equals("!1", {}, 0)


def test_evaluate_relational_operators():
    print("test evaluate relational operators.")
    equals("2<3", {}, 1)
    equals("4==4", {}, 1)
    equals("4==1", {}, 0)


def test_evaluate_logical_operators():
    print("test evaluate logical operators.")
    equals("1==1", {}, 1)
    equals("1!=1", {}, 0)
    equals("1&&1", {}, 1)
    equals("1&&0", {}, 0)
    equals("0&&0", {}, 0)
    equals("1||1", {}, 1)
    equals("1||0", {}, 1)
    equals("0||0", {}, 0)
    equals("!1", {}, 0)
    equals("!0", {}, 1)


def test_evaluate_division_by_zero():
    print("test evaluate division by zero.")
    try:
        equals("1/0", {}, None)
        assert False, "Expected a division by zero error"
    except Exception as e:
        assert str(e) == "Division by zero"


def test_evaluate_if_statement():
    print("test evaluate if statement.")
    equals("if (1) x=4", {"x": 0}, None, {"x": 4})


def test_evaluate_while_statement():
    print("test evaluate while statement.")
    equals("while (0) x=4", {"x": 0}, None, {"x": 0})
    equals("while (x>0) {x=x-1;y=y+1}", {"x": 3, "y": 0}, None, {"x": 0, "y": 3})


def test_evaluate_block_statement():
    print("test evaluate block statement.")
    equals("{x=4}", {}, None, {"x": 4})
    equals("{x=4; y=3}", {}, None, {"x": 4, "y": 3})
    equals("{x=4; y=3; y=1}", {}, None, {"x": 4, "y": 1})
    equals("{x=3; y=0; while (x>0) {x=x-1;y=y+1}}", {}, None, {"x": 0, "y": 3})


def test_evaluate_function_expression():
    print("test evaluate function_expression.")
    equals(
        "function(x) {return x}",
        None,
        {
            "tag": "function",
            "parameters": {"tag": "<identifier>", "value": "x"},
            "body": {
                "tag": "block",
                "statement": {
                    "tag": "return",
                    "value": {"tag": "<identifier>", "value": "x"},
                },
            },
        },
        None,
    )
    equals(
        "f = function(x) {return x}",
        {},
        None,
        {
            "f": {
                "tag": "function",
                "parameters": {"tag": "<identifier>", "value": "x"},
                "body": {
                    "tag": "block",
                    "statement": {
                        "tag": "return",
                        "value": {"tag": "<identifier>", "value": "x"},
                    },
                },
            },
        },
    )


def test_evaluate_function_statement():
    print("test evaluate function_statement.")
    equals(
        "function f(x) {return x}",
        {},
        None,
        {
            "f": {
                "tag": "function",
                "parameters": {"tag": "<identifier>", "value": "x"},
                "body": {
                    "tag": "block",
                    "statement": {
                        "tag": "return",
                        "value": {"tag": "<identifier>", "value": "x"},
                    },
                },
            },
        },
    )

def test_evaluate_print_statement():
    print("test evaluate print_statement.")
    equals("print()", {}, None, None)
    equals("print(1)", {}, None, None)
    equals("print(1,2)", {}, None, None)
    equals("print(1,2,3+4)", {}, None, None)


def test_evaluate_return_statement():
    print("test evaluate return statement.")
    code = "return"
    result, returning = evaluate(parse(tokenize(code)), {})
    assert returning
    assert result == None

    code = "return 1"
    result, returning = evaluate(parse(tokenize(code)), {})
    assert returning
    assert result == 1

    code = "{x=2; return x;}"
    result, returning = evaluate(parse(tokenize(code)), {})
    assert returning
    assert result == 2

    code = "if (1) {x=2; return x;}"
    result, returning = evaluate(parse(tokenize(code)), {})
    assert returning
    assert result == 2

    code = "{x=0; while(x<10) {x=3; return x;}}"
    result, returning = evaluate(parse(tokenize(code)), {})
    assert returning
    assert result == 3

def test_evaluate_function_call():
    print("test evaluate function call.")
    def ev(code, environment):
        return evaluate(parse(tokenize(code)), environment)
    environment = {}
    result, _ = ev("f = function() {return}", environment)
    result, _ = ev("f()", environment)
    assert result == None
    result, _ = ev("f = function(x) {return x}", environment)
    result, _ = ev("f(1)", environment)
    assert result == 1
    result, _ = ev("f = function(x) {return x + x}", environment)
    result, _ = ev("f(1)", environment)
    assert result == 2
    result, _ = ev("f = function(x,y) {return x * y}", environment)
    result, _ = ev("f(1,2)", environment)
    assert result == 2
    result, _ = ev("f(2,3)", environment)
    assert result == 6
    result, _ = ev("function g(x,y) {return x * y + 1}", environment)
    result, _ = ev("g(1,2)", environment)
    assert result == 3
    result, _ = ev("g(2,3)", environment)
    assert result == 7
    result, _ = ev("f(1,2) + g(1,2)", environment)
    assert result == 5
    result, _ = ev("f(2,3) + g(2,3)", environment)
    assert result == 13

def test_evaluate_square_root_function():
    print("test evaluate square root function.")
    def ev(code, environment):
        return evaluate(parse(tokenize(code)), environment)
    environment = {}
    code = """
        function abs(x) {
            if (x > 0) { return x; } else {return -x;}
        }
    """
    result, _ = ev(code, environment)
    result, _ = ev("abs(2)", environment)
    assert result == 2
    result, _ = ev("abs(-3)", environment)
    assert result == 3
    code = """
        function squareRoot(number) {
            guess = number / 2;
            while (abs(guess * guess - number) > tolerance) {
                guess = (guess + number / guess) / 2; 
            };
            return guess;
        }    
    """
    result, _ = ev(code, environment)
    result, _ = ev("tolerance = 0.00000001;", environment)
    result, _ = ev("squareRoot(16);", environment)
    print([result])
    result, _ = ev("print(squareRoot(16));", environment)
    result, _ = ev("print(squareRoot(9));", environment)
    result, _ = ev("print(squareRoot(4));", environment)
    result, _ = ev("print(tolerance);", environment)

def test_evaluate_expression_function_call():
    print("test evaluate expression_function_call.")
    def ev(code, environment):
        return evaluate(parse(tokenize(code)), environment)
    environment = {}
    code = """
        function abs(x) {
            if (x > 0) { return x; } else {return -x;}
        }
    """
    result, _ = ev(code, environment)
    result, _ = ev("abs(-2)", environment)
    assert result == 2
    code = """
        function absf() {
            return abs
        }
    """
    result, _ = ev(code, environment)
    result, _ = ev("absf", environment)
    result, _ = ev("absf()", environment)
    result, _ = ev("absf()(-3)", environment)
    print(result)
    result, _ = ev("function(x) {return x*x} (4)", environment)
    print(result)

 
if __name__ == "__main__":
    print("test evaluator...")
    test_evaluate_single_value()
    test_evaluate_single_identifier()
    test_evaluate_simple_addition()
    test_evaluate_simple_assignment()
    test_evaluate_complex_expression()
    test_evaluate_subtraction()
    test_evaluate_division()
    test_evaluate_division_by_zero()
    test_evaluate_unary_operators()
    test_evaluate_relational_operators()
    test_evaluate_logical_operators()
    test_evaluate_if_statement()
    test_evaluate_while_statement()
    test_evaluate_block_statement()
    test_evaluate_function_expression()
    test_evaluate_function_statement()
    test_evaluate_print_statement()
    test_evaluate_return_statement()
    test_evaluate_function_call()
    test_evaluate_square_root_function()
    test_evaluate_expression_function_call()

    print("done.")
