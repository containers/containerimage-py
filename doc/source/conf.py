######
# Hack
#
# Make sibling modules visible to this nested executable
import os, sys
sys.path.insert(0, os.path.abspath('../../'))
# End Hack
######

print(sys.path)

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'containerimage-py'
copyright = '2025, IBM Corporation'
author = 'Ethan Balcik'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon'
]

napoleon_google_docstring = True
autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = ['tests.rst']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_favicon = '_static/container-image-py-favicon.png'
html_static_path = ['_static']
