# TeamLab Seed Reference

## 1. Purpose

Файл фиксирует утверждённые seed-данные для системных справочников TeamLab: `Field`, `Specialization` и `Skill`. Он предназначен для следующего этапа: подготовки seed-файла и idempotent management command для наполнения базы данных.

## 2. Scope and rules

- `Field` и `Specialization` — системные справочники.
- `Skill` — системный справочник.
- `Specialization` используется для matching пользователя и роли проекта.
- `Skill` используется для уточнения профиля, требований роли, подсказок, фильтров и поиска.
- `Skill` не должен дублировать `Field` или `Specialization`.
- Этот файл не является миграцией, кодом, management command, seed JSON/YAML или API-контрактом.

## 3. Field seed data

| order | name | slug | is_featured | description | notes |
| --- | --- | --- | --- | --- | --- |
| 1 | Дизайн | design | true | Визуальные, интерфейсные и художественные роли. | Универсальный entry-point для visual и digital design. |
| 2 | Звук и музыка | audio-music | true | Звук, музыка, запись, обработка и музыкальный production. | Отдельная audio/music-корзина; не сливать с video production. |
| 3 | Контент | content | true | Тексты, сценарии, редактура и создание контента. | Короткое широкое название вместо `Контент и тексты`. |
| 4 | Маркетинг и продвижение | marketing | true | Продвижение, paid/social/PR-коммуникации и рост аудитории. | Отдельно от content craft; отвечает за distribution/growth. |
| 5 | Разработка | development | true | Software, web, mobile, game и прикладная разработка. | Опорное digital-направление рядом с дизайном. |
| 6 | Съёмки и продакшн | production | true | Видео, съёмки, режиссура, монтаж и актёрские роли. | Включает shooting, post-production и production execution. |
| 7 | Продукт | product | true | Product management, аналитика, discovery и исследования. | Короткое top-level название вместо `Управление продуктом`. |

## 4. Specialization seed data

### Дизайн (`design`)

| order | name | slug | description | aliases | source | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | UX/UI-дизайнер | ux-ui-designer | Проектирует пользовательский опыт и интерфейсы цифровых продуктов. | UI/UX дизайнер; UX designer; UI designer | renamed_from_design | Каноническая digital design-роль; инструменты и методы уходят в Skill |
| 2 | Продуктовый дизайнер | product-designer | Проектирует цифровой продукт целиком: сценарии, интерфейсы и пользовательскую ценность. | дизайнер продукта; product designer | from_design | Оставлен в Design, потому что доминирующий craft — дизайн |
| 3 | Графический дизайнер | graphic-designer | Создаёт визуальные материалы, айдентику и коммуникационную графику. | графдизайнер; graphic designer | from_design | Устойчивая visual role |
| 4 | Иллюстратор | illustrator | Создаёт иллюстрации и визуальные образы для продукта и контента. | illustrator | from_design | Самостоятельная visual craft specialization |
| 5 | Моушн-дизайнер | motion-designer | Делает анимированную графику, титры и motion-визуалы. | motion designer; motion graphics designer | from_design | Visual craft; не переносить в Production |
| 6 | Художник | artist | Создаёт художественные образы, визуальные концепты и авторские арт-материалы. | artist; concept artist | from_design | Пограничная, но полезная creative role для MVP |

### Звук и музыка (`audio-music`)

| order | name | slug | description | aliases | source | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Звукорежиссёр | sound-engineer | Отвечает за запись, обработку и техническое качество звука. | sound engineer; audio engineer | from_design | Роль уровня production, а не набор DAW-навыков |
| 2 | Саунд-дизайнер | sound-designer | Создаёт звуковые эффекты и аудиосреду проекта. | sound designer | added | Отдельный audio craft |
| 3 | Композитор | composer | Пишет музыку и музыкальные темы для проекта. | composer | added | Самостоятельная музыкальная specialization |
| 4 | Музыкальный продюсер | music-producer | Ведёт музыкальный production-процесс и собирает музыкальный результат. | music producer; битмейкер | added | Отличать от общего media producer |
| 5 | Музыкант-исполнитель | musician-performer | Исполняет вокальные или инструментальные партии. | музыкант; исполнитель | added | Конкретный инструмент — в Skill |

### Контент (`content`)

| order | name | slug | description | aliases | source | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Копирайтер | copywriter | Пишет тексты для продукта, коммуникации и публикаций. | copywriter | from_design | Чёткая текстовая role-label |
| 2 | Контент-редактор | content-editor | Редактирует, собирает и доводит контент до публикации. | editor; редактор; content editor | added | Роль уровня output/process, не просто навык грамотности |
| 3 | Сценарист | scriptwriter | Пишет сценарии и narrative-структуру для видео, подкастов и историй. | сторителлер; scriptwriter | renamed_from_design | Сохраняет исходную идею storyteller, но яснее для UX |
| 4 | Контент-креатор | content-creator | Создаёт контент-единицы для платформ и медиа-форматов. | creator; контент-мейкер | added | Делает контент, но не равен SMM-специалисту |

### Маркетинг и продвижение (`marketing`)

| order | name | slug | description | aliases | source | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Маркетолог | marketer | Отвечает за общую маркетинговую стратегию и продвижение проекта. | marketer; digital marketer | from_design | Полезная generalist-role для раннего MVP |
| 2 | SMM-специалист | smm-specialist | Ведёт соцсети, контент-план и коммуникацию с аудиторией в соцмедиа. | SMM manager; social media manager | renamed_from_design | Сохраняется как самостоятельная specialization |
| 3 | Performance-маркетолог | performance-marketer | Запускает и оптимизирует платные digital-кампании по метрикам эффективности. | performance marketer; PPC specialist; специалист по контекстной рекламе | renamed_from_design | “Контекстная реклама” уходит в alias и future skills |
| 4 | PR-менеджер | pr-manager | Ведёт внешние коммуникации, инфоповоды и связи с партнёрами/медиа. | PR specialist; public relations | added | Нужен, чтобы не сводить весь marketing только к paid и social |

