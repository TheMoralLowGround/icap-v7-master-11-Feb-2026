import traceback


# version#5.01.13102022 @Fahim
def process(temperature):
    # print('input string', temperature)
    try:
        temperature = temperature.strip()
        required_maximum = None
        required_minimum = None
        temperature_uom = None
        requires_temperature_control = "FALSE"

        # spliting each words of temperature (input string) into a list
        temperature_list = temperature.split(" ")
        for i in range(len(temperature_list)):
            if "(" in temperature_list[i] and ")" in temperature_list[i]:
                temperature_list[i] = temperature_list[i].replace("(", "")
                temperature_list[i] = temperature_list[i].replace(")", "")
                temperature_list[i] = temperature_list[i].strip()
            if (
                "+" in temperature_list[i]
                and temperature.count("+") < 3
                and (
                    "+" in temperature_list[i + 1]
                    or "+" in temperature_list[i + 2]
                    or temperature_list[i].count("+") == 2
                )
            ):
                if temperature_list[i].count("+") == 2:
                    required_minimum = temperature_list[i][1]
                    required_maximum = temperature_list[i][3:].strip()
                else:
                    required_minimum = temperature_list[i].replace("+", "").strip()
                    if "+" in temperature_list[i + 1]:
                        required_maximum = (
                            temperature_list[i + 1].replace("+", "").strip()
                        )
                    elif "+" in temperature_list[i + 2]:
                        required_maximum = (
                            temperature_list[i + 2].replace("+", "").strip()
                        )
                temperature_uom = "CEL"
                requires_temperature_control = "TRUE"
                break
            if "-" in temperature_list[i]:
                temperature_first_part = temperature_list[i].split("-")[0].strip()
                temperature_last_part = (
                    temperature_list[i].split("-")[1].strip().upper()
                )
                if temperature_first_part.isnumeric() and (
                    "C" in temperature_last_part
                    or (
                        temperature_last_part.isnumeric()
                        and temperature_list[i + 1].lower() == "c"
                    )
                ):
                    required_minimum = temperature_first_part
                    required_maximum = temperature_last_part.replace("C", "").strip()
                    temperature_uom = "CEL"
                    requires_temperature_control = "TRUE"
                if temperature_list[i] == "-":
                    if temperature_list[i - 1].isnumeric():
                        required_minimum = temperature_list[i - 1]
                    if temperature_list[i + 1].isnumeric():
                        required_maximum = temperature_list[i + 1]
                    temperature_uom = "CEL"
                    requires_temperature_control = "TRUE"
                    break
            if temperature_list[i].lower() == "to":
                if (
                    "c" in temperature_list[i - 1].lower()
                    and "c" in temperature_list[i + 1].lower()
                ):
                    temp1 = temperature_list[i - 1].lower().replace("c", "").strip()
                    temp2 = temperature_list[i + 1].lower().replace("c", "").strip()
                    if int(temp1) > int(temp2):
                        required_maximum = temp1
                        required_minimum = temp2
                    else:
                        required_maximum = temp2
                        required_minimum = temp1
                    temperature_uom = "CEL"
                    requires_temperature_control = "TRUE"

        # generating output list
        if requires_temperature_control == "TRUE":
            output_list = [
                requires_temperature_control,
                required_maximum,
                required_minimum,
                temperature_uom,
            ]
        else:
            output_list = [requires_temperature_control]
        return output_list
    except:
        # print(traceback.print_exc())
        return [temperature]
