import urllib.request
import json
import gzip
import zipfile
import xml.etree.ElementTree as ET
import os
from collections import deque, defaultdict


def get_direct_dependencies(package, repo, mode):
    """
    Извлекает прямые зависимости пакета.
    Для 'test': repo - путь к JSON {"pkg": ["dep1", "dep2"], ...}
    """
    deps = []
    try:
        if mode == 'remote':
            # (код из этапа 2, без изменений)
            with urllib.request.urlopen(repo) as response:
                index_data = response.read().decode('utf-8')
                index = json.loads(index_data)

            reg_base = None
            for resource in index.get('resources', []):
                if resource.get('@type') == 'RegistrationsBaseUrl/3.6.0':
                    reg_base = resource.get('@id')
                    break
            if not reg_base:
                raise ValueError("RegistrationsBaseUrl/3.6.0 не найден в index.json.")

            reg_url = f"{reg_base}{package.lower()}/index.json"

            req = urllib.request.Request(reg_url, headers={'Accept-Encoding': 'gzip'})
            with urllib.request.urlopen(req) as response:
                data = response.read()
                encoding = response.info().get('Content-Encoding')
                if encoding == 'gzip':
                    data = gzip.decompress(data)
                reg = json.loads(data)

            last_page = reg['items'][-1]
            if 'items' in last_page:
                latest_entry = last_page['items'][-1]['catalogEntry']
            else:
                with urllib.request.urlopen(last_page['@id']) as response:
                    page_data = response.read().decode('utf-8')
                    page = json.loads(page_data)
                latest_entry = page['items'][-1]['catalogEntry']

            dependency_groups = latest_entry.get('dependencyGroups', [])
            for group in dependency_groups:
                dependencies = group.get('dependencies', [])
                for dep in dependencies:
                    dep_id = dep.get('id')
                    if dep_id:
                        deps.append(dep_id)

        elif mode == 'local':
            # (код из этапа 2, без изменений)
            if not os.path.isfile(repo) or not repo.endswith('.nupkg'):
                raise ValueError("Для local mode repo должен быть путем к .nupkg файлу.")

            with zipfile.ZipFile(repo, 'r') as z:
                nuspec_files = [name for name in z.namelist() if name.endswith('.nuspec')]
                if not nuspec_files:
                    raise ValueError("Файл .nuspec не найден в .nupkg.")
                nuspec_path = nuspec_files[0]

                with z.open(nuspec_path) as f:
                    xml_content = f.read()
                tree = ET.fromstring(xml_content)

                ns = {'nuspec': 'http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd'}

                dep_elements = tree.findall(".//nuspec:dependency", ns)
                for dep in dep_elements:
                    dep_id = dep.get('id')
                    if dep_id:
                        deps.append(dep_id)

        elif mode == 'test':
            # Новый: Читать JSON из файла
            if not os.path.isfile(repo) or not repo.endswith('.json'):
                raise ValueError("Для test mode repo должен быть путем к .json файлу.")

            with open(repo, 'r') as f:
                graph = json.load(f)

            deps = graph.get(package.upper(), [])  # Пакеты uppercase

        # Уникальные зависимости
        unique_deps = list(set(deps))
        return unique_deps

    except Exception as e:
        raise ValueError(f"Ошибка при получении зависимостей для {package}: {str(e)}")


def build_dependency_graph(start_package, repo, mode, max_depth, filter_str):
    """
    Строит граф зависимостей используя BFS (итеративный с очередью).
    Возвращает dict {pkg: [direct_deps]} с учетом глубины и фильтра.
    Обработка циклов: visited set.
    """
    graph = {}  # {pkg: [deps]}
    visited = set()
    queue = deque([(start_package, 0)])  # (pkg, depth)

    while queue:
        current_pkg, depth = queue.popleft()

        if current_pkg in visited:
            continue  # Цикл или уже посещено
        visited.add(current_pkg)

        if depth >= max_depth:
            continue  # Превышена глубина

        # Получить прямые зависимости
        try:
            deps = get_direct_dependencies(current_pkg, repo, mode)
        except ValueError:
            deps = []  # Если ошибка (пакет не найден) - пропустить

        # Фильтровать
        if filter_str:
            filtered_deps = [dep for dep in deps if filter_str.lower() not in dep.lower()]
        else:
            filtered_deps = deps

        graph[current_pkg] = filtered_deps

        # Добавить в очередь
        for dep in filtered_deps:
            if dep not in visited:
                queue.append((dep, depth + 1))

    return graph


def topological_sort(graph):
    """
    Выполняет topological sort с помощью Kahn's algorithm (BFS).
    Возвращает список пакетов в порядке загрузки (зависимости сначала).
    Если цикл - возвращает частичный порядок и флаг цикла.
    """
    # Вычислить in-degree (кол-во входящих рёбер)
    indegree = defaultdict(int)
    for deps in graph.values():
        for dep in deps:
            indegree[dep] += 1

    # Добавить узлы без входящих (листья или изолированные)
    queue = deque([pkg for pkg in graph if indegree[pkg] == 0])

    order = []
    while queue:
        current = queue.popleft()
        order.append(current)

        # Уменьшить indegree соседей
        for neighbor in graph.get(current, []):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    # Проверить на цикл
    has_cycle = len(order) < len(graph)
    return order, has_cycle