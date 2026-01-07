#!/usr/bin/env python3
"""
Heal Golden Notebook - Ensures test notebook has all required artifacts.

This script checks the golden notebook and generates any missing artifacts.
Run manually or as a nightly job - NOT per-PR (generation takes 15+ minutes).

Usage:
    python scripts/heal_golden_notebook.py

Environment:
    NOTEBOOKLM_GOLDEN_NOTEBOOK_ID - Optional, defaults to Google's demo notebook

Requirements:
    - Valid auth at ~/.notebooklm/storage_state.json
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from notebooklm import NotebookLMClient
from notebooklm.auth import load_auth_from_storage, AuthTokens
import httpx


# Google's shared demo notebook - stable, pre-seeded with content
DEFAULT_GOLDEN_NOTEBOOK_ID = "19bde485-a9c1-4809-8884-e872b2b67b44"

# Required artifacts for full test coverage
REQUIRED_ARTIFACTS = {
    "audio": "Audio Overview",
    "video": "Deep Dive Video",
    "quiz": "Quiz",
    "flashcards": "Flashcards",
    "slide_deck": "Slide Deck",
    "mind_map": "Mind Map",
    "infographic": "Infographic",
}

# Required sources (at least one needed for generation)
REQUIRED_SOURCES = {
    "text": "Sample text content for testing",
}


async def get_auth_tokens() -> AuthTokens:
    """Load auth tokens from storage."""
    cookies = load_auth_from_storage()
    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())

    async with httpx.AsyncClient() as http:
        resp = await http.get(
            "https://notebooklm.google.com/",
            headers={"Cookie": cookie_header},
            follow_redirects=True,
        )
        resp.raise_for_status()

        from notebooklm.auth import extract_csrf_from_html, extract_session_id_from_html
        csrf = extract_csrf_from_html(resp.text)
        session_id = extract_session_id_from_html(resp.text)

    return AuthTokens(cookies=cookies, csrf_token=csrf, session_id=session_id)


async def check_sources(client: NotebookLMClient, notebook_id: str) -> dict:
    """Check what sources exist in the notebook."""
    sources = await client.sources.list(notebook_id)
    return {
        "count": len(sources),
        "sources": sources,
        "has_content": len(sources) > 0,
    }


async def check_artifacts(client: NotebookLMClient, notebook_id: str) -> dict:
    """Check what artifacts exist in the notebook."""
    artifacts = await client.artifacts.list(notebook_id)

    found = {}
    missing = []

    for art_type, display_name in REQUIRED_ARTIFACTS.items():
        # Check if artifact type exists
        matching = [a for a in artifacts if art_type in a.type.lower()]
        if matching:
            found[art_type] = matching[0]
        else:
            missing.append(art_type)

    return {
        "found": found,
        "missing": missing,
        "all_artifacts": artifacts,
    }


async def ensure_sources(client: NotebookLMClient, notebook_id: str) -> bool:
    """Ensure notebook has at least one source for generation."""
    sources = await client.sources.list(notebook_id)

    if sources:
        print(f"  Sources: {len(sources)} found")
        return True

    print("  Sources: None found, adding sample text...")
    result = await client.sources.add_text(
        notebook_id,
        REQUIRED_SOURCES["text"],
        title="Test Content for Artifact Generation"
    )

    if result:
        print(f"  Sources: Added text source ({result.id})")
        return True
    else:
        print("  Sources: Failed to add text source!")
        return False


async def generate_missing_artifacts(
    client: NotebookLMClient,
    notebook_id: str,
    missing: list[str],
) -> dict:
    """Generate missing artifacts (fire-and-forget, no waiting)."""
    results = {}

    for art_type in missing:
        print(f"  Generating {art_type}...", end=" ", flush=True)

        try:
            if art_type == "audio":
                result = await client.artifacts.generate_audio(notebook_id)
            elif art_type == "video":
                result = await client.artifacts.generate_video(notebook_id)
            elif art_type == "quiz":
                result = await client.artifacts.generate_quiz(notebook_id)
            elif art_type == "flashcards":
                result = await client.artifacts.generate_flashcards(notebook_id)
            elif art_type == "slide_deck":
                result = await client.artifacts.generate_slide_deck(notebook_id)
            elif art_type == "mind_map":
                result = await client.artifacts.generate_mind_map(notebook_id)
            elif art_type == "infographic":
                result = await client.artifacts.generate_infographic(notebook_id)
            else:
                print("skipped (unknown type)")
                continue

            if result:
                print("triggered")
                results[art_type] = "triggered"
            else:
                print("failed (no result)")
                results[art_type] = "failed"

        except Exception as e:
            print(f"error: {e}")
            results[art_type] = f"error: {e}"

    return results


async def heal():
    """Main healing function."""
    notebook_id = os.environ.get("NOTEBOOKLM_GOLDEN_NOTEBOOK_ID", DEFAULT_GOLDEN_NOTEBOOK_ID)

    print("=" * 60)
    print("Golden Notebook Health Check")
    print("=" * 60)
    print(f"Notebook ID: {notebook_id}")
    if notebook_id == DEFAULT_GOLDEN_NOTEBOOK_ID:
        print("(Using Google's shared demo notebook)")
    print()

    try:
        auth = await get_auth_tokens()
    except FileNotFoundError:
        print("Error: No auth tokens found")
        print("Run 'notebooklm login' first to authenticate")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading auth: {e}")
        sys.exit(1)

    async with NotebookLMClient(auth) as client:
        # Check sources
        print("Checking sources...")
        has_sources = await ensure_sources(client, notebook_id)
        if not has_sources:
            print("\nCannot proceed without sources!")
            sys.exit(1)
        print()

        # Check artifacts
        print("Checking artifacts...")
        artifact_status = await check_artifacts(client, notebook_id)

        for art_type, display_name in REQUIRED_ARTIFACTS.items():
            if art_type in artifact_status["found"]:
                print(f"  {display_name}: exists")
            else:
                print(f"  {display_name}: MISSING")
        print()

        # Report status
        found_count = len(artifact_status["found"])
        total_count = len(REQUIRED_ARTIFACTS)
        missing = artifact_status["missing"]

        if not missing:
            print(f"Status: {found_count}/{total_count} artifacts healthy")
            print("Golden notebook is ready for testing!")
            return

        print(f"Status: {found_count}/{total_count} artifacts healthy")
        print(f"Missing: {', '.join(missing)}")
        print()

        # Generate missing artifacts
        print("Generating missing artifacts...")
        print("(Note: Generation takes 2-15+ minutes per artifact)")
        print()

        results = await generate_missing_artifacts(client, notebook_id, missing)

        print()
        print("=" * 60)
        print("Generation Summary")
        print("=" * 60)
        for art_type, status in results.items():
            print(f"  {REQUIRED_ARTIFACTS[art_type]}: {status}")

        triggered = sum(1 for s in results.values() if s == "triggered")
        print()
        print(f"Triggered {triggered} generation(s)")
        print("Run this script again in 15-30 minutes to verify completion")


def main():
    """Entry point."""
    asyncio.run(heal())


if __name__ == "__main__":
    main()
