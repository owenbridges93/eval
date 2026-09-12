import argparse 
from decimal import Decimal
import math

"""
potential future ideas: 
- expand new function parsing (injecting parentheses) to unary operators as well
- refactor by integrating oop into algorithms 
- clean up code
- add inline documentation
- add option to use radians in trig functions
- add functions that accept more than one argument
- make debug message indentation more accurate
"""

# Create argparse fields
PARSER = argparse.ArgumentParser(description = 'Evaluate a mathematical expression.')
PARSER.add_argument('-e', '--expression', help = 'The expression to evaluate.')
PARSER.add_argument('-d', '--debug', action = 'store_const', const = 'true', help = 'Whether or not debug mode should be turned on (true/false).')
PARSER.add_argument('-r', '--round', help = 'How many decimal places to round output to (defaults to 3 and can be negative).', default = 3)
ARGS = PARSER.parse_args()

# 
DEBUG = True if ARGS.debug else False
ROUND_OUTPUT_TO = int(ARGS.round)

POSITIVE_OPERATIONS = {
    '+' : lambda a, b: a + b,
    '-' : lambda a, b: a - b,
    '*' : lambda a, b: a * b,
    '**' : lambda a, b: a ** b,
    '^' : lambda a, b: a ** b,
    '/' : lambda a, b: a / b,
    '//' : lambda a, b: a // b,
    '%' : lambda a, b: a % b,
    '!' : lambda a: a * POSITIVE_OPERATIONS['!'](a - 1) if a > 1 else 1
}

UNARY_ALONE_OPERATORS = ['!']

UNARY_CONCAT_OTHER = []

for operator in UNARY_ALONE_OPERATORS:
    UNARY_CONCAT_OTHER.extend([operator + op for op in POSITIVE_OPERATIONS if op not in UNARY_ALONE_OPERATORS])

UNARY_OPERATORS = UNARY_ALONE_OPERATORS + UNARY_CONCAT_OTHER

UNARY_CONCAT_OPERATIONS = {symbol: lambda a, b, symbol=symbol: POSITIVE_OPERATIONS[symbol[1]](POSITIVE_OPERATIONS[symbol[0]](a), b) for symbol in UNARY_CONCAT_OTHER}

NEGATIVE_OPERATIONS = {symbol + '-': lambda a, b, symbol=symbol: POSITIVE_OPERATIONS[symbol](a, -b) for symbol in POSITIVE_OPERATIONS if symbol not in UNARY_OPERATORS}

FUNCTIONS = { # implement min max 
    'sin' : lambda a: Decimal(math.sin(a*Decimal(math.pi)/180)),
    'cos' : lambda a: Decimal(math.cos(a*Decimal(math.pi)/180)),
    'tan' : lambda a: Decimal(math.tan(a*Decimal(math.pi)/180)),
    'sqrt' : lambda a: Decimal(math.sqrt(a))
}

FUNCTION_CHARS = []

for func in FUNCTIONS:
    FUNCTION_CHARS.extend(list(func))

OPERATIONS = POSITIVE_OPERATIONS | NEGATIVE_OPERATIONS | UNARY_CONCAT_OPERATIONS | FUNCTIONS

PEMDAS = [
    ('!'),
    ('^', '**'),
    ('*', '/', '//', '%'), 
    ('+', '-')
]

for index, precedence in enumerate(PEMDAS):
    newops = [item for item in precedence]

    for op in precedence:
        if op in UNARY_ALONE_OPERATORS:
            for sub_op in POSITIVE_OPERATIONS:
                if sub_op not in UNARY_ALONE_OPERATORS:
                    newops.append(op + sub_op)
        else:
            newops.append(op + "-")
    
    PEMDAS[index] = tuple(newops)

OPERATORS_IN_PEMDAS = []

for precedence in PEMDAS:
    OPERATORS_IN_PEMDAS.extend(precedence)

PEMDAS.insert(0, tuple(FUNCTIONS.keys()))

DIGITS = "1234567890."

VALID_CHARS = set(OPERATIONS) | set(DIGITS) | {'(', ')'} | set(FUNCTION_CHARS)

def debug_message(*args, indent = 0):
    if DEBUG:
        message = ' '.join([str(item) for item in args])

        print('[DEBUG]', ' ' * indent * 2, message)

def find_phrases(STRING, POSSIBLE_CHARS):
    phrases = ['']

    for char in STRING:
        if char in POSSIBLE_CHARS:
            phrases[-1] += char
        else:
            phrases.append('')

    for _ in range(phrases.count('')):
        phrases.remove('')

    return phrases

def parse_expression(expression):
    expression = expression.strip(" \'\"")

    expression = list(expression)

    insertions = 0
    exp_copy = expression[:]

    for index, char in enumerate(exp_copy[:-1]):
        if char == '-' and (index == 0 or exp_copy[index - 1] == '('):
                expression.insert(index + insertions, '0')
                insertions += 1

    expression = ''.join(expression)

    expression_numbers = find_phrases(expression, DIGITS)
    expression_operations = find_phrases(expression, list(OPERATIONS.keys()) + FUNCTION_CHARS)

    debug_message('parse_expression:', expression, expression_numbers, expression_operations, indent = 4)

    for i in range(len(expression_numbers)):
        expression_numbers[i] = Decimal(expression_numbers[i])

    if not set(expression) <= VALID_CHARS:
        raise Exception("INVALID CHARACTERS DETECTED")

    for item in expression_operations:
        if len(item) > 1 and not (item in OPERATIONS or item in UNARY_OPERATORS or item in FUNCTIONS) :
            raise Exception("INVALID FUNCTION / OPERATOR")

        if item not in OPERATORS_IN_PEMDAS:
            raise Exception("FUNCTION / OPERATOR NOT IN ORDER OF OPERATIONS")

    if not expression.count('(') == expression.count(')'):
        raise Exception("MISMATCHED PARENTHESES")

    NUM_UNARY_OPERATORS = sum(expression_operations.count(operation) for operation in UNARY_ALONE_OPERATORS)
    NUM_FUNCTIONS = sum(expression_operations.count(operation) for operation in FUNCTIONS)
    if not len(expression_numbers) - len(expression_operations) + NUM_UNARY_OPERATORS + NUM_FUNCTIONS == 1:
        raise Exception("WRONG RATIO OF NUMBERS TO OPERATORS")

    return expression_numbers, expression_operations

