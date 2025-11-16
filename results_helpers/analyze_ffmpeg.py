import argparse
import pandas as pd

parser = argparse.ArgumentParser(description="Analyze FFmpeg benchmark results.")
parser.add_argument("--input", default="normalized_results.csv", help="Input CSV file")
parser.add_argument("--output", default="ffmpeg_aggregated.csv", help="Output CSV file")
args = parser.parse_args()

df = pd.read_csv(args.input)

ffmpeg = df[df["task_group"] == "ffmpeg"].copy()

agg = ffmpeg.groupby(["cloud_provider", "arch", "instance_type"], as_index=False).agg(
    mean_wall_s=("wall_s", "mean"),
    std_wall_s=("wall_s", "std"),
    runs=("wall_s", "count"),
)

agg["relative_speed"] = 10 / agg["mean_wall_s"]
agg = agg.sort_values(["arch", "instance_type"])

agg = agg.round(
    {
        "mean_wall_s": 2,
        "std_wall_s": 2,
        "relative_speed": 3,
    }
)

print(agg.to_string(index=False))

agg.to_csv(args.output, index=False)
