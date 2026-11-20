import os
import gdstk
import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import label

# --- Settings ---
INPUT_PNG = "logo.png"          # Black-on-white line-art image
OUT_DIR = "src/macros"
MACRO_NAME = "my_logo"
TARGET_W = 180                  # ~117 um wide (fits easily inside 346.64 x 160.72 um)
PIXEL_SIZE_UM = 0.65            # >= 0.65 um passes MT.1 (0.44), MT.2a (0.46), and MT.2b (0.60)
THICKEN_PASSES = 2              # Thickens 1px lines before resizing
METAL_LAYER = 81                # gf180mcuD Metal5 (top routing layer)
PR_BNDRY_LAYER = 0              # Required by LibreLane streamout (invisible on silicon)

os.makedirs(OUT_DIR, exist_ok=True)

# 1. Load line-art image & thicken thin lines before resizing
img = Image.open(INPUT_PNG).convert("L")
for _ in range(THICKEN_PASSES):
    img = img.filter(ImageFilter.MinFilter(3))

TARGET_H = round(TARGET_W * (img.height / img.width))
img = img.resize((TARGET_W, TARGET_H), Image.Resampling.BILINEAR)
arr = np.array(img) < 200

# Crop empty white border
ys, xs = np.where(arr)
arr = arr[ys.min():ys.max()+1, xs.min():xs.max()+1]

# Fix isolated 2x2 checkerboard corners
rows, cols = arr.shape
fixes = []
for r in range(rows - 1):
    for c in range(cols - 1):
        patch = arr[r:r+2, c:c+2]
        if np.array_equal(patch, [[True, False], [False, True]]):
            fixes.append((r, c+1))
        elif np.array_equal(patch, [[False, True], [True, False]]):
            fixes.append((r, c))
for r, c in fixes:
    arr[r, c] = True

# Remove ANY connected component with fewer than 2 pixels (2 * 0.65^2 = 0.845 um^2 > 0.5625 MT.4 limit)
labeled, num_features = label(arr)
for comp_id in range(1, num_features + 1):
    if np.sum(labeled == comp_id) < 2:
        arr[labeled == comp_id] = False

width_um = round(cols * PIXEL_SIZE_UM, 3)
height_um = round(rows * PIXEL_SIZE_UM, 3)

# 2. Build GDS
lib = gdstk.Library(unit=1e-6, precision=1e-9)
cell = lib.new_cell(MACRO_NAME)
cell.add(gdstk.rectangle((0.0, 0.0), (width_um, height_um), layer=PR_BNDRY_LAYER))

rects = []
for r in range(rows):
    for c in range(cols):
        if arr[r, c]:
            x0 = round(c * PIXEL_SIZE_UM, 3)
            y0 = round((rows - 1 - r) * PIXEL_SIZE_UM, 3)
            rects.append(
                gdstk.rectangle(
                    (x0, y0),
                    (round(x0 + PIXEL_SIZE_UM, 3), round(y0 + PIXEL_SIZE_UM, 3)),
                    layer=METAL_LAYER,
                )
            )

merged = gdstk.boolean(rects, [], "or", layer=METAL_LAYER) if rects else []
cell.add(*merged)
lib.write_gds(f"{OUT_DIR}/{MACRO_NAME}.gds")

# 3. Build transparent LEF
lef = f"""VERSION 5.7 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO {MACRO_NAME}
  CLASS BLOCK ;
  FOREIGN {MACRO_NAME} 0.000 0.000 ;
  ORIGIN 0.000 0.000 ;
  SIZE {width_um:.3f} BY {height_um:.3f} ;
END {MACRO_NAME}

END LIBRARY
"""
with open(f"{OUT_DIR}/{MACRO_NAME}.lef", "w") as f:
    f.write(lef)

print(f"Generated {OUT_DIR}/{MACRO_NAME}.gds ({width_um} x {height_um} um)")
