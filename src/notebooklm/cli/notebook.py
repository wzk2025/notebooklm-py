"""Notebook management CLI commands.

Commands:
    list       List all notebooks
    create     Create a new notebook
    delete     Delete a notebook
    rename     Rename a notebook
    share      Share a notebook
    summary    Get notebook summary
    analytics  Get notebook analytics
    history    Get conversation history
    ask        Ask a question
    configure  Configure chat settings
    research   Start a research session
    featured   List featured notebooks
"""

import click
from rich.table import Table

from ..client import NotebookLMClient
from ..types import ChatMode
from .helpers import (
    console,
    run_async,
    get_client,
    get_current_notebook,
    set_current_notebook,
    get_current_conversation,
    set_current_conversation,
    clear_context,
    require_notebook,
    with_client,
    json_output_response,
)
from ..auth import AuthTokens


@click.group()
def notebook():
    """Notebook management commands.

    \b
    Commands:
      list       List all notebooks
      create     Create a new notebook
      delete     Delete a notebook
      rename     Rename a notebook
      share      Share a notebook
      ask        Ask a question
      summary    Get notebook summary
      analytics  Get notebook analytics
      history    Get conversation history
    """
    pass


@notebook.command("list")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@with_client
def notebook_list(ctx, json_output, client_auth):
    """List all notebooks."""
    async def _run():
        async with NotebookLMClient(client_auth) as client:
            notebooks = await client.notebooks.list()

            if json_output:
                data = {
                    "notebooks": [
                        {
                            "index": i,
                            "id": nb.id,
                            "title": nb.title,
                            "is_owner": nb.is_owner,
                            "created_at": nb.created_at.isoformat()
                            if nb.created_at
                            else None,
                        }
                        for i, nb in enumerate(notebooks, 1)
                    ],
                    "count": len(notebooks),
                }
                json_output_response(data)
                return

            table = Table(title="Notebooks")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Owner")
            table.add_column("Created", style="dim")

            for nb in notebooks:
                created = nb.created_at.strftime("%Y-%m-%d") if nb.created_at else "-"
                owner_status = "Owner" if nb.is_owner else "Shared"
                table.add_row(nb.id, nb.title, owner_status, created)

            console.print(table)

    return _run()


@notebook.command("create")
@click.argument("title")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@with_client
def notebook_create(ctx, title, json_output, client_auth):
    """Create a new notebook."""
    async def _run():
        async with NotebookLMClient(client_auth) as client:
            nb = await client.notebooks.create(title)

            if json_output:
                data = {
                    "notebook": {
                        "id": nb.id,
                        "title": nb.title,
                        "created_at": nb.created_at.isoformat()
                        if nb.created_at
                        else None,
                    }
                }
                json_output_response(data)
                return

            console.print(f"[green]Created notebook:[/green] {nb.id} - {nb.title}")

    return _run()


@notebook.command("delete")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@with_client
def notebook_delete(ctx, notebook_id, yes, client_auth):
    """Delete a notebook."""
    notebook_id = require_notebook(notebook_id)
    if not yes and not click.confirm(f"Delete notebook {notebook_id}?"):
        return

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            success = await client.notebooks.delete(notebook_id)
            if success:
                console.print(f"[green]Deleted notebook:[/green] {notebook_id}")
                # Clear context if we deleted the current notebook
                if get_current_notebook() == notebook_id:
                    clear_context()
                    console.print("[dim]Cleared current notebook context[/dim]")
            else:
                console.print("[yellow]Delete may have failed[/yellow]")

    return _run()


@notebook.command("rename")
@click.argument("new_title")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@with_client
def notebook_rename(ctx, new_title, notebook_id, client_auth):
    """Rename a notebook."""
    notebook_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            await client.notebooks.rename(notebook_id, new_title)
            console.print(f"[green]Renamed notebook:[/green] {notebook_id}")
            console.print(f"[bold]New title:[/bold] {new_title}")

    return _run()


@notebook.command("share")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@with_client
def notebook_share(ctx, notebook_id, client_auth):
    """Configure notebook sharing."""
    notebook_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            result = await client.notebooks.share(notebook_id)
            if result:
                console.print("[green]Sharing configured[/green]")
                console.print(result)
            else:
                console.print("[yellow]No sharing info returned[/yellow]")

    return _run()


