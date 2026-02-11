def process(string):
    try:
        string = string.strip()

        def get_alpha_count(s):
            count = 0
            for c in s:
                if c.isalpha():
                    count += 1
            return count

        if get_alpha_count(string) < 2:
            return [string]

        split_data = string.split(" ")
        number = split_data[0]
        uom = split_data[1]
        # print(number, uom)
        if number and uom:
            return [number, uom.upper()]
        else:
            return [string]
    except:
        return [string]
