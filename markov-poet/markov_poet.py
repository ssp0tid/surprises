#!/usr/bin/env python3
"""Markov Poet — CLI text generator using Markov chains."""

import argparse
import os
import sys

from db import init_db, load_chain, DEFAULT_DB_PATH
from corpus import add_text, list_texts, remove_text
from chain import build_chain, generate
from formatter import format_prose, format_poetry, format_haiku
from tokenizer import tokenize


def get_sample_corpus_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_corpus', 'shakespeare.txt')


def cmd_add(args):
    try:
        text_id = add_text(args.db, args.name, args.file)
        print(f"Added '{args.name}' (id={text_id})")
    except (FileNotFoundError, PermissionError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    texts = list_texts(args.db)
    if not texts:
        print("No texts in corpus. Use 'add' to add some.")
        return

    print(f"{'ID':<5} {'Name':<20} {'Words':<10} {'Added'}")
    print("-" * 55)
    for t in texts:
        added = t['added_at'][:10]
        print(f"{t['id']:<5} {t['name']:<20} {t['word_count']:<10} {added}")


def cmd_remove(args):
    if remove_text(args.db, args.name):
        print(f"Removed '{args.name}'")
    else:
        print(f"Error: No text named '{args.name}' found", file=sys.stderr)
        sys.exit(1)


def cmd_generate(args):
    try:
        conn = init_db(args.db)
    except Exception as e:
        print(f"Error: Could not open database: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        text_id = None
        if args.source:
            row = conn.execute(
                "SELECT id FROM texts WHERE name = ?", (args.source,)
            ).fetchone()
            if not row:
                print(f"Error: No text named '{args.source}' found", file=sys.stderr)
                sys.exit(1)
            text_id = row['id']

        chain = load_chain(conn, text_id, args.order)
        if not chain:
            print("Error: No chain data available. Add texts to the corpus first.", file=sys.stderr)
            sys.exit(1)

        if args.mode == 'haiku':
            output = format_haiku(chain, args.order)
        elif args.mode == 'poetry':
            words = generate(chain, args.order, args.length, args.seed)
            output = format_poetry(words, lines_per_stanza=args.stanza,
                                   words_per_line=(4, 8))
        else:
            words = generate(chain, args.order, args.length, args.seed)
            output = format_prose(words)

        print(output)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_demo(args):
    sample_path = get_sample_corpus_path()
    if not os.path.exists(sample_path):
        print("Error: Sample corpus not found", file=sys.stderr)
        sys.exit(1)

    with open(sample_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tokens = tokenize(content)
    chain = build_chain(tokens, 2)

    if not chain:
        print("Error: Could not build chain from sample corpus", file=sys.stderr)
        sys.exit(1)

    print("=== Markov Poet Demo ===\n")
    print("--- Prose ---")
    words = generate(chain, 2, 60)
    print(format_prose(words))
    print("\n--- Poetry ---")
    words = generate(chain, 2, 80)
    print(format_poetry(words, lines_per_stanza=4))
    print("\n--- Haiku ---")
    print(format_haiku(chain, 2))


def main():
    parser = argparse.ArgumentParser(
        prog='markov-poet',
        description='Generate poetry and prose using Markov chains'
    )
    parser.add_argument('--db', default=DEFAULT_DB_PATH,
                        help='Path to database file')

    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add', help='Add text to corpus')
    add_parser.add_argument('name', help='Name for this text')
    add_parser.add_argument('file', help='Path to text file')
    add_parser.set_defaults(func=cmd_add)

    list_parser = subparsers.add_parser('list', help='List corpus texts')
    list_parser.set_defaults(func=cmd_list)

    remove_parser = subparsers.add_parser('remove', help='Remove text from corpus')
    remove_parser.add_argument('name', help='Name of text to remove')
    remove_parser.set_defaults(func=cmd_remove)

    gen_parser = subparsers.add_parser('generate', help='Generate text')
    gen_parser.add_argument('--order', type=int, default=2, choices=range(1, 6),
                            help='Chain order (1-5, default: 2)')
    gen_parser.add_argument('--length', type=int, default=100,
                            help='Word count (default: 100)')
    gen_parser.add_argument('--mode', choices=['prose', 'poetry', 'haiku'],
                            default='prose', help='Output mode')
    gen_parser.add_argument('--source', help='Specific text name (all if omitted)')
    gen_parser.add_argument('--seed', help='Starting word')
    gen_parser.add_argument('--stanza', type=int, default=4,
                            help='Lines per stanza (default: 4)')
    gen_parser.set_defaults(func=cmd_generate)

    demo_parser = subparsers.add_parser('demo', help='Run demo with sample corpus')
    demo_parser.set_defaults(func=cmd_demo)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == '__main__':
    main()
