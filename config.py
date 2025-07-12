"""
Working Configuration for Legal AI Document Reader
Simple, functional configuration without complex imports
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
TEMP_DIR = PROJECT_ROOT / "temp"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Model configurations
NER_MODEL = "dslim/bert-base-NER"
CONFIDENCE_THRESHOLD = 0.8

# Document processing settings
MAX_FILE_SIZE_MB = 50
SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt']
MAX_PAGES = 50

# Risk assessment settings
RISK_SCORE_RANGE = (1, 10)
RISK_WEIGHTS = {
    'liability': 3.0,
    'termination': 2.5,
    'payment': 2.0,
    'missing_clauses': 1.5,
    'unusual_terms': 1.0
}

# UI settings
PAGE_TITLE = "Legal AI Document Intelligence Platform"
PAGE_ICON = "⚖️"
LAYOUT = "wide"

# Processing timeouts
PROCESSING_TIMEOUT = 300  # 5 minutes
MAX_TEXT_LENGTH = 100000  # characters

# Regex patterns for entity extraction
ENTITY_PATTERNS = {
    'dates': r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b',
    'money': r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})? dollars?\b',
    'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
    'percentages': r'\b\d+(?:\.\d+)?%\b'
}

# Q&A predefined questions
PREDEFINED_QUESTIONS = [
    "What is the contract value?",
    "When does this contract expire?",
    "Who are the parties involved?",
    "What are the payment terms?",
    "What is the termination notice period?",
    "Are there any liability limitations?",
    "What are the key obligations?",
    "When is the effective date?"
]

# Risk keywords and indicators
RISK_INDICATORS = {
    'high_risk': [
        'unlimited liability', 'personal guarantee', 'liquidated damages',
        'immediate termination', 'no cure period', 'broad indemnification'
    ],
    'medium_risk': [
        'penalty', 'forfeit', 'breach', 'default', 'suspend',
        'terminate for convenience', 'exclusive dealing'
    ],
    'low_risk': [
        'reasonable efforts', 'commercially reasonable', 'good faith',
        'mutual agreement', 'standard terms'
    ]
}

# Standard contract clauses to check for
STANDARD_CLAUSES = [
    'confidentiality', 'non-disclosure', 'intellectual property',
    'limitation of liability', 'indemnification', 'termination',
    'governing law', 'dispute resolution', 'force majeure'
]
