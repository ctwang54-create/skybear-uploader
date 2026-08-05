# skybear-uploader

Cowork plugin that lets a Webuy Planner upload one Skybear travel package per
session — PDF in, **draft** Skybear records out. The human Planner reviews and
clicks **Publish for sale** themselves.

> Single Cowork session = 1 PDF + ~7 chat answers = 1 new wt_tour code under
> the matching wt_travel, all in draft state.

---

## Status

- **v0.3.0** — automatic images. PDF in → itinerary content **and** a full
  gallery out, still all draft. See [Images](#images) below.
- **v0.1.0** — Phase 1 (lib + 13/13 tests passing) + Phase 2 (4 skill manifests)
  + Phase 3 (live UAT dry-run verified end-to-end).
- See parent [SPEC.md](../SPEC.md) for full design.
- See [docs/skybear-fields.md](docs/skybear-fields.md) for field inventory.
- Phase 3 evidence: `wt_tour id=11571` (`12WBMXMN10/26MF`) created and bound
  to `wt_travel id=149` via `wt_travel_tour id=27935` on 2026-05-08, all in
  draft state.

## Layout

```
skybear-uploader/
├── plugin.json                              # cowork plugin manifest
├── .env.example / .env                      # SKYBEAR_RO_MYSQL_* + URLs
├── requirements.txt                         # pymysql, dotenv, pytest
│
├── lib/
│   ├── tour_code.py        # derive_tour_code(date, type_code, airline)
│   ├── pricing.py          # default Tour Fare formula + Estimated Cost defaults
│   ├── config.py / db.py   # RO MySQL connection (Skybear slave)
│   ├── existence_check.py  # 3 SELECT queries → ExistenceReport
│   ├── pdf_extract_prompt.md   # multimodal extraction template
│   ├── selectors.yaml      # Skybear UI selector + per-finding mapping
│   │
│   ├── image_spec.py       # the house standard, and why each number is that
│   ├── pdf_images.py       # extract + classify the brochure's own photos
│   ├── photo_source.py     # web fallback, mirroring webuy-itinerary-creation
│   ├── image_norm.py       # detail-aware 4:3 crop → 1440×1080 JPEG
│   ├── image_plan.py       # slot assignment, gap tracking, materialise
│   └── preview.py          # self-contained review page
│
├── skills/
│   ├── skybear-upload-package/SKILL.md      # parent (intake + chat + delegation)
│   ├── skybear-create-tourcode/SKILL.md     # Step 2 (Modal → Edit Page → Submit)
│   ├── skybear-update-display/SKILL.md      # Step 3 (Dep Date & Price binding)
│   ├── skybear-plan-images/SKILL.md         # Step 3a (pick + normalise + review)
│   ├── skybear-upload-images/SKILL.md       # Step 3b (fill the six image slots)
│   ├── skybear-verify/SKILL.md              # Step 4 (admin URLs + public-site)
│   └── skybear-publish-gate/SKILL.md        # draft → published, by a human
│
├── tests/                  # 28 tests, all passing
│   ├── test_tour_code.py        # 4 unit tests (incl. UAT-verified samples)
│   ├── test_pricing.py          # 4 unit tests (formula + 9-cost defaults)
│   └── test_existence_check.py  # 5 integration tests (live UAT MySQL)
│
├── docs/
│   └── skybear-fields.md   # Phase 0 field inventory + URL patterns
│
└── examples/
    └── WBMXMN_walkthrough.md   # sample Cowork session transcript
```

## Quick start (dev)

```bash
cd skybear-uploader
cp .env.example .env
# fill in SKYBEAR_RO_MYSQL_PASSWORD
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest tests/      # 13 passed
```

## Plug-in to Cowork

To package this directory into a `.plugin` file, run the
`cowork-plugin-management:create-cowork-plugin` skill from a Cowork session.
The skill will produce a single `.plugin` artifact for distribution.

In a regular Cowork session, just say *"上传这个 PDF 到 Skybear"* (with a PDF
attached) and the **`skybear-upload-package`** skill triggers automatically.

## Images

A brochure carries its own photos, and those beat any stock lookup on intent
— they are what the product team chose. So the pipeline is PDF-first, with
the web filling only what the deck can't cover.

**What comes out of a brochure.** `pdf_images.extract()` sorts every embedded
raster into `photo`, `route_map`, `cover_poster` or `furniture`. That
classification is not cosmetic: page 1 of every deck is a rasterised poster
with the tour title baked in, and every deck carries a pale-blue schematic
route map. Both look like photographs to any colour statistic, and both would
be obviously wrong in a carousel. The route map is genuinely useful, though —
it goes straight into `wt_travel.route_map_url`, a slot v1 left empty.

**Captions are not evidence.** `caption_hint` is the text nearest the image
box, and it is wrong often enough to matter. In WBCURC the photo captioned
"Tongren Grand Canyon 铜仁大峡谷" — a Guizhou landmark — is the Flaming
Mountains in Turpan, because that deck was built from the Guizhou deck. Three
of its nine captions named the wrong place. Subjects are decided by an agent
looking at the photo, with the caption as a prior at most.

**The house standard is measured, not assumed.** The Skybear admin UI
suggests "1920×1080 (16:9)" for the carousel and nothing shipped follows it;
sampling the OSS originals behind a live product gave 1080-class images at
3:4, 4:3 and 9:16 mixed together. Everything now normalises to **4:3 at
1440×1080** — the largest live tier, and the ratio that survives the wide
hero crop. `lib/image_spec.py` carries the measurements behind every
threshold, including why the upscale ceiling is 2.0 and not 1.65.

**The web fallback needs keys to be any good.** It mirrors the rules in the
sibling `webuy-itinerary-creation` repo — Shutterstock → Unsplash → Pexels →
Wikimedia Commons, GPS-gated, judged on accuracy before beauty. With no keys
set only Commons is reachable, and Commons is an archive rather than a photo
library: a launch-sample run got mineral specimens for "Keketuohai", locator
maps of China for "Urumqi", and a road sign for "Urho Ghost City". 4 of 48
candidates were usable. Set `UNSPLASH_ACCESS_KEY` / `PEXELS_API_KEY` /
`SHUTTERSTOCK_TOKEN` before relying on it.

**Nothing uploads unreviewed.** `preview.py` renders a self-contained page
showing every image with its provenance, upscale factor and the hero's actual
wide crop. The Planner approves that page before `skybear-upload-images`
runs, and separately ticks *Publish for sale* before anything is public.

## Known limitations

| Limitation | Workaround |
|---|---|
| `wt_tour.tl_tm_name` left NULL | Planner fills TM/TL in Skybear after Submit (leader-picker UI is custom; Phase 4 may automate) |
| `wt_tour.airline_code` left "" | Planner fills "Main Airline" field on Edit Package after Submit |
| Cover Video Asset / Cover Video still not filled | No video source exists; the portrait 9:16 still is specced in `image_spec.COVER_PORTRAIT` but unused |
| Image upload selectors unverified against a live page | v1 skipped all six slots, so no run has driven them. First run is an inventory pass — see `skybear-upload-images` §"Not yet verified" |
| Trip Items inside Sections not auto-created | description field includes attractions inline |
| `pax_type ≠ 1` (G-Group) not supported | Aborted with error; FIT/MICE/etc. → v2 |
| `webuytravel.sg` is production; UAT changes don't show there | Verify step reports "not visible (expected for draft)" |

## Phase 3 test data on UAT (cleanup notes)

Phase 3 left one draft tour on UAT (no bookings, never published, harmless).

| Object | ID | State |
|---|---|---|
| `wt_tour` | 11571 | tour_code `12WBMXMN10/26MF`, tr_status=0 (Pending), sales_num=0, deleted_status=0 |
| `wt_tour_price` rows | 18 | all under tour_id=11571 |
| `wt_tour_flight_itinerary` rows | 2 | MF886 SIN→XMN + MF851 XMN→SIN |
| `wt_travel_tour` | 27935 | binding 11571 ↔ travel_id=149 |

**Cleanup options** (none urgent — data is draft and isolated):

1. **Leave it** as a permanent Phase 3 evidence record. Future runs must use
   a different tour_code (e.g. test with `12WBMXMN10/26SQ`).
2. **Soft-delete via UI**: open Package List → search `12WBMXMN10/26MF` →
   Modify → set Tr Status to *Canceled* → Submit. Tour stays in DB but won't
   accept bookings. (UI may also show a `Delete` link under Action — not yet
   verified for this row.)
3. **Hard-delete via DB**: requires RW MySQL credentials (Phase 3 only had RO).
   Run via DBA:
   ```sql
   DELETE FROM wt_tour_price WHERE tour_id = 11571;
   DELETE FROM wt_tour_flight_itinerary WHERE tour_id = 11571;
   DELETE FROM wt_travel_tour WHERE id = 27935;
   UPDATE wt_tour SET deleted_status = 1 WHERE id = 11571;
   -- (Skybear convention: soft-delete via deleted_status flag, not row delete)
   ```

## Roadmap (v2+)

- **Main Airline + leader-picker** automation (close last 2 NULL gaps)
- **F-FIT** support (`pax_type=2`, `wt_fit_*` table family)
- **NEW-mode wt_travel creation** with image upload, sections from PDF,
  Trip Items, sort_num convention verified
- **CSV-driven multi-departure series** (one PDF → N tour codes in one run)
