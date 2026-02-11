import datetime
import traceback

from dateutil import parser

from .shape_converter import str_to_shape
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def process(date):
    """Convert Date Now will handle multiple types of dates"""
    try:
        if isinstance(date, list):
            new_dates = []
            for d1 in date:
                new_dates.append(process(d1))
            return new_dates
        date_sets = [
            ("%d.%m.%Y", "%m.%d.%Y"),
            ("%d/%m/%Y", "%m/%d/%Y"),
            ("%d-%m-%Y", "%m-%d-%y"),
        ]
        north_america_date = None
        for x, y in date_sets:
            try:
                north_america_date = datetime.datetime.strptime(date, x).strftime(y)
            except:
                pass
        if not north_america_date:
            # For cases where dates were in DD-MM-YY (March 2nd 2023 was denoted as 02-03-23)
            # We do manual intervention here
            try:
                if str_to_shape(date) == "DD-DD-DD":
                    split_date = date.split("-")
                    day = split_date[0]
                    month = split_date[1]
                    if int(month) < 13:  # Checking if the month is less than 13
                        date = month + "-" + day + "-20" + split_date[-1]

                        return date
            except:
                pass

            north_america_date = parser.parse(date).strftime("%m-%d-%Y")

        return north_america_date
    except:
        print(traceback.print_exc())
        return date
