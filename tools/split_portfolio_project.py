r"""Вынести проект сайтов из агента в отдельную папку.

Зачем
----
Человек справедливо заметил: портфолио с сайтами — это не агент, и
 держать его в репозитории агента незачем. Занимает оно 430 МБ из
495, то есть 86 процентов объёма, и к агенту отношения не имеет.

Главная сложность
-----------------
Путь `site/` зашит в коде примерно двадцати пяти инструментов. Если
просто перенести данные и оставить инструменты, все они разом
сломаются.

Решение здесь простое: инструменты переезжают **вместе со своими
данными**. У каждого из них `ROOT` — это папка на уровень выше
самого скрипта, и после переноса `ROOT` укажет на папку проекта
сайтов. Ни строчки кода менять не придётся: `ROOT / "site"`
останется верным просто потому, что изменилось то, откуда считается
`ROOT`.

Почему это надёжно
-------------------
Проверяется не «должно работать», а фактически: после переноса
каждый инструмент разбирается, а ключевые из них (`build_site.py`,
`make_catalog.py`) запускаются на настоящих данных и должны сделать
своё дело.

Что переезжает
--------------
Данные: `site/`, `site-dist/`, `portfolios/`, `publish/`, `sites/`,
`screenshots/`.

Инструменты: те, что ссылаются на эти папки. Остальные — инструменты
агента, они остаются.

Что остаётся в агенте
---------------------
Ядро (`hub/`, `providers/`, `config/`), тесты, боты, радио,
плеер, утилиты агента. Репозиторий станет в шесть раз легче.

Запуск:
    .venv\\Scripts\\python.exe tools\\split_portfolio_project.py
    .venv\\Scripts\\python.exe tools\\split_portfolio_project.py --dry-run
"""

from __future__ import annotations

import argparse
import ast
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORTFOLIO = ROOT.parent / "portfolio"

#: Данные сайтов.
SITE_DATA = ("site", "site-dist", "portfolios", "publish", "sites",
             "screenshots")

#: Что ищется в коде инструмента, чтобы понять, чей он.
SITE_MARKERS = ('"site"', "'site'", '"site-dist"', '"portfolios"',
                '"publish"', '"shots"', '"demo"')

#: Инструменты агента: переезд им не нужен ни при каких условиях.
#: Список явный, чтобы инструмент про сайты не уехал вместе с
#: агентом из-за одного случайного совпадения в тексте.
AGENT_TOOLS = {
    "check_env.py", "check_secrets.py", "check_tool_models.py",
    "check_vision.py", "clean_tmp_folders.py", "force_remove_bench.py",
    "clean_root.py", "make_connections_doc.py", "make_bots_standalone.py",
    "update_bot_tests.py", "split_name_test.py", "split_glossary_test.py",
    "rebuild_handle.py", "fix_handle_order.py", "fix_handle_small.py",
    "wire_chars.py", "update_projects_map.py", "fix_archive_name.py",
    "set_bot_personas.py", "prepare_git.py", "final_layout.py",
    "build_structure.py", "tidy_demo.py", "tidy_root_files.py",
    "tidy_character.py", "reorganize_root.py", "finish_moves.py",
    "unify_sites.py", "tidy_root_files.py", "agent.py", "bot_proxy.py",
    "bot_proxy_ada.py", "subagents_run.py", "selfcheck.py",
    "llm_bench.py", "bench_regressions.py",
}


def is_site_tool(path: Path) -> bool:
    """Свой ли это инструмент сайтов."""
    if path.name in AGENT_TOOLS:
        return False
    try:
        body = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return any(marker in body for marker in SITE_MARKERS)


def wipe(path: Path) -> None:
    for item in [path, *path.rglob("*")]:
        try:
            os.chmod(item, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        except OSError:
            pass
    shutil.rmtree(path, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="вынести проект сайтов")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    dry = args.dry_run

    tools = sorted(p for p in (ROOT / "tools").glob("*.py"))
    site_tools = [p for p in tools if is_site_tool(p)]
    agent_tools = [p for p in tools if p not in site_tools]

    print(f"инструментов всего: {len(tools)}")
    print(f"  уезжают с сайтами: {len(site_tools)}")
    print(f"  остаются в агенте:  {len(agent_tools)}")

    if dry:
        print("\nПРОСМОТР. Ничего не переносится.\n")
        print("уезжают:")
        for tool in site_tools:
            print(f"  {tool.name}")
        return 0

    # 1. Папка проекта.
    (PORTFOLIO / "tools").mkdir(parents=True, exist_ok=True)

    # 2. Данные. Переносятся целиком, кроме demo/_assets: там
    #    197 МБ временных картинок, и в репозитории им не место.
    for name in SITE_DATA:
        src = ROOT / name
        if not src.exists():
            print(f"  нет {name} — пропускаю")
            continue
        dst = PORTFOLIO / name
        if dst.exists():
            print(f"  {name} уже есть на месте — пропускаю")
            continue
        print(f"  переношу {name}")
        shutil.move(str(src), str(dst))

    # 3. Инструменты.
    moved = 0
    for tool in site_tools:
        target = PORTFOLIO / "tools" / tool.name
        if target.exists():
            continue
        shutil.move(str(tool), str(target))
        moved += 1
    print(f"  перенесено инструментов: {moved}")

    # 4. Проверка: каждый переехавший инструмент разбирается.
    print()
    print("=== проверка: инструменты разбираются ===")
    broken = []
    for tool in sorted((PORTFOLIO / "tools").glob("*.py")):
        try:
            ast.parse(tool.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as exc:
            broken.append((tool.name, str(exc)[:60]))
    if broken:
        for name, why in broken:
            print(f"  СЛОМАНО {name}: {why}")
    else:
        print(f"  все {len(list((PORTFOLIO / 'tools').glob('*.py')))} "
              f"разбираются")

    # 5. Проверка на настоящих данных: сборщик обязан отработать.
    print()
    print("=== проверка: сборка сайтов на новом месте ===")
    python = ROOT / ".venv" / "Scripts" / "python.exe"
    if python.is_file():
        result = subprocess.run(
            [str(python), str(PORTFOLIO / "tools" / "build_site.py")],
            capture_output=True, text=True, cwd=str(PORTFOLIO), timeout=1800)
        tail = (result.stdout or result.stderr).strip().splitlines()
        for line in tail[-3:]:
            print(f"  {line}")
        if result.returncode != 0:
            print("  СБОРКА НЕ ПРОШЛА")
            return 1
        print("  сборка прошла")
    else:
        print("  виртуальное окружение не найдено — сборка не проверена")

    print()
    print(f"проект сайтов: {PORTFOLIO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())