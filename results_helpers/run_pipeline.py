#!/usr/bin/env python3
"""
run_pipeline.py

Single entry point for the post-processing pipeline.

Usage:
    python run_pipeline.py my-benchmark-bucket

This script:
  1. Synchronizes benchmark results from an S3 bucket
  2. Runs parse_results.py
  3. Runs get_aws_prices.py
  4. Runs analyze-* scripts
  5. Runs plot-* scripts
  6. Runs economy-* scripts
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(name: str, cmd: list[str]) -> None:
    """Run a command as a separate process with logging and exit code check."""
    print(f"\n=== [{name}] ===")
    print(f"$ {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=False,
            text=True,
        )
    except FileNotFoundError as e:
        print(f"[ERROR] Command not found: {cmd[0]} ({e})")
        sys.exit(1)

    if result.returncode != 0:
        print(f"[ERROR] Step '{name}' exited with code {result.returncode}")
        sys.exit(result.returncode)
    else:
        print(f"[OK] Step '{name}' completed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Full post-processing pipeline for benchmark results from S3."
    )
    parser.add_argument(
        "s3_bucket",
        help="S3 bucket name without the s3:// prefix (e.g., my-bench-bucket)",
    )
    args = parser.parse_args()

    bucket = args.s3_bucket
    root_dir = Path(__file__).resolve().parent.parent
    scripts_dir = Path(__file__).resolve().parent
    data_dir = root_dir / "data"
    results_dir = root_dir / "results"
    results_dir.mkdir(exist_ok=True)

    # 1. Sync results from S3
    data_dir.mkdir(exist_ok=True)
    run_step(
        "Sync S3 → ./data",
        ["aws", "s3", "sync", f"s3://{bucket}", str(data_dir)],
    )

    # 2. Parse JSONL → normalized CSV
    run_step(
        "Parse results (JSONL → normalized CSV)",
        [
            "python",
            str(scripts_dir / "parse_results.py"),
            "--input_dir",
            str(data_dir),
            "--output",
            str(results_dir / "normalized_results.csv"),
        ],
    )

    # 3. Fetch AWS prices and merge with results
    run_step(
        "Fetch AWS prices",
        [
            "python",
            str(scripts_dir / "get_aws_prices.py"),
            "--region",
            "eu-west-1",
            "--normalized-csv",
            str(results_dir / "normalized_results.csv"),
            "--output",
            str(results_dir / "aws_instance_prices.csv"),
        ],
    )

    # 4. Analyze per test
    run_step(
        "Analyze stress-ng",
        [
            "python",
            str(scripts_dir / "analyze_stressng.py"),
            "--input",
            str(results_dir / "normalized_results.csv"),
            "--output",
            str(results_dir / "stressng_aggregated.csv"),
        ],
    )
    run_step(
        "Analyze ffmpeg",
        [
            "python",
            str(scripts_dir / "analyze_ffmpeg.py"),
            "--input",
            str(results_dir / "normalized_results.csv"),
            "--output",
            str(results_dir / "ffmpeg_aggregated.csv"),
        ],
    )
    run_step(
        "Analyze numpy",
        [
            "python",
            str(scripts_dir / "analyze_numpy.py"),
            "--input",
            str(results_dir / "normalized_results.csv"),
            "--output",
            str(results_dir / "numpy_aggregated.csv"),
        ],
    )

    # 5. Plot results
    run_step(
        "Plot stress-ng",
        [
            "python",
            str(scripts_dir / "plot_stressng.py"),
            "--input",
            str(results_dir / "normalized_results.csv"),
            "--output_dir",
            str(results_dir),
        ],
    )
    run_step(
        "Plot ffmpeg",
        [
            "python",
            str(scripts_dir / "plot_ffmpeg.py"),
            "--input",
            str(results_dir / "ffmpeg_aggregated.csv"),
            "--output_dir",
            str(results_dir),
        ],
    )
    run_step(
        "Plot numpy",
        [
            "python",
            str(scripts_dir / "plot_numpy.py"),
            "--input",
            str(results_dir / "numpy_aggregated.csv"),
            "--output_dir",
            str(results_dir),
        ],
    )

    # 6. Economic analysis
    run_step(
        "Economy analysis",
        [
            "python",
            str(scripts_dir / "analyze_economy.py"),
            "--input-dir",
            str(results_dir),
            "--output-dir",
            str(results_dir),
        ],
    )

    print("\n=== Done. All pipeline steps completed successfully. ===")


if __name__ == "__main__":
    main()
