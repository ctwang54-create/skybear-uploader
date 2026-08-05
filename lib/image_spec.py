"""Webuy house image standard — the single source of truth for every slot.

The numbers here are **measured from live production**, not from the Skybear
admin UI hints. The Edit Display Detail page suggests "1920×1080 (16:9)" for
Image Carousel, but no shipped product follows it. Sampling the OSS originals
behind `webuytravel.sg/tours/115` (9D8N Guizhou, a direct style peer of the
tours we upload) gave:

    1080×1440 (3:4)  ×6      1440×1080 (4:3)  ×3
    1080×1923 (9:16) ×3      1012× 847 (thumb)
    200–900 KB JPEG, served from prod-webuysg.oss.webuy.ren/travel-video/

So the real house scale is a **1080-class short edge**, with mixed aspect
ratios — which is exactly why the live catalogue looks inconsistent. The
product page crops the first carousel image into a very wide hero band, and a
9:16 portrait loses most of its frame there.

Decision (2026-08-05, with wangchengtai): normalise everything to **4:3
landscape at 1440×1080**. It matches the largest live tier, survives the hero
crop, and makes the carousel uniform.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SlotSpec:
    """Target geometry + encoding for one Skybear image slot."""

    name: str
    width: int
    height: int
    max_bytes: int
    jpeg_quality: int
    max_count: int
    max_upscale: float

    @property
    def aspect(self) -> float:
        return self.width / self.height

    @property
    def min_source_width(self) -> int:
        """Narrowest crop window that can fill this slot without going soft.

        Note this is measured on the **cropped** window, not the raw file.
        Cropping a 942×579 brochure photo to 4:3 leaves only 772px of width
        to work with — the raw long edge flatters it.
        """
        return int(round(self.width / self.max_upscale))


# Skybear caps every upload at 6MB; we aim well under so OSS re-encode and
# the `x-oss-process` resize chain never hit the ceiling.
_MAX_BYTES = 5 * 1024 * 1024

# Image Carousel → wt_travel_image (image_type=1). The first image becomes
# the product-page hero, rendered ~1600px wide and cropped to a ~3:1 band.
#
# The 2.0 ceiling is measured, not assumed. A 1.65 ceiling was tried first
# and rejected zero-for-three across the launch brochures — every brochure
# photo lands at a 719–860px 4:3 crop — which would have handed the whole
# carousel to stock imagery. Rendering the worst case (a 733×704 Huangguoshu
# Falls shot, 1.97×) at full size showed no objectionable softening, and the
# live catalogue's own heroes are already cropped out of ~1080px-wide
# regions, so this bar is at or above what ships today.
CAROUSEL = SlotSpec("carousel", 1440, 1080, _MAX_BYTES, 86, 10, max_upscale=2.0)

# List Thumbnail → wt_travel.list_thumbneil (sic — the column really is
# misspelled). Live thumb is 1012×847 ≈ 6:5; 4:3 sits close and keeps one
# ratio across the whole product.
THUMBNAIL = SlotSpec("thumbnail", 1440, 1080, _MAX_BYTES, 86, 1, max_upscale=2.0)

# Per-day Image Grid → wt_travel_section_image. Rendered as small tiles, so
# a softer source is invisible here. The looser ceiling is deliberate: it is
# what lets a 725px brochure photo still serve its own day instead of being
# replaced by stock, which is the whole point of PDF-first.
SECTION = SlotSpec("section", 1200, 900, _MAX_BYTES, 84, 10, max_upscale=1.90)

# Cover Video Asset → wt_travel.video_cover_url. The one slot that is
# genuinely portrait (UI hint 986×1752 ≈ 9:16) — do NOT 4:3 this one.
COVER_PORTRAIT = SlotSpec("cover_portrait", 986, 1752, _MAX_BYTES, 86, 1, max_upscale=1.65)


# --- quality gates ----------------------------------------------------

# Below this on either edge it is furniture, not a photo — the brochures
# embed 67×64 / 87×81 / 160×160 icons and 73×70 bullet glyphs.
MIN_ANY_EDGE = 300

# Page-wide banners and rule lines. Measured: 1562×386 (4.05) and 1294×320
# (4.04) are decorative headers in all three samples.
MAX_ASPECT = 3.0
MIN_ASPECT = 1 / 3.0

# Smallest 4:3 crop window worth keeping at all. Under this the photo can't
# even serve a section tile, so the day goes to the web fallback.
MIN_PDF_CROP_WIDTH = SECTION.min_source_width  # 632px


def crop_window(width: int, height: int, aspect: float) -> tuple[int, int]:
    """Largest (w, h) of ratio `aspect` that fits inside `width`×`height`.

    This — not the raw file size — is the number that decides whether a
    source can fill a slot. A 942×579 photo has a healthy-looking 942px
    long edge, but the widest 4:3 window inside it is only 772px, because
    the crop is bounded by the 579px height.
    """
    if width / height > aspect:  # too wide → height-bound
        h = height
        w = int(round(h * aspect))
    else:  # too tall (or exact) → width-bound
        w = width
        h = int(round(w / aspect))
    return w, h
