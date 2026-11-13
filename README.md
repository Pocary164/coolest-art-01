# Leviathan Bloom

A colossal luminous jellyfish rising over a night ocean — drawn entirely by
code. There are no image assets in this repository: `main.py` is a small
software rasterizer (Python 3.13, standard library only) that paints every
pixel at run time and writes the result to `$MAKEFUN_OUTPUT_DIR/entry.png`.

## How it is made

- **Scene**: gradient indigo sky and dark teal sea, a seeded starfield with
  one shooting star, and a giant jellyfish as the single focal point — a
  scalloped bell with a cyan-to-violet gradient, a magenta inner dome, and
  the four amber lobes of its gonad ring glowing through the bell.
- **Tentacles**: ten main ribbons (layered translucent passes over a bright
  core) plus fine thread tentacles and frilled oral arms, all following
  seeded sine paths; their light pools and shimmers on the water below.
- **Technique**: scanline polygon fills, soft ellipses, polyline strokes,
  and additive light accumulated in a half-resolution glow buffer, finished
  with a vignette pass. The PNG is encoded with `zlib`/`struct` from the
  standard library.
- **Deterministic**: a fixed-seed PRNG and no clock or network access — two
  runs produce byte-identical output (1024×1024, ~0.6 MB, runs in seconds).

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png
```

License: MIT (see `LICENSE`).
