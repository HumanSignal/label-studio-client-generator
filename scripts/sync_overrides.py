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


def get_urls_from_spec(spec: dict) -> Set[str]:
    """Extract all urls from an openapi spec."""
    urls = spec.get('paths', {}).keys()
    return set(urls)


def get_all_urls_by_filename() -> Dict[str, Set[str]]:
    """Get all urls from openapi spec YAML files."""
    base_dir = REPO_ROOT_PATH / 'fern' / 'openapi' / 'resources'
    urls_by_filename = {}
    
    for file in base_dir.glob('*.yaml'):
        with open(str(file), 'r') as f:
            spec = YAML_CLIENT.load(f) or {}
        urls = get_urls_from_spec(spec)
        if urls:
            urls_by_filename[file.name] = urls
    
    return urls_by_filename


def create_override_entries(url: str, openapi_spec_filename: str) -> Dict:
    """Create a new set of override entries from the openapi spec for the given url."""
    ref_path = url.replace('/', '~1')
    group_name = openapi_spec_filename.replace('.yaml', '')

    spec_path = str(REPO_ROOT_PATH / 'fern' / 'openapi' / 'resources' / openapi_spec_filename)
    with open(spec_path, 'r') as f:
        spec = YAML_CLIENT.load(f)
    methods = spec['paths'][url].keys()
    
    return {
        method: {
            '$ref': f'./resources/{openapi_spec_filename}#/paths/{ref_path}/{method}',
            'x-fern-sdk-group-name': group_name,
            'x-fern-sdk-method-name': get_method_name(method, url),
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


def main():
    overrides_path = str(REPO_ROOT_PATH / 'fern' / 'openapi' / 'overrides.yaml')
    with open(overrides_path, 'r') as f:
        overrides = YAML_CLIENT.load(f) or {}
    existing_urls = get_urls_from_spec(overrides)

    urls_by_filename = get_all_urls_by_filename()
    new_entries = {}
    for filename, urls in urls_by_filename.items():
        for url in urls:
            if url not in existing_urls:
                new_entries[url] = create_override_entries(url, filename)
    
    if new_entries:
        print(f"Adding {len(new_entries)} new entries to overrides.yaml...")

        overrides['paths'] = overrides.get('paths', {})
        for path, entry in new_entries.items():
            if path not in overrides['paths']:
                overrides['paths'][path] = entry

        with open(overrides_path, 'w') as f:
            YAML_CLIENT.dump(overrides, f)

        print("Done!")
    else:
        print("No new entries to add.")


if __name__ == '__main__':
    main()
