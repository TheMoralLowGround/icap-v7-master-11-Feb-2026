
import os
import json
import copy
from rapidfuzz import fuzz



def add_postion_information_to_exception_kv(ra_json,data_list,xml_list = [],is_ra_json_available = True):
    
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

    for item in data_list:
        item['key_position'] = "0,0,0,0"
        item['value_position'] = "0,0,0,0"

    ra_json = ra_json["nodes"][0]
    kvv_items = []
  
    xml_list_or_ra_json_pages = []
    key_value_list = data_list
    if is_ra_json_available:
        
        xml_list_or_ra_json_pages = ra_json["children"]
    else:
        xml_list_or_ra_json_pages = xml_list  


    
    
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

    return data_list