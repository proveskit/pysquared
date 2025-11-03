#!/usr/bin/env python3
"""
Add PySquared dependencies to CircuitPython frozen modules.

This script reads the dependencies from circuitpython-workspaces/flight-software/pyproject.toml
and helps set up the corresponding repositories as git submodules in the CircuitPython frozen/ directory.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def parse_pyproject_dependencies(pyproject_path: Path) -> list[dict]:
    """Parse dependencies from pyproject.toml."""
    dependencies = []
    
    with open(pyproject_path) as f:
        content = f.read()
    
    # Find the dependencies section
    deps_section = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if not deps_section:
        print("Error: Could not find dependencies section in pyproject.toml")
        return []
    
    deps_text = deps_section.group(1)
    
    # Parse each dependency line
    for line in deps_text.split('\n'):
        line = line.strip().strip(',').strip('"')
        if not line or line.startswith('#'):
            continue
        
        dep_info = {}
        
        # Check if it's a git dependency
        if '@' in line and 'git+' in line:
            # Format: "package @ git+https://github.com/org/repo@version"
            # First split on ' @ ' to separate package from URL
            parts = line.split(' @ ', 1)
            package_name = parts[0].strip()
            git_url = parts[1].strip() if len(parts) > 1 else ''
            
            if git_url.startswith('git+'):
                git_url = git_url[4:]  # Remove 'git+' prefix
            
            # Now split URL and version on last '@'
            if '@' in git_url:
                url, version = git_url.rsplit('@', 1)
                dep_info['name'] = package_name
                dep_info['url'] = url
                dep_info['version'] = version
                dep_info['type'] = 'git'
        elif '==' in line:
            # Format: "package==version"
            package_name, version = line.split('==')
            package_name = package_name.strip()
            version = version.strip()
            
            # Convert PyPI package name to GitHub repo name
            # adafruit-circuitpython-ina219 -> Adafruit_CircuitPython_INA219
            if package_name.startswith('adafruit-circuitpython-'):
                lib_name = package_name.replace('adafruit-circuitpython-', '')
                lib_name_parts = lib_name.split('-')
                lib_name_camel = ''.join(p.upper() if len(p) <= 3 else p.capitalize() 
                                        for p in lib_name_parts)
                repo_name = f"Adafruit_CircuitPython_{lib_name_camel}"
                url = f"https://github.com/adafruit/{repo_name}"
                
                dep_info['name'] = package_name
                dep_info['url'] = url
                dep_info['version'] = version
                dep_info['type'] = 'pypi'
        
        if dep_info:
            dependencies.append(dep_info)
    
    return dependencies


def add_submodule(frozen_dir: Path, dep: dict, dry_run: bool = False) -> bool:
    """Add a dependency as a git submodule."""
    # Determine directory name
    if dep['type'] == 'git':
        # Extract repo name from URL
        repo_name = dep['url'].rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
    else:
        # Use the repo name from URL
        repo_name = dep['url'].rstrip('/').split('/')[-1]
    
    submodule_path = frozen_dir / repo_name
    
    # Check if submodule already exists
    if submodule_path.exists():
        print(f"  ⚠️  {repo_name} already exists, skipping")
        return True
    
    print(f"  📦 Adding {dep['name']} ({repo_name})")
    print(f"     URL: {dep['url']}")
    print(f"     Version: {dep['version']}")
    
    if dry_run:
        print("     [DRY RUN - would add submodule]")
        return True
    
    try:
        # Add as git submodule
        cmd = ['git', 'submodule', 'add', dep['url'], str(submodule_path)]
        subprocess.run(cmd, check=True, cwd=frozen_dir.parent, 
                      capture_output=True, text=True)
        
        # Checkout specific version
        subprocess.run(['git', 'checkout', dep['version']], 
                      check=True, cwd=submodule_path,
                      capture_output=True, text=True)
        
        print(f"     ✅ Added successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"     ❌ Failed to add: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Add PySquared dependencies to CircuitPython frozen modules'
    )
    parser.add_argument(
        '--pyproject',
        type=Path,
        default=Path(__file__).parent.parent / 'circuitpython-workspaces' / 
                'flight-software' / 'pyproject.toml',
        help='Path to pyproject.toml (default: ../circuitpython-workspaces/flight-software/pyproject.toml)'
    )
    parser.add_argument(
        '--frozen-dir',
        type=Path,
        default=Path(__file__).parent / 'circuitpython' / 'frozen',
        help='Path to CircuitPython frozen directory (default: ./circuitpython/frozen)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List dependencies without adding them'
    )
    
    args = parser.parse_args()
    
    # Validate paths
    if not args.pyproject.exists():
        print(f"Error: pyproject.toml not found at {args.pyproject}")
        sys.exit(1)
    
    if not args.list and not args.frozen_dir.parent.exists():
        print(f"Error: CircuitPython directory not found at {args.frozen_dir.parent}")
        print("Run 'make setup' first to clone CircuitPython")
        sys.exit(1)
    
    # Parse dependencies
    print(f"📖 Reading dependencies from {args.pyproject}")
    dependencies = parse_pyproject_dependencies(args.pyproject)
    
    if not dependencies:
        print("No dependencies found")
        sys.exit(1)
    
    print(f"\n✨ Found {len(dependencies)} dependencies\n")
    
    # List mode - just show dependencies
    if args.list:
        for dep in dependencies:
            print(f"  • {dep['name']}")
            print(f"    URL: {dep['url']}")
            print(f"    Version: {dep['version']}")
            print(f"    Type: {dep['type']}")
            print()
        return
    
    # Create frozen directory if it doesn't exist
    args.frozen_dir.mkdir(parents=True, exist_ok=True)
    
    # Add each dependency
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    success_count = 0
    for dep in dependencies:
        if add_submodule(args.frozen_dir, dep, args.dry_run):
            success_count += 1
        print()
    
    print(f"\n{'📋 Would add' if args.dry_run else '✅ Added'} {success_count}/{len(dependencies)} dependencies")
    
    if not args.dry_run and success_count > 0:
        print("\n⚠️  Don't forget to:")
        print("   1. Commit the new submodules to git")
        print("   2. Update board mpconfigboard.mk files to include frozen modules")
        print("   3. Build firmware with: make firmware BOARD=<board>")


if __name__ == '__main__':
    main()
