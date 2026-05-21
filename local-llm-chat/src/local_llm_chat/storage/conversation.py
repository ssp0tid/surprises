import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Conversation:
    id: str
    model: str
    system_prompt: str
    created_at: str
    updated_at: str
    messages: list[Message]


def _get_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_conv_filename(conv_id: str) -> str:
    return f"{conv_id}.json"


def new_conversation(model: str, system_prompt: str) -> Conversation:
    now = datetime.now(timezone.utc)
    conv_id = f"conv_{now.strftime('%Y%m%d_%H%M%S')}"
    timestamp = now.isoformat()

    return Conversation(
        id=conv_id,
        model=model,
        system_prompt=system_prompt,
        created_at=timestamp,
        updated_at=timestamp,
        messages=[],
    )


def save_conversation(conv: Conversation, save_dir: str) -> None:
    os.makedirs(save_dir, exist_ok=True)

    conv.updated_at = _get_timestamp()

    filepath = os.path.join(save_dir, _get_conv_filename(conv.id))

    data = {
        "id": conv.id,
        "model": conv.model,
        "system_prompt": conv.system_prompt,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": [asdict(msg) for msg in conv.messages],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_conversation(conv_id: str, save_dir: str) -> Conversation:
    filepath = os.path.join(save_dir, _get_conv_filename(conv_id))

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    messages = [Message(**msg_data) for msg_data in data.get("messages", [])]

    return Conversation(
        id=data["id"],
        model=data["model"],
        system_prompt=data["system_prompt"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        messages=messages,
    )


def delete_conversation(conv_id: str, save_dir: str) -> None:
    filepath = os.path.join(save_dir, _get_conv_filename(conv_id))
    os.remove(filepath)


def list_conversations(save_dir: str) -> list[Conversation]:
    if not os.path.isdir(save_dir):
        return []

    conversations = []

    for filename in os.listdir(save_dir):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(save_dir, filename)

        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            conv = Conversation(
                id=data["id"],
                model=data["model"],
                system_prompt="",
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                messages=[],
            )
            conversations.append(conv)
        except (json.JSONDecodeError, KeyError, OSError):
            continue

    conversations.sort(key=lambda c: c.updated_at, reverse=True)

    return conversations
