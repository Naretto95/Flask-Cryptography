#!/usr/bin/env python3
"""Caesar and Vigenere cipher cryptanalysis toolkit.

An interactive command-line tool for breaking classic substitution
ciphers: brute-forcing a Caesar shift, recovering a Caesar shift via
letter-frequency analysis, and recovering a Vigenere key (by brute
force over key lengths, or for a known key length) using the same
frequency-analysis technique on each key position independently.

Originally written by Lilian Naretto and Corentin Javaud.
"""
from __future__ import annotations

import string

ALPHABET = string.ascii_uppercase
ALPHABET_SIZE = len(ALPHABET)

# Reference letter frequencies (per mille) used to score a decryption
# candidate against natural-language text. Only the peaks that matter
# for scoring are populated (E and A dominate both French and English);
# every other letter is left at zero. This is a lightweight heuristic,
# not a complete frequency table.
FRENCH_FREQUENCIES = (
    900, 0, 0, 0, 1500, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
)
ENGLISH_FREQUENCIES = (
    900, 0, 0, 0, 1500, 0, 0, 0, 800, 0, 0, 300, 300,
    700, 500, 0, 0, 0, 700, 600, 200, 0, 0, 0, 0, 0,
)


def caesar_shift(text: str, shift: int) -> str:
    """Shift every letter in `text` forward by `shift` positions in the
    alphabet (a negative shift moves backward). Non-letters pass through
    unchanged."""
    text = text.upper()
    return "".join(
        ALPHABET[(ALPHABET.index(char) + shift) % ALPHABET_SIZE] if char in ALPHABET else char
        for char in text
    )


def letter_frequencies(text: str) -> list[float]:
    """Return the relative frequency of each letter A-Z in `text`."""
    counts = [0] * ALPHABET_SIZE
    for char in text:
        if char in ALPHABET:
            counts[ALPHABET.index(char)] += 1
    total = sum(counts) or 1
    return [count / total for count in counts]


def best_caesar_shift(ciphertext: str, reference_frequencies: tuple[int, ...]) -> int:
    """Find the Caesar shift that, when applied to `ciphertext`, best
    matches `reference_frequencies` (highest dot-product score). The
    returned shift can be passed straight to `caesar_shift` to decrypt."""
    scores = []
    for shift in range(ALPHABET_SIZE):
        candidate_frequencies = letter_frequencies(caesar_shift(ciphertext, shift))
        score = sum(freq * ref for freq, ref in zip(candidate_frequencies, reference_frequencies))
        scores.append(score)
    return scores.index(max(scores))


def caesar_brute_force(ciphertext: str) -> None:
    """Print every possible Caesar shift so a human can pick the one that
    reads as plaintext."""
    for shift in range(ALPHABET_SIZE):
        print(f"shift = {shift:>2}  {caesar_shift(ciphertext, shift)}")


def caesar_frequency_analysis(ciphertext: str, reference_frequencies: tuple[int, ...] = FRENCH_FREQUENCIES) -> None:
    """Guess the Caesar shift via frequency analysis and print the result."""
    shift = best_caesar_shift(ciphertext, reference_frequencies)
    print(f"shift = {shift}  plaintext = {caesar_shift(ciphertext, shift)}")


def vigenere_key_from_length(
    ciphertext: str,
    key_length: int,
    reference_frequencies: tuple[int, ...] = ENGLISH_FREQUENCIES,
) -> str:
    """Recover a Vigenere key of a known length. Each key position behaves
    like an independent Caesar cipher across the letters it encrypted, so
    every column `ciphertext[offset::key_length]` is solved on its own via
    frequency analysis."""
    key_chars = []
    for offset in range(key_length):
        column = ciphertext[offset::key_length]
        decrypt_shift = best_caesar_shift(column, reference_frequencies)
        encrypt_shift = (ALPHABET_SIZE - decrypt_shift) % ALPHABET_SIZE
        key_chars.append(ALPHABET[encrypt_shift])
    return "".join(key_chars)


def vigenere_decrypt(ciphertext: str, key: str) -> str:
    """Decrypt a Vigenere ciphertext with a known key. Non-letters pass
    through unchanged and don't consume a key position."""
    key = key.upper()
    ciphertext = ciphertext.upper()
    decrypted_chars = []
    key_index = 0
    for char in ciphertext:
        if char not in ALPHABET:
            decrypted_chars.append(char)
            continue
        key_shift = ALPHABET.index(key[key_index % len(key)])
        decrypted_chars.append(ALPHABET[(ALPHABET.index(char) - key_shift) % ALPHABET_SIZE])
        key_index += 1
    return "".join(decrypted_chars)


def main() -> None:
    ciphertext = input("Phrase to decrypt: ").replace(" ", "")
    print(
        "1) Caesar brute force\n"
        "2) Caesar frequency analysis\n"
        "3) Vigenere brute force (unknown key length, tries 1-20)\n"
        "4) Vigenere with a known key length"
    )
    choice = input("Method: ").strip()

    if choice == "1":
        caesar_brute_force(ciphertext)
    elif choice == "2":
        caesar_frequency_analysis(ciphertext)
    elif choice == "3":
        for key_length in range(1, 21):
            key = vigenere_key_from_length(ciphertext, key_length)
            print(f"key length = {key_length:>2}  key = {key}  plaintext = {vigenere_decrypt(ciphertext, key)}")
    elif choice == "4":
        key_length = int(input("Key length: "))
        key = vigenere_key_from_length(ciphertext, key_length)
        print(f"key = {key}  plaintext = {vigenere_decrypt(ciphertext, key)}")
    else:
        print(f"Unknown option: {choice!r}")


if __name__ == "__main__":
    main()
