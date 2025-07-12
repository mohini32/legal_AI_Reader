"""
Question Answering Engine for Legal Documents
Advanced Q&A system with context awareness and legal knowledge
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class QAResult:
    """Q&A result with confidence and context"""
    question: str
    answer: str
    confidence: float
    context: str = ""
    sources: List[str] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []

class LegalQAEngine:
    """Advanced Q&A engine for legal documents"""
    
    def __init__(self):
        self.document_text = ""
        self.entities = {}
        self.load_legal_patterns()
    
    def load_legal_patterns(self):
        """Load legal Q&A patterns and knowledge"""
        
        # Multi-currency patterns
        self.currency_patterns = {
            "USD": [r'\$[\d,]+(?:\.\d{2})?', r'USD\s*[\d,]+', r'dollars?'],
            "CAD": [r'CAD\s*[\d,]+', r'C\$[\d,]+', r'Canadian\s+dollars?'],
            "GBP": [r'£[\d,]+(?:\.\d{2})?', r'GBP\s*[\d,]+', r'pounds?'],
            "INR": [r'₹[\d,]+(?:\.\d{2})?', r'Rs\.?\s*[\d,]+', r'INR\s*[\d,]+', r'rupees?', r'[\d,]+\s*(?:crores?|lakhs?)'],
            "EUR": [r'€[\d,]+(?:\.\d{2})?', r'EUR\s*[\d,]+', r'euros?'],
        }
        
        # Legal entity patterns
        self.entity_patterns = {
            "companies": [
                r'\b[A-Z][a-zA-Z\s&]+(?:Inc|LLC|Corp|Corporation|Company|Ltd|Limited|Pvt\.?\s*Ltd\.?|LLP)\b',
                r'\b[A-Z][a-zA-Z\s&]+(?:GmbH|AG|SA|SAS|BV|AB|AS)\b'
            ],
            "people": [
                r'\b(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b',
                r'\b[A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b'
            ]
        }
        
        # Date patterns
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{4}\b'
        ]
        
        # Jurisdiction patterns
        self.jurisdiction_patterns = [
            r'courts?\s+(?:of|in|at)\s+([A-Za-z\s]+)(?:\s+shall\s+have\s+jurisdiction|jurisdiction)',
            r'governed\s+by\s+(?:the\s+)?laws?\s+of\s+([A-Za-z\s]+)',
            r'subject\s+to\s+(?:the\s+)?jurisdiction\s+of\s+([A-Za-z\s]+)',
            r'exclusive\s+jurisdiction\s+of\s+([A-Za-z\s]+)',
            r'courts?\s+of\s+([A-Za-z\s]+)\s+shall\s+have\s+jurisdiction'
        ]
        
        # Termination patterns
        self.termination_patterns = [
            r'(?:terminate|termination).*?(?:upon|after|within)\s+(\d+\s+(?:days?|months?|years?))',
            r'(?:notice\s+of\s+)?termination.*?(\d+\s+(?:days?|months?|years?))',
            r'either\s+party\s+may\s+terminate.*?(\d+\s+(?:days?|months?|years?))',
            r'contract\s+(?:shall\s+)?terminate.*?(\d+\s+(?:days?|months?|years?))'
        ]
        
        # Payment patterns
        self.payment_patterns = [
            r'payment.*?(?:due|payable).*?(\d+\s+(?:days?|months?))',
            r'invoice.*?(?:due|payable).*?(\d+\s+(?:days?|months?))',
            r'(?:net\s+)?(\d+)\s+days?',
            r'payment\s+terms?.*?(\d+\s+(?:days?|months?))'
        ]
    
    def set_document(self, text: str, entities: Dict = None):
        """Set the document text and entities for Q&A"""
        self.document_text = text
        self.entities = entities or {}
    
    def answer_question(self, question: str, country_preference: str = "International") -> QAResult:
        """Answer a question about the document"""
        question_lower = question.lower()
        
        # Route to specific answer functions
        if any(word in question_lower for word in ['value', 'amount', 'price', 'cost', 'money', 'payment']):
            return self._answer_money_question(question, country_preference)
        
        elif any(word in question_lower for word in ['party', 'parties', 'who', 'company', 'organization']):
            return self._answer_party_question(question)
        
        elif any(word in question_lower for word in ['date', 'when', 'expire', 'expiry', 'term', 'duration']):
            return self._answer_date_question(question)
        
        elif any(word in question_lower for word in ['jurisdiction', 'court', 'law', 'governing', 'legal']):
            return self._answer_jurisdiction_question(question)
        
        elif any(word in question_lower for word in ['terminate', 'termination', 'end', 'cancel']):
            return self._answer_termination_question(question)
        
        elif any(word in question_lower for word in ['payment', 'pay', 'invoice', 'billing']):
            return self._answer_payment_question(question)
        
        else:
            return self._answer_general_question(question)
    
    def _answer_money_question(self, question: str, country_preference: str) -> QAResult:
        """Answer questions about monetary amounts"""
        
        # Get currency patterns based on country preference
        if country_preference in self.currency_patterns:
            patterns = self.currency_patterns[country_preference]
        else:
            # Use all patterns for International
            patterns = []
            for currency_patterns in self.currency_patterns.values():
                patterns.extend(currency_patterns)
        
        money_matches = []
        contexts = []
        
        for pattern in patterns:
            for match in re.finditer(pattern, self.document_text, re.IGNORECASE):
                money_matches.append(match.group())
                # Get context around the match
                start = max(0, match.start() - 100)
                end = min(len(self.document_text), match.end() + 100)
                context = self.document_text[start:end].strip()
                contexts.append(context)
        
        if money_matches:
            unique_amounts = list(set(money_matches))
            answer = f"Found monetary amounts: {', '.join(unique_amounts[:5])}"
            if len(unique_amounts) > 5:
                answer += f" and {len(unique_amounts) - 5} more"
            
            return QAResult(
                question=question,
                answer=answer,
                confidence=0.9,
                context=contexts[0] if contexts else "",
                sources=unique_amounts
            )
        else:
            return QAResult(
                question=question,
                answer="No monetary amounts found in the document.",
                confidence=0.3
            )
    
    def _answer_party_question(self, question: str) -> QAResult:
        """Answer questions about parties/organizations"""
        
        companies = []
        people = []
        contexts = []
        
        # Find companies
        for pattern in self.entity_patterns["companies"]:
            for match in re.finditer(pattern, self.document_text):
                companies.append(match.group().strip())
                # Get context
                start = max(0, match.start() - 50)
                end = min(len(self.document_text), match.end() + 50)
                context = self.document_text[start:end].strip()
                contexts.append(context)
        
        # Find people (if asking about individuals)
        if any(word in question.lower() for word in ['person', 'individual', 'signatory', 'representative']):
            for pattern in self.entity_patterns["people"]:
                for match in re.finditer(pattern, self.document_text):
                    people.append(match.group().strip())
        
        all_parties = list(set(companies + people))
        
        if all_parties:
            answer = f"Found parties: {', '.join(all_parties[:5])}"
            if len(all_parties) > 5:
                answer += f" and {len(all_parties) - 5} more"
            
            return QAResult(
                question=question,
                answer=answer,
                confidence=0.85,
                context=contexts[0] if contexts else "",
                sources=all_parties
            )
        else:
            return QAResult(
                question=question,
                answer="No clear parties or organizations identified in the document.",
                confidence=0.3
            )
    
    def _answer_date_question(self, question: str) -> QAResult:
        """Answer questions about dates"""
        
        dates = []
        contexts = []
        
        for pattern in self.date_patterns:
            for match in re.finditer(pattern, self.document_text, re.IGNORECASE):
                dates.append(match.group())
                # Get context
                start = max(0, match.start() - 80)
                end = min(len(self.document_text), match.end() + 80)
                context = self.document_text[start:end].strip()
                contexts.append(context)
        
        if dates:
            unique_dates = list(set(dates))
            answer = f"Found important dates: {', '.join(unique_dates[:5])}"
            if len(unique_dates) > 5:
                answer += f" and {len(unique_dates) - 5} more"
            
            return QAResult(
                question=question,
                answer=answer,
                confidence=0.8,
                context=contexts[0] if contexts else "",
                sources=unique_dates
            )
        else:
            return QAResult(
                question=question,
                answer="No specific dates found in the document.",
                confidence=0.3
            )
    
    def _answer_jurisdiction_question(self, question: str) -> QAResult:
        """Answer questions about jurisdiction and governing law"""
        
        jurisdictions = []
        contexts = []
        
        for pattern in self.jurisdiction_patterns:
            for match in re.finditer(pattern, self.document_text, re.IGNORECASE):
                full_match = match.group()
                jurisdiction = match.group(1) if match.groups() else full_match
                jurisdictions.append(jurisdiction.strip())
                
                # Get context
                start = max(0, match.start() - 50)
                end = min(len(self.document_text), match.end() + 50)
                context = self.document_text[start:end].strip()
                contexts.append(context)
        
        if jurisdictions:
            unique_jurisdictions = list(set(jurisdictions))
            answer = f"Found jurisdiction/governing law: {', '.join(unique_jurisdictions)}"
            
            return QAResult(
                question=question,
                answer=answer,
                confidence=0.9,
                context=contexts[0] if contexts else "",
                sources=unique_jurisdictions
            )
        else:
            return QAResult(
                question=question,
                answer="No clear jurisdiction or governing law clauses found.",
                confidence=0.3
            )
    
    def _answer_termination_question(self, question: str) -> QAResult:
        """Answer questions about termination clauses"""
        
        termination_terms = []
        contexts = []
        
        for pattern in self.termination_patterns:
            for match in re.finditer(pattern, self.document_text, re.IGNORECASE):
                term = match.group(1) if match.groups() else match.group()
                termination_terms.append(term.strip())
                
                # Get context
                start = max(0, match.start() - 100)
                end = min(len(self.document_text), match.end() + 100)
                context = self.document_text[start:end].strip()
                contexts.append(context)
        
        if termination_terms:
            unique_terms = list(set(termination_terms))
            answer = f"Found termination terms: {', '.join(unique_terms)}"
            
            return QAResult(
                question=question,
                answer=answer,
                confidence=0.85,
                context=contexts[0] if contexts else "",
                sources=unique_terms
            )
        else:
            return QAResult(
                question=question,
                answer="No specific termination clauses found.",
                confidence=0.3
            )
    
    def _answer_payment_question(self, question: str) -> QAResult:
        """Answer questions about payment terms"""
        
        payment_terms = []
        contexts = []
        
        for pattern in self.payment_patterns:
            for match in re.finditer(pattern, self.document_text, re.IGNORECASE):
                term = match.group(1) if match.groups() else match.group()
                payment_terms.append(term.strip())
                
                # Get context
                start = max(0, match.start() - 100)
                end = min(len(self.document_text), match.end() + 100)
                context = self.document_text[start:end].strip()
                contexts.append(context)
        
        if payment_terms:
            unique_terms = list(set(payment_terms))
            answer = f"Found payment terms: {', '.join(unique_terms)}"
            
            return QAResult(
                question=question,
                answer=answer,
                confidence=0.85,
                context=contexts[0] if contexts else "",
                sources=unique_terms
            )
        else:
            return QAResult(
                question=question,
                answer="No specific payment terms found.",
                confidence=0.3
            )
    
    def _answer_general_question(self, question: str) -> QAResult:
        """Answer general questions using keyword matching"""
        
        # Simple keyword-based search
        question_words = re.findall(r'\b\w+\b', question.lower())
        
        # Find sentences containing question keywords
        sentences = re.split(r'[.!?]+', self.document_text)
        relevant_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            matches = sum(1 for word in question_words if word in sentence_lower and len(word) > 3)
            if matches >= 2:  # At least 2 keywords match
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            # Return the most relevant sentence
            best_sentence = max(relevant_sentences, key=len)
            answer = best_sentence[:300] + "..." if len(best_sentence) > 300 else best_sentence
            
            return QAResult(
                question=question,
                answer=answer,
                confidence=0.6,
                context=best_sentence,
                sources=[best_sentence]
            )
        else:
            return QAResult(
                question=question,
                answer="I couldn't find specific information to answer that question. Please try rephrasing or ask about parties, amounts, dates, or jurisdiction.",
                confidence=0.2
            )
    
    def get_suggested_questions(self, country_preference: str = "International") -> List[str]:
        """Get suggested questions based on document content and country"""
        
        suggestions = [
            "What is the contract value?",
            "Who are the parties involved?",
            "When does this contract expire?",
            "What are the payment terms?",
            "What jurisdiction governs this contract?",
            "Are there any termination clauses?"
        ]
        
        # Add country-specific questions
        if country_preference == "India":
            suggestions.extend([
                "What are the GST/PAN numbers mentioned?",
                "Which Indian courts have jurisdiction?",
                "Are there any FEMA compliance requirements?"
            ])
        elif country_preference == "USA":
            suggestions.extend([
                "What US state law governs this contract?",
                "Are there any federal compliance requirements?"
            ])
        elif country_preference == "UK":
            suggestions.extend([
                "Which UK courts have jurisdiction?",
                "Are there any Companies House requirements?"
            ])
        
        return suggestions

# Convenience function for backward compatibility
def answer_question(text: str, question: str, entities: Dict = None, country_preference: str = "International") -> str:
    """Simple Q&A function"""
    qa_engine = LegalQAEngine()
    qa_engine.set_document(text, entities)
    result = qa_engine.answer_question(question, country_preference)
    return result.answer