@notebook.command("summary")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option("--topics", is_flag=True, help="Include suggested topics")
@with_client
def notebook_summary(ctx, notebook_id, topics, client_auth):
    """Get notebook summary with AI-generated insights.

    \b
    Examples:
      notebooklm notebook summary              # Summary only
      notebooklm notebook summary --topics     # With suggested topics
    """
    notebook_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            description = await client.notebooks.get_description(notebook_id)
            if description and description.summary:
                console.print("[bold cyan]Summary:[/bold cyan]")
                console.print(description.summary)

                if topics and description.suggested_topics:
                    console.print("\n[bold cyan]Suggested Topics:[/bold cyan]")
                    for i, topic in enumerate(description.suggested_topics, 1):
                        console.print(f"  {i}. {topic.question}")
            else:
                console.print("[yellow]No summary available[/yellow]")

    return _run()


@notebook.command("analytics")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@with_client
def notebook_analytics(ctx, notebook_id, client_auth):
    """Get notebook analytics."""
    notebook_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            analytics = await client.notebooks.get_analytics(notebook_id)
            if analytics:
                console.print("[bold cyan]Analytics:[/bold cyan]")
                console.print(analytics)
            else:
                console.print("[yellow]No analytics available[/yellow]")

    return _run()


@notebook.command("history")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option("--limit", "-l", default=20, help="Number of messages")
@click.option("--clear", is_flag=True, help="Clear local conversation cache")
@with_client
def notebook_history(ctx, notebook_id, limit, clear, client_auth):
    """Get conversation history or clear local cache.

    \b
    Example:
      notebooklm notebook history              # Show history for current notebook
      notebooklm notebook history -n nb123     # Show history for specific notebook
      notebooklm notebook history --clear      # Clear local cache
    """
    async def _run():
        async with NotebookLMClient(client_auth) as client:
            if clear:
                result = client.chat.clear_cache()
                if result:
                    console.print("[green]Local conversation cache cleared[/green]")
                else:
                    console.print("[yellow]No cache to clear[/yellow]")
                return

            nb_id = require_notebook(notebook_id)
            history = await client.chat.get_history(nb_id, limit=limit)

            if history:
                console.print("[bold cyan]Conversation History:[/bold cyan]")
                try:
                    conversations = history[0] if history else []
                    if conversations:
                        table = Table()
                        table.add_column("#", style="dim")
                        table.add_column("Conversation ID", style="cyan")
                        for i, conv in enumerate(conversations, 1):
                            conv_id = (
                                conv[0] if isinstance(conv, list) and conv else str(conv)
                            )
                            table.add_row(str(i), conv_id)
                        console.print(table)
                        console.print(
                            "\n[dim]Note: Only conversation IDs available. Use 'notebooklm ask -c <id>' to continue.[/dim]"
                        )
                    else:
                        console.print("[yellow]No conversations found[/yellow]")
                except (IndexError, TypeError):
                    console.print(history)
            else:
                console.print("[yellow]No conversation history[/yellow]")

    return _run()


@notebook.command("ask")
@click.argument("question")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option(
    "--conversation-id", "-c", default=None, help="Continue a specific conversation"
)
@click.option(
    "--new", "new_conversation", is_flag=True, help="Start a new conversation"
)
@with_client
def notebook_ask(ctx, question, notebook_id, conversation_id, new_conversation, client_auth):
    """Ask a notebook a question.

    By default, continues the last conversation. Use --new to start fresh.

    \b
    Example:
      notebooklm notebook ask "what are the main themes?"
      notebooklm notebook ask --new "start fresh question"
      notebooklm notebook ask -c <id> "continue this one"
    """
    nb_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            effective_conv_id = None
            if new_conversation:
                effective_conv_id = None
                console.print("[dim]Starting new conversation...[/dim]")
            elif conversation_id:
                effective_conv_id = conversation_id
            else:
                effective_conv_id = get_current_conversation()
                if not effective_conv_id:
                    try:
                        history = await client.chat.get_history(nb_id, limit=1)
                        if history and history[0]:
                            last_conv = history[0][-1]
                            effective_conv_id = (
                                last_conv[0]
                                if isinstance(last_conv, list)
                                else str(last_conv)
                            )
                            console.print(
                                f"[dim]Continuing conversation {effective_conv_id[:8]}...[/dim]"
                            )
                    except Exception:
                        pass

            result = await client.chat.ask(
                nb_id, question, conversation_id=effective_conv_id
            )

            if result.get("conversation_id"):
                set_current_conversation(result["conversation_id"])

            console.print("[bold cyan]Answer:[/bold cyan]")
            console.print(result["answer"])
            if result.get("is_follow_up"):
                console.print(
                    f"\n[dim]Conversation: {result['conversation_id']} (turn {result.get('turn_number', '?')})[/dim]"
                )
            else:
                console.print(f"\n[dim]New conversation: {result['conversation_id']}[/dim]")

    return _run()


