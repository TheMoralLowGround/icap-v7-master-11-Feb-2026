import os
import json
import time  
import xml.etree.ElementTree as ET
import copy
from rapidfuzz import fuzz



class RAJson:
    # NODES is dictionary where every key is Type of element, we need to extract from XML file. Value associated to each key is the name to be outputted in resulting JSON File.
    # For example: Script will look for 'L' elements and put into json with type 'line'.
    NODES = {
        "Block": "block",
        "Table": "table",
        "Row": "row",
        "Cell": "cell",
        "Para": "paragraph",
        "Title": "paragraph",
        "L": "line",
        "W": "word",
    }

    NODE_KEYS = list(NODES.keys())

    def process_element(self, element):
        """
        This function reads attributes of given XML Tree element and return details
        in form of dictionary.
        Children property is generated recursively.
        """
        element_type = element.tag
        attrs = element.attrib
        attrs["type"] = self.NODES.get(element_type, element_type)

        if attrs["type"] == "word":
            children = []
        else:
            child_elements = [i for i in list(element) if i.tag in self.NODE_KEYS]
            children = [self.process_element(e) for e in child_elements]

        attrs["id"] = ""
        if children:
            attrs["children"] = children
        return attrs

    def process_PAGE(self, xml_file_path):
        """
        This function accepts path of XML file on disk, convert XML file into tree object,
        reads attributes root (PAGE) element and return details in form of dictionary.
        Children property is generated recursively.
        """
        tree = ET.parse(xml_file_path)
        PAGE = tree.getroot()
        attrs = PAGE.attrib
        attrs["type"] = "page"

        childrens = list(PAGE)

        # Add style info to styles key in page
        style_nodes = [i for i in childrens if i.tag == "Style"]
        attrs["styles"] = [i.attrib for i in style_nodes]

        # Filter only required elements
        childrens = [i for i in childrens if i.tag in self.NODE_KEYS]
        attrs["children"] = [self.process_element(e) for e in childrens]

        return attrs

    def pre_process_PAGE(self, P):
        """
        This function accepts Page element and generate XML file path based on Page ID.
        Then each page is processed using process_PAGE function.
        """
        page_id = P.get("id")
        export_attrs = {}
        for V in P.findall("./V"):
            key = V.get("n")

            # always rename imagefile to lowercase
            if key == "IMAGEFILE":
                export_attrs[key] = V.text.lower()
            else:
                export_attrs[key] = V.text

        xml_file_path = os.path.join(self.input_folder_path, f"{page_id}_layout.xml")

        page_attrs = self.process_PAGE(xml_file_path)
        page_attrs.update(export_attrs)
        return page_attrs


# Top parse positions (Left, Top, Right, Bottom)
def parse_pos(word_object):
    return [int(coordinate) for coordinate in word_object['pos'].split(",")]

def get_left_pos(word_object):
    return parse_pos(word_object)[0]

def get_right_pos(word_object):
    return parse_pos(word_object)[2]

def get_top_pos(word_object):
    return parse_pos(word_object)[1]

def get_bottom_pos(word_object):
    return parse_pos(word_object)[3]


def check_chunk(range_list, val1, val2, threshold, extra_space=0):
    """
    Check chunk threshold by using right and left pos of 2 object
    """
    val1_right_pos = val1["pos"].split(",")[2]
    val2_left_pos = val2["pos"].split(",")[0]
    
    val1_top_pos = val1["pos"].split(",")[1]
    val2_top_pos = val2["pos"].split(",")[1]
    
    difference = abs(int(val1_right_pos) - int(val2_left_pos))
    
    if threshold_check(int(val1_top_pos), int(val2_top_pos), int(threshold)):
        if int(difference) >= int(range_list[0]) and int(difference) <= (int(range_list[1]) + int(extra_space)):
            return True
        else:
            return False
    else:
        return False
    
