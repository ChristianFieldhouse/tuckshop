#!/usr/bin/env python3
"""
requires: pip install pillow qrcode
this script generates an a4-printable png image (300dpi) with a grid of qr codes,
each showing a price and a “scan to pay” arrow.
"""

from pathlib import Path
import qrcode
from PIL import Image, ImageDraw, ImageFont

# a4 dimensions at 300dpi (approximate pixels)
A4_WIDTH = 2480
A4_HEIGHT = 3508
MARGIN = 50  # margin around the grid in pixels

# grid settings: adjust columns/rows as needed
cols = 3
rows = 4
cell_width = (A4_WIDTH - 2 * MARGIN) // cols
cell_height = (A4_HEIGHT - 2 * MARGIN) // rows

product = "custard_creams"
item_count_file = Path(f"item_counts/{product}.txt")
count = 0
if not item_count_file.is_file():
    item_count_file.write_text(str(count))
count = int(item_count_file.read_text())
item_count_file.write_text(str(count + cols*rows))

# sample product data; add as many items as needed (max = cols*rows)
products = [
    {"product": f"{product}_{count+i:04}", "amount": "1.00"}
    for i in range(cols*rows)
]

# base url for your google apps script; the qr code will include query parameters for each product
BASE_URL = ("https://christianfieldhouse.github.io/tuckshop/buy.html")

# create a blank a4 white page
page = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
draw = ImageDraw.Draw(page)

text_font_size = 70
try:
    text_font = ImageFont.truetype("Coolvetica Rg.otf", text_font_size)
except Exception:
    print("get a font!!!")
    text_font = ImageFont.load_default()

# determine the appropriate resampling filter
try:
    resample_filter = Image.Resampling.LANCZOS
except AttributeError:
    resample_filter = Image.ANTIALIAS

for index, item in enumerate(products):
    # determine cell position
    col = index % cols
    row = index // cols
    cell_x = MARGIN + col * cell_width
    cell_y = MARGIN + row * cell_height

    # construct the qr code url with product data
    qr_url = f"{BASE_URL}?amount={item['amount']}&product={item['product']}"

    # generate the qr code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # decide the qr code image size (e.g. 70% of cell height)
    qr_size = int(cell_height * 0.7)
    qr_img = qr_img.resize((qr_size, qr_size), resample=resample_filter)

    # center the qr code in the cell horizontally at the top of the cell
    qr_x = cell_x + (cell_width - qr_size) // 2
    qr_y = cell_y
    page.paste(qr_img, (qr_x, qr_y))

    # define texts; ditch the arrow and "£" in favor of "GBP" and "scan to pay" to the right.
    price_text = f"GBP {item['amount']}"
    scan_text = "scan to pay"

    # measure both texts using textbbox
    bbox_price = draw.textbbox((0, 0), price_text, font=text_font)
    price_w = bbox_price[2] - bbox_price[0]
    price_h = bbox_price[3] - bbox_price[1]

    bbox_scan = draw.textbbox((0, 0), scan_text, font=text_font)
    scan_w = bbox_scan[2] - bbox_scan[0]
    scan_h = bbox_scan[3] - bbox_scan[1]

    # set a gap between the price and the scan text (e.g. 20 pixels)
    gap = 20
    combined_width = price_w + gap + scan_w

    # position the texts centered horizontally below the qr code.
    text_x = cell_x + (cell_width - combined_width) // 2
    text_y = qr_y + qr_size + 10  # gap of 10 pixels below the qr code

    # draw the price text first
    draw.text((text_x, text_y), price_text, fill="black", font=text_font)
    # draw the scan text to the right of the price text
    draw.text((text_x + price_w + gap, text_y), scan_text, fill="black", font=text_font)

# add bottom label text
bottom_text = f"{product} {count} : {count + cols*rows}"
small_text_font_size = 30
try:
    small_text_font = ImageFont.truetype("coolvetica/Coolvetica Rg.otf", small_text_font_size)
except Exception:
    small_text_font = ImageFont.load_default()

# measure bottom text size using textbbox
bbox_bottom = draw.textbbox((0, 0), bottom_text, font=small_text_font)
bottom_text_w = bbox_bottom[2] - bbox_bottom[0]
bottom_text_h = bbox_bottom[3] - bbox_bottom[1]

# position the text centered horizontally, just above the bottom margin
bottom_text_x = (A4_WIDTH - bottom_text_w) // 2
bottom_text_y = A4_HEIGHT - MARGIN - bottom_text_h

draw.text((bottom_text_x, bottom_text_y), bottom_text, fill="black", font=small_text_font)


# save the resulting a4 grid as a png file
page.save(f"printouts/{bottom_text}.png")
print(f"Saved {bottom_text}")
