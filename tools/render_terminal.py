#!/usr/bin/env python3
"""Render captured console output as a Kali-style terminal window PNG."""
import re
import sys

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- palette ----
BG = (26, 28, 35)
BAR = (23, 24, 31)
BORDER = (48, 50, 62)
BTN = (43, 45, 54)
BTN_DARK = (35, 37, 45)
TITLE = (238, 238, 236)
ICON = (208, 211, 218)
GREEN = (46, 194, 126)
BLUE = (39, 127, 255)
FG = (222, 225, 231)
GRAY = (150, 156, 169)
TABLE = (200, 204, 212)
RED = (255, 110, 110)
YELLOW = (240, 200, 80)

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FALLBACK = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"

# ------------------------------------------------------------- dimensions ----
SS = 2                      # supersampling factor
WIDTH = 1480                # final image width
BAR_H = 52
MARGIN_X = 24
PAD_TOP = 16
PAD_BOTTOM = 22
LINE_H = 24
FS = 15
TITLE_FS = 15

PROMPT1 = re.compile(r"^┌──\((?P<user>[^㉿]+)㉿(?P<host>[^)]+)\)-\[(?P<path>.*)\]$")
PROMPT2 = re.compile(r"^└─\$ ?(?P<cmd>.*)$")


def s(v):
    """Scale a 1x coordinate to the supersampled canvas."""
    return int(round(v * SS))


def wrap_text(draw, font, text, first_w, rest_w):
    """Wrap text at spaces (hard-splitting long tokens), in supersampled px."""
    words = text.split(" ")
    lines, cur = [], ""
    avail = first_w
    for word in words:
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=font) <= avail:
            cur = trial
            continue
        if cur:
            lines.append(cur)
            avail = rest_w
            cur = ""
        while draw.textlength(word, font=font) > avail:
            lo, hi = 1, len(word)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if draw.textlength(word[:mid], font=font) <= avail:
                    lo = mid
                else:
                    hi = mid - 1
            lines.append(word[:lo])
            word = word[lo:]
            avail = rest_w
        cur = word
    lines.append(cur)
    return lines


def output_segments(line):
    """Colour a captured console line the way WPScan/apt style output looks."""
    if line.startswith("[+]"):
        segs = [("[+]", GREEN)]
        rest = line[3:]
        for part in re.split(r"(Insecure|Latest)", rest):
            if part == "Insecure":
                segs.append((part, RED))
            elif part == "Latest":
                segs.append((part, GREEN))
            elif part:
                segs.append((part, FG))
        return segs
    if line.startswith("[!]"):
        return [("[!]", RED), (line[3:], FG)]
    if line.startswith("[i]"):
        return [("[i]", BLUE), (line[3:], FG)]
    if line.startswith(" |") or line.startswith("| "):
        return [(line, GRAY)]
    if line.startswith("|"):
        return [(line, TABLE)]
    if line.startswith("XAMPP:"):
        return [(line, FG)]
    return [(line, FG)]


def parse_rows(text):
    rows = []
    for raw in text.rstrip("\n").split("\n"):
        raw = raw.replace("\t", "    ")
        m = PROMPT1.match(raw)
        if m:
            rows.append(("p1", m.group("user"), m.group("host"), m.group("path")))
            continue
        m = PROMPT2.match(raw)
        if m:
            rows.append(("p2", m.group("cmd")))
            continue
        rows.append(("out", raw))
    rows.append(("p1", "olowoyobabajide", "jyde", "~/Documents/wordpress_work"))
    rows.append(("p2", ""))
    return rows


