import os
import xml.etree.ElementTree as ET
import json
from rapidfuzz import process, fuzz, utils
import re
import copy
import core.scripts.title_classification as classifier
import spacy
from typing import Union, List
#import traceback

nlp = spacy.load("/app/core/model/en_core_web_sm-3.7.1")


# Function to detect phone numbers
def detect_phone_numbers(text):
    """
    Detect phone numbers within a given text string.

    Method Parameters
    ----------
    text : str
        Input text to search for phone numbers.

    Returns
    -------
    list of str
        A list of phone numbers found in the text. 
        Matches common formats with optional '+' prefix, digits, spaces, dashes, or parentheses.
    """
    phone_pattern = re.compile(r"\+?\d[\d\s\-\(\)]{9,}")
    return phone_pattern.findall(text)


# Function to detect dates
def detect_dates(text):
    """
    Detect date expressions within a given text string.

    Parameters
    ----------
    text : str
        Input text to search for dates.

    Returns
    -------
    list of str
        A list of date strings found in the text.
        Supports formats like:
        - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
        - Dth Month YYYY (e.g., "12th March 2021"), etc
    """
    date_pattern = re.compile(
        r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b|\b\d{1,2}(?:th|rd|st|nd)?\s\w+\s\d{4}\b"
    )
    return date_pattern.findall(text)



def find_location(text, category):
    """
        Detect whether a given text refers to a location or organization, 
        while filtering out category keyword matches.

        Method Parameters
        ----------
        text : str
            Input text to analyze for potential location entities.
        category : dict[str, list[str]]
            Dictionary mapping category labels to lists of keywords. 
            If the text strongly matches any keyword (fuzzy score > 90), 
            the location check is skipped.

        Returns
        -------
        boolean
            True if the text contains a named entity labeled as a location (GPE) or organization (ORG).
            False if it strongly matches a category keyword or if no location/organization entity is found.
        """
    for label, keywords in category.items():
        # Using process.extractOne to find the best match within each category
        match, score, idx = process.extractOne(
            text, keywords, scorer=fuzz.WRatio, processor=utils.default_process
        )
        if score > 90:
            return False
    doc = nlp(text)

    for ent in doc.ents:
        if ent.label_ == "GPE" or ent.label_ == "ORG":
            return True
    return False



# takes the a list(page) by preprocessing_xml_withoutPrintArea  and a list of position(bounding box)as parameter and return the desired text inside the bounding box
def find_text_bbox(doc, box):
    """
    Extract text inside a given bounding box and also return the full line text(s).
    Example: doc = [
    [("Invoice", [10, 10, 50, 20]), ("No.", [60, 10, 80, 20]), ("12345", [90, 10, 140, 20])]
    ]
    box = [85, 5, 145, 25]   #will cover only "12345"

    returns -> ("12345", "Invoice No. 12345")

    Method Parameters
    ----------
    doc : list of list
        A list of lines, where each line is a list of words.
        Each word is a tuple: (word_text, [x_min, y_min, x_max, y_max]).
    box : list[int]
        Target bounding box [x_min, y_min, x_max, y_max].

    Returns
    -------
    tuple(str, str)
        - box_text: concatenated words fully inside the bounding box
        - trigger_line_text: concatenated full line text(s) where triggers were found
    """
    box_texts = []          #stores all words inside the bounding box
    trigger_line_text = ""  #stores full line(s) if that line contains the trigger word(s)

    if len(box) == 4:  #must have 4 coordinates
        for line in doc:
            line_box_text = ""  # Words inside the box for this line
            line_text = ""      #entire line text

            for word_text, (x1, y1, x2, y2) in line:
                #if the word is completely inside the box
                if box[0] <= x1 and box[1] <= y1 and box[2] >= x2 and box[3] >= y2:
                    line_box_text += word_text + " "
                line_text += word_text + " "

            #if any words matched inside the box, record both
            if line_box_text:
                box_texts.append(line_box_text)
                trigger_line_text += line_text

    return (" ".join(box_texts).strip(), trigger_line_text.strip())