def threshold_check(num1, num2, check_threshold):
    """
    Check if the difference between 2 number is less than threshold
    """
    return abs(int(num1) - int(num2)) <= int(check_threshold)

def chunk_node_to_word(chunk_list):
    """
    Convert Chunks data(with POS) to Word only
    """
    words = []
    
    pos = [get_left_pos(chunk_list[0]), get_top_pos(chunk_list[0]),
           get_right_pos(chunk_list[-1]), get_bottom_pos(chunk_list[0])]
    
    pos = [str(x) for x in pos]
        
    for chunk in chunk_list:
        words.append(chunk['v'])
    
    page_id = chunk_list[0]['id'].split(".")[0]
    
    return [" ".join(words), ",".join(pos), page_id]



def construct_sentences(word_dict):
    space_unit = 10  # Pixels per space (adjustable)
    line_height = 25  # Average line height in pixels (adjustable)
    sentences = []
    lines = word_dict[0]
    
    # Collect all words with their positions
    words_info = []
    for line_key in lines:
        word_list = lines[line_key]
        for word_entry in word_list:
            word = word_entry[0]
            position = word_entry[1]
            left, top, right, bottom = map(int, position.split(','))
            words_info.append({'word': word, 'left': left, 'top': top, 'right': right, 'bottom': bottom})
    
    # Sort words by top position, then by left position
    words_info.sort(key=lambda x: (x['top'], x['left']))
    
    # Initialize variables for tracking
    prev_line_num = None
    prev_bottom = None
    line_buffer = {}
    
    for word_info in words_info:
        # Calculate line number and character position
        line_num = int(word_info['top'] / line_height)
        char_pos = int(word_info['left'] / space_unit)
        
        # Handle vertical gaps
        if prev_line_num is not None and line_num > prev_line_num + 1:
            gap_lines = line_num - prev_line_num - 1
            for i in range(prev_line_num + 1, line_num):
                line_buffer[i] = ''  # Empty lines for gaps
        
        # Initialize line in buffer if not present
        if line_num not in line_buffer:
            line_buffer[line_num] = {}
        
        # Add word to line buffer at the calculated character position
        line_buffer[line_num][char_pos] = word_info['word']
        
        prev_line_num = line_num
        prev_bottom = word_info['bottom']
    
    # Build the final text lines
    max_line_num = max(line_buffer.keys())
    final_lines = []
    for i in range(max_line_num + 1):
        if i in line_buffer:
            line_content = line_buffer[i]
            # Build line string based on character positions
            if line_content:
                sorted_positions = sorted(line_content.keys())
                line_str = ''
                last_pos = 0
                for pos in sorted_positions:
                    spaces = pos - last_pos
                    line_str += ' ' * spaces + line_content[pos]
                    last_pos = pos + len(line_content[pos])
                final_lines.append(line_str.rstrip())
            else:
                final_lines.append('')
        else:
            final_lines.append('')  # Empty line
    
    # Remove leading and trailing empty lines
    while final_lines and not final_lines[0]:
        final_lines.pop(0)
    while final_lines and not final_lines[-1]:
        final_lines.pop()
    
    # Join lines into a single text
    return '\n'.join(final_lines)






