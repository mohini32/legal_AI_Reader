"""
Legal AI Document Reader - Complete Application
Uses ALL available modules: NER, QA Engine, Chat Memory, Feedback, Summarization, Risk Detection
"""
import streamlit as st
import pandas as pd
import re
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import hashlib

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import ALL available modules
try:
    from modules import clause_extraction, utils
    from modules.summarizer import Summarize  # Proper import for summarization
    from modules.risk_detection import RiskDetector
    from modules.ner import LegalNER, extract_entities
    from modules.qa_engine import LegalQAEngine, QAResult  # Import QA engine
    from modules.chat_memory import ChatMemory
    from modules.feedback import FeedbackManager, FeedbackCollector
    try:
        from modules.enhanced_risk_detection import EnhancedRiskDetector
        ENHANCED_RISK_AVAILABLE = True
    except ImportError:
        ENHANCED_RISK_AVAILABLE = False
    MODULES_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Some modules not available: {e}. Using fallback mode.")
    MODULES_AVAILABLE = False
    ENHANCED_RISK_AVAILABLE = False

# Import configuration
try:
    import config
except ImportError:
    class Config:
        PAGE_TITLE = "Legal AI Document Reader"
        PAGE_ICON = "⚖️"
        LAYOUT = "wide"
        MAX_FILE_SIZE_MB = 50
        SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt']
    config = Config()

# Configure Streamlit
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT
)

# Initialize session state with ALL modules
if 'chat_memory' not in st.session_state:
    st.session_state.chat_memory = ChatMemory() if MODULES_AVAILABLE else None
if 'qa_engine' not in st.session_state:
    st.session_state.qa_engine = LegalQAEngine() if MODULES_AVAILABLE else None
if 'feedback_manager' not in st.session_state:
    st.session_state.feedback_manager = FeedbackManager() if MODULES_AVAILABLE else None
if 'summarizer' not in st.session_state:
    try:
        st.session_state.summarizer = Summarize() if MODULES_AVAILABLE else None
    except Exception:
        st.session_state.summarizer = None  # Fallback if model not available
if 'ner_system' not in st.session_state:
    st.session_state.ner_system = LegalNER() if MODULES_AVAILABLE else None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'current_document' not in st.session_state:
    st.session_state.current_document = None
if 'document_id' not in st.session_state:
    st.session_state.document_id = None

