import traceback
from datetime import timedelta

from dateutil import parser


def process(input_text, is_european, date_rule):
    """Convert Date converts dates to iso2 standards"""
    try:
        if date_rule != None:
            try:
                date_rule = date_rule.replace(" ", "")
                date_rule = int(date_rule)
                date = str(
                    parser.parse(input_text, dayfirst=is_european)
                    + timedelta(days=date_rule)
                )
            except:
                date = str(parser.parse(input_text, dayfirst=is_european))
        else:
            date = str(parser.parse(input_text, dayfirst=is_european))

        date = date.replace(" ", "T") + "+00:00"

        return date

    except:
        #print(traceback.print_exc())
        return input_text
