# def find_text_bbox(
#     doc,
#     box,
# ):  # if one_line is true, it will only return only the desired text part of immidiet next line
#     # print(box)
#     text = []
#     trigger_line_text = ""
#     if len(box) == 4:
#         for line in doc:
#             box_text = ""
#             line_text = ""
#             for word in line:
#                 if (
#                     box[0] <= word[1][0]
#                     and box[1] <= word[1][1]
#                     and box[2] >= word[1][2]
#                     and box[3] >= word[1][3]
#                 ):
#                     # print(line)
#                     box_text += word[0] + " "
#                 line_text += word[0] + " "
#             if box_text != "":
#                 text.append(box_text)
#                 trigger_line_text += line_text
#     # print(text)
#     return (" ".join(text)[0:-1], trigger_line_text[0:-1])

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

            for word in line:
                word_text = word[0]
                x1, y1, x2, y2 = word[1]
                
                if box[0] <= x1 and box[1] <= y1 and box[2] >= x2 and box[3] >= y2:
                    line_box_text += word_text + " "
                line_text += word_text + " "

            #if any words matched inside the box, record both
            if line_box_text.strip():
                box_texts.append(line_box_text.strip())
                trigger_line_text += line_text.strip()

    return (" ".join(box_texts), trigger_line_text)
