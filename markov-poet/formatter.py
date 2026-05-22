"""Output formatting — prose, poetry, and haiku modes."""

import random
import textwrap


def count_syllables(word: str) -> int:
    """Vowel-group heuristic for syllable counting."""
    word = word.lower().strip(".,!?;:'\"()-")
    if not word:
        return 0

    vowels = "aeiouy"
    count = 0
    prev_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel

    if word.endswith('e') and count > 1:
        count -= 1
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        count += 1

    return max(1, count)


def format_prose(words: list[str], width: int = 72) -> str:
    """Wrap to width and capitalize sentence starts."""
    if not words:
        return ''

    text = ' '.join(words)
    sentences = []
    current = []

    for word in text.split():
        current.append(word)
        if word and word[-1] in '.!?':
            sentence = ' '.join(current)
            sentences.append(sentence[0].upper() + sentence[1:] if sentence else '')
            current = []

    if current:
        sentence = ' '.join(current)
        sentences.append(sentence[0].upper() + sentence[1:] if sentence else '')

    full_text = ' '.join(sentences)
    return textwrap.fill(full_text, width=width)


def format_poetry(words: list[str], lines_per_stanza: int = 4,
                  words_per_line: tuple[int, int] = (4, 8)) -> str:
    """Format words into poetry with random line lengths and stanza breaks."""
    if not words:
        return ''

    lines = []
    i = 0
    while i < len(words):
        line_len = random.randint(words_per_line[0], words_per_line[1])
        line_words = words[i:i + line_len]
        line = ' '.join(line_words)
        if line:
            lines.append(line[0].upper() + line[1:])
        i += line_len

    stanzas = []
    for j in range(0, len(lines), lines_per_stanza):
        stanza = '\n'.join(lines[j:j + lines_per_stanza])
        stanzas.append(stanza)

    return '\n\n'.join(stanzas)


def format_haiku(chain: dict, order: int) -> str:
    """Attempt a 5-7-5 syllable haiku using the chain."""
    target_syllables = [5, 7, 5]
    lines = []

    for target in target_syllables:
        best_line = _build_syllable_line(chain, order, target)
        lines.append(best_line)

    return '\n'.join(lines)


def _build_syllable_line(chain: dict, order: int, target: int) -> str:
    from chain import generate

    best = None
    best_diff = float('inf')

    for _ in range(20):
        words = generate(chain, order, length=10)
        line_words = []
        syllable_count = 0

        for w in words:
            s = count_syllables(w)
            if syllable_count + s <= target + 1:
                line_words.append(w)
                syllable_count += s
                if syllable_count >= target:
                    break

        diff = abs(syllable_count - target)
        if diff < best_diff:
            best_diff = diff
            best = ' '.join(line_words)
            if diff == 0:
                break

    result = best or ' '.join(generate(chain, order, length=3))
    return result[0].upper() + result[1:] if result else ''
