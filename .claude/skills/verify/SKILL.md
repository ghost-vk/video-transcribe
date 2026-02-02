---
name: verifying-functionality
description: Runs manual tests to verify core functionality works correctly. Use after implementing features, refactoring, or before releases. Tests use video files from test_data/video/.
---

# Manual Testing

Verify that core functionality works after changes.

## Test videos

Located in `test_data/video/`:
- `video_1.mp4` (1.7 MB) — small file, quick tests
- `video_2.mp4` (40 MB) — medium file
- `video_3_it_meeting.mp4` (404 MB) — large file, chunking test

## Test commands

### 1. Convert video to audio

```bash
# Small file
.venv/bin/video-transcribe convert test_data/video/video_1.mp4

# Custom output path
.venv/bin/video-transscribe convert test_data/video/video_1.mp4 -o /tmp/test_audio.mp3
```

**Verify:** Output file exists, is valid MP3, ~16kHz mono

### 2. Transcribe audio

```bash
# With default provider (Z.AI)
.venv/bin/video-transcribe transcribe test_data/video/video_1.txt

# With OpenAI diarization
.venv/bin/video-transcribe transcribe test_data/video/video_1.mp3 -m gpt-4o-transcribe-diarize

# With language specified
.venv/bin/video-transcribe transcribe test_data/video/video_1.mp3 -l ru
```

**Verify:** Output contains transcript, speaker labels (if diarization)

### 3. Process full pipeline

```bash
# Basic processing
.venv/bin/video-transcribe process test_data/video/video_1.mp4

# With post-processing
.venv/bin/video-transcribe process test_data/video/video_3_it_meeting.mp4 --preset meeting

# Screencast preset
.venv/bin/video-transcribe process test_data/video/video_1.mp4 --preset screencast

# Keep audio for debugging
.venv/bin/video-transcribe process test_data/video/video_1.mp4 --keep-audio
```

**Verify:** Creates `.txt` transcript + `.md` summary (if post-process enabled)

### 4. Chunking test (large file)

```bash
# Triggers chunking (>20MB for OpenAI, >30s for Z.AI)
.venv/bin/video-transcribe process test_data/video/video_3_it_meeting.mp4
```

**Verify:** Progress shows chunk processing, final transcript is complete

### 5. Custom prompts

```bash
# Create test prompt file
cat > /tmp/test_prompt.md << 'EOF'
---
system: |
  Summarize the transcript briefly.
---

{transcript}
EOF

# Use custom prompt
.venv/bin/video-transcribe process test_data/video/video_1.mp4 --prompt-file /tmp/test_prompt.md
```

**Verify:** Uses custom prompt, output matches format

## Success criteria

- No errors or exceptions
- Output files created in expected locations
- Audio quality is acceptable (16kHz, mono)
- Transcripts contain expected content
- Post-processing generates valid markdown

## Quick smoke test

```bash
# Fast verification (~30 seconds)
.venv/bin/video-transcribe convert test_data/video/video_1.mp4 && \
.venv/bin/video-transcribe transcribe test_data/video/video_1.mp3 && \
echo "Smoke test passed"
```
