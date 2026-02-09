from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3


@dataclass
class _Line:
    kind: str  # "blank" | "comment" | "vert" | "face" | "uv"
    data: Any = None
    comment: str | None = None  # without leading '#'


def _split_comment(line: str) -> tuple[str, str | None]:
    if "#" not in line:
        return line, None
    code, comment = line.split("#", 1)
    c = comment.strip()
    return code, (c if c else None)


def _fmt_num(x: float) -> str:
    # Keep files readable: ints as ints, otherwise trimmed floats.
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    return s if s else "0"


class Model:
    """Minimal model container + loader/saver for a tiny AFR format.

    Format (comments allowed anywhere using '#', preserved on save):
        verts
        x y z
        ...

        faces
        i1 i2 i3
        ...

        uvs
        u1 v1 u2 v2 u3 v3   # one line per face
        ...
    """

    def __init__(
        self,
        verts: list[Vec3] | None = None,
        faces: list[tuple[int, int, int]] | None = None,
        uvs: list[tuple[Vec2, Vec2, Vec2]] | None = None,
    ):
        self.preamble: list[_Line] = []
        self.verts_lines: list[_Line] = []
        self.faces_lines: list[_Line] = []
        self.uvs_lines: list[_Line] = []

        if verts is not None:
            self.verts = verts
        if faces is not None:
            self.faces = faces
        if uvs is not None:
            self.uvs = uvs

    @property
    def verts(self) -> list[Vec3]:
        return [ln.data for ln in self.verts_lines if ln.kind == "vert"]

    @verts.setter
    def verts(self, vs: list[Vec3]) -> None:
        self.verts_lines = [_Line("vert", v) for v in vs]

    @property
    def faces(self) -> list[tuple[int, int, int]]:
        return [ln.data for ln in self.faces_lines if ln.kind == "face"]

    @faces.setter
    def faces(self, fs: list[tuple[int, int, int]]) -> None:
        self.faces_lines = [_Line("face", f) for f in fs]

    @property
    def uvs(self) -> list[tuple[Vec2, Vec2, Vec2]]:
        return [ln.data for ln in self.uvs_lines if ln.kind == "uv"]

    @uvs.setter
    def uvs(self, us: list[tuple[Vec2, Vec2, Vec2]]) -> None:
        self.uvs_lines = [_Line("uv", u) for u in us]

    def validate(self) -> None:
        if self.uvs and len(self.uvs) != len(self.faces):
            raise ValueError(
                f"uvs count ({len(self.uvs)}) must match faces count ({len(self.faces)})"
            )

    @classmethod
    def load(cls, path: str | Path) -> "Model":
        p = Path(path)
        text = p.read_text(encoding="utf-8")
        m = cls()

        section: str | None = None

        def add_line(target: list[_Line], kind: str, data=None, comment=None):
            target.append(_Line(kind, data=data, comment=comment))

        for raw in text.splitlines():
            line = raw.rstrip("\n")
            code, comment = _split_comment(line)
            code_stripped = code.strip()

            # Preserve blank/comment-only lines.
            if code_stripped == "":
                if comment is None:
                    target = m.preamble if section is None else getattr(m, f"{section}_lines")
                    add_line(target, "blank")
                else:
                    target = m.preamble if section is None else getattr(m, f"{section}_lines")
                    add_line(target, "comment", comment=comment)
                continue

            lower = code_stripped.lower()
            if lower in ("verts", "faces", "uvs"):
                section = lower
                continue

            if section is None:
                # Non-empty preamble line: keep as comment for round-tripping.
                add_line(m.preamble, "comment", comment=(code_stripped if comment is None else f"{code_stripped} # {comment}"))
                continue

            parts = code_stripped.split()
            target = getattr(m, f"{section}_lines")
            if section == "verts":
                if len(parts) != 3:
                    raise ValueError(f"{p}: invalid vert line: {raw!r}")
                x, y, z = (float(parts[0]), float(parts[1]), float(parts[2]))
                add_line(target, "vert", Vec3(x, y, z), comment=comment)
            elif section == "faces":
                if len(parts) != 3:
                    raise ValueError(f"{p}: invalid face line: {raw!r}")
                i1, i2, i3 = (int(parts[0]), int(parts[1]), int(parts[2]))
                add_line(target, "face", (i1, i2, i3), comment=comment)
            elif section == "uvs":
                if len(parts) != 6:
                    raise ValueError(f"{p}: invalid uv line: {raw!r}")
                u1, v1, u2, v2, u3, v3 = (float(x) for x in parts)
                add_line(
                    target,
                    "uv",
                    (Vec2(u1, v1), Vec2(u2, v2), Vec2(u3, v3)),
                    comment=comment,
                )

        m.validate()
        return m

    def save(self, path: str | Path) -> None:
        self.validate()
        p = Path(path)

        def emit_line(out: list[str], line: _Line) -> None:
            if line.kind == "blank":
                out.append("")
                return
            if line.kind == "comment":
                # Store comment-only lines with '#'.
                out.append("# " + (line.comment or ""))
                return

            if line.kind == "vert":
                v: Vec3 = line.data
                s = f"{_fmt_num(v.x)} {_fmt_num(v.y)} {_fmt_num(v.z)}"
            elif line.kind == "face":
                i1, i2, i3 = line.data
                s = f"{i1} {i2} {i3}"
            elif line.kind == "uv":
                (a, b, c) = line.data
                s = (
                    f"{_fmt_num(a.x)} {_fmt_num(a.y)} "
                    f"{_fmt_num(b.x)} {_fmt_num(b.y)} "
                    f"{_fmt_num(c.x)} {_fmt_num(c.y)}"
                )
            else:
                raise ValueError(f"unknown line kind: {line.kind}")

            if line.comment:
                s += "  # " + line.comment
            out.append(s)

        out: list[str] = []
        if self.preamble:
            for ln in self.preamble:
                emit_line(out, ln)
        else:
            out.append("# afrmodel v1")

        out.append("verts")
        for ln in self.verts_lines:
            emit_line(out, ln)

        out.append("")
        out.append("faces")
        for ln in self.faces_lines:
            emit_line(out, ln)

        out.append("")
        out.append("uvs")
        for ln in self.uvs_lines:
            emit_line(out, ln)

        out.append("")
        p.write_text("\n".join(out), encoding="utf-8")

