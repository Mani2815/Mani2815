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
        "bg": "transparent", "text": "#c9d1d9",
        "colors": {
            0: ("#ebedf0", "#d1d5da", "#f3f4f6"),
            1: ("#0e4429", "#002d11", "#165c36"),
            2: ("#006d32", "#005323", "#00873d"),
            3: ("#26a641", "#168a30", "#33c24f"),
            4: ("#39d353", "#23b43b", "#4ff267"),
        }
    },
    "light": {
        "bg": "transparent", "text": "#1f2328",
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
    DX, DY = 16, 9
    DZ = 4
    W, H = 1450, 850
    OX, OY = 160, 280
    
    blue = "#0969da" if theme_name == "light" else "#58a6ff"
    gray = "#57606a" if theme_name == "light" else "#8b949e"
    
    tx = 1060
    ty = 180
    
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="{theme["bg"]}" rx="10"/>',
        
        # Title
        f'<g transform="translate(60, 50)">',
        f'<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="{blue}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',
        f'<text x="48" y="26" fill="{blue}" font-family="sans-serif" font-weight="bold" font-size="32">Contributions calendar</text>',
        f'</g>',
        
        # Commits streaks
        f'<g transform="translate({tx}, {ty})">',
        f'<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="{blue}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="4" y="4" width="6" height="16"></rect></svg>',
        f'<text x="44" y="24" fill="{blue}" font-family="sans-serif" font-weight="bold" font-size="26">Commits streaks</text>',
        
        # Current streak
        f'<g transform="translate(0, 44)">',
        f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{gray}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 11-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 2.5z"></path></svg>',
        f'<text x="40" y="20" fill="{gray}" font-family="sans-serif" font-size="24">Current streak {current:,} days</text>',
        f'</g>',
        
        # Best streak
        f'<g transform="translate(0, 88)">',
        f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{gray}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5l-10 14M22 12H2M19 19L5 5"></path></svg>',
        f'<text x="40" y="20" fill="{gray}" font-family="sans-serif" font-size="24">Best streak {longest:,} days</text>',
        f'</g>',
        f'</g>',
        
        # Commits per day
        f'<g transform="translate({tx}, {ty + 160})">',
        f'<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="{blue}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><line x1="3" y1="12" x2="9" y2="12"></line><line x1="15" y1="12" x2="21" y2="12"></line></svg>',
        f'<text x="44" y="24" fill="{blue}" font-family="sans-serif" font-weight="bold" font-size="26">Commits per day</text>',
        
        # Highest in a day
        f'<g transform="translate(0, 44)">',
        f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{gray}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>',
        f'<text x="40" y="20" fill="{gray}" font-family="sans-serif" font-size="24">Highest in a day at {max_day:,}</text>',
        f'</g>',
        
        # Average per day
        f'<g transform="translate(0, 88)">',
        f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{gray}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>',
        f'<text x="40" y="20" fill="{gray}" font-family="sans-serif" font-size="24">Average per day at ~{avg:.2f}</text>',
        f'</g>',
        f'</g>',
        
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
