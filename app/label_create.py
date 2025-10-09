"""
label_creator.py

Creates a printable label image containing a QR code plus text (model number & unit ID).

Usage:
    from label_creator import create_label
    img = create_label("001122AABBCC", model_number="MYMODEL")
    img.save("label.png")  # or process as needed
"""
from typing import Optional
import qrcode
from PIL import Image, ImageDraw, ImageFont
from log import logger

def create_label(unit_id, model_number='', width=355, height=120):
    logger.info("create_label called: unit_id=%s, model_number=%s, size=%dx%d",
                unit_id, model_number, width, height)
    print("create_label called: unit_id=%s, model_number=%s, size=%dx%d",
                unit_id, model_number, width, height)

    # --- Input validation ---
    if not isinstance(unit_id, str):
        logger.error("Invalid unit_id type: expected str, got %s", type(unit_id).__name__)
        raise ValueError("Unit ID must be a 12-character hexadecimal string")

    s = unit_id.strip()
    if len(s) != 12 or not all(c in "0123456789abcdefABCDEF" for c in s):
        logger.error("Invalid unit_id value: %r", unit_id)
        raise ValueError("Unit ID must be a 12-character hexadecimal string")

    # Normalize display form (uppercase)
    unit_id_display = s.upper()
    logger.debug("Normalized unit_id for display: %s", unit_id_display)

    # --- Prepare QR data ---
    qr_data = f"Model:{model_number}\nUnitID:{unit_id_display}"
    logger.debug("QR data prepared (len=%d)", len(qr_data))

    try:
        # Create QR code (fit=True lets the library pick a version)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=2,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        logger.info("QR code generated successfully")
    except Exception as e:
        logger.exception("Failed to generate QR code: %s", e)
        raise

    try:
        # Create final label image (grayscale 'L' to make text rendering easier)
        img = Image.new('L', (width, height), 'white')
        draw = ImageDraw.Draw(img)

        # Determine QR size: keep some padding (10px)
        padding = 10
        qr_size = min(height - 2 * padding, width // 2)
        logger.debug("Calculated qr_size=%d, padding=%d", qr_size, padding)

        # Convert QR image to grayscale and resize using high-quality resampling
        if qr_img.mode != 'L':
            qr_img = qr_img.convert('L')
            logger.debug("Converted qr_img to 'L' mode for paste compatibility")

        qr_img = qr_img.resize((qr_size, qr_size))
        logger.debug("Resized QR image to %dx%d", qr_size, qr_size)

        # Paste QR at left with padding
        img.paste(qr_img, (padding, padding))
        logger.debug("Pasted QR image at (%d, %d)", padding, padding)
    except Exception as e:
        logger.exception("Error while preparing/pasting QR image: %s", e)
        raise

    # --- Load fonts (attempt project fonts, fallback to default) ---
    font_small: Optional[ImageFont.FreeTypeFont] = None
    font_large: Optional[ImageFont.FreeTypeFont] = None
    try:
        font_small = ImageFont.truetype("Res/ARIALNB.TTF", size=16)
        logger.info("Loaded small font from Res/ARIALNB.TTF")
    except IOError:
        font_small = ImageFont.load_default()
        logger.warning("Failed to load Res/ARIALNB.TTF; using default font for small text")

    try:
        font_large = ImageFont.truetype("Res/ARLRDBD.TTF", size=20)
        logger.info("Loaded large font from Res/ARLRDBD.TTF")
    except IOError:
        font_large = ImageFont.load_default()
        logger.warning("Failed to load Res/ARLRDBD.TTF; using default font for large text")

    # --- Compose textual content to the right of QR ---
    try:
        text_x = padding + qr_size + padding  # left edge for text area
        text_y_top = padding + 10
        text_width = width - text_x - padding
        logger.debug("Text area: x=%d width=%d", text_x, text_width)

        # Draw model number label and value
        draw.text((text_x - 6, text_y_top), "Model Number:", fill="black", font=font_small)
        draw.text((text_x, text_y_top + 16), model_number, fill="black", font=font_large)

        # Draw unit id label and value near bottom of text area
        unit_label_y = height - padding - 60
        draw.text((text_x - 6, unit_label_y), "Unit ID:", fill="black", font=font_small)
        draw.text((text_x, unit_label_y + 15), unit_id_display, fill="black", font=font_large)

        logger.info("Rendered text on label (model & unit id)")
    except Exception as e:
        logger.exception("Error while drawing text onto label image: %s", e)
        raise

    # --- Convert to strict black & white (mode '1') for thermal / label printers ---
    try:
        bw_image = img.point(lambda x: 0 if x < 128 else 255, mode="1")
        logger.info("Converted image to black & white (mode '1')")
    except Exception as e:
        logger.exception("Failed to convert image to black & white: %s", e)
        raise

    logger.info("Label image created successfully for unit_id=%s", unit_id_display)
    return bw_image