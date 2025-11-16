#!/usr/bin/env bash
set -euo pipefail


RUN_ID="${RUN_ID:-}"
TASK="${TASK:-}"
DATASET="${DATASET:-}"
EXTRA="${EXTRA:-}"
INSTANCE_ID="${INSTANCE_ID:-}"
INSTANCE_TYPE="${INSTANCE_TYPE:-}"
CLOUD_PROVIDER="${CLOUD_PROVIDER:-}"
CLOUD_REGION="${CLOUD_REGION:-}"

now_ms() { date +%s%3N; }  # мілісекунди
arch=$(uname -m)
cpu_model=$(awk -F: '/model name|Hardware/ {print $2; exit}' /proc/cpuinfo | sed 's/^ //')
threads=$(nproc)
mem_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo)

emit_json() {
  jq -nc \
    --arg ts_start "$1" \
    --arg ts_end "$2" \
    --arg cmd "$3" \
    --arg exit_code "$4" \
    --arg arch "$arch" \
    --arg cpu_model "$cpu_model" \
    --argjson threads "$threads" \
    --argjson mem_kb "$mem_kb" \
    --arg run_id "$RUN_ID" \
    --arg task "$TASK" \
    --arg dataset "$DATASET" \
    --arg extra "$EXTRA" \
    --argjson wall_s "$5" \
    --argjson user_s "$6" \
    --argjson sys_s "$7" \
    --argjson max_rss_kb "$8" \
    --arg instance_id "$INSTANCE_ID" \
    --arg instance_type "$INSTANCE_TYPE" \
    --arg cloud_provider "$CLOUD_PROVIDER" \
    --arg cloud_region "$CLOUD_REGION" \
  '{
      ts_start:$ts_start,
      ts_end:$ts_end,
      cmd:$cmd,
      exit_code: ($exit_code|tonumber),
      metrics:{
        wall_s:$wall_s,
        user_s:$user_s,
        sys_s:$sys_s,
        max_rss_kb:$max_rss_kb
      },
      host:{
        arch:$arch,
        cpu_model:$cpu_model,
        threads:$threads,
        mem_kb:$mem_kb,
        instance_id:$instance_id,
        instance_type:$instance_type,
        cloud_provider:$cloud_provider,
        cloud_region:$cloud_region
      },
      meta:{
        run_id:$run_id,
        task:$task,
        dataset:$dataset,
        extra:$extra
      }
    }'
}

measure() {
  local ts0 ts1 wall cmd exit_code
  cmd="$*"
  ts0=$(now_ms)
  tmp=$(mktemp)
  set +e
  /usr/bin/time -f 'USER=%U\nSYS=%S\nMAXRSS=%M' -o "$tmp" bash -c "$cmd"
  exit_code=$?
  set -e
  ts1=$(now_ms)
  wall=$(awk -v a="$ts0" -v b="$ts1" 'BEGIN{print (b-a)/1000.0}')
  user=$(awk -F= '/^USER=/ {print $2}' "$tmp")
  sys=$(awk -F= '/^SYS=/ {print $2}' "$tmp")
  rss=$(awk -F= '/^MAXRSS=/ {print $2}' "$tmp")
  rm -f "$tmp"
  emit_json "$ts0" "$ts1" "$cmd" "$exit_code" "$wall" "$user" "$sys" "$rss"
  return "$exit_code"
}

case "${1:-help}" in
  run)
    shift
    measure "$*"
    ;;
  stress-ng)
    shift
    measure "stress-ng $*"
    ;;
  ffmpeg)
    shift
    measure "ffmpeg $*"
    ;;
  numpy)
    shift
    sub="${1:-matmul}"; shift || true
    measure "python3 /opt/bench/numpy_tasks.py ${sub} $*"
    ;;
  help|--help|-h)
    cat <<USAGE
Usage:
  bench run <any command ...>
  bench stress-ng [--cpu 1 --cpu-method all --metrics-brief --cpu-ops 1000 --timeout 60s ...]
  bench ffmpeg   [common ffmpeg args ...]
  bench numpy    [matmul N | elem N [ITER]]

Env meta (optional): RUN_ID, TASK, DATASET, EXTRA
Output: JSON-string with metrics + stdout/err of the command in plain format
USAGE
    ;;
  *)
    echo "unknown subcommand: $1" >&2; exit 2
    ;;
esac