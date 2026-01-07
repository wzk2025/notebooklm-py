"""Notebook management CLI commands.

Commands:
    list       List all notebooks
    create     Create a new notebook
    delete     Delete a notebook
    rename     Rename a notebook
    share      Configure notebook sharing
    featured   List featured/public notebooks
    summary    Get notebook summary with AI-generated insights
    analytics  Get notebook analytics
"""

import click
from rich.table import Table

from ..client import NotebookLMClient
from .helpers import (
    console,
    require_notebook,
    with_client,
    json_output_response,
    get_current_notebook,
    clear_context,
    resolve_notebook_id,
)


def register_notebook_commands(cli):
    """Register notebook commands on the main CLI group."""

    @cli.command("list")
    @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
    @with_client
    def list_cmd(ctx, json_output, client_auth):
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

    @cli.command("create")
    @click.argument("title")
    @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
    @with_client
    def create_cmd(ctx, title, json_output, client_auth):
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

    @cli.command("delete")
    @click.option(
        "-n",
        "--notebook",
        "notebook_id",
        default=None,
        help="Notebook ID (uses current if not set). Supports partial IDs.",
    )
    @click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
    @with_client
    def delete_cmd(ctx, notebook_id, yes, client_auth):
        """Delete a notebook.

        Supports partial IDs - 'notebooklm delete -n abc' matches 'abc123...'
        """
        notebook_id = require_notebook(notebook_id)

        async def _run():
            async with NotebookLMClient(client_auth) as client:
                # Resolve partial ID to full ID
                resolved_id = await resolve_notebook_id(client, notebook_id)

                # Confirm after resolution so user sees the full ID
                if not yes and not click.confirm(f"Delete notebook {resolved_id}?"):
                    return

                success = await client.notebooks.delete(resolved_id)
                if success:
                    console.print(f"[green]Deleted notebook:[/green] {resolved_id}")
                    # Clear context if we deleted the current notebook
                    if get_current_notebook() == resolved_id:
                        clear_context()
                        console.print("[dim]Cleared current notebook context[/dim]")
                else:
                    console.print("[yellow]Delete may have failed[/yellow]")

        return _run()

    @cli.command("rename")
    @click.argument("new_title")
    @click.option(
        "-n",
        "--notebook",
        "notebook_id",
        default=None,
        help="Notebook ID (uses current if not set). Supports partial IDs.",
    )
    @with_client
    def rename_cmd(ctx, new_title, notebook_id, client_auth):
        """Rename a notebook.

        NOTEBOOK_ID supports partial matching (e.g., 'abc' matches 'abc123...').
        """
        notebook_id = require_notebook(notebook_id)

        async def _run():
            async with NotebookLMClient(client_auth) as client:
                resolved_id = await resolve_notebook_id(client, notebook_id)
                await client.notebooks.rename(resolved_id, new_title)
                console.print(f"[green]Renamed notebook:[/green] {resolved_id}")
                console.print(f"[bold]New title:[/bold] {new_title}")

        return _run()

    @cli.command("share")
    @click.option(
        "-n",
        "--notebook",
        "notebook_id",
        default=None,
        help="Notebook ID (uses current if not set). Supports partial IDs.",
    )
    @with_client
    def share_cmd(ctx, notebook_id, client_auth):
        """Configure notebook sharing.

        NOTEBOOK_ID supports partial matching (e.g., 'abc' matches 'abc123...').
        """
        notebook_id = require_notebook(notebook_id)

        async def _run():
            async with NotebookLMClient(client_auth) as client:
                resolved_id = await resolve_notebook_id(client, notebook_id)
                result = await client.notebooks.share(resolved_id)
                if result:
                    console.print("[green]Sharing configured[/green]")
                    console.print(result)
                else:
                    console.print("[yellow]No sharing info returned[/yellow]")

        return _run()

    @cli.command("featured")
    @click.option("--limit", "-n", default=20, help="Number of notebooks")
    @with_client
    def featured_cmd(ctx, limit, client_auth):
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

    @cli.command("summary")
    @click.option(
        "-n",
        "--notebook",
        "notebook_id",
        default=None,
        help="Notebook ID (uses current if not set). Supports partial IDs.",
    )
    @click.option("--topics", is_flag=True, help="Include suggested topics")
    @with_client
    def summary_cmd(ctx, notebook_id, topics, client_auth):
        """Get notebook summary with AI-generated insights.

        NOTEBOOK_ID supports partial matching (e.g., 'abc' matches 'abc123...').

        \b
        Examples:
          notebooklm summary              # Summary only
          notebooklm summary --topics     # With suggested topics
        """
        notebook_id = require_notebook(notebook_id)

        async def _run():
            async with NotebookLMClient(client_auth) as client:
                resolved_id = await resolve_notebook_id(client, notebook_id)
                description = await client.notebooks.get_description(resolved_id)
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

    @cli.command("analytics")
    @click.option(
        "-n",
        "--notebook",
        "notebook_id",
        default=None,
        help="Notebook ID (uses current if not set). Supports partial IDs.",
    )
    @with_client
    def analytics_cmd(ctx, notebook_id, client_auth):
        """Get notebook analytics.

        NOTEBOOK_ID supports partial matching (e.g., 'abc' matches 'abc123...').
        """
        notebook_id = require_notebook(notebook_id)

        async def _run():
            async with NotebookLMClient(client_auth) as client:
                resolved_id = await resolve_notebook_id(client, notebook_id)
                analytics = await client.notebooks.get_analytics(resolved_id)
                if analytics:
                    console.print("[bold cyan]Analytics:[/bold cyan]")
                    console.print(analytics)
                else:
                    console.print("[yellow]No analytics available[/yellow]")

        return _run()
