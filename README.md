# Menanam Cahaya (Planting Light) — coolest-art-01 entry

A flat, woodblock-style night scene generated entirely in pure Python
(standard library only, no assets, no network).

## The idea

Balinese–Javanese philosophy holds **Bhuana Agung** (the macrocosm) and
**Bhuana Alit** (the microcosm) as mirrors of one another. Here a giant
full moon hangs over flooded terraced rice paddies; the terraces reflect
the moon and stars so completely that sky and earth become one surface.
Along one terrace bund, a line of tiny farmers in conical *caping* hats
practises **gotong royong** — collective work — planting glowing golden
rice seedlings into the mirrored water. They are, quite literally,
planting starlight into the earth: the cosmos tended by human hands,
one seedling at a time.

## Style

Vintage ukiyo-e woodblock formula: flat bold shapes, deep indigo +
cream + gold palette with a single red accent (the lead farmer's sash),
chunky silhouettes readable at thumbnail size, and a fine deterministic
speckle grain over the whole print.

## Running

    python3 main.py

Writes `entry.png` (1024×1024) into `$MAKEFUN_OUTPUT_DIR` (default:
current directory). Fully deterministic — every run produces a
byte-identical file. Runs in a few CPU-seconds.
