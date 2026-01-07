# Smart Download CLI Design

**Date:** 2026-01-07
**Status:** Approved
**Author:** Claude Code (brainstorming session)

## Overview

Redesign the `notebooklm download` command to auto-detect artifact types, support batch downloads, and provide a better user experience.

## Current State

```bash
# Current: requires explicit type
notebooklm download audio ./output.mp3
notebooklm download video ./output.mp4
notebooklm download slides ./output.pdf
notebooklm download infographic ./output.png
```

**Problems:**
- User must know artifact type
- User must specify output filename
- No batch download support
- No way to download all artifacts at once

## Proposed Design

### Command Syntax

```bash
# Smart single download (auto-detect type)
notebooklm download <artifact_id>

# Smart single with custom output
notebooklm download <artifact_id> -o <path>

# Batch download
notebooklm download <id1> <id2> <id3>

# Download all artifacts
notebooklm download --all

# With output directory
notebooklm download --all -o ./downloads

# Preview mode
notebooklm download --all --dry-run

# Force overwrite existing files
notebooklm download --all --overwrite
```

### Auto-Detection Logic

The system looks up the artifact by ID and determines:
1. Artifact type (audio, video, slides, infographic, quiz, etc.)
2. Whether it's downloadable
3. Appropriate file extension

```
Artifact ID → Lookup → Type Detection → Download or Error
```

### Downloadable vs Non-Downloadable

| Type | Downloadable | Extension | Notes |
|------|--------------|-----------|-------|
| Audio (podcast) | ✓ | .mp3 | |
| Video | ✓ | .mp4 | |
| Slides | ✓ | .pdf | |
| Infographic | ✓ | .png | |
| Quiz | ✗ | - | View in NotebookLM UI |
| Flashcards | ✗ | - | View in NotebookLM UI |
| Mind Map | ✗ | - | View in NotebookLM UI |
| Data Table | ✗ | - | Export to Google Sheets |
| Report | ✗ | - | Export to Google Docs |

### Filename Generation

**Default behavior:** Use artifact title, sanitized for filesystem safety.

```python
def sanitize_filename(title: str) -> str:
    """Convert artifact title to safe filename."""
    # Remove/replace unsafe characters
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace spaces with underscores or hyphens
    safe = safe.replace(' ', '_')
    # Truncate if too long
    return safe[:200]
```

**Examples:**
- "Research Overview" → `Research_Overview.mp3`
- "Deep Dive: AI Ethics" → `Deep_Dive_AI_Ethics.mp4`
- "My Report (Draft)" → `My_Report_Draft.pdf`

### Output Behavior

| Command | Output Location |
|---------|-----------------|
| `download <id>` | Current directory, title-based name |
| `download <id> -o file.mp3` | Specified file path |
| `download <id> -o ./dir/` | Specified directory, title-based name |
| `download id1 id2` | Current directory, title-based names |
| `download --all` | Current directory, title-based names |
| `download --all -o ./dir` | Specified directory, title-based names |

### Conflict Handling

When a file already exists:

**Default:** Skip with warning
```
⚠ Skipped: Research_Overview.mp3 (already exists, use --overwrite)
```

**With `--overwrite`:** Replace existing files
```
✓ Overwrote: Research_Overview.mp3
```

### Error Handling

#### Single Download - Non-Downloadable

```bash
$ notebooklm download abc123  # abc123 is a quiz
✗ Cannot download: "Chapter Quiz" is a Quiz
  Quizzes are not downloadable. View in NotebookLM UI instead.
Exit code: 1
```

#### Single Download - Not Found

```bash
$ notebooklm download xyz789
✗ Artifact not found: xyz789
Exit code: 1
```

#### Batch Download - Mixed Results

```bash
$ notebooklm download id1 id2 id3  # id2 is flashcards
✓ Downloaded: Research_Overview.mp3
⚠ Skipped: Study Cards (flashcards - not downloadable)
✓ Downloaded: Summary.pdf

Downloaded: 2 | Skipped: 1 non-downloadable
Exit code: 0
```

#### Download All - Mixed Results

```bash
$ notebooklm download --all
✓ Downloaded: Research_Overview.mp3
✓ Downloaded: Deep_Dive.mp4
⚠ Skipped: Chapter Quiz (quiz - not downloadable)
⚠ Skipped: Study Cards (flashcards - not downloadable)
⚠ Skipped: Concept Map (mind-map - not downloadable)
✓ Downloaded: Summary.pdf

Downloaded: 3 | Skipped: 3 non-downloadable
Exit code: 0
```

