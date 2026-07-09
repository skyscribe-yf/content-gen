"""
热点检测 Pipeline — 检查AI领域新模型/调价/重大事件

数据源:
  - HuggingFace trending models
  - OpenAI/Anthropic/DeepSeek changelog
  - GitHub trending AI repos

用法:
  python3 hotspot-pipeline.py check          # 检查最近热点
  python3 hotspot-pipeline.py check --days 7 # 检查最近7天
  python3 hotspot-pipeline.py models         # 列出最近新发布的模型
  python3 hotspot-pipeline.py prices         # 检查价格变动
"""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("需要 requests: pip install requests")

ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

# ── 热点与选题映射 ──

HOTSPOT_MAP = {
    "openai": {
        "keywords": ["gpt", "o1", "o3", "o4", "dall-e", "sora", "openai"],
        "triggers": ["新模型发布", "重大调价", "新功能"],
        "topics": ["E1 coding实测", "E6 价格速报", "F6 CoT/思维链"],
    },
    "anthropic": {
        "keywords": ["claude", "anthropic"],
        "triggers": ["新模型发布", "新功能"],
        "topics": ["E1 coding实测", "F2 注意力衰减"],
    },
    "deepseek": {
        "keywords": ["deepseek", "r1", "v3"],
        "triggers": ["新模型发布", "重大调价"],
        "topics": ["E5 开源vs闭源", "F1 MoE架构", "E6 价格速报"],
    },
    "google": {
        "keywords": ["gemini", "google ai", "bard"],
        "triggers": ["新模型发布"],
        "topics": ["E1 coding实测", "F2 长上下文"],
    },
    "meta": {
        "keywords": ["llama", "meta ai"],
        "triggers": ["新开源模型"],
        "topics": ["E5 开源vs闭源", "F7 多任务学习"],
    },
    "image_gen": {
        "keywords": ["midjourney", "stable diffusion", "flux", "dall-e", "sora"],
        "triggers": ["新图像模型"],
        "topics": ["E3 画图对比", "F3 扩散采样"],
    },
}


def _fetch_hf_trending() -> list[dict]:
    """获取HuggingFace trending模型"""
    try:
        # ponytail: 用非官方API，可能随时变，失败就跳过
        resp = requests.get(
            "https://huggingface.co/api/trending",
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            models = []
            for item in data.get("recentModels", [])[:10]:
                models.append({
                    "name": item.get("id", ""),
                    "likes": item.get("likes", 0),
                    "url": f"https://huggingface.co/{item.get('id', '')}",
                })
            return models
    except Exception:
        pass
    return []


def _fetch_github_trending() -> list[dict]:
    """获取GitHub trending AI repos"""
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={
                "q": f"AI LLM model created:>{(date.today() - timedelta(days=7)).isoformat()}",
                "sort": "stars",
                "order": "desc",
                "per_page": 10,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            repos = []
            for item in data.get("items", [])[:10]:
                repos.append({
                    "name": item.get("full_name", ""),
                    "stars": item.get("stargazers_count", 0),
                    "desc": item.get("description", "")[:80],
                    "url": item.get("html_url", ""),
                })
            return repos
    except Exception:
        pass
    return []


def _match_hotspot(text: str) -> list[str]:
    """匹配文本到热点类别"""
    text_lower = text.lower()
    matched = []
    for category, info in HOTSPOT_MAP.items():
        for kw in info["keywords"]:
            if kw in text_lower:
                matched.append(category)
                break
    return matched


def check(days: int = 3):
    """检查最近热点"""
    print(f"\n🔍 热点检测（最近 {days} 天）\n")
    print("=" * 60)

    # 1. HuggingFace trending
    print("\n📊 HuggingFace Trending 模型:")
    hf_models = _fetch_hf_trending()
    if hf_models:
        for m in hf_models[:5]:
            categories = _match_hotspot(m["name"])
            topic_suggestions = []
            for c in categories:
                topic_suggestions.extend(HOTSPOT_MAP[c]["topics"])

            print(f"  🔥 {m['name']} ({m['likes']} likes)")
            if topic_suggestions:
                print(f"     → 选题建议: {', '.join(topic_suggestions[:3])}")
    else:
        print("  ⚠️ 无法获取（网络问题）")

    # 2. GitHub trending
    print("\n💻 GitHub AI Trending:")
    gh_repos = _fetch_github_trending()
    if gh_repos:
        for r in gh_repos[:5]:
            categories = _match_hotspot(r["name"] + " " + r["desc"])
            topic_suggestions = []
            for c in categories:
                topic_suggestions.extend(HOTSPOT_MAP[c]["topics"])

            print(f"  ⭐ {r['name']} ({r['stars']} stars)")
            print(f"     {r['desc']}")
            if topic_suggestions:
                print(f"     → 选题建议: {', '.join(topic_suggestions[:3])}")
    else:
        print("  ⚠️ 无法获取（网络问题）")

    # 3. 价格变动检查
    print("\n💰 价格变动:")
    price_pipeline = Path(__file__).parent / "price-pipeline.py"
    try:
        result = subprocess.run(
            [sys.executable, str(price_pipeline), "diff"],
            capture_output=True, text=True, timeout=10,
        )
        if result.stdout.strip():
            print(result.stdout)
        else:
            print("  ✅ 无变动")
    except Exception:
        print("  ⚠️ 无法检查")

    # 4. 综合建议
    print("\n" + "=" * 60)
    print("🎯 综合选题建议:\n")

    all_suggestions = {}
    for m in hf_models[:5]:
        for c in _match_hotspot(m["name"]):
            for t in HOTSPOT_MAP[c]["topics"]:
                all_suggestions[t] = all_suggestions.get(t, 0) + 1

    for r in gh_repos[:5]:
        for c in _match_hotspot(r["name"] + " " + r["desc"]):
            for t in HOTSPOT_MAP[c]["topics"]:
                all_suggestions[t] = all_suggestions.get(t, 0) + 1

    if all_suggestions:
        sorted_suggestions = sorted(all_suggestions.items(), key=lambda x: -x[1])
        for topic, count in sorted_suggestions[:5]:
            print(f"  ⭐ {topic} (热度: {count})")
    else:
        print("  暂无强热点，继续按系列排期写原理篇")

    # 保存缓存
    cache_file = CACHE_DIR / f"hotspot-{date.today().isoformat()}.json"
    cache_file.write_text(json.dumps({
        "date": date.today().isoformat(),
        "hf_models": hf_models,
        "gh_repos": gh_repos,
        "suggestions": all_suggestions,
    }, ensure_ascii=False, indent=2))


def list_models():
    """列出最近新模型"""
    print("\n🤖 最近热门AI模型:\n")
    hf_models = _fetch_hf_trending()
    for m in hf_models[:10]:
        print(f"  {m['name']:<40s} {m['likes']:>6d} likes  {m['url']}")


def check_prices():
    """检查价格变动"""
    price_pipeline = Path(__file__).parent / "price-pipeline.py"
    subprocess.run([sys.executable, str(price_pipeline), "diff"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="热点检测Pipeline")
    sub = parser.add_subparsers(dest="command")

    check_p = sub.add_parser("check", help="检查热点")
    check_p.add_argument("--days", type=int, default=3, help="检查天数")

    sub.add_parser("models", help="列出最近新模型")
    sub.add_parser("prices", help="检查价格变动")

    args = parser.parse_args()

    if args.command == "check":
        check(args.days)
    elif args.command == "models":
        list_models()
    elif args.command == "prices":
        check_prices()
    else:
        parser.print_help()
