import argparse
import pandas as pd
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="Plot stress-ng benchmark results.")
parser.add_argument("--input", default="stressng_aggregated.csv", help="Input CSV file")
parser.add_argument("--output_dir", default=".", help="Output directory for plots")
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

cols_to_round = [
    "mean_ops_real",
    "std_ops_real",
    "mean_ops_usr_sys",
    "std_ops_usr_sys",
    "scaling_coeff",
]
agg[cols_to_round] = agg[cols_to_round].round(2)

print("stress-ng aggregated results:")
print(agg.to_string(index=False))

arm = agg[agg["arch"] == "aarch64"].sort_values("mean_ops_real")
amd = agg[agg["arch"] == "x86_64"].sort_values("mean_ops_real")

# -----------------------------
# Figure 1: ARM64 – bogo ops/s (real) по instance_type
# -----------------------------
plt.figure(figsize=(10, 5))
x_pos = range(len(arm))

plt.bar(x_pos, arm["mean_ops_real"])
plt.xticks(x_pos, arm["instance_type"], rotation=45, ha="right")
plt.ylabel("bogo ops/s (real)")
plt.xlabel("Тип інстансу")
plt.title("Результати stress-ng для ARM64 (bogo ops/s real)")
plt.tight_layout()
plt.savefig(f"{args.output_dir}/stressng_arm64_bogo_ops_real.png", dpi=200)

# -----------------------------
# Figure 2: AMD64 – bogo ops/s (real) по instance_type
# -----------------------------
plt.figure(figsize=(10, 5))
x_pos = range(len(amd))

plt.bar(x_pos, amd["mean_ops_real"])
plt.xticks(x_pos, amd["instance_type"], rotation=45, ha="right")
plt.ylabel("bogo ops/s (real)")
plt.xlabel("Тип інстансу")
plt.title("Результати stress-ng для AMD64 (bogo ops/s real)")
plt.tight_layout()
plt.savefig(f"{args.output_dir}/stressng_amd64_bogo_ops_real.png", dpi=200)

# -----------------------------
# Figure 3: Aggregated – bogo ops/s (real) by arch and instance_type
# -----------------------------
plt.figure(figsize=(12, 6))
x_pos = range(len(amd) + len(arm))
all_data = pd.concat([arm, amd]).sort_values(["arch", "mean_ops_real"])
plt.bar(
    x_pos,
    all_data["mean_ops_real"],
    color=["blue" if a == "aarch64" else "orange" for a in all_data["arch"]],
)
plt.xticks(x_pos, all_data["instance_type"], rotation=45, ha="right")
plt.ylabel("bogo ops/s (real)")
plt.xlabel("Тип інстансу")
plt.title("Агреговані результати stress-ng (bogo ops/s real)")
plt.tight_layout()
plt.savefig(f"{args.output_dir}/stressng_aggregated_bogo_ops_real.png", dpi=200)

print(
    "Graphics saved as:\n"
    " - stressng_arm64.png\n"
    " - stressng_amd64.png\n"
    " - stressng_comparison.png"
)
