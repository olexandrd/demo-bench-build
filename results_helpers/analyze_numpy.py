import argparse
import pandas as pd

parser = argparse.ArgumentParser(description="Analyze NumPy benchmark results.")
parser.add_argument("--input", default="normalized_results.csv", help="Input CSV file")
parser.add_argument("--output", default="numpy_aggregated.csv", help="Output CSV file")
args = parser.parse_args()

df = pd.read_csv(args.input)

numpy_df = df[df["task_group"] == "numpy"].copy()

agg = numpy_df.groupby(
    ["cloud_provider", "arch", "instance_type", "task_kind"], as_index=False
).agg(
    mean_wall_s=("wall_s", "mean"),
    std_wall_s=("wall_s", "std"),
    runs=("wall_s", "count"),
)

agg["relative_speed"] = 1 / agg["mean_wall_s"]

agg = agg.round(
    {
        "mean_wall_s": 3,
        "std_wall_s": 3,
        "relative_speed": 3,
    }
)

agg.to_csv(args.output, index=False)
print(agg)
