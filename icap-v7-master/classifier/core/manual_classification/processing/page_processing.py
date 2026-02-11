from core.manual_classification.utils.text_utils import detect_dates, detect_phone_numbers, find_location
from core.manual_classification.utils.bbox_utils import find_text_bbox
from core.title_classfication.processing.data_processing import preprocessing_rajson_withoutPrintArea
import json


# def check_duplicate_trigger(merged_category, custom_category, processed_page):
#     for idx in range(len(processed_page["trigger"])):
#         trigger = processed_page["trigger"][idx]["pattern"]
#         remarks = None
#         for key in merged_category.keys():
#             for k in merged_category[key]:
#                 if k.lower() == trigger.lower():
#                     # print(k.lower(), trigger.lower())
#                     processed_page["trigger_landmarks"][idx]["unique_trigger"] = 0
#                     processed_page["remarks"][idx].append(
#                         "The same key is already present in catgory: " + key
#                     )
#                     if (
#                         key in custom_category
#                         and trigger.lower() in custom_category[key]
#                     ):
#                         custom_category[key].remove(trigger.lower())
#         break
#REFACTORED
def check_duplicate_trigger(merged_categories: dict, custom_categories: dict, processed_page: dict) -> None:
    """
    Checks for duplicate triggers in the processed page and updates remarks.

    Method Parameters:
    ----------
    merged_categories : dict
        Dictionary of all categories with their associated triggers.
        Format: {category_name: [trigger1, trigger2, ...], ...}

    custom_categories : dict
        Dictionary of custom categories with triggers.
        Format similar to merged_categories. Triggers found in duplicates
        will be removed from this dictionary if they exist.

    processed_page : dict
        Dictionary representing a page with triggers and metadata.
        Must contain the following keys:
        - "trigger": list of dicts with key "pattern" representing trigger text.
        - "trigger_landmarks": list of dicts with key "unique_trigger" (int, initially 1)
        - "remarks": list of lists of strings, where remarks will be appended.

    Returns:
    -------
    None
        Updates the processed_page(input) and custom_categories(input) dictionaries in place.
    """
    for idx, trigger_info in enumerate(processed_page["trigger"]):
        trigger_text = trigger_info["pattern"]
        
        for category_name, triggers in merged_categories.items():
            for existing_trigger in triggers:
                if existing_trigger.lower() == trigger_text.lower():
                    # Mark as duplicate in processed page
                    processed_page["trigger_landmarks"][idx]["unique_trigger"] = 0
                    
                    # Add remark about duplication
                    processed_page["remarks"][idx].append(
                        f"The same key is already present in category: {category_name}"
                    )
                    
                    # Remove from custom category if present
                    if category_name in custom_categories and trigger_text.lower() in custom_categories[category_name]:
                        custom_categories[category_name].remove(trigger_text.lower())


# def get_trigger_landmarks(processed_page, category):
#     processed_page["trigger_landmarks"] = []
#     processed_page["remarks"] = []
#     extremas = processed_page["extremas"]
#     if len(processed_page["trigger"]) > 0:
#         for trigger in processed_page["trigger"]:
#             trigger_landmarks = {
#                 "entity check": 0,
#                 "unique_trigger": 0.5,
#                 "Trigger_line_text_match": 0,
#                 "top_position": 0,
#                 "font_weight": 0,
#                 "font_size": 0,
#                 "classification": 0,
#             }
#             remarks = []
#             trigger_pos = list(map(int, trigger["pos"].split(",")))
#             bottom_limit = extremas[1] + (extremas[3] - extremas[1]) * (40 / 100)
#             box_text = find_text_bbox(processed_page["page_text"], trigger_pos)
#             # print(box_text)
#             if (
#                 len(detect_phone_numbers(trigger["pattern"])) != 0
#                 or len(detect_dates(trigger["pattern"])) != 0
#                 or find_location(trigger["pattern"], category) != False
#             ):
#                 remarks.append(
#                     "You cannot select phone number, date and time and location as a trigger"
#                 )
#                 trigger_landmarks["entity check"] = -3