def have_same_triggers(page_triggers: list[str], memory_triggers: list[str]) -> bool:
    """
    Checks if two lists of triggers contain the exact same elements, 
    ignoring order and duplicates.

    Method Parameters
    ----------
    page_triggers : list of str
        List of triggers from the current page.

    memory_triggers : list of str
        List of triggers stored in memory for comparison.

    Returns
    -------
    boolean
        True if both lists contain the same triggers, False otherwise.
    """
    return set(page_triggers) == set(memory_triggers)


def find_matches_master_category(page_triggers: List[str], user_category: str, updated_master_category: dict) -> Union[str, None]:
    """
    Finds a category in the master category dictionary that has the same triggers 
    as the current page, excluding the user's category.

    Method Parameters
    ----------
    page_triggers : list of str
        List of triggers from the current page.
    user_category : str
        The category assigned by the user; this category is skipped in the search.
    updated_master_category : dict
        Dictionary mapping category names to lists of trigger lists.

    Returns
    -------
    str or None
        Returns the first category in the master dictionary that has the same triggers
        as "page_triggers". Returns None if no match is found.
    """
    for category_name in updated_master_category:
        if category_name != user_category:
            for trigger_list in updated_master_category[category_name]:
                #if the page triggers match this list exactly
                if have_same_triggers(page_triggers, trigger_list):
                    return category_name
    return None


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

def get_page_path(page_list):
    """
    Extracts valid layout file paths from a list of page dictionaries.

    This function iterates over a list of dictionaries, where each value is a page.
    If a page has a non-empty and non-None value for the key "layout_file_path",
    that value is added to the result list.

    Method Parameters:
        page_list (list[dict]): A list of dictionaries where each dictionary 
            represents a page and contains a "layout_file_path" key.

    Returns:
        list[str]: A list of valid layout file paths, excluding None and empty strings.
    """
    path_list = []
    for page in page_list:
        if page["layout_file_path"] not in (None, ""):
            path_list.append(page["layout_file_path"])
    return path_list


# def map_predictions(page_list, prediction, path_list):
#     # print(prediction)
#     for cat in prediction:
#         for page_range in prediction[cat]:
#             # 1 means start of a document and 0 means continuation of a document
#             start_index = 1
#             for p_idx in range(page_range[0] - 1, page_range[1]):
#                 layout_path = path_list[p_idx]
#                 for idx in range(len(page_list)):
#                     if page_list[idx]["layout_file_path"] in (None, ""):
#                         page_list[idx]["manual_classified_doc_type"] = None
#                         page_list[idx]["start_index"] = 1
#                     if layout_path == page_list[idx]["layout_file_path"]:
#                         page_list[idx]["manual_classified_doc_type"] = cat
#                         if (
#                             page_list[idx]["user_classified_doc_type"] not in (None, "")
#                             and "trigger_landmarks" in page_list[idx]
#                         ):
#                             if page_list[idx]["user_classified_doc_type"] == cat:
#                                 page_list[idx]["trigger_landmarks"][0][
#                                     "classification"
#                                 ] = 4
#                             else:
#                                 if page_list[idx]["remarks"] == None:
#                                     page_list[idx]["remarks"] = [
#                                         ["classification failed."]
#                                     ]
#                                     page_list[idx]["color"] = "red"
#                                 else:
#                                     page_list[idx]["remarks"][0].append(
#                                         "classification failed."
#                                     )
#                                     page_list[idx]["color"] = "red"

#                         if start_index == 1:
#                             page_list[idx]["start_index"] = 1
#                             start_index = 0
#                         else:
#                             page_list[idx]["start_index"] = 0

