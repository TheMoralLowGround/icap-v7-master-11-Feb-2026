import re
import traceback

"""

This is a spceicfic exceptional alternator where we have the capability to alter the
output-json.

Legacy and to be made redundant by introducing GUI based post-processing.

"""


def process(profile_id, doc_type, input_json):
    # @Emon on 06/10/2022 - Removed luxxotica alternator
    output_json = input_json.copy()

    # if "pall" in profile_id.lower() and "packing list" in doc_type.lower():
    #     if "goodsLines" in output_json.keys():
    #         goodsLines = output_json["goodsLines"]
    #         dim_data = None
    #         goodsLine_count = len(goodsLines)
    #         if not dim_data:
    #             for goodsLine in goodsLines:
    #                 if "dimensions" in goodsLine.keys():
    #                     dim_data = goodsLine["dimensions"]
    #                     goodsLine.pop("dimensions", None)
    #                     goodsLine.pop("Batch", None)
    #                 grossWeight = goodsLine["grossWeight"].strip().split(" ")[0]
    #                 grossWeight_UOM = goodsLine["grossWeight"].strip().split(" ")[1]
    #                 goodsLine["grossWeight"] = grossWeight
    #                 if grossWeight_UOM == "KG":
    #                     grossWeight = "KGM"
    #                 goodsLine["grossWeightUom"] = grossWeight_UOM

    #         dim_data_split = dim_data.split('\n')
    #         dim_count = len(dim_data_split)
    #         if dim_count > goodsLine_count:
    #             for i in range(dim_count):
    #                 try:
    #                     dim_to_be_used_split = re.split(r'\D+', dim_data_split[i])
    #                     goodsLines[i]["length"] = dim_to_be_used_split[1]
    #                     goodsLines[i]["width"] = dim_to_be_used_split[2]
    #                     goodsLines[i]["height"] = dim_to_be_used_split[3]
    #                     goodsLines[i]["packageCount"] = dim_to_be_used_split[0]
    #                 except:
    #                     new_goodsLine = goodsLines[0].copy()
    #                     new_goodsLine.pop("length", None)
    #                     new_goodsLine.pop("width", None)
    #                     new_goodsLine.pop("height", None)
    #                     dim_to_be_used_split = re.split(r'\D+', dim_data_split[i])
    #                     new_goodsLine["length"] = dim_to_be_used_split[1]
    #                     new_goodsLine["width"] = dim_to_be_used_split[2]
    #                     new_goodsLine["height"] = dim_to_be_used_split[3]
    #                     packageCount = dim_to_be_used_split[0]
    #                     new_goodsLine["packageCount"] = packageCount
    #                     goodsLines.insert(i, new_goodsLine)

    #         elif dim_count == 1:
    #             dim_to_be_used_split = re.split(r'\D+', dim_data)
    #             goodsLines[0]["length"] = dim_to_be_used_split[1]
    #             goodsLines[0]["width"] = dim_to_be_used_split[2]
    #             goodsLines[0]["height"] = dim_to_be_used_split[3]
    #             goodsLines[0]["packageCount"] = dim_to_be_used_split[0]

    #         output_json["goodsLines"] = goodsLines

    #         return output_json
    # elif "PALL_MEDISTAD" in profile_id.lower() and "commercial invoice" in doc_type.lower():
    #     crf_storage = None
    #     srn_storage = None
    #     if "CRF" in output_json.keys():
    #         crf_storage = output_json["CRF"]
    #         output_json.pop("CRF", None)

    #     if "goodsLines" in output_json.keys():
    #         goodsLines = output_json["goodsLines"]
    #         for goodsLine in goodsLines:
    #             if "SRN" in goodsLine.keys():
    #                 srn_storage = goodsLine["SRN"]
    #                 goodsLine.pop("SRN", None)
    #             if "YourProductNumber" in goodsLine.keys():
    #                 goodsLine.pop("YourProductNumber", None)
    #     if srn_storage:
    #         if "references" in output_json.keys():
    #             output_json["references"].append({"type": "SRN", "number": srn_storage})
    #         else:
    #             output_json["references"] = [{"type": "SRN", "number": srn_storage}]

    #     if crf_storage:
    #         if "references" in output_json.keys():
    #             output_json["references"].append({"type": "CRF", "number": crf_storage})
    #         else:
    #             output_json["references"] = [{"type": "CRF", "number": crf_storage}]
    #     return output_json

    # elif "kr_daewon" in profile_id.lower() and "packing list" in doc_type.lower():
    #     try:
    #         if "references" in output_json.keys():
    #             references = output_json["references"]
    #             for reference in references:
    #                 srn = reference["number"]
    #                 srn = srn.split()[0]
    #                 reference['number'] = srn
    #     except:
    #         pass
    #     return output_json

    if "qtb" in profile_id.lower():
        try:
            if "requestedDeliveryDate" in output_json.keys():
                delivery_date = output_json["requestedDeliveryDate"].strip()
                delivery_date = delivery_date.split("au")[-1]
                delivery_date = delivery_date.split()
                if "jan" in delivery_date[1].lower():
                    delivery_date[1] = "01"
                elif (
                    "feb" in delivery_date[1].lower()
                    or "fev" in delivery_date[1].lower()
                    or "fév" in delivery_date[1].lower()
                    or "fey" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "02"
                elif "mar" in delivery_date[1].lower():
                    delivery_date[1] = "03"
                elif (
                    "apr" in delivery_date[1].lower()
                    or "avr" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "04"
                elif (
                    "may" in delivery_date[1].lower()
                    or "mai" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "05"
                elif "jun" in delivery_date[1].lower():
                    delivery_date[1] = "06"
                elif (
                    "jul" in delivery_date[1].lower()
                    or "juil" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "07"
                elif (
                    "aug" in delivery_date[1].lower()
                    or "aou" in delivery_date[1].lower()
                    or "aoû" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "08"
                elif "sep" in delivery_date[1].lower():
                    delivery_date[1] = "09"
                elif "oct" in delivery_date[1].lower():
                    delivery_date[1] = "10"
                elif "nov" in delivery_date[1].lower():
                    delivery_date[1] = "11"
                elif (
                    "dec" in delivery_date[1].lower()
                    or "déc" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "12"
                try:
                    delivery_date = (
                        delivery_date[1]
                        + "/"
                        + delivery_date[0]
                        + "/"
                        + delivery_date[2]
                    )
                except:
                    pass
                output_json["requestedDeliveryDate"] = delivery_date.strip()
        except:
            pass
        try:
            if "goodsLines" in output_json.keys():
                goods_lines = output_json["goodsLines"]
                for goods_line in goods_lines:
                    if "innerPackageType" in goods_line.keys():
                        innerPackageType = goods_line["innerPackageType"]
                        if (
                            "HC" in innerPackageType
                            or "RF" in innerPackageType
                            or "GP" in innerPackageType
                        ):
                            innerPackageType = innerPackageType.replace("HC", "")
                            innerPackageType = innerPackageType.replace("RF", "")
                            innerPackageType = innerPackageType.replace("GP", "")
                            intinnerPackageType = int(innerPackageType)
                            intinnerPackageType = intinnerPackageType * 1000
                            innerPackageType = str(intinnerPackageType)
                            goods_line["grossWeight"] = innerPackageType
                            goods_line["grossWeightUOM"] = "KGM"
                try:
                    output_json["goodsLines"] = goodsLines
                except:
                    pass
        except:
            pass
        return output_json

    elif "festo" in profile_id.lower() and "commercial invoice" in doc_type.lower():
        try:
            if "references" in output_json.keys():
                references = output_json["references"]
                for reference in references:
                    srn = reference["number"]
                    srn = srn.split()[0]
                    reference["number"] = srn
        except:
            pass
        try:
            if "modeOfTransport" in output_json.keys():
                modeoftransport = output_json["modeOfTransport"]
                modeoftransport = modeoftransport.split("\n")[0]
                output_json["modeOfTransport"] = modeoftransport.strip()
        except:
            pass
        return output_json

    elif ("siemens" in profile_id.lower()) and ("packing list" in doc_type.lower()):

        def supplierName_picker(supplierName):
            if not "," in supplierName:
                return supplierName
            supplier_name_split_by_comma = supplierName.split(",")
            if not len(supplier_name_split_by_comma[0]) < 5:
                output = supplier_name_split_by_comma[0]
            else:
                output = (
                    supplier_name_split_by_comma[0] + supplier_name_split_by_comma[1]
                )
            return output

        try:
            goods_lines = output_json["goodsLines"]
            for row in goods_lines:
                if "supplierName" in row.keys():
                    new_supplierName = supplierName_picker(row["supplierName"])
                    row["supplierName"] = new_supplierName
            output_json["goodsLines"] = goods_lines
            return output_json
        except:
            print(traceback.print_exc())
            return input_json

    elif "arburg" in profile_id.lower():
        try:
            if "references" in output_json.keys():
                for data_idx, data in enumerate(output_json["references"]):
                    if data["type"] == "SRN":
                        data["number"] = data["number"].split("/")[0].strip()
                    output_json["references"][data_idx] = data
            if "consignee" in output_json.keys():
                if "accountNumber" in output_json["consignee"].keys():
                    if output_json["consignee"]["accountNumber"][0] == "D":
                        new_string = "0" + output_json["consignee"]["accountNumber"][1:]
                        output_json["consignee"].update({"accountNumber": new_string})
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    # this is for general electric
    elif "US_AFR_GE".lower() in profile_id.lower():
        try:
            if "goodsLines" in output_json.keys():
                new_dict = dict()
                new_dict["grossWeight"] = output_json["goodsLines"][0]["grossWeight"]
                new_dict["grossWeightUom"] = output_json["goodsLines"][1][
                    "grossWeightUom"
                ]
                new_dict["length"] = output_json["goodsLines"][0]["length"]
                new_dict["width"] = output_json["goodsLines"][0]["width"]
                new_dict["height"] = output_json["goodsLines"][0]["height"]
                new_dict["grossWeight"] = str(int(new_dict["grossWeight"]) * 0.455)
                new_dict["dimensionUOM"] = "IN"
                output_json["goodsLines"] = []
                output_json["goodsLines"].append(new_dict)
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif "alqurum" in profile_id.lower():
        try:
            if "notify" in output_json.keys():
                notify = output_json["notify"]
                if notify["name"] == "Notify Party":
                    notify["name"] = notify["addressLine1"]
                    notify["addressLine1"] = notify["addressLine2"]
                    del notify["addressLine2"]
                output_json["notify"] = notify
                if notify["name"] == "Repair & Return":
                    del output_json["notify"]

            if "consignee" in output_json.keys():
                consignee = output_json["consignee"]
                if consignee["name"] == "Consignee":
                    consignee["name"] = consignee["addressLine1"]
                    consignee["addressLine1"] = consignee["addressLine2"]
                    del consignee["addressLine2"]
                output_json["consignee"] = consignee

            if "shipper" in output_json.keys():
                shipper = output_json["shipper"]
                if (
                    shipper["name"] == "Al-qurum Jewellery LLC"
                    or shipper["name"] == "AI-qurum Jewellery LLC"
                    or shipper["name"] == "Ai-qurum Jewellery LLC"
                ):
                    shipper["name"] = "AL-qurum Jewellery LLC"
                if (
                    "AI" in shipper["name"]
                    or "Ai" in shipper["name"]
                    or "Al" in shipper["name"]
                ):
                    try:
                        shipper["name"] = shipper["name"].replace("AI", "AL")
                    except:
                        pass
                    try:
                        shipper["name"] = shipper["name"].replace("Ai", "AL")
                    except:
                        pass
                    try:
                        shipper["name"] = shipper["name"].replace("Al", "AL")
                    except:
                        pass
                output_json["shipper"] = shipper
            return output_json
        except:
            print(traceback.print_exc())
            return input_json

    elif "HUSQVARNA".lower() in profile_id.lower():
        try:
            if "references" in output_json.keys():
                new_data = list()
                for data in output_json["references"]:
                    try:

                        def get_alpha_count(s):
                            count = 0
                            for c in s:
                                if c.isalpha():
                                    count += 1
                            return count

                        if data["type"] == "CRF":
                            crf_number = data["number"].strip()
                            try:
                                crf_number = crf_number.split(" ")[1]
                                data["number"] = crf_number
                                if get_alpha_count(crf_number) < 2:
                                    new_data.append(data)
                            except:
                                pass
                        if data["type"] == "PMN":
                            pmn_number = data["number"].strip()
                            pmn_number = pmn_number.split(" ")[0]
                            data["number"] = pmn_number
                            new_data.append(data)
                    except:
                        new_data.append(data)
                output_json["references"] = new_data
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif "rohde" in profile_id.lower():
        try:
            if "shipper" in output_json.keys():
                shipper = output_json["shipper"]
                if shipper["name"] == "Rohde&Schwarz":
                    shipper["name"] = shipper["addressLine1"]
                    shipper["addressLine1"] = shipper["addressLine2"]
                    del shipper["addressLine2"]
                output_json["shipper"] = shipper

            if "references" in output_json.keys():
                references = output_json["references"]
                for reference in references:
                    if reference["type"] == "CRF":
                        if "Flugdaten" in reference["number"]:
                            references.remove(reference)
                output_json["references"] = references

            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif (
        "DE_PALL".lower() in profile_id.lower()
        and "Shipping Order".lower() in doc_type.lower()
    ):
        try:
            if "goodsLines" in output_json.keys():
                goods_lines = output_json["goodsLines"]
                new_goods_lines = list()
                target_goods_line = goods_lines[0]
                mark_and_numbers = ""
                pack_found = 0
                for goods_line in goods_lines[1:]:
                    if "packageCount" in goods_line.keys():
                        pack_found = 1
                        target_goods_line["marksAndNumbers"] = mark_and_numbers[:-1]
                        mark_and_numbers = ""
                        new_goods_lines.append(target_goods_line)
                        target_goods_line = goods_line
                    if goods_line["marksAndNumbers"][0].isnumeric():
                        mark_and_number = goods_line["marksAndNumbers"]
                    try:
                        if mark_and_number[-1] == ",":
                            mark_and_number = mark_and_number[:-1]
                    except:
                        pass
                    mark_and_numbers = mark_and_numbers + mark_and_number + ","
                if pack_found == 0:
                    target_goods_line["marksAndNumbers"] = mark_and_numbers[:-1]
                    new_goods_lines.append(target_goods_line)
                output_json["goodsLines"] = new_goods_lines

            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif (
        "WARREN".lower() in profile_id.lower()
        and "commercial invoice".lower() in doc_type.lower()
    ):
        try:
            if "references" in output_json.keys():
                references = output_json["references"]
                crf = references[0]["number"].split(";")
                new_crf = list()
                for count, x in enumerate(crf):
                    crf[count] = x.strip()
                    if crf[count] not in new_crf:
                        new_crf.append(crf[count])
                new_crf = "; ".join(new_crf)
                references[0]["number"] = new_crf
                output_json["references"] = references

            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif ("IVOCLAR".lower() in profile_id.lower()) and (
        "Shippers Letter of Instruction".lower() in doc_type.lower()
    ):
        try:
            if "goodsLines" in output_json.keys():
                goodsLines = output_json["goodsLines"]
                count = 0
                for goodsLine in goodsLines[:]:
                    if "harmonizedCode" in goodsLine.keys():
                        if count == 0:
                            hscode = goodsLine["harmonizedCode"]
                            count += 1
                        goodsLines.remove(goodsLine)
                goodsLines[0]["harmonizedCode"] = hscode
                output_json["goodsLines"] = goodsLines
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif "jinhap".lower() in profile_id.lower():
        try:
            if "goodsLines" in output_json.keys():
                goodsLines = output_json["goodsLines"]
                for goodsLine in goodsLines:
                    if "goodsDescription" in goodsLine.keys():
                        goods_description = goodsLine["goodsDescription"]
                        new_goods = ""
                        goods_description = goods_description.split(" ")
                        for goods in goods_description[:]:
                            count = 0
                            for char in goods:
                                if char.isnumeric() == True:
                                    count = 1
                            if count == 1:
                                goods_description.remove(goods)
                        try:
                            for goods in goods_description:
                                new_goods = new_goods + goods + " "
                        except:
                            pass
                        goodsLine["goodsDescription"] = new_goods.strip()
                output_json["goodsLines"] = goodsLines
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif "suzuki".lower() in profile_id.lower():
        try:
            if "originLocationName" in output_json.keys():
                origin_name = output_json["originLocationName"]
                try:
                    origin_name = origin_name.replace("CZECft", "CZECH")
                except:
                    pass
                try:
                    origin_name = origin_name.replace("TAP き N", "JAPAN")
                except:
                    pass
                try:
                    origin_name = origin_name.replace(" mINA ", "CHINA")
                except:
                    pass
                try:
                    origin_name = origin_name.replace("ITA", "ITALY")
                except:
                    pass
                try:
                    origin_name = origin_name.replace(" BELGIJM", " BELGIUM")
                except:
                    pass
                try:
                    origin_name = origin_name.replace(" Y,\n・ ・ ・ ・ ・\n", "")
                except:
                    pass
                try:
                    origin_name = origin_name.replace("\n", "")
                except:
                    pass
                try:
                    origin_name = origin_name.replace("Y,", "")
                except:
                    pass
                try:
                    origin_name = origin_name.replace(
                        "JAPANCHINAFRANCE", "JAPAN CHINA FRANCE"
                    )
                except:
                    pass
                output_json["originLocationName"] = origin_name
            if "goodsLines" in output_json.keys():
                goods_lines = output_json["goodsLines"]
                for goods_line in goods_lines:
                    if "length" in goods_line.keys():
                        goods_line["dimensionsUom"] = "CM"
                output_json["goodsLines"] = goods_lines
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif (
        "FLEXTRONICS".lower() in profile_id.lower()
        and "commercial invoice".lower() in doc_type.lower()
    ):
        try:
            if "incotermsLocation" in output_json.keys():
                if output_json["incotermsLocation"] == "Buest":
                    output_json["incotermsLocation"] = "Budapest"
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif "Caterpillar".lower() in profile_id.lower():
        try:
            if "requestedShippingDate" in output_json.keys():
                delivery_date = output_json["requestedShippingDate"].strip()
                delivery_date = delivery_date.split("-")
                if "jan" in delivery_date[1].lower():
                    delivery_date[1] = "01"
                elif (
                    "feb" in delivery_date[1].lower()
                    or "fev" in delivery_date[1].lower()
                    or "fév" in delivery_date[1].lower()
                    or "fey" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "02"
                elif "mar" in delivery_date[1].lower():
                    delivery_date[1] = "03"
                elif (
                    "apr" in delivery_date[1].lower()
                    or "avr" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "04"
                elif (
                    "may" in delivery_date[1].lower()
                    or "mai" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "05"
                elif "jun" in delivery_date[1].lower():
                    delivery_date[1] = "06"
                elif (
                    "jul" in delivery_date[1].lower()
                    or "juil" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "07"
                elif (
                    "aug" in delivery_date[1].lower()
                    or "aou" in delivery_date[1].lower()
                    or "aoû" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "08"
                elif "sep" in delivery_date[1].lower():
                    delivery_date[1] = "09"
                elif "oct" in delivery_date[1].lower():
                    delivery_date[1] = "10"
                elif "nov" in delivery_date[1].lower():
                    delivery_date[1] = "11"
                elif (
                    "dec" in delivery_date[1].lower()
                    or "déc" in delivery_date[1].lower()
                ):
                    delivery_date[1] = "12"
                try:
                    delivery_date = (
                        delivery_date[1]
                        + "/"
                        + delivery_date[0]
                        + "/"
                        + delivery_date[2]
                    )
                except:
                    pass
                output_json["requestedShippingDate"] = delivery_date.strip()
        except:
            pass
        return output_json
    elif "jaguar".lower() in profile_id.lower():
        try:
            if "goodsLines" in output_json.keys():
                goods_lines = output_json["goodsLines"]
                for goods_line in goods_lines:
                    goods_line["packageCount"] = "1"
                output_json["goodsLines"] = goods_lines
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif ("siemens" in profile_id.lower()) and (
        "Shippers Letter of Instruction".lower() in doc_type.lower()
    ):
        try:
            if "goodsLines" in output_json.keys():
                goods_lines = output_json["goodsLines"]
                new_goods_lines = list()
                for goods_line in goods_lines:
                    keys = list(goods_line.keys())
                    keys_length = len(keys)
                    if keys_length != 1 or keys[0] != "packageCount":
                        new_goods_lines.append(goods_line)
                output_json["goodsLines"] = new_goods_lines
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif "bentley".lower() in profile_id.lower():
        try:
            if "goodsLines" in output_json.keys():
                goods_lines = output_json["goodsLines"]
                for goods_line in goods_lines[:]:
                    if "Shipping Advice".lower() in doc_type:
                        goods_line["packageCount"] = "1"
                    if "harmonizedCode" in goods_line.keys():
                        hscode = goods_line["harmonizedCode"]
                        goods_lines[0]["harmonizedCode"] = hscode
                        goods_lines.remove(goods_line)
                output_json["goodsLines"] = goods_lines
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif (
        "medtronic".lower() in profile_id.lower()
        and "packing list".lower() in doc_type.lower()
    ):
        try:
            if "goodsLines" in output_json.keys():
                goods_lines = output_json["goodsLines"]
                new_goods_lines = list()
                for goods_line in goods_lines:
                    if "height" in goods_line.keys():
                        new_goods_lines.append(goods_line)
                output_json["goodsLines"] = new_goods_lines
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    elif "olympus".lower() in profile_id.lower():
        try:
            if "goodsLines" in output_json.keys():
                goods_lines = output_json["goodsLines"]
                for goods_line in goods_lines[:]:
                    if "volume" in goods_line.keys():
                        goods_line["volumeUOM"] = "l"
                output_json["goodsLines"] = goods_lines
            return output_json
        except:
            print(traceback.print_exc())
            return input_json
    else:
        # print('No output alternation done')
        return input_json
