from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtGui import QPixmap
from pylibdmtx.pylibdmtx import encode


def generate_datamatrix_image(data: str) -> Image:
    encoded = encode(f"${data}".encode('utf-8'), fnc1=36)
    img = Image.frombytes(
        'RGB', (encoded.width, encoded.height), encoded.pixels
    )
    return img


def get_qt_pixmap(image: Image) -> QPixmap:
    converted_img = image.convert("RGBA")
    qim = ImageQt(converted_img)
    # noinspection PyTypeChecker
    pix = QPixmap.fromImage(qim)
    return pix


def get_gs1dm_pixmap(data: str) -> QPixmap:
    img = generate_datamatrix_image(data)
    return get_qt_pixmap(img)
