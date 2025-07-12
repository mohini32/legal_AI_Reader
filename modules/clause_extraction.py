import spacy
from spacy.language import Language
nlp=spacy.load("en_core_web_sm")
@Language.component("set_custom_boundaries")
def set_custom_boundaries(doc):
    for token in doc[:-1]:
        if token.text in [";","but","and","although","however","but","Hence"]:
            doc[token.i+1].is_sent_start = True
    return doc 

if "set_custom_boundaries" not in nlp.pipe_names:
    nlp.add_pipe("set_custom_boundaries", before="parser")


def extract_clauses(text):
    doc=nlp(text)
    return [sent.text.strip() for sent in doc.sents]          
        