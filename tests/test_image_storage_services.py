from io import BytesIO
from unittest.mock import patch

import pytest

from images.services import download_image, save_processed_image


IMAGE_BYTES = b'complete-image-data'
IMAGE_ETAG = '"image-etag"'


def s3_response(data, *, content_length=None):
    body = BytesIO(data)
    return body, {
        'Body': body,
        'ContentLength': (
            len(data) if content_length is None else content_length
        ),
    }


def test_download_image_checks_etag_and_confirmed_size(settings):
    settings.STORAGES['media_s3']['OPTIONS']['bucket_name'] = 'teamlab-media'
    body, response = s3_response(IMAGE_BYTES)

    with patch('images.services.boto3.client') as client_factory:
        client_factory.return_value.get_object.return_value = response

        result = download_image(
            key='temporary/upload/image',
            expected_etag=IMAGE_ETAG,
            expected_size=len(IMAGE_BYTES),
            max_size=len(IMAGE_BYTES),
        )

    assert result == IMAGE_BYTES
    assert body.closed
    client_factory.return_value.get_object.assert_called_once_with(
        Bucket='teamlab-media',
        Key='temporary/upload/image',
        IfMatch=IMAGE_ETAG,
    )


@pytest.mark.parametrize(
    ('data', 'content_length', 'expected_size'),
    (
        (IMAGE_BYTES, len(IMAGE_BYTES), len(IMAGE_BYTES) + 1),
        (IMAGE_BYTES[:-1], len(IMAGE_BYTES), len(IMAGE_BYTES)),
    ),
    ids=('confirmed-size-mismatch', 'truncated-body'),
)
def test_download_image_rejects_inconsistent_size(
    data,
    content_length,
    expected_size,
):
    body, response = s3_response(data, content_length=content_length)

    with patch('images.services.boto3.client') as client_factory:
        client_factory.return_value.get_object.return_value = response

        with pytest.raises(ValueError):
            download_image(
                key='temporary/upload/image',
                expected_etag=IMAGE_ETAG,
                expected_size=expected_size,
                max_size=len(IMAGE_BYTES),
            )

    assert body.closed


def test_save_processed_image_sets_webp_content_type():
    with patch('images.services.storages') as storage_handler:
        storage = storage_handler.__getitem__.return_value
        storage.save.return_value = 'media/upload/g0/a1/original.webp'

        saved_key = save_processed_image(
            key='media/upload/g0/a1/original.webp',
            image_bytes=IMAGE_BYTES,
        )

    assert saved_key == 'media/upload/g0/a1/original.webp'
    key, content = storage.save.call_args.args
    assert key == saved_key
    assert content.read() == IMAGE_BYTES
    assert content.content_type == 'image/webp'
