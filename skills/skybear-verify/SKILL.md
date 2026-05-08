---
name: skybear-verify
description: |
  Internal skill called by skybear-upload-package after Step 2+3. Confirms the
  draft tour is reachable in Skybear admin and reports public-site visibility
  on webuytravel.sg.
mcps_required:
  - Claude_in_Chrome
---

# skybear-verify (Step 4)

## Inputs

```yaml
env: uat | prod
tour_type:
  type_code: WBMXMN
  type_name_cn: "7天6晚穿越客家原乡 × 闽南文化深度之旅"
new_tour:
  id: NNNN
  tour_code: 12WBMXMN10/26MF
travel:
  id: 149
```

## Steps

### 4a. Skybear admin draft URL

```
admin_url = "{base_url}/#/packageAirlineMaintenance/editPackage?id={new_tour.id}&type=edit"
display_url = "{base_url}/#/packageDisplayMgmt/editDisplayDetail?id={travel.id}&type=edit"
```

Just compute, don't navigate (we want to leave the Planner's tabs at
Package List or wherever they are).

### 4b. Public storefront search

```
1. navigate(tab, "https://www.webuytravel.sg")
2. wait(3s)
3. Search by:
   - type_code (e.g. WBMXMN)
   - then type_name_cn (e.g. "陈建彬" or "客家原乡")
   - then type_name_en (e.g. "Hakka Homeland")
4. Record what's visible: 0 results = expected for draft;
   visible = means somehow already published (alert Planner).
```

UAT note: `webuytravel.sg` is **production** storefront. UAT-created tours
will NOT appear there. So the verify step on UAT will always say "not
visible (UAT does not feed prod storefront)". Adjust messaging accordingly.

### 4c. Final report to parent skill

```yaml
ok: true
admin_urls:
  edit_package: "https://test01.travel.webuy.ren/#/packageAirlineMaintenance/editPackage?id=NNNN&type=edit"
  edit_display: "https://test01.travel.webuy.ren/#/packageDisplayMgmt/editDisplayDetail?id=149&type=edit"
public_visibility:
  searched:    [WBMXMN, "陈建彬", "Hakka Homeland"]
  url:         "https://www.webuytravel.sg"
  visible:     false
  expected:    "draft → not visible until Planner ticks 'Publish for sale'"
next_steps:
  - "Open admin edit_package URL → review tour_code, prices, flights"
  - "Open admin edit_display URL → review wt_travel content + tick 'Publish for sale' when ready"
  - "Wait 2-5 min after publish, re-search webuytravel.sg to confirm live"
```