### Dry Run Mode

Preview what would be downloaded without actually downloading:

```bash
$ notebooklm download --all --dry-run
Downloadable:
  ✓ Research Overview (audio) → Research_Overview.mp3
  ✓ Deep Dive (video) → Deep_Dive.mp4
  ✓ Summary (slides) → Summary.pdf

Not downloadable:
  ✗ Chapter Quiz (quiz)
  ✗ Study Cards (flashcards)
  ✗ Concept Map (mind-map)

Would download: 3 files
```

### Exit Codes

| Scenario | Exit Code |
|----------|-----------|
| All downloads succeeded | 0 |
| Some downloads, some non-downloadable skipped | 0 |
| Single artifact not downloadable | 1 |
| Single artifact not found | 1 |
| All artifacts not downloadable | 1 |
| Download failed (network error) | 1 |
| No artifacts exist | 1 |

### JSON Output

All commands support `--json` for machine-readable output:

```bash
$ notebooklm download --all --json
```

```json
{
  "downloaded": [
    {"id": "abc123", "title": "Research Overview", "type": "audio", "path": "Research_Overview.mp3"},
    {"id": "def456", "title": "Deep Dive", "type": "video", "path": "Deep_Dive.mp4"}
  ],
  "skipped": [
    {"id": "ghi789", "title": "Chapter Quiz", "type": "quiz", "reason": "not_downloadable"}
  ],
  "failed": [],
  "summary": {
    "downloaded": 2,
    "skipped": 1,
    "failed": 0
  }
}
```

## CLI Options Summary

```
notebooklm download [OPTIONS] [ARTIFACT_IDS]...

Arguments:
  ARTIFACT_IDS    One or more artifact IDs to download (optional if --all)

Options:
  --all           Download all downloadable artifacts in current notebook
  -o, --output    Output path (file for single, directory for multiple)
  --overwrite     Overwrite existing files (default: skip)
  --dry-run       Preview without downloading
  -n, --notebook  Notebook ID (uses current context if not specified)
  --json          Output in JSON format
  --help          Show help message
```

## Backward Compatibility

The existing explicit commands remain available for users who prefer them:

```bash
# These still work
notebooklm download audio ./output.mp3
notebooklm download video ./output.mp4 -a <artifact_id>
```

The new smart download is additive, not a breaking change.

## Implementation Notes

### Artifact Type Detection

Use existing `artifact list` functionality to:
1. Fetch artifact by ID
2. Check `artifact_type` field
3. Map to downloadable status and extension

```python
DOWNLOADABLE_TYPES = {
    StudioContentType.AUDIO_OVERVIEW: (".mp3", "audio"),
    StudioContentType.VIDEO_OVERVIEW: (".mp4", "video"),
    StudioContentType.SLIDE_DECK: (".pdf", "slides"),
    StudioContentType.INFOGRAPHIC: (".png", "infographic"),
}

def is_downloadable(artifact: Artifact) -> bool:
    return artifact.artifact_type in DOWNLOADABLE_TYPES
```

### Batch Download Implementation

```python
async def download_batch(artifact_ids: list[str], output_dir: Path) -> DownloadResult:
    results = DownloadResult()

    for artifact_id in artifact_ids:
        artifact = await client.artifacts.get(artifact_id)

        if not is_downloadable(artifact):
            results.skipped.append(SkippedArtifact(artifact, "not_downloadable"))
            continue

        filename = sanitize_filename(artifact.title) + get_extension(artifact)
        output_path = output_dir / filename

        if output_path.exists() and not overwrite:
            results.skipped.append(SkippedArtifact(artifact, "already_exists"))
            continue

        try:
            await download_artifact(artifact, output_path)
            results.downloaded.append(DownloadedArtifact(artifact, output_path))
        except Exception as e:
            results.failed.append(FailedArtifact(artifact, str(e)))

    return results
```

## Testing Plan

### Unit Tests
- Filename sanitization edge cases
- Downloadable type detection
- Exit code logic

### Integration Tests
- Mock artifact lookup and download
- JSON output format
- Batch processing logic

### E2E Tests
- Download single artifact
- Download multiple artifacts
- Download all with mixed types
- Dry run mode
- Conflict handling

## Future Considerations

- Progress bars for large downloads
- Parallel downloads for batch operations
- Resume interrupted downloads
- Filter `--all` by type (e.g., `--all --type audio`)
