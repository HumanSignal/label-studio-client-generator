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


def load_yaml(file_path: str) -> dict:
    yaml = YAML()
    with open(file_path, 'r') as f:
        return yaml.load(f)


def get_paths_from_resource(resource_file: str) -> Set[str]:
    """Extract all paths from a resource YAML file."""
    content = load_yaml(resource_file)
    if not content or 'paths' not in content:
        return set()
    return set(content['paths'].keys())


def get_all_resource_paths() -> Dict[str, Set[str]]:
    """Get all paths from all resource YAML files."""
    base_dir = Path(__file__).parent.parent / 'fern' / 'openapi' / 'resources'
    resource_paths = {}
    
    for file in base_dir.glob('*.yaml'):
        paths = get_paths_from_resource(str(file))
        if paths:
            resource_paths[file.name] = paths
    
    return resource_paths


def get_existing_override_paths(overrides_file: str) -> Set[str]:
    """Get all paths already defined in overrides.yaml."""
    content = load_yaml(overrides_file)
    if not content or 'paths' not in content:
        return set()
    return set(content['paths'].keys())


def create_override_entry(path: str, resource_file: str) -> Dict:
    """Create a new override entry for a path."""
    ref_path = path.replace('/', '~1')
    group_name = resource_file.replace('.yaml', '')
    
    resource_content = load_yaml(str(Path(__file__).parent.parent / 'fern' / 'openapi' / 'resources' / resource_file))
    methods = resource_content['paths'][path].keys()
    
    entries = {}
    for method in methods:
        entries[method] = {
            '$ref': f'./resources/{resource_file}#/paths/{ref_path}/{method}',
            'x-fern-sdk-group-name': group_name,
            'x-fern-sdk-method-name': get_method_name(method, path),
            'x-fern-audiences': ['public']
        }
    
    return entries


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


def update_overrides(overrides_file: str, new_entries: Dict[str, Dict]) -> None:
    with open(overrides_file, 'r') as f:
        content = f.read()
    
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 80
    yaml.indent(mapping=2, sequence=4, offset=2)
    
    data = yaml.load(content) or {}
    
    if 'paths' not in data:
        data['paths'] = {}
    
    for path, entry in new_entries.items():
        if path not in data['paths']:
            data['paths'][path] = entry
    
    with open(overrides_file, 'w') as f:
        yaml.dump(data, f)


def main():
    overrides_file = str(Path(__file__).parent.parent / 'fern' / 'openapi' / 'overrides.yaml')
    existing_paths = get_existing_override_paths(overrides_file)
    resource_paths = get_all_resource_paths()
    new_entries = {}
    for resource_file, paths in resource_paths.items():
        for path in paths:
            if path not in existing_paths:
                new_entries[path] = create_override_entry(path, resource_file)
    
    if new_entries:
        print(f"Adding {len(new_entries)} new entries to overrides.yaml")
        update_overrides(overrides_file, new_entries)
        print("Done!")
    else:
        print("No new entries to add.")


if __name__ == '__main__':
    main()
