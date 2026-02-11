#Global Import
import copy
import xml.etree.ElementTree as ET
# Local Import
from core.title_classfication.utils.text_utils import detect_avoiding_entities, find_location
from core.title_classfication.utils.rajson_utils import create_page_json, create_style_list_json
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

def create_cat_dict(cat):
    new_dict = {}
    for key in cat:
        new_dict[key] = 0
    return new_dict

def create_key_map(matrix):

    new_matrix = {}

    for label, keywords in matrix.items():
        # Create a dictionary for this label with all keyword weights set to zero.
        temp = {k: 0 for k in keywords.keys()}

        # Add the updated dictionary to the new matrix.
        new_matrix[label] = temp

    # Return the newly created matrix with zero-initialized weights.
    return new_matrix

def extract_ids(all_lines):
    all_ids = []

    # Iterate over each line in the provided text.
    for line in all_lines:
        # Split the line into individual words.
        for word in line.split(" "):
            # Count the number of digits in the word.
            digits = sum(c.isdigit() for c in word)
            
            # Check if the word qualifies as an ID:
            # - It must have at least 4 characters.
            # - It must contain more digits than non-digits.
            if len(word) >= 4 and digits >= (len(word) - digits):
                all_ids.append(word)  # Add the word to the list of IDs.

    # Return the list of detected IDs.
    return all_ids

#  function extracts document identifiers (e.g., numbers, IDs) from a document's text content
def find_document_ids(doc, style_list, extremas, category, scan_threshold=40):
    if len(style_list) == 0:
        return 0

    bottom_limit = extremas[1] + (extremas[3] - extremas[1]) * (40 / 100)
    all_line_text = []
    for line in doc:
        # Calculate the vertical limit for scanning, based on the bounding box and scan threshold.
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


def boundaries_fix(batch,boundaries):
    # Fix boundary when all previos pages has (None,None) page no
    boundaries_new = []
    for idx in range(len(boundaries) - 1):
        start = boundaries[idx]
        end = boundaries[idx + 1] - 1
        try:
            if idx!= 0  and start != end and batch[boundaries[idx-1]]["label"] == batch[boundaries[idx]]["label"] and batch[boundaries[idx+1]-1]["label"] != None and batch[boundaries[idx+1]-1]["label"] != batch[boundaries[idx]]["label"] and batch[boundaries[idx]+1]["label"] == batch[boundaries[idx+1]-1]["label"]:
                boundaries_new.append(boundaries[idx])
                boundaries_new.append(boundaries[idx]+1)
                print("######## Split Boundary correction method initiated from data_processing script following by page_validation script")
            elif start+1 == end and batch[start]["label"] != batch[end]["label"] and batch[end]["label"] != None:
                boundaries_new.append(boundaries[idx])
                boundaries_new.append(boundaries[idx]+1)
                print("######## Split Boundary correction method initiated from data_processing script following by page_validation script")
            else:
                boundaries_new.append(boundaries[idx])
            
            
        except:
            boundaries_new.append(boundaries[idx])
            pass
            
    boundaries_new.append(len(batch) + 1)  

    return boundaries_new



def split_documents(batch):

 
    splits = {}
    n_pages = len(batch)
    print(f"split_documents: total pages = {n_pages}")

    # 1. Forward-fill None labels
    for i in range(1, n_pages + 1):
        lbl = batch[i]["label"]
        if lbl is None or lbl == "None":
            new_lbl = batch[i - 1]["label"] if i > 1 else None
            print(f"split_documents: page {i} label was None, replacing with previous label={new_lbl}")
            batch[i]["label"] = new_lbl
        # else:
        #     print(f"split_documents: page {i} label unchanged={lbl}")

    # 2. Compute boundaries: new segment when Page_number[0] is None or 1
    boundaries = [1]
    for i in range(2, n_pages + 1):
        pg0 = batch[i]["Page_number"][0]
        if pg0 is None or pg0 == 1:
            boundaries.append(i)
    boundaries.append(n_pages + 1)
    print(f"split_documents: boundaries = {boundaries}")

    try:
        boundaries = boundaries_fix(batch,boundaries)
        
    except:
        pass
    
    # 3. Build segments
    for idx in range(len(boundaries) - 1):
        start = boundaries[idx]
        end = boundaries[idx + 1] - 1
            
        label = batch[start]["label"]
        #print(f"split_documents: segment pages {start}-{end}, assigned label='{label}'")
        splits.setdefault(label, []).append((start, end))

    print(f"split_documents: result splits = {splits}")
    return splits
    
    # merged_segments = {}
    # for label, segs in splits.items():
    #     if not segs:
    #         continue
    #     # Sort segments by start page (should already be ordered, but ensure)
    #     segs.sort(key=lambda x: x[0])
    #     merged = []
    #     current_start, current_end = segs[0]
    #     for start, end in segs[1:]:
    #         if current_end + 1 >= start:
    #             current_end = max(current_end, end)
    #         else:
    #             merged.append((current_start, current_end))
    #             current_start, current_end = start, end
    #     merged.append((current_start, current_end))
    #     merged_segments[label] = merged

    # return merged_segments


def preprocessing_rajson_withoutPrintArea(page_dict, style_prob=40):
    style_list = create_style_list_json(page_dict, style_prob=style_prob)
    doc, extremas = create_page_json(page_dict)
    return doc, style_list, extremas