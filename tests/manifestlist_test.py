import copy
import json
from image.manifestlistentry    import  ContainerImageManifestListEntry
from image.containerimage       import  ContainerImageManifestList
from image.manifest             import  ContainerImageManifest
from tests.registryclientmock   import  REDHAT_MANIFEST_LIST_EXAMPLE, \
                                        REDHAT_AMD64_MANIFEST, \
                                        REDHAT_ARM64_MANIFEST, \
                                        REDHAT_PPC64LE_MANIFEST, \
                                        REDHAT_S390X_MANIFEST, \
                                        MOCK_IMAGE_NAME, \
                                        MOCK_REGISTRY_CREDS, \
                                        mock_get_manifest

# An example manifest list from the CNCF manifest v2s2 spec
CNCF_MANIFEST_LIST_EXAMPLE = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
    "manifests": [
        {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "digest": "sha256:e692418e4cbaf90ca69d05a66403747baa33ee08806650b51fab815ad7fc331f",
            "size": 7143,
            "platform": {
                "architecture": "ppc64le",
                "os": "linux"
            }
        },
        {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "digest": "sha256:5b0bcabd1ed22e9fb1310cf6c2dec7cdef19f0ad69efa1f392e94a4333501270",
            "size": 7682,
            "platform": {
                "architecture": "amd64",
                "os": "linux",
                "features": [
                    "sse4"
                ]
            }
        }
    ]
}

"""
ContainerImageManifest tests

Unit tests for the ContainerImageManifest class
"""
def test_container_image_manifest_list_get_entries():
    # Ensure entries match expected typing and length
    manifest_list = ContainerImageManifestList(
        copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
    )
    entries = manifest_list.get_entries()
    assert isinstance(entries, list)
    assert len(entries) == 2
    assert isinstance(entries[0], ContainerImageManifestListEntry)
    assert isinstance(entries[1], ContainerImageManifestListEntry)

def test_container_image_manifest_list_get_manifests(mocker):
    # Mock the ContainerImageRegistryClient.get_manifest function which is
    # called in the implementation of ContainerImageManifestList.get_size
    mocker.patch(
        "image.containerimage.ContainerImageRegistryClient.get_manifest",
        mock_get_manifest
    )
    manifest_list = ContainerImageManifestList(
        copy.deepcopy(REDHAT_MANIFEST_LIST_EXAMPLE)
    )
    manifests = manifest_list.get_manifests(
        MOCK_IMAGE_NAME, MOCK_REGISTRY_CREDS
    )
    expected_manifests = [
        ContainerImageManifest(REDHAT_AMD64_MANIFEST),
        ContainerImageManifest(REDHAT_ARM64_MANIFEST),
        ContainerImageManifest(REDHAT_PPC64LE_MANIFEST),
        ContainerImageManifest(REDHAT_S390X_MANIFEST)
    ]
    assert json.dumps(manifests) == json.dumps(expected_manifests)
    assert isinstance(manifests[0], ContainerImageManifest)
    assert isinstance(manifests[1], ContainerImageManifest)
    assert isinstance(manifests[2], ContainerImageManifest)
    assert isinstance(manifests[3], ContainerImageManifest)

def test_container_image_manifest_list_get_size(mocker):
    # Mock the ContainerImageRegistryClient.get_manifest function which is
    # called in the implementation of ContainerImageManifestList.get_size
    mocker.patch(
        "image.containerimage.ContainerImageRegistryClient.get_manifest",
        mock_get_manifest
    )
    manifest_list = ContainerImageManifestList(
        copy.deepcopy(REDHAT_MANIFEST_LIST_EXAMPLE)
    )
    size = manifest_list.get_size(MOCK_IMAGE_NAME, MOCK_REGISTRY_CREDS)
    expected_size = REDHAT_MANIFEST_LIST_EXAMPLE["manifests"][0]["size"] + \
                    REDHAT_MANIFEST_LIST_EXAMPLE["manifests"][1]["size"] + \
                    REDHAT_MANIFEST_LIST_EXAMPLE["manifests"][2]["size"] + \
                    REDHAT_MANIFEST_LIST_EXAMPLE["manifests"][3]["size"] + \
                    REDHAT_AMD64_MANIFEST["config"]["size"] + \
                    REDHAT_AMD64_MANIFEST["layers"][0]["size"] + \
                    REDHAT_ARM64_MANIFEST["config"]["size"] + \
                    REDHAT_ARM64_MANIFEST["layers"][0]["size"] + \
                    REDHAT_PPC64LE_MANIFEST["config"]["size"] + \
                    REDHAT_PPC64LE_MANIFEST["layers"][0]["size"] + \
                    REDHAT_S390X_MANIFEST["config"]["size"] + \
                    REDHAT_S390X_MANIFEST["layers"][0]["size"]
    assert size == expected_size

def test_container_image_manifest_list_to_string():
    # Ensure stringified manifest list matches expected string
    manifest_list_str = json.dumps(
        CNCF_MANIFEST_LIST_EXAMPLE, indent=3, sort_keys=False
    )
    manifest_list = ContainerImageManifestList(CNCF_MANIFEST_LIST_EXAMPLE)
    assert str(manifest_list) == manifest_list_str

def test_container_image_manifest_to_json():
    # Ensure JSONified manifest list matches expected JSON conversion
    manifest_list = ContainerImageManifestList(CNCF_MANIFEST_LIST_EXAMPLE)
    assert json.dumps(manifest_list) == json.dumps(CNCF_MANIFEST_LIST_EXAMPLE)
