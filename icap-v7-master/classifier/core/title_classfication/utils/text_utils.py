# Global Import
import re
from rapidfuzz import process, fuzz, utils
#Local Import
from core.model.nlp_model import load_nlp_model

nlp = load_nlp_model()

#Function to detect cleaned string containing only alphabetic characters and spaces
def special_filter(text):
    # Remove special characters and numbers using regular expressions
    cleaned_text = re.sub("[^A-Za-z]+", " ", text)
    return cleaned_text


# Function to detect phone numbers
def detect_phone_numbers(text):
    phone_pattern = re.compile(r"\+?\d[\d\s\-\(\)]{9,}")
    return phone_pattern.findall(text)

# Function to detect dates
def detect_dates(text):
    date_pattern = re.compile(
        r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b|\b\d{1,2}(?:th|rd|st|nd)?\s\w+\s\d{4}\b"
    )
    return date_pattern.findall(text)



# Main function to call all detectors
def detect_avoiding_entities(text):
    phones = detect_phone_numbers(text)
    dates = detect_dates(text)

    return {"Phone Numbers": phones, "Dates": dates}

def find_s_id(line, label):
    # Split the label into individual words.
    label = label.split()

    # Iterate over each word in the line.
    for word in line:
        # Calculate the similarity score between the current word and the first word of the label.
        score = fuzz.token_set_ratio(word[0].lower(), label[0].lower())

        # If the similarity score is greater than or equal to 95, return the style ID of the word.
        if score >= 95:
            return word[2]  # Style ID is the third element in the word list.

    # If no match is found, return None.
    return None

# checks if a line contains any location
def find_location(text, category):
    # print(category)
    for label, keywords in category.items():
        # Using process.extractOne to find the best match within each category
        match, score, idx = process.extractOne(
            text, keywords, scorer=fuzz.WRatio, processor=utils.default_process
        )
        if score > 90:
            # print("ignored text:", text)
            return False
    doc = nlp(text)
    for ent in doc.ents:
        # Detect locations (GPE: Geopolitical Entity)
        if ent.label_ == "GPE":
            # print("location",text)
            return True
    return False

# checks if words has common sub string
def check_word_presence(word1, word2):
    # Initialize a flag to True, assuming the words are present.
    flag = True

    # Split the first word (phrase) into individual words and check if each exists in the second word (phrase).
    for i in word1.lower().split():
        if i not in word2.lower():
            flag = False  # Set flag to False if any word is not found.
            break

    # If the first condition is satisfied, return True.
    if flag:
        return flag

    # Reset the flag and repeat the process, checking if words from the second string exist in the first string.
    for i in word2.lower().split():
        if i not in word1.lower():
            flag = False  # Set flag to False if any word is not found.
            break

    # Return the result of the check.
    return flag
#  This function extracts numeric values from a string, optionally splitting it based on a given separator
def find_num_from_string(string_fragments, sig=None):
    if sig == None:
        number = ""
        for ch in string_fragments:
            if "0" <= ch <= "9":
                number += ch
            elif number != "" or " " < ch <= "/":
                break

        if number != "":
            return number
        else:
            return ""
    else:
        string_fragments = string_fragments.split(sig)
        start = find_num_from_string(string_fragments[0][::-1])[::-1]
        end = find_num_from_string(string_fragments[1])
        return (int(start), int(end))


def find_digit_of_digit(input_string):
    # Define regular expression pattern
    pattern = r"\b\d+\s*(?:of)\s*\d+\b|\b\d+of\d+\b|\b\d+of\d+\b"

    # Find all matches using the pattern
    matches = re.findall(pattern, input_string)
    return matches


def find_special_numbers(input_string):
    # Define regular expression pattern
    input_string = input_string.replace("I", "1").replace("i", "1").replace("l", "1")
    pattern = r"\b\d+(?:\s*(?:of|\/|-)\s*\d+)?\b"

    # Find all matches using the pattern
    matches = re.findall(pattern, input_string)

    return matches