def map_predictions(page_list, predictions, layout_paths):
    """
    Maps predicted document categories to corresponding pages and updates metadata.

    For each predicted category, this function iterates over page ranges and assigns
    the predicted classification to the appropriate pages based on their layout file paths. 
    It updates the following fields in each page dictionary:
    
    - "manual_classified_doc_type": Category assigned by the prediction.
    - "start_index": Marks the start (1) or continuation (0) of a classified document.
    - "trigger_landmarks": Updates classification results when user classification is present.
    - "remarks" and "color": Records mismatches between user classification and prediction.

    Args:
        page_list (list[dict]): A list of page dictionaries. Each page must include:
            - "layout_file_path" (str | None): The path of the layout file for the page.
            - "manual_classified_doc_type" (str | None): Field to store predicted category.
            - "user_classified_doc_type" (str | None): Category assigned by a user (optional).
            - "trigger_landmarks" (list[dict], optional): Landmarks with classification metadata.
            - "remarks" (list[list[str]], optional): Notes about mismatches.
            - "color" (str, optional): Indicator for mismatches.
        predictions (dict): Mapping of category → list of (start_page, end_page) tuples.
            Example: {"invoice": [(1, 3), (5, 5)], "receipt": [(4, 4)]}.
        layout_paths (list[str]): List of layout file paths indexed by page order.

    Returns:
        list[dict]: The updated page list with applied predictions and metadata changes. x (will not return)
    """
    for category in predictions:
        for page_range in predictions[category]:
            # 1 means start of a document and 0 means continuation of a document
            start_index = 1
            for page_idx in range(page_range[0] - 1, page_range[1]):
                layout_path = layout_paths[page_idx]
                for idx in range(len(page_list)):
                    if page_list[idx]["layout_file_path"] in (None, ""):
                        page_list[idx]["manual_classified_doc_type"] = None
                        page_list[idx]["start_index"] = 1
                    if layout_path == page_list[idx]["layout_file_path"]:
                        page_list[idx]["manual_classified_doc_type"] = category
                        if (
                            page_list[idx]["user_classified_doc_type"] not in (None, "")
                            and "trigger_landmarks" in page_list[idx]
                        ):
                            if page_list[idx]["user_classified_doc_type"] == category:
                                page_list[idx]["trigger_landmarks"][0]["classification"] = 4
                            else:
                                if page_list[idx]["remarks"] is None:
                                    page_list[idx]["remarks"] = [["classification failed."]]
                                    page_list[idx]["color"] = "red"
                                else:
                                    page_list[idx]["remarks"][0].append("classification failed.")
                                    page_list[idx]["color"] = "red"

                        if start_index == 1:
                            page_list[idx]["start_index"] = 1
                            start_index = 0
                        else:
                            page_list[idx]["start_index"] = 0
    #return page_list


def assign_color_score(page_list):
    """
    Assigns a color indicator and score to each page based on user classification,
    manual classification, and landmark scores.

    The function iterates through a list of page dictionaries and updates the following fields:
    - "color":
        - "green": Correct classification or high landmark score.
        - "yellow": Medium landmark score.
        - "red": Incorrect classification or low landmark score.
    - "score": normalized landmark score (landmark_score / 100) for pages that have landmarks.

    Rules:
    1. If a page has a user classification and landmarks:
       - Compute the sum of the first landmark dictionary values as landmark_score.
       - If user classification matches manual classification, set color to green (initializing it).
       - Adjust color based on landmark_score thresholds:
         - >=8 → green
         - >=6 → yellow
         - <6 → red
       - If user classification does not match manual classification, override color to red.
    2. If a page has no landmarks ("trigger" is empty):
       - Set color to green if user classification matches manual classification or is empty.
       - Otherwise, set color to red if a layout path exists.
    3. If manual classification is None but layout path exists, set color to red.

    Method Parameters:
        page_list (list[dict]): A list of dictionaries representing pages.
            (expected) Keys:
            - "user_classified_doc_type" (str | None): Classification given by the user.
            - "manual_classified_doc_type" (str | None): Predicted or manual classification.
            - "trigger_landmarks" (list[dict], optional): Landmark scores per page.
            - "trigger" (list, optional): Indicator of presence of landmarks.
            - "layout_file_path" (str | None): Path to the page's layout file.
            - "color" (str, optional): Field to store color indicator.
            - "score" (float, optional): Field to store normalized landmark score.

    Returns:
        None: The function updates the dictionaries in page_list in place.
    """
    for page in page_list:
        if (
            page["user_classified_doc_type"] not in (None, "")
            and "trigger_landmarks" in page
            and page["layout_file_path"] not in (None, "")
        ):
            landmark_score = sum(page["trigger_landmarks"][0].values())

            if page["user_classified_doc_type"] == page["manual_classified_doc_type"]:
                page["color"] = "Green"

            if landmark_score >= 8:
                page["color"] = "green"
                page["score"] = landmark_score / 100
            elif landmark_score >= 6:
                page["color"] = "yellow"
                page["score"] = landmark_score / 100
            else:
                page["color"] = "red"
                page["score"] = landmark_score / 100

            if page["user_classified_doc_type"] != page["manual_classified_doc_type"]:
                page["color"] = "red"
                page["score"] = landmark_score / 100

        if len(page["trigger"]) == 0:
            if (
                page["layout_file_path"] not in (None, "")
                and page["user_classified_doc_type"]
                == page["manual_classified_doc_type"]
            ) or page["user_classified_doc_type"] == "":
                page["color"] = "green"
            elif page["layout_file_path"] not in (None, ""):
                page["color"] = "red"

        if (
            "manual_classified_doc_type" in page
            and page["manual_classified_doc_type"] is None
            and page["layout_file_path"] not in (None, "")
        ):
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


