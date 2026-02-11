import re

from fuzzywuzzy import fuzz, process


def detect_company_by_email_and_rearrange(input_text):
    try:
        # Extract the email address from the input text using regex
        email = re.search(r"\S+@\S+", input_text).group(0)

        # Extract the domain name from the email address
        domain = email.split("@")[-1]
        company_name = domain.lower().replace(".com", "")

        all_lines_origin = input_text.split("\n")
        all_lines = all_lines_origin[:]
        all_lines = [x for x in all_lines if "@" not in x]
        result = process.extractOne(company_name, all_lines)
        if result:
            company_index = all_lines.index(result[0])
            changed_list = (
                all_lines_origin[company_index:] + all_lines_origin[:company_index]
            )
            return "\n".join(changed_list)
        return input_text
    except:
        return input_text
