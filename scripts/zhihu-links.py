#!/usr/bin/env python3
"""
知乎链接替换 — 将微信链接替换为知乎链接

promote/zhihu-*.md 中的内文引用、系列导航、文末链接等出现
的 mp.weixin.qq.com URL，需要替换为知乎专栏/回答的 URL。

映射表：templates/zhihu-urls.yaml

用法：
  python3 scripts/zhihu-links.py <input.md> --mapping templates/zhihu-urls.yaml
  python3 scripts/zhihu-links.py <input.md> --mapping templates/zhihu-urls.yaml --dry-run
"""

import re
import sys
import yaml
import argparse
from pathlib import Path


def load_mapping(mapping_path: str) -> dict:
    """加载微信 URL → 知乎 URL 的映射表"""
    path = Path(mapping_path)
    if not path.exists():
        print(f"⚠️  映射表不存在: {mapping_path}")
        print(f"   请创建映射文件，格式：")
        print(f"   wechat_url: zhihu_url")
        return {}
    
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    
    return data.get('mappings', data) if isinstance(data, dict) else data


def replace_links(content: str, mapping: dict) -> tuple[str, list[str]]:
    """替换内容中的微信链接为知乎链接"""
    changes = []
    
    for wechat_url, zhihu_url in mapping.items():
        if wechat_url in content:
            content = content.replace(wechat_url, zhihu_url)
            changes.append(f"  {wechat_url} → {zhihu_url}")
    
    # 处理剩余未映射的微信链接
    remaining = re.findall(r'https://mp\.weixin\.qq\.com/\S+', content)
    for url in remaining:
        # 替换为纯文字提及
        content = content.replace(url, '（原文发于公众号數解AI）')
        changes.append(f"  {url} →（原文发于公众号數解AI）[未映射]")
    
    return content, changes


def extract_all_links(content: str) -> list[str]:
    """提取文件中所有外链（用于构建初始映射表）"""
    wechat_links = re.findall(r'https://mp\.weixin\.qq\.com/\S+', content)
    zhihu_links = re.findall(r'https://(?:zhuanlan\.zhihu\.com|www\.zhihu\.com)/\S+', content)
    return list(set(wechat_links + zhihu_links))


def preprocess_file(filepath: str, mapping: dict, dry_run: bool = False) -> str:
    """处理文件"""
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    
    new_content, changes = replace_links(content, mapping)
    
    if changes:
        print(f"📝 {filepath} 链接替换:")
        for c in changes:
            print(c)
    else:
        print(f"📝 {filepath}: 无需替换")
    
    if dry_run:
        return filepath
    
    outpath = filepath.replace('.md', '.zhihu.md')
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 已保存: {outpath}")
    return outpath


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='知乎链接替换工具')
    parser.add_argument('input', help='输入文件路径')
    parser.add_argument('--mapping', '-m', required=True, help='映射表 YAML 路径')
    parser.add_argument('--dry-run', '-n', action='store_true', help='仅报告，不输出文件')
    parser.add_argument('--extract', '-e', action='store_true', help='提取所有外链')
    args = parser.parse_args()
    
    content = Path(args.input).read_text(encoding='utf-8')
    
    if args.extract:
        links = extract_all_links(content)
        print(f"📋 {args.input} 中的所有链接:")
        for link in sorted(links):
            print(f"   {link}")
    else:
        mapping = load_mapping(args.mapping)
        preprocess_file(args.input, mapping, args.dry_run)
