"""Generate content CLI commands.

Commands:
    audio        Generate audio overview (podcast)
    video        Generate video overview
    slide-deck   Generate slide deck
    quiz         Generate quiz
    flashcards   Generate flashcards
    infographic  Generate infographic
    data-table   Generate data table
    mind-map     Generate mind map
    report       Generate report
"""

import click

from ..client import NotebookLMClient
from ..types import (
    AudioFormat,
    AudioLength,
    VideoFormat,
    VideoStyle,
    QuizQuantity,
    QuizDifficulty,
    InfographicOrientation,
    InfographicDetail,
    SlideDeckFormat,
    SlideDeckLength,
    ReportFormat,
)
from .helpers import (
    console,
    require_notebook,
    with_client,
    json_output_response,
    json_error_response,
)


@click.group()
def generate():
    """Generate content from notebook.

    \b
    LLM-friendly design: Describe what you want in natural language.

    \b
    Examples:
      notebooklm use nb123
      notebooklm generate video "a funny explainer for kids age 5"
      notebooklm generate audio "deep dive focusing on chapter 3"
      notebooklm generate quiz "focus on vocabulary terms"

    \b
    Types:
      audio        Audio overview (podcast)
      video        Video overview
      slide-deck   Slide deck
      quiz         Quiz
      flashcards   Flashcards
      infographic  Infographic
      data-table   Data table
      mind-map     Mind map
      report       Report (briefing-doc, study-guide, blog-post, custom)
    """
    pass


