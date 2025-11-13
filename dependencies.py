import urllib.request
import json
import gzip
import zipfile
import xml.etree.ElementTree as ET
import os


def get_direct_dependencies(package, repo, mode):
    """
    Извлекает прямые зависимости пакета в формате NuGet.
    Для remote: repo — URL index.json (e.g., https://api.nuget.org/v3/index.json).
    Для local: repo — путь к .nupkg файлу.
    """
    deps = []
    try:
        if mode == 'remote':
            # Шаг 1: Загрузить index.json
            with urllib.request.urlopen(repo) as response:
                index_data = response.read().decode('utf-8')
                index = json.loads(index_data)

            # Шаг 2: Найти RegistrationsBaseUrl/3.6.0
            reg_base = None
            for resource in index.get('resources', []):
                if resource.get('@type') == 'RegistrationsBaseUrl/3.6.0':
                    reg_base = resource.get('@id')
                    break
            if not reg_base:
                raise ValueError("RegistrationsBaseUrl/3.6.0 не найден в index.json.")

            # Шаг 3: Сформировать URL registration index
            reg_url = f"{reg_base}{package.lower()}/index.json"

            # Шаг 4: Загрузить (с поддержкой gzip)
            req = urllib.request.Request(reg_url, headers={'Accept-Encoding': 'gzip'})
            with urllib.request.urlopen(req) as response:
                data = response.read()
                encoding = response.info().get('Content-Encoding')
                if encoding == 'gzip':
                    data = gzip.decompress(data)
                reg = json.loads(data)

            # Шаг 5: Найти последнюю версию (учитывая multi-page)
            last_page = reg['items'][-1]
            if 'items' in last_page:
                latest_entry = last_page['items'][-1]['catalogEntry']
            else:
                # Загрузить страницу, если items не embedded
                with urllib.request.urlopen(last_page['@id']) as response:
                    page_data = response.read().decode('utf-8')
                    page = json.loads(page_data)
                latest_entry = page['items'][-1]['catalogEntry']

            # Шаг 6: Извлечь зависимости
            dependency_groups = latest_entry.get('dependencyGroups', [])
            for group in dependency_groups:
                dependencies = group.get('dependencies', [])
                for dep in dependencies:
                    dep_id = dep.get('id')
                    if dep_id:
                        deps.append(dep_id)

        elif mode == 'local':
            # Проверка: repo должен быть .nupkg файлом
            if not os.path.isfile(repo) or not repo.endswith('.nupkg'):
                raise ValueError("Для local mode repo должен быть путем к .nupkg файлу.")

            # Открыть ZIP (.nupkg)
            with zipfile.ZipFile(repo, 'r') as z:
                # Найти .nuspec файл (обычно package_id.nuspec)
                nuspec_files = [name for name in z.namelist() if name.endswith('.nuspec')]
                if not nuspec_files:
                    raise ValueError("Файл .nuspec не найден в .nupkg.")
                nuspec_path = nuspec_files[0]  # Берем первый

                # Прочитать и парсить XML
                with z.open(nuspec_path) as f:
                    xml_content = f.read()
                tree = ET.fromstring(xml_content)

                # Namespace для NuGet nuspec
                ns = {'nuspec': 'http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd'}

                # Найти все <dependency id="...">
                dep_elements = tree.findall(".//nuspec:dependency", ns)
                for dep in dep_elements:
                    dep_id = dep.get('id')
                    if dep_id:
                        deps.append(dep_id)

        # Уникальные зависимости
        unique_deps = list(set(deps))
        return unique_deps

    except Exception as e:
        raise ValueError(f"Ошибка при получении зависимостей: {str(e)}")