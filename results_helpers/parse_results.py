#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

import pandas as pd


def read_file(path: Path):
    """
    Read .jsonl and split lines into:
    - json_recs: those that were successfully parsed as JSON
    - text_lines: everything else (for stress-ng metrics)
    """
    json_recs = []
    text_lines = []
    for line in path.read_text().splitlines():
        line_strip = line.strip()
        if not line_strip:
            continue
        try:
            json_recs.append(json.loads(line_strip))
        except json.JSONDecodeError:
            text_lines.append(line.rstrip("\n"))
    return json_recs, text_lines


def classify_records(json_recs):
    """
    In most cases we expect:
    - ffmpeg: 1 JSON with metrics
    - numpy: 1 JSON config + 1 JSON with metrics
    - stress-ng: 1 JSON with metrics
    """
    metrics = [r for r in json_recs if "metrics" in r]
    extra = [r for r in json_recs if "metrics" not in r]
    return metrics, extra


def get_task_group(task_kind: str) -> str:
    if not task_kind:
        return ""
    if task_kind.startswith("numpy"):
        return "numpy"
    if task_kind == "ffmpeg":
        return "ffmpeg"
    if task_kind == "stress-ng":
        return "synthetic"
    return "other"


def parse_numpy_extra(extra: dict) -> dict:
    # {"task": "numpy.elemwise", "n": 1000000, "iter": 50, "seconds": ...}
    return {
        "numpy_task": extra.get("task"),
        "numpy_n": extra.get("n"),
        "numpy_iter": extra.get("iter"),
        "numpy_seconds_reported": extra.get("seconds"),
    }


def parse_ffmpeg_cmd(cmd: str) -> dict:
    out = {}
    m = re.search(r"testsrc=duration=(\d+)", cmd)
    if m:
        out["ffmpeg_duration_s"] = int(m.group(1))

    m = re.search(r"size=(\d+)x(\d+)", cmd)
    if m:
        out["ffmpeg_width"] = int(m.group(1))
        out["ffmpeg_height"] = int(m.group(2))

    m = re.search(r"-c:v\s+(\S+)", cmd)
    if m:
        out["ffmpeg_codec"] = m.group(1)

    m = re.search(r"-preset\s+(\S+)", cmd)
    if m:
        out["ffmpeg_preset"] = m.group(1)

    m = re.search(r"-crf\s+(\d+)", cmd)
    if m:
        out["ffmpeg_crf"] = int(m.group(1))

    return out


def parse_stress_cmd(cmd: str) -> dict:
    out = {}
    m = re.search(r"--cpu\s+(\d+)", cmd)
    if m:
        out["stress_cpu_workers"] = int(m.group(1))

    m = re.search(r"--cpu-method\s+(\S+)", cmd)
    if m:
        out["stress_cpu_method"] = m.group(1)

    m = re.search(r"--cpu-ops\s+(\d+)", cmd)
    if m:
        out["stress_cpu_ops"] = int(m.group(1))

    m = re.search(r"--timeout\s+(\d+)s?", cmd)
    if m:
        out["stress_timeout_s"] = int(m.group(1))

    return out


def parse_stress_text(lines):
    """
    Parse stress-ng output text lines to extract metrics:
    stress-ng: metrc: [17] cpu 1000 2.60 5.20 0.00 384.10 192.22

    Повертає:
    - stress_stressor
    - stress_bogo_ops
    - stress_real_time_s
    - stress_usr_time_s
    - stress_sys_time_s
    - stress_bogo_ops_per_s_real
    - stress_bogo_ops_per_s_usr_sys
    """
    pattern = re.compile(
        r"stress-ng:\s+metrc:\s+\[\d+\]\s+(\S+)\s+(\d+)\s+([\d.]+)\s+"
        r"([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"
    )
    for line in lines:
        m = pattern.search(line)
        if m:
            stressor, bogo_ops, real, usr, sys, bogo_real, bogo_usrsys = m.groups()
            return {
                "stress_stressor": stressor,
                "stress_bogo_ops": int(bogo_ops),
                "stress_real_time_s": float(real),
                "stress_usr_time_s": float(usr),
                "stress_sys_time_s": float(sys),
                "stress_bogo_ops_per_s_real": float(bogo_real),
                "stress_bogo_ops_per_s_usr_sys": float(bogo_usrsys),
            }
    return {}


def build_row(path: Path, metrics_rec: dict, extra_rec: dict | None, text_lines):
    meta = metrics_rec.get("meta", {})
    host = metrics_rec.get("host", {})
    metrics = metrics_rec.get("metrics", {})

    # task_kind: priority meta.task, then extra.task, then empty
    task_kind = meta.get("task") or (extra_rec or {}).get("task") or ""
    cmd = metrics_rec.get("cmd", "")

    row = {
        "file": str(path),
        "ts_start": metrics_rec.get("ts_start"),
        "ts_end": metrics_rec.get("ts_end"),
        "run_id": meta.get("run_id", ""),
        "task_kind": task_kind,
        "task_group": get_task_group(task_kind),
        "cmd": cmd,
        "dataset": meta.get("dataset", ""),
        "arch": host.get("arch"),
        "cpu_model": host.get("cpu_model"),
        "threads": host.get("threads"),
        "mem_kb": host.get("mem_kb"),
        "instance_type": host.get("instance_type") or meta.get("instance_type"),
        "cloud_provider": host.get("cloud_provider") or meta.get("cloud_provider"),
        "exit_code": metrics_rec.get("exit_code"),
        "wall_s": metrics.get("wall_s"),
        "user_s": metrics.get("user_s"),
        "sys_s": metrics.get("sys_s"),
        "max_rss_kb": metrics.get("max_rss_kb"),
    }

    # numpy-specific
    if extra_rec and (extra_rec.get("task", "").startswith("numpy")):
        row.update(parse_numpy_extra(extra_rec))

    # ffmpeg-specific
    if task_kind == "ffmpeg":
        row.update(parse_ffmpeg_cmd(cmd))

    # stress-ng-specific
    if task_kind == "stress-ng":
        row.update(parse_stress_cmd(cmd))
        row.update(parse_stress_text(text_lines))

    return row


def main():
    parser = argparse.ArgumentParser(
        description="Parse jsonl benchmark results and export to CSV."
    )
    parser.add_argument(
        "--input_dir",
        help="Path to the directory with .jsonl files (e.g., ./data/raw)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="normalized_results.csv",
        help="Path to the output CSV (default: normalized_results.csv)",
    )
    args = parser.parse_args()

    root = Path(args.input_dir)
    if not root.is_dir():
        raise SystemExit(f"Input path is not a directory: {root}")

    all_rows = []

    for path in root.rglob("*.jsonl"):
        json_recs, text_lines = read_file(path)
        metrics_recs, extra_recs = classify_records(json_recs)

        # Most typical cases: 1 metrics + 0/1 extra
        if len(metrics_recs) == 1 and len(extra_recs) <= 1:
            extra = extra_recs[0] if extra_recs else None
            all_rows.append(build_row(path, metrics_recs[0], extra, text_lines))
        else:
            # fallback: separate row for each metrics_rec
            for m in metrics_recs:
                all_rows.append(build_row(path, m, None, text_lines))

    if not all_rows:
        raise SystemExit("Do not found any valid records with metrics.")

    df = pd.DataFrame(all_rows)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
