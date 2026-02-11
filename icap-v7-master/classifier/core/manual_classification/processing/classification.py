from core.manual_classification.processing.page_processing import (get_trigger_landmarks,check_duplicate_trigger, 
                                                                   handle_sheets, handle_name_matching, assign_color_score, update_category)
from core.title_classfication.app import predictLabel

from typing import Union, List

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



# def find_matches_master_category(page_triggers, user_cat, updated_master_category):
#     for cat in updated_master_category:
#         if cat != user_cat:
#             for trigger_list in updated_master_category[cat]:
#                 if have_same_triggers(page_triggers, trigger_list):
#                     return cat
#     return None

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

# def get_page_path(page_list):
#     path_list = []
#     for page in page_list:
#         if page["layout_file_path"] not in (None, ""):
#             path_list.append(page["layout_file_path"])
#     # print(path_list)
#     return path_list

def update_trigger_landmarks_for_page(page: dict, predicted_doc_type: str) -> None:
    """
    Updates the trigger landmarks and page color if the page was already user-classified.

    Method Parameters
    ----------
    page : dict.
        Page dictionary containing keys like 'user_classified_doc_type', 'trigger_landmarks', 'remarks', 'color'.
    predicted_doc_type : str
        Document type predicted for the page.

    Returns
    -------
    None
        Updates the page in-place.
    """
    if page.get('user_classified_doc_type') and page.get('trigger_landmarks'):
        if page['user_classified_doc_type'] == predicted_doc_type:
            page['trigger_landmarks'][0]['classification'] = 4
        else:
            #adding remarks if failed and marking page color to red
            page.setdefault('remarks', [[]])[0].append('classification failed.')
            page['color'] = 'red'


def map_predictions(page_list: list[dict], predictions: dict) -> None:
    """
    Maps predicted document types to pages and updates classification metadata.

    For each predicted document type and its page ranges:
    - Assigns 'manual_classified_doc_type' to pages in the range.
    - Updates trigger landmarks if the page was already user-classified.
    - Sets 'start_index' to 1 for the first page in the range, 0 for others.
    - Adds remarks and updates color if classification failed.

    Parameters
    ----------
    page_list : list of dict
        List of page dictionaries to update.
        Each page can contain keys like 'user_classified_doc_type', 'trigger_landmarks', 'color', etc.

    predictions : dict
        Dictionary mapping document types to lists of 1-based indexing page ranges.
        Example: {"Invoice": [(1, 3), (5, 5)]}

    Returns
    -------
    None
        Updates "page_list" (input) in-place.
    """
    for predicted_doc_type, page_ranges in predictions.items():
        for start_1b, end_1b in page_ranges:
            is_first_page = True
            for idx in range(start_1b - 1, end_1b):
                page = page_list[idx]

                # Assign manual classification
                page['manual_classified_doc_type'] = predicted_doc_type

                # Update trigger landmarks if user-classified
                update_trigger_landmarks_for_page(page, predicted_doc_type)

                #Setting the start_index flag for first page in the range
                page['start_index'] = 1 if is_first_page else 0
                is_first_page = False



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


# def analyze_triggers(
#     page_list,
#     page_range,
#     merged_category,
#     custom_category,
#     memory_points,
#     priority_directions,
#     project,
#     ra_json_paths
# ):
#     for page in page_list:
#         page_label = page["user_classified_doc_type"]
#         if page_label != None and len(page["trigger"]) != 0:
#             page_remarks = []
#             page_triggers = []
#             get_trigger_landmarks(page, merged_category)
#             check_duplicate_trigger(merged_category, custom_category, page)
#             for idx in range(len(page["trigger"])):
#                 if page_label in merged_category:
#                     merged_category[page_label].append(
#                         page["trigger"][idx]["pattern"].lower()
#                     )
#                 else:
#                     merged_category[page_label] = [
#                         page["trigger"][idx]["pattern"].lower()
#                     ]

#     predictions = predictLabel(
#         ra_json_paths, page_range, merged_category, custom_category, memory_points, priority_directions,project
#     )
#     # print(predictions)
#     map_predictions(page_list, predictions)
#     # handle_sheets(page_list)
#     handle_name_matching(page_list, page_range)
#     assign_color_score(page_list)
#     return update_category(page_list, custom_category)

def analyze_triggers(
    page_list: list[dict],
    page_ranges: list[tuple[int, int]],
    merged_category: dict,
    custom_category: dict,
    memory_points: dict,
    priority_directions: dict,
    project: str,
    ra_json_paths: list[str]
) -> dict:
    """
    Processes pages to analyze triggers, update categories, predict labels, 
    and assign color scores.

    Workflow:
    1) For each page with a user-classified doc type and triggers:
        - Extract trigger landmarks
        - Check for duplicate triggers in merged and custom categories
        - Update the merged_category with the current page's triggers
    2) Predict labels for pages using RA JSON and categories
    3) Map predicted labels to the page list
    4) Handle pages identified via name matching
    5) Assign color scores to pages
    6) Update the custom category dictionary with new triggers

    Method Parameters
    ----------
    page_list : list of dict
        List of pages, each containing keys like 'trigger', 'user_classified_doc_type', etc.
    page_ranges : list of tuple(int, int)
        List of 1-based page ranges for processing (used for name matching method above)
    merged_category : dict
        Dictionary containing all categories and triggers combined
    custom_category : dict
        Dictionary containing user-defined categories and triggers
    memory_points : dict
        Memory points used for prediction
    priority_directions : dict
        Priority information for prediction
    project : str
        Project name
    ra_json_paths : list of str
        Paths to RA JSON files for predictions

    Returns
    -------
    dict.
        Updated custom_category dictionary with new triggers added.
    """
    for page in page_list:
        page_label = page.get("user_classified_doc_type")
        #only process pages with a user label and at least one trigger
        if page_label and len(page.get("trigger", [])) != 0:
            #extracting landmarks for triggers
            get_trigger_landmarks(page, merged_category)
            #checking for duplicate triggers in merged and custom categories
            check_duplicate_trigger(merged_category, custom_category, page)
            
            #updating merged_category with current page triggers
            for trigger in page["trigger"]:
                trigger_text = trigger["pattern"].lower()
                if page_label in merged_category:
                    merged_category[page_label].append(trigger_text)
                else:
                    merged_category[page_label] = [trigger_text]

    #predicting document types for page ranges
    predictions = predictLabel(
        ra_json_paths,
        page_ranges,
        merged_category,
        custom_category,
        memory_points,
        priority_directions,
        project
    )

    #Map predicted labels to the page list
    map_predictions(page_list, predictions)

    #handling pages identified via name matching
    handle_name_matching(page_list, page_ranges)

    #assigning color scores based on trigger landmarks and classification
    assign_color_score(page_list)
    
    return update_category(page_list, custom_category)
