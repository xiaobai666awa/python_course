"""Shared helpers for normalizing and judging choice questions."""

from __future__ import annotations

import re
from string import ascii_uppercase
from typing import Dict, List, Optional, Set

from pojo.Problem import Problem, ProblemType

_CHOICE_ALIASES = {"choice", "选择题"}
_CHOICE_SPLIT_PATTERN = re.compile(r"[\n\r,，、|；;\/]+")
_OPTION_PREFIX_PATTERN = re.compile(r"^\s*([A-Za-z])\s*(?:[.)、:：-]|[)）])?\s*")


def is_choice_problem(problem: Problem) -> bool:
    """Return True if the given problem represents a choice question."""
    problem_type = getattr(problem, "type", None)
    if isinstance(problem_type, ProblemType):
        return problem_type == ProblemType.CHOICE
    if problem_type is None:
        return False
    return str(problem_type).strip().lower() in _CHOICE_ALIASES


def normalize_choice_answer(answer: Optional[str], options: Optional[List[str]] = None) -> Optional[str]:
    """Normalize raw answer text to sorted letter string such as "BC"."""
    if answer is None:
        return None
    normalized_text = str(answer).strip()
    if not normalized_text:
        return None

    tokens = _split_choice_tokens(normalized_text)
    valid_labels = _build_valid_labels(options)
    option_text_map = _build_option_text_map(options)

    letters: List[str] = []
    for token in tokens:
        extracted = _extract_letters_from_token(token, valid_labels)
        if extracted:
            letters.extend(extracted)
            continue

        lowered = token.lower()
        mapped = option_text_map.get(lowered)
        if mapped:
            letters.append(mapped)
            continue

        stripped = _strip_option_prefix(token)
        if stripped:
            mapped = option_text_map.get(stripped.lower())
            if mapped:
                letters.append(mapped)

    if not letters:
        return None

    filtered = [letter for letter in letters if not valid_labels or letter in valid_labels]
    if not filtered:
        return None

    return "".join(sorted(dict.fromkeys(filtered)))


def _split_choice_tokens(value: str) -> List[str]:
    parts = _CHOICE_SPLIT_PATTERN.split(value)
    tokens = [part.strip() for part in parts if part and part.strip()]
    return tokens or [value.strip()]


def _build_valid_labels(options: Optional[List[str]]) -> Set[str]:
    if not options:
        return set(ascii_uppercase)
    count = min(len(options), len(ascii_uppercase))
    return {chr(ord("A") + idx) for idx in range(count)}


def _build_option_text_map(options: Optional[List[str]]) -> Dict[str, str]:
    if not options:
        return {}
    mapping: Dict[str, str] = {}
    for index, raw in enumerate(options):
        label = chr(ord("A") + index)
        text = str(raw or "").strip()
        if not text:
            continue
        lowered = text.lower()
        mapping[lowered] = label
        stripped = _strip_option_prefix(text)
        if stripped:
            mapping.setdefault(stripped.lower(), label)
    return mapping


def _strip_option_prefix(value: str) -> str:
    return _OPTION_PREFIX_PATTERN.sub("", value, count=1).strip()


def _extract_letters_from_token(token: str, valid_labels: Set[str]) -> List[str]:
    letters_only = "".join(ch.upper() for ch in token if ch.isalpha())
    if not letters_only:
        return []

    if len(letters_only) == 1:
        letter = letters_only[0]
        if not valid_labels or letter in valid_labels:
            return [letter]
        return []

    if valid_labels and any(ch not in valid_labels for ch in letters_only):
        return []

    ordered = []
    for ch in letters_only:
        if ch not in ordered:
            ordered.append(ch)

    if valid_labels:
        ordered = [ch for ch in ordered if ch in valid_labels]

    return ordered
