---
name: Kling 3.0 — базовые промпты
description: Шаблоны промптов для генерации видео в фирменном стиле
type: reference
tool: kling-3.0
---

# 🎬 Kling 3.0 — промпт-библиотека FBA

> Kuaishou text/image-to-video. Используем для B-roll и атмосферных вставок.

---

## 🎯 Как используем

- **B-roll для Shorts / TikTok / Reels** (5-10с клипы)
- **Атмосферные интро для YouTube** (3-5с заставки)
- **Переходы в длинных видео** (1-2с элементы)
- **Фоновые клипы для каруселей Instagram**

---

## 🧩 Базовый каркас промпта

```
[СЦЕНА], [ДВИЖЕНИЕ КАМЕРЫ], [ДВИЖЕНИЕ В КАДРЕ], 
[ОСВЕЩЕНИЕ], [АТМОСФЕРА], 
[СТИЛЬ: cinematic, documentary, shallow DoF], 
[ДЛИТЕЛЬНОСТЬ: 5s]
```

---

## 🍣 Шаблон 1: Кухня в движении (B-roll)

```
Sushi chef hands working precisely on maki roll on dark wooden board, 
camera slowly dollies in from right side, 
steady professional movement, 
warm side lighting from left, 
dark graphite restaurant interior in background, 
documentary style, shallow depth of field, 
atmospheric Japanese restaurant mood, 
5 seconds, 9:16 vertical
```

---

## 📊 Шаблон 2: Таблица / цифры на экране

```
Close-up of laptop screen showing animated financial spreadsheet, 
numbers and charts updating dynamically, 
red accent numbers highlighted, 
subtle camera drift left to right, 
desk lamp creating warm side light, 
dark office environment, 
professional business atmosphere, 
cinematic, 5 seconds, 16:9
```

---

## 🏪 Шаблон 3: Ресторан снаружи (кейс-ролик)

```
Small modern sushi restaurant exterior at twilight, 
warm interior glow through large window, 
people silhouettes inside, 
camera slowly moves forward toward entrance, 
light rain starting, 
Russian provincial city street, 
cinematic atmospheric evening, 
moody documentary style, 
5 seconds, 16:9 horizontal
```

---

## 🔥 Шаблон 4: Динамичный хук для TikTok

```
Extreme close-up of chef knife slicing salmon fillet, 
precise single cut, camera steady, 
dramatic side light, 
focused intensity, 
dark background, 
vibrant red accent from ingredient, 
slow motion capture, 
cinematic quality, 
3 seconds, 9:16 vertical
```

---

## 📖 Шаблон 5: Открытие книги / документа

```
Hands opening a spiral-bound business notebook on dark wooden desk, 
pages flipping slowly showing handwritten notes and tables, 
soft overhead lighting, 
warm atmospheric mood, 
red pen beside notebook, 
documentary style, 
5 seconds, 16:9
```

---

## 📋 Правила движения

### Работающие движения камеры
- **Slow dolly in** — плавное приближение
- **Pan left/right** — горизонтальное панорамирование
- **Static with subtle drift** — почти неподвижно, лёгкий дрейф
- **Pull focus** — перефокусировка

### НЕ работающие (для нашего стиля)
- Быстрые zoom-in/out
- Вращение камеры
- Резкие смены ракурса
- «Handheld shake»

---

## 🎨 Согласование с бренд-палитрой

В **каждом** Kling-промпте упомяни:
- `dark graphite atmosphere`
- `warm side lighting` или `warm overhead lighting`
- `Japanese red accent` (если есть красный объект в сцене)
- `cinematic`, `documentary`, `atmospheric`

---

## ⚠️ Ограничения Kling

- Текст в кадре рендерится плохо — не планируй титры внутри генерации
- Лица крупно — бывают артефакты, лучше делать со стороны или кисти
- Руки крупным планом — хороши
- Логотипы — не использовать в промпте (плагиат-риск)

---

## 📁 Сохранение

Готовые видео → `platforms/<название>/assets/video/` с уникальным именем.
Успешные промпты — в [[design-system/examples/]].
