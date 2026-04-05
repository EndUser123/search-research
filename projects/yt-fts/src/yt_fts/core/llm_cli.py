"""
LLM CLI commands for yt-fts.

Extracted from cli.py to separate LLM-specific functionality.
Contains commands for chat and summarization using LLMs.
"""
from __future__ import annotations

import click

from yt_fts.llm.summarize import SummarizeHandler
from yt_fts.utils import get_model_config
from yt_fts.utils.rich_console import get_console

console = get_console()


def _get_console():
    """Get the Rich console instance for output.

    Returns:
        Console: Rich console instance configured for yt-fts output.
    """
    return console


def _handle_command_result(result: int | None = None) -> None:
    """Handle command execution results consistently without sys.exit().

    Args:
        result: Exit code from command execution (0=success, 1=error, 130=interrupt)
                If None, no action is taken (command handles its own flow control)
    """
    if result is not None:
        # Let Click handle the exit code naturally
        # This allows proper cleanup and maintains CLI behavior
        if result != 0:
            # For non-zero exit codes, we'll raise a SystemExit with the code
            # but this is more controlled than direct sys.exit() calls
            raise SystemExit(result)
        # For success (0), we simply return and let Click complete normally


@click.command(
    name="llm",
    help="""
        Interactive LLM/RAG chat bot, needs to be run on a channel with
        Embeddings.
    """,
)
@click.argument("prompt", required=True)
@click.option(
    "-c",
    "--channel",
    default=None,
    required=True,
    help="The name or id of the channel to generate embeddings for",
)
@click.option(
    "--api-key",
    default=None,
    help="OpenAI or Gemini API key. If not provided, the script will attempt to read it from"
    " the OPENAI_API_KEY or GEMINI_API_KEY environment variable.",
)
@click.option(
    "--model",
    default=None,
    help="Model to use for embeddings. Use 'local' for local sentence-transformers models, "
    "or specify a model name like 'sentence-transformers/all-MiniLM-L6-v2'. "
    "Defaults to Gemini if API key available, otherwise local.",
)
def llm(
    prompt: str, channel: str, api_key: str | None = None, model: str | None = None
) -> None:
    """Chat with YouTube content using LLM.

    Uses RAG (Retrieval Augmented Generation) to chat with channel content.
    Requires embeddings to be generated for the channel first.

    Args:
        prompt: The user's question or prompt.
        channel: The channel name or ID to search.
        api_key: Optional API key override.
        model: Optional model name override.
    """
    # Lazy import to avoid ImportError if OpenAI is not installed
    from yt_fts.llm.chatbot import LLMHandler

    try:
        model_config = get_model_config(api_key)
        # For local embeddings, we might not have an API key, but we need one for chat
        # If embeddings are local but no API key for chat, try to get one
        if not model_config["api_key"] or model_config["api_key"] == "":
            # Try to get API key for chat completion
            chat_config = get_model_config(
                api_key
            )  # Don't pass model to get default chat config
            api_key = chat_config["api_key"]
            # Keep the embedding model as local
            model_config["embedding_model"] = model_config["embedding_model"]
            # But use the chat model and base_url from the chat config
            model_config["chat_model"] = chat_config["chat_model"]
            model_config["base_url"] = chat_config["base_url"]
            model_config["name"] = chat_config["name"]
        else:
            api_key = model_config["api_key"]
    except ValueError:
        if "local" in str(model or "").lower():
            console.print(
                """
        [bold][red]Error:[/red][/bold] Using local embeddings but no API key found for chat completion.

        Local embeddings work, but you still need an API key for chat responses.
        Set one of these environment variables:
        - export GEMINI_API_KEY=<your_key>
        - export OPENAI_API_KEY=<your_key>
                      """
            )
        else:
            console.print(
                """
        [bold][red]Error:[/red][/bold] No valid API key found.

        Set one of these environment variables:
        - export GEMINI_API_KEY=<your_key> (for Gemini)
        - export OPENAI_API_KEY=<your_key> (for OpenAI)
        - Or use --model local for local embeddings (but still need API key for chat)
                      """
            )
        msg = "API key configuration error"
        raise click.ClickException(msg)

    llm_handler = LLMHandler(api_key, channel, model_config)
    llm_handler.init_llm(prompt)

    # Success - let Click handle naturally


@click.command(name="summarize", help="summarize a youtube video")
@click.argument("video", required=True)
@click.option("--model", "-m", default=None, help="Model to use in summary ex. gpt-4o")
@click.option(
    "--api-key",
    default=None,
    help="OpenAI or Gemini API key. If not provided, the script will attempt to read it from"
    " the OPENAI_API_KEY or GEMINI_API_KEY environment variable.",
)
def summarize(video: str, model: str | None, api_key: str | None) -> None:
    """Summarize a YouTube video using LLM.

    Args:
        video: The video URL or ID to summarize.
        model: Optional model name override for summarization.
        api_key: Optional API key override.
    """
    try:
        model_config = get_model_config(api_key)
        api_key = model_config["api_key"]
        if model:
            model_config["chat_model"] = model
    except ValueError:
        console.print(
            "[red]Error:[/red] GEMINI_API_KEY environment variable not set\n"
            'To set the key run: export "GEMINI_API_KEY=<your_key>" or pass '
            "one in with --api-key\n"
            "Get your free Gemini API key from: https://makersuite.google.com/app/apikey"
        )
        msg = "API key configuration error"
        raise click.ClickException(msg)

    summarize_handler = SummarizeHandler(api_key, model_config, video)
    summarize_handler.summarize_video()
