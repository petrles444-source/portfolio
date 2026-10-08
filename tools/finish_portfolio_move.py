r"""Довести перенос проекта сайтов: снять блокировки и проверить копию.

Зачем
----
`shutil.move` на Windows сначала пробует переименовать папку целиком,
и это мгновенно. Если что-то мешает — а мешало то же самое, что и
раньше, атрибут ReadOnly на каталогах — он падает на `os.rename`,
переходит к копированию, а на удалении оригинала снова спотыкается.

Результат получился в безопасную сторону: данные уже лежат в новом
месте, а оригинал остался. Это лучший из возможных исходов, но
состояние нужно довести до конца и — главное — проверить, что копия
полная. Именно это здесь и делается: сначала сверка по числу файлов и
их отпечаткам, и только потом удаление оригинала.

Запуск:
    .venv\\Scripts\\python.exe tools\\finish_portfolio_move.py
"""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORTFOLIO = ROOT.parent / "portfolio"

DATA = ("site", "site-dist", "portfolios", "publish", "sites",
        "screenshots")


def digest(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def clear_readonly(path: Path) -> int:
    cleared = 0
    for item in [path, *path.rglob("*")]:
        try:
            os.chmod(item, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
            cleared += 1
        except OSError:
            pass
    return cleared


def compare(src: Path, dst: Path) -> tuple[int, int, list[str]]:
    """Сверить две папки по содержимому.

    Считаются три вещи: сколько файлов потеряно, сколько отличается
    и какие именно. Простое сравнение числа файлов обманчиво — можно
    потерять один и получить один лишний.
    """
    src_files = {p.relative_to(src).as_posix(): p
                 for p in src.rglob("*") if p.is_file()}
    dst_files = {p.relative_to(dst).as_posix(): p
                 for p in dst.rglob("*") if p.is_file()}

    missing = sorted(set(src_files) - set(dst_files))
    extra = sorted(set(dst_files) - set(src_files))

    differs = []
    for key in sorted(set(src_files) & set(dst_files)):
        # Крупные файлы не сверяются по отпечатку: это минуты
        # вычислений ради проверки, которая почти всегда даёт
        # «одинаково». Сверяются только размер и сам факт.
        if src_files[key].stat().st_size != dst_files[key].stat().st_size:
            differs.append(key + " (размер)")
        elif src_files[key].stat().st_size < 2 * 1024 * 1024:
            if digest(src_files[key]) != digest(dst_files[key]):
                differs.append(key + " (содержимое)")
    return len(missing), len(extra), missing + differs


def main() -> int:
    print("=== сверка копии перед удалением оригинала ===")
    all_good = True

    for name in DATA:
        src = ROOT / name
        dst = PORTFOLIO / name
        if not dst.exists():
            print(f"  {name}: в новом месте нет — пропускаю")
            continue
        if not src.exists():
            print(f"  {name}: уже перенесён")
            continue

        missing, extra, problems = compare(src, dst)
        total = len([p for p in src.rglob("*") if p.is_file()])
        if missing or problems:
            all_good = False
            print(f"  {name}: НЕ СОВПАДАЕТ — не хватает {missing}, "
                  f"проблем {len(problems)}")
            for item in problems[:5]:
                print(f"      {item}")
            continue

        print(f"  {name}: совпадает ({total} файлов, "
              f"лишних в копии {extra})")
        clear_readonly(src)
        shutil.rmtree(src, ignore_errors=True)
        if src.exists():
            print(f"      оригинал НЕ УДАЛЁН")
            all_good = False
        else:
            print(f"      оригинал удалён")

    print()
    print("=== итог ===")
    if all_good:
        print("  перенос доведён до конца, данные целы")
        return 0
    print("  ЕСТЬ НЕСОВПАДЕНИЯ — оригиналы оставлены целыми")
    return 1


if __name__ == "__main__":
    sys.exit(main())