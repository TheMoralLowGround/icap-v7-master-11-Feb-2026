import traceback


def split_decimal(s, last_occurrence, input_type):
    """This function splits a decimal string (float) string
    Example: Input : 500.00 output [500, 00]
    Either on the third from the last or fourth from the last digit"""

    r = None
    number_of_digits_after_decimal = (len(s) - last_occurrence) - 1
    if input_type == ".":
        if number_of_digits_after_decimal == 2:
            r = s[-2:]
            s = s[:-2]

        elif number_of_digits_after_decimal == 3:
            r = s[-3:]
            s = s[:-3]
        return [s, r]
    else:

        if number_of_digits_after_decimal == 2:
            r = "." + s[-2:]
            s = s[:-2]
            # return [s, r]

        elif number_of_digits_after_decimal == 3:
            # print(s)
            r = "." + s[-3:]
            s = s[:-3]

        elif number_of_digits_after_decimal == 1:
            r = "." + s[-1]
            s = s[:-2]

        return [s, r]


def cw1_conversion(s):
    s = s.strip()  # Strip leading and trailing whitespace
    s = s.replace(" ", "")  # Remove any spaces within the string
    
    # Check if the input ends with a comma, and remove it if true
    if s[-1] == ",":
        s = s[:-1]

    if "." in s:
        s = s.replace(".", "")
    if "," in s:
        s = s.replace(",", ".")
    
    

    return s



def check_digit(input_text):
    return any(char.isdigit() for char in input_text)


def apply_convert_decimals_to_cw1(input_text):

    input_text = input_text.strip()
    if not check_digit(input_text):
        return input_text

    try:
        if input_text:
            input_text = cw1_conversion(input_text)
            
        return input_text
    except:
        print(traceback.print_exc())
        return input_text
    
