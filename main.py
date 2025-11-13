import argparse
import os
from urllib.parse import urlparse
from dependencies import get_direct_dependencies  # Новый импорт


def validate_repo(repo, mode):
    if mode == 'remote':
        parsed = urlparse(repo)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError(f"Невалидный URL для репозитория: {repo}. Ожидается формат http(s)://...")
    elif mode == 'local':
        if not os.path.exists(repo):
            raise ValueError(f"Путь к репозиторию не существует: {repo}")
    else:
        raise ValueError(f"Невалидный режим: {mode}. Допустимые: 'local' или 'remote'.")


def main():
    parser = argparse.ArgumentParser(
        description="Инструмент визуализации графа зависимостей для NuGet пакетов."
    )

    parser.add_argument('-p', '--package', required=True, type=str, help='Имя анализируемого пакета.')
    parser.add_argument('-r', '--repo', required=True, type=str,
                        help='URL репозитория (index.json) или путь к .nupkg файлу.')
    parser.add_argument('-m', '--mode', required=True, type=str, choices=['local', 'remote'],
                        help='Режим: local или remote.')
    parser.add_argument('-d', '--max-depth', default=3, type=int, help='Максимальная глубина (по умолчанию 3).')
    parser.add_argument('-f', '--filter', default='', type=str, help='Подстрока для фильтрации (по умолчанию пустая).')

    try:
        args = parser.parse_args()

        if args.max_depth < 1:
            raise ValueError(f"Максимальная глубина должна быть >=1, получено: {args.max_depth}")

        validate_repo(args.repo, args.mode)

        print("Параметры:")
        print(f"package: {args.package}")
        print(f"repo: {args.repo}")
        print(f"mode: {args.mode}")
        print(f"max_depth: {args.max_depth}")
        print(f"filter: {args.filter}")

        # Новый код: Получить и вывести прямые зависимости
        deps = get_direct_dependencies(args.package, args.repo, args.mode)
        print("Прямые зависимости:", ', '.join(deps) if deps else "Нет зависимостей.")

    except ValueError as ve:
        print(f"Ошибка валидации: {ve}")
        parser.print_help()
        exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        parser.print_help()
        exit(1)


if __name__ == "__main__":
    main()