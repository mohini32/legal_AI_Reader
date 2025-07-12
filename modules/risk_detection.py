from typing import List, Dict
import re
import spacy
from rapidfuzz import fuzz

nlp=spacy.load("en_core_web_sm")

# Some sample keywords. You'll grow this list later.
RISK_KEYWORDS = [
    "termination", "penalty", "liability", "indemnity", 
    "arbitration", "non-compete", "breach", "damages",
    "fine", "non-disclosure", "interest", "jurisdiction",
    "forfeit",
    "breach",
    "default",
    "suspend",
    "terminate for convenience",
    "exclusive dealing",
    "non-compete",
    "restraint of trade",
    "specific performance",
    "injunctive relief",
    "material adverse change",
    "reasonable efforts",
    "commercially reasonable",
    "good faith",
    "mutual agreement",
    "standard terms",
    "industry standard",
    "customary",
    "reasonable notice",
     "unlimited liability",
    "personal guarantee",
    "liquidated damages",
    "immediate termination",
    "no cure period",
    "broad indemnification",
    "joint and several liability",
    "waiver of jury trial",
    "confession of judgment",
    "attorney fees and costs"
]

class RiskDetector:
    def __init__(self,threshold=80):
      self.threshold=threshold

    def is_risky(self,text:str)-> bool:
      for word in RISK_KEYWORDS:
        if fuzz.partial_ratio(word.lower(),text.lower())>self.threshold:
            return True
      return False      

    def detect(self, clauses: List[str]) -> List[Dict]:
        flagged = []
        for clause in clauses:
            if self.is_risky(clause):
                flagged.append({
                    "clause": clause,
                    "risky": True
                })
            else:
                flagged.append({
                    "clause": clause,
                    "risky": False
                })
        return flagged
