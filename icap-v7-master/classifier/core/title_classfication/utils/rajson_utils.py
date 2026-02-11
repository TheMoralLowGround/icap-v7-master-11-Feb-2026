def find_text(doc, box):
    # Initialize an empty list to store the extracted text.
    text = []
    
    # Check if the bounding box contains exactly four coordinates.
    if len(box) == 4:
        # Iterate over each line in the document.
        for line in doc:
            line_text = ""  # Initialize an empty string to accumulate text for this line.
            
            # Iterate over each word in the line.
            for word in line:
                # Check if the word lies within the specified bounding box.
                # word[1] contains the position of the word as [left, top, right, bottom].
                if box[0] <= word[1][0] < box[2] and box[1] <= word[1][1] < box[3]:
                    # If the word lies within the box, append it to the line's text.
                    line_text += word[0] + " "
            
            # If this line contains any text within the bounding box, add it to the final result.
            if line_text != "":
                text.append(line_text)
    
    # Return the text as a list of strings.
    return text

def build_line_json(line_elem):
    line = []
    for w in line_elem.get("children", []):
        if w.get("type") == "word":
            v = w.get("v", "")
            pos_str = w.get("pos", "6000,6000,0,0")
            pos = [int(x) for x in pos_str.split(",")] if len(pos_str.split(",")) == 4 else [6000, 6000, 0, 0]
            s = int(w.get("s", 0))
            line.append([v, pos, s])
    return line

def create_style_list_json(page_dict, style_prob=40):
    styles = []
    for style in page_dict.get("styles", []):
        S_details = {}
        temp = style["v"].split("; ")
        for item in temp:
            if not item.strip():
                continue
            if ": " in item:
                key, value = item.split(": ")
                S_details[key.strip()] = value.strip()
        if "font-size" in S_details:
            S_details["font-size"] = float(S_details["font-size"].strip("pt;"))
        else:
            S_details["font-size"] = 4
        styles.append(S_details)
    if styles:
        max_font = max(font["font-size"] for font in styles)
        for font in styles:
            font["font-size"] = (font["font-size"] / max_font) * style_prob
    return styles

def findExtremas(extremas, coordinates):
    for i in range(len(extremas)):
        if extremas[i] is None:
            extremas[i] = coordinates[i]
    for i in range(len(extremas)):
        if i < 2:
            if coordinates[i] < extremas[i]:
                extremas[i] = coordinates[i]
        else:
            if coordinates[i] > extremas[i]:
                extremas[i] = coordinates[i]
    return extremas

def create_page_json(page_dict):
    doc = []
    extremas = [None, None, None, None]
    def traverse(elem):
        if isinstance(elem, dict):
            if elem.get("type") == "line":
                pos = [int(x) for x in elem["pos"].split(",")]
                nonlocal extremas
                extremas = findExtremas(extremas, pos)
                doc.append(build_line_json(elem))
            for child in elem.get("children", []):
                traverse(child)
        elif isinstance(elem, list):
            for child in elem:
                traverse(child)
    traverse(page_dict)
    return doc, extremas
