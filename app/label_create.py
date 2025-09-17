import qrcode
from PIL import Image, ImageDraw, ImageFont

def create_label(unit_id, model_number='', width=355, height=120):
    # Validate unit ID
    if (not isinstance(unit_id, str) or 
        len(unit_id) != 12 or 
        not all(c in "0123456789abcdefABCDEF" for c in unit_id)):
        raise ValueError("Unit ID must be a 12-character hexadecimal string")

    # Create combined data for QR code
    qr_data = f"Model:{model_number}\nUnitID:{unit_id}"
    
    # Generate QR code with automatic version and error correction
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=2,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Create main image
    img = Image.new('L', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Calculate dimensions
    qr_size = min(height - 20, width // 2)  # QR size with 10px padding
    qr_img = qr_img.resize((qr_size, qr_size))
    
    # Paste QR code on left with 10px padding
    img.paste(qr_img, (10, 10))
    
    # Load font (try Arial first, fallback to default)
    try:
        font = ImageFont.truetype("Res/ARIALNB.TTF", size=16)
    except IOError:
        font = ImageFont.load_default()
    
    # Load font (try Arial first, fallback to default)
    try:
        fontLarge = ImageFont.truetype("Res/ARLRDBD.TTF", size=20)
    except IOError:
        fontLarge = ImageFont.load_default()
    
    # Text positions
    text_x = qr_size + 10
    text_width = width - text_x - 10
    
    # Calculate font size based on available space
    #max_font_size = min(text_width // 10, height // 6)
    #try:
    #    font = ImageFont.truetype("arial.ttf", max_font_size)
    #except IOError:
    #    font = ImageFont.load_default()
    
    # Draw model number (top)
    draw.text((text_x-6, 20), f"Model Number:", fill="black", font=font)
    draw.text((text_x, 20 + 16), model_number, fill="black", font=fontLarge)
    
    # Draw unit ID (bottom)
    draw.text((text_x-6, height - 60), "Unit ID:", fill="black", font=font)
    draw.text((text_x, height - 60 + 15), unit_id, fill="black", font=fontLarge)
    
    #Convert to black and white
    bw_image = img.point(lambda x: 0 if x < 128 else 255, mode="1")

    
    return bw_image