### Разработка (`development`)

| order | name | slug | description | aliases | source | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Frontend-разработчик | frontend-developer | Разрабатывает клиентскую часть и интерфейсы продукта. | front developer; frontend developer | renamed_from_design | Канонический dev-role для UI delivery |
| 2 | Backend-разработчик | backend-developer | Разрабатывает серверную логику, API и интеграции. | back developer; backend developer | renamed_from_design | Ботовые и automation-сценарии лучше класть сюда через aliases/skills |
| 3 | Fullstack-разработчик | fullstack-developer | Закрывает и клиентскую, и серверную части в одной роли. | фулстек разработчик; full-stack developer | renamed_from_design | Рыночная самостоятельная роль |
| 4 | Мобильный разработчик | mobile-developer | Делает мобильные приложения и мобильный product delivery на iOS/Android/cross-platform. | React Native-разработчик; iOS developer; Android developer; mobile developer | renamed_from_design | Технологии и платформы остаются ниже уровня specialization |
| 5 | Разработчик игр | game-developer | Разрабатывает игровые механики, игровую логику и runtime. | геймдевелопер; game developer | renamed_from_design | Отдельный craft-domain внутри Development |
| 6 | Разработчик ПО | software-developer | Разрабатывает прикладные программы, утилиты, desktop-приложения, скрипты и программные инструменты вне узкой привязки к web, mobile или game development. | программист; software developer; application developer; desktop developer; прикладной разработчик | added | Нужен как широкая, но всё ещё человеко-понятная специализация для не-web разработки; конкретные языки, платформы и типы приложений уходят в Skill |

### Съёмки и продакшн (`production`)

| order | name | slug | description | aliases | source | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Продюсер | producer | Организует production-процесс, ресурсы, сроки и выпуск результата. | producer | from_design | Здесь это media/creative producer, а не product role |
| 2 | Режиссёр | director | Отвечает за постановку и режиссёрское видение проекта. | director | from_design | Чёткая production specialization |
| 3 | Видеооператор | videographer | Снимает видеоматериал и отвечает за визуальное capture-производство. | оператор; videographer; camera operator | added | Нужен для базового покрытия shoot-процессов |
| 4 | Монтажёр | video-editor | Собирает видеоматериал в финальный ролик или выпуск. | video editor; editor; монтажер | added | Отдельный post-production craft |
| 5 | Актёр | actor | Исполняет роль перед камерой или в постановке. | актриса; актёр театра и кино; actor | renamed_from_design | Одна каноническая запись, гендерные и уточняющие варианты — в aliases |

### Продукт (`product`)

| order | name | slug | description | aliases | source | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Менеджер продукта | product-manager | Определяет ценность продукта, приоритеты, roadmap и delivery-фокус. | продакт; product manager; product owner | added | Главная product specialization для MVP |
| 2 | Продуктовый аналитик | product-analyst | Анализирует продуктовые метрики, поведение пользователей и гипотезы роста. | product analyst | added | Стабильная product-role, не сводится к одному инструменту |
| 3 | UX-исследователь | ux-researcher | Проводит исследования пользователей и помогает product/design-решениям. | user researcher; researcher | added | В MVP логичнее в Product, потому что доминирует discovery-craft, а не визуальный дизайн |

## 5. Core Skill seed data

### Дизайн

| order | name | slug | type | description | aliases | relevant_fields | relevant_specializations | source | priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Figma | figma | tool | UI/UX, прототипы, дизайн-системы | фигма; figma | design, product | UX/UI-дизайнер; Продуктовый дизайнер | normalized_from_design | core | Главный design core tool |
| 2 | Adobe Photoshop | adobe-photoshop | tool | Растровая графика, композиты, подготовка визуалов | photoshop; фотошоп | design, content, production | Графический дизайнер; Художник | normalized_from_design | core | Официальное Adobe-название |
| 3 | Adobe Illustrator | adobe-illustrator | tool | Векторная графика и иллюстрация | illustrator; иллюстратор; илюстратор | design | Графический дизайнер; Иллюстратор | normalized_from_design | core | Нельзя путать с specialization `Иллюстратор` |
| 4 | Procreate | procreate | tool | Digital art и sketching workflow | procreate app | design | Иллюстратор; Художник | from_design | core | Сильный iPad-first art tool |
| 5 | Adobe After Effects | adobe-after-effects | tool | Моушн-графика и композитинг | after effects; ae | design, production | Моушн-дизайнер; Монтажёр | normalized_from_design | core | Нужен для motion-кластера |
| 6 | Miro | miro | tool | Совместная доска для discovery и planning | миро | design, product, marketing | UX/UI-дизайнер; Менеджер продукта | from_design | core | Cross-field core tool |
| 7 | Maze | maze | tool | UX-research, prototype testing, surveys | maze research | design, product | UX-исследователь; UX/UI-дизайнер | from_design | core | Core research/testing tool |
| 8 | Проектирование сложных интерфейсов | complex-interface-design | domain | Работа со сложной экранной логикой и состояниями | complex interface design | design | UX/UI-дизайнер; Продуктовый дизайнер | normalized_from_design | core | Нормализованная версия “сложные интерфейсы” |
| 9 | Вайрфреймы | wireframing | method | Каркасирование экранов и flows | wireframing; wireframes | design, product | UX/UI-дизайнер; Продуктовый дизайнер | added | core | Базовый design/product method |
| 10 | Интерактивное прототипирование | interactive-prototyping | method | Кликабельные и поведенческие прототипы | interactive prototyping; prototyping | design, product | UX/UI-дизайнер; Продуктовый дизайнер | added | core | Сильный мост между design и research |
| 11 | Адаптивный дизайн | responsive-design | method | Адаптация интерфейсов под разные экраны | responsive design; adaptive design; адаптивы | design, development | UX/UI-дизайнер; Frontend-разработчик | normalized_from_design | core | Нормализованная версия “адаптивы” |
| 12 | Дизайн-системы | design-systems | method | Компоненты, паттерны, UI consistency | design systems; design system | design, development | UX/UI-дизайнер; Продуктовый дизайнер | added | core | Полезно и для handoff |
| 13 | Информационная архитектура | information-architecture | method | Структура контента и навигации | information architecture; ia | design, content, product | UX/UI-дизайнер; UX-исследователь | added | core | Особенно важно для сложных интерфейсов |
| 14 | Пользовательские сценарии | user-flows | method | Сценарии и переходы пользователя | user flows; user journeys | design, product | UX/UI-дизайнер; Продуктовый дизайнер | added | core | Уточняет логику продукта |
| 15 | UX-исследования | ux-research | method | Исследование поведения и потребностей пользователей | ux research | design, product | UX/UI-дизайнер; UX-исследователь | added | core | Не specialization, а конкретный research craft |
| 16 | Типографика | typography | domain | Работа с шрифтом и иерархией текста | typography | design, content | Графический дизайнер; Копирайтер | added | core | Нужна для digital и brand-работ |
| 17 | Айдентика | visual-identity | domain | Айдентика, визуальный язык бренда | visual identity; brand identity | design, marketing | Графический дизайнер; Маркетолог | added | core | Хороший мост между design и marketing |
| 18 | Иллюстрация | illustration | domain | Создание иллюстративных визуалов | illustration | design | Иллюстратор; Художник | added | core | Craft-skill, а не роль |
| 19 | Моушн-графика | motion-graphics | domain | Анимированная графика и титры | motion graphics; motion design | design, production | Моушн-дизайнер; Монтажёр | added | core | Лучше как skill, не specialization |

