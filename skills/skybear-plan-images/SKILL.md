---
name: skybear-plan-images
description: |
  Internal skill called by skybear-upload-package. Builds the image plan for
  one tour: pulls the brochure's own photos, works out what each one actually
  shows, sources the gaps from the web, normalises everything to the house
  standard, and renders a review page. Produces files only — nothing is
  uploaded here.
---

# skybear-plan-images (image planning)

> Library: [lib/pdf_images.py](../../lib/pdf_images.py),
> [lib/photo_source.py](../../lib/photo_source.py),
> [lib/image_norm.py](../../lib/image_norm.py),
> [lib/image_plan.py](../../lib/image_plan.py),
> [lib/image_spec.py](../../lib/image_spec.py) — the house standard, with the
> measurements behind every number.

## Inputs (from parent skill)

```yaml
type_code: WBCKWE
region: "Guizhou China"          # search hint, not a filter
pdf_path: /path/to/brochure.pdf
sections:                        # from the PDF extraction step
  - sort_num: 0
    title_en: "Singapore > Chongqing"
    location_en: "Chongqing"
    landmarks: ["Hongyadong Chongqing"]
  - ...
work_dir: /path/to/session/outputs/<type_code>
```

`work_dir` must sit under a folder the Chrome tools are allowed to read —
`file_upload` only accepts session attachments and the session's own
outputs/uploads folders. Writing to a scratch temp dir here means the upload
step later fails with a permissions error.

---

## Step 1 — Extract and grade the brochure's photos

```python
from lib.pdf_images import extract
photos = extract(pdf_path, f"{work_dir}/raw")
```

`extract()` sorts every embedded raster into four kinds:

| kind | what it is | where it goes |
|---|---|---|
| `photo` | a real photograph | carousel / day grids |
| `route_map` | the pale-blue schematic with city pins | `wt_travel.route_map_url` |
| `cover_poster` | page-1 artwork with the title baked in | **nothing** — never upload |
| `furniture` | logos, header bands, bullet glyphs | discarded |

Report `len(photos.hero_grade)`, `len(photos.usable)`, `len(photos.undersized)`
to the Planner before going further. In the three launch brochures the
usable-photo count ran 4–9, so a low number is normal, not a fault.

## Step 2 — Look at every photo and say what it is

**Do not use `caption_hint` as the answer.** It is the text nearest the image
box and it is wrong often enough to matter: in WBCURC the photo captioned
"Tongren Grand Canyon 铜仁大峡谷" — a Guizhou landmark — is the Flaming
Mountains in Turpan, because the Xinjiang deck was built from the Guizhou
deck. Three of that brochure's nine captions named the wrong place.

So: Read each file in `{work_dir}/raw/` and set, for each,

* `subject` — what is actually pictured, bilingual, e.g. `"Huangguoshu
  Waterfall 黄果树大瀑布"`. Use `caption_hint` as a prior to check, not to copy.
* `day` — the itinerary day whose landmarks match that subject, from
  `sections`. Leave `None` if nothing matches: an unassigned photo may still
  ride in the carousel (order there is editorial) but must never be dropped
  into a day's grid, because a photo under the wrong day is a factual error
  on a page a customer is buying from.

Building one labelled contact sheet per tour and reading that is far cheaper
than reading each file — the launch run used 3 sheets for 20 photos.

## Step 3 — Plan, and see what's short

```python
from lib.image_plan import DaySection, build
plan = build(type_code, region, photos, sections)
```

`plan.gaps` lists every slot the brochure could not fill and what to search
for. Two reasons show up, and they need different fixes:

* *no brochure photo identified for DAY n* — nothing in the deck covers it.
* *…but it is only 744x385 — under the 632px floor* — the deck does cover it,
  the file is just too small. Worth telling the Planner: the product team may
  have a full-resolution original of exactly the right photo.

## Step 4 — Fill the gaps from the web

```python
from lib.photo_source import search, download, available_sources
```

Check `available_sources()` first and **say what's missing**. With only
Wikimedia Commons reachable the pool is documentary, not commercial: the
launch run got mineral specimens for "Keketuohai" (a famous mineral
locality), locator maps of China for "Urumqi", a road sign for "Urho Ghost
City", and a street scene with armed police for "Urumqi Grand Bazaar". Four
of 48 candidates were usable. Do not quietly ship that — tell the Planner the
web fill is degraded and which keys would fix it
(`UNSPLASH_ACCESS_KEY`, `PEXELS_API_KEY`, `SHUTTERSTOCK_TOKEN`).

Search terms matter more than they look. Commons full-text behaves close to
AND, so every extra word can empty the result set — `"Hongyadong"` returns 6
hits, `"Chongqing Hongyadong night Guizhou China"` returns 0. Use the plain
proper noun, and prefer the name Commons files things under (`Malinghe`, not
`Maling River Grand Canyon`; `Ghost City Karamay`, not `Urho Ghost City`).

Then judge each candidate on both axes, in this order:

1. **Accuracy** — is this the named place? Reject look-alikes, satellite
   images, museum dioramas, mineral specimens, locator maps, and anything
   whose own title names a different region.
2. **Appeal** — would it sell the trip? Reject dull, grey, cluttered,
   snapshot-like frames. Reject anything showing police, military, crowds
   at a ticket gate, construction, or litter.

Record each pick with `add_web(plan, "section", day, subject=…, url=…,
local=…, credit=…, license=…)`.

## Step 5 — Compose the carousel

```python
from lib.image_plan import compose_carousel
compose_carousel(plan, ordered_src_paths)
```

The carousel is a highlights reel drawn from images the plan already holds —
it is not a separate shoot. Order it yourself, best first. Position 0 is the
hero: the product page crops it into a ~3:1 band at ~1600px, so it wants a
wide, sharp, instantly-readable frame. If the only carousel-grade options are
brochure photos, expect a `source only NNNpx wide` note — that is a flag for
the reviewer, not an error.

## Step 6 — Materialise and render the review page

```python
from lib.image_plan import materialise
from lib.preview import render
materialise(plan, f"{work_dir}/out")
plan.to_json(f"{work_dir}/plan.json")
page = render(plan, f"{work_dir}/{type_code}_preview.html", tour_name=...)
```

Send `page` to the Planner and **stop**. Nothing goes to Skybear until they
have looked at it. If they want swaps, change the picks and re-run steps 4–6;
the plan JSON means nothing already decided has to be re-decided.

## Output to parent skill

```yaml
ok: true
plan_json: <work_dir>/plan.json
preview_html: <work_dir>/<type_code>_preview.html
counts: { carousel: 8, sections: 9, thumbnail: 1, route_map: 1 }
from_pdf: 10
from_web: 4
gaps: 3
degraded_sources: ["unsplash", "pexels", "shutterstock"]   # keys absent
```