@generate.command("audio")
@click.argument("description", default="", required=False)
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option(
    "--format",
    "audio_format",
    type=click.Choice(["deep-dive", "brief", "critique", "debate"]),
    default="deep-dive",
)
@click.option(
    "--length",
    "audio_length",
    type=click.Choice(["short", "default", "long"]),
    default="default",
)
@click.option("--language", default="en")
@click.option(
    "--wait/--no-wait", default=False, help="Wait for completion (default: no-wait)"
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@with_client
def generate_audio(
    ctx,
    description,
    notebook_id,
    audio_format,
    audio_length,
    language,
    wait,
    json_output,
    client_auth,
):
    """Generate audio overview (podcast).

    \b
    Example:
      notebooklm generate audio "deep dive focusing on key themes"
      notebooklm generate audio "make it funny and casual" --format debate
    """
    nb_id = require_notebook(notebook_id)
    format_map = {
        "deep-dive": AudioFormat.DEEP_DIVE,
        "brief": AudioFormat.BRIEF,
        "critique": AudioFormat.CRITIQUE,
        "debate": AudioFormat.DEBATE,
    }
    length_map = {
        "short": AudioLength.SHORT,
        "default": AudioLength.DEFAULT,
        "long": AudioLength.LONG,
    }

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            result = await client.artifacts.generate_audio(
                nb_id,
                language=language,
                instructions=description or None,
                audio_format=format_map[audio_format],
                audio_length=length_map[audio_length],
            )

            if not result:
                if json_output:
                    json_error_response("GENERATION_FAILED", "Audio generation failed")
                else:
                    console.print("[red]Audio generation failed[/red]")
                return

            if wait:
                if not json_output:
                    console.print(
                        f"[yellow]Generating audio...[/yellow] Task: {result.get('artifact_id')}"
                    )
                status = await client.artifacts.wait_for_completion(
                    nb_id, result["artifact_id"], poll_interval=10.0
                )
            else:
                status = result

            if json_output:
                if hasattr(status, "is_complete") and status.is_complete:
                    data = {
                        "artifact_id": status.artifact_id
                        if hasattr(status, "artifact_id")
                        else None,
                        "status": "completed",
                        "url": status.url,
                    }
                    json_output_response(data)
                elif hasattr(status, "is_failed") and status.is_failed:
                    json_error_response(
                        "GENERATION_FAILED", status.error or "Audio generation failed"
                    )
                else:
                    artifact_id = (
                        status.get("artifact_id") if isinstance(status, dict) else None
                    )
                    json_output_response({"artifact_id": artifact_id, "status": "pending"})
            else:
                if hasattr(status, "is_complete") and status.is_complete:
                    console.print(f"[green]Audio ready:[/green] {status.url}")
                elif hasattr(status, "is_failed") and status.is_failed:
                    console.print(f"[red]Failed:[/red] {status.error}")
                else:
                    console.print(f"[yellow]Started:[/yellow] {status}")

    return _run()


@generate.command("video")
@click.argument("description", default="", required=False)
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option(
    "--format",
    "video_format",
    type=click.Choice(["explainer", "brief"]),
    default="explainer",
)
@click.option(
    "--style",
    type=click.Choice(
        [
            "auto",
            "classic",
            "whiteboard",
            "kawaii",
            "anime",
            "watercolor",
            "retro-print",
            "heritage",
            "paper-craft",
        ]
    ),
    default="auto",
)
@click.option("--language", default="en")
@click.option(
    "--wait/--no-wait", default=False, help="Wait for completion (default: no-wait)"
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@with_client
def generate_video(
    ctx, description, notebook_id, video_format, style, language, wait, json_output, client_auth
):
    """Generate video overview.

    \b
    Example:
      notebooklm generate video "a funny explainer for kids age 5"
      notebooklm generate video "professional presentation" --style classic
      notebooklm generate video --style kawaii
    """
    nb_id = require_notebook(notebook_id)
    format_map = {"explainer": VideoFormat.EXPLAINER, "brief": VideoFormat.BRIEF}
    style_map = {
        "auto": VideoStyle.AUTO_SELECT,
        "classic": VideoStyle.CLASSIC,
        "whiteboard": VideoStyle.WHITEBOARD,
        "kawaii": VideoStyle.KAWAII,
        "anime": VideoStyle.ANIME,
        "watercolor": VideoStyle.WATERCOLOR,
        "retro-print": VideoStyle.RETRO_PRINT,
        "heritage": VideoStyle.HERITAGE,
        "paper-craft": VideoStyle.PAPER_CRAFT,
    }

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            result = await client.artifacts.generate_video(
                nb_id,
                language=language,
                instructions=description or None,
                video_format=format_map[video_format],
                video_style=style_map[style],
            )

            if not result:
                if json_output:
                    json_error_response("GENERATION_FAILED", "Video generation failed")
                else:
                    console.print("[red]Video generation failed[/red]")
                return

            if wait and result.get("artifact_id"):
                if not json_output:
                    console.print(
                        f"[yellow]Generating video...[/yellow] Task: {result.get('artifact_id')}"
                    )
                status = await client.artifacts.wait_for_completion(
                    nb_id, result["artifact_id"], poll_interval=10.0, timeout=600.0
                )
            else:
                status = result

            if json_output:
                if hasattr(status, "is_complete") and status.is_complete:
                    data = {
                        "artifact_id": status.artifact_id
                        if hasattr(status, "artifact_id")
                        else None,
                        "status": "completed",
                        "url": status.url,
                    }
                    json_output_response(data)
                elif hasattr(status, "is_failed") and status.is_failed:
                    json_error_response(
                        "GENERATION_FAILED", status.error or "Video generation failed"
                    )
                else:
                    artifact_id = (
                        status.get("artifact_id") if isinstance(status, dict) else None
                    )
                    json_output_response({"artifact_id": artifact_id, "status": "pending"})
            else:
                if hasattr(status, "is_complete") and status.is_complete:
                    console.print(f"[green]Video ready:[/green] {status.url}")
                elif hasattr(status, "is_failed") and status.is_failed:
                    console.print(f"[red]Failed:[/red] {status.error}")
                else:
                    console.print(f"[yellow]Started:[/yellow] {status}")

    return _run()


@generate.command("slide-deck")
@click.argument("description", default="", required=False)
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option(
    "--format",
    "deck_format",
    type=click.Choice(["detailed", "presenter"]),
    default="detailed",
)
@click.option(
    "--length",
    "deck_length",
    type=click.Choice(["default", "short"]),
    default="default",
)
@click.option("--language", default="en")
@click.option(
    "--wait/--no-wait", default=False, help="Wait for completion (default: no-wait)"
)
@with_client
def generate_slide_deck(
    ctx, description, notebook_id, deck_format, deck_length, language, wait, client_auth
):
    """Generate slide deck.

    \b
    Example:
      notebooklm generate slide-deck "include speaker notes"
      notebooklm generate slide-deck "executive summary" --format presenter --length short
    """
    nb_id = require_notebook(notebook_id)
    format_map = {
        "detailed": SlideDeckFormat.DETAILED_DECK,
        "presenter": SlideDeckFormat.PRESENTER_SLIDES,
    }
    length_map = {
        "default": SlideDeckLength.DEFAULT,
        "short": SlideDeckLength.SHORT,
    }

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            result = await client.artifacts.generate_slide_deck(
                nb_id,
                language=language,
                instructions=description or None,
                slide_deck_format=format_map[deck_format],
                slide_deck_length=length_map[deck_length],
            )

            if not result:
                console.print("[red]Slide deck generation failed[/red]")
                return

            if wait and result.get("artifact_id"):
                console.print(
                    f"[yellow]Generating slide deck...[/yellow] Task: {result.get('artifact_id')}"
                )
                status = await client.artifacts.wait_for_completion(
                    nb_id, result["artifact_id"], poll_interval=10.0
                )
            else:
                status = result

            if hasattr(status, "is_complete") and status.is_complete:
                console.print(f"[green]Slide deck ready:[/green] {status.url}")
            else:
                console.print(f"[yellow]Started:[/yellow] {status}")

    return _run()


@generate.command("quiz")
@click.argument("description", default="", required=False)
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option(
    "--quantity", type=click.Choice(["fewer", "standard", "more"]), default="standard"
)
@click.option(
    "--difficulty", type=click.Choice(["easy", "medium", "hard"]), default="medium"
)
@click.option(
    "--wait/--no-wait", default=False, help="Wait for completion (default: no-wait)"
)
@with_client
def generate_quiz(ctx, description, notebook_id, quantity, difficulty, wait, client_auth):
    """Generate quiz.

    \b
    Example:
      notebooklm generate quiz "focus on vocabulary terms"
      notebooklm generate quiz "test key concepts" --difficulty hard --quantity more
    """
    nb_id = require_notebook(notebook_id)
    quantity_map = {
        "fewer": QuizQuantity.FEWER,
        "standard": QuizQuantity.STANDARD,
        "more": QuizQuantity.MORE,
    }
    difficulty_map = {
        "easy": QuizDifficulty.EASY,
        "medium": QuizDifficulty.MEDIUM,
        "hard": QuizDifficulty.HARD,
    }

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            result = await client.artifacts.generate_quiz(
                nb_id,
                instructions=description or None,
                quantity=quantity_map[quantity],
                difficulty=difficulty_map[difficulty],
            )

            if not result:
                console.print(
                    "[red]Quiz generation failed (Google may be rate limiting)[/red]"
                )
                return

            task_id = result.get("artifact_id") or (
                result[0] if isinstance(result, list) else None
            )
            if wait and task_id:
                console.print("[yellow]Generating quiz...[/yellow]")
                status = await client.artifacts.wait_for_completion(
                    nb_id, task_id, poll_interval=5.0
                )
            else:
                status = result

            if hasattr(status, "is_complete") and status.is_complete:
                console.print("[green]Quiz ready[/green]")
            elif hasattr(status, "is_failed") and status.is_failed:
                console.print(f"[red]Failed:[/red] {status.error}")
            else:
                console.print(f"[yellow]Started:[/yellow] {status}")

    return _run()


@generate.command("flashcards")
@click.argument("description", default="", required=False)
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option(
    "--quantity", type=click.Choice(["fewer", "standard", "more"]), default="standard"
)
@click.option(
    "--difficulty", type=click.Choice(["easy", "medium", "hard"]), default="medium"
)
@click.option(
    "--wait/--no-wait", default=False, help="Wait for completion (default: no-wait)"
)
@with_client
def generate_flashcards(ctx, description, notebook_id, quantity, difficulty, wait, client_auth):
    """Generate flashcards.

    \b
    Example:
      notebooklm generate flashcards "vocabulary terms only"
      notebooklm generate flashcards --quantity more --difficulty easy
    """
    nb_id = require_notebook(notebook_id)
    quantity_map = {
        "fewer": QuizQuantity.FEWER,
        "standard": QuizQuantity.STANDARD,
        "more": QuizQuantity.MORE,
    }
    difficulty_map = {
        "easy": QuizDifficulty.EASY,
        "medium": QuizDifficulty.MEDIUM,
        "hard": QuizDifficulty.HARD,
    }

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            result = await client.artifacts.generate_flashcards(
                nb_id,
                instructions=description or None,
                quantity=quantity_map[quantity],
                difficulty=difficulty_map[difficulty],
            )

            if not result:
                console.print(
                    "[red]Flashcard generation failed (Google may be rate limiting)[/red]"
                )
                return

            task_id = result.get("artifact_id") or (
                result[0] if isinstance(result, list) else None
            )
            if wait and task_id:
                console.print("[yellow]Generating flashcards...[/yellow]")
                status = await client.artifacts.wait_for_completion(
                    nb_id, task_id, poll_interval=5.0
                )
            else:
                status = result

            if hasattr(status, "is_complete") and status.is_complete:
                console.print("[green]Flashcards ready[/green]")
            elif hasattr(status, "is_failed") and status.is_failed:
                console.print(f"[red]Failed:[/red] {status.error}")
            else:
                console.print(f"[yellow]Started:[/yellow] {status}")

    return _run()


@generate.command("infographic")
@click.argument("description", default="", required=False)
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option(
    "--orientation",
    type=click.Choice(["landscape", "portrait", "square"]),
    default="landscape",
)
@click.option(
    "--detail",
    type=click.Choice(["concise", "standard", "detailed"]),
    default="standard",
)
@click.option("--language", default="en")
@click.option(
    "--wait/--no-wait", default=False, help="Wait for completion (default: no-wait)"
)
@with_client
def generate_infographic(
    ctx, description, notebook_id, orientation, detail, language, wait, client_auth
):
    """Generate infographic.

    \b
    Example:
      notebooklm generate infographic "include statistics and key findings"
      notebooklm generate infographic --orientation portrait --detail detailed
    """
    nb_id = require_notebook(notebook_id)
    orientation_map = {
        "landscape": InfographicOrientation.LANDSCAPE,
        "portrait": InfographicOrientation.PORTRAIT,
        "square": InfographicOrientation.SQUARE,
    }
    detail_map = {
        "concise": InfographicDetail.CONCISE,
        "standard": InfographicDetail.STANDARD,
        "detailed": InfographicDetail.DETAILED,
    }

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            result = await client.artifacts.generate_infographic(
                nb_id,
                language=language,
                instructions=description or None,
                orientation=orientation_map[orientation],
                detail_level=detail_map[detail],
            )

            if not result:
                console.print(
                    "[red]Infographic generation failed (Google may be rate limiting)[/red]"
                )
                return

            task_id = result.get("artifact_id") or (
                result[0] if isinstance(result, list) else None
            )
            if wait and task_id:
                console.print("[yellow]Generating infographic...[/yellow]")
                status = await client.artifacts.wait_for_completion(
                    nb_id, task_id, poll_interval=5.0
                )
            else:
                status = result

            if hasattr(status, "is_complete") and status.is_complete:
                console.print("[green]Infographic ready[/green]")
            elif hasattr(status, "is_failed") and status.is_failed:
                console.print(f"[red]Failed:[/red] {status.error}")
            else:
                console.print(f"[yellow]Started:[/yellow] {status}")

    return _run()


@generate.command("data-table")
@click.argument("description")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option("--language", default="en")
@click.option(
    "--wait/--no-wait", default=False, help="Wait for completion (default: no-wait)"
)
@with_client
def generate_data_table(ctx, description, notebook_id, language, wait, client_auth):
    """Generate data table.

    \b
    Example:
      notebooklm generate data-table "comparison of key concepts"
      notebooklm generate data-table "timeline of events"
    """
    nb_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            result = await client.artifacts.generate_data_table(
                nb_id, language=language, instructions=description
            )

            if not result:
                console.print(
                    "[red]Data table generation failed (Google may be rate limiting)[/red]"
                )
                return

            task_id = result.get("artifact_id") or (
                result[0] if isinstance(result, list) else None
            )
            if wait and task_id:
                console.print("[yellow]Generating data table...[/yellow]")
                status = await client.artifacts.wait_for_completion(
                    nb_id, task_id, poll_interval=5.0
                )
            else:
                status = result

            if hasattr(status, "is_complete") and status.is_complete:
                console.print("[green]Data table ready[/green]")
            elif hasattr(status, "is_failed") and status.is_failed:
                console.print(f"[red]Failed:[/red] {status.error}")
            else:
                console.print(f"[yellow]Started:[/yellow] {status}")

    return _run()


@generate.command("mind-map")
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@with_client
def generate_mind_map(ctx, notebook_id, client_auth):
    """Generate mind map."""
    nb_id = require_notebook(notebook_id)

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            with console.status("Generating mind map..."):
                result = await client.artifacts.generate_mind_map(nb_id)

            if result:
                console.print("[green]Mind map generated:[/green]")
                if isinstance(result, dict):
                    console.print(f"  Note ID: {result.get('note_id', '-')}")
                    mind_map = result.get("mind_map", {})
                    if isinstance(mind_map, dict):
                        console.print(f"  Root: {mind_map.get('name', '-')}")
                        console.print(
                            f"  Children: {len(mind_map.get('children', []))} nodes"
                        )
                else:
                    console.print(result)
            else:
                console.print("[yellow]No result[/yellow]")

    return _run()


@generate.command("report")
@click.argument("description", default="", required=False)
@click.option(
    "--format",
    "report_format",
    type=click.Choice(["briefing-doc", "study-guide", "blog-post", "custom"]),
    default="briefing-doc",
    help="Report format (default: briefing-doc)",
)
@click.option(
    "-n",
    "--notebook",
    "notebook_id",
    default=None,
    help="Notebook ID (uses current if not set)",
)
@click.option(
    "--wait/--no-wait", default=False, help="Wait for completion (default: no-wait)"
)
@with_client
def generate_report_cmd(ctx, description, report_format, notebook_id, wait, client_auth):
    """Generate a report (briefing doc, study guide, blog post, or custom).

    \b
    Examples:
      notebooklm generate report                              # briefing-doc (default)
      notebooklm generate report --format study-guide         # study guide
      notebooklm generate report --format blog-post           # blog post
      notebooklm generate report "Create a white paper..."    # custom report
      notebooklm generate report --format blog-post "Focus on key insights"
    """
    nb_id = require_notebook(notebook_id)

    # Smart detection: if description provided without explicit format change, treat as custom
    actual_format = report_format
    custom_prompt = None
    if description:
        if report_format == "briefing-doc":
            actual_format = "custom"
            custom_prompt = description
        else:
            custom_prompt = description

    format_map = {
        "briefing-doc": ReportFormat.BRIEFING_DOC,
        "study-guide": ReportFormat.STUDY_GUIDE,
        "blog-post": ReportFormat.BLOG_POST,
        "custom": ReportFormat.CUSTOM,
    }
    report_format_enum = format_map[actual_format]

    format_display = {
        "briefing-doc": "briefing document",
        "study-guide": "study guide",
        "blog-post": "blog post",
        "custom": "custom report",
    }[actual_format]

    async def _run():
        async with NotebookLMClient(client_auth) as client:
            result = await client.artifacts.generate_report(
                nb_id,
                report_format=report_format_enum,
                custom_prompt=custom_prompt,
            )

            if not result:
                console.print(
                    "[red]Report generation failed (Google may be rate limiting)[/red]"
                )
                return

            task_id = result.get("artifact_id")
            if wait and task_id:
                console.print(f"[yellow]Generating {format_display}...[/yellow]")
                status = await client.artifacts.wait_for_completion(
                    nb_id, task_id, poll_interval=5.0
                )
            else:
                status = result

            if hasattr(status, "is_complete") and status.is_complete:
                console.print(f"[green]{format_display.title()} ready[/green]")
            elif hasattr(status, "is_failed") and status.is_failed:
                console.print(f"[red]Failed:[/red] {status.error}")
            else:
                artifact_id = (
                    status.get("artifact_id") if isinstance(status, dict) else None
                )
                console.print(f"[yellow]Started:[/yellow] {artifact_id or status}")

    return _run()