def perform_operation(OPERATION, A, B=None):
    A = Decimal(A)

    if B:
        B = Decimal(B)

        result = OPERATIONS[OPERATION](A, B)
    else:
        result = OPERATIONS[OPERATION](A)

    return f'{result:.{len(str(result))}f}'

def simplify(expression_numbers, expression_operations):
    debug_message("simplify:", expression_numbers, expression_operations, indent = 5)

    for precedence in PEMDAS:
        for index, operator in enumerate(expression_operations):
            if operator in precedence:
                if operator in set(UNARY_ALONE_OPERATORS) | set(FUNCTIONS):
                    num = perform_operation(operator, expression_numbers[index])
                else:
                    num = perform_operation(operator, expression_numbers[index], expression_numbers[index + 1])

                    expression_numbers.pop(index + 1)

                expression_numbers[index] = num
                expression_operations.pop(index)

                return simplify(expression_numbers, expression_operations)

    return expression_numbers[0]

def evaluate_basic(EXPRESSION):
    EXPRESSION_NUMBERS, EXPRESSION_OPERATIONS = parse_expression(EXPRESSION)
    return simplify(EXPRESSION_NUMBERS, EXPRESSION_OPERATIONS)

def traverse_parentheses(expression):
    debug_message('traverse_parentheses:', expression, indent = 2)

    memory = {}
    depth = 0

    for index, char in enumerate(expression):
        if char == '(':
            depth += 1
            memory[depth] = index

        if char == ')':
            open_index = memory[depth]
            close_index = index

            return traverse_parentheses(expression[:open_index] + str(traverse_parentheses(expression[open_index + 1:close_index])) + expression[close_index + 1:])

    expression = resolve_functions(expression)

    return evaluate_basic(expression)

def resolve_functions(expression):
    debug_message('resolve_functions:', expression, indent = 3)

    EXPRESSION_FUNCTIONS = find_phrases(expression, FUNCTION_CHARS)

    if not EXPRESSION_FUNCTIONS:
        return expression

    EXPRESSION_FUNCTION_CALL_COUNTS = {f : 0 for f in EXPRESSION_FUNCTIONS}
    EXPRESSION_FUNCTION_CALLS = []

    for f in EXPRESSION_FUNCTIONS:
        EXPRESSION_FUNCTION_CALLS.append((f, EXPRESSION_FUNCTION_CALL_COUNTS[f]))
        EXPRESSION_FUNCTION_CALL_COUNTS[f] += 1

    call = EXPRESSION_FUNCTIONS[0]
    call_contents = ''

    call_index = expression.index(call)
    contents_start_index = call_index + len(call)

    for char in expression[contents_start_index:]:
        if char not in DIGITS + '-':
            break

        call_contents += char

    call_length = len(call) + len(call_contents)


    if len(EXPRESSION_FUNCTIONS) == 1:
        result = perform_operation(call, call_contents)

        return expression[:call_index] + str(result) + expression[call_index + call_length:]

    return expression[:call_index] + evaluate(call, call_contents) + expression[call_index + call_length:]

def evaluate(expression):
    debug_message('evaluate:', expression, indent = 1)

    expression = list(expression)

    insertions = 0
    exp_copy = expression[:]

    for index in range(len(exp_copy) - 1):
        char = exp_copy[index]
        next_char = exp_copy[index + 1]

        if (char in list(DIGITS) + UNARY_OPERATORS and next_char in ['('] + FUNCTION_CHARS) or (char == ')' and next_char in list(DIGITS) + FUNCTION_CHARS) or (char == ')' and next_char == '('): # Check cases: n(, )n, )(
            expression.insert(index + 1 + insertions, '*')
            insertions += 1            

    expression = ''.join(expression)

    return traverse_parentheses(expression)

def find_and_format_answer(expression):
    debug_message('find_and_format_answer:', expression)

    result = Decimal(evaluate(expression))

    result = round(result, ROUND_OUTPUT_TO)

    result = Decimal(result).normalize()

    return result

if __name__ == '__main__':
    if ARGS.expression:
        try:
            print(find_and_format_answer(ARGS.expression))
        except Exception as ERROR:
            print(f"\nGenius caused {ERROR} error\nDon't be sorry. Be better.\n")

        exit(0)

    else:
        while True:
            try:
                EXPRESSION = input('Input expression: ')

                if EXPRESSION in ['exit', 'close']:
                    break

                print(f'\n{find_and_format_answer(EXPRESSION)}\n')

            except Exception as ERROR:
                print(f"\nGenius caused {ERROR} error\nDon't be sorry. Be better.\n")
