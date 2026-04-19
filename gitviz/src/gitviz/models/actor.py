"""Actor represents a person (author or committer) in git."""

from dataclasses import dataclass


@dataclass
class Actor:
    """Represents a person in git."""

    name: str
    email: str

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"

    def matches(self, query: str) -> bool:
        q = query.lower()
        return q in self.name.lower() or q in self.email.lower()
