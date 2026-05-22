"""Text tokenization and normalization."""

import re


_SENTENCE_END = re.compile(r'(?<=[.!?])\s+')
_WORD_SPLIT = re.compile(r'\s+')
_EM_DASH = re.compile(r'—')


def tokenize(text: str) -> list[str]:
    """Split text on whitespace, preserve punctuation attached to words, lowercase."""
    text = _EM_DASH.sub(' ', text)
    tokens = _WORD_SPLIT.split(text.strip().lower())
    return [t for t in tokens if t]


def sentence_split(text: str) -> list[list[str]]:
    """Split into sentences on .!? then tokenize each."""
    text = _EM_DASH.sub(' ', text)
    raw_sentences = _SENTENCE_END.split(text.strip())
    sentences = []
    for s in raw_sentences:
        tokens = tokenize(s)
        if tokens:
            sentences.append(tokens)
    return sentences
