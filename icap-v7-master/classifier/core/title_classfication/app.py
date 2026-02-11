from core.title_classfication.processing.data_processing import merge_dictionary, preprocessing_rajson_withoutPrintArea, find_document_ids, split_documents
from core.title_classfication.processing.classifier import predict_layout, write_to_txt_file
from core.title_classfication.validation.page_validation import predict_page_number_v2, check_relevency_with_previous_page,fix_page_number
import json
import re


def write_ra_json_to_txt_file(text: str):
    
    print("")
    with open("/batches/ra_json.txt", 'a', encoding='utf-8') as file:
        file.write(text + '\n\n')
        file.flush() 

def contains_email_file_pattern(text: str) -> bool:
    pattern = r'email_file(?:_\d+)?\.pdf'
    return re.search(pattern, text) is not None


def predictLabel(
    json_file_path,
    page_range,
    category,
    custom_category,
    memory_points,
    priority_direction,
    project,
    automatic_split=True,
):
    
    print("\n=== predictLabel start ===")
    # print(f"Input: {json_file_path=}, {page_range=}, {category=}, {custom_category=}, {memory_points=}, {priority_direction=}, {project=}, {automatic_split=}")
    category = merge_dictionary(category, custom_category)
    details = {}
    without_split_labels = {}
    count = 1

    with open(json_file_path[0], "r", encoding="utf-8") as f:
        data = json.load(f)
        
    write_ra_json_to_txt_file(f"{data}")
    write_ra_json_to_txt_file(f"{page_range}")
    write_ra_json_to_txt_file(f"{custom_category}")
    write_ra_json_to_txt_file(f"{project}")
    write_ra_json_to_txt_file(f"{automatic_split}")

    all_docs = data.get("nodes", [])
    all_pages = []
    for doc_idx, doc_obj in enumerate(all_docs):
        # print(f"Processing Document #{doc_idx} with id={doc_obj.get('id', None)}")
        if contains_email_file_pattern(doc_obj["file_path"]):
            continue
        for page_idx, page_dict in enumerate(doc_obj.get("children", [])):
            # print(f"  Found Page #{page_idx} with id={page_dict.get('id', None)}")
            all_pages.append((doc_idx, page_idx, page_dict))

    # print(f"Total pages detected (across all docs): {len(all_pages)}")

    for current_range in page_range:
        # print(f"\nPage range: {current_range}")
        page_details = {}
        page_count = 0
        prev_doc_ids = None
        for idx_tuple in all_pages[current_range[0] - 1 : current_range[1]]:
            doc_idx, page_idx, page_dict = idx_tuple
            # print(f"\n--- Processing Doc {doc_idx} Page {page_idx} id={page_dict.get('id', None)} ---")
            try:
                page, style_list, extremas = preprocessing_rajson_withoutPrintArea(
                    page_dict
                )
                # print(f"Page built. Lines: {len(page)} | Styles: {style_list} | Extremas: {extremas}")

                matrix_prob = None
                label, title_prob, matrix_prob, matrix_status = predict_layout(
                    page,
                    category,
                    memory_points,
                    style_list,
                    extremas,
                    priority_direction,
                )
                print("#############")
                write_to_txt_file("#############")
                print(label)
                write_to_txt_file(f"{label}")
                print(title_prob)
                write_to_txt_file(f"{title_prob}")
                

                try:
                    if label == "Blank":
                        page_number = (None, None)
                    else:
                        page_number = predict_page_number_v2(
                            page, priority_direction["page_direction"], extremas
                        )
                except Exception as e:
                    print("predict_page_number_v2 exception:", e)
                    page_number = (None, None)
                    
                print(page_number)
                write_to_txt_file(f"{page_number}")
                write_to_txt_file("#############")
                print("#############")
                
                
                if label is None:
                    label = "None"

                rel_score = 0
                try:
                    if len(style_list) > 0:
                        current_doc_ids = find_document_ids(
                            page, style_list, extremas, category
                        )
                        # print(f"current_doc_ids={current_doc_ids}")
                        if prev_doc_ids is not None:
                            rel_score = check_relevency_with_previous_page(
                                prev_doc_ids, current_doc_ids
                            )
                            # print(f"rel_score={rel_score}")
                        prev_doc_ids = current_doc_ids
                except Exception as e:
                    print("find_document_ids/check_relevency_with_previous_page exception:", e)
                    rel_score = 0
                    
                max_score = max(title_prob.values(), default=0)

                if max_score == 0 and page_number:
                    current_page, total_pages = page_number
                    prev_page = count - 1

                    if (
                        current_page > 1
                        and total_pages > 1
                        and prev_page in details
                        and details[prev_page].get("Page_number") == (current_page - 1, total_pages)
                    ):
                        label = details[prev_page].get("label")
                        matrix_status = 3    
                

                page_details[page_count] = {
                    "File_path": json_file_path,
                    "Doc_Index": doc_idx,
                    "Page_Index": page_idx,
                    "label": label,
                    "Score1": title_prob,
                    "Score2": matrix_prob,
                    "Page_number": page_number,
                    "rel_score": rel_score,
                    "used matrix": matrix_status,
                }
                details[count] = dict(page_details[page_count])  # Make a copy
                # print(f"Page result: {details[count]}")
                count += 1
            except Exception as e:
                print("Exception in page processing:", e)
                details[count] = {
                    "File_path": json_file_path,
                    "Doc_Index": doc_idx,
                    "Page_Index": page_idx,
                    "label": None,
                    "Score1": None,
                    "Score2": None,
                    "Page_number": (None, None),
                    "rel_score": 0,
                    "used matrix": 0,
                }
                count += 1

    # print("\n=== Finished processing pages. Details ===")
    # for k, v in details.items():
    #     print(f"details[{k}]: {v}")

    if len(details) > 0:
        if automatic_split == True:
            try:
                fix_page_number(details)
                detected_labels = split_documents(details)
                print("Result from split_documents:", detected_labels)
                return detected_labels
            except Exception as e:
                # print("split_documents/fix_page_number exception:", e)
                return {"None": [(1, len(all_pages))]}
        else:
            try:
                for current_range in page_range:
                    for i in range(current_range[0], current_range[1] + 1):
                        if details[i]["label"] == "None":
                            if i == current_range[1]:
                                if "None" not in without_split_labels:
                                    without_split_labels["None"] = [(current_range[0], current_range[1])]
                                else:
                                    without_split_labels["None"].append((current_range[0], current_range[1]))
                                break
                            else:
                                continue
                        if details[i]["label"] is not None:
                            if details[i]["label"] not in without_split_labels:
                                without_split_labels[details[i]["label"]] = [(current_range[0], current_range[1])]
                                break
                            else:
                                without_split_labels[details[i]["label"]].append((current_range[0], current_range[1]))
                                break
                        if i == current_range[1]:
                            if "None" not in without_split_labels:
                                without_split_labels["None"] = [(current_range[0], current_range[1])]
                            else:
                                without_split_labels["None"].append((current_range[0], current_range[1]))
                            break
                # print("Result from without_split_labels:", without_split_labels)
                return without_split_labels
            except Exception as e:
                print("Exception in non-split label processing:", e)
                return {"None": [1, len(all_pages)]}
    return {"None": [1, len(all_pages)]}