#             if trigger["pattern"].lower() == box_text[1].lower():
#                 trigger_landmarks["Trigger_line_text_match"] = 1.5
#             else:
#                 remarks.append("position of the trigger is not good")

#             if trigger_pos[1] <= bottom_limit:
#                 trigger_landmarks["top_position"] = 1
#             else:
#                 remarks.append("not found in top 40% of the page")

#             if (
#                 "font-weight"
#                 in processed_page["f_style"][int(trigger["style_id"])].keys()
#             ):
#                 trigger_landmarks["font_weight"] = 1
#             else:
#                 remarks.append("fonts are not bold")

#             if processed_page["f_style"][int(trigger["style_id"])]["font-size"] > 25:
#                 trigger_landmarks["font_size"] = (
#                     processed_page["f_style"][int(trigger["style_id"])]["font-size"]
#                     / 20
#                 )
#             else:
#                 remarks.append("font size too small")

#             processed_page["trigger_landmarks"].append(trigger_landmarks)
#             processed_page["remarks"].append(remarks)
#     else:
#         processed_page["remarks"] = [["No trigger was selected"]]

#refactoring

def check_if_trigger_is_an_entity(trigger_text: str, category: dict) -> tuple[int, list]:
    """
    Checks if a trigger is an invalid entity (phone number, date/time, location).

    Parameters
    ----------
    trigger_text : str
        The trigger text to check.
    category : dict
        Dictionary of categories for location detection.

    Returns
    -------
    entity_score : int
        -3 if invalid entity, 0 otherwise.
    remarks : list
        List of remarks if invalid.
    """
    remarks = []
    if (
        len(detect_phone_numbers(trigger_text)) != 0
        or len(detect_dates(trigger_text)) != 0
        or find_location(trigger_text, category) != False
    ):
        remarks.append(
            "You cannot select phone number, date and time and location as a trigger"
        )
        return -3, remarks
    return 0, remarks


def get_trigger_landmarks(processed_page: dict, category: dict) -> None:
    """
    Calculates landmark features for each trigger in a processed page and generates remarks.

    Each trigger is evaluated for:
    - Entity type validity (phone number, date, location)
    - Text match with its bounding box
    - Position on page (top 40%)
    - Font weight (bold)
    - Font size

    The function updates the processed_page (input) dictionary in-place.

    Method Parameters
    ----------
    processed_page : dict.
        Must contain:
        - "trigger": list of dicts, each with "pattern", "pos", "style_id"
        - "extremas": list or tuple of page boundaries (x_min,y_min,x_max,y_max)
        - "page_text": full page text
        - "f_style": list of dicts with font family properties ("font-size", optional "font-weight")
    category : dict
        dictionary of categories used for location detection.

    Returns
    -------
    None
        Updates "processed_page" with:
        - "trigger_landmarks": list of dicts with calculated feature scores
        - "remarks": list of lists containing remarks per trigger
    """
    #storing features and remarks for each trigger
    processed_page["trigger_landmarks"] = []
    processed_page["remarks"] = []

    extremas = processed_page["extremas"]  

    #check if there are any triggers
    if len(processed_page["trigger"]) > 0:
        for trigger_info in processed_page["trigger"]:
            landmark_features = {
                "entity check": 0,              
                "unique_trigger": 0.5,          
                "Trigger_line_text_match": 0,  
                "top_position": 0,              
                "font_weight": 0,              
                "font_size": 0,                 
                "classification": 0,           
            }
            remarks = []  #remarks for current trigger

            #parsing trigger position string into int
            trigger_pos = list(map(int, trigger_info["pos"].split(",")))

            bottom_limit = extremas[1] + (extremas[3] - extremas[1]) * 0.4

            box_text = find_text_bbox(processed_page["page_text"], trigger_pos)

            #check if trigger is invalid (phone number, date, or location)
            landmark_features["entity check"], entity_remarks = check_if_trigger_is_an_entity(trigger_info["pattern"], category)
            remarks.extend(entity_remarks)

            #checking if trigger text matches the text in its bounding box
            if trigger_info["pattern"].lower() == box_text[1].lower():
                landmark_features["Trigger_line_text_match"] = 1.5
            else:
                remarks.append("position of the trigger is not good")

            # if trigger is in the top 40% of the page
            if trigger_pos[1] <= bottom_limit:
                landmark_features["top_position"] = 1
            else:
                remarks.append("not found in top 40% of the page")

            #checking if font is bold
            font_style = processed_page["f_style"][int(trigger_info["style_id"])]
            if "font-weight" in font_style:
                landmark_features["font_weight"] = 1
            else:
                remarks.append("fonts are not bold")

            #if font size is sufficiently large
            if font_style["font-size"] > 25:
                landmark_features["font_size"] = font_style["font-size"] / 20
            else:
                remarks.append("font size too small")

            processed_page["trigger_landmarks"].append(landmark_features)
            processed_page["remarks"].append(remarks)
    else:
        #no triggers so default remark
        processed_page["remarks"] = [["No trigger was selected"]]


