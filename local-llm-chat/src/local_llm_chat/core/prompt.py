"""Prompt building module for Local LLM Chat."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from jinja2 import Environment, BaseLoader


class MessageRole(Enum):
    """Message role enumeration."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """A chat message."""

    role: MessageRole
    content: str


class PromptBuilder:
    """Builds prompts for LLM inference from conversation history."""

    DEFAULT_TEMPLATE = "{% for msg in messages %}{% if msg.role == 'system' %}{{ msg.content }}\n\n{% elif msg.role == 'user' %}User: {{ msg.content }}\n\n{% elif msg.role == 'assistant' %}Assistant: {{ msg.content }}\n\n{% endif %}{% endfor %}Assistant:"

    def __init__(
        self,
        system_prompt: str = "You are a helpful AI assistant.",
        template: Optional[str] = None,
    ) -> None:
        """Initialize the prompt builder.

        Args:
            system_prompt: The system prompt to use.
            template: Custom Jinja2 template for prompt formatting.
        """
        self._system_prompt = system_prompt
        self._template = template or self.DEFAULT_TEMPLATE
        self._jinja = Environment(loader=BaseLoader())

    def build(self, messages: list[Message]) -> str:
        """Build a prompt string from messages.

        Args:
            messages: List of conversation messages.

        Returns:
            str: Formatted prompt string.
        """
        all_messages = [Message(role=MessageRole.SYSTEM, content=self._system_prompt)]
        all_messages.extend(messages)
        return self._render(all_messages)

    def _render(self, messages: list[Message]) -> str:
        """Render messages using the Jinja2 template.

        Args:
            messages: List of messages to render.

        Returns:
            str: Rendered prompt string.
        """
        template = self._jinja.from_string(self._template)
        return template.render(
            messages=[{"role": msg.role.value, "content": msg.content} for msg in messages]
        )

    def add_message(
        self, messages: list[Message], role: MessageRole, content: str
    ) -> list[Message]:
        """Add a message to the conversation.

        Args:
            messages: Current message list.
            role: Role of the message.
            content: Content of the message.

        Returns:
            list[Message]: Updated message list.
        """
        return messages + [Message(role=role, content=content)]

    def get_system_prompt(self) -> str:
        """Return the current system prompt."""
        return self._system_prompt

    def set_system_prompt(self, system_prompt: str) -> None:
        """Update the system prompt.

        Args:
            system_prompt: New system prompt.
        """
        self._system_prompt = system_prompt
