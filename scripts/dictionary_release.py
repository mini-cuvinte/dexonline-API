import os
import sys
import psycopg

if __name__ == '__main__':
    version = int(sys.argv[1])
    with psycopg.connect(os.environ['DATABASE_URL']) as db:
        db.execute('select dictionary_private.publish_version(%s)', (version,))
    print(f'Activated dictionary version {version}', flush=True)
