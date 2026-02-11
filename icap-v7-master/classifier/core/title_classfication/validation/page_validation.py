from rapidfuzz import process, fuzz, utils
from core.title_classfication.utils.text_utils import find_special_numbers, find_num_from_string
from core.title_classfication.utils.rajson_utils import find_text

def validate_page_index(batch):
    # Iterate over each document in the batch, using its index and metadata.
    for num, info in batch.items():
        valid = True  # Setting the page index is valid by default.
        
        # Check if the current page has 'Page_number' marked as (1, None).
        if batch[num]["Page_number"] == (1, None):
            # Start forward validation to check the consistency of subsequent pages.
            ref_count = 0  # Counter for invalid references.
            count = 1      # Counter for the expected increment in page numbers.
            
            # Loop through subsequent pages to validate their numbering.
            for i in range(num + 1, len(batch)):
                # Check if a subsequent page's start page number is inconsistent.
                if (batch[i]["Page_number"][0] is not None
                        and batch[i]["Page_number"][0] > batch[num]["Page_number"][0] + count):
                    ref_count += 1  # Increment invalid reference count.
                    
                    # If more than one inconsistency is found, mark as invalid.
                    if ref_count > 1:
                        valid = False
                count += 1  # Increment the expected page number counter.
            
            # If the page numbering is invalid, reset it to (None, None).
            if not valid:
                batch[num]["Page_number"] = (None, None)

# updated
def predict_page_number_v2(doc, page_directions, extremas):
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

                    possible_tokens = find_special_numbers(page_index[1]) #line 592
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
                        possible_tokens = find_special_numbers(i) # line 592
                        if len(possible_tokens) != 0:
                            all_page_tokens.append(possible_tokens)
                            break

                    # check right of word page using position
                    # print('position: ',pos,doc[line_index])
                    text = find_text(doc, [pos[2], pos[1] - 10, pos[2] + 600, pos[3]]) #line 14
                    # print(text)
                    for i in text:
                        possible_tokens = find_special_numbers(i) #line 592
                        if len(possible_tokens) != 0:
                            all_page_tokens.append(possible_tokens)
                            break

                    # print("Page point 3:", page_number)
                    #print("@@@@@@@@@@@@@@@@@@@@")
                    #print(all_page_tokens)
                    #print("@@@@@@@@@@@@@@@@@@@@")
                   
                    check_priority = ("von", "of", "OF", "0F", "0l", "/", "-")
                    # trans_token = list(zip(*all_page_tokens))

                    for line_tokens in all_page_tokens:
                        for sig in check_priority:
                            date_flag = False
                            if sig == "/":
                                try : 
                                    if "/" in line_tokens[0] and len(line_tokens[1]) >= 4:
                                        date_flag = True
                                except:
                                    pass        
                                
                            if (
                                len(line_tokens) > 0
                                and sig.lower() in line_tokens[0].lower() and not date_flag
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
                    
                    date_flag = False
                    try : 
                        if "/" in all_page_tokens[1][0] and len(all_page_tokens[1][1]) >= 4:
                            date_flag = True
                    except:
                        pass   
                     
                    if len(all_page_tokens) >= 2 and len(all_page_tokens[1]) == 2 and not date_flag:
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

# next page connect with relevency and dynamic splitting assitance
# version 6
# def fix_page_number(batch):
#     validate_page_index(batch)
#     prev_none_count = 0
#     current_end = None
#     prev_page_number = None
#     prev_label = None  # Track the previous label to prevent cross-label adjustments

#     for num, info in batch.items():
#         start, end = info["Page_number"]
#         current_label = info["label"]  # Track the current label

#         prev_start, prev_end = None, None
#         # Store the page index of the previous entry
#         if num - 1 > 0:
#             prev_start, prev_end = batch[num - 1]["Page_number"]

#         # Handle invalid page numbers
#         if start is not None and (
#             start > len(batch) or start <= 0 or start > num + 5
#         ):
#             if (
#                 num + 1 <= len(batch)
#                 and batch[num + 1]["Page_number"][0] is not None
#                 and start + 1 != batch[num + 1]["Page_number"][0]
#             ) or (
#                 num - 1 > 0
#                 and batch[num - 1]["Page_number"][0] is not None
#                 and start - 1 != batch[num - 1]["Page_number"][0]
#             ):
#                 batch[num]["Page_number"] = (None, None)
#                 start = None
#                 end = None

#         # Handle total page count inconsistencies
#         if (
#             end is not None and end > len(batch) and num - 1 > 0 and prev_start is not None
#         ):
#             if (
#                 prev_start + 1 == start
#                 and prev_end is not None
#                 and prev_start + 1 <= prev_end <= len(batch)
#             ):
#                 batch[num]["Page_number"] = (start, prev_end)
#             elif prev_start is not None and prev_start + 1 == start:
#                 batch[num]["Page_number"] = (start, None)
#             else:
#                 batch[num]["Page_number"] = (None, None)

#         # Adjust missing page numbers based on the previous entry
#         if start is None:
#             if num - 1 > 0:
#                 if (
#                     batch[num - 1]["Page_number"][0] is not None
#                     and batch[num - 1]["Page_number"][1] is not None
#                     and batch[num - 1]["Page_number"][0] + 1
#                     <= batch[num - 1]["Page_number"][1]
#                 ):
#                     batch[num]["Page_number"] = (
#                         batch[num - 1]["Page_number"][0] + 1,
#                         batch[num - 1]["Page_number"][1],
#                     )
#                 elif batch[num]["rel_score"] > 20 and current_label == prev_label:
#                     count = 1
#                     for i in range(num - 1, 0, -1):
#                         if batch[i]["label"] != current_label:
#                             break
#                         if batch[i]["Page_number"][0] is not None:
#                             batch[num]["Page_number"] = (
#                                 batch[i]["Page_number"][0] + count,
#                                 batch[i]["Page_number"][1],
#                             )
#                             break
#                         count += 1

#         # Avoid cross-label adjustments
#         if current_label != prev_label:
#             prev_none_count = 0
#             prev_page_number = None
#             prev_label = current_label
#             continue

#         # Count consecutive None entries
#         if batch[num]["Page_number"][0] is None:
#             prev_none_count += 1
#         else:
#             if prev_none_count >= 1 and start - 1 <= prev_none_count:
#                 for i in range(1, prev_none_count + 1):
#                     if start - i <= 0:
#                         break
#                     batch[num - i]["Page_number"] = (start - i, end)
#                 prev_none_count = 0

#         prev_label = current_label
#         prev_page_number = batch[num]["Page_number"][0]

#     # Reverse validation for backward continuity
#     reverse_keys = list(batch.keys())[::-1]
#     prev_page_number = None
#     prev_label = None

#     for num in reverse_keys:
#         start, end = batch[num]["Page_number"]
#         current_label = batch[num]["label"]

#         # Avoid backward adjustments across labels
#         if current_label != prev_label:
#             prev_page_number = None
#             prev_label = current_label
#             continue

#         if start is None and prev_page_number is not None:
#             batch[num]["Page_number"] = (prev_page_number - 1, end)

#         prev_label = current_label
#         prev_page_number = batch[num]["Page_number"][0]

def check_relevency_with_previous_page(prev_page, current_page):
    # Find the intersection of words between the two pages.
    common_words = set(prev_page) & set(current_page)

    # Calculate the relevancy score as 10 points for each common word.
    return 10 * len(common_words)
