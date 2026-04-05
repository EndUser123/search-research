# ADR-003: Fast Change Detection using Shallow Hashing

- **Status:** Accepted
- **Date:** 2025-06-22

## Context

The initial file scanning phase of the application is unacceptably slow for users with large video libraries. The root cause is the current change-detection mechanism, which computes a full SHA256 hash of every file. This requires reading every byte of every file from disk, an operation that is extremely I/O-intensive and does not scale well. A faster method is required.

## Decision

We will replace the current full-content hashing mechanism with a much faster, "shallow hash". A file will be considered "unchanged" if a SHA256 hash of a concatenation of the **first 1MB** and the **last 1MB** of the file matches the previously recorded hash.

## Rationale

-   **Performance:** This method is orders of magnitude faster than a full-content hash. It requires reading a small, fixed amount of data (max 2MB) per file, dramatically reducing the I/O bottleneck and improving startup time from minutes to seconds.
-   **High Reliability:** This approach is significantly more reliable than a simple metadata check (file size, timestamp). By sampling the beginning and end of the file, the hash captures critical data like file headers, codec information (`moov` atoms), and container metadata, which are almost certain to change during any re-encode or meaningful file alteration. It provides the best balance of high performance and very high reliability for our use case.

## Consequences

-   The application will no longer detect changes that occur *only* in the middle of a file without affecting the first or last megabyte. This risk is deemed exceptionally low for this application's purpose.
-   The database schema for `vidrec_state.db` must be changed. The `file_hash` column will be renamed to `shallow_hash` to reflect the new meaning of the data. Users updating to this version will need to delete their old state database and perform a new, one-time scan.
