#!/usr/bin/env python3
"""Optional local MLX Whisper transcription; audio is never uploaded."""
import argparse
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    hours, minutes = divmod(minutes, 60)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path, help="Existing local audio file")
    parser.add_argument("--model", required=True, help="Local MLX model directory or HF repo ID")
    parser.add_argument("--language", default="auto",
                        help="Source speech language code or auto (default); independent of notes language")
    parser.add_argument("--output", required=True, type=Path, help="JSON path; also writes same-stem TXT")
    parser.add_argument("--offset", type=float, default=0, help="Clip start in original source, seconds")
    parser.add_argument("--prompt", help="Optional vocabulary hints, not verified transcript text")
    parser.add_argument("--independent", action="store_true", help="Disable previous-text conditioning")
    parser.add_argument("--work-dir", type=Path, help="Cache/temp directory; defaults to output parent")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing output files")
    args = parser.parse_args()
    source, output = args.audio.expanduser().resolve(), args.output.expanduser().resolve()
    companion = output.with_suffix(".txt")
    if not source.is_file():
        parser.error(f"Audio file does not exist: {source}")
    if output.suffix.lower() != ".json":
        parser.error("--output must end with .json")
    if not math.isfinite(args.offset) or args.offset < 0:
        parser.error("--offset must be a finite, nonnegative number of seconds")
    for target in (output, companion):
        if target == source or (target.exists() and target.samefile(source)):
            parser.error("Output cannot replace the source audio")
        if target.exists() and (not args.overwrite or not target.is_file()):
            parser.error(f"Output exists: {target}; choose another path or use --overwrite")
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        parser.error("MLX Whisper requires an Apple Silicon Mac with Metal; use another local ASR engine")
    if not shutil.which("ffmpeg"):
        parser.error("ffmpeg is missing from PATH; provide a prepared local environment")
    work = (args.work_dir or output.parent).expanduser().resolve()
    caches = {"HF_HOME": "hf-cache", "HF_HUB_CACHE": "hf-cache/hub",
              "HUGGINGFACE_HUB_CACHE": "hf-cache/hub", "HF_ASSETS_CACHE": "hf-cache/assets",
              "HF_XET_CACHE": "hf-cache/xet", "NUMBA_CACHE_DIR": "numba-cache",
              "XDG_CACHE_HOME": "cache", "TMPDIR": "tmp", "TMP": "tmp", "TEMP": "tmp"}
    for key, relative in caches.items():
        directory = work / relative
        directory.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(directory)
    tempfile.tempdir = str(work / "tmp")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    model_path = Path(args.model).expanduser()
    model = str(model_path.resolve()) if model_path.is_dir() else args.model
    if model_path.is_dir():
        os.environ["HF_HUB_OFFLINE"] = "1"
    elif args.model.startswith(("/", "~", ".")):
        parser.error(f"Local model directory does not exist: {args.model}")
    # A subprocess contains native Metal initialization failures, including sandbox aborts.
    probe = subprocess.run([sys.executable, "-c", "import mlx.core as mx; "
                            "raise SystemExit(0 if mx.metal.is_available() else 2)"],
                           capture_output=True, text=True)
    if probe.returncode:
        parser.error("MLX/Metal is unavailable. Check installed mlx-whisper and Metal access; "
                     "a sandbox may block the GPU. Use an authorized local environment. "
                     + probe.stderr.strip()[-800:])
    try:
        import mlx_whisper
    except ImportError as exc:
        parser.error(f"mlx-whisper is unavailable in this Python environment: {exc}")
    started = time.monotonic()
    print("Transcribing locally; a remote model ID may download model weights.", flush=True)
    result = mlx_whisper.transcribe(str(source), path_or_hf_repo=model,
                                   language=None if args.language.lower() == "auto" else args.language,
                                   task="transcribe", verbose=False,
                                   word_timestamps=False, initial_prompt=args.prompt,
                                   condition_on_previous_text=not args.independent)
    segments = []
    for segment in result.get("segments", []):
        start, end = float(segment["start"]), float(segment["end"])
        if not all(math.isfinite(value) for value in (start, end)) or not 0 <= start <= end:
            raise ValueError("ASR returned invalid segment timestamps; no output was written")
        segments.append({"start": round(start + args.offset, 3),
                         "end": round(end + args.offset, 3), "text": segment["text"].strip()})
    actual_language = result.get("language") or "unknown"
    if str(actual_language).lower() == "auto":
        actual_language = "unknown"
    data = {"language": actual_language, "text": result.get("text", "").strip(),
            "segments": segments, "provenance": {
                "engine": "mlx-whisper", "engine_version": importlib.metadata.version("mlx-whisper"),
                "model": model, "input": str(source), "offset_seconds": args.offset,
                "source_language_requested": args.language,
                "timestamp_reference": "original_source_seconds", "automatic_transcript": True,
                "human_verified": False, "independent": args.independent,
                "elapsed_seconds": round(time.monotonic() - started, 2)}}
    contents = (json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                "\n".join(f'[{timestamp(s["start"])}–{timestamp(s["end"])}] {s["text"]}'
                          for s in segments) + "\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    for target, content in zip((output, companion), contents):
        with target.open("w" if args.overwrite else "x", encoding="utf-8") as handle:
            handle.write(content)
    print(f"Saved {len(segments)} automatic, unverified segments: {output} and {companion}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        raise SystemExit(f"Transcription failed: {error}. Check file access, local dependencies, "
                         "model availability, and Metal/sandbox access.")
