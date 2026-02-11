# import libraries
import os
import xml.etree.ElementTree as ET
import json
from rapidfuzz import process, fuzz, utils
import re
import spacy
import copy

nlp = spacy.load("/app/core/model/en_core_web_sm-3.7.1")


# takes the a list(page) by preprocessing_xml_withoutPrintArea  and a list of position(bounding box)as parameter and return the desired text inside the bounding box
def find_text(
    doc, box
):  # if one_line is true, it will only return only the desired text part of immidiet next line
    # print(box)
    text = []
    if len(box) == 4:

        for line in doc:
            line_text = ""
            for word in line:
                if box[0] <= word[1][0] < box[2] and box[1] <= word[1][1] < box[3]:
                    # print(line)
                    line_text += word[0] + " "
            if line_text != "":
                text.append(line_text)
    # print(text)
    return text


def validate_page_index(batch):
    for num, info in batch.items():
        valid = True
        if batch[num]["Page_number"] == (1, None):
            # forward_validation
            ref_count = 0
            count = 1
            for i in range(num + 1, len(batch)):
                if (
                    batch[i]["Page_number"][0] != None
                    and batch[i]["Page_number"][0]
                    > batch[num]["Page_number"][0] + count
                ):
                    ref_count += 1
                    if ref_count > 1:
                        valid = False
                count += 1
            if valid == False:
                batch[num]["Page_number"] = (None, None)


# next page connect with relevency and dynamic splitting assitance
# version 6
def fix_page_number(batch):
    validate_page_index(batch)
    prev_none_count = 0
    current_end = None
    prev_page_number = None
    for num, info in batch.items():
        start, end = info["Page_number"]

        prev_start, prev_end = None, None
        # stores the page index of previous file
        if num - 1 > 0:
            prev_start, prev_end = batch[num - 1]["Page_number"]

        if start != None and (
            start > len(batch) or start <= 0 or start > num + 5
        ):  # handiling the current page number
            if (
                num + 1 <= len(batch)
                and batch[num + 1]["Page_number"][0] != None
                and num + 1 <= len(batch)
                and start + 1 != batch[num + 1]["Page_number"][0]
            ) or (
                num - 1 > 0
                and batch[num - 1]["Page_number"][0]
                and num - 1 > 0
                and (start - 1 != batch[num - 1]["Page_number"][0])
            ):
                batch[num]["Page_number"] = (None, None)
                start = None
                end = None

        if (
            (end != None and end > len(batch)) and num - 1 > 0 and prev_start != None
        ):  # handiling the total page count
            if (
                prev_start + 1 == start
                and prev_end != None
                and prev_start + 1 <= prev_end <= len(batch)
            ):
                batch[num]["Page_number"] = (
                    batch[num]["Page_number"][0],
                    batch[num - 1]["Page_number"][1],
                )
                start = batch[num]["Page_number"][0]
                end = batch[num - 1]["Page_number"][1]
            elif prev_start != None and prev_start + 1 == start:
                batch[num]["Page_number"] = (batch[num]["Page_number"][0], None)
                start = batch[num]["Page_number"][0]
                end = None
            else:
                batch[num]["Page_number"] = (None, None)
                start = None
                end = None

        if start == None and num - 1 > 0:
            if (
                batch[num - 1]["Page_number"][0] != None
                and batch[num - 1]["Page_number"][1] != None
                and batch[num - 1]["Page_number"][0] + 1
                <= batch[num - 1]["Page_number"][1]
            ):

                batch[num]["Page_number"] = (
                    batch[num - 1]["Page_number"][0] + 1,
                    batch[num - 1]["Page_number"][1],
                )
                start = batch[num]["Page_number"][0]
                end = batch[num]["Page_number"][1]

            elif batch[num]["rel_score"] > 20:
                count = 1
                r_count = 1
                for i in range(num - 1, 0, -1):

                    if (
                        batch[i]["Page_number"][0] != None
                        or batch[i]["Page_number"][0] == 1
                    ):
                        if (
                            batch[i]["Page_number"][1] != None
                            and (batch[i]["Page_number"][0] + count)
                            <= batch[i]["Page_number"][1]
                        ):
                            batch[num]["Page_number"] = (
                                batch[i]["Page_number"][0] + count,
                                batch[i]["Page_number"][1],
                            )
                            break
                        elif (
                            batch[i]["Page_number"][1] == None
                            and batch[i]["Page_number"][0] != None
                        ):
                            batch[num]["Page_number"] = (
                                batch[i]["Page_number"][0] + count,
                                batch[i]["Page_number"][1],
                            )
                            break
                        elif (
                            batch[i]["rel_score"] == 0
                            and batch[i]["label"] == batch[num]["label"]
                        ):
                            batch[num]["Page_number"] = (
                                count + 1,
                                batch[i]["Page_number"][1],
                            )
                            break
                    elif (
                        batch[i]["Page_number"][0] == None
                        and batch[i]["label"] == batch[num]["label"]
                        and batch[i]["rel_score"] < 20
                    ):
                        batch[num]["Page_number"] = (r_count + 1, None)
                        break
                    elif batch[i]["label"] != batch[num]["label"]:
                        break
                    count += 1
                    if batch[i]["rel_score"] > 20:
                        r_count += 1
                    else:
                        r_count = 0

        if batch[num]["Page_number"][0] == None:
            prev_none_count += 1

        # print(info['Page_number'])

        if prev_page_number != None:
            if start != 1:
                if prev_none_count >= 1 and start - 1 <= prev_none_count:
                    for i in range(1, prev_none_count + 1):
                        if start - i <= 0:
                            break
                        batch[num - i]["Page_number"] = (start - i, end)
                    prev_none_count = 0
                if prev_page_number + 1 != start:
                    info["Page_number"] = (prev_page_number + 1, end)

    # print( "mid",[batch[key]['Page_number'] for key in batch])
    # print(batch)
    reverse_keys = list(batch.keys())[::-1]
    # print(reverse_keys)
    prev_page_number = None
    for num in reverse_keys:
        start, end = batch[num]["Page_number"]
        if start != 1:
            if (
                prev_page_number != None
                and prev_page_number != 1
                and prev_page_number - 1 != start
                and prev_page_number - 1 > 0
            ):
                batch[num]["Page_number"] = (prev_page_number - 1, end)
        if start == 1:
            prev_page_number = None
        prev_page_number = batch[num]["Page_number"][0]
        # print(prev_page_number)
    # print(batch)


