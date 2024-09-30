"""Generate a random github style svg avatar."""

import html
import random as rd
from math import ceil


def as_hex(num: int) -> str:
    """Convert an int to a 2 digit hex string."""
    s = hex(num).lstrip("0x").rstrip("L")
    return f"{s:02}"


def hex_color(r: float, g: float, b: float) -> str:
    """Convert 3 floats in range (0, 1) to a hex color."""
    return f"#{as_hex(int(255 * r))}{as_hex(int(255 * g))}{as_hex(int(255 * b))}"


def gen_color_pair(dist: float = 0.7) -> tuple[str, str]:
    """Generate a pair of colors with a minimum distance between them."""
    v1 = (0.0, 0.0, 0.0)
    v2 = v1
    d = 0
    while d < dist:
        v1 = (rd.random(), rd.random(), rd.random())  # noqa: S311
        v2 = (rd.random(), rd.random(), rd.random())  # noqa: S311
        d = sum((x - y) ** 2 for x, y in zip(v1, v2, strict=True)) ** (1 / 2)
    return hex_color(*v1), hex_color(*v2)


def rect(x: int, y: int, color: str) -> str:
    """Generate a rect."""
    return (
        f"""<rect x="{10*x}" y="{10*y}" width="10" height="10" fill="{color}" stroke="{color}" />"""
    )


def generate_avatar(title: str | None = None, height: int = 7, width: int = 7) -> str:
    """Generate a random github style svg avatar."""
    fg_color, bg_color = gen_color_pair()
    fill_ratio = rd.uniform(0.3, 0.8)  # noqa: S311
    half_width = ceil(width / 2)
    k = round(fill_ratio * height * half_width)
    values = rd.sample([(x, y) for x in range(half_width) for y in range(height)], k=k)

    inner = ""
    if title is not None:
        inner += f"""<title>{html.escape(title)}</title>"""
    inner += f"""<rect width="100%" height="100%" fill="{bg_color}" />"""

    mid = width // 2 if width % 2 == 1 else None
    for x, y in values:
        inner += rect(x, y, fg_color)
        if x == mid:
            continue
        inner += rect(width - x - 1, y, fg_color)
    return (
        f"""<svg width="{10*width}" height="{10*height}" xmlns="http://www.w3.org/2000/svg">"""
        f"{inner}"
        """</svg>"""
    )
