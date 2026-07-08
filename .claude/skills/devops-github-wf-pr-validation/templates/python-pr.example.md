# Python PR workflow example

Project: Python application using `pyproject.toml`.

```yaml
name: PR Tests

on:
  pull_request:
    branches:
      - master
      - develop

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      src: ${{ steps.filter.outputs.src }}
      tests: ${{ steps.filter.outputs.tests }}
      workflow: ${{ steps.filter.outputs.workflow }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            src:
              - 'src/**'
            tests:
              - 'tests/**'
            workflow:
              - '.github/workflows/pr.yml'

  version-check:
    needs: changes
    if: github.base_ref == 'master' && (needs.changes.outputs.src == 'true' || needs.changes.outputs.workflow == 'true')
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install packaging
        run: pip install packaging

      - name: Check version bump in pyproject.toml
        run: |
          python << 'PY'
          import subprocess
          import sys
          import tomllib
          from packaging.version import Version

          def get_version(ref):
              if ref is None:
                  with open("pyproject.toml", "rb") as f:
                      data = tomllib.load(f)
              else:
                  out = subprocess.run(
                      ["git", "show", f"{ref}:pyproject.toml"],
                      capture_output=True, text=True, check=True,
                  )
                  data = tomllib.loads(out.stdout)
              return Version(data["project"]["version"])

          base_ref = f"origin/${{ github.base_ref }}"
          base_version = get_version(base_ref)
          pr_version = get_version(None)

          print(f"Base version: {base_version}")
          print(f"PR version: {pr_version}")

          if pr_version <= base_version:
              print("ERROR: version in pyproject.toml must be increased when src or workflow changes")
              sys.exit(1)

          print("Version was increased")
          PY

  test:
    needs: changes
    if: needs.changes.outputs.src == 'true' || needs.changes.outputs.tests == 'true'
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest]
        python-version: ['3.10', '3.11', '3.12', '3.13']
        include:
          - os: windows-latest
            python-version: '3.11'

    steps:
      - name: Enable Git long paths
        if: runner.os == 'Windows'
        run: git config --global core.longpaths true

      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: pytest -v
```
