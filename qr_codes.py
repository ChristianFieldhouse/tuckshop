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

def save_codes(product, price, cols=3, rows=4, from_0=False):
    cell_width = (A4_WIDTH - 2 * MARGIN) // cols
    cell_height = (A4_HEIGHT - 2 * MARGIN) // rows
    item_count_file = Path(f"item_counts/{product}.txt")
    count = 0
    if not item_count_file.is_file():
        item_count_file.write_text(str(count))
    if not from_0:
        count = int(item_count_file.read_text())
    item_count_file.write_text(str(count + cols*rows))

    # sample product data; add as many items as needed (max = cols*rows)
    products = [
        {"product": f"{product}_{count+i:04}", "amount": price}
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

        # center the qr code in the cell
        qr_x = cell_x + (cell_width - qr_size) // 2
        qr_y = cell_y + (cell_height - qr_size) // 2
        page.paste(qr_img, (qr_x, qr_y))

        price_text = f"£{item['amount']}, scan to pay"
        item_text = item['product']

        def get_wh(text):
            bbox_price = draw.textbbox((0, 0), text, font=text_font)
            w = bbox_price[2] - bbox_price[0]
            h = bbox_price[3] - bbox_price[1]
            return w, h

        price_w, price_h = get_wh(price_text)
        item_w, item_h = get_wh(item_text)

        # set a gap between the price and the scan text (e.g. 20 pixels)
        gapy = 10

        # position the texts centered horizontally below the qr code.
        text_x = cell_x + (cell_width - price_w) // 2
        text_y = qr_y + qr_size + gapy
        draw.text((text_x, text_y), price_text, fill="black", font=text_font)

        top_text_x = cell_x + (cell_width - item_w)//2
        top_text_y = qr_y - item_h - gapy
        draw.text((top_text_x, top_text_y), item_text, fill="black", font=text_font)

    filename = f"printouts/{product}_{count}_to_{count + cols*rows}.png"
    page.save(filename)
    print(f"Saved {filename}")

if __name__ == "__main__":
    for i in range(5):
        save_codes("crisps_2_pack", "1.00", from_0=(i==0))
    for i in range(1):
        save_codes("custard_creams", "1.00", from_0=(i==0))
    for i in range(1):
        save_codes("digestives", "1.50", from_0=(i==0))