### Звук и музыка

| order | name | slug | type | description | aliases | relevant_fields | relevant_specializations | source | priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Запись звука | sound-recording | domain | Запись голоса, инструментов и локационного звука | sound recording; audio recording | audio-music, production | Звукорежиссёр | added | core | Базовый audio production skill |
| 2 | Аудиомонтаж | audio-editing | domain | Резка, чистка, сборка аудиоматериала | audio editing; audio edit | audio-music | Звукорежиссёр; Саунд-дизайнер | added | core | Полезно и для подкастов |
| 3 | Сведение | mixing | domain | Сведение многодорожечного аудио | mixing; микс | audio-music | Звукорежиссёр; Музыкальный продюсер | added | core | Core audio craft |
| 4 | Мастеринг | mastering | domain | Финальная обработка аудиотрека | mastering | audio-music | Звукорежиссёр; Музыкальный продюсер | added | core | Отдельный stage skill |
| 5 | Саунд-дизайн | sound-design | domain | Создание звуковых эффектов и audio atmosphere | sound design | audio-music, development | Саунд-дизайнер; Разработчик игр | added | core | Cross-field навык |
| 6 | Композиция | music-composition | domain | Написание музыкальных тем и мелодий | music composition; composition | audio-music | Композитор; Музыкальный продюсер | added | core | Core skill для composer |
| 7 | Аранжировка | arrangement | domain | Аранжировка и сборка музыкальной структуры | arrangement | audio-music | Композитор; Музыкальный продюсер | added | core | Комплементарен композиции |
| 8 | Ableton Live | ableton-live | tool | DAW для музыки, sound design и live production | ableton | audio-music | Композитор; Музыкальный продюсер | added | core | Day-one music tool |
| 9 | Logic Pro | logic-pro | tool | DAW для записи, композиции и продакшна | logic; logic pro x | audio-music | Композитор; Музыкальный продюсер; Звукорежиссёр | added | core | Полезен в широком audio-кластере |
| 10 | Pro Tools | pro-tools | tool | Профессиональный audio production tool | protools | audio-music | Звукорежиссёр; Саунд-дизайнер | added | core | Сильный engineering-tool |
| 11 | Инструментальное исполнение | instrument-performance | domain | Исполнение инструментальных партий | instrument performance; instrumental performance | audio-music | Музыкант-исполнитель | added | core | Сохраняет инструментальную широту без дробления по каждому инструменту |
| 12 | Вокальное исполнение | vocal-performance | domain | Исполнение вокальных партий | vocal performance; vocals; singing | audio-music, production | Музыкант-исполнитель; Актёр | added | core | Нужен для vocalist / voice work |

### Контент

| order | name | slug | type | description | aliases | relevant_fields | relevant_specializations | source | priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Копирайтинг | copywriting | domain | Написание прикладных и маркетинговых текстов | copywriting | content, marketing | Копирайтер; Маркетолог | added | core | Базовый content skill |
| 2 | Редактура | editing | domain | Редактирование и улучшение текста | editing | content | Контент-редактор; Копирайтер | added | core | Не путать с video editing |
| 3 | Корректура | proofreading | domain | Вычитка языка, орфографии и чистоты текста | proofreading | content | Контент-редактор; Копирайтер | added | core | Полезно для редакторских ролей |
| 4 | Сценарное письмо | scriptwriting | domain | Написание сценариев и narrative structure | scriptwriting | content, production | Сценарист; Контент-креатор | added | core | Core script skill |
| 5 | Сторителлинг | storytelling | domain | Построение истории, драматургии и narrative hook | storytelling | content, marketing | Сценарист; Копирайтер; PR-менеджер | added | core | Стоит держать как skill |
| 6 | Тональность коммуникации | tone-of-voice | method | Единый стиль и голос коммуникации | tone of voice; tov | content, marketing | Копирайтер; Контент-редактор | added | core | Часто нужен брендам и продуктам |
| 7 | Контент-планирование | content-planning | method | Планирование контентных единиц и тем | content planning | content, marketing | Контент-редактор; Контент-креатор; SMM-специалист | added | core | Важный production/process layer |
| 8 | Редакционное планирование | editorial-planning | method | Планирование редакционного цикла и выпусков | editorial planning; editorial calendar | content | Контент-редактор | added | core | Нужен редакторской роли |
| 9 | SEO-копирайтинг | seo-copywriting | domain | Тексты с учётом поискового спроса | seo copywriting; seo writing | content, marketing | Копирайтер; Маркетолог | added | core | Не дублирует общий SEO |
| 10 | Лонгриды | long-form-content | format | Длинные тексты, статьи, лонгриды | long-form content; longread | content | Копирайтер; Контент-редактор | added | core | Формат, а не роль |
| 11 | Короткий контент | short-form-content | format | Короткие посты, captions, cards, snippets | short-form content; short content | content, marketing, production | Контент-креатор; SMM-специалист | added | core | Особенно полезно для social/video контента |

