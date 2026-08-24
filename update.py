import sys
import re

with open("scripts/isocalendar.py", "r") as f:
    code = f.read()

# Update THEMES dict for transparent bg and light plane in dark mode
code = re.sub(
    r'"dark":\s*\{[^}]*"bg":\s*"[^"]*",\s*"text":\s*"[^"]*",\s*"colors":\s*\{\s*0:\s*\("[^"]*",\s*"[^"]*",\s*"[^"]*"\),',
    '"dark": {\n        "bg": "transparent", "text": "#c9d1d9",\n        "colors": {\n            0: ("#ebedf0", "#d1d5da", "#f3f4f6"),',
    code
)
# Make light theme bg transparent too
code = re.sub(
    r'"light":\s*\{[^}]*"bg":\s*"[^"]*",',
    '"light": {\n        "bg": "transparent",',
    code
)

with open("scripts/isocalendar.py", "w") as f:
    f.write(code)
