import os
import sys
import psycopg

version = int(sys.argv[1])
with psycopg.connect(os.environ["DATABASE_URL"]) as connection:
    with connection.cursor() as cursor:
        cursor.execute("select version_id from dictionary_private.active_version where singleton=true")
        active = cursor.fetchone()
        if active and active[0] == version:
            raise ValueError("Refusing to remove the active dictionary")
        cursor.execute("delete from dictionary_private.versions where id=%s and status='archived' returning id", (version,))
        if cursor.fetchone() is None:
            raise ValueError("Only an archived version may be removed")
print(f"Removed archived version {version}", flush=True)
