import json
import os
from typing                 import  Any, Dict, Type, Union
from image.v2s2             import  ContainerImageManifestV2S2
from image.containerimage   import  ContainerImage
from image.config           import  ContainerImageConfig
from image.descriptor       import  ContainerImageDescriptor

"""
ContainerImageRegistryClient mocks

Mock functions & constants for interacting with the distribution registry API
"""

# Get the directory of this file to load the JSON schemas from files
WORKDIR = os.path.dirname(os.path.realpath(__file__))

def _load_mock_manifest(path: str) -> Dict[str, Any]:
    """
    Helper function for loading mock manifests
    """
    mock_manifest_dict = {}
    with open(path) as mock_manifest_file:
        mock_manifest_dict = json.load(mock_manifest_file)
    return mock_manifest_dict

# An example manifest list from RedHat UBI 9
REDHAT_MANIFEST_LIST_EXAMPLE = _load_mock_manifest(
    f"{WORKDIR}/mock/manifest-lists/redhat-manifest-list.json"
)

# A duplicate of the above, but with one manifest image changed
REDHAT_MANIFEST_LIST_EXAMPLE_DUP = _load_mock_manifest(
    f"{WORKDIR}/mock/manifest-lists/redhat-manifest-list-dup.json"
)

# The manifests for each of the arch manifests in the above UBI9 manifest list
REDHAT_AMD64_MANIFEST = _load_mock_manifest(
    f"{WORKDIR}/mock/manifests/redhat-amd64-manifest.json"
)
REDHAT_ARM64_MANIFEST = _load_mock_manifest(
    f"{WORKDIR}/mock/manifests/redhat-arm64-manifest.json"
)
REDHAT_PPC64LE_MANIFEST = _load_mock_manifest(
    f"{WORKDIR}/mock/manifests/redhat-ppc64le-manifest.json"
)
REDHAT_S390X_MANIFEST = _load_mock_manifest(
    f"{WORKDIR}/mock/manifests/redhat-s390x-manifest.json"
)

# The manifest of the one manifest image changed in the above manifest list dup
REDHAT_AMD64_MANIFEST_DUP = _load_mock_manifest(
    f"{WORKDIR}/mock/manifests/redhat-amd64-manifest-dup.json"
)

# An example OCI image index with attestation manifests
ATTESTATION_MANIFEST_LIST_EXAMPLE = _load_mock_manifest(
    f"{WORKDIR}/mock/manifest-lists/attestation-manifest-list.json"
)

# The manifests for each of the arch manifests in the above attestation index
ATTESTATION_AMD64_MANIFEST = _load_mock_manifest(
    f"{WORKDIR}/mock/manifests/attestation-amd64-manifest.json"
)
ATTESTATION_S390X_MANIFEST = _load_mock_manifest(
    f"{WORKDIR}/mock/manifests/attestation-s390x-manifest.json"
)
ATTESTATION_AMD64_ATTESTATION_MANIFEST = _load_mock_manifest(
    f"{WORKDIR}/mock/manifests/attestation-amd64-attestation-manifest.json"
)
ATTESTATION_S390X_ATTESTATION_MANIFEST = _load_mock_manifest(
    f"{WORKDIR}/mock/manifests/attestation-s390x-attestation-manifest.json"
)

# An example container image config
MOCK_CONFIG = _load_mock_manifest(
    f"{WORKDIR}/mock/configs/config.json"
)

# Mock an image name
MOCK_IMAGE_NAME = "this.is/my/registry/and-my-image"

# Mock an image tag list response
MOCK_TAG_LIST_RESPONSE = {
    "name": MOCK_IMAGE_NAME,
    "tags": [
        "latest",
        "latest-dup",
        "latest-attestation"
    ]
}

# Mock image registry creds for the above image name mock
MOCK_REGISTRY_CREDS = {
    "auths": {
        "this.is": {
            "auth": "dGVzdHVzZXI6dGVzdHBhc3M=",
            "username": "testuser",
            "password": "testpass",
            "email": "testuser@test.com"
        }
    }
}

