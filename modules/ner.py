"""
Enhanced Named Entity Recognition for Legal Documents
Combines multiple models and techniques for superior accuracy
"""
import re
import spacy
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from sentence_transformers import SentenceTransformer
import numpy as np
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Entity:
    """Enhanced entity representation"""
    text: str
    label: str
    start: int
    end: int
    confidence: float
    context: str = ""
    normalized_value: str = ""
    entity_type: str = ""
    metadata: Dict[str, Any] = None

class EnhancedNER:
    """
    Advanced NER system combining multiple approaches:
    1. Transformer-based models (BERT, Legal-BERT)
    2. spaCy NLP pipeline
    3. Rule-based extraction
    4. Domain-specific patterns
    5. Entity linking and normalization
    """
    
    def __init__(self, use_legal_models: bool = True):
        self.use_legal_models = use_legal_models
        self.confidence_threshold = 0.75
        self._initialize_models()
        self._load_patterns()
        
    def _initialize_models(self):
        """Initialize all NER models and pipelines"""
        logger.info("Initializing Enhanced NER models...")
        
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
            
            # Standard BERT NER
            self.ner_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                tokenizer="dslim/bert-base-NER",
                aggregation_strategy="simple",
                device=-1  # CPU
            )
            
            # Legal-specific BERT model (if available)
            if self.use_legal_models:
                try:
                    self.legal_ner_pipeline = pipeline(
                        "ner",
                        model="nlpaueb/legal-bert-base-uncased",
                        aggregation_strategy="simple",
                        device=-1
                    )
                except Exception as e:
                    logger.warning(f"Legal BERT model not available: {e}")
                    self.legal_ner_pipeline = None
            else:
                self.legal_ner_pipeline = None
                
            # Sentence transformer for entity linking
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("NER models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing NER models: {e}")
            raise
    
    def _load_patterns(self):
        """Load enhanced regex patterns for legal entities"""
        self.patterns = {
            # Enhanced date patterns
            'dates': [
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b'
            ],
            
            # Enhanced monetary patterns
            'money': [
                r'(?:\$|USD|EUR|GBP|CAD)\s*[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?',
                r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|euros?|pounds?|USD|EUR|GBP|CAD)\b',
                r'\b(?:million|billion|thousand)\s+(?:dollars?|euros?|pounds?)\b'
            ],
            
            # Legal-specific patterns
            'legal_citations': [
                r'\b\d+\s+[A-Z][a-z]+\.?\s+\d+\b',  # Case citations
                r'\b[A-Z][a-z]+\.?\s+v\.?\s+[A-Z][a-z]+\b',  # Case names
                r'\b\d+\s+U\.?S\.?C\.?\s+§?\s*\d+\b',  # USC citations
                r'\b\d+\s+C\.?F\.?R\.?\s+§?\s*\d+\b'  # CFR citations
            ],
            
            # Contract-specific entities
            'contract_terms': [
                r'\b(?:effective|commencement|expiration|termination)\s+date\b',
                r'\b(?:payment|due)\s+date\b',
                r'\b(?:notice|cure)\s+period\b',
                r'\b(?:liability|damage)\s+cap\b'
            ],
            
            # Party identification
            'parties': [
                r'\b(?:party|parties)\s+(?:of\s+the\s+)?(?:first|second|third)\s+part\b',
                r'\b(?:licensor|licensee|contractor|subcontractor)\b',
                r'\b(?:buyer|seller|vendor|client|customer)\b',
                r'\b(?:employer|employee|consultant)\b'
            ],
            
            # Addresses and locations
            'addresses': [
                r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)\b',
                r'\b[A-Z][a-z]+,\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?\b'  # City, State ZIP
            ],
            
            # Contact information
            'contact_info': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',  # Phone
                r'\b(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?\b'  # Website
            ],
            
            # Legal concepts
            'legal_concepts': [
                r'\b(?:force\s+majeure|act\s+of\s+god)\b',
                r'\b(?:intellectual\s+property|trade\s+secret)\b',
                r'\b(?:non-disclosure|confidentiality)\s+agreement\b',
                r'\b(?:limitation\s+of\s+liability|indemnification)\b'
            ]
        }
    
    def extract_with_transformers(self, text: str) -> List[Entity]:
        """Extract entities using transformer models"""
        entities = []
        
        # Standard BERT NER
        try:
            bert_entities = self.ner_pipeline(text)
            for ent in bert_entities:
                if ent['score'] >= self.confidence_threshold:
                    entities.append(Entity(
                        text=ent['word'],
                        label=ent['entity_group'],
                        start=ent['start'],
                        end=ent['end'],
                        confidence=ent['score'],
                        entity_type='transformer_ner'
                    ))
        except Exception as e:
            logger.error(f"Error in BERT NER: {e}")
        
        # Legal BERT NER (if available)
        if self.legal_ner_pipeline:
            try:
                legal_entities = self.legal_ner_pipeline(text)
                for ent in legal_entities:
                    if ent['score'] >= self.confidence_threshold:
                        entities.append(Entity(
                            text=ent['word'],
                            label=f"LEGAL_{ent['entity_group']}",
                            start=ent['start'],
                            end=ent['end'],
                            confidence=ent['score'],
                            entity_type='legal_transformer_ner'
                        ))
            except Exception as e:
                logger.error(f"Error in Legal BERT NER: {e}")
        
        return entities
    
    def extract_with_spacy(self, text: str) -> List[Entity]:
        """Extract entities using spaCy"""
        entities = []
        
        try:
            doc = self.nlp(text)
            for ent in doc.ents:
                entities.append(Entity(
                    text=ent.text,
                    label=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.8,  # spaCy doesn't provide confidence scores
                    context=ent.sent.text if ent.sent else "",
                    entity_type='spacy_ner'
                ))
        except Exception as e:
            logger.error(f"Error in spaCy NER: {e}")
        
        return entities
    
    def extract_with_patterns(self, text: str) -> List[Entity]:
        """Extract entities using regex patterns"""
        entities = []
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                try:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        entities.append(Entity(
                            text=match.group(),
                            label=category.upper(),
                            start=match.start(),
                            end=match.end(),
                            confidence=0.9,  # High confidence for pattern matches
                            entity_type='pattern_based'
                        ))
                except Exception as e:
                    logger.error(f"Error in pattern matching for {category}: {e}")
        
        return entities
    
    def normalize_entities(self, entities: List[Entity]) -> List[Entity]:
        """Normalize and clean entity values"""
        normalized = []
        
        for entity in entities:
            normalized_entity = entity
            
            # Normalize dates
            if 'date' in entity.label.lower():
                normalized_entity.normalized_value = self._normalize_date(entity.text)
            
            # Normalize monetary amounts
            elif 'money' in entity.label.lower() or entity.label in ['MONEY', 'MONETARY']:
                normalized_entity.normalized_value = self._normalize_money(entity.text)
            
            # Clean and normalize text
            normalized_entity.text = entity.text.strip()
            
            normalized.append(normalized_entity)
        
        return normalized
    
    def _normalize_date(self, date_text: str) -> str:
        """Normalize date formats"""
        # This is a simplified version - in production, use dateutil.parser
        return date_text.strip()
    
    def _normalize_money(self, money_text: str) -> str:
        """Normalize monetary amounts"""
        # Extract numeric value and currency
        import re
        amount_match = re.search(r'[\d,]+(?:\.\d{2})?', money_text)
        if amount_match:
            return amount_match.group().replace(',', '')
        return money_text
    
    def deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities and resolve conflicts"""
        # Group entities by position
        position_groups = defaultdict(list)
        for entity in entities:
            key = (entity.start, entity.end)
            position_groups[key].append(entity)
        
        deduplicated = []
        for position, group in position_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Choose entity with highest confidence
                best_entity = max(group, key=lambda x: x.confidence)
                deduplicated.append(best_entity)
        
        return deduplicated
    
    def extract_entities(self, text: str) -> Dict[str, List[Entity]]:
        """
        Main entity extraction method combining all approaches
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary of entity categories and their entities
        """
        logger.info("Starting enhanced entity extraction")
        
        all_entities = []
        
        # Extract using different methods
        transformer_entities = self.extract_with_transformers(text)
        spacy_entities = self.extract_with_spacy(text)
        pattern_entities = self.extract_with_patterns(text)
        
        # Combine all entities
        all_entities.extend(transformer_entities)
        all_entities.extend(spacy_entities)
        all_entities.extend(pattern_entities)
        
        # Normalize entities
        normalized_entities = self.normalize_entities(all_entities)
        
        # Remove duplicates
        final_entities = self.deduplicate_entities(normalized_entities)
        
        # Group by category
        categorized = defaultdict(list)
        for entity in final_entities:
            categorized[entity.label].append(entity)
        
        logger.info(f"Extracted {len(final_entities)} entities across {len(categorized)} categories")
        
        return dict(categorized)
    
    def get_entity_summary(self, entities: Dict[str, List[Entity]]) -> Dict[str, Any]:
        """Generate summary statistics for extracted entities"""
        summary = {
            'total_entities': sum(len(ents) for ents in entities.values()),
            'categories': list(entities.keys()),
            'category_counts': {cat: len(ents) for cat, ents in entities.items()},
            'high_confidence_entities': sum(
                1 for ents in entities.values() 
                for ent in ents if ent.confidence > 0.9
            ),
            'extraction_methods': list(set(
                ent.entity_type for ents in entities.values() for ent in ents
            ))
        }
        
        return summary
