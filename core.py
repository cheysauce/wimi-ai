"""
Core functions for Chinese Textbook Vocabulary Tool.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

import jieba
import pandas as pd
from pypinyin import Style, lazy_pinyin

CHINESE_RE = re.compile(r"[\u4e00-\u9fff]+")

DEFAULT_STOPWORDS = {
    "的", "了", "和", "是", "我", "你", "他", "她", "它", "们",
    "在", "有", "就", "不", "也", "都", "很", "一个", "这个", "那个",
    "吗", "呢", "啊", "吧", "然后", "所以", "因为", "但是", "如果",
    "就是", "还是", "可以", "没有", "不是", "被", "给", "把", "让",
}

def read_text_file(uploaded_file) -> str:
    raw = uploaded_file.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8-sig", errors="ignore")

def load_word_set(path: str | Path | None, default: Iterable[str] | None = None) -> set[str]:
    words = set(default or [])
    if not path:
        return words
    file_path = Path(path)
    if not file_path.exists():
        return words
    for line in file_path.read_text(encoding="utf-8").splitlines():
        word = line.strip()
        if word and not word.startswith("#"):
            words.add(word)
    return words

def parse_word_list(text: str) -> set[str]:
    if not text:
        return set()
    pieces = re.split(r"[\s,，、;；]+", text)
    return {piece.strip() for piece in pieces if piece.strip()}

def clean_text(text: str) -> str:
    text = re.sub(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}", " ", text)
    text = re.sub(r"[A-Za-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_chinese_words(
    text: str,
    stopwords: set[str] | None = None,
    known_words: set[str] | None = None,
    min_len: int = 1,
    hide_known: bool = True,
) -> list[str]:
    stopwords = stopwords or set()
    known_words = known_words or set()
    words: list[str] = []
    for token in jieba.cut(clean_text(text)):
        token = token.strip()
        if not CHINESE_RE.fullmatch(token):
            continue
        if len(token) < min_len:
            continue
        if token in stopwords:
            continue
        if hide_known and token in known_words:
            continue
        words.append(token)
    return words

def load_dictionary(path: str | Path | None) -> dict[str, str]:
    """Load dictionary from HSK xlsx file (single-sheet or multi-sheet) or CSV."""
    if not path or not Path(path).exists():
        return {}
    path = Path(path)
    if path.suffix == '.xlsx':
        xl = pd.ExcelFile(path)
        result = {}
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None)
            if df.shape[1] >= 6:
                for _, row in df.iterrows():
                    word = str(row.iloc[1]).strip()
                    eng = str(row.iloc[5]).strip()
                    if word and eng and word != 'nan' and eng != 'nan':
                        result.setdefault(word, eng)
        return result
    df = pd.read_csv(path)
    if not {'word', 'english'}.issubset(df.columns):
        raise ValueError("Dictionary CSV must have columns: word, english")
    return {str(r['word']).strip(): str(r['english']).strip() for _, r in df.iterrows() if str(r['word']).strip()}

def load_hsk_levels(path: str | Path | None) -> dict[str, int]:
    """Load HSK levels from HSK xlsx file (single-sheet or multi-sheet) or CSV."""
    if not path or not Path(path).exists():
        return {}
    path = Path(path)
    if path.suffix == '.xlsx':
        xl = pd.ExcelFile(path)
        result = {}
        hsk_map = {
            'HSK 1': 1, 'HSK1': 1, 'HSK 2': 2, 'HSK2': 2,
            'HSK 3': 3, 'HSK3': 3, 'HSK 4': 4, 'HSK4': 4,
            'HSK 5': 5, 'HSK5': 5, 'HSK 6': 6, 'HSK6': 6,
        }
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None)
            if df.shape[1] >= 7:
                # New format: single sheet with hsk level in col 6
                for _, row in df.iterrows():
                    word = str(row.iloc[1]).strip()
                    level_str = str(row.iloc[6]).strip()
                    level = hsk_map.get(level_str)
                    if word and level and word != 'nan':
                        result.setdefault(word, level)
            elif df.shape[1] == 6:
                # Old format: per-level sheets
                level = next((v for k, v in hsk_map.items() if sheet.startswith(k) and 'HSK1-HSK6' not in sheet), None)
                if level is None:
                    continue
                for _, row in df.iloc[2:].iterrows():
                    word = str(row.iloc[1]).strip()
                    if word and word != 'nan':
                        result.setdefault(word, level)
        return result
    df = pd.read_csv(path)
    if not {'word', 'hsk_level'}.issubset(df.columns):
        raise ValueError("HSK CSV must have columns: word, hsk_level")
    result = {}
    for _, row in df.iterrows():
        word = str(row['word']).strip()
        if not word:
            continue
        try:
            result[word] = int(row['hsk_level'])
        except ValueError:
            continue
    return result

def word_to_pinyin(word: str) -> str:
    return " ".join(lazy_pinyin(word, style=Style.TONE))

def difficulty_label(hsk_level: int | None, learner_level: int) -> str:
    if hsk_level is None:
        return "Unknown level"
    if hsk_level <= learner_level:
        return "Review"
    if hsk_level == learner_level + 1:
        return "Good challenge"
    return "Hard"

def study_priority_score(total_count: int, hsk_level: int | None, learner_level: int, word: str) -> float:
    frequency_component = min(60.0, math.log1p(total_count) * 25.0)
    length_component = min(12.0, max(0, len(word) - 1) * 3.0)
    if hsk_level is None:
        level_component = 25.0
    else:
        level_gap = hsk_level - learner_level
        if level_gap <= 0:
            level_component = 4.0
        elif level_gap == 1:
            level_component = 18.0
        else:
            level_component = min(35.0, 18.0 + (level_gap - 1) * 8.0)
    return round(frequency_component + level_component + length_component, 1)

def create_chapter_frequency_table(
    chapters: dict[str, str],
    known_words: set[str] | None = None,
    stopwords: set[str] | None = None,
    min_len: int = 1,
    hide_known: bool = True,
    dictionary: dict[str, str] | None = None,
    ai_translations: dict[str, str] | None = None,
    hsk_levels: dict[str, int] | None = None,
    learner_level: int = 2,
) -> pd.DataFrame:
    known_words = known_words or set()
    stopwords = stopwords or set()
    dictionary = dictionary or {}
    ai_translations = ai_translations or {}
    hsk_levels = hsk_levels or {}

    chapter_counters: dict[str, Counter[str]] = {}
    total_counter: Counter[str] = Counter()

    for chapter_name, chapter_text in chapters.items():
        words = extract_chinese_words(
            chapter_text,
            stopwords=stopwords,
            known_words=known_words,
            min_len=min_len,
            hide_known=hide_known,
        )
        counter = Counter(words)
        chapter_counters[chapter_name] = counter
        total_counter.update(counter)

    total_words = sum(total_counter.values())
    rows: list[dict[str, object]] = []

    for word, total_count in total_counter.most_common():
        hsk_level = hsk_levels.get(word)
        row: dict[str, object] = {
            "word": word,
            "pinyin": word_to_pinyin(word),
            "english": ai_translations.get(word) or dictionary.get(word, ""),
            "total_count": int(total_count),
            "percent": round((total_count / total_words) * 100, 3) if total_words else 0,
            "chapters_seen": sum(1 for c in chapter_counters.values() if c.get(word, 0) > 0),
            "hsk_level": hsk_level if hsk_level is not None else "unknown",
            "difficulty": difficulty_label(hsk_level, learner_level),
            "study_priority_score": study_priority_score(total_count, hsk_level, learner_level, word),
        }
        for chapter_name, counter in chapter_counters.items():
            row[chapter_name] = int(counter.get(word, 0))
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values(
        by=["study_priority_score", "total_count", "chapters_seen"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    return df

def extract_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}

def translate_words_with_openai(words: list[str], api_key: str, model: str = "gpt-4o-mini") -> dict[str, str]:
    if not words:
        return {}
    if not api_key:
        raise ValueError("OpenAI API key is required for AI translation.")
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    unique_words = list(dict.fromkeys(words))
    prompt = (
        "Translate these Chinese vocabulary items into short English meanings for a language learner.\n"
        "Return ONLY valid JSON where each key is the Chinese word and each value is a concise English meaning.\n"
        "Do not include explanations outside JSON.\n\n"
        f"Words: {unique_words}"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    content = response.choices[0].message.content or "{}"
    data = extract_json_object(content)
    return {str(k): str(v) for k, v in data.items()}

def save_words(path: str | Path, words: set[str]) -> None:
    Path(path).write_text("\n".join(sorted(words)), encoding="utf-8")