# Get Page Level Data
def chunk_process_level_page(PAGE, line_threshold=10, chunk_threshold=20, extra_chunk_space=10):
    # Here we will hold data with chunking line also word only version
    data = dict()
    
    # Go through all the XML objects 
    for PAGE_ID, PAGE in enumerate([PAGE]):
        
        # Extract all the W_nodes
        W_nodes = []
        
        
        def find_all_words(data):
            if isinstance(data, list):
                for elem1 in data:
                    find_all_words(elem1)
            elif isinstance(data, dict):
                for k, v in data.items():
                    if (k=="type") and (v=="word"):
                        W_nodes.append(data)
                    elif isinstance(v, list):
                        find_all_words(v)
                    
        # Find All Word elements and put it into W_nodes
        find_all_words(PAGE['children'])

                    
        
        # Turn All the Data into Lines with Chuncking
        word_space_list = []
        
        for index, W_node in enumerate(W_nodes):
            try:
                current_node_pos = W_node["pos"]
                current_node_right_pos = current_node_pos.split(",")[2]
                
                next_node_pos = W_nodes[index+1]["pos"]
                next_node_left_pos = next_node_pos.split(",")[0]
                
                diffr = int(next_node_left_pos) - int(current_node_right_pos)
                
                if diffr<0:
                    pass
                else:
                    word_space_list.append(diffr)
                
            except (IndexError, ValueError):
                pass
            
        
        if not W_nodes:
            continue
        
        # Only if there is only 1 word
        if (len(W_nodes) == 1) or word_space_list==[]:
            word_space_list=[5]
            
        
        space_list = sorted(list(set(word_space_list)))
        
        
        space_range = [space_list[0], space_list[0]+20]
        
    
        """
        Make Chunks
        """
        chunk_list = []
        
        start_idx = 0
        end_idx = len(W_nodes)
        
        while True:
            temp_chunk = []
            
            while True:
                try:
                    check = check_chunk(space_range, W_nodes[start_idx], W_nodes[start_idx+1], 
                                            chunk_threshold, extra_chunk_space)
                # 
                except IndexError:
                    start_idx = start_idx+1
                    if start_idx >= end_idx:
                        temp_chunk.append(W_nodes[start_idx-1])
                    break
        
                if check==True:
                    temp_chunk.append(W_nodes[start_idx])
                    
                    start_idx = start_idx+1
                else:
                    temp_chunk.append(W_nodes[start_idx])
                    start_idx = start_idx+1
                    break
            
            if temp_chunk !=[]:
                chunk_list.append(temp_chunk)
                
            if start_idx >= end_idx:
                break
            
            
        chunk_data = []
        
        
        for chunk in chunk_list:
            chunk_data.append(chunk_node_to_word(chunk))
        
        
        
        """
        Turn Data into Proper Lines
        """
        
        left_pos_holder = []
        top_pos_holder = []
        
        for chunk in chunk_data:
            left_pos_holder.append(int(chunk[1].split(",")[0]))
        
            top_pos_holder.append(int(chunk[1].split(",")[1]))
            
            
        sorted_top_pos_holder = sorted(set(top_pos_holder))    
        
        # Extra Check Threshold 5 times
        for _ in range(5):
            for index, i in enumerate(sorted_top_pos_holder):
                if index!=0:
                    check = threshold_check(sorted_top_pos_holder[index], sorted_top_pos_holder[index-1], line_threshold)
                    if check:
                        sorted_top_pos_holder.remove(i)
                        
                        
        unique_line_data = dict()

        
        for i in sorted_top_pos_holder:
            unique_line_data[str(i)] = []

        
        """
        for chunk in chunk_data:
            top_pos = int(chunk[1].split(",")[1])
            for key in unique_line_data.keys():
                check = threshold_check(int(key), top_pos, line_threshold)
                if check:
                    if chunk[0].strip() != "":
                        unique_line_data[key].append([chunk[0], chunk[1], chunk[2], int(chunk[1].split(",")[0])])
                        
        """
        prev_positions = set()
        for chunk in chunk_data:
            top_pos = int(chunk[1].split(",")[1])
            for key in unique_line_data.keys():
                check = threshold_check(int(key), top_pos, line_threshold)
                if prev_positions:
                    if chunk[1] in prev_positions:
                        check = False
                if check:
                    if chunk[0].strip() != "":
                        unique_line_data[key].append([chunk[0], chunk[1], chunk[2], int(chunk[1].split(",")[0])])
                        prev_positions.add(chunk[1])  # using add() for a set
                        
                    
                    
        # Remove if the line is empty
        for i in sorted_top_pos_holder:
            try:
                if len(unique_line_data[str(i)]) == 0:
                    del unique_line_data[str(i)]
                   
                # Remove if a line have only a chunk and chunk have only 1 char
                if len(unique_line_data[str(i)]) == 1:
                    if len(unique_line_data[str(i)][0][0].strip()) == 1:
                        del unique_line_data[str(i)]
            except:
                pass

        
        # Sort by left position
        for i in sorted_top_pos_holder:
            try:
                unique_line_data[str(i)] = sorted(unique_line_data[str(i)], key=lambda left_pos: left_pos[3])
            except:
                pass
            
        for i in sorted_top_pos_holder:
            try:
                for j in unique_line_data[str(i)]:
                    j.pop()
            except:
                pass

        # Append to Data Holder
        data[PAGE_ID] = unique_line_data
        
    return data






