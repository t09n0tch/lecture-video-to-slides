#!/usr/bin/env python3
"""Read lecture media with ffmpeg; write artifacts only under --work-dir."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def number(value):
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise argparse.ArgumentTypeError("Expected a finite, nonnegative number.")
    return value


def crop(value):
    if not re.fullmatch(r"\d+:\d+:\d+:\d+", value):
        raise argparse.ArgumentTypeError("Crop must be WIDTH:HEIGHT:X:Y in pixels.")
    w, h, _, _ = map(int, value.split(":"))
    if not w or not h:
        raise argparse.ArgumentTypeError("Crop width and height must be positive.")
    return value


def run(command):
    if not shutil.which(command[0]):
        raise ValueError(f"{command[0]} is missing; install ffmpeg/ffprobe first.")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError(f"{command[0]} failed:\n{result.stderr[-3500:]}")
    return result


def destination(args, source):
    root = args.work_dir.expanduser().resolve()
    output = args.output.expanduser()
    output = (root / output).resolve() if not output.is_absolute() else output.resolve()
    if not output.is_relative_to(root):
        raise ValueError("Output must be inside --work-dir; relative outputs are resolved there.")
    if output == source or (output.exists() and output.samefile(source)):
        raise ValueError("Output must not replace the source media.")
    if output.exists() and not args.overwrite:
        raise ValueError(f"Output exists: {output}; use --overwrite explicitly.")
    suffix = {"probe": ".json", "scenes": ".json", "frame": ".png", "audio": ".wav"}[args.command]
    if output.suffix.lower() != suffix:
        raise ValueError(f"{args.command} output must use {suffix}.")
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=Path("work"), help="Output root (default: ./work).")
    parser.add_argument("--overwrite", action="store_true", help="Explicitly replace an existing output.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("probe", "scenes", "frame", "audio"):
        command = commands.add_parser(name)
        command.add_argument("input", type=Path, help="Local source file; always preserved.")
        command.add_argument("--output", "-o", type=Path, required=True)
        if name in ("scenes", "frame"):
            command.add_argument("--crop", type=crop, help="Optional WIDTH:HEIGHT:X:Y; no scaling.")
        if name == "scenes":
            command.add_argument("--threshold", type=number, default=0.12, help="Scene threshold from 0 to 1.")
        if name == "frame":
            command.add_argument("--seconds", type=number, required=True)
        if name == "audio":
            command.add_argument("--start", type=number, default=0)
            command.add_argument("--duration", type=number, help="Optional positive clip duration in seconds.")
    args = parser.parse_args()
    temporary = None
    try:
        source = args.input.expanduser().resolve()
        if not source.is_file():
            raise ValueError(f"Source file not found: {source}")
        output = destination(args, source)
        descriptor, path = tempfile.mkstemp(prefix=".media-", suffix=output.suffix, dir=output.parent)
        os.close(descriptor)
        temporary = Path(path)
        payload = None
        base = ["ffmpeg", "-hide_banner", "-nostdin", "-nostats"]
        if args.command == "probe":
            result = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(source)])
            payload = {"schema_version": 1, "source": str(source), "ffprobe": json.loads(result.stdout)}
        elif args.command == "scenes":
            if args.threshold > 1:
                raise ValueError("Scene threshold must be between 0 and 1.")
            filters = ([f"crop={args.crop}"] if args.crop else []) + [f"select=gt(scene\\,{args.threshold})", "showinfo"]
            result = run(base + ["-loglevel", "info", "-i", str(source), "-map", "0:v:0", "-an", "-vf", ",".join(filters), "-f", "null", "-"])
            times = sorted({0.0, *(float(x) for x in re.findall(r"showinfo[^\n]*?pts_time:([0-9.eE+-]+)", result.stderr))})
            payload = {"schema_version": 1, "source": str(source), "crop": args.crop,
                       "threshold": args.threshold, "candidate_times_seconds": times,
                       "candidate_count": len(times),
                       "note": "Includes t=0. Candidates require visual review; these are not final pages."}
        elif args.command == "frame":
            command = base + ["-loglevel", "error", "-ss", str(args.seconds), "-i", str(source), "-map", "0:v:0", "-frames:v", "1", "-an"]
            if args.crop:
                command += ["-vf", f"crop={args.crop}"]
            run(command + ["-y", str(temporary)])
        else:
            if args.duration == 0:
                raise ValueError("Audio duration must be greater than zero.")
            command = base + ["-loglevel", "error", "-ss", str(args.start), "-i", str(source)]
            if args.duration is not None:
                command += ["-t", str(args.duration)]
            run(command + ["-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-y", str(temporary)])
        if payload is not None:
            temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if temporary.stat().st_size == 0 or (args.command == "audio" and temporary.stat().st_size <= 78):
            raise ValueError("No media was produced; check the chosen time, duration, and source streams.")
        if args.overwrite:
            os.replace(temporary, output)
        else:
            os.link(temporary, output)  # Atomic refusal if another process created the destination.
        print(output)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
