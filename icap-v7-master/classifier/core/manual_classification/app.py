import copy

from core.manual_classification.utils.text_utils import merge_dictionary
from core.manual_classification.processing.page_processing import handle_sheets, preprocess_page
from core.manual_classification.processing.classification import analyze_triggers
import traceback
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
        try:
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
        except Exception as e:
            traceback.print_exc()
            print(f"Error in train function: {e}")
           