def get_xml_to_text_info_list(path_to_xml):
    try:
        RAJSON = RAJson()
        page_data = RAJSON.process_PAGE(path_to_xml)
        chunk_page_data = chunk_process_level_page(page_data)
        #for k, v in chunk_page_data[0].items():
            #print("#########",k,v)
        #text_data = construct_sentences(chunk_page_data)
        return chunk_page_data
    except:
        return []
        pass

def get_ra_json_to_text_info_list(page_data):

    try:
        chunk_page_data = chunk_process_level_page(page_data)
        #for k, v in chunk_page_data[0].items():
            #print("#########",k,v)
        #text_data = construct_sentences(chunk_page_data)
        return chunk_page_data
    except:
        return []
        pass

def add_postion_information_to_key_value_vendor(xml_list,ra_json,is_ra_json_available,data_json):
    
    def adjust_position_for_combined_key_value(value_text, original_pos, char_threshold):
        pos_left_shift = len(value_text)*char_threshold
        l,t,r,b = original_pos.split(',')
        l = int(r) - pos_left_shift
        l = str(l)
        return f"{l},{t},{r},{b}"



    def get_calculated_position(main_position_temp,item_position):
        lm,tm,rm,bm = main_position_temp.split(',')
        li,ti,ri,bi = item_position.split(',')
        if abs(int(bm)-int(ti)) <= 80:
            l,t,r,b = min(int(lm),int(li)),min(int(tm),int(ti)),max(int(rm),int(ri)),max(int(bm),int(bi))
        else:
            l,t,r,b = lm,tm,rm,bm
        return f"{l},{t},{r},{b}"
    
    kvv_items = []
    vendor_data = data_json['vendor']
    key_value_list = data_json['key_data']
    
    vendor_page_id = vendor_data['page_id']
    vendor_temp = vendor_data['vendor']
    vendor_position_temp = vendor_data['vendor_position']
    is_vendor_position_added = False
    xml_list_or_ra_json_pages = []
    
    if is_ra_json_available:
        
        xml_list_or_ra_json_pages = ra_json["children"]
    else:
        xml_list_or_ra_json_pages = xml_list  


    try:
        for idx, path_to_xml_or_page in enumerate(xml_list_or_ra_json_pages):

            if is_ra_json_available:
                page_id = path_to_xml_or_page["id"]
            else:
                page_id = path_to_xml_or_page.replace("_layout.xml", "")[-8:]

            if vendor_page_id != page_id:
                continue
            
            if is_ra_json_available:
                chunk_page_data = get_ra_json_to_text_info_list(path_to_xml_or_page)
            else:
                 chunk_page_data = get_xml_to_text_info_list(path_to_xml_or_page)

            for k, v in chunk_page_data[0].items():
                for item_idx, item in enumerate(v):
                    chunk_data = item[0].strip().replace(',','').replace(' ','').lower()
                    if chunk_data in vendor_data['vendor'].strip().replace(',','').replace(' ','').lower():
                        
                        if chunk_data == vendor_data['vendor'].strip().replace(',','').replace(' ','').lower():
                            vendor_position_temp = item[1]
                            is_vendor_position_added = True
                            kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                            break
                        else:
                            if vendor_position_temp == '0,0,0,0':
                                vendor_temp = vendor_temp.replace(chunk_data,'')
                                vendor_position_temp = item[1]
                                
                                if vendor_temp == "":
                                    is_vendor_position_added = True
                                    kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                                    break
                            else:
                                vendor_position_temp = get_calculated_position(vendor_position_temp,item[1])
                                vendor_temp = vendor_temp.replace(chunk_data,'')
                                if vendor_temp == "":
                                    is_vendor_position_added = True
                                    kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                                    break
                            
                if is_vendor_position_added:
                    break
            if is_vendor_position_added:
                break
    except:
        pass
    vendor_data['vendor_position'] = vendor_position_temp
    
    
    key_position_mapped_done_list = []       
    for kv_idx, kv in enumerate(key_value_list):
        key_page_id = kv['page_id']
        #key_temp = kv['key'].replace(',','').replace(' ','').lower()
        key_temp = kv['key'].strip().replace(",","")
        key_position_temp = kv['key_position']
        is_key_position_added = False
        
        try:

            for idx, path_to_xml_or_page in enumerate(xml_list_or_ra_json_pages):

                if is_ra_json_available:
                    page_id = path_to_xml_or_page["id"]
                else:
                    page_id = path_to_xml_or_page.replace("_layout.xml", "")[-8:]

                if key_page_id != page_id:
                    continue
                
                if is_ra_json_available:
                    chunk_page_data = get_ra_json_to_text_info_list(path_to_xml_or_page)
                else:
                    chunk_page_data = get_xml_to_text_info_list(path_to_xml_or_page)
           
                for k, v in chunk_page_data[0].items():
                    for item_idx, item in enumerate(v):
                        
                        chunk_data = item[0].strip()
                        if chunk_data.strip()[-1] == ":":
                            chunk_data = chunk_data.strip()[:-1].strip()
                        
                        if chunk_data.strip().replace(",","") in kv['key'].strip().replace(",","") and f"{chunk_data}_{item[1]}" not in key_position_mapped_done_list:
                            
                            if chunk_data.strip().replace(",","") == kv['key'].strip().replace(",",""):
                                
                                key_position_temp = item[1]
                                key_position_mapped_done_list.append(f"{chunk_data}_{item[1]}")
                                kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                                is_key_position_added = True
                                
                                break
                            else:
                                if key_position_temp == '0,0,0,0':
                                    key_position_temp = item[1]
                                    key_temp = key_temp.replace(chunk_data,'')
                                    key_position_mapped_done_list.append(f"{chunk_data}_{item[1]}")
                                    kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                                    if key_temp == "":
                                        is_key_position_added = True
                                        break
                                else:
                                    key_position_temp = get_calculated_position(key_position_temp,item[1])
                                    key_temp = key_temp.replace(chunk_data,'')
                                    key_position_mapped_done_list.append(f"{chunk_data}_{item[1]}")
                                    kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                                    if key_temp == "":
                                        is_key_position_added = True
                                        break
                                
                    if is_key_position_added:
                        break
                if is_key_position_added:
                    break
        except:
            pass           
        kv['key_position'] = key_position_temp
            
            
    value_position_mapped_done_list = []
    comined_kv_done_dict = {}       
    for kv_idx, kv in enumerate(key_value_list):
        value_page_id = kv['page_id']
        value_temp = kv['value'].strip()
        value_checked_for_pos_from_page = ""
        value_position_temp = kv['value_position']
        is_value_position_added = False
        value_position_mapped_done_list_temp = []
        try:

            for idx, path_to_xml_or_page in enumerate(xml_list_or_ra_json_pages):

                if is_ra_json_available:
                    page_id = path_to_xml_or_page["id"]
                else:
                    page_id = path_to_xml_or_page.replace("_layout.xml", "")[-8:]

                if value_page_id != page_id:
                    continue
                
                if is_ra_json_available:
                    chunk_page_data = get_ra_json_to_text_info_list(path_to_xml_or_page)
                else:
                    chunk_page_data = get_xml_to_text_info_list(path_to_xml_or_page)
                
                for k, v in chunk_page_data[0].items():
                    for item_idx, item in enumerate(v):
                        
                        chunk_data = item[0].strip()
            
                        if chunk_data in value_temp and f"{item[0]}_{item[1]}" not in value_position_mapped_done_list and (int(kv['key_position'].split(',')[3]) < int(item[1].split(',')[1]) or (int(kv['key_position'].split(',')[2]) < int(item[1].split(',')[0]) and int(kv['key_position'].split(',')[1]) < int(item[1].split(',')[3]))) and  (int(kv['key_position'].split(',')[0]) - int(item[1].split(',')[0]))<300:                             
                            
                            if fuzz.ratio(chunk_data,kv['value'].strip().replace(",","")) >= 95:
                                
                                value_position_temp = item[1]
                                value_position_mapped_done_list.append(f"{item[0]}_{item[1]}")
                                value_position_mapped_done_list_temp.append(f"{item[0]}_{item[1]}")
                                kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                                is_value_position_added = True
                                value_checked_for_pos_from_page += item[0]
                                value_temp = ""
                                break
                            else:
                                if value_position_temp == '0,0,0,0':
                                    value_position_temp = item[1]
                                    value_temp = value_temp.replace(chunk_data,"",1)
                                    value_position_mapped_done_list.append(f"{item[0]}_{item[1]}")
                                    value_position_mapped_done_list_temp.append(f"{item[0]}_{item[1]}")
                                    kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                                    value_checked_for_pos_from_page += item[0]
                                    if value_temp == "":
                                        is_value_position_added = True
                                        break
                                else:
                                    value_position_temp = get_calculated_position(value_position_temp,item[1])
                                    value_temp = value_temp.replace(chunk_data,"",1)
                                    value_position_mapped_done_list.append(f"{item[0]}_{item[1]}")
                                    value_position_mapped_done_list_temp.append(f"{item[0]}_{item[1]}")
                                    kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                                    value_checked_for_pos_from_page += item[0]
                                    if value_temp == "":
                                        is_value_position_added = True
                                        break
                                
                    if is_value_position_added:
                        break
                if is_value_position_added:
                    break
        except:
            pass
        
        try:
            
            if value_position_temp != '0,0,0,0' and len(value_checked_for_pos_from_page) <= 5:
                value_position_temp = '0,0,0,0'

            if 1 - len(value_temp)/len(kv['value']) < 0.5:
                value_position_temp = '0,0,0,0'


            if value_position_temp == '0,0,0,0':
                is_value_position_added = False

                if f"{item[0]}_{item[1]}" in value_position_mapped_done_list:
                    value_position_mapped_done_list.remove(f"{item[0]}_{item[1]}")

                for k, v in chunk_page_data[0].items():
                    for item_idx, item in enumerate(v):
                        if f"{item[0]}_{item[1]}" in value_position_mapped_done_list:
                            continue
                        if fuzz.ratio(item[0], kv['value']) >= 90:
                            value_position_temp = item[1]
                            is_value_position_added = True
                            value_position_mapped_done_list.append(f"{item[0]}_{item[1]}")
                            kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                            break
                        elif fuzz.ratio(item[0], kv['key']+ kv['value']) >= 90:
                            l,_,r,_ = item[1].split(',')
                            char_threshold = (int(r) - int(l))/ len(item[0])
                            value_position_temp =  adjust_position_for_combined_key_value(kv['value'], item[1], char_threshold)
                            is_value_position_added = True
                            value_position_mapped_done_list.append(f"{item[0]}_{item[1]}")
                            kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                            break
                        elif fuzz.ratio(item[0], kv['key'].split(" ")[-1]+ kv['value']) >= 90:
                            l,_,r,_ = item[1].split(',')
                            char_threshold = (int(r) - int(l))/ len(item[0])
                            value_position_temp =  adjust_position_for_combined_key_value(kv['value'], item[1],char_threshold)
                            is_value_position_added = True
                            value_position_mapped_done_list.append(f"{item[0]}_{item[1]}")
                            kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                            break
                        elif (kv['key'] in item[0] and kv['value'] in item[0] and int(kv['key_position'].split(',')[3]) < int(item[1].split(',')[3])) or (kv['value'] in item[0] and kv['key'] not in item[0]):
                            l,t,r,b = item[1].split(',')
                            char_threshold = (int(r) - int(l))/ len(item[0])
                            l_shift, r_shift = len(item[0].split(kv['value'])[0])*char_threshold, len(item[0].split(kv['value'])[-1])*char_threshold
                            l = int(l) + l_shift
                            l = str(l)
                            r = int(r) - r_shift
                            r = str(r)
                            value_position_temp = f"{l},{t},{r},{b}"
                            is_value_position_added = True
                            if comined_kv_done_dict.get(f"{item[0]}_{item[1]}",None) == None:
                                comined_kv_done_dict[f"{item[0]}_{item[1]}"] = item[0].replace(kv['key'],"").replace(kv['value'],"")
                            else:
                                if comined_kv_done_dict[f"{item[0]}_{item[1]}"].replace(":","").replace(".","").strip() == "":
                                    value_position_mapped_done_list.append(f"{item[0]}_{item[1]}")
                                    kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                                else:
                                    comined_kv_done_dict[f"{item[0]}_{item[1]}"] = item[0].replace(kv['key'],"").replace(kv['value'],"")
                            break
                    if is_value_position_added:
                        break

            if value_position_temp == '0,0,0,0':
                is_value_position_added = False
                value_temp = kv["value"]
                for i in value_position_mapped_done_list_temp:
                    value_position_mapped_done_list.remove(i)

                for k, v in chunk_page_data[0].items():
                    for item_idx, item in enumerate(v):
                        
                        chunk_data = item[0].strip() 
                        if f"{item[0]}_{item[1]}" not in value_position_mapped_done_list and fuzz.ratio(item[0], value_temp[:len(item[0])]) >= 80:
                            if value_position_temp == '0,0,0,0':
                                    value_position_temp = item[1]
                                    value_temp = value_temp[len(item[0]):]
                                    value_position_mapped_done_list.append(f"{item[0]}_{item[1]}")
                                    kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                                    if value_temp == "":
                                        is_value_position_added = True
                                        break
                            else:
                                value_position_temp = get_calculated_position(value_position_temp,item[1])
                                value_temp = value_temp[len(item[0]):]
                                value_position_mapped_done_list.append(f"{item[0]}_{item[1]}")
                                kvv_items.append(f"{item[0]}{item[1]}{page_id}")
                                if value_temp == "":
                                    is_value_position_added = True
                                    break
                    if is_value_position_added:
                        break
        except:
            pass

        kv['value_position'] = value_position_temp

    return data_json, kvv_items



