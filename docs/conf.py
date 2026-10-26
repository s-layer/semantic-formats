# -- Project metadata -------------------------------------------------------

project = "s-layer-semantic-formats"
author = "Anentropic"
copyright = "2026, Anentropic"

# -- Path exclusions ----------------------------------------------------------

exclude_patterns = ["_build", ".venv"]

# -- Extensions --------------------------------------------------------------

extensions = [
    "autoapi.extension",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_design",
    "sphinx.ext.githubpages",
    "myst_parser",
]

# -- Napoleon (Google docstring style) ---------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_ivar = True

# -- Intersphinx (cross-project linking) -------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
    "jsonschema": ("https://python-jsonschema.readthedocs.io/en/stable", None),
}

# -- MyST parser -------------------------------------------------------------

myst_heading_anchors = 3
suppress_warnings = ["myst.header"]

# -- AutoAPI -----------------------------------------------------------------

autoapi_type = "python"
autoapi_dirs = ["../src"]
autoapi_root = "reference/api"
autoapi_add_toctree_entry = False
# "class", not "both": the models have no __init__ of their own, so "both" repeats
# pydantic's BaseModel.__init__ docstring on every class.
autoapi_python_class_content = "class"
autoapi_member_order = "bysource"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]

# -- Shibuya theme -----------------------------------------------------------

html_theme = "shibuya"
html_theme_options = {
    "accent_color": "orange",
    "color_mode": "auto",
    "github_url": "https://github.com/s-layer/semantic-formats",
    "toctree_maxdepth": 3,
    "toctree_titles_only": True,
    # nav_links are plain URLs, not checked by the build: update them when pages move.
    "nav_links": [
        {"title": "Overview", "url": "index"},
        {
            "title": "Tutorials",
            "url": "tutorials/index",
            "children": [
                {
                    "title": "Check the s_layer blocks in a dbt file",
                    "url": "tutorials/first-blocks",
                    "summary": "Write, check and fix your first blocks",
                },
            ],
        },
        {
            "title": "How-to guides",
            "url": "how-to/index",
            "children": [
                {
                    "title": "Write an s_layer block in dbt YAML",
                    "url": "how-to/write-a-block",
                    "summary": "Kinds, required keys and optional hints",
                },
                {
                    "title": "Validate a block",
                    "url": "how-to/validate-a-block",
                    "summary": "Check blocks and report every problem",
                },
                {
                    "title": "Compare blocks",
                    "url": "how-to/compare-blocks",
                    "summary": "Equality, storage and drift detection",
                },
                {
                    "title": "Round-trip warehouse tags",
                    "url": "how-to/round-trip-tags",
                    "summary": "Write and read S_LAYER_SPEC",
                },
                {
                    "title": "Use the JSON Schema",
                    "url": "how-to/use-the-json-schema",
                    "summary": "Check block shape in any tool",
                },
            ],
        },
        {
            "title": "Explanation",
            "url": "explanation/index",
            "children": [
                {
                    "title": "Understanding the s_layer block",
                    "url": "explanation/the-block",
                    "summary": "Sections, kinds and member types",
                },
                {
                    "title": "The normal form and equality",
                    "url": "explanation/normal-form",
                    "summary": "Defaults, equality and the tag payload",
                },
                {
                    "title": "Design decisions",
                    "url": "explanation/design-decisions",
                    "summary": "The rules where the design doc is silent",
                },
            ],
        },
        {"title": "Reference", "url": "reference/index"},
        {"title": "Release notes", "url": "changelog"},
    ],
}
html_css_files = [
    "css/s-layer.css",
]

html_static_path = ["_static"]
templates_path = ["_templates"]
