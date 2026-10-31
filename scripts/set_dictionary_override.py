import os
import re
import sys
import psycopg

word = sys.argv[1].upper()
allowed = sys.argv[2] == "true"
reason = sys.argv[3]
if not re.fullmatch(r"[A-Z]{2,20}", word) or not reason.strip():
    raise ValueError("Invalid word or reason")
with psycopg.connect(os.environ["DATABASE_URL"]) as connection:
    connection.execute(
        "insert into dictionary_private.overrides(word,allowed,reason) values(%s,%s,%s) on conflict(word) do update set allowed=excluded.allowed,reason=excluded.reason,updated_at=now()",
        (word, allowed, reason),
    )
print(f"Override saved: {word} -> {allowed}", flush=True)
