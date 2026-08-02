"""
CompanionBrain — wraps the Groq chat completion API and turns replies into
(text, mood) pairs so the UI knows which sprite/animation to show.

Reads the companion's name and personality from settings.json (editable via
the Settings window), and uses RAG-based long-term memory via CompanionMemory
so it can recall things across sessions, not just within one chat.
"""
import os
from dotenv import load_dotenv
from groq import Groq

from memory import CompanionMemory
from settings import load_settings
from paths import get_persistent_dir

load_dotenv(os.path.join(get_persistent_dir(), ".env"))

VALID_MOODS = {"happy", "neutral", "thinking", "sleepy"}


def build_system_prompt():
    settings = load_settings()
    name = settings.get("companion_name", "Companion")
    personality = settings.get("personality", "").strip()

    prompt = f"""You are {name}, a small, friendly desktop companion character who lives on the
user's screen and chats with them while they work. Keep replies short (1-3 sentences),
warm, and a little playful. Never break character.
"""
    if personality:
        prompt += f"\nPersonality notes: {personality}\n"

    prompt += """
You may be given "Relevant past memories" below the user's message - these are real
things the user told you before, possibly in an earlier session. Use them naturally if
they're relevant (e.g. following up on something), but don't force it if they aren't
relevant to the current message.

After your reply, on a new line, output exactly one mood tag from this list:
happy, neutral, thinking, sleepy

Format your response exactly like this:
<reply text>
MOOD: <tag>
"""
    return prompt


class CompanionBrain:
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = model
        self.history = [{"role": "system", "content": build_system_prompt()}]
        self.memory = CompanionMemory()

    def chat(self, user_message: str):
        if self.client is None:
            return "I need a GROQ_API_KEY in your .env file before I can think!", "neutral"

        relevant = self.memory.get_relevant_memories(user_message, n_results=3)
        if relevant:
            memory_block = "\n\n".join(relevant)
            augmented_message = f"{user_message}\n\n[Relevant past memories:]\n{memory_block}"
        else:
            augmented_message = user_message

        self.history.append({"role": "user", "content": augmented_message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            temperature=0.8,
            max_tokens=150,
        )
        raw = response.choices[0].message.content.strip()
        self.history.append({"role": "assistant", "content": raw})

        reply, mood = raw, "neutral"
        if "MOOD:" in raw:
            reply_part, mood_part = raw.rsplit("MOOD:", 1)
            reply = reply_part.strip()
            candidate = mood_part.strip().lower()
            mood = candidate if candidate in VALID_MOODS else "neutral"

        self.memory.add_memory(user_message, reply)

        if len(self.history) > 12:
            self.history = [self.history[0]] + self.history[-10:]

        return reply, mood

    def proactive_nudge(self, set_state_callback):
        set_state_callback("idle")
