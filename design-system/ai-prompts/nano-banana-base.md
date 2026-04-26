---
name: Nano Banana 2 — базовые промпты
description: Готовые шаблоны промптов для генерации изображений в фирменном стиле
type: reference
tool: nano-banana-2
---

# 🍌 Nano Banana 2 — промпт-библиотека FBA

> Google Gemini image generation. Используем для фирменных визуалов.

---

## 🎨 Базовый каркас промпта

Для сохранения единого стиля **каждый промпт** содержит:

```
[СЦЕНА], [РАКУРС], [ОСВЕЩЕНИЕ], [НАСТРОЕНИЕ], 
[ЦВЕТОВАЯ ПАЛИТРА: dark graphite #1A1A1A, japanese red accent #E30613, ochra #C08C4B], 
[СТИЛЬ: realistic photography, moody cinematic, high contrast], 
[БЕЗ: no text overlays, no stock photo feel, no clichés]
```

---

## 🍽️ Шаблон 1: Обложка поста про деньги / маржу

```
Professional restaurant kitchen countertop at dusk, 
financial spreadsheet on tablet next to prep bowls of fresh ingredients, 
calculator with sushi plate in background, 
shallow depth of field, 
cinematic lighting from the side, 
dark graphite background #1A1A1A, 
Japanese red accent on the calculator display #E30613, 
warm ochra tones from overhead lamp, 
moody professional atmosphere, 
realistic photography, no text overlays, 
9:16 vertical or 1:1 square
```

---

## 👨‍🍳 Шаблон 2: Обложка поста про операционку / кухню

```
Professional chef hands plating sushi with precision, 
modern industrial kitchen background, 
stainless steel surfaces, 
kitchen tools neatly organized, 
side lighting emphasizing hand movements and knife, 
dark graphite environment #1A1A1A, 
small Japanese red accent somewhere (apron label, bowl rim) #E30613, 
documentary realism style, 
no stock photography feel, 
4:5 vertical
```

---

## 📊 Шаблон 3: Обложка поста про маркетинг / анализ

```
Dark graphite desk with laptop screen showing analytics dashboard, 
notebook with handwritten notes, coffee cup, pen, 
overhead angle, 
dramatic lamp lighting from left, 
red accent elements on screen graphs #E30613, 
warm wood texture desk, 
moody business research atmosphere, 
realistic photo, 
16:9 landscape or 1:1 square
```

---

## 🏗️ Шаблон 4: Обложка поста про открытие филиала / кейс

```
Exterior of a small modern sushi restaurant at twilight, 
warm interior lights glowing through windows, 
simple minimal signage with red accent #E30613, 
people silhouettes inside, 
cobblestone street, 
Russian provincial city atmosphere, 
cinematic quality, moody and inviting, 
no text visible on signs, 
16:9 landscape
```

---

## 📄 Шаблон 5: Обложка лид-магнита (PDF)

```
Minimalist composition: a single object on dark graphite background #1A1A1A, 
the object is [варьируется — calculator / notebook / chef knife / sushi plate], 
single Japanese red accent stripe #E30613 across composition, 
centered symmetric layout, 
studio lighting, 
high contrast clean design, 
suitable for book cover, 
no text, empty space at top for title overlay, 
portrait A4 format
```

---

## 🧩 Правила составления своих промптов

### Всегда включай:
1. **Сцену** — что именно в кадре
2. **Ракурс** — сверху / сбоку / прямо / общий / крупно
3. **Освещение** — боковое / верхнее / мягкое / драматичное
4. **Цвета** — палитра бренда обязательно
5. **Стиль** — realistic photography / cinematic / documentary

### Никогда не используй:
- «beautiful», «amazing», «stunning» (ничего не добавляют)
- «best quality», «masterpiece» (не работает в Nano Banana как в Midjourney)
- Тексты в промпте (модель плохо рендерит текст)
- Более 5 объектов в одной сцене

---

## 🔁 Итерация

Если результат не подходит:
1. Уточни **конкретный элемент** («the knife is too large» → «smaller prep knife, 15cm blade»)
2. Уточни **освещение** («softer light from above» вместо «dramatic»)
3. Уточни **цвета** конкретными hex-кодами
4. Измени **стиль** (с realistic на editorial или наоборот)

---

## 📁 Сохранение результатов

Готовые изображения → `platforms/<название>/assets/` или `content-bank/visual/assets/`.

Хорошие находки — промпт + результат → [[design-system/examples/]] для библиотеки.
