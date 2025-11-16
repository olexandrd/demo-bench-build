#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def load_prices(path: str) -> pd.DataFrame:
    """Load instance prices (must contain instance_type, price_per_hour_usd, vcpus)."""
    prices = pd.read_csv(path)
    required = {"instance_type", "price_per_hour_usd", "vcpus"}
    missing = required - set(prices.columns)
    if missing:
        raise SystemExit(f"Price CSV is missing columns: {missing}")
    return prices[["instance_type", "price_per_hour_usd", "vcpus"]].drop_duplicates()


def plot_perf_per_dollar(df: pd.DataFrame, value_col: str, title: str, out_png: str):
    """
    Plot bar chart for performance_per_dollar_* metric by instance type.
    """
    labels = df["instance_type"] + " (" + df["arch"] + ")"
    x = range(len(df))

    plt.figure(figsize=(10, 5))
    plt.bar(x, df[value_col])
    plt.xticks(x, labels, rotation=45, ha="right")
    plt.ylabel("нормалізована продуктивність на долар")
    plt.xlabel("тип інстансу (архітектура)")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()
    print(f"Saved plot: {out_png}")


def analyze_stress(
    prices: pd.DataFrame,
    in_path="stressng_aggregated.csv",
    out_csv="stressng_economy.csv",
    out_png="stressng_perf_per_dollar.png",
    vcpus_used: int = 2,
    output_dir: str = ".",
):
    print("\n=== Analyzing stress-ng ===")
    df = pd.read_csv(in_path)
    df = df.merge(prices, on="instance_type", how="inner")

    # Raw performance metric: bogo ops/s (higher is better)
    df["performance_metric"] = df["mean_ops_real"]

    # Raw performance per dollar (no vCPU normalization)
    df["performance_per_dollar_raw"] = (
        df["performance_metric"] / df["price_per_hour_usd"]
    )

    # Normalized performance per dollar (scaled by vCPUs_total / vCPUs_used)
    df["performance_per_dollar_norm"] = (
        df["performance_metric"] / df["price_per_hour_usd"] * (df["vcpus"] / vcpus_used)
    )

    df = df.sort_values("performance_per_dollar_norm", ascending=False)

    df.to_csv(f"{output_dir}/{out_csv}", index=False)
    print(f"Saved stress-ng economy results to: {output_dir}/{out_csv}")
    print(
        df[
            [
                "arch",
                "instance_type",
                "mean_ops_real",
                "price_per_hour_usd",
                "vcpus",
                "performance_per_dollar_raw",
                "performance_per_dollar_norm",
            ]
        ]
    )

    plot_perf_per_dollar(
        df,
        value_col="performance_per_dollar_norm",
        title="Продуктивність на долар - stress-ng (нормалізовано до 2 vCPU)",
        out_png=f"{output_dir}/{out_png}",
    )


def analyze_ffmpeg(
    prices: pd.DataFrame,
    in_path="ffmpeg_aggregated.csv",
    out_csv="ffmpeg_economy.csv",
    out_png="ffmpeg_perf_per_dollar.png",
    vcpus_used: int = 2,
    output_dir: str = ".",
):
    print("\n=== Analyzing FFmpeg ===")
    df = pd.read_csv(in_path)
    df = df.merge(prices, on="instance_type", how="inner")

    # Use relative_speed if present, otherwise 1 / mean_wall_s
    if "relative_speed" in df.columns:
        df["performance_metric"] = df["relative_speed"]
    else:
        df["performance_metric"] = 1.0 / df["mean_wall_s"]

    df["performance_per_dollar_raw"] = (
        df["performance_metric"] / df["price_per_hour_usd"]
    )
    df["performance_per_dollar_norm"] = (
        df["performance_metric"] / df["price_per_hour_usd"] * (df["vcpus"] / vcpus_used)
    )

    df = df.sort_values("performance_per_dollar_norm", ascending=False)

    df.to_csv(f"{output_dir}/{out_csv}", index=False)
    print(f"Saved FFmpeg economy results to: {output_dir}/{out_csv}")
    print(
        df[
            [
                "arch",
                "instance_type",
                "mean_wall_s",
                "price_per_hour_usd",
                "vcpus",
                "performance_per_dollar_raw",
                "performance_per_dollar_norm",
            ]
        ]
    )

    plot_perf_per_dollar(
        df,
        value_col="performance_per_dollar_norm",
        title="Продуктивність на долар - FFmpeg (нормалізовано до 2 vCPU)",
        out_png=f"{output_dir}/{out_png}",
    )