def assign_color_score(page_list: list[dict]) -> None:
    """
    Assigns a color score to each page based on landmark scores, user classification, 
    and manual classification. Also calculates a normalized score.

    Method Parameters
    ----------
    page_list : list of dict
        Each dict represents a page and must include keys such as:
        - "trigger_landmarks": list of landmark dictionaries (optional)
        - "user_classified_doc_type": user-provided classification (optional)
        - "manual_classified_doc_type": manual or automatic classification (optional)
        - "trigger": list of triggers (optional)

    Returns
    -------
    None
        Updates each page dict in-place with:
        - "color": str ("green", "yellow", "red") based on classification and scores
        - "score": float (normalized landmark score, if applicable)
    """
    for page in page_list:
        # --- A) If the user classified and we have trigger_landmarks, score by landmark values ---
        if page.get("user_classified_doc_type") and page.get("trigger_landmarks"):
            # sum up the first landmark dict’s values
            landmark_score = sum(page["trigger_landmarks"][0].values())

            # baseline: green if user vs manual match
            if page["user_classified_doc_type"] == page.get("manual_classified_doc_type"):
                page["color"] = "green"

            # override by score thresholds
            if landmark_score >= 8:
                page["color"] = "green"
            elif landmark_score >= 6:
                page["color"] = "yellow"
            else:
                page["color"] = "red"

            # record normalized score
            page["score"] = landmark_score / 100

            # finally, if the user vs manual still mismatch, force red
            if page["user_classified_doc_type"] != page.get("manual_classified_doc_type"):
                page["color"] = "red"

        # --- B) If there are no triggers at all, simple green/red logic ---
        elif len(page.get("trigger", [])) == 0:
            # green if they agreed or user never classified, else red
            if (
                page.get("user_classified_doc_type") == page.get("manual_classified_doc_type")
                or not page.get("user_classified_doc_type")
            ):
                page["color"] = "green"
            else:
                page["color"] = "red"

        # --- C) If we never got a manual prediction, mark red ---
        if page.get("manual_classified_doc_type") is None:
            page["color"] = "red"



"""
[
{
"user_classified_doc_type":"Commercial Invoice",
"trigger":[{
    "pattern":"invoice",
    "pos": "200,300,400,200",
    "style_id":2,
    "x_percentage":10,
    "y_percentage":20,
    "color":'red'
 
}],
"auto_classified_doc_type":"Commercial Invoice",
"layout_file_path":"path"
}
]
"""