### Маркетинг и продвижение

| order | name | slug | type | description | aliases | relevant_fields | relevant_specializations | source | priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Контент-маркетинг | content-marketing | domain | Маркетинг через контент и контентные воронки | content marketing | marketing, content | Маркетолог; SMM-специалист | added | core | Хороший core мост между content и marketing |
| 2 | SMM | social-media-marketing | domain | Продвижение через соцмедиа-каналы | social media marketing; smm | marketing | SMM-специалист; Маркетолог | added | core | SMM как skill допустим, но не вместо specialization |
| 3 | Комьюнити-менеджмент | community-management | domain | Работа с сообществом и вовлечением аудитории | community management; управление сообществом | marketing | SMM-специалист; PR-менеджер | added | core | Не сводится только к posting |
| 4 | Performance-маркетинг | performance-marketing | domain | Управление paid acquisition по метрикам | performance marketing; performance | marketing | Performance-маркетолог; Маркетолог | added | core | Person-shaped specialization выше, skill — ниже |
| 5 | Google Ads | google-ads | platform | Платформа paid search/display кампаний | adwords | marketing | Performance-маркетолог | added | core | Канонический paid ads skill |
| 6 | Meta Ads | meta-ads | platform | Платформа платной рекламы Meta | facebook ads; instagram ads | marketing | Performance-маркетолог; SMM-специалист | added | core | Оставляет платформу на уровне skill |
| 7 | SEO | seo | domain | Поисковая оптимизация и search visibility | search engine optimization | marketing, content | Маркетолог; Копирайтер | added | core | Общий SEO, не только контент |
| 8 | Email-маркетинг | email-marketing | domain | Email-кампании, рассылки и nurture flow | email marketing; email campaigns | marketing | Маркетолог; PR-менеджер | added | core | Полезно для B2B/B2C MVP |
| 9 | Веб-аналитика | web-analytics | domain | Аналитика сайтов, страниц и campaign traffic | web analytics; website analytics | marketing, product | Маркетолог; Performance-маркетолог | added | core | Нужен для фильтров и маркетинг-аналитики |
| 10 | UTM-разметка | utm-tagging | method | Разметка ссылок и атрибуция трафика | utm tagging; utm parameters | marketing, product | Performance-маркетолог; Маркетолог | added | core | Очень прикладной seed skill |
| 11 | A/B testing | ab-testing | method | Эксперименты с креативами, страницами и flows | split testing | marketing, product | Performance-маркетолог; Продуктовый аналитик | added | core | Полезен и для marketing, и для product |
| 12 | Планирование кампаний | campaign-planning | method | Планирование рекламных и коммуникационных кампаний | campaign planning; campaign strategy | marketing, production | Маркетолог; PR-менеджер | added | core | Даёт process-layer выше платформ |
| 13 | PR-коммуникации | pr-communications | domain | Внешние коммуникации и инфоповоды | pr communications; public relations | marketing | PR-менеджер | added | core | Core PR craft |
| 14 | Работа со СМИ | media-outreach | domain | Коммуникация со СМИ, партнёрами и паблисити | media outreach; press outreach | marketing | PR-менеджер | added | core | Это именно skill, не specialization |

### Разработка

| order | name | slug | type | description | aliases | relevant_fields | relevant_specializations | source | priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | HTML | html | technology | Базовая разметка web-интерфейсов | hypertext markup language | development | Frontend-разработчик; Fullstack-разработчик | added | core | Day-one frontend base |
| 2 | CSS | css | technology | Стилизация и layout web-интерфейсов | cascading style sheets | development | Frontend-разработчик; Fullstack-разработчик | added | core | Day-one frontend base |
| 3 | JavaScript | javascript | technology | Основной язык web-логики и scripting | js | development | Frontend-разработчик; Fullstack-разработчик | added | core | Широкий базовый tech-skill |
| 4 | TypeScript | typescript | technology | Typed superset для modern web/mobile dev | ts | development | Frontend-разработчик; Fullstack-разработчик | added | core | Полезен и для React Native |
| 5 | React | react | technology | UI library для web-интерфейсов | reactjs | development | Frontend-разработчик; Fullstack-разработчик | added | core | Практичный MVP core |
| 6 | REST API | rest-api | technology | Проектирование и потребление HTTP API | restful api | development, product | Backend-разработчик; Fullstack-разработчик | added | core | Явный пример валидного skill |
| 7 | Интеграция API | api-integration | technology | Интеграция внешних и внутренних API | api integration; integrations | development | Backend-разработчик; Разработчик ПО | added | core | Важен для software/app workflows |
| 8 | Python | python | technology | Язык общего назначения для backend и automation | py | development | Backend-разработчик; Разработчик ПО | added | core | Хороший MVP base language |
| 9 | Django | django | technology | Python web framework | django framework | development | Backend-разработчик; Fullstack-разработчик | added | core | Валидный конкретный framework-skill |
| 10 | Node.js | node-js | technology | JavaScript runtime для backend и tooling | node | development | Backend-разработчик; Fullstack-разработчик | added | core | Полезен для JS stack |
| 11 | PostgreSQL | postgresql | technology | Реляционная БД для приложений и сервисов | postgres | development | Backend-разработчик; Разработчик ПО | added | core | Практичный database seed |
| 12 | SQL | sql | technology | Язык запросов и работы с реляционными данными | structured query language | development, product | Backend-разработчик; Продуктовый аналитик | added | core | Cross-field analytic + dev skill |
| 13 | Git | git | technology | Контроль версий и совместная работа с кодом | git version control | development | Frontend-разработчик; Backend-разработчик | added | core | Обязательная база для dev roles |
| 14 | Тестирование | testing | method | Проверка кода и сценариев работы ПО | testing; qa testing | development | Frontend-разработчик; Backend-разработчик; Разработчик ПО | added | core | Не specialization QA, а общий engineering skill |
| 15 | CI/CD | ci-cd | method | Сборка, деплой и delivery pipeline | continuous integration; continuous delivery | development | Backend-разработчик; Fullstack-разработчик | added | core | Базовый DevOps layer |
| 16 | Docker | docker | technology | Контейнеризация приложений и окружений | docker containers | development | Backend-разработчик; Разработчик ПО | added | core | Распространённый infra skill |
| 17 | Скриптовая автоматизация | automation-scripting | domain | Скрипты, автоматизация и internal tooling | automation scripting; scripting | development | Backend-разработчик; Разработчик ПО | added | core | Особенно полезен для software developer |
| 18 | Разработка ботов | bot-development | domain | Создание ботов и conversational automation | bot development; chatbots; bots | development | Backend-разработчик; Разработчик ПО | added | core | Оставить skill-кластером, не specialization |
| 19 | React Native | react-native | technology | Cross-platform mobile framework | reactnative | development | Мобильный разработчик | added | core | Каноническое skill-имя вместо specialization |
| 20 | Unity | unity | technology | Игровой движок и runtime environment | unity3d | development | Разработчик игр | added | core | Mainstream game-tech skill |
| 21 | Unreal Engine | unreal-engine | technology | Игровой движок для real-time 3D | unreal | development | Разработчик игр | added | core | Дополняет Unity |
| 22 | Разработка desktop-приложений | desktop-application-development | domain | Разработка desktop и standalone software | desktop application development; app development; desktop dev | development | Разработчик ПО | added | core | Важный skill для software-developer branch |
| 23 | Архитектура ПО | software-architecture | method | Архитектурное проектирование приложений и сервисов | software architecture; architecture design | development | Backend-разработчик; Fullstack-разработчик; Разработчик ПО | added | core | Держит software layer выше конкретных языков |
| 24 | Проектирование баз данных | database-design | domain | Проектирование структуры и связей данных | database design; schema design | development | Backend-разработчик; Разработчик ПО | added | core | Нужен для data-heavy roles |

