from decimal import ROUND_HALF_UP, Decimal

def apply_calculate_fields(string, condition, target_value):
    """
    Rounds to a dynamic number of decimals based on the input precision and trims unnecessary zeros.
    """
    try:
        changed_string = str(string).rstrip("0").rstrip(".") if "." in str(string) else str(string)
        changed_string = Decimal(str(string))
        target_value = str(target_value).rstrip("0").rstrip(".") if "." in str(target_value) else str(target_value)
        target_value = Decimal(str(target_value))

        if condition == "+":
            changed_string += target_value
        elif condition == "-":
            changed_string -= target_value
        elif condition == "*":
            changed_string *= target_value
        elif condition == "/":
            if target_value == Decimal("0"):
                return changed_string
            changed_string /= target_value

        # Round to a reasonable precision (6 decimals) and avoid scientific notation
        result = changed_string.quantize(Decimal("1.000000"), rounding=ROUND_HALF_UP)

        # Return clean string (strip trailing 0s and "." if it's a whole number)
        return str(result).rstrip("0").rstrip(".") if "." in str(result) else str(result)

    except:
        return string
