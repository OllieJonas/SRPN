import re  # Imported Regex for identifying what the input is (e.g. number, infix operator, operator, etc.)

# Max and min values for saturation
max_value = 2147483647
min_value = -2147483648

stack = []

# Infix
operator_stack = []

# Commenting
is_in_comment = False

# Random
rand_count = 0
rand_list = []
seed = 1

# Regex
expression_operators_regex = "+\\-*/%^"  # Regex for operators used within (infix) expressions
operators_regex = expression_operators_regex + "=d"  # Regex for operators in general

# Dictionary defining all tokens, with the integer representing the precedence (6 = HIGH, 1 = LOW)
tokens = {
    None: 1,  # Numbers
    '+': 2,
    '-': 2,
    '*': 3,
    '/': 4,
    '%': 5,
    '^': 6
}


# Main method for SRPN
def main():
    populate_random_numbers_list()
    print("You can now start interacting with the SRPN calculator")
    try:
        while True:
            inp = input()
            for i in inp.split():  # Process each text separated by whitespace as a separate command
                process_input(i)

    except (EOFError, KeyboardInterrupt):  # EOF and SIGINT gracefully closes the program
        exit(0)


# Checks for commenting and non-ASCII characters
def process_input(input):
    if input == '#':  # Toggles commenting
        toggle_comment()

    elif not input.isascii():  # Crashes when inputting a non-ASCII character
        crash()

    elif not is_in_comment:  # Disables any input if there's been a hash before this
        process_non_comments(input)


# This function decides whether something is an expression or not, then performs the necessary operations.
# An expression is everything except an operator on its own, d or =.
# It recurses through the string, slicing at the number of characters the thing we're processing consumes.
# preceding_token_is_number is for handling negative numbers vs the operator '-'
def process_non_comments(input, preceding_token_is_number=False):
    if len(input) == 0:  # Terminating case
        if len(operator_stack) > 0:  # Evaluate any outstanding adjacent operators
            evaluate_operator_stack()
        return

    if lookahead_is_expression(input):
        chars_to_consume, preceding_token_is_number = evaluate_expression(input, preceding_token_is_number)

    elif not is_valid_input(input[0]):
        print("Unrecognised operator or operand \"" + input[0] + "\".")
        chars_to_consume = 1

    else:  # If not an expression or invalid input, it has to be either an operator on its own, d or =
        evaluate_postfix_operator(input[0])
        chars_to_consume = 1

    # Recurses back through, slicing at the number of chars consumed by what's been calculated
    process_non_comments(input[chars_to_consume:], preceding_token_is_number)


# Evaluates infix or a number on its own
def evaluate_expression(expression, preceding_token_is_number):
    chars_consumed = 1

    if len(expression) > 43:  # Cuts off infix at 43
        expression = expression[:43]

    if lookahead_is_number(expression, preceding_token_is_number):
        number, chars_consumed = get_next_number(expression)
        append_to_stack(number)
        preceding_token_is_number = True

    elif not lookahead_is_expression(expression):  # Invalid character
        print("Unrecognised operator or operand \"" + expression[0] + "\".")

    elif lookahead_is_expression_operator(expression):
        current_op = expression[0]

        if len(operator_stack) > 0 and not has_precedence(current_op, operator_stack[-1]):  # Infix
            evaluate_operator_stack()

        operator_stack.append(current_op)
        preceding_token_is_number = False
    return chars_consumed, preceding_token_is_number


# Finds the next number by scanning for numbers up until the next operator
# Returns a tuple with the number itself and the number of characters in the number (eg. 9182 -> 9182, 4)
def get_next_number(input):
    if input[0] == 'r':  # Deals with random number
        return generate_random_number(), 1

    match = re.match("^-?[0-9]+", input)  # Gets all numbers up until something that isn't a number
    start, end = match.span()  # Gets starting and ending points of this number
    num_string = input[start:end]

    if is_potential_octal_number(num_string):
        if is_valid_octal_number(num_string):
            num = int(num_string, 8)
            return num, end - start
        else:
            if len(num_string) == 2:  # Bug(?) in legacy: If octal is 2 chars long (including 0), convert it to decimal
                return int(num_string), end - start
            else:
                return None, end - start

    else:
        num = int(num_string)  # Else convert to normal int
        return num, end - start


# Scans through the reversed operator buffer, evaluating with the stack as it goes.
def evaluate_operator_stack():
    reversed_operator_stack = operator_stack[::-1]  # Reverse the operator_stack
    operator_stack.clear()  # Bug causing weird precedence issues... (2+2^2*2 = 12 in legacy, not 10!)

    for ops in reversed_operator_stack:
        evaluate_postfix_operator(ops)


# Performs operations as postfix (including checking input is valid based on the operation, d and =)
def evaluate_postfix_operator(operator):
    # Special operators (i.e. =, d)
    if operator == 'd':
        evaluate_operator_stack()  # If d is found in infix, it evaluates everything before it regardless.
        if len(stack) == 0:
            print(min_value)  # Bug where if nothing in stack, prints min value
        for num in stack:
            print(int(num))  # Stored in stack as floats, printed as ints

    elif operator == '=':
        if len(stack) == 0:
            print("Stack empty.")
        else:
            print(int(stack[-1]))  # Prints top of stack

    # Operation Checks
    else:
        if len(stack) < 2:  # Check the stack is big enough to perform an operation
            print("Stack underflow.")

        elif operator in '/%' and stack[-1] == 0:  # Can't divide by 0
            print("Divide by 0.")

        elif operator == '^' and stack[-1] < 0:  # Prints negative power in original
            print("Negative power.")

        elif operator == '%' and stack[-2] == 0:  # Another bug in original
            crash()

        else:
            try:
                result = evaluate_operator(operator)
            except OverflowError:
                result = max_value
            append_to_stack(result)  # Pushes new result to the stack