def split_documents(batch):
    splits = {}
    num = 1
    while num <= len(batch):
        if batch[num]["Page_number"] == (None, None) or batch[num]["Page_number"] == (
            1,
            1,
        ):
            if batch[num]["label"] not in splits:
                splits[batch[num]["label"]] = [(num, num)]
            else:
                splits[batch[num]["label"]].append((num, num))
            num += 1

        else:
            if batch[num]["Page_number"][0] > 0:
                count = 0
                i = 1
                while (
                    num + i <= len(batch)
                    and batch[num + i]["Page_number"][0] != 1
                    and batch[num + i]["Page_number"][0] != None
                ):
                    count += 1
                    i = i + 1
                pg_num = num
                if batch[num]["label"] == None:
                    for i in range(1, count + 1):
                        if batch[num + i]["label"] != None:
                            pg_num = num + i
                            break
                if batch[pg_num]["label"] not in splits:
                    splits[batch[pg_num]["label"]] = [(num, num + count)]
                else:
                    splits[batch[pg_num]["label"]].append((num, num + count))

                if count == 0:
                    num = num + 1
                else:
                    num = num + count + 1

    return splits


# takes xml line element as parameter and returns a list of words. line = [[word1,position,style][word2,position,style],.....]
def build_line(line_elem):
    line = []
    # count=0
    for w in line_elem:
        if w.tag == "W":
            if "s" in w.attrib:
                # print(w.attrib['v'], w.attrib['pos'])
                if len(w.attrib["pos"].split(",")) == 4:
                    line.append(
                        [
                            w.attrib["v"],
                            list(map(int, w.attrib["pos"].split(","))),
                            int(w.attrib["s"]),
                        ]
                    )
                else:
                    line.append([w.attrib["v"], [6000, 6000, 0, 0], int(w.attrib["s"])])

                # count+=1
                # print(count)
            else:
                if len(w.attrib["pos"].split(",")) == 4:
                    line.append(
                        [w.attrib["v"], list(map(int, w.attrib["pos"].split(","))), 0]
                    )
                else:
                    line.append([w.attrib["v"], [6000, 6000, 0, 0], 0])
    return line