### Съёмки и продакшн

| order | name | slug | type | description | aliases | relevant_fields | relevant_specializations | source | priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Режиссура | directing | domain | Постановка сцены, кадра и экшена | directing | production | Режиссёр | added | core | Core director skill |
| 2 | Планирование кадров | shot-planning | method | Планирование кадров и съёмочных блоков | shot planning; shot list | production | Режиссёр; Видеооператор | added | core | Полезно до съёмки и на площадке |
| 3 | Раскадровка | storyboarding | method | Визуальная раскладка сцен и переходов | storyboarding; storyboard | production, design, content | Режиссёр; Сценарист; Моушн-дизайнер | added | core | Хороший cross-field skill |
| 4 | Операторская работа | camera-operation | domain | Работа с камерой и съёмочной техникой | camera operation; camera work | production | Видеооператор | added | core | Прямой craft skill |
| 5 | Постановка света | lighting-setup | domain | Постановка света для кадра и сцены | lighting setup; lighting | production | Видеооператор | added | core | Важен для video quality |
| 6 | Видеомонтаж | video-editing | domain | Монтаж исходного материала в итоговый ролик | video editing; editing video; монтаж | production | Монтажёр; Контент-креатор | added | core | Не путать с text editing |
| 7 | Цветокоррекция | color-grading | domain | Цветокоррекция и стилизация видео | color grading; grading | production | Монтажёр; Видеооператор | added | core | Постпродакшн core skill |
| 8 | Adobe Premiere Pro | adobe-premiere-pro | tool | NLE tool для монтажа и сборки видео | premiere; premiere pro | production | Монтажёр; Видеооператор | added | core | Практичный day-one video tool |
| 9 | DaVinci Resolve | davinci-resolve | tool | Монтаж, grading и post-production | resolve | production | Монтажёр; Видеооператор | added | core | Сильный постпродакшн tool |
| 10 | Управление продакшном | production-management | method | Организация сроков, процессов и ресурсов съёмки | production management; production planning | production | Продюсер; Режиссёр | added | core | Закрывает продюсерский management-layer |
| 11 | Создание Reels | reels-production | format | Короткое вертикальное видео под social formats | reels production; short video; reels | production, content, marketing | Контент-креатор; Монтажёр; SMM-специалист | added | core | Полезный MVP format-skill |
| 12 | Работа в кадре | on-camera-performance | domain | Работа перед камерой, пластика и подача | on-camera performance; camera acting | production | Актёр | added | core | Better than creating separate acting subroles |

### Продукт

