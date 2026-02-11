import traceback

from price_parser import Price

# version - 1.01.08022023


def negative_value_checker(input_value):
    negative = False
    if "CR" in input_value:
        negative = True

    if "(" and ")" in input_value:
        negative = True

    if "-" in input_value:
        negative = True

    return negative


def process(input_text, currency_dict):
    try:
        negative = negative_value_checker(input_text)

        price = Price.fromstring(input_text)
        currency = price.currency
        value = str(price.amount)

        if len(currency) == 1:
            currency = currency_dict[currency]

        if currency:
            if negative:
                value = "-" + value

            return [value, currency]

        return None
    except:
        # print(traceback.print_exc())
        return [input_text]