# takes root of the xml as input and returns a list of dictionary of all the font style and its details styles=[{font1}{font2}]
def create_style_list(root, style_prob=40):
    styles = (
        []
    )  # details of all fonts will be stored in this list [font1,font2,....] all elements of the list will be a dictionary. font with id 0 will be stored in 0 index
    for i in root.findall("Style"):  # looping all style elements
        S_details = (
            {}
        )  # creating a dictionary of the attributes of the style elements. font1={color:011,font_name:san..,font_weight:....}
        temp = i.attrib["v"].split("; ")
        for i in temp:
            key, value = i.split(": ")
            S_details[key] = value
        if "font-size" in S_details:
            S_details["font-size"] = float(
                S_details["font-size"].strip("pt;")
            )  # converting the font size to int
        else:
            S_details["font-size"] = 4
        styles.append(S_details)
    if len(styles) == 0:
        return styles
    max_font = max(font["font-size"] for font in styles)

    # Update all values of the 'B' key using the specified formula
    for font in styles:
        font["font-size"] = (font["font-size"] / max_font) * style_prob
    # print(styles)
    return styles  # [{'color': '000000', 'font-name': 'times new roman', 'font-family': 'ft_serif', 'font-weight': 'bold', 'font-size': 25.0},.......]


# takes the xml tree and the bottom coordinate as parameter and return a list of words and it's details for everyline above the limit
def create_page(tree):
    doc = (
        []
    )  # list to store the lines and its word  doc=[line1,line2,......] and line = [[word1,position,style_id][word2,position,style_id],.....]
    extremas = [None, None, None, None]
    # count=0
    for elem in tree.iter():  # iterates all elements of the tree
        if elem.tag == "L":  # checks if the element is Line
            line_pos = list(
                map(int, elem.attrib["pos"].split(","))
            )  # converts the position category of the line element to list of integers where [lef,top,right,bottom]
            # find the print area of the page
            extremas = findExtremas(extremas, line_pos)
            doc.append(
                build_line(elem)
            )  # appending all the lines returned by the build_line method
    return doc, extremas


def find_s_id(line, label):
    label = label.split()
    for word in line:
        score = fuzz.token_set_ratio(word[0].lower(), label[0].lower())
        if score >= 95:
            return word[2]


