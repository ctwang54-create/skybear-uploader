---
name: skybear-publish-gate
description: |
  The human review gate between an uploaded draft and a live product. Walks
  the reviewer through checking a tour on the public site, then — only on an
  explicit go-ahead from them — tells them how to publish it. This skill
  never ticks Publish for sale itself.
---

# skybear-publish-gate (unpublished → published)

Everything this plugin writes lands unpublished (`wt_travel.travel_status =
0`). That is the safety property the whole design rests on: a wrong photo, a
wrong day, a soft hero — all of it is invisible to customers until a person
decides otherwise.

**This skill does not publish.** Publishing is a person ticking a box in
Skybear. The skill's job is to make sure they are looking at the right things
before they do, and to hand them the exact steps afterwards.

## Step 1 — Preview the draft

A draft is not on `webuytravel.sg` yet, so review the Skybear side plus the
locally rendered page:

```
{base_url}/#/packageDisplayMgmt/editDisplayDetail?id={travel_id}&type=edit
{work_dir}/{type_code}_preview.html
```

Screenshot the Edit Display Detail gallery so the reviewer sees what actually
landed, not what the plan intended.

## Step 2 — Walk the checklist with them

Ask about each of these explicitly. Do not summarise them as "looks good".

**Accuracy — the one that can't be fixed later**
- Does every day's photo show something from *that day*? The brochures carry
  mislabelled captions (WBCURC's "Tongren Grand Canyon" photo is the Flaming
  Mountains, 3,000km away), so this is a real failure mode, not a formality.
- Does any photo show a place the tour does not visit?

**Fitness for a sales page**
- Hero: does the ~3:1 crop still read as the landmark, or did the crop cut
  its subject in half?
- Any photo with people's faces close up, police or military, construction,
  ticket gates, litter, or visible watermarks?
- Any photo that is obviously a diagram, a satellite image, a museum
  display, or AI-generated? Two WBCHET brochure photos look rendered rather
  than shot — worth a second opinion from the product team.

**Consistency**
- Do the carousel images look like one set — comparable colour, light and
  framing — or like a scrapbook?
- Any image visibly softer than its neighbours? The preview page flags
  anything upscaled past 1.7×.

**Licensing**
- Every web-sourced image has a `license` and `credit` in `plan.json`.
  Shutterstock previews must be licensed through the Webuy account before
  publishing. Commons images need their attribution honoured.

## Step 3 — Route the answer

**Not approved** → note which slots and why, go back to
`skybear-plan-images` step 4 with those days, re-materialise, re-review.
Nothing on Skybear changes in the meantime; the draft simply stays a draft.

**Approved** → give the Planner these steps and stop. Do not perform them.

> 1. Open `{base_url}/#/packageDisplayMgmt/editDisplayDetail?id={travel_id}&type=edit`
> 2. Scroll to **Product Status**
> 3. Tick ✅ **Publish for sale**
> 4. Click **Save**
>
> The product appears on https://www.webuytravel.sg/ within 5–10 minutes.

Ticking that box is the moment the tour becomes visible to customers, and it
belongs to the person accountable for the product — not to this plugin, and
not on their behalf "since they already said yes to the images".

## Step 4 — Check it live

Once the Planner confirms they have published, open
`https://www.webuytravel.sg/tours/{travel_id}-{slug}` and check the rendered
result — the hero crop, the gallery, the per-day images. The stored image and
the rendered image are different things: the site serves through
`prod-webuysg.oss.webuy.ren` with an `x-oss-process` resize chain, so this is
the first point at which anyone sees what a customer sees.

If something reads badly here, it is still fixable — untick *Publish for
sale*, fix the images, re-publish.
