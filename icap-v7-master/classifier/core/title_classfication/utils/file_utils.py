# Global Import
import json
import spacy

def load_labels(file_path):

    # Read the JSON file and load its content into a dictionary
    with open(file_path, "r") as json_file:
        category = json.load(json_file)
    return category

def load_memory_points(file_path):

    # Read the JSON file and load its content into a dictionary
    with open(file_path, "r") as json_file:
        matrix_keys = json.load(json_file)
    return matrix_keys

def load_nlp_model():
    nlp = spacy.load("/app/core/model/en_core_web_sm-3.7.1")
    return nlp