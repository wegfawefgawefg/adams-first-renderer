# Adams First Renderer (AFR)

AFR is a from-scratch, educational software renderer built with my bud Adam. The goal is to learn graphics fundamentals by implementing the basic drawing primitives ourselves and then building up toward 3D.

## Run (uv)

This repo uses `uv` and targets Python 3.13 (see `.python-version`).

```bash
uv sync
uv run python -m afr
```

You can also run the installed script:

```bash
uv run afr
```

## Controls

- Quit: `Esc` or `q` (or close the window)

## What Is Here

- `src/afr/primitives.py`: points/lines/rects/circles, and a tiny "shader" style approach for per-pixel drawing
- `src/afr/draw.py`: demo / frame loop drawing code
- `src/afr/main.py`: Pygame window + render loop
