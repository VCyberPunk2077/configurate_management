import argparse
import os
from urllib.parse import urlparse
from dependencies import build_dependency_graph, topological_sort


def validate_repo(repo, mode):
    if mode == 'remote':
        parsed = urlparse(repo)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError(f"Невалидный URL для репозитория: {repo}. Ожидается формат http(s)://...")
    elif mode in ['local', 'test']:
        if not os.path.exists(repo):
            raise ValueError(f"Путь к репозиторию не существует: {repo}")
    else:
        raise ValueError(f"Невалидный режим: {mode}. Допустимые: 'local', 'remote', 'test'.")


def main():
    parser = argparse.ArgumentParser(
        description="Инструмент визуализации графа зависимостей для NuGet пакетов с поддержкой теста и вывода порядка."
    )

    parser.add_argument('-p', '--package', required=True, type=str, help='Имя анализируемого пакета.')
    parser.add_argument('-r', '--repo', required=True, type=str,
                        help='URL репозитория (index.json), путь к .nupkg или .json для test.')
    parser.add_argument('-m', '--mode', required=True, type=str, choices=['local', 'remote', 'test'],
                        help='Режим: local, remote или test.')
    parser.add_argument('-d', '--max-depth', default=3, type=int, help='Максимальная глубина (по умолчанию 3).')
    parser.add_argument('-f', '--filter', default='', type=str, help='Подстрока для фильтрации (по умолчанию пустая).')
    parser.add_argument('-o', '--output', default='graph', type=str, choices=['graph', 'topological'],
                        help='Режим вывода: graph или topological (по умолчанию graph).')

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
        print(f"output: {args.output}")

        # Построить граф
        graph = build_dependency_graph(args.package, args.repo, args.mode, args.max_depth, args.filter)

        if args.output == 'graph':
            print("Граф зависимостей:")
            for pkg, deps in graph.items():
                print(f"{pkg}: {', '.join(deps) if deps else 'Нет зависимостей'}")
        elif args.output == 'topological':
            order, has_cycle = topological_sort(graph)
            print("Порядок загрузки зависимостей:", ', '.join(order))
            if has_cycle:
                print("Предупреждение: Обнаружен цикл в зависимостях, порядок частичный.")

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