---
name: skybear-upload-package
description: |
  Upload a Skybear travel package (G-Group) from a PDF brochure to Skybear admin
  (test01.travel.webuy.ren or travel.webuysg.com). Final state is always **draft** —
  the human Planner reviews and clicks Publish themselves.

  **Trigger when**: a Planner / OP drops a PDF (named like "WBxxx*.pdf" or
  containing a Skybear-style tour code) into a Cowork chat AND mentions
  "上传到 skybear", "上架配套", "create tour code", or similar intent.

  **Do NOT trigger** for: pricing-only updates (use skybear-update-pricing
  instead, v2), generic PDF reading, or non-G-Group products (FIT/MICE etc.,
  only pax_type=1 supported in v1).
trigger_keywords:
  - skybear
  - 上架
  - 上传配套
  - create tour code
  - new tour code
inputs:
  - type: pdf_attachment
    required: true
  - type: chat_dialogue
    fields:
      - departure_date
      - airline_code
      - outbound_flight  # e.g. "MF886 SIN-XMN 0855-1315"
      - return_flight    # e.g. "MF851 XMN-SIN 0940-1400"
      - leader_name
      - inventory
      - twin_price
      - airport_tax
mcps_required:
  - Claude_in_Chrome
---

# skybear-upload-package

> v1 scope: G-Group (`pax_type=1`), single Tour Code per run, always-draft.
> See parent [SPEC.md](../../../SPEC.md) and [docs/skybear-fields.md](../../docs/skybear-fields.md).

## When to invoke

Planner drops a Skybear-style PDF (e.g. `WBMXMN.pdf`) into a Cowork chat and asks
to "把这个配套上架到 skybear" / "create new tour code" / "上传配套到官网".

## Out of scope (v1)

- F-FIT (`pax_type=2`) → routes to `wt_fit_*`, not implemented.
- Multi tour-code ranges (CSV-driven) → run once per departure.
- Auto-publish → never. Always end at draft.
- Image carousel / cover video / route map upload → skipped in v1.
- PDF storage → PDF is consumed in-session, never persisted (Skybear
  `wt_tour_type_file` and `wt_tt_package.pdf_file_url` are deprecated since
  2024-12).

## Flow

