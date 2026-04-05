from typing import cast

import redis

try:
    # Connect to the default Redis instance on localhost
    r = redis.Redis(decode_responses=True)

    # Ping the server to ensure we have a connection
    r.ping()
    print("Successfully connected to Redis.")

    # Get the number of keys before clearing.
    # Use cast() to inform the type checker of the expected type.
    key_count = cast(int, r.dbsize())
    print(f"Found {key_count} keys in the database.")

    if key_count > 0:
        # This is the command that deletes everything
        print("Clearing all keys from the Redis database...")
        r.flushall()

        # Verify it's empty, using cast() again for type safety.
        new_key_count = cast(int, r.dbsize())
        print(f"Database cleared. Current key count: {new_key_count}")
        print("\nSUCCESS: The Redis queue has been cleared of all stale jobs.")
    else:
        print("\nSUCCESS: Redis database is already empty. No action needed.")

except redis.ConnectionError as e:
    print("\nERROR: Could not connect to Redis.")
    print(f"Please ensure your Redis server is running. Details: {e}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
