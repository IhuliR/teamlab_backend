# Интеграция frontend с загрузкой изображений

Новый поток загружает файл напрямую из браузера в Yandex Object Storage, после
чего backend проверяет объект, обрабатывает его через Celery/Pillow и привязывает
готовое изображение к сущности. Все запросы к TeamLab API требуют JWT access
token. Presigned POST в Object Storage отправляется без JWT.

## Ограничения

| `kind` | Назначение | `target_id` | Максимальный размер |
|---|---|---|---:|
| `user_avatar` | Аватар текущего пользователя | Не передаётся | 1 МиБ (1048576 байт) |
| `project_image` | Изображение проекта | ID проекта владельца | 2 МиБ (2097152 байта) |
| `portfolio_image` | Изображение работы портфолио | ID работы владельца | 2 МиБ (2097152 байта) |

Поддерживаются `image/jpeg`, `image/png` и `image/webp`. После загрузки backend
дополнительно проверяет точный размер, Content-Type, ETag, содержимое и формат.
Максимальный размер изображения — 2048x2048 px. Результат — WebP исходных
размеров и WebP-миниатюра строго 256x256.

## Полный поток загрузки

### 1. Создать upload-сессию

```http
POST /api/v1/image-uploads/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "kind": "project_image",
  "target_id": 42,
  "content_type": "image/jpeg",
  "size_bytes": 734003
}
```

Для аватара поле `target_id` передавать нельзя. Для проекта и работы портфолио
оно обязательно. `size_bytes` должен быть равен `file.size`, а `content_type` —
`file.type`.

Успешный ответ — `201 Created`:

```json
{
  "upload_id": "1e575f20-a5d2-4cd6-92cf-728f817a34df",
  "status": "awaiting_upload",
  "expires_at": "2026-11-03T12:05:00+00:00",
  "upload_url": "https://storage.yandexcloud.net/teamlab-media",
  "upload_fields": {
    "Content-Type": "image/jpeg",
    "key": "temporary/1e575f20-a5d2-4cd6-92cf-728f817a34df/image",
    "policy": "<opaque-value>"
  }
}
```

`upload_fields` в примере сокращён. Реальный объект содержит все поля подписи,
которые вернул backend. Клиент не должен разбирать, переименовывать или изменять
их значения. Presigned POST действует 5 минут, точное время указано в
`expires_at`.

### 2. Отправить файл в Object Storage

Добавьте в `FormData` все поля из `upload_fields`, затем файл последним полем
`file`. Не устанавливайте HTTP-заголовок `Content-Type` вручную: браузер сам
добавит `multipart/form-data` с boundary.

```ts
const formData = new FormData();

for (const [name, value] of Object.entries(uploadFields)) {
  formData.append(name, value);
}

formData.append('file', file);

const storageResponse = await fetch(uploadUrl, {
  method: 'POST',
  body: formData,
});

if (!storageResponse.ok) {
  throw new Error(`Object Storage upload failed: ${storageResponse.status}`);
}
```

Любой успешный `2xx` означает, что можно переходить к confirm. При ошибке S3 не
вызывайте confirm. Если подпись истекла или условия policy не выполнены, создайте
новую upload-сессию.

Frontend может показывать локальное превью через `URL.createObjectURL(file)` до
завершения обработки. После получения готового URL вызовите
`URL.revokeObjectURL()` для локального preview.

### 3. Подтвердить загрузку

```http
POST /api/v1/image-uploads/1e575f20-a5d2-4cd6-92cf-728f817a34df/confirm/
Authorization: Bearer <access-token>
```

Тело не требуется. Backend выполняет HEAD объекта и сверяет размер и MIME-тип.
Успешный ответ — `200 OK`:

```json
{
  "upload_id": "1e575f20-a5d2-4cd6-92cf-728f817a34df",
  "status": "queued"
}
```

Повторный confirm в статусе `queued` безопасен и также возвращает `200` без
повторной проверки S3.

### 4. Опросить статус обработки

```http
GET /api/v1/image-uploads/1e575f20-a5d2-4cd6-92cf-728f817a34df/
Authorization: Bearer <access-token>
```

Пока изображение обрабатывается:

```json
{
  "upload_id": "1e575f20-a5d2-4cd6-92cf-728f817a34df",
  "kind": "project_image",
  "status": "processing",
  "image_url": null,
  "thumbnail_url": null,
  "error_code": null,
  "error_message": ""
}
```

При успешном завершении:

```json
{
  "upload_id": "1e575f20-a5d2-4cd6-92cf-728f817a34df",
  "kind": "project_image",
  "status": "ready",
  "image_url": "https://storage.yandexcloud.net/teamlab-media/media/.../original.webp?<signature>",
  "thumbnail_url": "https://storage.yandexcloud.net/teamlab-media/media/.../thumbnail.webp?<signature>",
  "error_code": null,
  "error_message": ""
}
```

