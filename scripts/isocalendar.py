#!/usr/bin/env python3
"""
isocalendar.py - generates a 3D isometric contribution calendar SVG.
"""

import argparse
import datetime as dt
import json
import sys
import urllib.request
import urllib.error
import os
from pathlib import Path

CONTRIB_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

THEMES = {
    "dark": {
        "bg": "#0d1117", "text": "#c9d1d9",
        "colors": {
            0: ("#161b22", "#0d1117", "#21262d"),
            1: ("#0e4429", "#002d11", "#165c36"),
            2: ("#006d32", "#005323", "#00873d"),
            3: ("#26a641", "#168a30", "#33c24f"),
            4: ("#39d353", "#23b43b", "#4ff267"),
        }
    },
    "light": {
        "bg": "#ffffff", "text": "#1f2328",
        "colors": {
            0: ("#ebedf0", "#d1d5da", "#f3f4f6"),
            1: ("#9be9a8", "#79c98a", "#b5ebb0"),
            2: ("#40c463", "#2ea043", "#58d576"),
            3: ("#30a14e", "#21853a", "#42b65e"),
            4: ("#216e39", "#115225", "#2a8244"),
        }
    }
}

def graphql(query: str, variables: dict, token: str):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={"Authorization": f"bearer {token}", "User-Agent": "isocalendar.py"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def get_data(user: str, token: str):
    if not token:
        print("warn: no token, generating dummy data", file=sys.stderr)
        today = dt.date.today()
        days = [(today - dt.timedelta(days=i), (i*7)%25 if (i*7)%25 > 10 else 0) for i in range(365)]
        days.sort()
        return days, 1500
    try:
        data = graphql(CONTRIB_QUERY, {"login": user}, token)
    except urllib.error.HTTPError as e:
        print(f"error: HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
        
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total = cal["totalContributions"]
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"])
            for w in cal["weeks"] for d in w["contributionDays"]]
    days.sort()
    return days, total

def generate_svg(days, total, theme_name):
    theme = THEMES[theme_name]
    
    # Calculate stats
    longest = run = current = 0
    max_day = 0
    for _, c in days:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
        if c > 0:
            current = run
        max_day = max(max_day, c)
        
    avg = total / len(days) if days else 0
    
    # SVG parameters
    DX, DY = 14, 8
    DZ = 3
    W, H = 1060, 500
    OX, OY = 100, 24
    
    blue = "#58a6ff" if theme_name == "dark" else "#0969da"
    gray = "#8b949e" if theme_name == "dark" else "#57606a"
    
    tx = 830
    ty = 140
    
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="{theme["bg"]}" rx="10"/>',
        
        f'<text x="{tx}" y="{ty}" fill="{blue}" font-family="sans-serif" font-weight="bold" font-size="16">Commits streaks</text>',
        f'<text x="{tx}" y="{ty+24}" fill="{gray}" font-family="sans-serif" font-size="14">Current streak {current:,} days</text>',
        f'<text x="{tx}" y="{ty+44}" fill="{gray}" font-family="sans-serif" font-size="14">Best streak {longest:,} days</text>',
        
        f'<text x="{tx}" y="{ty+94}" fill="{blue}" font-family="sans-serif" font-weight="bold" font-size="16">Commits per day</text>',
        f'<text x="{tx}" y="{ty+118}" fill="{gray}" font-family="sans-serif" font-size="14">Highest in a day at {max_day:,}</text>',
        f'<text x="{tx}" y="{ty+138}" fill="{gray}" font-family="sans-serif" font-size="14">Average per day at ~{avg:.2f}</text>',
        '<g>'
    ]
    
    start_dow = days[0][0].weekday()
    start_dow = (start_dow + 1) % 7
    
    blocks = []
    for i, (date, count) in enumerate(days):
        week = (i + start_dow) // 7
        day = (i + start_dow) % 7
        
        level = 0
        if count > 0:
            if max_day > 0:
                level = min(4, 1 + int(3 * (count / max_day)))
            else:
                level = 1
                
        px = (week - day) * DX + OX
        py = (week + day) * DY + OY
        h = count * DZ if count > 0 else 0
        if count > 0 and h < DZ:
            h = DZ
            
        c_top, c_left, c_right = theme["colors"][level]
        blocks.append((week + day, px, py, h, c_top, c_left, c_right))
        
    blocks.sort(key=lambda b: b[0])
    
    for _, px, py, h, c_top, c_left, c_right in blocks:
        pts = f"{px},{py-h-DY} {px+DX},{py-h} {px},{py-h+DY} {px-DX},{py-h}"
        svg.append(f'<polygon points="{pts}" fill="{c_top}"/>')
        if h > 0:
            pts = f"{px-DX},{py-h} {px},{py-h+DY} {px},{py+DY} {px-DX},{py}"
            svg.append(f'<polygon points="{pts}" fill="{c_left}"/>')
            pts = f"{px},{py-h+DY} {px+DX},{py-h} {px+DX},{py} {px},{py+DY}"
            svg.append(f'<polygon points="{pts}" fill="{c_right}"/>')
            
    svg.append('</g>')
    svg.append('</svg>')
    return "\\n".join(svg)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", required=True)
    parser.add_argument("-o", "--out", type=Path, required=True)
    args = parser.parse_args()
    
    token = os.environ.get("GITHUB_TOKEN")
    days, total = get_data(args.user, token)
    
    for t in ("dark", "light"):
        dest = args.out.parent / f"{args.out.name}-{t}.svg"
        dest.write_text(generate_svg(days, total, t), encoding="utf-8")
        print(f"wrote {dest}")

if __name__ == "__main__":
    main()
