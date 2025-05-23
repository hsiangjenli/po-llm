import shutil

import emoji
import toml

shutil.copyfile("../../CHANGELOG.md", "CHANGELOG.md")


def emojize_changelog(path="CHANGELOG.md", output_path="CHANGELOG.md"):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    content = emoji.emojize(content, language="alias")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


emojize_changelog()

# Read the pyproject.toml file
with open("../../pyproject.toml", "r") as f:
    pyproject = toml.load(f)

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "python-package-template"
copyright = "2025, Hsiang-Jen Li"
author = "Hsiang-Jen Li"
release = pyproject["project"]["version"]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.graphviz",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinxcontrib.autodoc_pydantic",
    "nbsphinx",
    "sphinx_simplepdf",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_css_files = [
    "css/custom.css",
]

# Options for autodoc extension ------------------------------------------------------------------ #
pygments_style = "sphinx"
autodoc_pydantic_model_show_json = False
autodoc_pydantic_settings_show_json = False
autodoc_mock_imports = [
    "polib",
    "openai",
    "pandas",
    "lxml",
    "html5lib",
    "bs4",
    "requests",
    "playwright",
    "typer",
    "tqdm",
]