| order | name | slug | type | description | aliases | relevant_fields | relevant_specializations | source | priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Продуктовое discovery | product-discovery | method | Поиск проблем, ценности и решений продукта | product discovery; discovery | product | Менеджер продукта; UX-исследователь | added | core | Core PM/UXR layer |
| 2 | Планирование roadmap | roadmapping | method | Формирование продуктового roadmap | roadmapping; roadmap | product | Менеджер продукта | added | core | Нужен PM-роли |
| 3 | Управление backlog | backlog-management | method | Работа с backlog и приоритезацией задач | backlog management; backlog | product | Менеджер продукта | added | core | Прикладной PM-skill |
| 4 | JTBD | jtbd | method | Jobs To Be Done framework | jobs to be done | product | Менеджер продукта; UX-исследователь | added | core | Уместен как method-skill |
| 5 | Пользовательские истории | user-stories | method | Формулировка требований через сценарий пользователя | user stories; user story | product, development | Менеджер продукта; Frontend-разработчик | added | core | Хороший мост в delivery |
| 6 | Проверка гипотез | hypothesis-testing | method | Постановка и проверка продуктовых гипотез | hypothesis testing; experiment design | product, marketing | Менеджер продукта; Продуктовый аналитик | added | core | Полезен и для growth-like задач |
| 7 | Продуктовая аналитика | product-analytics | domain | Анализ поведения пользователей и продукта | product analytics; analytics | product | Продуктовый аналитик; Менеджер продукта | added | core | Отдельный product craft |
| 8 | Событийная аналитика | event-tracking | domain | Событийная схема и аналитическая instrumentation | event tracking; tracking plan | product, marketing | Продуктовый аналитик; Менеджер продукта | added | core | Нужен для аналитической связности |
| 9 | Анализ метрик | metrics-analysis | domain | Работа с метриками, воронками и интерпретацией данных | metrics analysis; metrics | product | Продуктовый аналитик; Менеджер продукта | added | core | Более широкий навык, чем только SQL |
| 10 | Пользовательские интервью | user-interviews | method | Интервью с пользователями и stakeholder discovery | user interviews; interviews | product, design | UX-исследователь; Менеджер продукта | added | core | Core UXR skill |
| 11 | Юзабилити-тестирование | usability-testing | method | Проверка интерфейса на понятность и проблемы | usability testing; usability | product, design | UX-исследователь; UX/UI-дизайнер | added | core | Полезно и для design, и для product |
| 12 | Синтез исследований | research-synthesis | method | Сводка, clustering и выводы по исследованиям | research synthesis; synthesis | product, design | UX-исследователь; Продуктовый аналитик | added | core | Делает research пригодным к решениям |

## 6. Optional and future Skill candidates

### Optional second-wave skills

| name | slug | priority | reason | when_to_add |
| --- | --- | --- | --- | --- |
| CorelDRAW | coreldraw | optional | Валиден, но Photoshop + Illustrator уже закрывают базовый graphic core | Когда появится устойчивый sign/print/illustration спрос |
| Affinity Designer | affinity-designer | optional | Полезный, но не must-have для MVP | Когда станет заметен спрос на non-Adobe stack |
| Sketch | sketch | optional | Валиден, но не обязателен при наличии Figma | Когда user-generated tail начнёт часто повторяться |
| Blender | blender | optional | Полезен для 3D, но не базовый для всего MVP | Когда вырастет доля 3D/motion/game проектов |
| Cinema 4D | cinema-4d | optional | Узкий pro 3D/motion tool | Когда motion/3D станет заметным use case |
| Spline | spline | optional | Нишевый интерактивный 3D tool | Когда появится спрос на web-based 3D/interactive design |
| Framer | framer | optional | No-code / site publishing edge-skill | Когда будет достаточно no-code product/design проектов |
| Webflow | webflow | optional | Важный web platform skill, но не day-one must-have | Когда команды станут явно искать no-code/web builders |
| Zeplin | zeplin | optional | Узкий design delivery tool | Когда handoff/distribution станет частым сценарием |
| Lookback | lookback | optional | Полезный research tool, но Maze покрывает базовый research/testing блок | Когда исследования станут глубже и регулярнее |
| Instagram | instagram | optional | Полезная platform specificity, но не обязательна в day-one seed | Когда появится много social-first контентных ролей |
| TikTok | tiktok | optional | Такой же platform-specific хвост | Когда short-form social cases станут массовыми |
| Customer journey mapping | customer-journey-mapping | optional | Сильный method-skill, но не критичен для старта | Когда product/marketing flows станут сложнее |
| Survey design | survey-design | optional | Нужен исследовательским ролям, но не всем | Когда UX-research активность станет заметной |
| iOS | ios | optional | Platform-specific mobile layer | Когда пользователи начнут массово указывать iOS отдельно |
| Android | android | optional | Platform-specific mobile layer | Когда пользователи начнут массово указывать Android отдельно |
| Swift | swift | optional | Важный mobile tech, но не обязателен в day-one системном справочнике | Когда станет видно повторяемость нативного iOS спроса |
| Kotlin | kotlin | optional | Аналогично Swift | Когда станет видно повторяемость нативного Android спроса |
| .NET | dotnet | optional | Полезен для `Разработчик ПО`, но не нужен как day-one core для всех | Когда software/application branch станет плотнее |
| Electron | electron | optional | Полезен для desktop apps, но слишком нишевый для старта | Когда станет заметен спрос на desktop wrappers |

### Future skills

| name | slug | priority | reason | when_to_add |
| --- | --- | --- | --- | --- |
| Go | go | future | Полезный backend/software язык, но слишком детализирует dev-core на старте | Когда аналитика спроса покажет стабильный повтор |
| Godot | godot | future | Валидный game-tech tool, но не базовый при наличии Unity/Unreal | Когда появится заметный инди-game кластер |
| Influencer marketing | influencer-marketing | future | Нужен не всем маркетинговым кейсам MVP | Когда платформа увидит creator/influencer-led промо |
| Creative coding | creative-coding | future | Интересный гибрид design+dev, но слишком нишевый для day-one seed | Когда появятся явные experimental/art-tech проекты |
| Mixpanel | mixpanel | future | Валидный analytics tool, но на старте достаточно generic product analytics + SQL | Когда станет виден устойчивый инструментальный спрос |

## 7. Specialization to recommended Skill mapping

### Дизайн

| specialization | core_skills | optional_skills |
| --- | --- | --- |
| UX/UI-дизайнер | Figma; Проектирование сложных интерфейсов; Вайрфреймы; Интерактивное прототипирование; Адаптивный дизайн; Дизайн-системы; Информационная архитектура; Пользовательские сценарии; UX-исследования | Sketch; Framer; Zeplin |
| Продуктовый дизайнер | Figma; Вайрфреймы; Интерактивное прототипирование; Дизайн-системы; Пользовательские сценарии; UX-исследования; Информационная архитектура; Miro; Maze | Framer; Webflow; Sketch |
| Графический дизайнер | Adobe Photoshop; Adobe Illustrator; Типографика; Айдентика; Иллюстрация; Figma | CorelDRAW; Affinity Designer |
| Иллюстратор | Иллюстрация; Adobe Illustrator; Procreate; Adobe Photoshop; Типографика | Affinity Designer; Blender |
| Моушн-дизайнер | Adobe After Effects; Моушн-графика; Раскадровка; Adobe Photoshop; Figma | Blender; Cinema 4D; Spline |
| Художник | Иллюстрация; Adobe Photoshop; Procreate; Раскадровка; Моушн-графика | Blender; Cinema 4D |

