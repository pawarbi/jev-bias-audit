"""Inject results/bundle.json into the report template."""
from pathlib import Path

root = Path(__file__).resolve().parent.parent
tpl = (root / "report" / "template.html").read_text(encoding="utf-8")
data = (root / "results" / "bundle.json").read_text(encoding="utf-8").replace("</", "<\\/")
html = tpl.replace("/*BUNDLE*/", data)
out = root / "report" / "jev-swap-test.html"
out.write_text(html, encoding="utf-8")
print(out, len(html) // 1024, "KB")