def add_postion_information_to_table(xml_list,ra_json,is_ra_json_available,data_json, kvv_items):

    def get_calculated_position(main_position_temp,item_position):
        lm,tm,rm,bm = main_position_temp.split(',')
        li,ti,ri,bi = item_position.split(',')
        if abs(int(bm)-int(ti)) <= 80:
            l,t,r,b = min(int(lm),int(li)),min(int(tm),int(ti)),max(int(rm),int(ri)),max(int(bm),int(bi))
        else:
            l,t,r,b = lm,tm,rm,bm
        return f"{l},{t},{r},{b}"
    
    cell_position_mapped_done_list = []  
    comined_cell_done_dict = {}
    xml_list_or_ra_json_pages = []
    if is_ra_json_available:
        
        xml_list_or_ra_json_pages = ra_json["children"]
    else:
        xml_list_or_ra_json_pages = xml_list  

    tables = data_json['table_data']

    for table in tables:
        rows = table['table_data']['rows']

        for row in rows:
            row_data = row['row_data']

            for values in row_data:
                page_id_final = ""
                cell_value_position = "0,0,0,0"
                value_temp = values["value"]
                try:
                    for idx, path_to_xml_or_page in enumerate(xml_list_or_ra_json_pages):
                        is_cell_position_added = False
                        chunk_page_data = []
                        if is_ra_json_available:
                            page_id = path_to_xml_or_page["id"]
                        else:
                            page_id = path_to_xml_or_page.replace("_layout.xml", "")[-8:]
                        if is_ra_json_available:
                            chunk_page_data = get_ra_json_to_text_info_list(path_to_xml_or_page)
                        else:
                            chunk_page_data = get_xml_to_text_info_list(path_to_xml_or_page)

                        for k, v in chunk_page_data[0].items():
                            for item_idx, item in enumerate(v):

                                combo_item = f"{item[0]}{item[1]}{page_id}"
                                if combo_item in cell_position_mapped_done_list:
                                    continue
                                if fuzz.ratio(item[0].strip(), values["value"].strip()) >= 90: 
                                    cell_value_position = item[1]
                                    cell_position_mapped_done_list.append(combo_item)
                                    is_cell_position_added = True
                                    page_id_final = page_id
                                    break
                                elif values["value"] in item[0] and values["label"] in item[0]:
                                    l,t,r,b = item[1].split(',')
                                    char_threshold = (int(r) - int(l))/ len(item[0])
                                    l_shift, r_shift = len(item[0].split(values['value'])[0])*char_threshold, len(item[0].split(values['value'])[-1])*char_threshold
                                    l = int(l) + l_shift
                                    l = str(l)
                                    r = int(r) - r_shift
                                    r = str(r)
                                    cell_value_position = f"{l},{t},{r},{b}"
                                    is_cell_position_added = True
                                    page_id_final = page_id
                                    if comined_cell_done_dict.get(f"{item[0]}{item[1]}{page_id}",None) == None:
                                        comined_cell_done_dict[f"{item[0]}{item[1]}{page_id}"] = item[0].replace(values["label"],"").replace(values['value'],"")
                                    else:
                                        if comined_cell_done_dict[f"{item[0]}{item[1]}{page_id}"].replace(":","").replace(".","").strip() == "":
                                            cell_position_mapped_done_list.append(f"{item[0]}{item[1]}{page_id}")
                
                                        else:
                                            comined_cell_done_dict[f"{item[0]}{item[1]}{page_id}"] = item[0].replace(values["label"],"").replace(values['value'],"")
                                    break
                                
                                elif fuzz.ratio(item[0], value_temp[:len(item[0])]) >= 90:
                                    if cell_value_position == '0,0,0,0':
                                            cell_value_position = item[1]
                                            value_temp = value_temp[len(item[0]):]
                                            cell_position_mapped_done_list.append(f"{item[0]}{item[1]}{page_id}")
                                            page_id_final = page_id
                                            if value_temp == "":
                                                is_cell_position_added = True
                                                break
                                    else:
                                        cell_value_position = get_calculated_position(cell_value_position,item[1])
                                        value_temp = value_temp[len(item[0]):]
                                        cell_position_mapped_done_list.append(f"{item[0]}{item[1]}{page_id}")
                                        page_id_final = page_id
                                        if value_temp == "":
                                            is_cell_position_added = True
                                            break
                                    
                            if is_cell_position_added:
                                break
                        if is_cell_position_added:
                            break
                except:
                    pass

                if values["value"] == "":
                    values["page_id"] = page_id_final
                    values["position"] = "0,0,0,0"
                else:
                    values["page_id"] = page_id_final
                    values["position"] = cell_value_position
    return data_json