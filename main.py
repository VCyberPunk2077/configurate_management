import argparse
import os
from urllib.parse import urlparse


def validate_repo(repo, mode):
    if mode == 'remote':
        # Проверяем, что это валидный URL
        parsed = urlparse(repo)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError(f"Невалидный URL для репозитория: {repo}. Ожидается формат http(s)://...")
    elif mode == 'local':
        # Проверяем существование пути
        if not os.path.exists(repo):
            raise ValueError(f"Путь к репозиторию не существует: {repo}")
    else:
        raise ValueError(f"Невалидный режим: {mode}. Допустимые: 'local' или 'remote'.")


def main():
    parser = argparse.ArgumentParser(
        description="Минимальный прототип инструмента визуализации графа зависимостей для менеджера пакетов."
    )

    # Обязательные параметры
    parser.add_argument('-p', '--package', required=True, type=str, help='Имя анализируемого пакета.')
    parser.add_argument('-r', '--repo', required=True, type=str,
                        help='URL репозитория или путь к файлу тестового репозитория.')
    parser.add_argument('-m', '--mode', required=True, type=str, choices=['local', 'remote'],
                        help='Режим работы с репозиторием: local или remote.')

    # Опциональные параметры
    parser.add_argument('-d', '--max-depth', default=3, type=int,
                        help='Максимальная глубина анализа зависимостей (по умолчанию 3).')
    parser.add_argument('-f', '--filter', default='', type=str,
                        help='Подстрока для фильтрации пакетов (по умолчанию пустая).')

    try:
        args = parser.parse_args()

        # Дополнительная валидация
        if args.max_depth < 1:
            raise ValueError(f"Максимальная глубина должна быть >=1, получено: {args.max_depth}")

        validate_repo(args.repo, args.mode)

        # Вывод параметров в формате ключ-значение
        print("Параметры:")
        print(f"package: {args.package}")
        print(f"repo: {args.repo}")
        print(f"mode: {args.mode}")
        print(f"max_depth: {args.max_depth}")
        print(f"filter: {args.filter}")

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