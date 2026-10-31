import hashlib
import os
import re
import sys
import psycopg

label, filename, source = sys.argv[1:4]
words = sorted({line.strip().upper() for line in open(filename, encoding="utf-8") if line.strip()})
if not words or any(not re.fullmatch(r"[A-Z]{2,20}", word) for word in words):
    raise ValueError("Empty or invalid word list")
digest = hashlib.sha256(("\n".join(words)+"\n").encode()).hexdigest()
with psycopg.connect(os.environ["DATABASE_URL"]) as db:
    with db.cursor() as cur:
        cur.execute("insert into dictionary_private.versions(label,source,license_approved) values(%s,%s,false) returning id", (label,source))
        version = cur.fetchone()[0]
        for i in range(0,len(words),1000):
            cur.executemany("insert into dictionary_private.entries(version_id,word) values(%s,%s)", [(version,w) for w in words[i:i+1000]])
            print(f"Inserted {min(i+1000,len(words))}/{len(words)}",flush=True)
        cur.execute("update dictionary_private.versions set status='ready',expected_count=%s,checksum=%s where id=%s",(len(words),digest,version))
print(f"Built version {version} ({len(words)} words), SHA256 {digest}; publication blocked until license approval",flush=True)
