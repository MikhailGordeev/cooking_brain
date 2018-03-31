import cv2
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol


def get_qr_data(image_file):
    file_to_decode = cv2.imread(image_file)
    file_to_decode_grey = cv2.cvtColor(file_to_decode, cv2.COLOR_BGR2GRAY)
    (thresh, im_bw) = cv2.threshold(file_to_decode_grey, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    im_bw = cv2.threshold(file_to_decode_grey, thresh, 255, cv2.THRESH_BINARY)[1]
    codes = decode(im_bw, symbols=[ZBarSymbol.QRCODE])
    return codes
