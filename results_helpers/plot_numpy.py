import argparse
import pandas as pd
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="Plot NumPy benchmark results.")
parser.add_argument("--input", default="numpy_aggregated.csv", help="Input CSV file")
parser.add_argument("--output_dir", default=".", help="Output directory for plots")
args = parser.parse_args()
agg = pd.read_csv(args.input)

arm = agg[agg["arch"] == "aarch64"].sort_values(["task_kind", "mean_wall_s"])
amd = agg[agg["arch"] == "x86_64"].sort_values(["task_kind", "mean_wall_s"])

# -----------------------------
# Figure 1 – ARM64 (separate matmul and elem)
# -----------------------------
plt.figure(figsize=(10, 5))
for task, data in arm.groupby("task_kind"):
    plt.bar(data["instance_type"], data["mean_wall_s"], label=f"{task}")
plt.xticks(rotation=45, ha="right")
plt.ylabel("Середній час виконання, с")
plt.xlabel("Тип інстансу")
plt.title("Час виконання NumPy-операцій (ARM64)")
plt.legend()
plt.tight_layout()
plt.savefig(f"{args.output_dir}/numpy_arm64.png", dpi=200)

# -----------------------------
# Figure 2 – AMD64 (separate matmul and elem)
# -----------------------------
plt.figure(figsize=(10, 5))
for task, data in amd.groupby("task_kind"):
    plt.bar(data["instance_type"], data["mean_wall_s"], label=f"{task}")
plt.xticks(rotation=45, ha="right")
plt.ylabel("Середній час виконання, с")
plt.xlabel("Тип інстансу")
plt.title("Час виконання NumPy-операцій (AMD64)")
plt.legend()
plt.tight_layout()
plt.savefig(f"{args.output_dir}/numpy_amd64.png", dpi=200)

# -----------------------------
# Figure 3 – Comparison of Both Architectures
# -----------------------------
plt.figure(figsize=(10, 5))

plt.bar(
    arm["instance_type"], arm["mean_wall_s"], label="ARM64 (Graviton)", color="green"
)
plt.bar(
    amd["instance_type"], amd["mean_wall_s"], label="AMD64 (Intel/AMD)", color="orange"
)
plt.xticks(rotation=45, ha="right")
plt.ylabel("Середній час виконання, с")
plt.xlabel("Тип інстансу")
plt.title("Порівняння ефективності NumPy між архітектурами")
plt.legend(["ARM64 (Graviton)", "AMD64 (Intel/AMD)"])
plt.tight_layout()
plt.savefig(f"{args.output_dir}/numpy_comparison.png", dpi=200)

print(
    "Graphics saved as:\n"
    " - numpy_arm64.png\n"
    " - numpy_amd64.png\n"
    " - numpy_comparison.png"
)