# Version v9 - New Classification logic with matrix now called from the predict_layout_method method and matrix also used for validation if necessary
def predict_layout(
    doc, category, memory_points, style_list, extremas, priority_direction, threshold=85
):
    if len(style_list) == 0:
        return "Blank", {"Blank": 150}, None
    cat_prob = create_cat_dict(priority_direction["category"])
    bottom_limit = extremas[1] + (extremas[3] - extremas[1]) * (40 / 100)
    dynamic_threshold = False
    best_category, best_score = None, 0
    for i in range(2):
        for line in doc:
            if len(line) > 0 and line[0][1][1] <= bottom_limit:
                # build the string for the line
                inp_str = " ".join(
                    sublist[0] for sublist in line
                )  # concate the words of the line separated by space
                # print(inp_str)
                if (
                    len(inp_str) > 4
                ):  # only processing the string if the length of the string is 5
                    for label, keywords in category.items():
                        # Using process.extractOne to find the best match within each category
                        match1, score, idx1 = process.extractOne(
                            inp_str,
                            keywords,
                            scorer=fuzz.token_set_ratio,
                            processor=utils.default_process,
                        )
                        match2, score2, idx2 = process.extractOne(
                            inp_str,
                            keywords,
                            scorer=fuzz.WRatio,
                            processor=utils.default_process,
                        )
                        # if label=="Bill Of Entry":
                        # print(match1,match2,score,score2,keywords[idx1],inp_str)
                        # print(score,score2,keywords[idx])
                        # print(label,match1,match2,score,score2,keywords[idx1],inp_str)
                        # print(score,score2,keywords[idx])
                        if score > score2:
                            idx = idx1
                        else:
                            idx = idx2
                        trigger = (
                            keywords[idx].strip("^^^")
                            if "^^^" in keywords[idx]
                            else keywords[idx]
                        )
                        trigger = (
                            trigger.strip("!!!") if "!!!" in keywords[idx] else trigger
                        )
                        focus = 1 if "^^^" in keywords[idx] else 0
                        force = 1 if "!!!" in keywords[idx] else 0

                        if (
                            (score >= 95 and score2 >= 95)
                            or (
                                (focus != 1 and force != 1)
                                and (
                                    (
                                        match1.lower() in match2.lower()
                                        or match2.lower() in match1.lower()
                                    )
                                    and len(inp_str.replace("-", " ").split())
                                    >= len(keywords[idx].split())
                                    and score >= threshold
                                    and score2 >= (threshold - 2.5)
                                )
                            )
                            or (
                                (focus == 1 or force == 1)
                                and (
                                    (
                                        match1.lower() in match2.lower()
                                        or match2.lower() in match1.lower()
                                    )
                                    and len(inp_str.replace("-", " ").split())
                                    >= len(keywords[idx].split())
                                    and score >= threshold + 3
                                    and score2 >= threshold + 3
                                )
                            )
                        ):
                            # print(score,score2,keywords[idx],inp_str)
                            s_id = find_s_id(line, match1)
                            if s_id == None:
                                s_id = line[0][2]
                            score += style_list[s_id][
                                "font-size"
                            ]  # adding probability for font size. fonts with bigger size has higher probability
                            # print(line)
                            # print(score)
                            if (
                                "font-weight" in style_list[s_id].keys()
                            ):  # if the font is bold then
                                score += 10  # adding probability for font-weight.
                            # print(score)
                            if focus == 1:
                                score += 25
                            if force == 1:
                                score += 2000
                            if score > cat_prob[label]:
                                cat_prob[label] = score
                            # print(label,"------","Word=",inp_str,"----",score, score2,keywords[idx],s_id,dynamic_threshold)

                        # print(label,"------","Word=",inp_str,"----",score, score2,keywords[idx])
        best_category, best_score = find_category(cat_prob)
        if best_score >= 125:
            break
        else:
            bottom_limit = extremas[1] + (extremas[3] - extremas[1]) * (45 / 100)
            dynamic_threshold = True

    """
    return 0 if matrix not used
    return 1 if Used_matrix_for_validation
    return 2 if Used_matrix_for_title
    
    """

    cautionous_category1 = ["Airway Bill"]
    cautionous_category2 = ["Delivery Note"]
    cautionous_category3 = ["Commercial Invoice", "Packing List"]
    if (
        best_category in cautionous_category3
        and 0 <= (cat_prob["Commercial Invoice"] - cat_prob["Packing List"]) <= 10
    ) or (best_category in cautionous_category3 and best_score <= 115):

        mat_label, mat_score = predict_for_matrix(doc, memory_points)
        if mat_label in ("Commercial Invoice", "Packing List"):
            return mat_label, cat_prob, mat_score, 1

    else:
        mat_label, mat_score = predict_for_matrix(doc, memory_points)
        if best_category in cautionous_category1:
            if best_score >= 130:
                return best_category, cat_prob, None, 0
            else:
                if best_category == "Airway Bill":
                    if mat_label == "Airway Bill":
                        return mat_label, cat_prob, mat_score, 1

        elif best_category in cautionous_category2:
            if best_score > 120:
                return best_category, cat_prob, None, 0
            else:
                if mat_label in cautionous_category3:
                    return best_category, cat_prob, mat_score, 1

        elif best_category == "Bill of Lading":
            if best_score >= 125:
                return best_category, cat_prob, None, 0
            else:
                if best_category == mat_label:
                    return mat_label, cat_prob, mat_score, 1

        elif best_score >= 110:
            return best_category, cat_prob, None, 0
    return mat_label, cat_prob, mat_score, 2


# checks if words has common sub string
def check_word_presence(word1, word2):
    flag = True
    for i in word1.lower().split():
        if i not in word2:
            flag = False
            break
    if flag == True:
        return flag
    for i in word2.lower().split():
        if i not in word1:
            flag = False
            break
    return flag


# takes the words list and root of the xml and the category dictionary and returns the predicted cls
def predict_for_matrix(doc, matrix):
    new_matrix = create_key_map(matrix)

    for line in doc:
        # build the string for the line
        inp_str = " ".join(
            sublist[0] for sublist in line
        )  # concate the words of the line separated by space
        inp_str = special_filter(inp_str)

        if (
            len(inp_str) > 2
        ):  # only processing the string if the length of the string is 5
            for label, keywords in matrix.items():
                # Using process.extractOne to find the best match within each category
                match = process.extract(
                    inp_str,
                    keywords.keys(),
                    scorer=fuzz.token_set_ratio,
                    processor=utils.default_process,
                    limit=3,
                )
                # You can set a threshold score to consider a match
                threshold = 70
                for i in match:
                    score = i[1]
                    key = i[0]
                    if score >= threshold:
                        if key.lower() in inp_str.lower():
                            new_matrix[label][key] = matrix[label][key]
                            # print(inp_str,'\n',match)

    return find_label_for_matrix(new_matrix)


