from PIL import Image
import zbarlight


def get_qr_data(image_file):
    file_path = image_file
    with open(file_path, 'rb') as image_file:
        image = Image.open(image_file)
        image.load()
    codes = zbarlight.scan_codes('qrcode', image)
    return codes
