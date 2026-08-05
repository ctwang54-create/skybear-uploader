---
name: skybear-upload-images
description: |
  Internal skill called by skybear-upload-package after skybear-plan-images
  and after the Planner has approved the review page. Drives Chrome to push
  the planned images into Edit Display Detail — List Thumbnail, Image
  Carousel, Route Map and each day's Image Grid — leaving the product
  unpublished.
mcps_required:
  - Claude_in_Chrome
---

# skybear-upload-images (Step 3b automation)

> Reference: [docs/skybear-fields.md](../../docs/skybear-fields.md) §3.1/§3.2,
> [lib/selectors.yaml](../../lib/selectors.yaml) §`edit_display_detail_page`.
> This skill fills the six image slots that v1 listed as `v1: skip`.

## Preconditions — check all four, abort on any

1. `plan.json` exists and the Planner has **explicitly approved** the review
   page. Approval is a message from the Planner in this session; a plan being
   present is not approval.
2. Every `out_path` in the plan exists on disk.
3. Those files sit under a directory the Chrome tools may read. `file_upload`
   only accepts session attachments and the session's outputs/uploads
   folders — a plan materialised into a temp dir will fail here, and the fix
   is to re-run `skybear-plan-images` with a `work_dir` under outputs.
4. The target `wt_travel.id` is known and its Edit Display Detail page loads
   with the expected TourType in the readonly header. Mismatch → abort. This
   check is what stops a Guizhou gallery landing on a Xinjiang product.

## Inputs

```yaml
env: uat | prod
travel_id: 149
type_code: WBCKWE
plan_json: <work_dir>/plan.json
```

## Flow

```
1. navigate(tab, "{base_url}/#/packageDisplayMgmt/editDisplayDetail?id={travel_id}&type=edit")
2. location.reload()          # SPA hash routing — see selectors.yaml
3. wait(3s)
4. screenshot — confirm the readonly TourType header matches {type_code}.
   Mismatch → ABORT, report, change nothing.
```

### 4a. Record what is already there

Before uploading anything, read the page and note how many images each slot
already holds. Skybear slots are **additive**, and the carousel caps at 10 —
uploading 8 into a slot that already holds 6 either overflows or silently
truncates. If a slot is already populated, do not top it up: report the
existing count to the Planner and ask whether to replace or leave it. This is
an existing live product; its current gallery is someone's earlier work.

### 4b. Upload, slot by slot

For each slot, find the file input with `read_page` (never click the upload
button — that opens a native picker this session cannot see), then
`file_upload` with the `out_path`s from the plan.

| Plan slot | UI control | Column | Cap |
|---|---|---|---|
| `thumbnail` | List Thumbnail | `wt_travel.list_thumbneil` | 1 |
| `carousel` | Image Carousel | `wt_travel_image` (image_type=1) | 10 |
| `route_map` | Route Map | `wt_travel.route_map_url` | 1 |
| `section` (position = day) | that day's Image Grid | `wt_travel_section_image` | 10 |

Upload in plan order — carousel position 0 must land first, because the
product page takes the first image as its hero.

For section grids, match by the Section's own label (`Section n - DAY n`),
not by DOM order: sections are drag-reorderable, so the third block on the
page is not reliably DAY 3.

After each slot, wait for its thumbnails to render and screenshot. A slot
that shows fewer thumbnails than files sent means Skybear rejected some —
usually size. Stop and report rather than continuing.

### 4c. Leave it unpublished

Do **not** touch the *Publish for sale* checkbox. Do not tick it; if it is
already ticked on a live product, do not untick it either — that would pull a
selling product off the site. Report its state either way.

```
5. click("Save")
6. wait(3s) — expect the redirect back to Package Content Mgmt, or a toast.
7. Re-navigate to editDisplayDetail?id={travel_id}, reload, and count the
   images in each slot. Report the counts you can actually see, not the
   counts you sent.
```

## Output to parent skill

```yaml
ok: true
travel_id: 149
uploaded: { thumbnail: 1, carousel: 8, route_map: 1, sections: {1: 1, 2: 1, ...} }
verified_on_reload: { carousel: 8, sections_with_images: 9 }
pre_existing_images_found: { carousel: 0, sections: 0 }
publish_status: draft        # never changed by this skill
public_url: https://www.webuytravel.sg/tours/<travel_id>-<slug>
```

## Not yet verified against a live page

Everything above follows the Phase 0 field inventory, but the image controls
themselves have never been driven — v1 skipped all six slots, so no run has
touched them. On the first execution, before uploading, `read_page` the
Basic Display Information block and the first Section, and record in
`lib/selectors.yaml` under a new `image_upload:` key:

- the actual selector for each file input, and whether it accepts `multiple`
- whether the carousel re-orders by drag only, or exposes an index field
- what Skybear does when a slot is over its cap
- whether Save is required per slot or once at the end

Treat the first run as an inventory pass on a single product with the
Planner watching, not as a batch.
