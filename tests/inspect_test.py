import copy
import json
import os
from image.containerimageinspect import ContainerImageInspect
from typing import Dict, Any

# Get the directory of this file to load the JSON schemas from files
WORKDIR = os.path.dirname(os.path.realpath(__file__))

def _load_json(path: str) -> Dict[str, Any]:
    """
    Helper function for loading mock manifests
    """
    mock_manifest_dict = {}
    with open(path) as mock_manifest_file:
        mock_manifest_dict = json.load(mock_manifest_file)
    return mock_manifest_dict

EXAMPLE_INSPECT = _load_json(f"{WORKDIR}/mock/inspect/inspect.json")

def test_load_skopeo_inspect_output():
    """
    Ensure we can load example output from skopeo inspect
    """
    exc = None
    try:
        inspect = ContainerImageInspect(EXAMPLE_INSPECT)
    except Exception as e:
        exc = e
    assert exc == None
    assert isinstance(inspect, ContainerImageInspect)

def test_load_inspect_no_labels():
    """
    Ensure we can load an inspect output with null labels
    """
    example = copy.deepcopy(EXAMPLE_INSPECT)
    example["Labels"] = None
    exc = None
    try:
        inspect = ContainerImageInspect(example)
    except Exception as e:
        exc = e
    assert exc == None
    assert isinstance(inspect, ContainerImageInspect)

def test_load_inspect_invalid_name():
    """
    Ensure we do not load inspect output with invalid image name
    """
    # Invalid name should not work
    example = copy.deepcopy(EXAMPLE_INSPECT)
    example["Name"] = "Not a container image"
    exc = None
    try:
        inspect = ContainerImageInspect(example)
    except Exception as e:
        exc = e
    assert exc != None

    # Empty name should work
    example["Name"] = ""
    exc = None
    try:
        inspect = ContainerImageInspect(example)
    except Exception as e:
        exc = e
    assert exc == None
    assert isinstance(inspect, ContainerImageInspect)

def test_load_inspect_invalid_digest():
    """
    Ensure we do not load inspect output with invalid digests
    """
    # Top-level digest
    example = copy.deepcopy(EXAMPLE_INSPECT)
    example["Digest"] = "notadigest"
    exc = None
    try:
        inspect = ContainerImageInspect(example)
    except Exception as e:
        exc = e
    assert exc != None

    # Layer digest(s)
    example = copy.deepcopy(EXAMPLE_INSPECT)
    example["Layers"][0] = "notadigest"
    exc = None
    try:
        inspect = ContainerImageInspect(example)
    except Exception as e:
        exc = e
    assert exc != None

    # LayersData digest(s)
    example = copy.deepcopy(EXAMPLE_INSPECT)
    example["LayersData"][0]["Digest"] = "notadigest"
    exc = None
    try:
        inspect = ContainerImageInspect(example)
    except Exception as e:
        exc = e
    assert exc != None