def find_num_from_string(string_fragments, sig=None):
    if sig == None:
        number = ""
        for ch in string_fragments:
            if "0" <= ch <= "9":
                number += ch
            elif number != "" or " " < ch <= "/":
                break

        if number != "":
            return number
        else:
            return ""
    else:
        string_fragments = string_fragments.split(sig)
        start = find_num_from_string(string_fragments[0][::-1])[::-1]
        end = find_num_from_string(string_fragments[1])
        return (int(start), int(end))


def find_digit_of_digit(input_string):
    # Define regular expression pattern
    pattern = r"\b\d+\s*(?:of)\s*\d+\b|\b\d+of\d+\b|\b\d+of\d+\b"

    # Find all matches using the pattern
    matches = re.findall(pattern, input_string)
    return matches


def find_special_numbers(input_string):
    # Define regular expression pattern
    input_string = input_string.replace("I", "1").replace("i", "1").replace("l", "1")
    pattern = r"\b\d+(?:\s*(?:of|\/|-)\s*\d+)?\b"

    # Find all matches using the pattern
    matches = re.findall(pattern, input_string)

    return matches


# Function to detect phone numbers
def detect_phone_numbers(text):
    phone_pattern = re.compile(r"\+?\d[\d\s\-\(\)]{9,}")
    return phone_pattern.findall(text)


# Function to detect dates
def detect_dates(text):
    date_pattern = re.compile(
        r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b|\b\d{1,2}(?:th|rd|st|nd)?\s\w+\s\d{4}\b"
    )
    return date_pattern.findall(text)


# Main function to call all detectors
def detect_avoiding_entities(text):
    phones = detect_phone_numbers(text)
    dates = detect_dates(text)

    return {"Phone Numbers": phones, "Dates": dates}


# checks if a line contains any location
def find_location(text, category):
    # print(category)
    for label, keywords in category.items():
        # Using process.extractOne to find the best match within each category
        match, score, idx = process.extractOne(
            text, keywords, scorer=fuzz.WRatio, processor=utils.default_process
        )
        if score > 90:
            # print("ignored text:", text)
            return False
    doc = nlp(text)
    for ent in doc.ents:
        # Detect locations (GPE: Geopolitical Entity)
        if ent.label_ == "GPE":
            # print("location",text)
            return True
    return False


def find_document_ids(doc, style_list, extremas, category, scan_threshold=40):
    if len(style_list) == 0:
        return 0

    bottom_limit = extremas[1] + (extremas[3] - extremas[1]) * (40 / 100)
    all_line_text = []
    for line in doc:
        if len(line) > 0 and line[0][1][1] <= bottom_limit:
            # build the string for the line
            inp_str = " ".join(
                sublist[0] for sublist in line
            )  # concate the words of the line separated by space
            if find_location(inp_str, category) == False:
                avoiding_entity = detect_avoiding_entities(inp_str)
                for entities in avoiding_entity.values():
                    for ent in entities:
                        if ent != None:
                            # print("Phone/Date: ",ent)
                            inp_str = inp_str.replace(ent, "")
                all_line_text.append(inp_str)
    return extract_ids(all_line_text)


def extract_ids(all_lines):
    all_ids = []
    for line in all_lines:
        for word in line.split(" "):
            digits = sum(c.isdigit() for c in word)
            if len(word) >= 4 and digits >= (len(word) - digits):
                all_ids.append(word)
    # print(all_ids)
    return all_ids


def check_relevency_with_previous_page(prev_page, current_page):
    common_words = set(prev_page) & set(current_page)
    # Get the number of common words
    # print(common_words)
    return 10 * len(common_words)