# def preprocess_page(page_list, ra_json_path):
#     # Load your RA-JSON file once
#     try:
#         with open(ra_json_path[0], "r", encoding="utf-8") as f:
#             data = json.load(f)
#     except Exception as e:
#         print(f"preprocess_page: Failed to load RA-JSON '{ra_json_path}': {e}")
#         # If JSON can't load, mark all pages as empty and return
#         for page in page_list:
#             page["page_text"] = []
#             page["f_style"]   = []
#             page["extremas"]  = [None, None, None, None]
#             page["remarks"]   = None
#         return page_list

#     all_docs = data.get("nodes", [])

#     for page in page_list:
#         file_idx = page.get("file_index", 0)
#         page_idx = page.get("page_index", 0)
#         try:
#             doc_obj   = all_docs[file_idx]
#             page_dict = doc_obj["children"][page_idx]
#         except Exception as e:
#             # print(f"preprocess_page: Cannot find page for file_index={file_idx}, page_index={page_idx}: {e}")
#             page["page_text"] = []
#             page["f_style"]   = []
#             page["extremas"]  = [None, None, None, None]
#             page["remarks"]   = None
#             continue

#         try:
            
#             page_text, f_style, extremas = preprocessing_rajson_withoutPrintArea(page_dict)
#             page["page_text"] = page_text
#             page["f_style"]   = f_style
#             page["extremas"]  = extremas
#         except Exception as e:
#             print(f"preprocess_page: Error processing page {page_idx} of file {file_idx}: {e}")
#             page["page_text"] = []
#             page["f_style"]   = []
#             page["extremas"]  = [None, None, None, None]

#         page["remarks"] = None

#     return page_list

#refactoring
def set_default_page_values(page: dict) -> None:
    """
    Assigns default values to a page dictionary when preprocessing fails.

    Method Parameters
    ----------
    page : dict
        The page dictionary to update in place.

    Returns
    -------
    None
        Updates page with default empty content and None remarks.
    """
    page["page_text"] = []
    page["f_style"]   = []
    page["extremas"]  = [None, None, None, None]
    page["remarks"]   = None


def preprocess_page(page_list: list[dict], ra_json_path: list[str]) -> list[dict]:
    """
    Preprocesses each page in page_list using RA-JSON data.

    For each page, extracts:
    - page_text: text content of the page
    - f_style: font style information
    - extremas: bounding box of page content

    If any step fails, defaults are assigned:
    - page_text = []
    - f_style = []
    - extremas = [None, None, None, None]

    Method Parameters
    ----------
    page_list : list of dict
        List of pages to preprocess. Each page dict should include:
        - "file_index": index of the file in RA-JSON
        - "page_index": index of the page in the file
    ra_json_path : list of str
        List containing path(s) to RA-JSON file(s). Only the first path is used.

    Returns
    -------
    list of dict
        Updated page_list with keys:
        - "page_text"
        - "f_style"
        - "extremas"
        - "remarks"
    """
    try:
        with open(ra_json_path[0], "r", encoding="utf-8") as f:
            ra_data = json.load(f)
    except Exception as e:
        print(f"preprocess_page: Failed to load RA-JSON '{ra_json_path}': {e}")
        # If JSON can't load, mark all pages as empty and return
        for page in page_list:
            set_default_page_values(page)
        return page_list

    all_documents = ra_data.get("nodes", [])

    for page in page_list:
        file_idx = page.get("file_index", 0)
        page_idx = page.get("page_index", 0)

        #extracting the page object from RA-JSON ---
        try:
            document_obj = all_documents[file_idx]
            page_dict = document_obj["children"][page_idx]
        except Exception as e:
            #assigning default values if page object is not found
            set_default_page_values(page)
            continue

        #preprocessing page content
        try:
            page_text, f_style, extremas = preprocessing_rajson_withoutPrintArea(page_dict)
            page["page_text"] = page_text
            page["f_style"]   = f_style
            page["extremas"]  = extremas
        except Exception as e:
            print(f"preprocess_page: Error processing page {page_idx} of file {file_idx}: {e}")
            page["page_text"] = []
            page["f_style"]   = []
            page["extremas"]  = [None, None, None, None]

        page["remarks"] = None

    return page_list


