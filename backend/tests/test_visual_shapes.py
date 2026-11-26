"""Shape parsing regressions — real defects found by eye, locked down.

`painter` promised "any shape" but `tool_gen_image` only drew cube/sphere:
"yashil uchburchak" produced green squares and the agent still reported PASS.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app_adapter  # noqa: E402

import pytest  # noqa: E402


@pytest.mark.parametrize(
    "goal,shape,count",
    [
        ("512x512 o'lchamda yashil uchburchak chiz", "triangle", 1),
        ("qizil yulduz", "star", 1),
        ("3 ta ko'k doira", "circle", 3),
        ("olti burchak", "hexagon", 1),
        ("besh burchak", "pentagon", 1),
        ("beshburchak", "pentagon", 1),
        ("2 ta sariq kub", "cube", 2),
        ("qizil shar", "sphere", 1),
        ("sariq to'rtburchak", "rect", 1),
        ("yashil halqa", "torus", 1),
    ],
)
def test_shape_and_count_are_parsed(goal, shape, count):
    spec = app_adapter.parse_visual_spec(goal)
    assert shape in spec["shapes"]
    assert spec["count"] == count


def test_shape_order_follows_the_request():
    """"uchburchak va kub" -> uchburchak birinchi chizilishi kerak."""
    assert app_adapter.parse_visual_spec("uchburchak va kub")["shapes"] == [
        "triangle",
        "cube",
    ]


def test_count_words_inside_shape_names_are_not_counts():
    """"uchburchak" ichidagi "uch" son emas; "3 ta uchburchak" esa son."""
    assert app_adapter.parse_visual_spec("uchburchak")["count"] == 1
    assert app_adapter.parse_visual_spec("3 ta uchburchak")["count"] == 3


def test_blender_script_covers_every_shape():
    """Blender skriptida har bir shakl uchun tarmoq bo'lishi shart."""
    script = app_adapter.build_scene_script_from_goal("uchburchak va yulduz")
    for shape in ("triangle", "pentagon", "hexagon", "star", "circle", "rect"):
        assert f"'{shape}'" in script, f"Blender skriptida {shape} yo'q"
    compile(script, "<blender_scene>", "exec")


def test_flat_shapes_are_rotated_upright():
    """Yassi shakl gorizontal yotsa kamera faqat qirrasini ko'radi.

    `primitive_cylinder_add` o'qini Z bo'ylab quradi, shuning uchun yupqa disk
    yotib qoladi va uchburchak "quti" bo'lib ko'rinadi. Har bir yassi shakl
    90° X atrofida burilishi shart.
    """
    script = app_adapter.build_scene_script_from_goal("uchburchak")
    flat_blocks = [ln for ln in script.splitlines() if "vertices=3," in ln]
    assert flat_blocks, "uchburchak uchun silindr topilmadi"
    # Burilish shu tarmoq ichida, primitivdan keyin bo'lishi kerak.
    idx = script.index("vertices=3,")
    window = script[idx:idx + 400]
    assert "rotation_euler[0] = math.radians(90)" in window, (
        "yassi shakl tik burilmagan — kamera uni qirrasidan ko'radi"
    )


def test_gen_image_draws_requested_shape(tmp_path):
    """Haqiqiy PNG: uchburchak so'ralganda uchburchak chiziladi."""
    import tools

    out = tmp_path / "triangle.png"
    result = tools.tool_gen_image(
        "yashil uchburchak", 320, 320, output_path=str(out)
    )
    assert result["success"] is True
    assert out.is_file() and out.stat().st_size > 1000
    assert result["spec"]["shapes"] == ["triangle"]

    # Uchburchak: uchida tor, tagida keng. Shaklning vertikal joylashuvi seed
    # bilan siljiydi va pastda yozuv bor, shuning uchun qat'iy nisbat emas —
    # shaklning haqiqiy bounding box'i topiladi, so'ng uning 25% va 75%
    # balandligidagi kengliklar solishtiriladi.
    from PIL import Image

    img = Image.open(out).convert("RGB")
    w, h = img.size
    bg = img.getpixel((2, 2))

    # Pastdagi yozuv zonasini chetlab o'tamiz (label = pastki ~18%).
    shape_bottom = int(h * 0.82)
    rows: list[int] = []
    for y in range(shape_bottom):
        row = y
        width = sum(1 for x in range(w) if img.getpixel((x, row)) != bg)
        if width:
            rows.append(y)

    assert rows, "rasmda fon bo'lmagan piksellar yo'q"
    y_top, y_bottom = min(rows), max(rows)
    extent = y_bottom - y_top

    def width_at(frac: float) -> int:
        y = min(y_bottom, y_top + int(extent * frac))
        return sum(1 for x in range(w) if img.getpixel((x, y)) != bg)

    narrow, wide = width_at(0.25), width_at(0.75)
    assert wide > narrow * 1.4, (
        f"shakl pastga qarab kengaymaydi (25%da {narrow}, 75%da {wide}) — "
        "bu uchburchak emas"
    )


def test_gen_image_still_draws_sphere_and_cube(tmp_path):
    import tools

    from PIL import Image

    for goal, shape in (("qizil shar", "sphere"), ("ko'k kub", "cube")):
        out = tmp_path / f"{shape}.png"
        res = tools.tool_gen_image(goal, 200, 200, output_path=str(out))
        assert res["success"] is True, res
        assert res["spec"]["shapes"] == [shape]
        assert Image.open(out).size == (200, 200)
