import os
import sys
import traceback


def test():
    try:
        sys.path.append(os.path.abspath("src"))
        print(f"sys.path: {sys.path}")

        print("Importing get_db_connection...")
        from yt_fts.db.infra import get_db_connection

        print("Imported.")

        print("Calling get_db_connection()...")
        try:
            conn = get_db_connection()
            print("Successfully called get_db_connection()")
            conn.close()
        except Exception:
            print("Failed to call get_db_connection()")
            traceback.print_exc()

    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    test()