# updated
def predict_page_number(doc, page_directions, extremas):
    # check corners
    bottom_limit = extremas[1] + (extremas[3] - extremas[1]) * (20 / 100)
    top_limit = extremas[3] - (extremas[3] - extremas[1]) * (20 / 100)
    page_number = ""
    continuation = None
    for line_index in range(len(doc)):
        # build the string for the line
        all_page_tokens = []
        inp_str = " ".join(
            sublist[0] for sublist in doc[line_index]
        )  # concate the words of the line separated by space
        jump_next_page_trigger = False
        for label, keywords in page_directions.items():
            # Using process.extractOne to find the best match within each category
            match2 = process.extract(
                inp_str,
                keywords,
                scorer=fuzz.WRatio,
                processor=utils.default_process,
                limit=1,
            )
            match = process.extract(
                inp_str,
                keywords,
                scorer=fuzz.token_set_ratio,
                processor=utils.default_process,
                limit=1,
            )
            # print(match2,match)
            # You can set a threshold score to consider a match
            threshold = 85
            possible_tokens = []
            # print(inp_str)
            # if label =="Continue" and match[0][1] >= threshold:
            # return "+1"
            if (
                (match[0][1] >= threshold or match2[0][1] >= threshold)
                and label == "Page"
                and match[0][0].lower() in inp_str.lower()
            ):
                # check right of word page
                page_index = inp_str.lower().split(match[0][0].lower())
                # print(inp_str,"********",match[0][0], page_index)
                # print(inp_str.lower().strip(match[0][0]))
                # print("Page point 1:", page_index)
                if len(page_index) >= 2:

                    possible_tokens = find_special_numbers(page_index[1])
                    # print(possible_tokens,page_index[1])
                    all_page_tokens.append(possible_tokens)

                """ 
                #check below of word page    
                if (line_index+1)<len(doc):
                    inp=' '.join(sublist[0] for sublist in doc[line_index+1])
                    #print('Next Line:',inp)
                    possible_tokens = find_special_numbers(inp)
                    all_page_tokens.append(possible_tokens)
                    #print('Tokens:',possible_tokens)
                """

                # check bottom of word page using position
                pos = []  # match token position in xml
                for word in doc[line_index]:
                    # print(word)
                    if match[0][0].lower() in word[0].lower():
                        pos = word[1]
                        # print(pos)
                        break

                # if the same page trigger repeats below this means current page trigger should be avoided.
                text = find_text(
                    doc,
                    [
                        pos[0] - 200,
                        pos[3] - 10,
                        pos[2] + 40,
                        pos[3] + (pos[3] - pos[1]) + 30,
                    ],
                )
                for i in text:
                    if match[0][0].lower() in i.lower():
                        jump_next_page_trigger = True

                if jump_next_page_trigger != True:
                    text = find_text(
                        doc,
                        [
                            pos[0] - 15,
                            pos[3] - 10,
                            pos[2] + 25,
                            pos[3] + (pos[3] - pos[1]) + 20,
                        ],
                    )  # checks bottom of the word page
                    for i in text:
                        possible_tokens = find_special_numbers(i)
                        if len(possible_tokens) != 0:
                            all_page_tokens.append(possible_tokens)
                            break

                    # check right of word page using position
                    # print('position: ',pos,doc[line_index])
                    text = find_text(doc, [pos[2], pos[1] - 10, pos[2] + 600, pos[3]])
                    # print(text)
                    for i in text:
                        possible_tokens = find_special_numbers(i)
                        if len(possible_tokens) != 0:
                            all_page_tokens.append(possible_tokens)
                            break

                    # print("Page point 3:", page_number)

                    # print(all_page_tokens)
                    check_priority = ("von", "of", "OF", "0F", "0l", "/", "-")
                    # trans_token = list(zip(*all_page_tokens))

                    for line_tokens in all_page_tokens:
                        for sig in check_priority:
                            if (
                                len(line_tokens) > 0
                                and sig.lower() in line_tokens[0].lower()
                            ):
                                start, end = find_num_from_string(line_tokens[0], sig)
                                if (
                                    start != ""
                                    and end != ""
                                    and 0 < int(start) <= int(end)
                                ):
                                    return (int(start), int(end))

                    if continuation != None:
                        return continuation

                    if len(all_page_tokens) >= 2 and len(all_page_tokens[1]) == 2:
                        start = find_num_from_string(all_page_tokens[1][0])
                        end = find_num_from_string(all_page_tokens[1][1])

                        if start != "" and end != "" and 0 < int(start) <= int(end):
                            return (int(start), int(end))

                    for line_tokens in all_page_tokens:
                        if len(line_tokens) > 0:
                            num = int(find_num_from_string(line_tokens[0]))
                            if num != None and 0 < num < 1000:
                                return (num, None)

                    """
                    all_numbers=[]
                    for line_tokens in  trans_token[0]:
                        if len(line_token)>0:
                            for sig in check_priority:
                                if sig in line_tokens[0]:
                                    return find_num_from_string(line_tokens[0])
                    """

            elif (
                label == "German"
                and (match[0][1] >= threshold or match2[0][1] >= threshold)
                and match[0][0].lower() in inp_str.lower()
            ):
                if (line_index + 1) < len(doc):
                    text = " ".join(sublist[0] for sublist in doc[line_index + 1])
                # print(text)
                possible_tokens = find_special_numbers(text)

                if len(possible_tokens) != 0:
                    page_num = find_num_from_string(possible_tokens[0])
                    if len(page_num) == 2:
                        return (int(page_num[0]), int(page_num[1]))
                    else:
                        return (int(page_num[0]), None)

            elif label == "ISF":
                for i in keywords:
                    if i.lower() in inp_str.lower():
                        return (2, None)

    all_page_tokens = []
    for line in doc:
        if (len(line) > 0 and line[0][1][1] <= bottom_limit) or (
            len(line) > 0 and line[0][1][1] >= top_limit
        ):
            # if (len(doc)>0 and doc[line_index][0][1][1]<=bottom_limit) or (len(doc)>0 and doc[line_index][0][1][1]>=top_limit):
            # build the string for the line
            inp_str = " ".join(
                sublist[0] for sublist in line
            )  # concate the words of the line separated by space
            # print(inp_str)
            possible_token = find_special_numbers(inp_str)
            if len(possible_token) == 1 and len(possible_token[0]) + 2 >= len(inp_str):
                all_page_tokens.append(possible_token)

    # print(all_page_tokens)
    check_priority = ("von", "of", "OF", "0F", "0l", "/", "-")
    # trans_token = list(zip(*all_page_tokens))
    # print(all_page_tokens)
    for sig in check_priority:
        for line_tokens in all_page_tokens:
            # print(sig)
            if len(line_tokens) > 0 and sig in line_tokens[0].lower():
                start, end = find_num_from_string(line_tokens[0], sig)
                if (
                    start != ""
                    and end != ""
                    and 0 < int(start) <= int(end)
                    and int(start) < 999
                    and int(end) < 999
                ):
                    return (int(start), int(end))

    return (None, None)


