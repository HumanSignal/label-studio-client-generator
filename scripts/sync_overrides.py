#!/usr/bin/env python3
# To run this script, use:
#   uv run scripts/sync_overrides.py
#
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "ruamel.yaml>=0.17.0",
# ]
# ///

from pathlib import Path
from typing import Dict, Set

from ruamel.yaml import YAML

YAML_CLIENT = YAML()
YAML_CLIENT.preserve_quotes = True
YAML_CLIENT.width = 80
YAML_CLIENT.indent(mapping=2, sequence=4, offset=2)

REPO_ROOT_PATH = Path(__file__).parent.parent


def get_paths_from_resource(resource_file: str) -> Set[str]:
    """Extract all paths from a resource YAML file."""
    with open(resource_file, 'r') as f:
        content = YAML_CLIENT.load(f)
    if not content or 'paths' not in content:
        return set()
    return set(content['paths'].keys())


def get_all_resource_urls_by_filename() -> Dict[str, Set[str]]:
    """Get all paths from all resource YAML files."""
    base_dir = REPO_ROOT_PATH / 'fern' / 'openapi' / 'resources'
    resource_urls_by_filename = {}
    
    for file in base_dir.glob('*.yaml'):
        paths = get_paths_from_resource(str(file))
        if paths:
            resource_paths[file.name] = paths
    
    return resource_urls_by_filename


def get_existing_override_urls(overrides_file: str) -> Set[str]:
    """Get all paths already defined in overrides.yaml."""
    with open(overrides_file, 'r') as f:
        content = YAML_CLIENT.load(f)
    if not content or 'paths' not in content:
        return set()
    return set(content['paths'].keys())


def create_override_entries(path: str, resource_filename: str) -> Dict:
    """Create a new override entry for a path."""
    ref_path = path.replace('/', '~1')
    group_name = resource_filename.replace('.yaml', '')

    resource_path = str(REPO_ROOT_PATH / 'fern' / 'openapi' / 'resources' / resource_filename)
    with open(resource_path, 'r') as f:
        resource_content = YAML_CLIENT.load(f)
    methods = resource_content['paths'][path].keys()
    
    return {
        method: {
            '$ref': f'./resources/{resource_filename}#/paths/{ref_path}/{method}',
            'x-fern-sdk-group-name': group_name,
            'x-fern-sdk-method-name': get_method_name(method, path),
            'x-fern-audiences': ['public']
        }
        for method in methods
    }


def get_method_name(http_method: str, path: str) -> str:
    if http_method == 'get':
        if path.endswith('/'):
            return 'list'
        return 'get'
    elif http_method == 'post':
        return 'create'
    elif http_method == 'patch':
        return 'update'
    elif http_method == 'delete':
        return 'delete'
    return http_method


def update_overrides(overrides_path: str, new_entries: Dict[str, Dict]) -> None:
    with open(overrides_path, 'r') as f:
        content = f.read()
    
    data = YAML_CLIENT.load(content) or {}
    data['paths'] = data.get('paths', {})
    for path, entry in new_entries.items():
        if path not in data['paths']:
            data['paths'][path] = entry
    
    with open(overrides_path, 'w') as f:
        YAML_CLIENT.dump(data, f)


def main():
    overrides_path = str(REPO_ROOT_PATH / 'fern' / 'openapi' / 'overrides.yaml')
    existing_urls = get_existing_override_urls(overrides_path)
    resource_urls_by_filename = get_all_resource_urls_by_filename()
    new_entries = {}
    for resource_filename, urls in resource_urls_by_filename.items():
        for url in urls:
            if url not in existing_urls:
                new_entries[url] = create_override_entries(url, resource_filename)
    
    if new_entries:
        print(f"Adding {len(new_entries)} new entries to overrides.yaml...")
        update_overrides(overrides_path, new_entries)
        print("Done!")
    else:
        print("No new entries to add.")


if __name__ == '__main__':
    main()
