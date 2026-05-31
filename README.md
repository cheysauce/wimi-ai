# Chinese Vocabulary Frequency Tool v2

This is a beginner-friendly local web app for turning Chinese textbook chapters into a ranked vocabulary table.

## Features

1. **Known-word list**: hide words the learner already knows.
2. **Pinyin**: add pronunciation for each Chinese word.
3. **Translation**: use a local dictionary first, with optional AI translation for missing words.
4. **Textbook chapters**: compare word frequency across multiple chapters.
5. **Difficulty / study priority score**: rank words by frequency plus learner level.

## How to run locally

Open terminal or PowerShell inside this folder, then run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app should open at:

```text
http://localhost:8501
```

## Recommended workflow

1. Paste Chapter 1, Chapter 2, etc., or upload `.txt` files.
2. Add words you already know in the Known Words tab.
3. Choose your learner level in the sidebar.
4. Click **Create frequency table**.
5. Download the CSV.
6. Mark more words as known and run again.

## Translation options

The app uses this file first:

```text
data/dictionary.csv
```

Format:

```csv
word,english
学习,to study; to learn
中文,Chinese language
```

For more complete dictionary coverage, you can later replace this with a larger dictionary export, such as CC-CEDICT converted to CSV.

AI translation is optional. Put your OpenAI API key in the sidebar and click **AI-translate missing words**. For real products, save AI translations to a database or CSV so you do not pay repeatedly for the same words.

## HSK level file

The study priority score uses:

```text
data/hsk_levels.csv
```

Format:

```csv
word,hsk_level
我,1
学习,1
环境,3
```

If a word is not in the HSK file, the app marks its level as `unknown` and gives it a moderate difficulty penalty.

## Study priority formula

The app combines:

- Frequency in the uploaded chapters
- Difficulty compared with the learner's HSK level
- Unknown level penalty
- Word length as a small complexity signal

Higher score means: **study this word sooner**.

This is a practical heuristic, not a scientific language acquisition model. You can tune the formula in `core.py` later.
