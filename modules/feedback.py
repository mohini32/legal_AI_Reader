"""
User Feedback System for Legal AI Document Reader
Collects and processes user feedback to improve AI performance
"""
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Feedback:
    """Feedback data structure"""
    id: Optional[int] = None
    timestamp: str = ""
    document_name: str = ""
    feature: str = ""  # 'entity_extraction', 'risk_detection', 'qa_system', 'summarization'
    rating: int = 0  # 1-5 scale
    comment: str = ""
    suggestion: str = ""
    user_correction: str = ""
    ai_output: str = ""
    expected_output: str = ""
    session_id: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class FeedbackManager:
    """Manages user feedback collection and analysis"""
    
    def __init__(self, db_path: str = "data/feedback.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for feedback storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                document_name TEXT,
                feature TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                suggestion TEXT,
                user_correction TEXT,
                ai_output TEXT,
                expected_output TEXT,
                session_id TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_feedback(self, feedback: Feedback) -> int:
        """Add feedback to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO feedback (
                timestamp, document_name, feature, rating, comment,
                suggestion, user_correction, ai_output, expected_output, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            feedback.timestamp, feedback.document_name, feedback.feature,
            feedback.rating, feedback.comment, feedback.suggestion,
            feedback.user_correction, feedback.ai_output, feedback.expected_output,
            feedback.session_id
        ))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return feedback_id
    
    def get_feedback(self, feature: Optional[str] = None, 
                    min_rating: Optional[int] = None,
                    limit: Optional[int] = None) -> List[Feedback]:
        """Retrieve feedback from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM feedback WHERE 1=1"
        params = []
        
        if feature:
            query += " AND feature = ?"
            params.append(feature)
        
        if min_rating:
            query += " AND rating >= ?"
            params.append(min_rating)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        feedback_list = []
        for row in rows:
            feedback = Feedback(
                id=row[0], timestamp=row[1], document_name=row[2],
                feature=row[3], rating=row[4], comment=row[5],
                suggestion=row[6], user_correction=row[7], ai_output=row[8],
                expected_output=row[9], session_id=row[10]
            )
            feedback_list.append(feedback)
        
        return feedback_list
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute("SELECT COUNT(*), AVG(rating) FROM feedback")
        total_feedback, avg_rating = cursor.fetchone()
        
        # Stats by feature
        cursor.execute('''
            SELECT feature, COUNT(*), AVG(rating), MIN(rating), MAX(rating)
            FROM feedback GROUP BY feature
        ''')
        feature_stats = {}
        for row in cursor.fetchall():
            feature_stats[row[0]] = {
                'count': row[1],
                'avg_rating': round(row[2], 2) if row[2] else 0,
                'min_rating': row[3],
                'max_rating': row[4]
            }
        
        # Recent feedback trends
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*), AVG(rating)
            FROM feedback
            WHERE timestamp >= datetime('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        ''')
        recent_trends = []
        for row in cursor.fetchall():
            recent_trends.append({
                'date': row[0],
                'count': row[1],
                'avg_rating': round(row[2], 2) if row[2] else 0
            })
        
        conn.close()
        
        return {
            'total_feedback': total_feedback or 0,
            'average_rating': round(avg_rating, 2) if avg_rating else 0,
            'feature_stats': feature_stats,
            'recent_trends': recent_trends
        }
    
    def get_improvement_suggestions(self) -> Dict[str, List[str]]:
        """Get improvement suggestions from user feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get suggestions for low-rated feedback
        cursor.execute('''
            SELECT feature, suggestion, user_correction
            FROM feedback
            WHERE rating <= 3 AND (suggestion != '' OR user_correction != '')
        ''')
        
        suggestions = {}
        for row in cursor.fetchall():
            feature = row[0]
            if feature not in suggestions:
                suggestions[feature] = []
            
            if row[1]:  # suggestion
                suggestions[feature].append(f"Suggestion: {row[1]}")
            if row[2]:  # user_correction
                suggestions[feature].append(f"Correction: {row[2]}")
        
        conn.close()
        return suggestions
    
    def export_feedback(self, filepath: str, format: str = 'json'):
        """Export feedback data"""
        feedback_list = self.get_feedback()
        
        if format.lower() == 'json':
            data = [asdict(fb) for fb in feedback_list]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == 'csv':
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if feedback_list:
                    writer = csv.DictWriter(f, fieldnames=asdict(feedback_list[0]).keys())
                    writer.writeheader()
                    for fb in feedback_list:
                        writer.writerow(asdict(fb))

class FeedbackCollector:
    """Streamlit UI components for collecting feedback"""
    
    def __init__(self, feedback_manager: FeedbackManager):
        self.feedback_manager = feedback_manager
    
    def collect_rating_feedback(self, feature: str, ai_output: str = "", 
                              document_name: str = "", session_id: str = ""):
        """Collect simple rating feedback"""
        import streamlit as st
        
        st.subheader(f"📝 Rate {feature.replace('_', ' ').title()}")
        
        rating = st.slider(
            "How would you rate this feature?",
            min_value=1, max_value=5, value=3,
            help="1 = Very Poor, 5 = Excellent"
        )
        
        comment = st.text_area(
            "Comments (optional):",
            placeholder="Tell us what you think..."
        )
        
        if st.button(f"Submit Rating for {feature.replace('_', ' ').title()}"):
            feedback = Feedback(
                document_name=document_name,
                feature=feature,
                rating=rating,
                comment=comment,
                ai_output=ai_output,
                session_id=session_id
            )
            
            feedback_id = self.feedback_manager.add_feedback(feedback)
            st.success(f"Thank you for your feedback! (ID: {feedback_id})")
            return feedback_id
        
        return None
    
    def collect_detailed_feedback(self, feature: str, ai_output: str = "",
                                document_name: str = "", session_id: str = ""):
        """Collect detailed feedback with corrections"""
        import streamlit as st
        
        st.subheader(f"📝 Detailed Feedback for {feature.replace('_', ' ').title()}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            rating = st.slider(
                "Overall Rating:",
                min_value=1, max_value=5, value=3,
                help="1 = Very Poor, 5 = Excellent"
            )
            
            comment = st.text_area(
                "What did you like or dislike?",
                placeholder="Your thoughts on the AI's performance..."
            )
        
        with col2:
            suggestion = st.text_area(
                "Suggestions for improvement:",
                placeholder="How can we make this better?"
            )
            
            user_correction = st.text_area(
                "Correct output (if AI was wrong):",
                placeholder="What should the correct result be?"
            )
        
        if st.button(f"Submit Detailed Feedback for {feature.replace('_', ' ').title()}"):
            feedback = Feedback(
                document_name=document_name,
                feature=feature,
                rating=rating,
                comment=comment,
                suggestion=suggestion,
                user_correction=user_correction,
                ai_output=ai_output,
                session_id=session_id
            )
            
            feedback_id = self.feedback_manager.add_feedback(feedback)
            st.success(f"Thank you for your detailed feedback! (ID: {feedback_id})")
            return feedback_id
        
        return None
    
    def show_feedback_stats(self):
        """Display feedback statistics"""
        import streamlit as st
        
        stats = self.feedback_manager.get_feedback_stats()
        
        st.subheader("📊 Feedback Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Feedback", stats['total_feedback'])
        with col2:
            st.metric("Average Rating", f"{stats['average_rating']}/5")
        with col3:
            improvement_suggestions = self.feedback_manager.get_improvement_suggestions()
            st.metric("Features with Suggestions", len(improvement_suggestions))
        
        # Feature-wise stats
        if stats['feature_stats']:
            st.subheader("📈 Feature Performance")
            
            feature_df = []
            for feature, feature_stat in stats['feature_stats'].items():
                feature_df.append({
                    'Feature': feature.replace('_', ' ').title(),
                    'Feedback Count': feature_stat['count'],
                    'Average Rating': feature_stat['avg_rating'],
                    'Min Rating': feature_stat['min_rating'],
                    'Max Rating': feature_stat['max_rating']
                })
            
            import pandas as pd
            df = pd.DataFrame(feature_df)
            st.dataframe(df, use_container_width=True)
        
        # Recent trends
        if stats['recent_trends']:
            st.subheader("📅 Recent Feedback Trends")
            
            import pandas as pd
            trends_df = pd.DataFrame(stats['recent_trends'])
            st.line_chart(trends_df.set_index('date')['avg_rating'])

# Convenience functions
def quick_feedback(feature: str, rating: int, comment: str = "", 
                  document_name: str = "", session_id: str = ""):
    """Quick way to add feedback"""
    feedback_manager = FeedbackManager()
    feedback = Feedback(
        document_name=document_name,
        feature=feature,
        rating=rating,
        comment=comment,
        session_id=session_id
    )
    return feedback_manager.add_feedback(feedback)

def get_feature_rating(feature: str) -> float:
    """Get average rating for a feature"""
    feedback_manager = FeedbackManager()
    stats = feedback_manager.get_feedback_stats()
    
    if feature in stats['feature_stats']:
        return stats['feature_stats'][feature]['avg_rating']
    return 0.0
