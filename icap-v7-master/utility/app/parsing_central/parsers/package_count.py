def process(string):
    try:
        split_at = 0
        for idx, c in enumerate(string):
            if c.isalpha():
                split_at = idx
                break

        uom_string = string[split_at:]
        uom_string_split = uom_string.split()
        uom = ""
        extra_data_list = []
        for x_idx, x in enumerate(uom_string_split):
            if not x[0].isdigit():
                uom += x

        new_string = string.replace(uom, "").strip()

        number_char_idx_val_list = []
        number = ""
        # for c_idx, c in enumerate(new_string):
        #    if c == "," or c == "." or c.isdigit():
        #        number_char_idx_val_list.append([c_idx, c])
        # for [c_idx, c] in number_char_idx_val_list:
        #    if (c == '.') or ( c ==','):
        #        if(c_idx - (c_idx-1)) == 1:
        #            number +=c
        #    else:
        #        number +=c
        number = string[:split_at]
        extra_data = None

        if extra_data_list:
            extra_data = " ".join(extra_data_list)

        if extra_data:
            if (uom.strip().lower() in extra_data.lower()) or (
                number.strip() in extra_data
            ):
                extra_data = None

        # if "pallet" in uom.lower():
        # if "m3" in uom.lower():
        # uom = uom.replace("M3", "")
        # uom = uom.replace("m3", "")
        if uom.lower() == "palletpallet":
            uom = "pallet"
        if uom.lower() == "palletspallets":
            uom = "pallets"

        if number and uom:
            return [number, uom.upper(), extra_data]

        else:
            return [string]
    except:
        return [string]
