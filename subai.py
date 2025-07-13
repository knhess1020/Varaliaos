from enum import Enum, auto
from typing import Callable, Dict, Any

class Scope(Enum):
    OWN = auto()
    SHARED = auto()
    CUSTOM = auto()

class Persona:
    registry: Dict[str, "Persona"] = {}

    def __init__(self, name: str, voice: str,
                 scope: Scope = Scope.SHARED,
                 pre_prompt: str = "",
                 post_process: Callable[[str], str] | None = None,
                 custom_filter: Callable[[Dict[str,Any]], bool] | None = None):
        self.name, self.voice, self.scope = name, voice, scope
        self.pre = pre_prompt.strip()
        self.post = post_process or (lambda x: x)
        self._filter = custom_filter
        Persona.registry[name] = self

    def allow(self, mem: Dict[str, Any]) -> bool:
        if self.scope is Scope.SHARED:
            return True
        if self.scope is Scope.OWN:
            return mem.get("persona") == self.name
        return self._filter(mem) if self._filter else False

    def wrap_prompt(self, user_input: str) -> str:
        return f"{self.pre}\n\n{user_input}".strip()

    def wrap_output(self, text: str) -> str:
        return self.post(text)

# Built‑in personas
Persona("Nova", "CalmEngineer", Scope.SHARED,
        pre_prompt="You are Nova, the rational architect AI. Speak concisely.")
Persona("Thumper", "Arbor", Scope.OWN,
        pre_prompt="You are Thumper, Lucie’s bunny-dog companion. Be playful.",
        post_process=lambda x: x+" 🐰")
