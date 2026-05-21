#!/usr/bin/env python3
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
from collections import defaultdict

GITHUB_USER = "Ywj-ch"
EXCLUDE_REPOS = {"Ywj-ch.github.io"}
LIMIT = 8
OUTPUT = pathlib.Path("assets/top-langs.svg")

API_BASE = "https://api.github.com"

COLORS = {
    "C++": "#f34b7d",
    "C": "#555555",
    "Java": "#b07219",
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Vue": "#41b883",
    "CSS": "#563d7c",
    "HTML": "#e34c26",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "Ruby": "#701516",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "PHP": "#4F5D95",
    "Kotlin": "#A97BFF",
    "Scala": "#c22d40",
    "Objective-C": "#438eff",
    "Lua": "#000080",
    "Dart": "#00B4AB",
    "Elixir": "#6e4a7e",
    "Haskell": "#5e5086",
    "Clojure": "#db5855",
    "Groovy": "#4298b8",
    "Perl": "#0298c3",
    "R": "#198ce7",
    "MATLAB": "#e16737",
    "Assembly": "#6E4C13",
    "Solidity": "#AA6746",
    "TeX": "#3D6117",
    "CMake": "#DA3434",
    "Makefile": "#427819",
    "Procfile": "#3B2F63",
    "Blade": "#f7523f",
    "Sass": "#a53b70",
    "SCSS": "#c6538c",
    "Less": "#1d365d",
}


def api(path):
    url = f"{API_BASE}{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{GITHUB_USER}-lang-stats",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"API error {e.code} for {url}: {body}", file=sys.stderr)
        return None
    except (urllib.error.URLError, OSError) as e:
        print(f"Network error for {url}: {e}", file=sys.stderr)
        return None


def get_all_repos():
    repos = []
    page = 1
    while True:
        data = api(f"/users/{GITHUB_USER}/repos?per_page=100&page={page}&type=public&sort=updated")
        if data is None or not data:
            break
        repos.extend(data)
        page += 1
    return repos


def get_languages(repo_full_name):
    return api(f"/repos/{repo_full_name}/languages")


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def generate_svg(languages):
    total = sum(languages.values())
    sorted_langs = sorted(languages.items(), key=lambda x: -x[1])

    others_count = sum(v for k, v in sorted_langs[LIMIT:])
    displayed = list(sorted_langs[:LIMIT])
    if others_count > 0:
        displayed.append(("Others", others_count))

    total_displayed = sum(v for _, v in displayed)

    items = []
    for name, bytes_count in displayed:
        pct = bytes_count / total_displayed * 100
        items.append((name, bytes_count, pct))

    W = 340
    PAD = 20
    ROW_H = 28
    HEADER_H = 45
    BAR_W = 180
    NAME_W = 85
    H = HEADER_H + len(items) * ROW_H + PAD

    def svg_tag(name, **attrs):
        a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return f"  <{name} {a}/>"

    L = []
    L.append(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">')

    L.append("  <defs>")
    L.append('    <linearGradient id="card-bg" x1="0" y1="0" x2="0" y2="1">')
    L.append('      <stop offset="0%" stop-color="#1a1b27"/>')
    L.append('      <stop offset="100%" stop-color="#141b2d"/>')
    L.append("    </linearGradient>")
    L.append("  </defs>")

    L.append(svg_tag("rect", width=W, height=H, fill="url(#card-bg)", rx=10))
    L.append(svg_tag("rect", x=0.5, y=0.5, width=W - 1, height=H - 1, fill="none", stroke="#30363d", **{"stroke-width": 1}, rx=10))

    L.append(f'  <text x="{PAD}" y="30" fill="#f0f6fc" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',Helvetica,Arial,sans-serif" font-size="14" font-weight="600">Most Used Languages</text>')

    y = HEADER_H
    for name, _, pct in items:
        color = COLORS.get(name, "#666666")
        pct_str = f"{pct:.1f}%"
        filled = max(int(BAR_W * pct / 100), 1)

        x_bar = PAD + NAME_W
        x_pct = x_bar + BAR_W + 8

        L.append(f'  <text x="{PAD}" y="{y + 12}" fill="#8b949e" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',Helvetica,Arial,sans-serif" font-size="12">{esc(name)}</text>')
        L.append(svg_tag("rect", x=x_bar, y=y + 2, width=BAR_W, height=10, fill="#2d2d3a", rx=5))
        L.append(svg_tag("rect", x=x_bar, y=y + 2, width=filled, height=10, fill=color, rx=5))

        L.append(f'  <text x="{x_pct}" y="{y + 12}" fill="#c9d1d9" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',Helvetica,Arial,sans-serif" font-size="12">{pct_str}</text>')

        y += ROW_H

    L.append("</svg>")
    return "\n".join(L) + "\n"


def main():
    print("Fetching repositories...")
    repos = get_all_repos()
    if not repos:
        print("Failed to fetch repos, aborting.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(repos)} repositories")

    repo_names = [r["full_name"] for r in repos if r["name"] not in EXCLUDE_REPOS]
    print(f"Processing {len(repo_names)} repositories (after exclusions)...")

    all_langs = defaultdict(int)
    for full_name in repo_names:
        langs = get_languages(full_name)
        if langs is None:
            print(f"  Skipping {full_name} (API error)")
            continue
        if not langs:
            continue
        name = full_name.split("/")[1]
        detail = ", ".join(f"{k}:{v:,}" for k, v in sorted(langs.items(), key=lambda x: -x[1]))
        print(f"  {name}  ->  {detail}")
        for lang, count in langs.items():
            all_langs[lang] += count

    if not all_langs:
        print("No language data found!", file=sys.stderr)
        sys.exit(1)

    total = sum(all_langs.values())
    print(f"\nTotal: {total:,} bytes across {len(all_langs)} languages")

    svg = generate_svg(dict(all_langs))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"\nSVG written to {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