def create_cat_dict(cat):
    new_dict = {}
    for key in cat:
        new_dict[key] = 0
    return new_dict


# filterout special characters and numbers from words and lines
def special_filter(text):
    # Remove special characters and numbers using regular expressions
    cleaned_text = re.sub("[^A-Za-z]+", " ", text)
    return cleaned_text


def create_key_map(matrix):
    new_matrix = {}
    for key, values in matrix.items():
        temp = {}
        for k in values.keys():
            temp[k] = 0
        new_matrix[key] = temp
    return new_matrix


def find_category(cat_prob):
    # print(cat_prob)
    best_label = None
    best_score = 0
    for label, score in cat_prob.items():
        if score > best_score:
            best_score = score
            best_label = label
    return best_label, best_score


def find_label_for_matrix(matrix):
    # print(matrix)
    best_score = 0
    best_label = None
    for label, weight in matrix.items():
        score = sum(weight.values())
        if score > best_score:
            best_score = score
            best_label = label
    if best_label != "Bill of Lading" and best_score > 0.5:
        return best_label, matrix
    elif best_score > 0.7:
        return best_label, matrix

    return None, matrix


# find top and lower point
def findExtremas(extremas, coordinates):
    for i in range(len(extremas)):
        if extremas[i] == None:
            extremas[i] = coordinates[i]

    for i in range(len(extremas)):
        if i < 2:
            if coordinates[i] < extremas[i]:
                extremas[i] = coordinates[i]
        else:
            if coordinates[i] > extremas[i]:
                extremas[i] = coordinates[i]

    return extremas


# takes the path of the category json file and returns a dictionary where the cls_labels are the keys and the values are list of triggers.
def load_labels(file_path):

    # Read the JSON file and load its content into a dictionary
    with open(file_path, "r") as json_file:
        category = json.load(json_file)
    return category


# takes the path of the memory points json file and returns a dictionary where the cls_labels are the keys and the values are list of triggers.
def load_memory_points(file_path):

    # Read the JSON file and load its content into a dictionary
    with open(file_path, "r") as json_file:
        matrix_keys = json.load(json_file)
    return matrix_keys


# takes xml file path and %percentage of the area to search as parameter and returns the list of lines and root of the xml file and font style list
def preprocessing_xml_withoutPrintArea(file_path, area=40):
    # loading xml file
    tree = ET.parse(file_path)
    root = tree.getroot()
    # crated a list of words that are above the limit
    page, extremas = create_page(tree)
    # created a list of dictionary of the font style element
    f_style = create_style_list(root)
    # print(page,f_style)
    return page, f_style, extremas


