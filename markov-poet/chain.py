"""Markov chain builder and generator."""

import random


def build_chain(tokens: list[str], order: int) -> dict:
    """Build a Markov chain from a token list.

    Returns {tuple_of_state_words: {next_word: count}}.
    """
    if order < 1 or order > 5:
        raise ValueError("Order must be between 1 and 5")
    if len(tokens) <= order:
        return {}

    chain: dict[tuple, dict[str, int]] = {}
    for i in range(len(tokens) - order):
        state = tuple(tokens[i:i + order])
        next_word = tokens[i + order]
        if state not in chain:
            chain[state] = {}
        chain[state][next_word] = chain[state].get(next_word, 0) + 1

    return chain


def _weighted_choice(transitions: dict[str, int]) -> str:
    words = list(transitions.keys())
    weights = list(transitions.values())
    return random.choices(words, weights=weights, k=1)[0]


def _find_seed_state(chain: dict, order: int, seed: str | None) -> tuple:
    if not chain:
        raise RuntimeError("Chain is empty — add texts to the corpus first")

    if seed:
        seed_lower = seed.lower()
        candidates = [s for s in chain if s[0] == seed_lower]
        if candidates:
            return random.choice(candidates)

    return random.choice(list(chain.keys()))


def generate(chain: dict, order: int, length: int, seed: str | None = None) -> list[str]:
    """Weighted random walk through the chain, producing `length` words."""
    if not chain:
        raise RuntimeError("Chain is empty — add texts to the corpus first")

    state = _find_seed_state(chain, order, seed)
    output = list(state)

    for _ in range(length - order):
        transitions = chain.get(state)
        if not transitions:
            state = random.choice(list(chain.keys()))
            transitions = chain[state]

        next_word = _weighted_choice(transitions)
        output.append(next_word)
        state = tuple(output[-order:])

    return output


def generate_sentence(chain: dict, order: int, max_words: int = 50) -> str:
    """Generate words until sentence-ending punctuation or max_words reached."""
    if not chain:
        raise RuntimeError("Chain is empty — add texts to the corpus first")

    state = _find_seed_state(chain, order, None)
    output = list(state)

    for _ in range(max_words - order):
        transitions = chain.get(state)
        if not transitions:
            state = random.choice(list(chain.keys()))
            transitions = chain[state]

        next_word = _weighted_choice(transitions)
        output.append(next_word)

        if next_word and next_word[-1] in '.!?':
            break

        state = tuple(output[-order:])

    result = ' '.join(output)
    return result[0].upper() + result[1:] if result else ''
