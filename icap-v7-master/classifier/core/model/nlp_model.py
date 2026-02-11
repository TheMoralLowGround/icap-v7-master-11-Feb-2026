import spacy

def load_nlp_model():
    nlp = spacy.load("/app/core/model/en_core_web_sm-3.7.1")
    return nlp