# used to merge the dictionary with the master category and custom category
def merge_dictionary(dict1, dict2):
    merged_dict = copy.deepcopy(dict1)
    for cat in dict2.keys():
        if cat in merged_dict:
            for trigger in dict2[cat]:
                if trigger not in merged_dict[cat]:
                    merged_dict[cat].append(trigger)
        else:
            merged_dict[cat] = dict2[cat]

    return merged_dict


def predictLabel(
    file_path,
    page_range,
    category,
    custom_category,
    memory_points,
    priority_direction,
    project,
    automatic_split=True,
):
    category = merge_dictionary(category, custom_category)
    details = {}
    without_split_labels = {}
    count = 1
    if type(file_path) == list:
        for current_range in page_range:
            page_details = {}
            page_count = 0
            prev_doc_ids = None
            for path in file_path[current_range[0] - 1 : current_range[1]]:
                try:

                    page, style_list, extremas = preprocessing_xml_withoutPrintArea(
                        path
                    )
                    # predicting the class of the xml
                    matrix_prob = None
                    label, title_prob, matrix_prob, matrix_status = predict_layout(
                        page,
                        category,
                        memory_points,
                        style_list,
                        extremas,
                        priority_direction,
                    )
                    # print(title_prob,matrix_prob)
                    try:
                        if label == "Blank":
                            page_number = (None, None)
                        else:
                            page_number = predict_page_number(
                                page, priority_direction["page_direction"], extremas
                            )
                    except:
                        page_number = (None, None)

                    # print(count,path,label, page_number)
                    if label == None:
                        label = "None"

                    rel_score = 0
                    # print(current_doc_ids)
                    try:
                        if len(style_list) > 0:
                            current_doc_ids = find_document_ids(
                                page, style_list, extremas, category
                            )
                            # print(current_doc_ids)
                            if prev_doc_ids != None:
                                rel_score = check_relevency_with_previous_page(
                                    prev_doc_ids, current_doc_ids
                                )
                            # print(count,file_path, label, page_number, rel_score, matrix_status)
                            prev_doc_ids = current_doc_ids
                    except:
                        rel_score = 0

                    page_details[page_count] = {
                        "File_path": file_path,
                        "label": label,
                        "Score1": title_prob,
                        "Score2": matrix_prob,
                        "Page_number": page_number,
                        "rel_score": rel_score,
                        "used matrix": matrix_status,
                    }

                    details[count] = {
                        "File_path": file_path,
                        "label": label,
                        "Score1": title_prob,
                        "Score2": matrix_prob,
                        "Page_number": page_number,
                        "rel_score": rel_score,
                        "used matrix": matrix_status,
                    }
                    count += 1
                except:
                    details[count] = {
                        "File_path": file_path,
                        "label": None,
                        "Score1": None,
                        "Score2": None,
                        "Page_number": (None, None),
                        "rel_score": 0,
                        "used matrix": 0,
                    }
                    count += 1

        if len(details) > 0:
            if automatic_split == True:
                try:
                    # print(details)
                    fix_page_number(details)
                    # print(details)
                    # print([batch_details[key]['Page_number'] for key in batch_details])
                    detected_labels = split_documents(details)
                    # print(detected_labels)
                    return detected_labels
                except:
                    return {"None": [(1, len(file_path))]}

            else:
                try:
                    # print(details)
                    for current_range in page_range:
                        for i in range(current_range[0], current_range[1] + 1):
                            if details[i]["label"] != None:
                                if details[i]["label"] not in without_split_labels:
                                    without_split_labels[details[i]["label"]] = [
                                        (current_range[0], current_range[1])
                                    ]
                                    break
                                else:
                                    without_split_labels[details[i]["label"]].append(
                                        (current_range[0], current_range[1])
                                    )
                                    break
                            if i == current_range[1]:
                                if "None" not in without_split_labels:
                                    without_split_labels["None"] = [
                                        (current_range[0], current_range[1])
                                    ]
                                    break
                                else:
                                    without_split_labels["None"].append(
                                        (current_range[0], current_range[1])
                                    )
                                    break
                    # print(without_split_labels)
                    return without_split_labels
                except:
                    return {"None": [1, len(file_path)]}
        return {"None": [1, len(file_path)]}