def draw_header(d, width, font_title, font_glyph):
    d.rectangle([0, 0, width, s(BAR_H)], fill=BAR)
    d.line([(0, s(BAR_H)), (width, s(BAR_H))], fill=BORDER, width=s(1))

    # left: terminal button and new-tab button
    d.rounded_rectangle([s(16), s(11), s(52), s(43)], radius=s(7),
                        fill=BTN_DARK, outline=(62, 65, 78), width=s(1))
    d.text((s(34), s(27)), ">_", font=font_glyph, fill=ICON, anchor="mm")

    d.rounded_rectangle([s(58), s(11), s(94), s(43)], radius=s(7), fill=BTN)
    cx, cy = s(76), s(27)
    d.line([(cx - s(6), cy), (cx + s(6), cy)], fill=(228, 231, 238), width=s(2))
    d.line([(cx, cy - s(6)), (cx, cy + s(6))], fill=(228, 231, 238), width=s(2))

    # centred title
    d.text((width // 2, s(27)), "olowoyobabajide@jyde: ~",
           font=font_title, fill=TITLE, anchor="mm")

    # right: search, menu, window controls
    for x in (WIDTH - 186, WIDTH - 146):
        d.rounded_rectangle([s(x), s(11), s(x + 32), s(43)], radius=s(7), fill=BTN)

    scx, scy = s(WIDTH - 170), s(26)
    d.ellipse([scx - s(6), scy - s(6), scx + s(6), scy + s(6)],
              outline=ICON, width=s(2))
    d.line([(scx + s(4), scy + s(4)), (scx + s(9), scy + s(9))],
           fill=ICON, width=s(2))

    mcx = s(WIDTH - 130)
    for dy in (-6, 0, 6):
        d.ellipse([mcx - s(2), s(27 + dy) - s(2), mcx + s(2), s(27 + dy) + s(2)],
                  fill=(232, 235, 241))

    nmx = s(WIDTH - 108)
    d.line([(nmx - s(7), s(27)), (nmx + s(7), s(27))], fill=ICON, width=s(2))
    xmx = s(WIDTH - 72)
    d.rounded_rectangle([xmx - s(6), s(21), xmx + s(6), s(33)],
                        radius=s(2), outline=ICON, width=s(2))

    ccx, ccy = s(WIDTH - 30), s(27)
    d.ellipse([ccx - s(14), ccy - s(14), ccx + s(14), ccy + s(14)], fill=BLUE)
    d.line([(ccx - s(5), ccy - s(5)), (ccx + s(5), ccy + s(5))],
           fill=(255, 255, 255), width=s(2))
    d.line([(ccx - s(5), ccy + s(5)), (ccx + s(5), ccy - s(5))],
           fill=(255, 255, 255), width=s(2))


def main():
    src, out = sys.argv[1], sys.argv[2]
    rows = parse_rows(open(src, encoding="utf-8").read())

    width = WIDTH * SS
    text_w = (WIDTH - 2 * MARGIN_X) * SS

    font = ImageFont.truetype(MONO, s(FS))
    font_b = ImageFont.truetype(MONO_B, s(FS))
    font_title = ImageFont.truetype(SANS, s(TITLE_FS))
    font_glyph = ImageFont.truetype(MONO_B, s(12))
    font_fb = ImageFont.truetype(FALLBACK, s(18))

    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    # Build physical lines: list of segment lists.
    lines = []
    p1_prefix_w = probe.textlength("┌──(", font=font_b)
    p2_prefix_w = probe.textlength("└─$ ", font=font_b)

    for row in rows:
        kind = row[0]
        if kind == "p1":
            _, user, host, path = row
            lines.append([
                ("┌──(", GREEN, font_b),
                (user, BLUE, font_b),
                ("㉿", BLUE, font_fb),
                (host, BLUE, font_b),
                (")-[", GREEN, font_b),
                (path, GREEN, font_b),
                ("]", GREEN, font_b),
            ])
        elif kind == "p2":
            cmd = row[1]
            chunks = wrap_text(probe, font, cmd, text_w - p2_prefix_w, text_w) if cmd else [""]
            lines.append([
                ("└─", GREEN, font_b),
                ("$ ", BLUE, font_b),
                (chunks[0], FG, font),
            ])
            for extra in chunks[1:]:
                lines.append([(extra, FG, font)])
        else:
            text = row[1]
            if not text:
                lines.append([])
                continue
            for part in wrap_text(probe, font, text, text_w, text_w):
                lines.append([(t, c, font) for t, c in output_segments(part)])

    height = BAR_H + PAD_TOP + len(lines) * LINE_H + PAD_BOTTOM
    img = Image.new("RGBA", (WIDTH * SS, height * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle([0, 0, width - 1, height * SS - 1],
                        radius=s(10), fill=BAR)
    d.rectangle([0, s(BAR_H), width, height * SS], fill=BG)
    draw_header(d, width, font_title, font_glyph)
    d.rounded_rectangle([0, 0, width - 1, height * SS - 1],
                        radius=s(10), outline=BORDER, width=s(1))

    y = (BAR_H + PAD_TOP) * SS
    for segs in lines:
        x = MARGIN_X * SS
        baseline = y + int(LINE_H * 0.78 * SS)
        for text, color, f in segs:
            pad = s(2) if text == "㉿" else 0
            d.text((x + pad, baseline), text, font=f, fill=color, anchor="ls")
            x += probe.textlength(text, font=f) + 2 * pad
        y += LINE_H * SS

    img = img.resize((WIDTH, height), Image.LANCZOS)
    img.save(out)
    print(out, img.size)


if __name__ == "__main__":
    main()
