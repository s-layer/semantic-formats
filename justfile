default:
    @just --list

# Set up the agent cli with GSD and skills based on agent name [claude|opencode]
setup-agent-cli agent="claude":
    @selected_agent="{{agent}}"; \
    selected_agent="${selected_agent#agent=}"; \
    case "${selected_agent}" in \
        claude) gsd_name="claude"; skills_name="claude-code" ;; \
        opencode) gsd_name="opencode"; skills_name="opencode" ;; \
        *) echo "Invalid agent '${selected_agent}'. Expected 'claude' or 'opencode'."; exit 1 ;; \
    esac; \
    npx @opengsd/gsd-core --"${gsd_name}" --local; \
    npx skills add abatilo/vimrc/plugins/abatilo-core/skills/diataxis-documentation -a "${skills_name}" -y; \
    npx skills add blader/humanizer -a "${skills_name}" -y

# Build the docs site
docs-build:
    uvx git-cliff -o CHANGELOG.md
    uv run sphinx-build -b html docs docs/_build/html

# Serve the docs dev server with live-reload (default port 8000)
docs-serve port="8000":
    uvx git-cliff -o CHANGELOG.md
    uv run sphinx-autobuild docs docs/_build/html --port {{port}}

# Run the test suite
test:
    uv run pytest

# Run the property tests with more examples, as CI does
test-ci:
    uv run pytest --hypothesis-profile=ci

# Regenerate the committed JSON Schema from the models
schema:
    uv run python scripts/regen_schema.py

# Fail if the committed JSON Schema differs from the models
schema-check:
    uv run python scripts/regen_schema.py --check
