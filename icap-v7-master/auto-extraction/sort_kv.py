
def group_by_page_id(data_list):

    grouped = {}
    
    for item in data_list:
        page_id = item.get('page_id')
        if page_id not in grouped:
            grouped[page_id] = []
        grouped[page_id].append(item)
    
    return grouped




# def sort_kv_by_position(data_json):
#     #This function sort the kv based on top left position
#     def get_sort_key(item):
#         pos = item['value_position']
#         if pos == "0,0,0,0":
#             return (float('inf'), float('inf'))
#         parts = pos.split(',')
#         left = float(parts[0])
#         top = float(parts[1])
#         return (top, left)

#     kv_list = data_json["key_data"]
#     kv_group_based_on_page = group_by_page_id(kv_list)
#     sorted_kv_list = []
#     for k,v in kv_group_based_on_page.items():
#         sorted_kv_list.extend(sorted(v, key=get_sort_key))

#     data_json["key_data"] = sorted_kv_list
#     return data_json







def sort_items_by_position(items_list, threshold=20):
    """
    Sort a list of items by position with grouping based on top position threshold.
    
    Args:
        items_list: List of items with 'value_position' field
        threshold: Maximum difference in top position for items to be in same group (default: 20)
    
    Returns:
        Sorted list of items
    """
    def get_position_values(item):
        pos = item['value_position']
        if pos == "0,0,0,0":
            return None  
        parts = pos.split(',')
        left = float(parts[0])
        top = float(parts[1])
        return (left, top)
    
    
    normal_items = []
    zero_items = []
    
    for item in items_list:
        if item['value_position'] == "0,0,0,0":
            zero_items.append(item)
        else:
            normal_items.append(item)
    
    
    normal_items.sort(key=lambda item: get_position_values(item)[1])
    
    
    groups = []
    current_group = []
    current_top = None
    
    for item in normal_items:
        _, item_top = get_position_values(item)
        
        if current_top is None or abs(item_top - current_top) <= threshold:
            current_group.append(item)
            if current_top is None or item_top < current_top:
                current_top = item_top  
        else:
            if current_group:
                groups.append(current_group)
            current_group = [item]
            current_top = item_top
    
    if current_group:
        groups.append(current_group)
    
    
    sorted_items = []
    for group in groups:
        
        sorted_group = sorted(group, key=lambda item: get_position_values(item)[0])
        sorted_items.extend(sorted_group)
    
    sorted_items.extend(zero_items)
    
    return sorted_items


def sort_kv_by_position(data_json, threshold=20):
    """
    Sort key-value pairs by position in the data_json structure.
    
    Args:
        data_json: Dictionary containing 'key_data' list
        threshold: Maximum difference in top position for items to be in same group (default: 20)
    
    Returns:
        Modified data_json with sorted key_data
    """
    
    
    kv_list = data_json["key_data"]
    kv_group_based_on_page = group_by_page_id(kv_list)
    
    sorted_kv_list = []
    
    for k,v in kv_group_based_on_page.items():
        sorted_kv_list.extend(sort_items_by_position(v, threshold))
        
    data_json["key_data"] = sorted_kv_list
    
    return data_json



def sort_kv_by_alphabet(data_json):
    kv_list = data_json["key_data"]
    
    sorted_kv_list = sorted(kv_list, key=lambda x: x["key"].lower())
    data_json["key_data"] = sorted_kv_list
    
    return data_json
    