def analyze_numpy(
    prices: pd.DataFrame,
    in_path="numpy_aggregated.csv",
    out_prefix="numpy",
    vcpus_used: int = 2,
    output_dir: str = ".",
):
    print("\n=== Analyzing NumPy ===")
    df = pd.read_csv(in_path)
    df = df.merge(prices, on="instance_type", how="inner")

    if "task_kind" not in df.columns:
        raise SystemExit(
            "numpy_aggregated.csv must contain 'task_kind' (e.g. 'matmul', 'elem')."
        )

    for task in sorted(df["task_kind"].unique()):
        sub = df[df["task_kind"] == task].copy()

        # Use relative_speed if present, otherwise 1 / mean_wall_s
        if "relative_speed" in sub.columns:
            sub["performance_metric"] = sub["relative_speed"]
        else:
            sub["performance_metric"] = 1.0 / sub["mean_wall_s"]

        sub["performance_per_dollar_raw"] = (
            sub["performance_metric"] / sub["price_per_hour_usd"]
        )
        sub["performance_per_dollar_norm"] = (
            sub["performance_metric"]
            / sub["price_per_hour_usd"]
            * (sub["vcpus"] / vcpus_used)
        )

        sub = sub.sort_values("performance_per_dollar_norm", ascending=False)

        out_csv = f"{output_dir}/{out_prefix}_{task}_economy.csv"
        out_png = f"{output_dir}/{out_prefix}_{task}_perf_per_dollar.png"

        sub.to_csv(out_csv, index=False)
        print(f"\nNumPy task = {task}")
        print(f"Saved NumPy economy results to: {out_csv}")
        print(
            sub[
                [
                    "arch",
                    "instance_type",
                    "task_kind",
                    "mean_wall_s",
                    "price_per_hour_usd",
                    "vcpus",
                    "performance_per_dollar_raw",
                    "performance_per_dollar_norm",
                ]
            ]
        )

        plot_perf_per_dollar(
            sub,
            value_col="performance_per_dollar_norm",
            title=f"Продуктивність на долар - NumPy ({task}, нормалізовано до 2 vCPU)",
            out_png=out_png,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Analyze economic efficiency (performance_per_dollar) for different workloads."
    )
    parser.add_argument(
        "--input-dir", default=".", help="Input directory for aggregated CSV files"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output directory for economy analysis results",
    )
    parser.add_argument(
        "--prices",
        default=None,
        help="CSV with instance prices (default: aws_instance_prices.csv)",
    )
    parser.add_argument(
        "--stress",
        default=None,
        help="Aggregated stress-ng results (default: stressng_aggregated.csv)",
    )
    parser.add_argument(
        "--ffmpeg",
        default=None,
        help="Aggregated FFmpeg results (default: ffmpeg_aggregated.csv)",
    )
    parser.add_argument(
        "--numpy",
        default=None,
        help="Aggregated NumPy results (default: numpy_aggregated.csv)",
    )
    parser.add_argument(
        "--vcpus-used",
        type=int,
        default=2,
        help="Number of vCPUs actually used in benchmarks (default: 2)",
    )

    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    prices_path = (
        Path(args.prices) if args.prices else input_dir / "aws_instance_prices.csv"
    )
    stress_path = (
        Path(args.stress) if args.stress else input_dir / "stressng_aggregated.csv"
    )
    ffmpeg_path = (
        Path(args.ffmpeg) if args.ffmpeg else input_dir / "ffmpeg_aggregated.csv"
    )
    numpy_path = Path(args.numpy) if args.numpy else input_dir / "numpy_aggregated.csv"

    prices = load_prices(prices_path)

    if Path(stress_path).is_file():
        analyze_stress(
            prices,
            in_path=stress_path,
            vcpus_used=args.vcpus_used,
            output_dir=args.output_dir,
        )
    else:
        print(f"⚠️ stress-ng file not found: {stress_path}")

    if Path(ffmpeg_path).is_file():
        analyze_ffmpeg(
            prices,
            in_path=ffmpeg_path,
            vcpus_used=args.vcpus_used,
            output_dir=args.output_dir,
        )
    else:
        print(f"⚠️ FFmpeg file not found: {ffmpeg_path}")

    if Path(numpy_path).is_file():
        analyze_numpy(
            prices,
            in_path=numpy_path,
            vcpus_used=args.vcpus_used,
            output_dir=args.output_dir,
        )
    else:
        print(f"⚠️ NumPy file not found: {numpy_path}")


if __name__ == "__main__":
    main()
