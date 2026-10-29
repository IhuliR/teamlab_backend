from io import BytesIO
from unittest.mock import patch

import pytest
from PIL import Image

from images.constants import (
    MAX_IMAGE_BYTES,
    MAX_IMAGE_DIMENSION,
    THUMBNAIL_SIZE,
)
from images.processing import process_image, validate_image


def image_bytes(
    image_format,
    *,
    size=(48, 32),
    mode='RGB',
    color=None,
    exif=None,
):
    if color is None:
        color = 128 if mode == 'L' else (25, 100, 200)
    image = Image.new(mode, size, color)
    buffer = BytesIO()
    save_kwargs = {'format': image_format}
    if exif is not None:
        save_kwargs['exif'] = exif
    image.save(buffer, **save_kwargs)
    return buffer.getvalue()


def decoded_image(image_data):
    image = Image.open(BytesIO(image_data))
    image.load()
    return image


@pytest.mark.parametrize('image_format', ('JPEG', 'PNG', 'WEBP'))
def test_supported_image_is_validated_and_processed(image_format):
    source_size = (48, 32)
    source = image_bytes(image_format, size=source_size)

    assert validate_image(source) == (image_format, *source_size)

    processed, thumbnail = process_image(source)
    processed_image = decoded_image(processed)
    thumbnail_image = decoded_image(thumbnail)

    assert processed_image.format == 'WEBP'
    assert processed_image.size == source_size
    assert thumbnail_image.format == 'WEBP'
    assert thumbnail_image.size == THUMBNAIL_SIZE


def test_process_image_preserves_rgba_transparency():
    source = image_bytes(
        'PNG',
        size=(40, 30),
        mode='RGBA',
        color=(255, 0, 0, 0),
    )

    processed, thumbnail = process_image(source)
    processed_image = decoded_image(processed)
    thumbnail_image = decoded_image(thumbnail)

    assert processed_image.mode == 'RGBA'
    assert processed_image.getchannel('A').getextrema() == (0, 0)
    assert thumbnail_image.mode == 'RGBA'
    assert thumbnail_image.getchannel('A').getextrema() == (0, 0)


def test_process_image_applies_exif_orientation():
    exif = Image.Exif()
    exif[274] = 6
    source = image_bytes(
        'JPEG',
        size=(40, 20),
        exif=exif,
    )

    processed, thumbnail = process_image(source)
    processed_image = decoded_image(processed)
    thumbnail_image = decoded_image(thumbnail)

    assert processed_image.size == (20, 40)
    assert thumbnail_image.size == THUMBNAIL_SIZE


@pytest.mark.parametrize(
    'invalid_data',
    (b'', b'not-an-image'),
    ids=('empty', 'random-bytes'),
)
def test_validate_image_rejects_empty_or_random_bytes(invalid_data):
    with pytest.raises(ValueError):
        validate_image(invalid_data)


def test_validate_and_process_reject_corrupted_image():
    valid_image = image_bytes('PNG')
    corrupted_image = valid_image[:len(valid_image) // 2]

    with pytest.raises(ValueError):
        validate_image(corrupted_image)

    with pytest.raises(ValueError):
        process_image(corrupted_image)


def test_validate_image_rejects_file_over_byte_limit():
    oversized_data = b'x' * (MAX_IMAGE_BYTES + 1)

    with pytest.raises(ValueError, match='Недопустимый размер файла'):
        validate_image(oversized_data)


def test_validate_image_rejects_dimension_over_limit():
    oversized_image = image_bytes(
        'PNG',
        size=(MAX_IMAGE_DIMENSION + 1, 1),
    )

    with pytest.raises(ValueError, match='Превышены допустимые размеры'):
        validate_image(oversized_image)


def test_validate_image_wraps_decoder_error():
    with patch(
        'images.processing.Image.open',
        side_effect=OSError('decoder failed'),
    ):
        with pytest.raises(ValueError, match='Некорректный файл изображения'):
            validate_image(b'non-empty')


def test_validate_image_rejects_decompression_bomb_warning(monkeypatch):
    source = image_bytes('PNG', size=(20, 20))
    monkeypatch.setattr(Image, 'MAX_IMAGE_PIXELS', 300)

    with pytest.raises(ValueError, match='Некорректный файл изображения'):
        validate_image(source)


def test_process_image_converts_grayscale_jpeg():
    source = image_bytes('JPEG', mode='L')

    processed, thumbnail = process_image(source)
    processed_image = decoded_image(processed)
    thumbnail_image = decoded_image(thumbnail)

    assert processed_image.format == 'WEBP'
    assert processed_image.size == (48, 32)
    assert thumbnail_image.format == 'WEBP'
    assert thumbnail_image.size == THUMBNAIL_SIZE
