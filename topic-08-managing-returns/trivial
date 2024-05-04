#!/usr/bin/env python

import sys
import readline
from tokenizer import tokenize
from parser import parse, format
from evaluator import evaluate


def repl(eval):
    environment = {}
    status = {
        "interactive": True,
        "force_interactive": False,
        "show_environment": False,
    }
    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            continue
        if arg == "-e":
            status["show_environment"] = True
        if arg == "-i":
            if sys.stdin.isatty():
                status["force_interactive"] = True
            else:
                print("Can't use -i to force interaction with redirected input.")
                exit(1)

    # process any source files provided
    for arg in sys.argv[1:]:
        if arg.startswith("-"):
            continue
        with open(arg, "r") as f:
            source_code = f.read()
            environment = eval(source_code, environment)
            if status["show_environment"]:
                print(environment)
            status["interactive"] = False

    if not sys.stdin.isatty():
        source_code = sys.stdin.read()
        environment = eval(source_code, environment)
        if status["show_environment"]:
            print(environment)
        status["interactive"] = False
        return

    if status["interactive"] or status["force_interactive"]:
        while True:
            try:
                source_line = input("% ")
                if source_line == ".e":
                    status["show_environment"] = not status["show_environment"]
                    if status["show_environment"]:
                        print(environment)
                    continue
                environment = eval(source_line, environment)
                if status["show_environment"]:                  
                    print(environment)
            except EOFError:
                print(" exiting.")
                break
            except KeyboardInterrupt:
                print("^C exiting.")
                break


# evaluation function
def eval(code, environment):
    # wrap code to allow multiple statements
    tokens = tokenize("{" + code + "}")
    ast = parse(tokens)
    _, environment = evaluate(ast, environment)
    return environment

if __name__ == "__main__":
    repl(eval)
