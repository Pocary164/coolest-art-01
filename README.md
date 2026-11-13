# Leviathan Bloom (v3)

A colossal luminous jellyfish rising over a night ocean — drawn entirely by
code. There are no image assets in this repository: `main.py` is a small
software rasterizer (Python 3.13, standard library only) that paints every
pixel at run time and writes the result to `$MAKEFUN_OUTPUT_DIR/entry.png`.

## How it is made

- **Scene**: a deeper indigo sky and dark teal sea, a seeded starfield with
  cross-sparkle stars, one shooting star and a pale moon with a halo — and
  a giant jellyfish as the single focal point, its bell grown larger than
  the first version so the subject fills the frame.
- **The bell**: a scalloped dome with a cyan-to-violet gradient, volumetric
  flank shading, a magenta inner dome, and fifteen radial canals veining
  from the heart of the bell to its margin. The four amber lobes of the
  gonad ring are painted in three gradient layers each, so they glow with
  real depth through the bell, and the rim is finished with a three-pass
  rim light (wide halo, mid band, hot core) plus a glowing margin line.
- **Tentacles**: eleven main ribbons (layered translucent passes over a
  bright core), thirty-six fine thread tentacles, and six frilled oral
  arms with a warm highlight pass — all following seeded sine paths.
- **Water**: their light pools on the surface in a soft reflection, a
  vertical shimmer column of light strokes under the bell, hundreds of
  horizontal glints and bioluminescent plankton sparkles.
- **Technique**: scanline polygon fills, soft ellipses, polyline strokes,
  and additive light accumulated in a half-resolution glow buffer, finished
  with a vignette pass. The PNG is encoded with `zlib`/`struct` from the
  standard library.
- **Deterministic**: a fixed-seed PRNG and no clock or network access — two
  runs produce byte-identical output (1024×1024, ~0.72 MB, a few CPU-seconds).

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png
```

License: MIT (see `LICENSE`).
