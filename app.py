from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core import (
    DEFAULT_STOPWORDS,
    create_chapter_frequency_table,
    load_dictionary,
    load_hsk_levels,
    load_word_set,
    parse_word_list,
    read_text_file,
    save_words,
    translate_words_with_openai,
)

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
KNOWN_PATH = DATA_DIR / "known_words.txt"
STOPWORDS_PATH = DATA_DIR / "stopwords.txt"
DICTIONARY_PATH = DATA_DIR / "HSK1-6-Pinyin-order-dictionary.xlsx"
HSK_PATH = DATA_DIR / "HSK1-6-Pinyin-order-dictionary.xlsx"

st.set_page_config(
    page_title="Chinese Vocabulary Frequency Tool",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Chinese Vocabulary Frequency Tool")
st.caption("Paste text, upload a file, or record audio — then rank vocabulary by study priority.")

if "known_words" not in st.session_state:
    st.session_state.known_words = load_word_set(KNOWN_PATH)
if "ai_translations" not in st.session_state:
    st.session_state.ai_translations = {}
if "last_table" not in st.session_state:
    st.session_state.last_table = pd.DataFrame()

DATA_DIR.mkdir(exist_ok=True)
stopwords = load_word_set(STOPWORDS_PATH, default=DEFAULT_STOPWORDS)
dictionary = load_dictionary(DICTIONARY_PATH)
hsk_levels = load_hsk_levels(HSK_PATH)

with st.sidebar:
    st.header("Settings")
    learner_level = st.selectbox(
        "Learner level",
        options=[1, 2, 3, 4, 5, 6],
        index=1,
        help="Used for the study priority score.",
    )
    min_len = st.radio(
        "Minimum word length",
        options=[1, 2],
        index=1,
        help="Use 2 to remove many one-character function words.",
    )
    hide_known = st.checkbox("Hide known words", value=True)
    remove_stopwords = st.checkbox("Remove common stopwords", value=True)
    top_n = st.number_input("Show top N words", min_value=10, max_value=1000, value=100, step=10)
    st.divider()
    st.subheader("Optional AI translation")
    openai_api_key = st.text_input("OpenAI API key", type="password", help="Optional.")
    ai_limit = st.slider("Translate missing top words", min_value=5, max_value=100, value=30, step=5)

chapters: dict[str, str] = {}

tab_chapters, tab_known, tab_resources = st.tabs(["1. Text Input", "2. Known words", "3. Dictionary / levels"])

with tab_chapters:
    st.subheader("Add text")

    input_method = st.radio(
        "Input method",
        ["📄 Upload / Paste text", "🎙️ Record or Upload Audio (Speech-to-Text)"],
        horizontal=True,
    )

    if input_method == "📄 Upload / Paste text":
        uploaded_files = st.file_uploader(
            "Upload one or more .txt files",
            type=["txt"],
            accept_multiple_files=True,
        )
        if uploaded_files:
            for i, file in enumerate(uploaded_files, start=1):
                name = file.name.rsplit(".", 1)[0] or f"Text {i}"
                chapters[name] = read_text_file(file)
            st.success(f"Loaded {len(chapters)} file(s).")

        pasted_text = st.text_area(
            "Or paste text here",
            height=240,
            placeholder="Paste Chinese text here...",
            key="pasted_text",
        )
        if pasted_text.strip():
            chapters["Pasted text"] = pasted_text

    else:
        from faster_whisper import WhisperModel
        from streamlit_mic_recorder import mic_recorder

        @st.cache_resource
        def load_whisper():
            return WhisperModel("base", device="cpu", compute_type="int8")

        whisper_model = load_whisper()

        audio_input_method = st.radio(
            "Audio input",
            ["🎙️ Record from mic", "📂 Upload audio file"],
            horizontal=True,
        )

        if audio_input_method == "🎙️ Record from mic":
            st.info("Click the button below to record spoken Chinese.")
            audio = mic_recorder(
                start_prompt="⏺ Start recording",
                stop_prompt="⏹ Stop recording",
                just_once=True,
                key="mic_recorder",
            )
            if audio:
                import tempfile
                st.audio(audio["bytes"])
                with st.spinner("Transcribing audio..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                        f.write(audio["bytes"])
                        tmp_path = f.name
                segments, _ = whisper_model.transcribe(tmp_path, language="zh")
                transcript = "".join([seg.text for seg in segments])
                st.success("Transcription complete!")
                st.text_area("Transcribed text (edit if needed)", value=transcript, height=180, key="stt_result")
                chapters["Recording"] = st.session_state.get("stt_result", transcript)

        else:
            uploaded_audio = st.file_uploader(
                "Upload an audio file",
                type=["wav", "mp3", "m4a", "ogg", "flac"],
                key="audio_upload",
            )
            if uploaded_audio:
                import tempfile
                st.audio(uploaded_audio)
                with st.spinner("Transcribing audio..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_audio.name.split(".")[-1]) as f:
                        f.write(uploaded_audio.read())
                        tmp_path = f.name
                segments, _ = whisper_model.transcribe(tmp_path, language="zh")
                transcript = "".join([seg.text for seg in segments])
                st.success("Transcription complete!")
                st.text_area("Transcribed text (edit if needed)", value=transcript, height=180, key="audio_stt_result")
                chapters["Audio upload"] = st.session_state.get("audio_stt_result", transcript)

with tab_known:
    st.subheader("Known-word list")
    st.write("Words in this list can be hidden from the results, so the learner focuses on new vocabulary.")
    known_text = st.text_area(
        "Known words",
        value="\n".join(sorted(st.session_state.known_words)),
        height=240,
        help="One word per line is easiest, but spaces and commas also work.",
    )
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Update known words in this session"):
            st.session_state.known_words = parse_word_list(known_text)
            st.success(f"Updated session known-word list: {len(st.session_state.known_words)} words.")
    with col_b:
        if st.button("Save known words locally"):
            st.session_state.known_words = parse_word_list(known_text)
            save_words(KNOWN_PATH, st.session_state.known_words)
            st.success(f"Saved to {KNOWN_PATH}")
    st.download_button(
        "Download known_words.txt",
        data="\n".join(sorted(st.session_state.known_words)).encode("utf-8"),
        file_name="known_words.txt",
        mime="text/plain",
    )

with tab_resources:
    st.subheader("Dictionary and level files")
    st.write("The app uses the HSK 1-6 xlsx file for dictionary lookups and HSK levels.")
    st.code(
        "data/HSK1-6-Pinyin-order-dictionary.xlsx — HSK 1-6 words, pinyin & English\n"
        "data/stopwords.txt format: one word per line",
        language="text",
    )
    st.write(f"Dictionary entries loaded: **{len(dictionary)}**")
    st.write(f"HSK level entries loaded: **{len(hsk_levels)}**")
    st.write(f"Stopwords loaded: **{len(stopwords)}**")

st.divider()

if st.button("Create frequency table", type="primary"):
    chapters = {name: text for name, text in chapters.items() if text and text.strip()}
    if not chapters:
        st.warning("Add at least one text first.")
    else:
        table = create_chapter_frequency_table(
            chapters=chapters,
            known_words=st.session_state.known_words,
            stopwords=stopwords if remove_stopwords else set(),
            min_len=min_len,
            hide_known=hide_known,
            dictionary=dictionary,
            ai_translations=st.session_state.ai_translations,
            hsk_levels=hsk_levels,
            learner_level=int(learner_level),
        )
        st.session_state.last_table = table

table = st.session_state.last_table

if not table.empty:
    visible_table = table.head(int(top_n)).copy()

    st.subheader("Vocabulary results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique words shown", len(table))
    c2.metric("Total counted words", int(table["total_count"].sum()))
    c3.metric("Known words", len(st.session_state.known_words))
    c4.metric("Dictionary translations", int((table["english"].astype(str).str.len() > 0).sum()))

    display_cols = [
        "rank", "word", "pinyin", "english", "total_count", "percent", "chapters_seen",
        "hsk_level", "difficulty", "study_priority_score",
    ]
    extra_cols = [col for col in visible_table.columns if col not in display_cols]
    display_cols = display_cols + extra_cols

    st.dataframe(visible_table[display_cols], use_container_width=True, hide_index=True)

    csv_data = table.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Download full CSV",
        data=csv_data,
        file_name="chinese_vocabulary_frequency_table.csv",
        mime="text/csv",
    )

    st.subheader("Improve the known-word list")
    words_to_mark = st.multiselect(
        "Select words you already know",
        options=table["word"].head(300).tolist(),
    )
    if st.button("Add selected words to known list"):
        st.session_state.known_words.update(words_to_mark)
        st.success(f"Added {len(words_to_mark)} word(s). Click 'Create frequency table' again to hide them.")

    st.subheader("Optional: fill missing translations with AI")
    missing = table[table["english"].astype(str).str.len() == 0]["word"].head(int(ai_limit)).tolist()
    st.write(f"Missing translations in top results: {len(missing)}")
    if st.button("AI-translate missing words"):
        if not openai_api_key:
            st.warning("Enter an OpenAI API key in the sidebar first.")
        elif not missing:
            st.info("No missing translations in the selected range.")
        else:
            with st.spinner("Translating missing words..."):
                try:
                    new_translations = translate_words_with_openai(missing, api_key=openai_api_key)
                    st.session_state.ai_translations.update(new_translations)
                    st.success(f"Added {len(new_translations)} AI translation(s). Click 'Create frequency table' again to refresh.")
                except Exception as exc:
                    st.error(f"AI translation failed: {exc}")
else:
    st.info("Add text above, then click **Create frequency table**.")