# Mock the ContainerImageRegistryClient.get_manifest function
def mock_get_manifest(
        ref_or_img: Union[str, ContainerImage],
        auth: Dict[str, Any],
        http: bool=False,
        skip_verify: bool=False
    ) -> Type[
        ContainerImageManifestV2S2
    ]:
    """
    Mocks the ContainerImageRegistryClient.get_manifest function

    Args:
    ref (Union[str, ContainerImage]): The image reference
    auth (Dict[str, Any]): The auth for the reference

    Returns:
    Type[ContainerImageManifest]: The manifest
    """
    if str(ref_or_img) == f"{MOCK_IMAGE_NAME}@" + \
        "sha256:f5d2c6a1e0c86e4234ea601552dbabb4ced0e013a1efcbfb439f1f6a7a9275b0":
        return json.dumps(REDHAT_AMD64_MANIFEST).encode('utf-8')
    elif str(ref_or_img) == f"{MOCK_IMAGE_NAME}@" + \
        "sha256:96f4394d39e6edb69ca51f000f3e7dfb62990f55868134cfd83c82177651e848":
        return json.dumps(REDHAT_ARM64_MANIFEST).encode('utf-8')
    elif str(ref_or_img) == f"{MOCK_IMAGE_NAME}@" + \
        "sha256:39c59a30e3ecae689c23b27e54a81e03d9a5db22d11890edaf6bb16bac783e8b":
        return json.dumps(REDHAT_PPC64LE_MANIFEST).encode('utf-8')
    elif str(ref_or_img) == f"{MOCK_IMAGE_NAME}@" + \
        "sha256:d187f310724694b1daae2f99f6f86ae05b573eed6826fa40d4233e76bd07312e":
        return json.dumps(REDHAT_S390X_MANIFEST).encode('utf-8')
    elif str(ref_or_img) == f"{MOCK_IMAGE_NAME}@" + \
        "sha256:058913b247adb61e488c14ee8ab0f5c8022fd08dc945a9d900a02f32effde5c2":
        return json.dumps(REDHAT_AMD64_MANIFEST_DUP).encode('utf-8')
    elif str(ref_or_img) == f"{MOCK_IMAGE_NAME}:latest":
        return json.dumps(REDHAT_MANIFEST_LIST_EXAMPLE).encode('utf-8')
    elif str(ref_or_img) == f"{MOCK_IMAGE_NAME}:latest-dup":
        return json.dumps(REDHAT_MANIFEST_LIST_EXAMPLE_DUP).encode('utf-8')
    elif str(ref_or_img) == f"{MOCK_IMAGE_NAME}:latest-attestation":
        return json.dumps(ATTESTATION_MANIFEST_LIST_EXAMPLE).encode('utf-8')
    elif str(ref_or_img) == f"{MOCK_IMAGE_NAME}@" + \
        "sha256:aa0304d8024783de8537f7e776f33deb57820b853849355b9cbc2a618511521d":
        return json.dumps(ATTESTATION_AMD64_MANIFEST).encode('utf-8')
    elif str(ref_or_img) == f"{MOCK_IMAGE_NAME}@" + \
        "sha256:d06586cc1e3a1f21052c2747237c2394917c8ab7d2e10c284ab975196eff0084":
        return json.dumps(ATTESTATION_S390X_MANIFEST).encode('utf-8')
    elif str(ref_or_img) == f"{MOCK_IMAGE_NAME}@" + \
        "sha256:171dcd736979ede2a044022fab58b6fa558e5ea9b1486d655d213c688af2c592":
        return json.dumps(ATTESTATION_AMD64_ATTESTATION_MANIFEST).encode('utf-8')
    elif str(ref_or_img) == f"{MOCK_IMAGE_NAME}@" + \
        "sha256:61d78e5bc2772b75b97fc80f1e796594da4c5421957872be9302b39b1cf155b8":
        return json.dumps(ATTESTATION_S390X_ATTESTATION_MANIFEST).encode('utf-8')
    else:
        raise Exception(f"Unmocked reference: {ref_or_img}")

# Mock the ContainerImageRegistryClient.get_config function
def mock_get_config(
        ref_or_img: Union[str, ContainerImage],
        config_desc: ContainerImageDescriptor,
        auth: Dict[str, Any],
        http: bool=False,
        skip_verify: bool=False
    ) -> Dict[str, Any]:
    """
    Mocks the ContainerImageRegistryClient.get_config function

    Args:
    ref (Union[str, ContainerImage]): The image reference
    auth (Dict[str, Any]): The auth for the reference

    Returns:
    ContainerImageConfig: The container image config
    """
    if str(ref_or_img) == f"{MOCK_IMAGE_NAME}:latest":
        return MOCK_CONFIG
    else:
        raise Exception(f"Unmocked reference: {ref_or_img}")

def mock_get_digest(
        ref_or_img: Union[str, ContainerImage],
        auth: Dict[str, Any],
        http: bool=False,
        skip_verify: bool=False
    ) -> str:
    """
    Mocks the ContainerImageRegistryClient.get_digest function

    Args:
    ref (Union[str, ContainerImage]): The image reference
    auth (Dict[str, Any]): The auth for the reference

    Returns:
    str: The digest
    """
    if str(ref_or_img) == f"{MOCK_IMAGE_NAME}:latest":
        return "sha256:8f74ffc756f871ee9037fb8e0c3cd9c5cb54e92e014f92d771ab8e6bf925f372"
    else:
        raise Exception(f"Unmocked reference: {ref_or_img}")

def mock_list_tags(
        ref_or_img: Union[str, ContainerImage],
        auth: Dict[str, Any],
        http: bool=False,
        skip_verify: bool=False
    ) -> Dict[str, Any]:
    """
    Mocks the ContainerImageRegistryClient.list_tags function

    Args:
    ref (Union[str, ContainerImage]): The image reference
    auth (Dict[str, Any]): The auth for the reference

    Returns:
    Dict[str, Any]: The tag list response
    """
    return MOCK_TAG_LIST_RESPONSE
