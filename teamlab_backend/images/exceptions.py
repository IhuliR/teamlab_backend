from rest_framework.exceptions import APIException


class StorageUnavailable(APIException):
    status_code = 503
    default_detail = 'Хранилище временно недоступно.'
    default_code = 'storage_unavailable'
