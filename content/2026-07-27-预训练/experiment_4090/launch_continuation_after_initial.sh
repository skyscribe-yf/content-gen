#!/usr/bin/env bash
set -euo pipefail

root=/root/autodl-tmp/pretraining-demo
output_dir="$root/artifacts/gpu-main-20260716-final-artifacts"
initial_pid_file="$root/logs/gpu-main-20260716-final-artifacts.pid"
continuation_log="$root/logs/gpu-main-20260716-continuation.log"
continuation_pid_file="$root/logs/gpu-main-20260716-continuation.pid"
monitor_log="$root/logs/gpu-main-20260716-continuation-monitor.log"
monitor_pid_file="$root/logs/gpu-main-20260716-continuation-monitor.pid"
python="$root/../conda/envs/pretrain-4090/bin/python"

initial_pid=$(<"$initial_pid_file")
while kill -0 "$initial_pid" 2>/dev/null; do
  sleep 30
done

checkpoint="$output_dir/checkpoint.pt"
while [[ ! -s "$checkpoint" ]]; do
  sleep 10
done

cp -n "$checkpoint" "$output_dir/checkpoint-60m.pt"
cp -n "$output_dir/metrics.jsonl" "$output_dir/metrics-60m.jsonl"
cp -n "$output_dir/summary.json" "$output_dir/summary-60m.json"
if [[ ! -f "$output_dir/best-checkpoint-60m.pt" ]]; then
  cp "$output_dir/best-checkpoint.pt" "$output_dir/best-checkpoint-60m.pt"
fi

"$python" "$root/continue_4090.py" \
  --checkpoint "$checkpoint" \
  --archive "$root/data/TinyStoriesChinese/TinyStories_all_data_zh.tar.gz" \
  --output-dir "$output_dir" \
  --max-minutes 30 >"$continuation_log" 2>&1 &
continuation_pid=$!
printf '%s\n' "$continuation_pid" >"$continuation_pid_file"

nohup bash -c '
  set -euo pipefail
  pid=$1
  output_dir=$2
  monitor_log=$3
  while kill -0 "$pid" 2>/dev/null; do
    {
      date -Is
      ps -p "$pid" -o etime=,pcpu=,pmem=,rss=
      nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
      tail -n 1 "$output_dir/metrics.jsonl" 2>/dev/null || true
    } >>"$monitor_log"
    for _ in 1 2 3; do sleep 30; done
  done
  printf "%s\n" "monitor stopped: continuation process exited" >>"$monitor_log"
' _ "$continuation_pid" "$output_dir" "$monitor_log" >/dev/null 2>&1 &
printf '%s\n' "$!" >"$monitor_pid_file"

wait "$continuation_pid"
"$python" "$root/analyze_metrics.py" --metrics "$output_dir/metrics.jsonl" --output-dir "$output_dir" >>"$continuation_log" 2>&1
