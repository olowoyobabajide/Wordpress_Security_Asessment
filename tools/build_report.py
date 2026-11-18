#!/usr/bin/env python3
"""Build the styled HTML report from the Markdown source."""
import pathlib
import markdown

BASE = pathlib.Path(__file__).resolve().parent.parent
REPORT = BASE / "report"
SRC = REPORT / "wordpress-core-security-report.md"

text = SRC.read_text()
marker = "## 1. Executive summary"
body = text[text.index(marker):]
html_body = markdown.markdown(body, extensions=["tables", "fenced_code", "sane_lists", "attr_list"])

cover = """
<div class="cover">
  <div class="kicker">Security assessment report</div>
  <h1>Comparative Security Assessment of WordPress 4.0.38 (Site A) and WordPress 7.1.4 (Site B) on XAMPP</h1>
  <div class="rule"></div>
  <table class="meta">
    <tr><td>Prepared by</td><td>Olowoyobabajide</td></tr>
    <tr><td>Date</td><td>15 November 2026</td></tr>
    <tr><td>Platform</td><td>Kali GNU/Linux Rolling 2026.2 &middot; XAMPP for Linux 8.2.12-0</td></tr>
    <tr><td>Targets</td><td>Site A: WordPress 4.0.38 &middot; Site B: WordPress 7.1.4</td></tr>
    <tr><td>Scanner</td><td>WPScan 4.1.0</td></tr>
  </table>
</div>
"""

css = """
@page { size: A4; margin: 16mm 15mm 15mm 15mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { -webkit-print-color-adjust: exact; print-color-adjust: exact; font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif; font-size: 10.2pt; line-height: 1.5; color: #1b1b1b; margin: 0; }
.cover { page-break-after: always; padding-top: 55mm; }
.kicker { font-size: 10pt; letter-spacing: 0.18em; text-transform: uppercase; color: #8a1c1c; font-weight: bold; }
.cover h1 { font-size: 25pt; line-height: 1.2; margin: 8mm 0 6mm 0; color: #111; border: 0; page-break-after: auto; }
.rule { height: 0; width: 34mm; border-top: 3px solid #8a1c1c; margin-bottom: 12mm; }
table.meta { border: 0; width: 100%; font-size: 10pt; margin: 0; }
table.meta td { border: 0; padding: 2.2mm 0; vertical-align: top; background: transparent !important; }
table.meta td:first-child { width: 34mm; color: #666; text-transform: uppercase; font-size: 8.5pt; letter-spacing: .08em; }
h2 { font-size: 16pt; color: #8a1c1c; margin: 13mm 0 4mm 0; padding-bottom: 2mm; border-bottom: 1px solid #d8d8d8; page-break-after: avoid; }
h2:first-of-type { margin-top: 0; }
h3 { font-size: 12.2pt; color: #1f1f1f; margin: 8mm 0 2.5mm 0; page-break-after: avoid; }
h4 { font-size: 10.8pt; margin: 5mm 0 2mm 0; page-break-after: avoid; }
p { margin: 0 0 3mm 0; text-align: justify; }
ul, ol { margin: 0 0 3.5mm 0; padding-left: 6mm; }
li { margin-bottom: 1.4mm; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.8pt; background: #f2f2f2; padding: 0.3mm 1mm; border-radius: 2px; }
pre { background: #14181f; color: #e6edf3; padding: 4mm; border-radius: 2mm; font-size: 8.4pt; line-height: 1.45; overflow-wrap: break-word; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; color: inherit; padding: 0; font-size: 8.4pt; }
table { width: 100%; border-collapse: collapse; margin: 3mm 0 5mm 0; font-size: 9pt; page-break-inside: avoid; }
th, td { border: 0.6pt solid #cfcfcf; padding: 2mm 2.4mm; vertical-align: top; text-align: left; }
th { background: #f0eeee; font-weight: bold; border-bottom: 1.4pt solid #8a1c1c; }
tr:nth-child(even) td { background: #fafafa; }
img { display: block; max-width: 100%; max-height: 232mm; width: auto; height: auto; margin: 3mm auto 1mm auto; border: 0.6pt solid #c9c9c9; page-break-inside: avoid; }
img.tall { max-height: 250mm; }
p > em { display: block; text-align: center; font-size: 8.6pt; color: #555; margin: 1mm 0 6mm 0; }
hr { border: 0; border-top: 1px solid #ddd; margin: 6mm 0; }
strong { color: #111; }
blockquote { border-left: 3px solid #8a1c1c; margin: 3mm 0; padding: 1mm 4mm; color: #333; background: #faf7f7; }
"""

doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>WordPress Core Security Assessment</title>
<style>{css}</style></head>
<body>
{cover}
{html_body}
</body></html>"""

out = REPORT / "wordpress-core-security-report.html"
out.write_text(doc)
print(out, len(doc))
