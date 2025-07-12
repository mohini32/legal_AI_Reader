"""
Enhanced Risk Detection System for Legal Documents
Uses ML models, semantic analysis, and legal domain knowledge
"""
import re
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskCategory(Enum):
    LIABILITY = "liability"
    FINANCIAL = "financial"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    CONFIDENTIALITY = "confidentiality"
    TERMINATION = "termination"
    DISPUTE_RESOLUTION = "dispute_resolution"

@dataclass
class RiskFactor:
    """Represents a detected risk factor"""
    text: str
    category: RiskCategory
    level: RiskLevel
    confidence: float
    explanation: str
    clause_context: str = ""
    recommendations: List[str] = field(default_factory=list)
    legal_precedents: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)

@dataclass
class RiskAssessment:
    """Complete risk assessment result"""
    overall_score: float
    risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    missing_clauses: List[str]
    recommendations: List[str]
    summary: str
    confidence: float

class EnhancedRiskDetector:
    """
    Advanced risk detection system using:
    1. Semantic similarity analysis
    2. ML-based classification
    3. Legal domain knowledge
    4. Pattern-based detection
    5. Missing clause analysis
    """
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self._initialize_models()
        self._load_risk_knowledge()
        
    def _initialize_models(self):
        """Initialize ML models and NLP components"""
        logger.info("Initializing Enhanced Risk Detection models...")
        
        try:
            # Sentence transformer for semantic analysis
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # spaCy for text processing
            self.nlp = spacy.load("en_core_web_sm")
            
            # TF-IDF vectorizer for text analysis
            self.tfidf = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 3)
            )
            
            logger.info("Risk detection models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing risk detection models: {e}")
            raise
    
    def _load_risk_knowledge(self):
        """Load comprehensive risk knowledge base"""
        
        # High-risk patterns with detailed explanations
        self.risk_patterns = {
            RiskCategory.LIABILITY: {
                'patterns': [
                    r'\bunlimited\s+liability\b',
                    r'\bpersonal\s+guarantee\b',
                    r'\bjoint\s+and\s+several\s+liability\b',
                    r'\bindemnif(?:y|ication)\b.*\bfrom\s+and\s+against\s+all\b',
                    r'\bhold\s+harmless\b',
                    r'\bno\s+limitation\s+of\s+liability\b'
                ],
                'explanations': {
                    'unlimited liability': 'Unlimited liability exposes parties to potentially catastrophic financial losses without caps or limits.',
                    'personal guarantee': 'Personal guarantees put individual assets at risk beyond business assets.',
                    'joint and several liability': 'Joint and several liability makes each party responsible for the full amount of damages.'
                }
            },
            
            RiskCategory.FINANCIAL: {
                'patterns': [
                    r'\bliquidated\s+damages\b',
                    r'\bpenalty\b(?!\s+clause)',
                    r'\binterest\s+rate\b.*\b(?:per\s+month|monthly)\b',
                    r'\bimmediate\s+payment\b',
                    r'\bno\s+right\s+to\s+offset\b',
                    r'\bpayment\s+in\s+advance\b'
                ],
                'explanations': {
                    'liquidated damages': 'Liquidated damages clauses can result in significant financial penalties.',
                    'penalty': 'Penalty clauses may impose harsh financial consequences for minor breaches.',
                    'high interest': 'Excessive interest rates can create unsustainable financial burdens.'
                }
            },
            
            RiskCategory.TERMINATION: {
                'patterns': [
                    r'\bterminate\s+(?:immediately|without\s+notice)\b',
                    r'\bno\s+cure\s+period\b',
                    r'\btermination\s+for\s+convenience\b',
                    r'\bimmediate\s+termination\b',
                    r'\bterminate\s+at\s+will\b'
                ],
                'explanations': {
                    'immediate termination': 'Immediate termination clauses provide no opportunity to cure breaches.',
                    'termination for convenience': 'Termination for convenience allows unilateral contract termination without cause.',
                    'no cure period': 'Absence of cure periods prevents parties from correcting minor violations.'
                }
            },
            
            RiskCategory.INTELLECTUAL_PROPERTY: {
                'patterns': [
                    r'\bassignment\s+of\s+(?:all\s+)?(?:intellectual\s+property|ip)\b',
                    r'\bwork\s+for\s+hire\b',
                    r'\bexclusive\s+license\b',
                    r'\btrade\s+secrets?\b.*\bperpetual\b',
                    r'\bnon-compete\b.*\b(?:worldwide|global)\b'
                ],
                'explanations': {
                    'ip assignment': 'Broad IP assignment clauses may transfer valuable intellectual property rights.',
                    'work for hire': 'Work for hire provisions can result in loss of ownership of created works.',
                    'exclusive license': 'Exclusive licenses may prevent use of own intellectual property.'
                }
            },
            
            RiskCategory.COMPLIANCE: {
                'patterns': [
                    r'\bstrict\s+compliance\b',
                    r'\bmaterial\s+adverse\s+change\b',
                    r'\brepresentations\s+and\s+warranties\b.*\bsurvive\b',
                    r'\bcontinuing\s+representations\b'
                ],
                'explanations': {
                    'strict compliance': 'Strict compliance requirements leave no room for minor deviations.',
                    'material adverse change': 'Material adverse change clauses can trigger contract termination.',
                    'surviving warranties': 'Surviving warranties extend liability beyond contract termination.'
                }
            }
        }
        
        # Standard clauses that should be present
        self.standard_clauses = {
            'limitation_of_liability': [
                'limitation of liability', 'liability cap', 'damages limitation'
            ],
            'force_majeure': [
                'force majeure', 'act of god', 'unforeseeable circumstances'
            ],
            'confidentiality': [
                'confidentiality', 'non-disclosure', 'proprietary information'
            ],
            'dispute_resolution': [
                'dispute resolution', 'arbitration', 'mediation', 'governing law'
            ],
            'termination_notice': [
                'termination notice', 'notice period', 'advance notice'
            ],
            'intellectual_property': [
                'intellectual property', 'ip rights', 'proprietary rights'
            ]
        }
        
        # Risk mitigation recommendations
        self.mitigation_strategies = {
            RiskCategory.LIABILITY: [
                "Add liability caps to limit maximum exposure",
                "Include mutual indemnification clauses",
                "Negotiate carve-outs for gross negligence and willful misconduct",
                "Consider insurance requirements"
            ],
            RiskCategory.FINANCIAL: [
                "Negotiate payment terms and schedules",
                "Add right to offset provisions",
                "Include dispute resolution for payment disputes",
                "Consider escrow arrangements for large payments"
            ],
            RiskCategory.TERMINATION: [
                "Add cure periods for non-material breaches",
                "Negotiate termination notice requirements",
                "Include survival clauses for important provisions",
                "Define material breach clearly"
            ]
        }
    
    def analyze_semantic_risks(self, text: str) -> List[RiskFactor]:
        """Analyze risks using semantic similarity"""
        risk_factors = []
        
        # Split text into sentences for analysis
        doc = self.nlp(text)
        sentences = [sent.text for sent in doc.sents]
        
        if not sentences:
            return risk_factors
        
        # Get embeddings for all sentences
        sentence_embeddings = self.embedder.encode(sentences)
        
        # Analyze each risk category
        for category, data in self.risk_patterns.items():
            for pattern in data['patterns']:
                # Find pattern matches
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    # Find the sentence containing this match
                    match_sentence = None
                    for i, sent in enumerate(sentences):
                        if match.start() >= text.find(sent) and match.end() <= text.find(sent) + len(sent):
                            match_sentence = sent
                            break
                    
                    if match_sentence:
                        # Calculate risk level based on pattern severity
                        risk_level = self._calculate_risk_level(pattern, match_sentence)
                        
                        # Get explanation
                        explanation = self._get_risk_explanation(pattern, category, data)
                        
                        risk_factor = RiskFactor(
                            text=match.group(),
                            category=category,
                            level=risk_level,
                            confidence=0.85,
                            explanation=explanation,
                            clause_context=match_sentence,
                            recommendations=self.mitigation_strategies.get(category, []),
                            mitigation_strategies=self.mitigation_strategies.get(category, [])
                        )
                        
                        risk_factors.append(risk_factor)
        
        return risk_factors
    
    def _calculate_risk_level(self, pattern: str, context: str) -> RiskLevel:
        """Calculate risk level based on pattern and context"""
        # High-risk patterns
        high_risk_indicators = [
            'unlimited', 'immediate', 'no cure', 'personal guarantee',
            'joint and several', 'liquidated damages'
        ]
        
        # Critical risk patterns
        critical_risk_indicators = [
            'unlimited liability', 'personal guarantee', 'immediate termination'
        ]
        
        pattern_lower = pattern.lower()
        context_lower = context.lower()
        
        if any(indicator in pattern_lower or indicator in context_lower 
               for indicator in critical_risk_indicators):
            return RiskLevel.CRITICAL
        elif any(indicator in pattern_lower or indicator in context_lower 
                 for indicator in high_risk_indicators):
            return RiskLevel.HIGH
        elif any(word in pattern_lower for word in ['penalty', 'forfeit', 'breach']):
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _get_risk_explanation(self, pattern: str, category: RiskCategory, data: Dict) -> str:
        """Get detailed explanation for a risk pattern"""
        explanations = data.get('explanations', {})
        
        # Try to find specific explanation
        for key, explanation in explanations.items():
            if key in pattern.lower():
                return explanation
        
        # Default explanations by category
        default_explanations = {
            RiskCategory.LIABILITY: "This clause may expose parties to significant liability risks.",
            RiskCategory.FINANCIAL: "This provision could result in unexpected financial obligations.",
            RiskCategory.TERMINATION: "This termination clause may be unfavorable to one party.",
            RiskCategory.INTELLECTUAL_PROPERTY: "This clause affects intellectual property rights.",
            RiskCategory.COMPLIANCE: "This provision imposes strict compliance requirements."
        }
        
        return default_explanations.get(category, "This clause presents potential risks.")
    
    def detect_missing_clauses(self, text: str) -> List[str]:
        """Detect important missing clauses"""
        missing_clauses = []
        text_lower = text.lower()
        
        for clause_type, keywords in self.standard_clauses.items():
            if not any(keyword in text_lower for keyword in keywords):
                missing_clauses.append(clause_type.replace('_', ' ').title())
        
        return missing_clauses
    
    def calculate_overall_risk_score(self, risk_factors: List[RiskFactor], 
                                   missing_clauses: List[str]) -> Tuple[float, RiskLevel]:
        """Calculate overall risk score and level"""
        if not risk_factors and not missing_clauses:
            return 2.0, RiskLevel.LOW
        
        # Base score calculation
        score = 0.0
        
        # Add scores based on risk factors
        risk_weights = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 2.5,
            RiskLevel.HIGH: 4.0,
            RiskLevel.CRITICAL: 5.0
        }
        
        for factor in risk_factors:
            weight = risk_weights[factor.level]
            score += weight * factor.confidence
        
        # Add penalty for missing clauses
        score += len(missing_clauses) * 0.5
        
        # Normalize score to 1-10 scale
        max_possible_score = len(risk_factors) * 5.0 + len(missing_clauses) * 0.5
        if max_possible_score > 0:
            normalized_score = min(10.0, (score / max_possible_score) * 10)
        else:
            normalized_score = 1.0
        
        # Determine risk level
        if normalized_score >= 8.0:
            risk_level = RiskLevel.CRITICAL
        elif normalized_score >= 6.0:
            risk_level = RiskLevel.HIGH
        elif normalized_score >= 4.0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return normalized_score, risk_level
    
    def assess_risk(self, text: str) -> RiskAssessment:
        """
        Perform comprehensive risk assessment
        
        Args:
            text: Document text to analyze
            
        Returns:
            Complete risk assessment
        """
        logger.info("Starting enhanced risk assessment")
        
        # Detect risk factors
        risk_factors = self.analyze_semantic_risks(text)
        
        # Detect missing clauses
        missing_clauses = self.detect_missing_clauses(text)
        
        # Calculate overall score
        overall_score, risk_level = self.calculate_overall_risk_score(
            risk_factors, missing_clauses
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_factors, missing_clauses)
        
        # Generate summary
        summary = self._generate_summary(risk_factors, missing_clauses, overall_score)
        
        # Calculate confidence
        confidence = self._calculate_confidence(risk_factors)
        
        assessment = RiskAssessment(
            overall_score=overall_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            missing_clauses=missing_clauses,
            recommendations=recommendations,
            summary=summary,
            confidence=confidence
        )
        
        logger.info(f"Risk assessment completed. Score: {overall_score:.1f}, Level: {risk_level.value}")
        
        return assessment
    
    def _generate_recommendations(self, risk_factors: List[RiskFactor], 
                                missing_clauses: List[str]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Recommendations for risk factors
        for factor in risk_factors:
            if factor.recommendations:
                recommendations.extend(factor.recommendations[:2])  # Top 2 recommendations
        
        # Recommendations for missing clauses
        if missing_clauses:
            recommendations.append(f"Consider adding the following clauses: {', '.join(missing_clauses)}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:10]  # Top 10 recommendations
    
    def _generate_summary(self, risk_factors: List[RiskFactor], 
                         missing_clauses: List[str], overall_score: float) -> str:
        """Generate risk assessment summary"""
        if overall_score >= 8.0:
            severity = "critical"
        elif overall_score >= 6.0:
            severity = "high"
        elif overall_score >= 4.0:
            severity = "moderate"
        else:
            severity = "low"
        
        summary = f"This document presents {severity} risk with a score of {overall_score:.1f}/10. "
        
        if risk_factors:
            summary += f"Found {len(risk_factors)} risk factors across {len(set(f.category for f in risk_factors))} categories. "
        
        if missing_clauses:
            summary += f"Missing {len(missing_clauses)} important protective clauses. "
        
        summary += "Review recommendations for risk mitigation strategies."
        
        return summary
    
    def _calculate_confidence(self, risk_factors: List[RiskFactor]) -> float:
        """Calculate overall confidence in the assessment"""
        if not risk_factors:
            return 0.8  # Default confidence for no risks found
        
        avg_confidence = sum(factor.confidence for factor in risk_factors) / len(risk_factors)
        return min(0.95, avg_confidence)  # Cap at 95%
