"""Note management CLI commands.

Commands:
    list    List all notes
    create  Create a new note
    get     Get note content
    save    Update note content
    rename  Rename a note
    delete  Delete a note
"""

import click
from rich.table import Table

from ..client import NotebookLMClient
from .helpers import (
    console,
    require_notebook,
    with_client,
)


@click.group()
def note():
    """Note management commands.

    \b
    Commands:
      list    List all notes
      create  Create a new note
      get     Get note content
      save    Update note content
      delete  Delete a note
    """
    pass


def _parse_note(n: list) -> tuple[str, str, str]:
    """Parse note structure and return (note_id, title, content).

    GET_NOTES structure: [note_id, [note_id, content, metadata, None, title]]
    - n[0] = note ID
    - n[1][1] = content (or n[1] if string - old format)
    - n[1][4] = title
    """
    note_id = str(n[0]) if len(n) > 0 and n[0] else "-"
    content = ""
    title = "Untitled"

    if len(n) > 1:
        if isinstance(n[1], str):
            # Old format: [note_id, content]
            content = n[1]
        elif isinstance(n[1], list):
            # New format: [note_id, [note_id, content, metadata, None, title]]
            inner = n[1]
            if len(inner) > 1 and isinstance(inner[1], str):
                content = inner[1]
            if len(inner) > 4 and isinstance(inner[4], str):
                title = inner[4]

    return note_id, title, content


@note.command("list")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@with_client
def note_list(ctx, notebook_id, client_auth):
    """List all notes in a notebook."""
    nb_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            notes = await client.notes.list(nb_id)

            if not notes:
                console.print("[yellow]No notes found[/yellow]")
                return

            table = Table(title=f"Notes in {nb_id}")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Preview", style="dim", max_width=50)

            for n in notes:
                if isinstance(n, list) and len(n) > 0:
                    note_id, title, content = _parse_note(n)
                    preview = content[:50]
                    table.add_row(
                        note_id, title, preview + "..." if len(content) > 50 else preview
                    )

            console.print(table)

    return _run()


@note.command("create")
@click.argument("content", default="", required=False)
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option("-t", "--title", default="New Note", help="Note title")
@with_client
def note_create(ctx, content, notebook_id, title, client_auth):
    """Create a new note.

    \b
    Examples:
      notebooklm note create                        # Empty note with default title
      notebooklm note create "My note content"     # Note with content
      notebooklm note create "Content" -t "Title"  # Note with title and content
    """
    nb_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            result = await client.notes.create(nb_id, title, content)

            if result:
                console.print("[green]Note created[/green]")
                console.print(result)
            else:
                console.print("[yellow]Creation may have failed[/yellow]")

    return _run()


@note.command("get")
@click.argument("note_id")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@with_client
def note_get(ctx, note_id, notebook_id, client_auth):
    """Get note content."""
    nb_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            n = await client.notes.get(nb_id, note_id)

            if n:
                if isinstance(n, list) and len(n) > 0:
                    nid, title, content = _parse_note(n)
                    console.print(f"[bold cyan]ID:[/bold cyan] {nid}")
                    console.print(f"[bold cyan]Title:[/bold cyan] {title}")
                    console.print(f"[bold cyan]Content:[/bold cyan]\n{content}")
                else:
                    console.print(n)
            else:
                console.print("[yellow]Note not found[/yellow]")

    return _run()


@note.command("save")
@click.argument("note_id")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option("--title", help="New title")
@click.option("--content", help="New content")
@with_client
def note_save(ctx, note_id, notebook_id, title, content, client_auth):
    """Update note content."""
    if not title and not content:
        console.print("[yellow]Provide --title and/or --content[/yellow]")
        return

    nb_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            await client.notes.update(nb_id, note_id, content=content, title=title)
            console.print(f"[green]Note updated:[/green] {note_id}")

    return _run()


@note.command("rename")
@click.argument("note_id")
@click.argument("new_title")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@with_client
def note_rename(ctx, note_id, new_title, notebook_id, client_auth):
    """Rename a note."""
    nb_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            # Get current note to preserve content
            n = await client.notes.get(nb_id, note_id)
            if not n:
                console.print("[yellow]Note not found[/yellow]")
                return

            # Extract content from note structure
            content = ""
            if len(n) > 1 and isinstance(n[1], list):
                inner = n[1]
                if len(inner) > 1 and isinstance(inner[1], str):
                    content = inner[1]

            await client.notes.update(nb_id, note_id, content=content, title=new_title)
            console.print(f"[green]Note renamed:[/green] {new_title}")

    return _run()


@note.command("delete")
@click.argument("note_id")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@with_client
def note_delete(ctx, note_id, notebook_id, yes, client_auth):
    """Delete a note."""
    if not yes and not click.confirm(f"Delete note {note_id}?"):
        return

    nb_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            await client.notes.delete(nb_id, note_id)
            console.print(f"[green]Deleted note:[/green] {note_id}")

    return _run()
