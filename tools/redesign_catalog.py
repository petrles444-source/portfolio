r"""Переделать каталог: крупное превью вместо мелкой картинки.

Зачем
----
Человек прислал скриншот и сказал прямо: превью мелкие, и сразу не
видно, что на сайте. На скриншоте у карточек Aurum и Lumen снимка не
было вовсе — вместо него полоса из палитры, — но даже там, где снимок
есть, он занимал 168 пикселей рядом с текстом.

Три причины, и все три проверяются здесь:

1. **Превью мелкое.** `width: clamp(96px, 15vw, 168px)` — это
   миниатюра для иконки, а не витрина. Ставится на всю ширину
   карточки.
2. **Превью нет у семи портфолио.** Причина найдена отдельно: их не
   было в списке адресов для съёмки. Список дополнен, снимки
   сняты — см. `tools/add_portfolio_shots.py`.
3. **Пропорции.** Снимок 1280×800 — это 16:10. Кадр показывается
   целиком, без обрезки, иначе половина страницы пропадает. Но если
   страница окажется сильно вытянутой по вертикали, кадр сжимается
   по высоте и остаётся читаемым: пропорция кадра сохраняется, а
   рамка подстраивается под содержимое.

Что меняется
------------
* `.card` становится вертикальной: снимок сверху во всю ширину,
  текст под ним;
* сетка остаётся в две колонки — с крупным снимком карточка
  становится высокой, и в четыре колонки они не влезут;
* добавлена рамка при наведении и подпись под снимком;
* `.noshot` (снимка нет) остаётся на месте: честнее пустой рамки,
  видно, что это витрина, а не кадр.

Запуск:
    .venv\\Scripts\\python.exe tools\\redesign_catalog.py
    .venv\\Scripts\\python.exe tools\\redesign_catalog.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "site" / "assets" / "catalog.css"

#: Начало блока со стилями карточки и превью. Всё отсюда до
#: `@media` про телефон заменяется целиком — так не остаётся
#: половины от старого оформления.
START = "/* Карточка: полоса слева — единственное место с цветом. */"
END = "@media (max-width: 620px) {"

NEW_BLOCK = """/*
 * Карточка.
 *
 * Устройство прежнее было горизонтальным: слева снимок шириной 168
 * пикселей, справа текст. На деле витрина от этого не работала —
 * в снимке шириной 168 пикселей помещалось около четверти экрана,
 * и понять, что на странице, было невозможно.
 *
 * Теперь карточка вертикальная: снимок занимает всю ширину, текст
 * лежит под ним. Растянутая по вертикали страница сжимает кадр по
 * высоте, но не искажает его: пропорция сохраняется, а рамка
 * подстраивается под содержимое.
 */
.card {
  display: flex;
  flex-direction: column;
  gap: 0;
  align-items: stretch;
  /* Номер стоит поверх снимка. Без `relative` он уехал бы искать
   * ближайшего предка с позиционированием — то есть уехал бы из
   * карточки совсем. */
  position: relative;
  text-decoration: none;
  color: inherit;
  background: var(--card);
  border: 1px solid var(--rule);
  border-top: 3px solid var(--muted);
  padding: 0;
  overflow: hidden;
  transition: border-color 140ms ease, transform 140ms ease,
              box-shadow 140ms ease;
}

.card:hover {
  background: #fff;
  border-color: var(--muted);
  box-shadow: 0 6px 22px rgba(28, 26, 22, .10);
}

.card:focus-visible {
  outline: 2px solid var(--muted);
  outline-offset: 2px;
}

.card-wide { border-top-width: 3px; }

/* Текстовая часть — под снимком, с внутренними отступами. */
.card .body {
  padding: clamp(14px, 2vw, 20px) clamp(16px, 2.4vw, 24px)
           clamp(18px, 2.4vw, 24px);
}

.card .num {
  position: absolute;
  top: 10px;
  left: 12px;
  z-index: 2;
}

/* --- превью --- */
/*
 * Снимок настоящего первого экрана: без обрезки, целиком. Раньше он
 * влезал в 168 пикселей и превращался в пятно; теперь ширина равна
 * ширине карточки, и по кадру видно, что вообще за страница.
 *
 * `object-fit: contain`, а не `cover`: обрезка убрала бы половину
 * кадра у сильно вытянутых страниц, а ради того, чтобы ряд был ровный,
 * и не стоит — высоты и так выравниваются по сетке.
 */
.shot {
  display: block;
  width: 100%;
  height: auto;
  /* Нижняя граница вместо рамки со всех сторон: рамка под снимком
     сливалась бы с рамкой карточки и давала двойную линию. */
  border-bottom: 1px solid var(--rule);
  background: #efece4;
  /* Кадр не должен растягиваться по высоте карточки. */
  max-height: 62vh;
  object-fit: contain;
  object-position: top center;
}

/* Место под снимок, когда его нет. Полоса, а не пустая рамка: видно,
 * что это витрина, а не кадр. Справочники и подачи снимать смысла
 * нет — у них нет своего визуального лица. */
.noshot {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 10;
  border-bottom: 1px solid var(--rule);
  background:
    linear-gradient(135deg,
      transparent 0 46%,
      color-mix(in srgb, var(--muted) 55%, transparent) 46% 54%,
      transparent 54% 100%),
    var(--card);
}

/* Сетка: две колонки. С крупным снимком карточка высокая, и в четыре
 * колонки на обычном мониторе они не поместятся — получится ряд
 * узких полос. */
"""

TAIL = """@media (max-width: 900px) {
  /* На планшете две колонки уже жмут снимок до неразборчивости. */
  .grid { grid-template-columns: 1fr; }
}

@media (max-width: 620px) {
  .card .num { padding-top: 0; }
  .shot, .noshot { aspect-ratio: 16 / 9; }
  .noshot { aspect-ratio: 16 / 9; }
}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="переделать каталог")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not CSS.is_file():
        print("файл стилей каталога не найден", file=sys.stderr)
        return 1

    body = CSS.read_text(encoding="utf-8")
    start = body.find(START)
    end = body.find(END, start if start != -1 else 0)

    if start == -1 or end == -1:
        print(f"границы блока не найдены: начало={start}, конец={end}",
              file=sys.stderr)
        print("  стили каталога придётся править руками", file=sys.stderr)
        return 1

    if args.dry_run:
        print("ПРОСМОТР: ничего не менялось")
        print(f"  заменяется {end - start} символов "
              f"(строки {body[:start].count(chr(10)) + 1}—"
              f"{body[:end].count(chr(10)) + 1})")
        return 0

    tail_start = end
    # Медиаправило для телефона заменяется целиком: в старом оно
    # переносило снимок вбок, а теперь он и так сверху.
    media_end = body.find("\n}\n", tail_start)
    if media_end == -1:
        media_end = len(body)
    else:
        media_end += 3

    new_body = body[:start] + NEW_BLOCK + TAIL + body[media_end:]
    CSS.write_text(new_body, encoding="utf-8")

    print(f"  заменено {end - start + (media_end - tail_start)} символов")
    print(f"  catalog.css: {len(new_body)} символов")

    # Проверка: новые правила на месте, старых нет.
    for needle in ("width: 100%", "grid-template-columns: 1fr 1fr",
                   "object-fit: contain", "flex-direction: column"):
        ok = needle in new_body
        print(f"  {'ок  ' if ok else 'НЕТ '} {needle}")
    return 0 if all(n in new_body for n in
                    ("flex-direction: column", "object-fit: contain")) else 1


if __name__ == "__main__":
    sys.exit(main())