"""
CompanionMemory — a small wrapper around a local ChromaDB vector store.

Stores every (user message, companion reply) pair as a memory, and can
retrieve the most relevant past memories for a new message. This is what
turns the companion from "stateless chatbot" into something with real
long-term memory across sessions.

No external embedding API needed — ChromaDB's default embedding function
downloads a small local model (all-MiniLM-L6-v2, ~80MB) the first time you
use it, then runs fully offline after that.
"""
import os
import time
import chromadb
from paths import get_persistent_dir

DB_DIR = os.path.join(get_persistent_dir(), "memory_db")


class CompanionMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DB_DIR)
        self.collection = self.client.get_or_create_collection(name="conversations")
        self._counter = self.collection.count()

    def add_memory(self, user_message: str, companion_reply: str):
        """Store one exchange as a searchable memory."""
        combined = f"User said: {user_message}\nCompanion replied: {companion_reply}"
        self._counter += 1
        self.collection.add(
            documents=[combined],
            ids=[f"mem_{self._counter}_{int(time.time())}"],
        )

    def get_relevant_memories(self, query: str, n_results: int = 3):
        """Return the n most relevant past exchanges for this new message.
        Returns an empty list if there's no memory yet (first run)."""
        if self.collection.count() == 0:
            return []
        n = min(n_results, self.collection.count())
        results = self.collection.query(query_texts=[query], n_results=n)
        return results["documents"][0] if results["documents"] else []
