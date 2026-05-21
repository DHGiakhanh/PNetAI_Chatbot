from dataclasses import dataclass

@dataclass
class User:
    id: str
    is_authenticated: bool = False
