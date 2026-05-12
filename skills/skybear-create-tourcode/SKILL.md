---
name: skybear-create-tourcode
description: |
  Internal skill called by skybear-upload-package. Drives Skybear UI to create
  a single wt_tour (tour code) given a derived plan. Step 2 of the SPEC flow.

  Always called with full pre-validated input from the parent skill. Never
  triggered directly by the user.
mcps_required:
  - Claude_in_Chrome
---

# skybear-create-tourcode (Step 2 automation)

> Reference: [docs/skybear-fields.md](../../docs/skybear-fields.md) §"Step 2",
> [lib/selectors.yaml](../../lib/selectors.yaml) §`create_package_modal` and
> §`edit_package_page`.

## Inputs (from parent skill)

```yaml
env: uat | prod
tour_type:
  id: 595
  type_code: WBMXMN
  travel_days: 7
  area_id: 337
tour_code_parts:
  mm: "12"
  type_code: WBMXMN
  suffix: "10/26MF"
tour_basic:
  tour_name: "7D6N HAKKA HOMELAND × MINNAN CULTURAL DISCOVERY — TRAVEL WITH MARCUS CHIN"
  departure_date: 2026-12-10
  return_date: 2026-12-16
  travel_days: 7
  quantity: 30
  leader_name: "Marcus Chin"
flights:
  outbound:
    date: 2026-12-10
    flight_no: MF886
    company_code: MF
    from: SIN
    to: XMN
    dep_time: "0855"
    arr_time: "1315"
    arrival_day: 0
  return:
    date: 2026-12-16
    flight_no: MF851
    company_code: MF
    from: XMN
    to: SIN
    dep_time: "0940"
    arr_time: "1400"
    arrival_day: 0
tour_fare:
  twin: 2199
  triple: 2199
  child_half_twin: 2199
  child_with_bed: 2159
  child_no_bed: 2099
  single: 2599
  infant: 0
airport_tax: 250
```

## Preconditions

- Browser at `https://test01.travel.webuy.ren` (UAT) or
  `https://travel.webuysg.com` (prod), already authenticated as Planner.
  Login flow itself is **not** automated — if the page is on `/#/login`,
  pause and ask Planner to log in manually then resume.
- claude-in-chrome MCP connected.
- Tour code uniqueness already verified by parent skill via existence_check
  (re-running this skill on an existing tour code is undefined behavior).

## Steps

### 2a. Open the Create Package modal

```
navigate(tab, "{base_url}/#/packageAirlineMaintenance/packageList")
location.reload()                       # SPA hash routing fix; Phase 0 finding #10
wait(2s)
find(tab, "Create Package button") → ref
click(ref)
wait(1s)
screenshot   // confirm modal "New Tour Code" is open
```

### 2b. Fill the modal (Phase 3 corrected method per field)

**Phase 3 finding #6 + #2**: Element UI datepicker rejects JS native value setter.
TM/TL is actually a leader-picker, not free text. Use the *exact* method per row.

| UI element | Value | How (Phase 3 verified) |
|---|---|---|
| Tour Code MM dropdown | `tour_code_parts.mm` | `click` MM input (i=0) → wait → JS click `.el-select-dropdown__item` matching "12" |
| Tour Code type input | `tour_code_parts.type_code` | `form_input` "WBMXMN" → `key` Down → `key` Return. Auto-fills Tour Type readonly + Tour Name + Region + Pax Type. |
| Tour Code suffix input | `tour_code_parts.suffix` | JS `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set` then dispatch input event (works for plain text) |
| Tour Name | (auto-filled by autocomplete) | leave or override |
| **Departure Date** | `DD/MM/YYYY` | **Must use `computer.type`** — JS setter does NOT trigger v-model. Steps: JS focus input → `computer.type "10/12/2026"` → `key Tab` |
| Travel Days | (auto from type, default 7) | leave |
| **Return Date** | `DD/MM/YYYY` | same as Departure Date — keyboard only |
| Pax Type | (readonly, auto from type = "G-Group Tr") | abort if not "G-Group Tr" |
| Quantity | `tour_basic.quantity` | JS setter works, OR triple_click + type |
| Paym Due Days | leave default `21` | skip |
| **TM/TL** | (skip in v1) | **Phase 3 finding #2**: leader-picker UI; click + type / JS setter all fail. v1 leaves NULL; Planner fills manually post-create. |

Sanity-check the auto-filled Pax Type field shows `G-Group Tr`. If anything
else (FIT, MICE, ALTITUDE), abort with "v1 only supports G-Group".

### 2c. Save modal → find new tour_id via UI search (no Python deps required)

