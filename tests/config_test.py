import copy
import json
import os
from image.config import ContainerImageConfig
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

EXAMPLE_CONFIG = _load_json(f"{WORKDIR}/mock/configs/config.json")

def test_load_config():
    """
    Ensure we can load a config from the OCI image spec
    """
    exc = None
    try:
        inspect = ContainerImageConfig(EXAMPLE_CONFIG)
    except Exception as e:
        exc = e
    assert exc == None
    assert isinstance(inspect, ContainerImageConfig)

def test_load_config_no_platform():
    """
    Ensure the config fails to load if no OS or arch given
    """
    # No os
    conf = copy.deepcopy(EXAMPLE_CONFIG)
    conf.pop("os")
    exc = None
    try:
        config = ContainerImageConfig(conf)
    except Exception as e:
        exc = e
    assert exc != None

    # No architecture
    conf = copy.deepcopy(EXAMPLE_CONFIG)
    conf.pop("architecture")
    exc = None
    try:
        config = ContainerImageConfig(conf)
    except Exception as e:
        exc = e
    assert exc != None

def test_load_config_no_rootfs():
    """
    Ensure the config fails to load if no rootfs property given
    """
    # No rootfs property at all
    conf = copy.deepcopy(EXAMPLE_CONFIG)
    conf.pop("rootfs")
    exc = None
    try:
        config = ContainerImageConfig(conf)
    except Exception as e:
        exc = e
    assert exc != None

    # No type in rootfs property
    conf = copy.deepcopy(EXAMPLE_CONFIG)
    conf["rootfs"].pop("type")
    exc = None
    try:
        config = ContainerImageConfig(conf)
    except Exception as e:
        exc = e
    assert exc != None

    # No diff_ids in rootfs property
    conf = copy.deepcopy(EXAMPLE_CONFIG)
    conf["rootfs"].pop("diff_ids")
    exc = None
    try:
        config = ContainerImageConfig(conf)
    except Exception as e:
        exc = e
    assert exc != None