@notebook.command("configure")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option(
    "--mode",
    "chat_mode",
    type=click.Choice(["default", "learning-guide", "concise", "detailed"]),
    default=None,
    help="Predefined chat mode",
)
@click.option(
    "--persona", default=None, help="Custom persona prompt (up to 10,000 chars)"
)
@click.option(
    "--response-length",
    type=click.Choice(["default", "longer", "shorter"]),
    default=None,
    help="Response verbosity",
)
@with_client
def notebook_configure(ctx, notebook_id, chat_mode, persona, response_length, client_auth):
    """Configure chat persona and response settings.

    \b
    Modes:
      default        General purpose (default behavior)
      learning-guide Educational focus with learning-oriented responses
      concise        Brief, to-the-point responses
      detailed       Verbose, comprehensive responses

    \b
    Examples:
      notebooklm notebook configure --mode learning-guide
      notebooklm notebook configure --persona "Act as a chemistry tutor"
      notebooklm notebook configure --mode detailed --response-length longer
    """
    nb_id = require_notebook(notebook_id)

    async def _run():
        from ..rpc import ChatGoal, ChatResponseLength

        async with NotebookLMClient(client_auth) as client:
            if chat_mode:
                mode_map = {
                    "default": ChatMode.DEFAULT,
                    "learning-guide": ChatMode.LEARNING_GUIDE,
                    "concise": ChatMode.CONCISE,
                    "detailed": ChatMode.DETAILED,
                }
                await client.chat.set_mode(nb_id, mode_map[chat_mode])
                console.print(f"[green]Chat mode set to: {chat_mode}[/green]")
                return

            goal = ChatGoal.CUSTOM if persona else None
            length = None
            if response_length:
                length_map = {
                    "default": ChatResponseLength.DEFAULT,
                    "longer": ChatResponseLength.LONGER,
                    "shorter": ChatResponseLength.SHORTER,
                }
                length = length_map[response_length]

            await client.chat.configure(
                nb_id, goal=goal, response_length=length, custom_prompt=persona
            )

            parts = []
            if persona:
                parts.append(
                    f'persona: "{persona[:50]}..."'
                    if len(persona) > 50
                    else f'persona: "{persona}"'
                )
            if response_length:
                parts.append(f"response length: {response_length}")
            result = (
                f"Chat configured: {', '.join(parts)}"
                if parts
                else "Chat configured (no changes)"
            )
            console.print(f"[green]{result}[/green]")

    return _run()


@notebook.command("research")
@click.argument("query")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option("--source", type=click.Choice(["web", "drive"]), default="web")
@click.option("--mode", type=click.Choice(["fast", "deep"]), default="fast")
@click.option("--import-all", is_flag=True, help="Import all found sources")
@with_client
def notebook_research(ctx, query, notebook_id, source, mode, import_all, client_auth):
    """Start a research session."""
    notebook_id = require_notebook(notebook_id)

    async def _run():
        import time

        async with NotebookLMClient(client_auth) as client:
            console.print(
                f"[yellow]Starting {mode} research on {source}...[/yellow]"
            )
            result = await client.research.start(notebook_id, query, source, mode)
            if not result:
                console.print("[red]Research failed to start[/red]")
                raise SystemExit(1)

            task_id = result["task_id"]
            console.print(f"[dim]Task ID: {task_id}[/dim]")

            status = None
            for _ in range(60):
                status = await client.research.poll(notebook_id)
                if status.get("status") == "completed":
                    break
                elif status.get("status") == "no_research":
                    console.print("[red]Research failed to start[/red]")
                    raise SystemExit(1)
                time.sleep(5)
            else:
                status = {"status": "timeout"}

            if status.get("status") == "completed":
                sources = status.get("sources", [])
                console.print(f"\n[green]Found {len(sources)} sources[/green]")

                if import_all and sources and task_id:
                    imported = await client.research.import_sources(
                        notebook_id, task_id, sources
                    )
                    console.print(f"[green]Imported {len(imported)} sources[/green]")
            else:
                console.print(f"[yellow]Status: {status.get('status', 'unknown')}[/yellow]")

    return _run()


@notebook.command("featured")
@click.option("--limit", "-n", default=20, help="Number of notebooks")
@with_client
def notebook_featured(ctx, limit, client_auth):
    """List featured/public notebooks."""
    async def _run():
        async with NotebookLMClient(client_auth) as client:
            projects = await client.notebooks.list_featured(page_size=limit)

            if not projects:
                console.print("[yellow]No featured notebooks found[/yellow]")
                return

            table = Table(title="Featured Notebooks")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="green")

            for proj in projects:
                if isinstance(proj, list) and len(proj) > 0:
                    table.add_row(
                        str(proj[0] or "-"), str(proj[1] if len(proj) > 1 else "-")
                    )

            console.print(table)

    return _run()
