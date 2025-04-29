"""
Template files for project scaffolding.
"""
import os
import json

# Directory containing the template files
TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_template_path(filename):
    """Get the absolute path to a template file."""
    return os.path.join(TEMPLATE_DIR, filename)

def get_template_content(filename):
    """Get the content of a template file."""
    with open(get_template_path(filename), 'r') as f:
        return f.read()

def get_sample_dataset():
    """Get the sample dataset as a Python object."""
    with open(get_template_path('sample_dataset.json'), 'r') as f:
        return json.load(f)
