from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygame

from afr.linalg.vec3 import Vec3
from afr.scene import Material, Texture


def _load_texture(path: Path):
    surf = pygame.image.load(str(path))
    if pygame.display.get_surface() is not None:
        surf = surf.convert_alpha()
    return surf


def _resolve_texture(tex_name: str, search_dirs: list[Path]) -> Path | None:
    # Keep it simple: exact filename lookup across a few dirs.
    for d in search_dirs:
        p = d / tex_name
        if p.exists():
            return p
    return None


def load_mtl(path: str | Path, *, extra_texture_dirs: list[Path] | None = None) -> dict[str, Material]:
    """Load a minimal subset of Wavefront .mtl (enough for base color textures).

    Supports:
    - newmtl
    - Kd (diffuse color)
    - map_Kd (diffuse/base color texture)
    """
    p = Path(path)
    base_dir = p.parent
    extra_texture_dirs = extra_texture_dirs or []

    # Common search dirs: mtl dir, project assets/textures
    tex_dirs = [base_dir] + extra_texture_dirs

    mats: dict[str, Material] = {}
    current: Material | None = None

    for raw in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if not parts:
            continue
        cmd = parts[0]
        args = parts[1:]

        if cmd == "newmtl" and args:
            name = " ".join(args)
            current = Material(name=name)
            mats[name] = current
            continue

        if current is None:
            continue

        if cmd == "Kd" and len(args) >= 3:
            try:
                r, g, b = float(args[0]), float(args[1]), float(args[2])
                current.base_color = Vec3(r, g, b)
            except ValueError:
                pass
        elif cmd == "map_Kd" and args:
            tex_name = args[-1]
            tex_path = _resolve_texture(tex_name, tex_dirs)
            if tex_path is not None:
                current.base_color_tex = Texture(_load_texture(tex_path))

    return mats

