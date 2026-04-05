import re


def escape_fts5_query(query: str) -> str:
    """
    Escape special characters in a full-text search query for FTS5.
    """
    special_chars = ['"', "*", "(", ")", "-", "+"]
    for char in special_chars:
        query = query.replace(char, f'"{char}"')
    return query


def escape_fts5_term(term: str) -> str:
    """
    Escape a single search term for FTS5 queries.

    Args:
        term: A single search term.

    Returns:
        The escaped term wrapped in double quotes.
    """
    special_chars = ['"', "*", "(", ")", "+", "-"]
    for char in special_chars:
        term = term.replace(char, f'"{char}"')
    return f'"{term}"'


def parse_query(query: str) -> str:
    """Parse a search query into FTS5-compatible syntax.

    Extracts quoted phrases and individual terms, escaping FTS5 special characters
    while preserving boolean operators (AND, OR).

    Args:
        query: The raw search query string.

    Returns:
        An FTS5-compatible query string with escaped terms.
    """
    terms = re.findall(r'"[^"]*"|\S+', query)
    parsed_query = []
    for term in terms:
        if term in ("AND", "OR"):
            parsed_query.append(term.upper())
        else:
            parsed_query.append(escape_fts5_term(term.strip('"')))
    return " ".join(parsed_query)


def parse_query_with_proximity(
    query: str, proximity: int | None = None, near_term: str | None = None
) -> str:
    """
    Parse query with NEAR proximity support.

    Args:
        query: The search query text
        proximity: Max word distance for NEAR queries (default: 10). None = don't use NEAR.
        near_term: Optional term to search near (finds all query terms near this word)

    Returns:
        FTS5-compatible query string with NEAR operators

    Examples:
        >>> parse_query_with_proximity("neural network", proximity=5)
        '"neural NEAR/5 network"'
        >>> parse_query_with_proximity("deep learning", near_term="AI", proximity=10)
        '"deep NEAR/10 AI" AND "learning NEAR/10 AI"'
        >>> parse_query_with_proximity("test query")  # No proximity specified
        '"test" "query"'
    """
    # Extract quoted phrases and individual terms
    terms = re.findall(r'"[^"]*"|\S+', query)

    # Filter out empty terms
    terms = [t for t in terms if t.strip()]

    # Handle --near option: find all query terms near the specified word
    if near_term:
        # Default proximity to 10 if not specified
        if proximity is None:
            proximity = 10

        # Escape the near term for FTS5
        escaped_near = escape_fts5_term(near_term.strip('"'))

        # Build NEAR queries for each term in the original query
        near_clauses = []
        for term in terms:
            # Skip boolean operators and empty terms
            if term in ("AND", "OR", "NOT") or not term.strip():
                continue

            # Strip quotes from term for NEAR query
            clean_term = term.strip('"')

            # Skip if this is the near term itself
            if clean_term.lower() == near_term.strip('"').lower():
                continue

            # Create NEAR clause
            near_clauses.append(f'"{escape_fts5_term(clean_term)} NEAR/{proximity} {escaped_near}"')

        # Join with AND if we have multiple clauses
        if near_clauses:
            return " AND ".join(near_clauses)
        # If only near_term was provided, just search for it
        return escaped_near

    # Handle --proximity option: add NEAR between consecutive query terms
    # Only apply if proximity is explicitly specified (not None)
    if proximity is not None and len(terms) > 1:
        # Build NEAR query for consecutive terms
        # For query "machine learning AI", we create:
        # "machine NEAR/10 learning" AND "learning NEAR/10 AI"

        # Filter out boolean operators for proper NEAR construction
        search_terms = []
        for term in terms:
            if term not in ("AND", "OR", "NOT"):
                search_terms.append(term.strip('"'))

        # Create NEAR clauses between consecutive terms
        near_clauses = []
        for i in range(len(search_terms) - 1):
            term1 = escape_fts5_term(search_terms[i])
            term2 = escape_fts5_term(search_terms[i + 1])
            near_clauses.append(f'"{term1} NEAR/{proximity} {term2}"')

        # Join all NEAR clauses with AND
        if near_clauses:
            return " AND ".join(near_clauses)

    # Fallback to standard query parsing if no special handling needed
    return parse_query(query)
