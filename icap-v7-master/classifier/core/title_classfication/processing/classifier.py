
#Global Import
from rapidfuzz import process, fuzz, utils
#Local Import
import os
from .data_processing import create_key_map, create_cat_dict 
from core.title_classfication.utils.text_utils import special_filter, find_s_id

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


def write_to_txt_file(text: str):
    print("")
    # with open("/batches/log_file.txt", 'a', encoding='utf-8') as file:
    #     file.write(text + '\n')
    #     file.flush() 

def validate_label_for_trigger_duplication(best_label_prev,best_score_prev,cat_prob,best_matches_label_keyword_track,memory_points):

    def get_best_score_keys(scores_dict):
        """
        Returns a list of keys that have the highest score value.
        If multiple keys share the same highest score, all are returned.
        
        Args:
            scores_dict: Dictionary with keys as strings and values as scores (numbers)
        
        Returns:
            List of keys with the highest score
        """
        if not scores_dict:
            return []
        max_score = max(scores_dict.values())
        best_keys = [key for key, score in scores_dict.items() if score == max_score]
        
        return best_keys

    best_labels = get_best_score_keys(cat_prob)
    #print("^^^^^^^^^",best_labels)
    if len(best_labels) == 1:
        return best_label_prev,best_score_prev,cat_prob
    else:
        for idx, best_label in enumerate(best_labels):
            for item in best_matches_label_keyword_track.get(best_label,[]):
                cat_prob[best_label] += memory_points.get(best_label,{}).get(item,0)
                
        best_label = get_best_score_keys(cat_prob)[0]
        best_score = cat_prob[best_label]
        return best_label, best_score, cat_prob


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
            len(inp_str) > 4
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






def predict_layout(
    doc, category, memory_points, style_list, extremas, priority_direction, threshold=85
):
    matched_lines = []
    if len(style_list) == 0:
        return "Blank", {"Blank": 150}, None
    cat_prob = create_cat_dict(priority_direction["category"]) # line 901
    bottom_limit = extremas[1] + (extremas[3] - extremas[1]) * (40 / 100)
    dynamic_threshold = False
    best_matches_label_keyword_track = {}
    best_category, best_score = None, 0
    for i in range(2):
        for line in doc:
            if len(line) > 0 and line[0][1][1] <= bottom_limit:
                # build the string for the line
                inp_str = " ".join(
                    sublist[0] for sublist in line
                )  # concate the words of the line separated by space
                
                if (
                    len(inp_str) > 4
                ):  # only processing the string if the length of the string is 5
                    print(inp_str)
                    write_to_txt_file(inp_str)
                    for label, keywords in category.items():
                        # Using process.extractOne to find the best match within each category
                        match1, score, idx1 = process.extractOne(
                            inp_str,
                            keywords,
                            scorer=fuzz.token_set_ratio,
                            processor=utils.default_process,
                        ) # rapidfuzz used
                        match2, score2, idx2 = process.extractOne(
                            inp_str,
                            keywords,
                            scorer=fuzz.WRatio,
                            processor=utils.default_process,
                        ) #rapidfuzz used
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
                        
                        
                        ## Exception page handlingb section
                        if fuzz.ratio(inp_str.strip(),"CUSTOMS BROKERAGE") >= 95:
                            cat_prob["Miscellaneous Document"] += 50
                        if "SENDER LIABLE FOR UNPAID CHARGES" in inp_str.strip():
                            cat_prob["Proof Of Delivery"] += 50
                        if fuzz.ratio(inp_str.strip(),"TRANZITNA LISTA STAVKI") >= 95:
                            cat_prob["Proof Of Delivery"] += 50    
                            
                        if score >= 95:
                            matched_lines.append(inp_str)
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
                            
                            if label not in best_matches_label_keyword_track.keys():
                                best_matches_label_keyword_track[label] = [match1]
                            else:
                                best_matches_label_keyword_track[label].append(match1)
                            
                            s_id = find_s_id(line, match1) # line 341
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
        # print(cat_prob)
        # print(f"{cat_prob=}\n{matched_lines=}")
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
    
    write_to_txt_file(f"***********{best_matches_label_keyword_track}")
    write_to_txt_file(f"***********{best_category}, {best_score} , {cat_prob}")
    print("***********",best_matches_label_keyword_track)
    print("***********",best_category, best_score, cat_prob)
    
    best_category, best_score, cat_prob = validate_label_for_trigger_duplication(best_category, best_score, cat_prob, best_matches_label_keyword_track, memory_points)
    #print("^^^^****^^^^^^")
    cautionous_category1 = ["Airway Bill"]
    cautionous_category2 = ["Delivery Note"]
    cautionous_category3 = ["Commercial Invoice", "Packing List"]

    if cat_prob["Commercial Invoice"] == cat_prob["Airway Bill"] and cat_prob["Airway Bill"] >= 110:
        best_category = "Airway Bill"
        cat_prob["Commercial Invoice"] = 0 
        return "Airway Bill", cat_prob, cat_prob["Airway Bill"], 0

    if (
        best_category in cautionous_category3
        and 0 <= (cat_prob["Commercial Invoice"] - cat_prob["Packing List"]) <= 10
    ) or (best_category in cautionous_category3 and best_score <= 115):

        mat_label, mat_score = predict_for_matrix(doc, memory_points) #line 528
        if mat_label in ("Commercial Invoice", "Packing List"):
            return mat_label, cat_prob, mat_score, 1

    else:
        
        mat_label, mat_score = predict_for_matrix(doc, memory_points) #line 528
        print("***@@@@@@@@@@@",mat_label, mat_score)
        write_to_txt_file(f"***@@@@@@@@@@@ {mat_label},{mat_score}")
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


