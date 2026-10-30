from fastapi import FastAPI, HTTPException
from pathlib import Path
import os
import unicodedata

app = FastAPI(title="Mini Cuvinte Lexical API", version="1.0.0")
WORDS_PATH = Path(os.getenv("WORDS_FILE", "data/words.txt"))

def normalize(word: str) -> str:
    return unicodedata.normalize("NFC", word.strip().lower())

def load_words() -> set[str]:
    if not WORDS_PATH.is_file():
        return set()
    return {normalize(line) for line in WORDS_PATH.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")}

words = load_words()

@app.get("/health")
def health():
    return {"status": "ok", "dictionary_loaded": bool(words), "word_count": len(words)}

@app.get("/api/v1/words/{word}")
def check_word(word: str):
    term = normalize(word)
    if not term or len(term) > 64 or not all(c.isalpha() or c == "-" for c in term):
        raise HTTPException(status_code=422, detail="Invalid word")
    return {"word": term, "status": "valid" if term in words else "unknown", "source": os.getenv("LEXICAL_SOURCE", "local"), "word_count": len(words)}
