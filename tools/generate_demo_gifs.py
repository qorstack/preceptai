from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "demo"
TRANSCRIPTS = OUT_DIR / "transcripts"
LOGO = ROOT / "landing" / "logo.png"

W, H = 960, 540
FPS = 10
DURATION = 9
FRAME_MS = int(1000 / FPS)

BG = "#050505"
INK = "#f7f4ed"
TEXT = "#d7d0c2"
MUTED = "#8f897d"
LINE = "#343129"
PANEL = "#171714"
PANEL_TOP = "#11110f"
RED = "#ff5a49"
AMBER = "#f0c45c"
MINT = "#68d99b"
CYAN = "#71d7ff"
VIOLET = "#a98cff"


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []
    if mono:
        candidates.extend(
            [
                r"C:\Windows\Fonts\JetBrainsMono-Regular.ttf",
                r"C:\Windows\Fonts\consolaz.ttf" if bold else r"C:\Windows\Fonts\consola.ttf",
                r"C:\Windows\Fonts\CascadiaMono.ttf",
            ]
        )
    candidates.extend(
        [
            r"C:\Windows\Fonts\seguisb.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        ]
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


F_TITLE = font(38, True)
F_H2 = font(18, True)
F_BODY = font(15)
F_LABEL = font(12, True, mono=True)
F_MONO = font(14, mono=True)
F_MONO_B = font(14, True, mono=True)


def color_for_terminal(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("PS "):
        return AMBER
    if stripped == "True":
        return MINT
    if stripped == "False":
        return RED
    if "landing\\" in stripped or "agents/sage" in stripped or "agents\\sage" in stripped:
        return CYAN
    return TEXT if stripped else MUTED


def color_for_ai(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("Sage"):
        return INK
    if stripped.startswith("Ikigai") or stripped.startswith("Decision"):
        return AMBER
    if stripped.startswith("Risk"):
        return MINT
    if stripped.startswith("Matched") or stripped.startswith("Plan"):
        return CYAN
    if stripped.startswith("-") or stripped[:2] in {"1.", "2.", "3.", "4."}:
        return TEXT
    return MUTED if not stripped else INK


def visual_lines(raw: str, width: int, ai: bool) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for line in raw.splitlines():
        color = color_for_ai(line) if ai else color_for_terminal(line)
        if not line:
            lines.append(("", color))
            continue
        chunks = wrap(
            line,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
            subsequent_indent="  ",
        )
        for chunk in chunks:
            lines.append((chunk, color))
    return lines


def reveal_count(total: int, progress: float, start: float, end: float) -> int:
    if progress < start:
        return 0
    if progress >= end:
        return total
    p = (progress - start) / (end - start)
    return max(1, int(total * p))


def draw_base(progress: float) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 64):
        d.line((x, 0, x, H), fill="#0d0d0b")
    for y in range(0, H, 64):
        d.line((0, y, W, y), fill="#0d0d0b")
    for r in range(260, 20, -20):
        a = r / 260
        d.ellipse((48 - r, 8 - r, 48 + r, 8 + r), fill=(int(5 + 32 * a), int(5 + 8 * a), int(5 + 5 * a)))

    d.text((34, 24), "Sage IKEGAI", fill=INK, font=F_TITLE)
    d.text((38, 72), "EXAMPLE", fill=AMBER, font=F_LABEL)
    d.rounded_rectangle((34, 90, 926, 136), radius=10, fill="#11110f", outline=LINE)
    d.text((54, 106), 'User: create an ecommerce landing page with product hero, collection grid, and checkout CTA', fill=TEXT, font=F_BODY)
    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        logo.thumbnail((44, 44), Image.Resampling.LANCZOS)
        img.paste(logo, (872, 25), logo)
    d.rounded_rectangle((34, 508, 926, 518), radius=5, fill="#201f1b")
    d.rounded_rectangle((34, 508, 34 + int(892 * progress), 518), radius=5, fill=MINT)
    return img


def panel(d: ImageDraw.ImageDraw, xy, title: str, accent: str) -> None:
    x1, y1, x2, y2 = xy
    d.rounded_rectangle(xy, radius=12, fill=PANEL, outline=LINE)
    d.rectangle((x1, y1, x2, y1 + 30), fill=PANEL_TOP)
    d.text((x1 + 14, y1 + 9), title.upper(), fill=accent, font=F_LABEL)


def draw_lines(
    d: ImageDraw.ImageDraw,
    xy,
    title: str,
    accent: str,
    lines: list[tuple[str, str]],
    shown: int,
    max_visible: int,
) -> None:
    x1, y1, x2, _ = xy
    panel(d, xy, title, accent)
    visible = lines[:shown]
    start = max(0, len(visible) - max_visible)
    if start:
        d.text((x2 - 92, y1 + 9), f"{start} above", fill=MUTED, font=F_LABEL)
    y = y1 + 42
    for line, color in visible[start:]:
        d.text((x1 + 14, y), line, fill=color, font=F_MONO_B if line.startswith(("Sage", "Risk", "Decision", "Plan", "Matched")) else F_MONO)
        y += 14


def render() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ai = visual_lines((TRANSCRIPTS / "ai-ecommerce-real.txt").read_text(encoding="utf-8"), 88, ai=True)

    frames = []
    total = DURATION * FPS
    for idx in range(total):
        progress = idx / (total - 1)
        img = draw_base(progress)
        d = ImageDraw.Draw(img)
        ai_count = reveal_count(len(ai), progress, 0.08, 0.60)
        draw_lines(d, (34, 150, 926, 500), "ai response", MINT, ai, ai_count, 22)
        frames.append(img)

    output = OUT_DIR / "sage-ikigai-example.gif"
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"wrote {output.relative_to(ROOT)} ({DURATION}s, {total} frames)")


if __name__ == "__main__":
    render()
