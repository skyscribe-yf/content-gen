"""
apimart.ai 任务轮询下载工具

用法:
  python scripts/poll_tasks.py OUTPUT_DIR TASK_ID:filename.png [TASK_ID:filename.png ...]

示例:
  python scripts/poll_tasks.py content/2026-07-15-deepseek-moe \\
    task_01KX1ZBT:03-bias-trick.png \\
    task_01KX1ZTB:04-moe-dataflow.png

自动从项目根 .env 读取 API_MART_KEY，轮询任务状态，完成后下载到指定目录。
"""
import requests
import os
import time
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env():
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        for line in open(env_path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'\"")


def poll_and_download(output_dir: str, task_map: dict[str, str], poll_interval: int = 10, max_attempts: int = 60):
    key = os.environ.get("API_MART_KEY", "")
    headers = {"Authorization": f"Bearer {key}"}
    os.makedirs(output_dir, exist_ok=True)

    pending = set(task_map.keys())
    for attempt in range(max_attempts):
        if not pending:
            break
        for tid in list(pending):
            try:
                resp = requests.get(f"https://api.apimart.ai/v1/tasks/{tid}", headers=headers, timeout=10)
                data = resp.json()
                inner = data.get("data", data)
                status = inner.get("status", "")
                progress = inner.get("progress", "?")

                if status == "completed":
                    images = inner.get("result", {}).get("images", [])
                    if images and images[0].get("url"):
                        url = images[0]["url"][0]
                        img = requests.get(url, timeout=60).content
                        fname = task_map[tid]
                        path = os.path.join(output_dir, fname)
                        with open(path, "wb") as f:
                            f.write(img)
                        cost = inner.get("cost", "?")
                        print(f"✅ {fname} ({len(img)//1024}KB, ${cost})")
                        pending.remove(tid)
                    else:
                        print(f"⚠️ {tid}: completed but no images")
                        pending.remove(tid)
                elif status == "failed":
                    err = inner.get("error", {}).get("message", "unknown")
                    print(f"❌ {task_map[tid]}: {err}")
                    pending.remove(tid)
                else:
                    if attempt % 5 == 0:
                        print(f"⏳ {task_map[tid]}: {status} ({progress}%)")
            except Exception as e:
                print(f"⚠️ {tid}: {e}")

        if pending:
            time.sleep(poll_interval)

    if pending:
        print(f"⚠️ Still pending after timeout: {[task_map[t] for t in pending]}")
        sys.exit(1)
    else:
        print("🎉 All done!")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    output_dir = sys.argv[1]
    task_map = {}
    for arg in sys.argv[2:]:
        tid, fname = arg.split(":", 1)
        task_map[tid.strip()] = fname.strip()

    load_env()
    poll_and_download(output_dir, task_map)
