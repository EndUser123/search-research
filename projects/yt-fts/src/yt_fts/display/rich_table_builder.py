"""
RichTableBuilder - Fluent API for building Rich tables.

This module provides a builder pattern for creating Rich tables with less
boilerplate code. It encapsulates common table creation patterns used
throughout yt-fts.

Example:
    >>> builder = RichTableBuilder(title="My Table", header_style="bold magenta")
    >>> builder.add_column("Name", style="cyan", justify="left")
    >>> builder.add_column("Value", style="green")
    >>> builder.add_row("Alice", "123")
    >>> builder.add_row("Bob", "456")
    >>> builder.print()
"""
from __future__ import annotations

from collections.abc import Iterable
from io import StringIO
from typing import Any, Literal, cast

from rich.console import Console
from rich.table import Table


class RichTableBuilder:
    """
    Fluent builder for Rich Table instances.

    Provides a streamlined API for creating and configuring Rich tables
    with consistent styling across the application.
    """

    def __init__(
        self,
        title: str | None = None,
        header_style: str = "bold",
        show_header: bool = True,
    ) -> None:
        """
        Initialize a new RichTableBuilder.

        Args:
            title: Optional table title.
            header_style: Rich style for header row (default: "bold").
            show_header: Whether to show the header row.
        """
        self._table = Table(title=title, header_style=header_style, show_header=show_header)
        self._columns_configured = False
        self._rows: list[list[str]] = []

    def add_column(
        self,
        header: str,
        style: str = "",
        justify: Literal["left", "center", "right"] = "left",
        width: int | None = None,
        **kwargs: Any,
    ) -> "RichTableBuilder":
        """
        Add a column to the table.

        Args:
            header: Column header text.
            style: Rich style string for the column.
            justify: Text alignment (left, center, right).
            width: Optional fixed width for the column.
            **kwargs: Additional arguments passed to Table.add_column().

        Returns:
            Self for method chaining.
        """
        self._table.add_column(header, style=style or None, justify=justify, width=width, **kwargs)
        return self

    def add_columns(self, *columns: str | tuple[str, dict[str, Any]]) -> "RichTableBuilder":
        """
        Add multiple columns to the table.

        Args:
            *columns: Column definitions. Each can be:
                - A string (header name only)
                - A tuple of (header, options_dict)

        Returns:
            Self for method chaining.

        Example:
            >>> builder.add_columns(
            ...     "Name",
            ...     ("Count", {"style": "green", "justify": "right"})
            ... )
        """
        for col in columns:
            if isinstance(col, str):
                self.add_column(col)
            elif isinstance(col, tuple) and len(col) == 2:
                header, opts = col
                self.add_column(header, **opts)
        return self

    def add_row(self, *items: Any, **kwargs: Any) -> "RichTableBuilder":
        """
        Add a row to the table.

        Args:
            *items: Row values as strings or objects convertible to strings.
            **kwargs: Additional arguments passed to Table.add_row().

        Returns:
            Self for method chaining.
        """
        # Convert all items to strings
        str_items = [str(item) if item is not None else "" for item in items]
        self._table.add_row(*str_items, **kwargs)
        return self

    def add_rows(self, rows: Iterable[Iterable[Any]]) -> "RichTableBuilder":
        """
        Add multiple rows to the table.

        Args:
            rows: Iterable of row iterables.

        Returns:
            Self for method chaining.
        """
        for row in rows:
            self.add_row(*row)
        return self

    def add_separator(
        self,
        text: str = "----",
        repeat_count: int | None = None,
        style: str = "dim",
    ) -> "RichTableBuilder":
        """
        Add a visual separator row.

        Args:
            text: The separator text/character.
            repeat_count: How many times to repeat the text per column.
                If None, uses the length of text.
            style: Rich style for the separator.

        Returns:
            Self for method chaining.
        """
        # Get number of columns from the table
        num_columns = len(self._table.columns)
        if repeat_count is None:
            repeat_count = len(text)

        separator_items = [text * repeat_count] * num_columns
        self._table.add_row(*separator_items, style=style)
        return self

    def add_empty_row(self, count: int = 1) -> "RichTableBuilder":
        """
        Add one or more empty rows as visual spacing.

        Args:
            count: Number of empty rows to add.

        Returns:
            Self for method chaining.
        """
        for _ in range(count):
            self.add_row(*[""] * len(self._table.columns))
        return self

    def build(self) -> Table:
        """
        Build and return the Rich Table instance.

        Returns:
            Configured Rich Table instance.
        """
        return self._table

    def render(self, console: Console | None = None, width: int = 80) -> str:
        """
        Render the table to a string.

        Args:
            console: Optional Console instance. If None, creates a new one.
            width: Terminal width for rendering (default: 80).

        Returns:
            Rendered table as a string.
        """
        if console is None:
            console = Console(file=StringIO(), force_terminal=True, width=width)

        console.print(self._table)
        return cast("StringIO", console.file).getvalue()

    def print(self, console: Console | None = None) -> None:
        """
        Print the table to console.

        Args:
            console: Optional Console instance. If None, creates a new one.
        """
        if console is None:
            console = Console()
        console.print(self._table)

    def __enter__(self) -> "RichTableBuilder":
        """Support context manager usage."""
        return self

    def __exit__(self, *args: object) -> None:
        """Print table on context exit if configured."""


def create_simple_table(
    title: str,
    columns: list[str],
    rows: list[list[Any]],
    header_style: str = "bold magenta",
    column_style: str | None = None,
) -> Table:
    """
    Create a simple table with the given columns and rows.

    Convenience function for quickly creating basic tables without
    using the builder pattern.

    Args:
        title: Table title.
        columns: List of column header strings.
        rows: List of row data (each row is a list of values).
        header_style: Style for the header row.
        column_style: Default style for all columns (optional).

    Returns:
        Configured Rich Table instance.

    Example:
        >>> table = create_simple_table(
        ...     title="Results",
        ...     columns=["Name", "Value"],
        ...     rows=[["Alice", 100], ["Bob", 200]]
        ... )
    """
    builder = RichTableBuilder(title=title, header_style=header_style)

    for col in columns:
        if column_style:
            builder.add_column(col, style=column_style)
        else:
            builder.add_column(col)

    for row in rows:
        builder.add_row(*row)

    return builder.build()


def render_table_as_string(table: Table, width: int = 80) -> str:
    """
    Render a Rich Table to a string.

    Args:
        table: The Rich Table instance.
        width: Terminal width for rendering.

    Returns:
        Rendered table as a string.
    """
    string_io = StringIO()
    console = Console(file=string_io, force_terminal=True, width=width)
    console.print(table)
    return string_io.getvalue()
