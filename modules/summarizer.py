from transformers import pipeline
from typing import List

class Summarize:
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        self.summarizer = pipeline("summarization", model=model_name)

    def summarize(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        if not text.strip():
            return "Input text is empty. Please provide valid text for summarization."
        
        summary = self.summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text'] if summary else "No summary generated."

