from rapidfuzz import process, fuzz, utils
import re
from core.model.nlp_model import load_nlp_model
import copy

nlp = load_nlp_model()

# Function to detect phone numbers
def detect_phone_numbers(text):
    """
    Detect phone numbers within a given text string.

    Method Parameters
    ----------
    text : str
        Input text to search for phone numbers.

    Returns
    -------
    list of str
        A list of phone numbers found in the text. 
        Matches common formats with optional '+' prefix, digits, spaces, dashes, or parentheses.
    """
    phone_pattern = re.compile(r"\+?\d[\d\s\-\(\)]{9,}")
    return phone_pattern.findall(text)


# Function to detect dates
def detect_dates(text):
    """
    Detect date expressions within a given text string.

    Parameters
    ----------
    text : str
        Input text to search for dates.

    Returns
    -------
    list of str
        A list of date strings found in the text.
        Supports formats like:
        - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
        - Dth Month YYYY (e.g., "12th March 2021"), etc
    """
    date_pattern = re.compile(
        r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b|\b\d{1,2}(?:th|rd|st|nd)?\s\w+\s\d{4}\b"
    )
    return date_pattern.findall(text)



def find_location(text, category):
    """
        Detect whether a given text refers to a location or organization, 
        while filtering out category keyword matches.

        Method Parameters
        ----------
        text : str
            Input text to analyze for potential location entities.
        category : dict[str, list[str]]
            Dictionary mapping category labels to lists of keywords. 
            If the text strongly matches any keyword (fuzzy score > 90), 
            the location check is skipped.

        Returns
        -------
        boolean
            True if the text contains a named entity labeled as a location (GPE) or organization (ORG).
            False if it strongly matches a category keyword or if no location/organization entity is found.
        """
    for label, keywords in category.items():
        # Using process.extractOne to find the best match within each category
        match, score, idx = process.extractOne(
            text, keywords, scorer=fuzz.WRatio, processor=utils.default_process
        )
        if score > 90:
            return False
    doc = nlp(text)

    for ent in doc.ents:
        if ent.label_ == "GPE" or ent.label_ == "ORG":
            return True
    return False

def merge_dictionary(dict1, dict2):
    """
    Merges two dictionaries.
        - If a category exists in both dictionaries, their triggers are combined without duplicates.
        - If a category exists only in dict2, it is added to the merged result.

    Method Parameters
    ----------
    dict1 : dict[str, list]
    dict2 : dict[str, list]

    Returns
    -------
    dict[str, list]
    """
    merged_dict = copy.deepcopy(dict1)
    for category in dict2.keys():
        if category in merged_dict:
            for trigger in dict2[category]:
                if trigger not in merged_dict[category]:
                    merged_dict[category].append(trigger)
        else:
            merged_dict[category] = dict2[category]

    return merged_dict