def get_document_id(text: str) -> str:
    """Generate unique document ID for chat memory"""
    return hashlib.md5(text.encode()).hexdigest()[:8]

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded file"""
    try:
        if uploaded_file.type == "text/plain":
            return str(uploaded_file.read(), "utf-8")
        elif uploaded_file.type == "application/pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(uploaded_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                st.error("PDF support requires pypdf. Install with: pip install pypdf")
                return None
        elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                                   "application/msword"]:
            try:
                import docx
                doc = docx.Document(uploaded_file)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except ImportError:
                st.error("DOCX support requires python-docx. Install with: pip install python-docx")
                return None
        else:
            st.error(f"Unsupported file type: {uploaded_file.type}")
            return None
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return None

def analyze_document_with_all_modules(text, country_preference="International"):
    """Analyze document using ALL available modules"""
    results = {}
    
    # 1. ENTITY EXTRACTION using NER module
    if MODULES_AVAILABLE and st.session_state.ner_system:
        try:
            with st.spinner("🔍 Extracting entities with NER..."):
                entities = st.session_state.ner_system.extract_entities(text)
                entity_summary = st.session_state.ner_system.get_entity_summary(entities)
                results['entities'] = entities
                results['entity_summary'] = entity_summary
                st.success(f"✅ Extracted {entity_summary['total_entities']} entities")
        except Exception as e:
            st.warning(f"NER module error: {e}")
            results['entities'] = extract_entities(text)
    else:
        # Fallback entity extraction
        results['entities'] = {
            'MONEY': re.findall(r'[\$₹£€][\d,]+(?:\.\d{2})?|(?:USD|INR|GBP|EUR|CAD|Rs\.?)\s*[\d,]+', text, re.IGNORECASE),
            'DATE': re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text),
            'EMAIL': re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text),
            'PHONE': re.findall(r'\b(?:\+\d{1,3}[-.\s]?)?\d{10}\b', text),
            'ORGANIZATIONS': re.findall(r'\b[A-Z][a-zA-Z\s&]+(?:Inc|LLC|Corp|Corporation|Company|Ltd|Limited|Pvt\.?\s*Ltd\.?|LLP|GmbH|AG|SA)\b', text)
        }
    
    # 2. DOCUMENT SUMMARIZATION using Summarizer module
    if MODULES_AVAILABLE and st.session_state.summarizer:
        try:
            with st.spinner("📄 Generating document summary..."):
                # Truncate text if too long for summarizer
                text_for_summary = text[:5000] if len(text) > 5000 else text
                summary = st.session_state.summarizer.summarize(text_for_summary)
                results['summary'] = summary
                st.success("✅ Document summarized")
        except Exception as e:
            st.warning(f"Summarization error: {e}")
            # Simple fallback summary
            sentences = re.split(r'[.!?]+', text)
            results['summary'] = '. '.join(sentences[:3]) + '.'
    else:
        # Simple fallback summary
        sentences = re.split(r'[.!?]+', text)
        results['summary'] = '. '.join(sentences[:3]) + '.'
    
    # 3. RISK DETECTION using Risk Detection modules
    try:
        with st.spinner("⚠️ Analyzing risks..."):
            if ENHANCED_RISK_AVAILABLE:
                risk_detector = EnhancedRiskDetector()
                risk_assessment = risk_detector.assess_risk(text)
            else:
                risk_detector = RiskDetector()
                risk_clauses = risk_detector.detect([text])
                # Convert to standard format
                risk_assessment = {
                    'overall_score': len([r for r in risk_clauses if r.get('risky', False)]) * 2,
                    'risk_level': 'High' if len([r for r in risk_clauses if r.get('risky', False)]) > 3 else 'Medium' if len([r for r in risk_clauses if r.get('risky', False)]) > 1 else 'Low',
                    'risk_factors': risk_clauses
                }
            results['risk_assessment'] = risk_assessment
            st.success(f"✅ Risk analysis complete - Level: {risk_assessment.get('risk_level', 'Unknown')}")
    except Exception as e:
        st.warning(f"Risk detection error: {e}")
        results['risk_assessment'] = {'overall_score': 0, 'risk_level': 'Unknown', 'risk_factors': []}
    
    # 4. CLAUSE EXTRACTION using Clause Extraction module
    try:
        with st.spinner("📋 Extracting clauses..."):
            if MODULES_AVAILABLE and hasattr(clause_extraction, 'extract_clauses'):
                clauses = clause_extraction.extract_clauses(text)
                results['clauses'] = clauses
            else:
                # Simple clause extraction
                sentences = re.split(r'[.!?]+', text)
                results['clauses'] = [s.strip() for s in sentences if len(s.strip()) > 50][:10]
            st.success(f"✅ Extracted {len(results['clauses'])} clauses")
    except Exception as e:
        st.warning(f"Clause extraction error: {e}")
        results['clauses'] = []
    
    # 5. SETUP QA ENGINE with document
    if MODULES_AVAILABLE and st.session_state.qa_engine:
        try:
            st.session_state.qa_engine.set_document(text, results.get('entities', {}))
            results['qa_ready'] = True
            st.success("✅ Q&A engine ready")
        except Exception as e:
            st.warning(f"QA engine setup error: {e}")
            results['qa_ready'] = False
    else:
        results['qa_ready'] = False
    
    return results

def display_chat_history(document_id):
    """Display chat history for current document"""
    if st.session_state.chat_memory and document_id:
        history = st.session_state.chat_memory.get_history(document_id)
        if history:
            st.subheader("💬 Previous Questions & Answers")
            with st.expander(f"Chat History ({len(history)} interactions)", expanded=False):
                for i, interaction in enumerate(history, 1):
                    st.markdown(f"**Q{i}:** {interaction['question']}")
                    st.markdown(f"**A{i}:** {interaction['answer']}")
                    st.markdown("---")
                
                if st.button("🗑️ Clear Chat History"):
                    st.session_state.chat_memory.clear_history(document_id)
                    st.rerun()

def ask_question_with_qa_engine(question, country_preference, document_id):
    """Ask question using QA engine and save to chat memory"""
    if MODULES_AVAILABLE and st.session_state.qa_engine:
        try:
            # Use QA engine
            qa_result = st.session_state.qa_engine.answer_question(question, country_preference)
            
            # Display result
            st.markdown(f"**Q:** {question}")
            st.markdown(f"**A:** {qa_result.answer}")
            
            if qa_result.confidence < 0.5:
                st.warning(f"⚠️ Low confidence answer ({qa_result.confidence:.2f})")
            
            if qa_result.context:
                with st.expander("📄 Context"):
                    st.markdown(qa_result.context)
            
            # Save to chat memory
            if st.session_state.chat_memory and document_id:
                st.session_state.chat_memory.add_interaction(document_id, question, qa_result.answer)
            
            return qa_result
            
        except Exception as e:
            st.error(f"QA engine error: {e}")
            return None
    else:
        st.error("QA engine not available")
        return None

def main():
    """Main application using ALL modules"""
    
    # Header
    st.title("⚖️ Legal AI Document Reader")
    st.markdown("*Complete AI-powered contract analysis with all modules*")
    
    # Module status indicator
    if MODULES_AVAILABLE:
        st.success("🟢 **All AI modules loaded and ready!**")
    else:
        st.warning("🟡 **Running in fallback mode - some features limited**")
    
    # Sidebar
    with st.sidebar:
        st.header("🌍 Settings")
        
        # Country/Region preference
        country_preference = st.selectbox(
            "Country/Region Focus",
            ["International", "USA", "Canada", "UK", "India", "EU"],
            help="Optimize analysis for specific legal systems and currencies"
        )
        
        # Currency preference display
        currency_map = {
            "International": "Multi-currency",
            "USA": "US Dollars ($)",
            "Canada": "Canadian Dollars (CAD)",
            "UK": "British Pounds (£)",
            "India": "Indian Rupees (₹)",
            "EU": "Euros (€)"
        }
        st.info(f"**Primary Currency:** {currency_map[country_preference]}")
        
        st.subheader("🤖 AI Modules Status")
        module_status = []
        if MODULES_AVAILABLE:
            module_status.extend([
                "✅ **NER** (Named Entity Recognition)",
                "✅ **QA Engine** (Question Answering)",
                "✅ **Chat Memory** (Conversation History)",
                "✅ **Feedback System** (User Ratings)",
                "✅ **Document Summarization**",
                "✅ **Risk Detection & Assessment",
                "✅ **Clause Extraction**"
            ])
            if ENHANCED_RISK_AVAILABLE:
                module_status.append("✅ **Enhanced Risk Detection**")
            if st.session_state.summarizer:
                module_status.append("✅ **AI Summarization Model**")
        else:
            module_status.extend([
                "🟡 Basic Entity Extraction",
                "🟡 Simple Risk Detection",
                "🟡 Basic Q&A System"
            ])
        
        for status in module_status:
            st.markdown(status)
        
        # Chat memory status
        if st.session_state.chat_memory and st.session_state.document_id:
            history_count = len(st.session_state.chat_memory.get_history(st.session_state.document_id))
            st.info(f"💬 **Chat History:** {history_count} interactions")
    
    # Main content
    st.header("📄 Document Upload & Analysis")
    
    uploaded_file = st.file_uploader(
        "Choose a legal document",
        type=['pdf', 'docx', 'doc', 'txt'],
        help="Upload contracts, agreements, or legal documents for comprehensive AI analysis"
    )
    
    if uploaded_file is not None:
        # File info
        col1, col2, col3 = st.columns(3)
        with col1:
            file_size = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.metric("File Size", f"{file_size:.2f} MB")
        with col2:
            st.metric("File Type", uploaded_file.type.split('/')[-1].upper())
        with col3:
            st.metric("Region Focus", country_preference)
        
        # Process document
        if st.button("🚀 Analyze Document with ALL AI Modules", type="primary", use_container_width=True):
            with st.spinner("🔍 Running comprehensive AI analysis..."):
                # Extract text
                text = extract_text_from_file(uploaded_file)
                
                if text:
                    st.session_state.current_document = text
                    st.session_state.document_id = get_document_id(text)
                    
                    # Analyze using ALL modules
                    analysis_results = analyze_document_with_all_modules(text, country_preference)
                    st.session_state.analysis_results = analysis_results
                    
                    st.success("🎉 **Complete AI analysis finished!**")
                    
                    # Display results in tabs
                    tab1, tab2, tab3, tab4, tab5 = st.tabs([
                        "📊 Overview", "🔍 Entities", "⚠️ Risk Analysis", "💬 Q&A Engine", "📝 Feedback"
                    ])
                    
                    with tab1:
                        st.subheader("📋 Document Overview")
                        
                        # Quick stats
                        word_count = len(text.split())
                        char_count = len(text)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Words", f"{word_count:,}")
                        with col2:
                            st.metric("Characters", f"{char_count:,}")
                        with col3:
                            st.metric("Pages (est.)", max(1, word_count // 250))
                        with col4:
                            risk_level = analysis_results.get('risk_assessment', {}).get('risk_level', 'Unknown')
                            st.metric("Risk Level", risk_level)
                        
                        # AI-Generated Summary
                        st.subheader("🤖 AI-Generated Summary")
                        summary = analysis_results.get('summary', 'Summary not available.')
                        st.write(summary)
                        
                        # Entity Summary
                        entity_summary = analysis_results.get('entity_summary', {})
                        if entity_summary:
                            st.subheader("📊 Entity Analysis Summary")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Total Entities", entity_summary.get('total_entities', 0))
                                st.metric("Entity Types", len(entity_summary.get('entity_types', [])))
                            with col2:
                                indian_specific = entity_summary.get('indian_specific', {})
                                if indian_specific.get('currency_found'):
                                    st.success("✅ Indian currency detected")
                                if indian_specific.get('indian_orgs', 0) > 0:
                                    st.success(f"✅ {indian_specific['indian_orgs']} Indian organizations found")
                        
                        # Key clauses
                        clauses = analysis_results.get('clauses', [])
                        if clauses:
                            st.subheader("📋 Key Clauses")
                            for i, clause in enumerate(clauses[:5], 1):
                                st.markdown(f"**{i}.** {clause[:200]}...")
                    
                    with tab2:
                        st.subheader("🔍 Advanced Entity Extraction Results")
                        
                        entities = analysis_results.get('entities', {})
                        
                        if entities:
                            # Display entities by category
                            for entity_type, entity_list in entities.items():
                                if entity_list:
                                    st.markdown(f"**{entity_type.replace('_', ' ').title()}:**")
                                    
                                    # Handle different entity formats
                                    if isinstance(entity_list, list):
                                        if entity_list and hasattr(entity_list[0], 'text'):
                                            # Entity objects with text attribute
                                            for entity in entity_list[:10]:
                                                confidence = getattr(entity, 'confidence', 1.0)
                                                st.markdown(f"• {entity.text} (confidence: {confidence:.2f})")
                                        else:
                                            # Simple string list
                                            for entity in entity_list[:10]:
                                                st.markdown(f"• {entity}")
                                    
                                    st.markdown("")  # Add spacing
                        else:
                            st.info("No entities extracted. This might indicate an issue with the NER module.")
                    
                    with tab3:
                        st.subheader("⚠️ Comprehensive Risk Assessment")
                        
                        risk_assessment = analysis_results.get('risk_assessment', {})
                        
                        # Risk overview
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            risk_score = risk_assessment.get('overall_score', 0)
                            st.metric("Risk Score", f"{risk_score:.1f}/10")
                        with col2:
                            risk_level = risk_assessment.get('risk_level', 'Unknown')
                            st.metric("Risk Level", risk_level)
                        with col3:
                            risk_factors = risk_assessment.get('risk_factors', [])
                            st.metric("Risk Factors", len(risk_factors))
                        
                        # Risk details
                        if risk_factors:
                            st.subheader("🔍 Identified Risk Factors")
                            for i, risk in enumerate(risk_factors[:10], 1):
                                if isinstance(risk, dict):
                                    if 'keyword' in risk:
                                        severity = risk.get('severity', 'Medium')
                                        severity_color = "🔴" if severity == 'High' else "🟡" if severity == 'Medium' else "🟢"
                                        st.markdown(f"{severity_color} **{risk['keyword'].title()}** ({severity})")
                                        if 'context' in risk:
                                            st.markdown(f"   _{risk['context']}_")
                                    elif 'clause' in risk:
                                        risky = risk.get('risky', False)
                                        status = "🔴 High Risk" if risky else "🟢 Low Risk"
                                        st.markdown(f"{status}: {risk['clause'][:100]}...")
                                else:
                                    st.markdown(f"• {risk}")
                        else:
                            st.success("No significant risk factors identified.")
                    
                    with tab4:
                        st.subheader("💬 Advanced Q&A Engine")
                        
                        # Display chat history
                        display_chat_history(st.session_state.document_id)
                        
                        # QA Engine status
                        if analysis_results.get('qa_ready'):
                            st.success("✅ **Q&A Engine is ready!**")
                            
                            # Get suggested questions from QA engine
                            if st.session_state.qa_engine:
                                suggested_questions = st.session_state.qa_engine.get_suggested_questions(country_preference)
                            else:
                                suggested_questions = [
                                    "What is the contract value?",
                                    "Who are the parties involved?",
                                    "When does this contract expire?",
                                    "What are the payment terms?",
                                    "What jurisdiction governs this contract?"
                                ]
                            
                            st.markdown(f"**🎯 Suggested Questions for {country_preference}:**")
                            
                            # Display suggested questions as buttons
                            for question in suggested_questions:
                                if st.button(question, key=f"suggested_{question}"):
                                    ask_question_with_qa_engine(question, country_preference, st.session_state.document_id)
                            
                            # Custom question input
                            st.markdown("**❓ Ask Your Own Question:**")
                            custom_question = st.text_input("Enter your question about the document:")
                            
                            if st.button("Ask Question", disabled=not custom_question):
                                if custom_question:
                                    ask_question_with_qa_engine(custom_question, country_preference, st.session_state.document_id)
                        
                        else:
                            st.error("❌ Q&A Engine not available. Please check module installation.")
                    
                    with tab5:
                        st.subheader("📝 User Feedback System")
                        
                        if MODULES_AVAILABLE and st.session_state.feedback_manager:
                            feedback_collector = FeedbackCollector(st.session_state.feedback_manager)
                            
                            # Overall analysis feedback
                            st.markdown("**Rate the overall analysis:**")
                            feedback_collector.collect_rating_feedback(
                                feature="overall_analysis",
                                ai_output=str(analysis_results),
                                document_name=uploaded_file.name,
                                session_id=str(datetime.now().timestamp())
                            )
                            
                            # Module-specific feedback
                            st.markdown("**Rate specific features:**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Rate Entity Extraction"):
                                    feedback_collector.collect_detailed_feedback(
                                        feature="entity_extraction",
                                        ai_output=str(analysis_results.get('entities', {})),
                                        document_name=uploaded_file.name
                                    )
                            
                            with col2:
                                if st.button("Rate Risk Assessment"):
                                    feedback_collector.collect_detailed_feedback(
                                        feature="risk_assessment",
                                        ai_output=str(analysis_results.get('risk_assessment', {})),
                                        document_name=uploaded_file.name
                                    )
                            
                            # Show feedback statistics
                            if st.checkbox("Show Feedback Statistics"):
                                feedback_collector.show_feedback_stats()
                        
                        else:
                            st.error("❌ Feedback system not available.")
                
                else:
                    st.error("Could not extract text from the document.")
    
    else:
        # Welcome message
        st.info("👆 Upload a legal document to get started with comprehensive AI analysis!")
        
        # Feature showcase
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🤖 **AI Modules**
            - Advanced NER with confidence scores
            - AI-powered document summarization
            - Intelligent Q&A engine
            - Multi-country entity recognition
            - Chat memory for conversations
            """)
        
        with col2:
            st.markdown("""
            ### ⚖️ **Legal Analysis**
            - Comprehensive risk assessment
            - Contract clause extraction
            - Liability analysis
            - Termination risk evaluation
            - Compliance requirement detection
            """)
        
        with col3:
            st.markdown("""
            ### 🌍 **Multi-Country Support**
            - USA, Canada, UK, India, EU
            - Multi-currency detection
            - Country-specific legal entities
            - Jurisdiction analysis
            - Regulatory compliance checks
            """)

if __name__ == "__main__":
    main()