```
0. ENV CHOICE (default: prod)
   Ask the Planner ONCE per session via AskUserQuestion:
     "Upload to which environment?"
       a) Production — https://travel.webuysg.com  (推荐)
       b) UAT test  — https://test01.travel.webuy.ren
   Store the chosen base_url for the rest of the session.
   If Planner says "prod" / "生产" / "正式" / nothing → use Production.
   If "uat" / "test" / "测试" → use UAT.

   IMPORTANT: All subsequent UI navigation, Chrome tabs, and verify steps
   MUST use the chosen base_url. Skill files reference URLs symbolically as
   {base_url}; substitute the chosen one.

1. INTAKE
   1a. Receive PDF attachment
   1b. If PDF > 20MB: rasterize each page to PNG (1600px wide) using
       PyMuPDF (see scripts/pdf_to_png.py). Read pages individually.
   1c. Run extraction prompt (lib/pdf_extract_prompt.md) → structured YAML

2. EXTRACT (Claude multimodal)
   - tour_type.{type_code, type_name_en, type_name_cn, travel_days}
   - travel.{product_name_en, product_name_cn, highlights[], sections[]}
   - travel.{cities_cn[], meal_plan_summary, accommodation_level,
              important_note_en, important_note_cn}
   - departure_date_hint (if visible on PDF cover)

3. ASK PLANNER (chat) — fields PDF doesn't have
   Required:
     - departure_date (date)
     - airline_code (e.g. MF)
     - outbound_flight: flight_no, dep_time HHMM, arr_time HHMM, dep_apt, arr_apt
     - return_flight:   same shape
     - leader_name (free text → wt_tour.tl_tm_name)
     - inventory (int)
     - twin_price (decimal)
     - airport_tax (decimal)
   Optional (defaults applied if omitted, see lib/pricing.py):
     - single_supplement (default 400)
     - child_with_bed_diff (default -40)
     - child_no_bed_diff (default -100)
     - infant_price (default 0)
     - return_date (auto-derived = departure + travel_days - 1; ask Planner to confirm)

4. DERIVE
   from lib.tour_code import derive_tour_code
   from lib.pricing import derive_tour_fare

   tour_code = derive_tour_code(departure_date, type_code, airline_code)
   # e.g. (2026-12-10, "WBMXMN", "MF") → "12WBMXMN10/26MF"

   fare = derive_tour_fare(twin_price)
   # twin_price=2199 → TWN/TRP/ChdHfTwn=2199, ChdWEbed=2159,
   #                   ChdWOBed=2099, SGLfare=2599

5. EXISTENCE CHECK (read-only MySQL slave)
   from lib.existence_check import check
   from lib.config import load_settings

   report = check(load_settings(), type_code, tour_code.full)
   - If report.tour_type is None and pax_type != 1 → ABORT ("v1 仅支持 G-Group")
   - If report.tour is not None → ABORT ("Tour code already exists; this skill
     creates new ones only. Use skybear-update-pricing v2 for edits.")
   - If report.travel is not None → mark Step 3 as "REUSE travel id=N"
   - If report.travel is None → mark Step 3 as "CREATE NEW wt_travel"

6. REVIEW SUMMARY (chat)
   Print a clean review block to the Planner:
     ┌─────────────────────────────────────────────────────────┐
     │ Tour Type:  WBMXMN id=595 (REUSE)                       │
     │ Tour Code:  12WBMXMN10/26MF (NEW)                       │
     │ wt_travel:  id=149 (REUSE; Section 1-7 already filled)  │
     │ Departure:  2026-12-10  Return: 2026-12-16              │
     │ Airline:    MF (out: MF886 0855-1315; ret: MF851)       │
     │ Leader:     Marcus Chin                                 │
     │ Inventory:  30                                          │
     │ Prices (SGD):                                           │
     │   Twin: 2199  Single: 2599  ChdW/Bed: 2159  ChdW/o: 2099│
     │   Triple: 2199  ChdHfTwn: 2199  Infant: 0               │
     │   Airport Tax: 250                                      │
     │ Status will be: DRAFT (you must Publish manually)       │
     └─────────────────────────────────────────────────────────┘
   Wait for Planner to type "OK / 继续 / proceed".

7. DRIVE UI
   Delegate to skybear-create-tourcode skill (Step 2).
   Then delegate to skybear-update-display skill (Step 3).

8. VERIFY
   Delegate to skybear-verify skill.
   Final report: tour_id, draft URL, public-site visibility.
```

## Stop conditions (any of these = halt and inform Planner)

- Existing wt_tour_type pax_type ≠ 1.
- Tour code already exists in wt_tour (we don't overwrite).
- PDF unreadable (after retry with rasterization).
- Planner says "stop" / "取消" / "wait" anywhere in the dialogue.
- Skybear browser session not authenticated (login redirect detected).
- Submit button click returns validation errors that we don't auto-fix
  (e.g. unexpected required field added by Skybear updates).

## Success criteria (v1 acceptance, per SPEC §11)

1. End-to-end run on UAT with WBMXMN sample PDF.
2. Planner sees correct extraction within 60s of dropping PDF.
3. After ≤7 chat answers, Planner sees correct review block.
4. After Planner approval, plugin completes Skybear UI flow in <3 min.
5. Final report shows tour_id, draft URL, webuytravel.sg search result.
6. Re-running with same inputs is idempotent (no duplicate tour code).
7. No tour ever gets `Publish for sale` ticked by the plugin.

## Handover to other skills

| Sub-task | Skill |
|---|---|
| Browser Step 2 (Modal + Edit Page) | `skybear-create-tourcode` |
| Browser Step 3 (Edit Display Detail + wt_travel_tour binding) | `skybear-update-display` |
| Public-site verification | `skybear-verify` |