### Звук и музыка

| specialization | core_skills | optional_skills |
| --- | --- | --- |
| Звукорежиссёр | Запись звука; Аудиомонтаж; Сведение; Мастеринг; Pro Tools; Logic Pro |  |
| Саунд-дизайнер | Саунд-дизайн; Аудиомонтаж; Pro Tools; Ableton Live; Logic Pro |  |
| Композитор | Композиция; Аранжировка; Ableton Live; Logic Pro; Сторителлинг | Pro Tools |
| Музыкальный продюсер | Композиция; Аранжировка; Сведение; Мастеринг; Ableton Live; Logic Pro |  |
| Музыкант-исполнитель | Инструментальное исполнение; Вокальное исполнение; Запись звука; Аранжировка; Logic Pro | Ableton Live |

### Контент

| specialization | core_skills | optional_skills |
| --- | --- | --- |
| Копирайтер | Копирайтинг; Тональность коммуникации; Сторителлинг; SEO-копирайтинг; Лонгриды; Редактура; Корректура | Контент-маркетинг |
| Контент-редактор | Редактура; Корректура; Редакционное планирование; Контент-планирование; Тональность коммуникации; Лонгриды; Сторителлинг | SEO-копирайтинг |
| Сценарист | Сценарное письмо; Сторителлинг; Раскадровка; Тональность коммуникации; Лонгриды; Короткий контент |  |
| Контент-креатор | Контент-планирование; Короткий контент; Сторителлинг; Сценарное письмо; Видеомонтаж; Создание Reels; Копирайтинг | Instagram; TikTok |

### Маркетинг и продвижение

| specialization | core_skills | optional_skills |
| --- | --- | --- |
| Маркетолог | Контент-маркетинг; Планирование кампаний; SEO; Веб-аналитика; UTM-разметка; Email-маркетинг; A/B testing; Айдентика | Customer journey mapping |
| SMM-специалист | SMM; Комьюнити-менеджмент; Контент-планирование; Короткий контент; Создание Reels; Meta Ads; Планирование кампаний | Instagram; TikTok |
| Performance-маркетолог | Performance-маркетинг; Google Ads; Meta Ads; UTM-разметка; Веб-аналитика; A/B testing; Анализ метрик | Email-маркетинг |
| PR-менеджер | PR-коммуникации; Работа со СМИ; Сторителлинг; Планирование кампаний; Тональность коммуникации; Контент-маркетинг; Копирайтинг; Комьюнити-менеджмент | Email-маркетинг |

### Разработка

| specialization | core_skills | optional_skills |
| --- | --- | --- |
| Frontend-разработчик | HTML; CSS; JavaScript; TypeScript; React; Адаптивный дизайн; Тестирование; Git; Дизайн-системы; REST API | Framer; Zeplin |
| Backend-разработчик | Python; Django; Node.js; REST API; Интеграция API; PostgreSQL; SQL; Docker; CI/CD; Проектирование баз данных | Go |
| Fullstack-разработчик | HTML; CSS; JavaScript; TypeScript; React; REST API; Node.js; PostgreSQL; Git; Тестирование | Docker |
| Мобильный разработчик | React Native; TypeScript; REST API; Интеграция API; Git; Тестирование | iOS; Android; Swift; Kotlin |
| Разработчик игр | Unity; Unreal Engine; Git; Саунд-дизайн; Раскадровка | Blender; Godot |
| Разработчик ПО | Python; SQL; Git; Тестирование; Скриптовая автоматизация; Разработка desktop-приложений; Интеграция API; Архитектура ПО; Проектирование баз данных | .NET; Electron |

### Съёмки и продакшн

| specialization | core_skills | optional_skills |
| --- | --- | --- |
| Продюсер | Управление продакшном; Планирование кампаний; Раскадровка; Создание Reels; Miro |  |
| Режиссёр | Режиссура; Планирование кадров; Раскадровка; Сценарное письмо; Управление продакшном; Цветокоррекция |  |
| Видеооператор | Операторская работа; Постановка света; Планирование кадров; Цветокоррекция; Adobe Premiere Pro; DaVinci Resolve; Раскадровка |  |
| Монтажёр | Видеомонтаж; Adobe Premiere Pro; DaVinci Resolve; Цветокоррекция; Создание Reels; Моушн-графика; Adobe After Effects; Короткий контент |  |
| Актёр | Работа в кадре; Сторителлинг; Сценарное письмо; Вокальное исполнение; Создание Reels |  |

### Продукт

| specialization | core_skills | optional_skills |
| --- | --- | --- |
| Менеджер продукта | Продуктовое discovery; Планирование roadmap; Управление backlog; Пользовательские истории; Проверка гипотез; JTBD; Пользовательские интервью; Продуктовая аналитика; Miro | Customer journey mapping |
| Продуктовый аналитик | Продуктовая аналитика; Событийная аналитика; Анализ метрик; SQL; Веб-аналитика; Проверка гипотез; A/B testing; Синтез исследований | Mixpanel |
| UX-исследователь | UX-исследования; Пользовательские интервью; Юзабилити-тестирование; Синтез исследований; Maze; Miro; Информационная архитектура | Lookback; Survey design |

## 8. Alias and deduplication rules

### 8.1 Field aliases

| alias | canonical_field |
| --- | --- |
| Контент и тексты | Контент |
| Управление продуктом | Продукт |
| Креативное управление | Не canonical Field; распределять по доминирующей Specialization |

### 8.2 Specialization aliases

