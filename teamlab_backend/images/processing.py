import warnings
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from .constants import (
    ALLOWED_IMAGE_FORMATS,
    MAX_IMAGE_DIMENSION,
    THUMBNAIL_SIZE,
    MAX_IMAGE_BYTES,
)


def validate_image(image_bytes: bytes) -> tuple[str, int, int]:
    if not 0 < len(image_bytes) <= MAX_IMAGE_BYTES:
        raise ValueError('Недопустимый размер файла.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter(
                'error',
                Image.DecompressionBombWarning,
            )
            with Image.open(BytesIO(image_bytes)) as image:
                image.verify()

            with Image.open(BytesIO(image_bytes)) as image:
                image_format = image.format
                width, height = image.size
                image.load()

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombWarning,
        Image.DecompressionBombError,
    ) as exc:
        raise ValueError('Некорректный файл изображения.') from exc

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValueError('Неподдерживаеый формат изображения.')

    if (
        width <= 0
        or height <= 0
        or width > MAX_IMAGE_DIMENSION
        or height > MAX_IMAGE_DIMENSION
    ):
        raise ValueError('Превышены допустимые размеры изображения.')

    return image_format, width, height


def process_image(image_bytes: bytes) -> tuple[bytes, bytes]:
    validate_image(image_bytes)

    with Image.open(BytesIO(image_bytes)) as source:
        image = ImageOps.exif_transpose(source)
        image.load()

        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert(
                'RGBA' if 'A' in image.getbands() else 'RGB'
            )

        thumbnail = ImageOps.fit(
            image,
            THUMBNAIL_SIZE,
            method=Image.Resampling.LANCZOS,
        )
        webp_buffer = BytesIO()
        image.save(webp_buffer, format='WEBP', quality=85)

        thumbnail_buffer = BytesIO()
        thumbnail.save(thumbnail_buffer, format='WEBP', quality=85)

    return webp_buffer.getvalue(), thumbnail_buffer.getvalue()
