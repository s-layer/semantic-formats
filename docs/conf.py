# -- Project metadata -------------------------------------------------------

project = "s-layer-semantic-formats"
author = "Anentropic"
copyright = "2026, Anentropic"

# -- Path exclusions ----------------------------------------------------------

exclude_patterns = ["_build", ".venv"]

# -- Extensions --------------------------------------------------------------

extensions = [
    "autoapi.extension",
    "sphinx.ext.napoleon",
    "sphinx_design",
    "sphinx.ext.githubpages",
    "myst_parser",
]

# -- MyST parser -------------------------------------------------------------

myst_heading_anchors = 3
suppress_warnings = ["myst.header"]

# -- AutoAPI -----------------------------------------------------------------

autoapi_type = "python"
autoapi_dirs = ["../src"]
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
    "nav_links": [
        {"title": "Overview", "url": "index"},
        {"title": "Release notes", "url": "changelog"},
    ],
}
html_css_files = [
    "css/s-layer.css",
]

html_static_path = ["_static"]
templates_path = ["_templates"]