| alias | canonical_specialization |
| --- | --- |
| front developer | Frontend-разработчик |
| front разработчик | Frontend-разработчик |
| back developer | Backend-разработчик |
| back разработчик | Backend-разработчик |
| фулстек разработчик | Fullstack-разработчик |
| full-stack developer | Fullstack-разработчик |
| React Native-разработчик | Мобильный разработчик |
| iOS developer | Мобильный разработчик |
| Android developer | Мобильный разработчик |
| геймдевелопер | Разработчик игр |
| game developer | Разработчик игр |
| программист | Разработчик ПО |
| software developer | Разработчик ПО |
| application developer | Разработчик ПО |
| desktop developer | Разработчик ПО |
| прикладной разработчик | Разработчик ПО |
| разработчик ботов | Backend-разработчик |
| контекстная реклама | Performance-маркетолог |
| PPC specialist | Performance-маркетолог |
| актриса | Актёр |
| актёр театра и кино | Актёр |
| storyteller | Сценарист |
| сторителлер | Сценарист |
| UI designer | UX/UI-дизайнер |
| UX designer | UX/UI-дизайнер |
| product owner | Менеджер продукта |
| продакт | Менеджер продукта |

### 8.3 Skill aliases and deduplication

| input_variant | canonical_skill | rule |
| --- | --- | --- |
| Figma / figma / Фигма | Figma | Нормализовать case-insensitive; кириллическую форму хранить как alias. |
| Photoshop / photoshop / фотошоп | Adobe Photoshop | Разговорные и сокращённые формы не создавать отдельными Skill. |
| Illustrator / illustrator / иллюстратор / илюстратор | Adobe Illustrator | Если речь об инструменте — `Adobe Illustrator`; если о роли — это Specialization `Иллюстратор`. |
| CorelDRAW / corel draw / корлдро | CorelDRAW | Нормализовать пробелы, регистр и кириллические варианты. |
| React Native / ReactNative / react-native | React Native | Использовать один canonical Skill со slug `react-native`. |
| iOS / IOS / ios | iOS | Сохранять точный platform case в canonical display-name. |
| Backend / backend / back | Не Skill | Это alias к Specialization `Backend-разработчик`, а не canonical Skill. |
| wireframing / wireframes | Вайрфреймы | Generic English skills переводить в русский canonical name, английский вариант хранить в aliases. |
| shot planning | Планирование кадров | Generic method-skill хранить по-русски; английский вариант — alias. |
| research synthesis | Синтез исследований | Generic method-skill хранить по-русски; английский вариант — alias. |
| пользовательский ввод совпал с existing alias | Соответствующий canonical Skill | Не создавать новый canonical record; связывать с существующим навыком. |
| brand + version suffix | Canonical brand/product name без версии | В MVP не добавлять версии продукта, если версия не меняет смысл навыка. |

## 9. Excluded and postponed items

### 9.1 Not Specialization

| item | reason | target |
| --- | --- | --- |
| разработка | Слишком общая формулировка, не работает как specialization для матчинга | удалить |
| AI-дизайнер | Скорее способ работы, tooling-stack или нишевый подвид нескольких design-ролей | в Skill / future version |
| разработчик ботов | Слишком узкий backend-subtype; дробит matching pool | alias или Skill под `Backend-разработчик` |
| развработка Recat Native для IOS Android | Смесь опечатки, платформ и framework-level формулировки | alias под `Мобильный разработчик`; технологии — в Skill |
| актриса | Гендерный дубль | alias под `Актёр` |
| актёр театра и кино | Уточняющий дубль более широкой роли | alias под `Актёр` |
| контекстная реклама | Канал/механика, а не удобный person-shaped label | alias/Skill под `Performance-маркетолог` |
| стилист | Для MVP слишком нишевая creative role | future version |
| дублирующий `продуктовый дизайнер` | Полный дубль | удалить как дубль |

### 9.2 Not Skill

| item | reason | target |
| --- | --- | --- |
| UX/UI-дизайнер | Это specialization, а не skill | specialization |
| Backend-разработчик | Это specialization, а не skill | specialization |
| SMM-специалист | Это specialization, а не skill | specialization |
| Звукорежиссёр | Это specialization, а не skill | specialization |
| Продюсер | Это specialization, а не skill | specialization |
| Дизайн | Это уровень Field, слишком общий | удалить |
| Разработка | Это уровень Field, слишком общий | удалить |
| Контент | Это уровень Field, слишком общий | удалить |
| креативность | Soft skill слишком расплывчатый для core seed | удалить |
| ответственность | Soft skill, не помогает filters/suggestions | удалить |
| коммуникабельность | Soft skill, не годится как main canonical Skill | удалить |
| Иллюстратор | Двусмысленно: это specialization; как tool нужно `Adobe Illustrator` | specialization или alias к tool |
| React Native-разработчик | Это role-formulation, а не skill | specialization alias + skill `React Native` |
| AI-дизайнер | Не skill и не day-one specialization в этой задаче | description / future |

## 10. Validation checklist

- [ ] 7 Field.
- [ ] Все Field имеют unique slug.
- [ ] Все Field имеют `is_featured = true`.
- [ ] 33 Specialization.
- [ ] Каждая Specialization имеет существующий Field.
- [ ] Все Specialization имеют unique slug.
- [ ] 104 core Skill.
- [ ] 20 optional Skill.
- [ ] 5 future Skill.
- [ ] Все Skill имеют unique slug.
- [ ] Skill не дублируют Field.
- [ ] Skill не дублируют Specialization.
- [ ] Aliases не создаются как отдельные canonical records.
- [ ] Mapping Specialization -> Skill использует только существующие canonical Skill names или optional/future candidates.
- [ ] Нет внешних citations в `seed_reference.md`.
- [ ] Нет research/changelog/design-communication blocks.

## 11. Notes for implementation

На следующем этапе этот reference можно преобразовать в `seed_data.yml` или `seed_data.json` и использовать как основу для idempotent management command. В качестве ключа для `update_or_create` следует использовать стабильный `slug`. Aliases стоит обрабатывать отдельно, если в модели есть поле или таблица для aliases. Если aliases пока не поддерживаются моделью, их нужно оставить в reference-документе для будущей нормализации, поиска и ручной модерации пользовательского ввода.