# this will only be used for single triggers
def analyze_triggers(
    page_list,
    page_range,
    merged_category,
    custom_category,
    memory_points,
    priority_directions,
    project
):
    """
    Analyzes triggers in a list of pages, predicts document categories, updates classifications,
    handles sheets and name matching, and assigns color-coded scores.

    1. Iterates through each page in page_list:
        - Retrieves the user-assigned document type.
        - If triggers are present, collect landmarks and updates merged categories.
        - Checks for duplicate triggers across the merged (input) and custom categories (input).
    2. Extracts valid layout file paths from pages.
    3. Uses a classifier to predict labels for the pages based on layout paths, categories, 
       memory points, and project-specific priority directions.
    4. Maps predictions back to the page_list, updating manual classifications and start indices.
    5. Performs additional post-processing:
        - Handles sheet-based data processing.
        - Performs name matching for further validation.
        - Assigns color-coded scores based on classification correctness and landmark scores.
    6. Updates and returns the custom category dictionary with applied classifications.

    Method Parameters:
        page_list (list[dict]): List of page dictionaries containing keys such as:
            - "user_classified_doc_type" (str | None)
            - "manual_classified_doc_type" (str | None)
            - "trigger" (list[dict])
            - "layout_file_path" (str | None)
            - Additional fields for remarks, landmarks, color, etc.
        page_range (tuple): Tuple indicating the range of pages to process (start, end).
        merged_category (dict.): Dictionary of existing merged categories for document types.
        custom_category (dict.): Dictionary of custom categories for document types.
        memory_points (dict.): Memory points used for classifier predictions.
        priority_directions (dict.): Project-specific priority information for classifier.
        project (str): Identifier for the current project context.

    Returns:
        dict.: Updated custom_category dictionary after applying predictions and post-processing.
    """
    for page in page_list:
        page_label = page["user_classified_doc_type"]
        if page_label != None and len(page["trigger"]) != 0:
            page_remarks = []
            page_triggers = []
            get_trigger_landmarks(page, merged_category)
            check_duplicate_trigger(merged_category, custom_category, page)
            for idx in range(len(page["trigger"])):
                if page_label in merged_category:
                    merged_category[page_label].append(
                        page["trigger"][idx]["pattern"].lower()
                    )
                else:
                    merged_category[page_label] = [
                        page["trigger"][idx]["pattern"].lower()
                    ]

    file_paths = get_page_path(page_list)
    predictions = classifier.predictLabel(
        file_paths, page_range, merged_category, {}, memory_points, priority_directions, project
    )

    map_predictions(page_list, predictions, file_paths)
    handle_sheets(page_list)
    handle_name_matching(page_list, page_range)
    assign_color_score(page_list)
    return update_category(page_list, custom_category)


