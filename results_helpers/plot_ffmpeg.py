import argparse
import pandas as pd
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="Plot FFmpeg benchmark results.")
parser.add_argument("--input", default="ffmpeg_aggregated.csv", help="Input CSV file")
parser.add_argument("--output_dir", default=".", help="Output directory for plots")
args = parser.parse_args()
agg = pd.read_csv(args.input)

arm = agg[agg["arch"] == "aarch64"].sort_values("mean_wall_s")
amd = agg[agg["arch"] == "x86_64"].sort_values("mean_wall_s")

# -----------------------------
# Figure 1 – ARM64 (video processing time)
# -----------------------------
plt.figure(figsize=(10, 5))
x_pos = range(len(arm))
plt.bar(x_pos, arm["mean_wall_s"], color="green")
plt.xticks(x_pos, arm["instance_type"], rotation=45, ha="right")
plt.ylabel("Середній час обробки, с")
plt.xlabel("Тип інстансу")
plt.title("Час обробки відео FFmpeg для ARM64")
plt.tight_layout()
plt.savefig(f"{args.output_dir}/ffmpeg_arm64_time.png", dpi=200)

# -----------------------------
# Figure 2 – AMD64 (video processing time)
# -----------------------------
plt.figure(figsize=(10, 5))
x_pos = range(len(amd))
plt.bar(x_pos, amd["mean_wall_s"], color="orange")
plt.xticks(x_pos, amd["instance_type"], rotation=45, ha="right")
plt.ylabel("Середній час обробки, с")
plt.xlabel("Тип інстансу")
plt.title("Час обробки відео FFmpeg для AMD64")
plt.tight_layout()
plt.savefig(f"{args.output_dir}/ffmpeg_amd64_time.png", dpi=200)

# -----------------------------
# Figure 3 – Both Architectures
# -----------------------------
plt.figure(figsize=(10, 5))
plt.bar(
    arm["instance_type"], arm["mean_wall_s"], label="ARM64 (Graviton)", color="green"
)
plt.bar(
    amd["instance_type"], amd["mean_wall_s"], label="AMD64 (Intel/AMD)", color="orange"
)
plt.ylabel("Середній час обробки, с")
plt.xlabel("Тип інстансу")
plt.title("Порівняння ефективності обробки відео (FFmpeg)")
plt.legend()
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(f"{args.output_dir}/ffmpeg_comparison.png", dpi=200)

print(
    "Graphics saved as:\n"
    " - ffmpeg_arm64_time.png\n"
    " - ffmpeg_amd64_time.png\n"
    " - ffmpeg_comparison.png"
)
