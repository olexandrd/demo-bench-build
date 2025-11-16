import argparse
import pandas as pd

parser = argparse.ArgumentParser(description="Analyze synthetic benchmark results.")
parser.add_argument("--input", default="normalized_results.csv", help="Input CSV file")
parser.add_argument(
    "--output", default="stressng_aggregated.csv", help="Output CSV file"
)
args = parser.parse_args()

df = pd.read_csv(args.input)

synthetic = df[df["task_group"] == "synthetic"].copy()

agg = synthetic.groupby(
    ["cloud_provider", "arch", "instance_type"], as_index=False
).agg(
    mean_ops_real=("stress_bogo_ops_per_s_real", "mean"),
    std_ops_real=("stress_bogo_ops_per_s_real", "std"),
    mean_ops_usr_sys=("stress_bogo_ops_per_s_usr_sys", "mean"),
    std_ops_usr_sys=("stress_bogo_ops_per_s_usr_sys", "std"),
    runs=("stress_bogo_ops_per_s_real", "count"),
)

agg["scaling_coeff"] = agg["mean_ops_usr_sys"] / agg["mean_ops_real"]

agg = agg.sort_values(["arch", "instance_type"])

cols_to_round = [
    "mean_ops_real",
    "mean_ops_usr_sys",
    "scaling_coeff",
]
agg[cols_to_round] = agg[cols_to_round].round(2)

print(agg.to_string(index=False))

agg.to_csv(args.output, index=False)
