---
name: skybear-update-display
description: |
  Internal skill called by skybear-upload-package. Step 3 of the SPEC flow:
  ensure the new wt_tour shows up under the right wt_travel for public-site
  display. Either creates a fresh wt_travel from PDF content (if none exists)
  or just binds the new tour to an existing one.
mcps_required:
  - Claude_in_Chrome
---

# skybear-update-display (Step 3 automation)

> Reference: [docs/skybear-fields.md](../../docs/skybear-fields.md) §"Step 3 — Edit Display Detail",
> [lib/selectors.yaml](../../lib/selectors.yaml) §`edit_display_detail_page`.

## Inputs (from parent skill)

```yaml
env: uat | prod
tour_type:
  id: 595
  type_code: WBMXMN
mode: REUSE | NEW       # from existence_check.report.travel
travel:                 # only present if mode == REUSE
  id: 149
new_tour:
  id: NNNN              # from skybear-create-tourcode output
  tour_code: 12WBMXMN10/26MF
extracted_content:      # only used if mode == NEW
  product_name_en: ...
  product_name_cn: ...
  highlights: [...]
  sections: [...]
  important_note_en: ...
  important_note_cn: ...
  meal_plan_summary: ...
  accommodation_level: ...
```

## Two modes

### MODE: REUSE (an existing wt_travel exists for this TourType)

Most common case (e.g. WBMXMN UAT today: id=149 already has Section 1-7 +
Highlight + List Thumbnail).

```
1. navigate(tab, "{base_url}/#/packageDisplayMgmt/editDisplayDetail?id={travel.id}&type=edit")
2. location.reload()           # SPA hash workaround
3. wait(3s)
4. screenshot — verify the page shows the right TourType (top readonly field)

5. Bind new tour to this wt_travel (Phase 3 finding #3, RESOLVED):
   The "Dep Date & Price" section auto-lists ALL wt_tour rows under this
   TourType as orange cards. Each card has a checkbox in its top-right
   corner. Click the card whose tour_code matches `new_tour.tour_code`.

   ```
   scroll to "Dep Date & Price" section
   find: orange card containing text "{new_tour.tour_code}" (e.g. "12WBMXMN10/26MF")
   click the checkbox at that card's top-right (≈ +35,-15 from card top-right)
   wait 1s — the table below should populate with one row showing:
     Dep Date | Flight Info (e.g. "MF / CX") | Tour Fare | Selling Price | Cost | Tax | Qty
   ```

   Verify checkbox is now ticked (filled blue ✓). Other tour cards under
   this TourType already-bound stay ticked; do NOT untick them.

6. Verify "Publish for sale" checkbox is **NOT** ticked (Phase 0 finding #6).
   If it's already ticked from previous edit, leave it alone — never tick
   on behalf of Planner. Don't untick a previously-ticked product either,
   that's destructive.

7. click("Save")
8. wait(3s)
9. Verify success: should redirect back to Package Content Mgmt list, or
   show a toast.

10. (Verification) Re-navigate to editDisplayDetail?id={travel.id} and
    inspect "Dep Date & Price" — confirm new_tour.tour_code now appears.
```

### MODE: NEW (no wt_travel exists for this TourType yet)

Less common. Triggered when existence_check returns travel == None.

```
1. navigate(tab, "{base_url}/#/packageDisplayMgmt/packageContentMgmt")
2. click("Creat/Publish")  # NB: Skybear UI typo, not "Create"
3. Fill Basic Display Information:
   - Tour Type dropdown: select extracted.tour_type.type_code
   - Product Name (双语并排): product_name_en | product_name_cn
   - Highlight (动态多行): for each h in extracted_content.highlights:
       click "+ Add" → fill h.en | h.cn
   - List Thumbnail / Image Carousel / Route Map: LEAVE EMPTY here.
     `skybear-upload-images` fills them after the Planner approves the
     review page — text first, images second, so a rejected gallery never
     blocks the itinerary content from landing.
   - Cover Video Asset / Cover Video: SKIP (still no source for video)
4. Sections: for each s in extracted_content.sections (sort_num 0..N-1):
   click "+ Add Section"
   - Section Name (双语): "DAY {sort_num+1}" | "第{cn_num}天"
   - Section Title (双语): s.title_en | s.title_cn
   - Section Location (双语): s.location_en | s.location_cn
   - Section Description (双语): s.description_en | s.description_cn
   - Image grid: LEAVE EMPTY (filled by `skybear-upload-images`)
   - Trip Item: SKIP (Phase 0 unresolved structure)
5. Dep Date & Price: should auto-populate after Save (see MODE REUSE step 5).
6. Product Status / Publish for sale: **DO NOT TICK**.
7. click("Save")
```

## Defensive checks

- Verify **TourType binding**: page top should show `<type_code> | <type_name>`.
  Mismatch → abort.
- Verify **Pax Type**: must be G-Group on the underlying TourType. If admin
  somehow opens this page on a FIT product, abort.
- Verify **delete_status = 0** implied by being editable (deleted records
  redirect to list).

## Output to parent skill

```yaml
ok: true
travel_id: 149
mode: REUSE
sections_written: 0       # 0 in REUSE mode; N in NEW mode
tour_bound: true          # whether Dep Date & Price populated post-Save
publish_status: draft     # always
```

## Phase 3 verified (2026-05-08, against UAT WBMXMN)

1. **wt_travel_tour binding** — RESOLVED: orange-card checkbox in "Dep Date & Price" (see step 5 above). After Save, `wt_travel_tour` row inserts (verified id=27935 for tour_id=11571 → travel_id=149).
2. **Trip Item internals** — RESOLVED: per-Section sub-records with Trip Type (dropdown e.g. "Attractions") + Trip Title (双语) + Trip Description (双语) + Trip Photos. Underlying DB table not yet identified (likely a child of `wt_travel_section`). v1 still doesn't create Trip Items.
3. **sort_num convention** — STILL UNVERIFIED in NEW mode (Phase 3 reused existing wt_travel id=149). Next NEW-mode run should observe.

## Phase 3 evidence

```
travel_id: 149 (REUSE)
new wt_travel_tour: id=27935 (travel_id=149, tour_type_id=595, tour_id=11571)
publish_status: 0 (Publish for sale unticked) ✓
```