Продолжайте polling для `queued` и `processing`. Остановите его для `ready` или
`failed`. В `failed` покажите пользователю понятное сообщение и разрешите начать
новую загрузку. Текущая реализация использует коды `invalid_image`,
`storage_error` и `attempts_exhausted`.

### 5. Привязать готовое изображение

```http
POST /api/v1/image-uploads/1e575f20-a5d2-4cd6-92cf-728f817a34df/attach/
Authorization: Bearer <access-token>
```

Тело не требуется. Upload-сессия уже связана с нужной сущностью через `kind` и
`target_id`. Успешный ответ — `200 OK` с теми же полями polling и статусом
`attached`:

```json
{
  "upload_id": "1e575f20-a5d2-4cd6-92cf-728f817a34df",
  "kind": "project_image",
  "status": "attached",
  "image_url": "https://storage.yandexcloud.net/teamlab-media/media/.../original.webp?<signature>",
  "thumbnail_url": "https://storage.yandexcloud.net/teamlab-media/media/.../thumbnail.webp?<signature>",
  "error_code": null,
  "error_message": ""
}
```

Attach разрешён только для `ready`. Повторный attach той же уже привязанной
загрузки идемпотентен. При замене старое изображение остаётся доступным до
успешной привязки нового, после чего удаляется фоновой задачей.

## Варианты create-запроса

Аватар текущего пользователя:

```json
{
  "kind": "user_avatar",
  "content_type": "image/webp",
  "size_bytes": 524288
}
```

Изображение проекта владельца:

```json
{
  "kind": "project_image",
  "target_id": 42,
  "content_type": "image/png",
  "size_bytes": 1048576
}
```

Изображение собственной работы портфолио:

```json
{
  "kind": "portfolio_image",
  "target_id": 17,
  "content_type": "image/jpeg",
  "size_bytes": 734003
}
```

Остальные шаги и endpoint attach одинаковы для всех трёх вариантов.

## Замена и удаление

Для замены через S3 выполните полный новый поток и вызовите attach новой
upload-сессии. Старое изображение не нужно удалять заранее.

Отдельное удаление изображения:

```http
DELETE /api/v1/users/me/avatar/
DELETE /api/v1/projects/{project_id}/image/
DELETE /api/v1/users/me/portfolio-works/{portfolio_work_id}/image/
Authorization: Bearer <access-token>
```

Успешный ответ — `204 No Content`. Удаление изображения проекта разрешено только
его владельцу; portfolio endpoint видит только работы текущего пользователя.
Удаление самой работы выполняется через
`DELETE /api/v1/users/me/portfolio-works/{portfolio_work_id}/` и также запускает
очистку связанного S3-изображения.

## Ошибки API

| Код | Когда возникает |
|---:|---|
| `400` | Неверный `kind`, MIME, размер или `target_id`; истёк confirm; объект отсутствует в S3; размер/MIME не совпали; attach вызван не для `ready`. |
| `401` | Нет корректного JWT access token. |
| `403` | Пользователь не владеет проектом/работой либо право владения изменилось до attach. |
| `404` | Сущность или upload-сессия не найдена. Чужая upload-сессия также скрывается как `404`. |
| `503` | Yandex Object Storage недоступен либо backend не смог сформировать signed URL. |

Ошибки DRF обычно приходят объектом полей, например:

```json
{
  "size_bytes": ["Размер изображения превышает лимит."]
}
```

Ошибка доступности хранилища:

```json
{
  "detail": "Хранилище временно недоступно."
}
```

## Signed URL

`image_url`, `thumbnail_url`, а также поля `avatar`/`image` в обычных ответах API
могут содержать подписанные URL приватного бакета. Они действуют 1 час.

- Не сохраняйте signed URL как постоянный идентификатор изображения.
- Не удаляйте и не изменяйте query-параметры подписи.
- После истечения URL повторите GET исходного ресурса или polling upload-сессии,
  если `upload_id` сохранён на клиенте.
- Для профиля обновляйте `GET /api/v1/users/me/` или
  `GET /api/v1/users/{user_id}/`; для проекта —
  `GET /api/v1/projects/{project_id}/`; для своего портфолио —
  `GET /api/v1/users/me/portfolio-works/`.

## Совместимость с Base64

Существующие сценарии продолжают работать и заменяют/удаляют ранее привязанные
S3-изображения:

- `PUT /api/v1/users/me/avatar/` — `{"avatar": "data:image/png;base64,..."}`;
- `PATCH /api/v1/users/me/` — поле `avatar` с data URL или `null`;
- `POST /api/v1/projects/` и `PATCH /api/v1/projects/{project_id}/` — поле
  `image` с data URL; в PATCH `null` удаляет изображение;
- `POST /api/v1/users/me/portfolio-works/` и
  `PATCH /api/v1/users/me/portfolio-works/{portfolio_work_id}/` — необязательное
  поле `image` с data URL; в PATCH `null` удаляет изображение.

Для новых загрузок предпочтителен presigned POST: он не передаёт содержимое файла
через Django и предоставляет статус фоновой обработки.