**Correction (Phase 3 finding #1 + #5)**: Modal Save does **NOT** redirect.
The page stays on `packageList`. Also, a confirmation dialog appears.

```
click("Save")
wait(2s)
# Confirmation dialog appears: "Tour code cannot be changed after saving. Confirm save?"
click(".el-message-box button.el-button--primary"  // text "Confirm")
wait(4s)
# Modal closes; URL is still on packageList. Backend has inserted the new wt_tour.

# Find the new tour_id via the Package List search UI
# (works for any colleague — no RO MySQL credentials needed)
1. Focus the "Tour Code" search textbox at the top of Package List
2. Use real keyboard `computer.type(tour_code.full)` — e.g. "12WBMXMN10/26MF"
3. Press Escape if an autocomplete dropdown appears
4. Click the "Search" button
5. Wait 2s for the list to refresh
6. The first row in the list should match the new tour_code; capture its
   "Modify" link href — the URL pattern is:
     /#/packageAirlineMaintenance/editPackage?id=<NNN>&type=edit
   Extract NNN as new_tour_id.

navigate(tab, f"{base_url}/#/packageAirlineMaintenance/editPackage?id={new_tour_id}&type=edit")
location.reload()
wait(3s)
```

**Optional dev shortcut** (skip if `.env` not configured):
If the developer has `SKYBEAR_RO_MYSQL_*` env vars set, they can use
`lib.existence_check` to query the slave DB directly. Colleagues using the
plugin via Cowork should NOT need to configure this — the UI-search path
above is the supported runtime flow.

If validation errors appeared instead (red text under fields, dialog stays open):
- Common cause: dates set via JS setter only show in DOM but v-model is empty.
  Fix: re-fill date fields via `computer.type` keyboard input then Tab.

### 2c2. Edit Package — Main Airline (Phase 3 finding #8, NEW)

Phase 0 missed this field. It sets `wt_tour.airline_code`. Without it, the
DB stores empty string.

```
find input next to label "Main Airline"
JS focus → computer.type tour_code_parts.airline (e.g. "MF")
key Tab
```

If Main Airline is an autocomplete/select widget (not yet verified for all
airlines), use Down + Return like the Tour Type input.

### 2d. Edit Package page — flight itinerary

For each of `flights.outbound` and `flights.return`:

```
find "Flight Itinerary" section header
click "Add New" if no empty row exists yet
fill row fields:
  Date: DD/MM/YYYY
  Flight No: MF886 / MF851
  From: SIN / XMN  (uppercase 3-letter IATA)
  To:   XMN / SIN
  Departure Time: HHMM (4-digit, no colon)
  Arriving Time:  HHMM
  Arrival Day:    0 (default; +1 only if PDF/Planner says overnight)
  Seat Code:      G   (default per Phase 0 finding #8)
  Flights Status: RQ  (default)
```

### 2e. Edit Package — Tour Fare (price_type=1)

Fill the 7 sellPrice cells (cost cells leave 0):

| Column | Value |
|---|---|
| SGLfare.sellPrice | `tour_fare.single` |
| TWNfare.sellPrice | `tour_fare.twin` |
| TRPFare.sellPrice | `tour_fare.triple` |
| ChdHfTwn.sellPrice | `tour_fare.child_half_twin` |
| ChdWEbed.sellPrice | `tour_fare.child_with_bed` |
| ChdWOBed.sellPrice | `tour_fare.child_no_bed` |
| InfFare.sellPrice | `tour_fare.infant` |

Skip [Set Tiered Price] button (v1 doesn't use early-bird pricing).

### 2f. Edit Package — Land Tour, Additional Charges, Waiver, Additional Discount

```
Land Tour (price_type=2): all 0 (skip; pre-filled 0)
Additional Charges:
  AirportTaxes/FuelSurcharge.sellPrice = airport_tax
Waiver Of Charges (price_type=4): all 0
Additional Discount: skip (no Add Custom Charge)
```

### 2g. Edit Package — Estimated Cost (9 required fields, Phase 0 finding #3)

Fill all 9 with `lib.pricing.ESTIMATED_COST_DEFAULTS`:
- Air Ticket = 0
- Airport Taxes = 0
- Land Tour Cost = 0
- Tour Leader Cost = 0
- Celebrity Cost = 0
- Referral Cost = 0
- Sales Commission = 30 (default; explicitly set to be safe)
- Back Office Commission = 0
- Celebrity Commission = 0

### 2h. Submit

```
click("Submit")
wait(3s)
screenshot    // confirm redirect back to Package List
read_page     // verify new row with our tour_code is present
```

If Submit fails:
- Take a screenshot, return error to parent skill with the raw validation message.
- Do **not** retry automatically — Planner needs to see what Skybear changed.

## Output to parent skill

```yaml
ok: true
tour_id: NNNN          # extracted from URL after modal Save
tour_code: 12WBMXMN10/26MF
tr_status: Pending      # i.e. wt_tour.tr_status = 0 (draft)
edit_url: https://test01.travel.webuy.ren/#/packageAirlineMaintenance/editPackage?id=NNNN&type=edit
```

## Cleanup on failure

Do not auto-delete partial records. Skybear has no obvious "delete tour"
button in this UI; deletion via DB is out of scope. Report the partial state
to the Planner so they can decide whether to manually fix or leave the
half-baked draft.