# Pops the first 2 items off the stack, then performs the operations
# Takes an operator, returns the result after popping two items off the stack and then performing that operation.
def evaluate_operator(operator):
    rhs = float(stack.pop())  # Pops first item (right hand operand / side) from stack
    lhs = float(stack.pop())  # Pops second item (left hand operand / side) from stack

    # Operator functions
    if operator == '+':
        result = lhs + rhs

    elif operator == '-':
        result = lhs - rhs

    elif operator == '*':
        result = lhs * rhs

    elif operator == '/':
        result = lhs / rhs

    elif operator == '%':
        result = lhs % rhs

    elif operator == '^':
        result = lhs ** rhs
    else:
        result = 0
    return result


# Generates a random number using the list generated by populate_random_number_list()
# Based on an adapted version of this: https://www.mscs.dal.ca/~selinger/random/
def generate_random_number():
    global rand_count
    rand_max = 23  # Maximum value for rand_count
    rand_min = 1  # Minimum value for rand_count

    rand_count += 1

    adjusted_rand_count = (rand_count - rand_min) % (rand_max - rand_min) + rand_min  # Allows wrapping of rand count between 1 and 23

    return convert_to_int32(rand_list[adjusted_rand_count]) >> 1


# Populates a list of random numbers
# Again, based on an adapted version of this: https://www.mscs.dal.ca/~selinger/random/
def populate_random_numbers_list():
    global rand_count
    global rand_list
    global seed

    rand_list.append(seed)

    for n in range(1, 31):
        rand_list.append(16807 * rand_list[n - 1] % max_value)
        if rand_list[n] < 0:
            rand_list[n] += max_value

    for n in range(31, 34):
        rand_list.append(rand_list[n - 31])

    for n in range(34, 366):  # The max amount of values the SRPN will give you before looping back
        rand_list.append(rand_list[(n - 31)] + rand_list[(n - 3)])

    del rand_list[:343]  # We don't care about anything below this as SRPN only loops through 22 different rand numbers


# Converts to a 32 bit integer, allows for intentional wrapping of numbers
def convert_to_int32(num):
    return num & 0xffffffff


# Adds to the stack, and performs the stack overflow check each time.
def append_to_stack(number):
    if len(stack) > 22:  # Checks that the stack isn't going to go over the limit
        print("Stack overflow.")
        return
    if number is not None:
        stack.append(saturate_input(number))  # Adds to the stack


# Checks that the input is within a 32 bit range
def saturate_input(input):
    if input > max_value:
        return max_value
    elif input < min_value:
        return min_value
    return input


# Toggles commenting mode
def toggle_comment():
    global is_in_comment
    is_in_comment = not is_in_comment  # Toggles commenting flag


# Gets if Operator 1 has a precedence over Operator 2
def has_precedence(operator1, operator2):
    return tokens.get(operator1) >= tokens.get(operator2)


# Gets if a number should be converted to octal using Regex
def is_potential_octal_number(num_string):
    return re.match("^-?0[0-9]+$", num_string)


# Gets if a number actually can be converted to octal using Regex
def is_valid_octal_number(num_string):
    return re.match("^-?0[0-7]+$", num_string) is not None


# Returns whether the input is either a positive or a negative number using Regex, or random number 'r'
def is_number(num_string):
    return re.match('^-?[0-9]+$', num_string) is not None or num_string == 'r'  # If signed number or random


# Gets if there is an operator using the operators list and Regex
def is_operator(input):
    return re.match('[' + operators_regex + ']', input) is not None


# Gets if the operator could potentially be a part of an expression (ie. not =, d)
def is_expression_operator(input):
    return re.match('[' + expression_operators_regex + ']', input) is not None


# Only valid input are operators, numbers or d, =
def is_valid_input(input):
    return is_operator(input) or is_number(input)


# Checks to see if a number is the next thing in the input
# Number or negative number and the preceding token isn't a number (so basically it's not x-y, but rather just -y)
def lookahead_is_number(input, preceding_token_is_number=False):
    return len(input) > 0 and is_number(input[0]) or len(input) > 1 and input[0] == '-' and \
           is_number(input[1]) and not preceding_token_is_number


# Evaluates if following characters is an expression ie. anything that will result in a value being pushed onto the
# stack. For example, a number or a (postfix or infix) operator (Note: not = or d) NB: There is a special case,
# where an expression starting with an operator is treated as an infix operation, with the last stack element as its
# first operand (with the exception of -, where the number is treated as a negative)
def lookahead_is_expression(input):
    return lookahead_is_number(input) or lookahead_is_expression_operator(input)


# If next infix character is 0, return true
def lookahead_is_expression_operator(input):
    return is_expression_operator(input[0])


# Method called whenever legacy crashes, although this gracefully exits.
def crash():
    exit(1)


# Run on start
if __name__ == "__main__":
    main()
