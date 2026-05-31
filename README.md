`#` 📚 `WiMi AI — Chinese Vocabulary Frequency Tool` 

```
A web app for turning Chinese text into a ranked vocabulary study list. Paste
text, upload files, or record/upload audio — the app segments the Chinese, adds
pinyin and English translations, tags HSK levels, and ranks words by study
priority.
```

```
🔗 **Live app:** [wimiworld.streamlit.app](https://wimiworld.streamlit.app)
```

```
---
```

```
## 🔗 Features
```

`1. **Known-word filtering** — hide words the learner already knows` 

`2. **Pinyin** — automatic pronunciation for every word` 

`3. **HSK level tagging** — each word tagged HSK 1–6 (or "unknown")` 

`4. **English translations** — looked up from the HSK 1–6 dictionary automatically` 

`5. **Optional AI translation** — fills in missing translations via OpenAI API` 

`6. **Study priority score** — ranks words by frequency + difficulty vs. learner level` 

`7. **Audio input** — record from mic or upload audio files (WAV, MP3, M4A, OGG, FLAC), auto-transcribed via Whisper` 

`8. **Text input** — paste text directly or upload `.txt` files` 

`9. **Download CSV** — export the full vocabulary table` 

```
---
```

```
## 🔗 How to Use (Live App)
```

`1. Open [wimiworld.streamlit.app](https://wimiworld.streamlit.app)` 

`2. In the **Text Input** tab, choose your input method:` 

- `Paste Chinese text directly` 

- `Upload a `.txt` file` 

- `Record audio from your mic` 

- `Upload an audio file` 

`3. Adjust settings in the **sidebar** (learner level, filters)` 

`4. Click **Create frequency table**` 

`5. Browse ranked vocabulary with pinyin, English, HSK level, and study priority` 

`6. Download results as CSV or mark words as known and run again` 

```
---
```

`## How to Run Locally` 🛠️� 

```
```bash
git clone https://github.com/cheysauce/wimi-ai.git
cd wimi-ai
pip install -r requirements.txt
streamlit run app.py
```
```

```
The app will open at:
```

```
```
```

```
http://localhost:8501
```
```

```
---
```

`##` ⚙️� `Settings (Sidebar)` 

```
| Setting | Description |
|---|---|
```

```
| **Learner level** | Your current HSK level — affects difficulty labels and
priority scores |
```

```
| **Minimum word length** | Set to 2 to filter out single-character function
words |
```

```
| **Hide known words** | Hides words from your `known_words.txt` list |
```

`| **Remove stopwords** | Filters out common filler words (` 的 `,` 了 `,` 然后 `, etc.) |` 

```
| **Show top N words** | Limits how many words appear in the results table |
```

```
---
```

```
## 🔗 Project Structure
```

```
```
```

## `wimi-ai/` 

```
├── app.py                                    # Streamlit frontend
├── core.py                                   # Core logic (segmentation,
scoring, loading)
```

- `├── requirements.txt                          # Python dependencies └── data/` 

- `├── HSK1-6-Pinyin-order-dictionary.xlsx   # HSK 1-6 reference (words, pinyin, English, level)` 

- `├── known_words.txt                       # Words to hide from results └── stopwords.txt                         # Common words to filter out ```` 

```
---
```

```
## 🔗 Dictionary & HSK Levels
```

```
The app reads directly from the HSK 1–6 xlsx file for both translations and
level data — no separate CSV files needed. It supports both single-sheet and
multi-sheet xlsx formats automatically.
```

```
If a word is not in the HSK file, the app marks its level as `unknown` and gives
it a moderate difficulty penalty in the scoring.
```

```
---
```

## `## 🔗 Optional AI Translation` 

```
Words not found in the HSK dictionary can be translated using OpenAI's API:
```

`1. Get an API key from [platform.openai.com](https://platform.openai.com)` 

`2. Enter it in the sidebar under **Optional AI translation**` 

`3. Click **AI-translate missing words**` 

```
For production use, consider caching AI translations to avoid repeated API
costs.
```

```
---
```

`##` 📊 `Study Priority Formula` 

```
The score combines:
```

- `**Frequency** in the uploaded text` 

- `**Difficulty** compared with the learner's HSK level` 

- `**Unknown level penalty** for words outside HSK 1–6` 

- `**Word length** as a small complexity signal` 

```
Higher score = **study this word sooner**. This is a practical heuristic, not a
scientific language acquisition model. The formula can be tuned in `core.py`.
```

```
---
```

## `##` 📦 `Dependencies` 

- `[Streamlit](https://streamlit.io/) — web app framework` 

- `[jieba](https://github.com/fxsjy/jieba) — Chinese word segmentation` 

- `[pypinyin](https://github.com/mozillazg/python-pinyin) — pinyin generation` 

- `[faster-whisper](https://github.com/SYSTRAN/faster-whisper) — speech-to-text transcription` 

- `[openai](https://github.com/openai/openai-python) — optional AI translation` 

- `[openpyxl](https://openpyxl.readthedocs.io/) — xlsx file reading` 

