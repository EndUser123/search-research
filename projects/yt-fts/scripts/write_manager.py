from pathlib import Path

content = """\"\"\"
Search orchestration manager for yt-fts.
\"\"\"

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import Any

from rich.console import Console

from yt_fts.utils import get_model_config


class SearchMode:
    \"\"\"Search mode configuration.\"\"\"

    def __init__(self, fts_only: bool = False, vector_only: bool = False):
        self.fts_only = fts_only
        self.vector_only = vector_only

    @property
    def use_fts(self) -> bool:
        return not self.vector_only

    @property
    def use_vector(self) -> bool:
        return not self.fts_only

    def validate(self, console: Console) -> None:
        if self.fts_only and self.vector_only:
            console.print(
                \"[bold red]Error:[/bold red] Cannot use both --fts-only and --vector-only at the same time\"
            )
            import click
            msg = \"Invalid search mode combination\"
            raise click.ClickException(msg)


class SearchScope:
    \"\"\"Search scope configuration.\"\"\"

    def __init__(
        self,
        channel: str | None = None,
        video_id: str | None = None,
        channels: tuple[str, ...] = (),
    ):
        self.channel = channel
        self.video_id = video_id
        self.channels = channels

    @property
    def is_multi_channel(self) -> bool:
        return bool(self.channels)

    @property
    def is_single_channel(self) -> bool:
        return bool(self.channel)

    @property
    def is_video(self) -> bool:
        return bool(self.video_id)

    @property
    def is_all(self) -> bool:
        return not (self.channel or self.video_id or self.channels)

    @property
    def scope_name(self) -> str:
        if self.is_multi_channel:
            return \"multi-channel\"
        if self.is_single_channel:
            return \"channel\"
        if self.is_video:
            return \"video\"
        return \"all\"


class ProactiveSearchHandler:
    \"\"\"Handler for proactive search injection.\"\"\"

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def should_enable(self, scope: SearchScope, output_format: str) -> bool:
        if scope.is_multi_channel:
            self.console.print(
                \"[yellow]Warning:[/yellow] Proactive search not supported with --channels flag\"
            )
            return False
        return True

    def get_proactive_scope(self, scope: SearchScope) -> str:
        if scope.is_single_channel:
            return \"channel\"
        if scope.is_video:
            return \"video\"
        return \"all\"

    def execute(self, query: str, scope: SearchScope, output_format: str, limit: int) -> dict:
        from yt_fts.lib.search import ProactiveSearchInjection

        injector = ProactiveSearchInjection()
        proactive_scope = self.get_proactive_scope(scope)
        proactive_channel = scope.channel if scope.is_single_channel else None

        context = injector.get_injection_context(
            query=query,
            scope=proactive_scope,
            channel=proactive_channel,
            video_id=scope.video_id if scope.is_video else None,
            limit=limit,
        )

        self._display_context(context, output_format, query)
        return context

    def _display_context(self, context: dict, output_format: str, query: str) -> None:
        if context[\"should_inject\"]:
            self.console.print(
                f\"\n[bold cyan]Proactive Search:[/bold cyan] Detected '{context['intent']}' intent\"
            )
            if context[\"results\"] and len(context[\"results\"]) > 0:
                self.console.print(
                    f\"[green]Found {len(context['results'])} result(s)[/green]\"
                )
                if output_format == \"json\":
                    self.console.print(\"\n[bold]Formatted Search Results for LLM:[/bold]\")
                    self.console.print(context[\"formatted_for_llm\"])
                else:
                    self.console.print(\"[dim](Use --format json to see results)[/dim]\")
            else:
                self.console.print(\"[yellow]No results found[/yellow]\")
            self.console.print()
        else:
            self.console.print(
                f\"[dim]Proactive Search:[/dim] Intent is '{context['intent']}', skipping\n\"
            )


class VectorSearchConfig:
    \"\"\"Configuration for vector search operations.\"\"\"

    def __init__(self, api_key: str | None = None, console: Console | None = None):
        self.api_key = api_key
        self.console = console or Console()
        self._resolved_key: str | None = None

    def get_api_key(self) -> str:
        if self._resolved_key:
            return self._resolved_key

        key = self.api_key
        if not key:
            try:
                model_config = get_model_config()
                key = model_config[\"api_key\"]
            except ValueError:
                self.console.print(
                    \"[bold red]Error:[/bold red] GEMINI_API_KEY not set\"
                )
                import click
                msg = \"API key required\"
                raise click.ClickException(msg)

        self._resolved_key = key
        return key

    def ensure_embeddings(self, channel_id: str, api_key: str) -> bool:
        from yt_fts.llm.auto_embeddings import auto_ensure_embeddings_for_vsearch

        if not auto_ensure_embeddings_for_vsearch(channel_id, api_key):
            self.console.print(\"[red]Error:[/red] Embeddings generation failed.\")
            return False
        return True


def create_multi_channel_result(result: dict[str, Any]) -> Any:
    return type(
        \"MultiChannelResult\",
        (),
        {
            \"video_id\": result.get(\"video_id\", \"\"),
            \"video_title\": result.get(\"title\", \"\"),
            \"channel_id\": result.get(\"channel_id\", \"\"),
            \"channel_name\": result.get(\"channel_name\", \"\"),
            \"start_time\": result.get(\"start_time\", \"\"),
            \"text\": result.get(\"text\", \"\"),
            \"link\": result.get(\"link\", \"\"),
            \"result_type\": \"fts\",
            \"timestamp\": result.get(\"start_time\", \"\"),
            \"relevance_score\": 1.0,
        },
    )()


def create_vector_result(result: dict[str, Any], channel_id: str) -> Any:
    from yt_fts.core.search_cli import _time_to_seconds

    return type(
        \"MultiChannelResult\",
        (),
        {
            \"video_id\": result[\"video_id\"],
            \"video_title\": result[\"video_title\"],
            \"channel_id\": channel_id,
            \"channel_name\": result.get(\"channel_name\", \"\"),
            \"start_time\": result[\"start_time\"],
            \"text\": result.get(\"text\", \"\"),
            \"link\": f\"https://youtu.be/{result['video_id']}?t={_time_to_seconds(result['start_time'])}\",
            \"relevance_score\": result[\"similarity\"],
            \"result_type\": \"vector\",
            \"timestamp\": result.get(\"start_time\", \"\"),
        },
    )()
"""

dest = Path("src/yt_fts/core/search_manager.py")
dest.write_text(content, encoding="utf-8")
print(f"Created {dest}")
