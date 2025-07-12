from typing import List, Dict

class ChatMemory:
    def __init__(self):
        # { "doc_id_1": [ {q:..., a:...}, ... ], "doc_id_2": [...] }
        self.memory = {}

    def add_interaction(self, doc_id: str, question: str, answer: str):
        if doc_id not in self.memory:
            self.memory[doc_id] = []
        self.memory[doc_id].append({
            "question": question,
            "answer": answer
        })

    def get_history(self, doc_id: str) -> List[Dict]:
        return self.memory.get(doc_id, [])

    def clear_history(self, doc_id: str):
        if doc_id in self.memory:
            del self.memory[doc_id]