def preprocess_page(page_list):
    """
    Preprocesses each page by extracting text, formatting, and extremas from its layout file.

    For pages with a valid 'layout_file_path', this function uses the classifier to extract:
        - page_text: textual content of the page
        - f_style: formatting/style information
        - extremas: extremal values or layout markers

    Pages without a valid layout path are initialized with default empty values.

    Method Parameters:
        page_list (list[dict]): List of page dictionaries containing 'layout_file_path'.

    Returns:
        list[dict]: Updated page_list with added keys: 'page_text', 'f_style', 'extremas', 'remarks'.
    """
    for page in page_list:
        if page["layout_file_path"] not in (None, ""):
            page_text, f_style, extremas = (
                classifier.preprocessing_xml_withoutPrintArea(page["layout_file_path"])
            )
            page["page_text"] = page_text
            page["f_style"] = f_style
            page["extremas"] = extremas
            page["remarks"] = None
        else:
            page["page_text"] = ""
            page["f_style"] = []
            page["extremas"] = 0
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


def merge_dictionary(dict1, dict2):
    """
    Merges two dictionaries.
        - If a category exists in both dictionaries, their triggers are combined without duplicates.
        - If a category exists only in dict2, it is added to the merged result.

    Method Parameters
    ----------
    dict1 : dict[str, list]
    dict2 : dict[str, list]

    Returns
    -------
    dict[str, list]
    """
    merged_dict = copy.deepcopy(dict1)
    for category in dict2.keys():
        if category in merged_dict:
            for trigger in dict2[category]:
                if trigger not in merged_dict[category]:
                    merged_dict[category].append(trigger)
        else:
            merged_dict[category] = dict2[category]

    return merged_dict


# will use to train new triggers, original_page_list
def train(
    original_page_list,
    page_range,
    master_category,
    custom_category,
    memory_points,
    priority_directions,
    project,
    ra_json_paths
):
    """
    Train the document classification system by preprocessing pages, 
    merging categories, and analyzing triggers.

    Parameters
    ----------
    original_page_list : list[dict]
        List of pages containing metadata and extracted features.
    page_range : list[tuple[int, int]]
        Ranges of pages to process (start, end).
    master_category : dict[str, list]
        The predefined master dictionary of categories and triggers.
    custom_category : dict[str, list]
        User-defined dictionary of categories and triggers.
    memory_points : list
        Historical data points to improve prediction.
    priority_directions : dict
        Rules or preferences that guide trigger priority.
    project : str
        Identifier for the project being processed.
    ra_json_paths : list[str]
        Paths to JSON files used for reference analysis.

    Returns
    -------
    tuple
        (updated_page_list, updated_custom_category)
        - updated_page_list : list[dict]
          The processed and cleaned page data.
        - updated_custom_category : dict[str, list]
          Updated custom categories with merged triggers.
    """

    if len(page_range) == 0:
        page_range = [(0, 0)]
        
        # handle_sheets(original_page_list)
        return original_page_list, custom_category  # successful 200/ error 404
    else:
        #try:
            merged_category = merge_dictionary(custom_category, master_category)
            copied_custom_category = copy.deepcopy(custom_category)
            copied_page_list = copy.deepcopy(original_page_list)
            copied_master_category = copy.deepcopy(master_category)
            updated_page_list = preprocess_page(copied_page_list,ra_json_paths)
            updated_custom_category = analyze_triggers(
                updated_page_list,
                page_range,
                merged_category,
                copied_custom_category,
                memory_points,
                priority_directions,
                project,
                ra_json_paths
            )
            
            # handling 'manual_classified_doc_type' for excel sheets
            for page in updated_page_list:
                page.pop("page_text")
                page.pop("f_style")

                if page.get("trigger_landmarks"):
                    page.pop("trigger_landmarks")

            return updated_page_list, updated_custom_category  # successful 200/ error 404
        # except Exception as e:
        #     traceback.print_exc()
        #     print(f"Error in train function: {e}")