def update_category(page_list: list[dict], custom_category: dict) -> dict:
    """
    Updates the custom category dictionary based on user-classified pages.

    For each page:
    - If the page has a valid user classification and at least one trigger
    - And the page color is "green" or "yellow"
    - The first trigger's pattern (lowercased) is added to the custom category 
      under the page label.

    Parameters
    ----------
    page_list : list of dict
        List of pages, each containing:
        - "user_classified_doc_type": user-provided classification
        - "trigger": list of triggers, each with "pattern"
        - "color": str ("green", "yellow", "red")

    custom_category : dict
        Dictionary mapping category labels to lists of triggers.

    Returns
    -------
    dict
        Updated custom_category dictionary with new triggers added.
    """
    for page in page_list:
        page_label = page["user_classified_doc_type"]
        #only update if user provided a label and triggers exist
        if page_label != None and page_label != "" and len(page["trigger"]) != 0:
            trigger = page["trigger"][0]["pattern"]
            #only include triggers from pages that are green or yellow
            if page["color"] in ("green", "yellow"):
                if page_label not in custom_category:
                    custom_category[page_label] = [trigger.lower()]
                else:
                    custom_category[page_label].append(trigger.lower())
    return custom_category


# handling page_list for name_matching doc type
def handle_name_matching(page_list: list[dict], page_range: list[tuple[int, int]]) -> list[dict]:
    """
    Updates pages within specified ranges if they have a name-matching document type.

    For each range in "page_range":
    - Iterate over pages in the range
    - If a page has a non-empty 'name_matching_doc_type':
        - Reset 'manual_classified_doc_type' to empty
        - Set 'start_index' to 1 for the first matching page in the range, 0 for subsequent pages
        - Add a remark indicating name matching

    Method Parameters:
    ----------
    page_list : list of dict
        List of pages, each containing:
        - "name_matching_doc_type": str
        - "manual_classified_doc_type": str
        - "remarks": list of lists
        - "start_index": int

    page_ranges : list of tuple(int, int)
        List of (start_page, end_page) indices (1-based) for ranges to process.

    Returns
    -------
    list of dict
        Updated page_list with name matching adjustments applied.
    """
    for idx in range(len(page_range)):
        start_index = 1
        for pg_idx in range(page_range[idx][0] - 1, page_range[idx][1]):
            if page_list[pg_idx]["name_matching_doc_type"] != "":
                page_list[pg_idx]["manual_classified_doc_type"] = ""
                page_list[pg_idx]["start_index"] = start_index
                page_list[pg_idx]["remarks"] = [["name matching doctype"]]
                start_index = 0

    return page_list


# handling page_list for excel sheets
def handle_sheets(page_list: list[dict]) -> list[dict]:
    """
    Updates pages that correspond to Excel sheets or layouts.

    For each page:
    - If 'layout_file_path' is None or empty, this indicates the page is an Excel sheet.
    - Resets 'manual_classified_doc_type' to None
    - Sets 'start_index' to 1
    - Adds a remark indicating it's an Excel sheet

    Method Parameters
    ----------
    page_list : list of dict
        List of pages, each containing:
        - "layout_file_path": str or None, path to layout file (Excel or other)
        - "manual_classified_doc_type": str or None
        - "remarks": list of lists
        - "start_index": int

    Returns
    -------
    list of dict
        Updated page_list after applying excel sheet adjustments.
    """
    for page in page_list:
        if page["layout_file_path"] in (None, ""):
            page["manual_classified_doc_type"] = None
            page["start_index"] = 1
            page["remarks"] = [["excel sheets"]]
    return page_list