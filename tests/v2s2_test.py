import copy
import json
from jsonschema                 import  ValidationError
from image.containerimage       import  ContainerImageManifestListV2S2
from image.manifest             import  ContainerImageManifest
from image.manifestlistentry    import  ContainerImageManifestListEntry
from image.v2s2                 import  ContainerImageManifestListEntryV2S2, \
                                        ContainerImageManifestV2S2
from tests.registryclientmock   import  REDHAT_MANIFEST_LIST_EXAMPLE, \
                                        REDHAT_AMD64_MANIFEST, \
                                        REDHAT_ARM64_MANIFEST, \
                                        REDHAT_PPC64LE_MANIFEST, \
                                        REDHAT_S390X_MANIFEST, \
                                        ATTESTATION_MANIFEST_LIST_EXAMPLE, \
                                        MOCK_IMAGE_NAME, \
                                        MOCK_REGISTRY_CREDS, \
                                        mock_get_manifest

# An example manifest from the CNCF manifest v2s2 spec
CNCF_MANIFEST_EXAMPLE = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
    "config": {
        "mediaType": "application/vnd.docker.container.image.v1+json",
        "digest": "sha256:b5b2b2c507a0944348e0303114d8d93aaaa081732b86451d9bce1f432a537bc7",
        "size": 7023
    },
    "layers": [
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "digest": "sha256:e692418e4cbaf90ca69d05a66403747baa33ee08806650b51fab815ad7fc331f",
            "size": 32654
        },
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "digest": "sha256:3c3a4604a545cdc127456d94e421cd355bca5b528f4a9c1905b15da2eb4a4c6b",
            "size": 16724
        },
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "digest": "sha256:ec4b8955958665577945c89419d1af06b5f7636b4ac3da7f12184802ad867736",
            "size": 73109
        }
    ]
}

# Example manifest from the OCI image manifest spec
# Ref: https://github.com/opencontainers/image-spec/blob/v1.0.1/manifest.md
OCI_MANIFEST_EXAMPLE = {
    "schemaVersion": 2,
    "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
        "size": 7023,
        "digest": "sha256:b5b2b2c507a0944348e0303114d8d93aaaa081732b86451d9bce1f432a537bc7"
    },
    "layers": [
        {
            "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
            "size": 32654,
            "digest": "sha256:9834876dcfb05cb167a5c24953eba58c4ac89b1adf57f28f2f9d09af107ee8f0"
        },
        {
            "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
            "size": 16724,
            "digest": "sha256:3c3a4604a545cdc127456d94e421cd355bca5b528f4a9c1905b15da2eb4a4c6b"
        },
        {
            "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
            "size": 73109,
            "digest": "sha256:ec4b8955958665577945c89419d1af06b5f7636b4ac3da7f12184802ad867736"
        }
    ],
    "annotations": {
        "com.example.key1": "value1",
        "com.example.key2": "value2"
    }
}

# An example manifest from RedHat UBI 9
REDHAT_MANIFEST_EXAMPLE = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
    "config": {
        "mediaType": "application/vnd.docker.container.image.v1+json",
        "size": 6236,
        "digest": "sha256:ffc89b04201adf69c0acd4e94297121e623f9d8a47cccb2aa412bc4b991976fb"
    },
    "layers": [
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "size": 37364487,
            "digest": "sha256:9d38740decc88f04976b3123db64216586005286cafbf52d64706fa02375bde9"
        }
    ]
}

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

# An example manifest list entry from the CNCF manifest v2s2 spec
CNCF_MANIFEST_LIST_ENTRY_EXAMPLE = {
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

# An example image index entry following the OCI spec
DOCKER_BUILDX_ATTESTATION_INDEX_ENTRY = {
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "digest": "sha256:61d78e5bc2772b75b97fc80f1e796594da4c5421957872be9302b39b1cf155b8",
    "size": 566,
    "annotations": {
        "vnd.docker.reference.digest": "sha256:d06586cc1e3a1f21052c2747237c2394917c8ab7d2e10c284ab975196eff0084",
        "vnd.docker.reference.type": "attestation-manifest"
    },
    "platform": {
        "architecture": "unknown",
        "os": "unknown"
    }
}

# An example manifest list entry from RedHat UBI 9
REDHAT_MANIFEST_LIST_ENTRY_EXAMPLE = {
    "digest": "sha256:96f4394d39e6edb69ca51f000f3e7dfb62990f55868134cfd83c82177651e848",
    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
    "platform": {
        "architecture": "arm64",
        "os": "linux",
        "variant": "v8"
    },
    "size": 429
}

"""
ContainerImageManifestV2S2 tests

Unit tests for the ContainerImageManifestV2S2 class
"""
def test_container_image_v2s2_manifest_static_validation():
    # Empty dict should be invalid
    empty_dict_valid, err = ContainerImageManifestV2S2.validate_static({})
    assert empty_dict_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Valid CNCF example should be valid
    cncf_example_valid, err = ContainerImageManifestV2S2.validate_static(
        copy.deepcopy(CNCF_MANIFEST_EXAMPLE)
    )
    assert cncf_example_valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # No schemaVersion should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_EXAMPLE)
    cncf_example_mut.pop("schemaVersion")
    no_sv_valid, err = ContainerImageManifestV2S2.validate_static(
        cncf_example_mut
    )
    assert no_sv_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # No mediaType should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_EXAMPLE)
    cncf_example_mut.pop("mediaType")
    no_mt_valid, err = ContainerImageManifestV2S2.validate_static(
        cncf_example_mut
    )
    assert no_mt_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Valid RedHat example should be valid
    rh_example_valid, err = ContainerImageManifestV2S2.validate_static(
        copy.deepcopy(REDHAT_MANIFEST_EXAMPLE)
    )
    assert rh_example_valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # OCI example should be invalid
    oci_example_valid, err = ContainerImageManifestV2S2.validate_static(
        copy.deepcopy(OCI_MANIFEST_EXAMPLE)
    )
    assert oci_example_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

def test_container_image_v2s2_manifest_instantiation():
    # Ensure exception is thrown on instantiation using invalid schema
    exc = None
    try:
        manifest = ContainerImageManifestV2S2(
            json.dumps({}).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure ContainerImageManifestV2S2 is returned when using valid schema
    manifest = ContainerImageManifestV2S2(
        json.dumps(
            copy.deepcopy(CNCF_MANIFEST_EXAMPLE)
        ).encode('utf-8')
    )
    assert isinstance(manifest, ContainerImageManifestV2S2)

    # Ensure generic ContainerImageManifest can be converted into a
    # ContainerImageManifestV2S2
    generic_manifest = ContainerImageManifest(
        json.dumps(
            copy.deepcopy(CNCF_MANIFEST_EXAMPLE)
        ).encode('utf-8')
    )
    manifest = ContainerImageManifestV2S2.from_manifest(
        generic_manifest
    )
    assert isinstance(manifest, ContainerImageManifestV2S2)

def test_container_image_v2s2_manifest_instance_validation():
    # Ensure ContainerImageManifestV2S2 instantiates and is valid post-instantiation
    manifest = ContainerImageManifestV2S2(
        json.dumps(
            copy.deepcopy(CNCF_MANIFEST_EXAMPLE)
        ).encode('utf-8')
    )
    valid, err = manifest.validate()
    assert valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # Ensure if we invalidate a property of the manifest, it's invalid
    manifest.manifest["mediaType"] = 1234
    valid, err = manifest.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest.manifest["mediaType"] = copy.copy(
        CNCF_MANIFEST_EXAMPLE["mediaType"]
    )

    # Ensure if we invalidate a property of the manifest config, it's invalid
    manifest.manifest["config"]["digest"] = "notadigest"
    valid, err = manifest.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest.manifest["config"]["digest"] = copy.copy(
        CNCF_MANIFEST_EXAMPLE["config"]["digest"]
    )

    # Ensure if we invalidate a property of the manifest config, it's invalid
    manifest.manifest["config"]["size"] = "1234"
    valid, err = manifest.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest.manifest["config"]["digest"] = copy.copy(
        CNCF_MANIFEST_EXAMPLE["config"]["size"]
    )

    # Ensure if we invalidate a property of a manifest layer, it's invalid
    manifest.manifest["layers"][0]["digest"] = "notadigest"
    valid, err = manifest.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest.manifest["layers"][0]["digest"] = copy.copy(
        CNCF_MANIFEST_EXAMPLE["layers"][0]["digest"]
    )

    # Ensure if we invalidate a property of a manifest layer, it's invalid
    manifest.manifest["layers"][0]["size"] = "1234"
    valid, err = manifest.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest.manifest["layers"][0]["size"] = copy.copy(
        CNCF_MANIFEST_EXAMPLE["layers"][0]["size"]
    )

"""
ContainerImageManifestListV2S2 tests

Unit tests for the ContainerImageManifestListV2S2 class
"""
def test_container_image_v2s2_manifest_list_static_validation():
    # Empty dict should be invalid
    empty_dict_valid, err = ContainerImageManifestListV2S2.validate_static({})
    assert empty_dict_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Valid CNCF example should be valid
    cncf_example_valid, err = ContainerImageManifestListV2S2.validate_static(
        copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
    )
    assert cncf_example_valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # No schemaVersion should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
    cncf_example_mut.pop("schemaVersion")
    no_sv_valid, err = ContainerImageManifestListV2S2.validate_static(
        cncf_example_mut
    )
    assert no_sv_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # No mediaType should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
    cncf_example_mut.pop("mediaType")
    no_mt_valid, err = ContainerImageManifestListV2S2.validate_static(
        cncf_example_mut
    )
    assert no_mt_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # No manifests should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
    cncf_example_mut.pop("manifests")
    no_mf_valid, err = ContainerImageManifestListV2S2.validate_static(
        cncf_example_mut
    )
    assert no_mf_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Manifest missing digest should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
    cncf_example_mut["manifests"][0].pop("digest")
    no_dig_valid, err = ContainerImageManifestListV2S2.validate_static(
        cncf_example_mut
    )
    assert no_dig_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Manifest with invalid digest should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
    cncf_example_mut["manifests"][0]["digest"] = "notadigest"
    no_dig_valid, err = ContainerImageManifestListV2S2.validate_static(
        cncf_example_mut
    )
    assert no_dig_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Ensure OCI manifest list is invalid
    oci_valid, err = ContainerImageManifestListV2S2.validate_static(
        ATTESTATION_MANIFEST_LIST_EXAMPLE
    )
    assert oci_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

def test_container_image_v2s2_manifest_list_instantiation():
    # Ensure exception is thrown on instantiation using invalid schema
    exc = None
    try:
        manifest_list = ContainerImageManifestListV2S2(
            json.dumps({}).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure ContainerImageManifestListV2S2 is returned when using valid schema
    manifest_list = ContainerImageManifestListV2S2(
        json.dumps(
            copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
        ).encode('utf-8')
    )
    assert isinstance(manifest_list, ContainerImageManifestListV2S2)

def test_container_image_v2s2_manifest_list_instance_validation():
    # Ensure ContainerImageManifestListV2S2 instantiates and is valid post-instantiation
    manifest_list = ContainerImageManifestListV2S2(
        json.dumps(
            copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
        ).encode('utf-8')
    )
    valid, err = manifest_list.validate()
    assert valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # Ensure if we invalidate a property of the manifest, it's invalid
    manifest_list.manifest_list["mediaType"] = 1234
    valid, err = manifest_list.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest_list.manifest_list["mediaType"] = copy.copy(
        CNCF_MANIFEST_LIST_EXAMPLE["mediaType"]
    )

    # Ensure if we drop a property of the manifest, it's invalid
    manifest_list.manifest_list.pop("schemaVersion")
    valid, err = manifest_list.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest_list.manifest_list["schemaVersion"] = copy.copy(
        CNCF_MANIFEST_LIST_EXAMPLE["schemaVersion"]
    )

    # Ensure if we invalidate a property of a manifest entry, it's invalid
    manifest_list.manifest_list["manifests"][0]["digest"] = "notadigest"
    valid, err = manifest_list.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest_list.manifest_list["manifests"][0]["digest"] = copy.copy(
        CNCF_MANIFEST_LIST_EXAMPLE["manifests"][0]["digest"]
    )

def test_container_image_v2s2_manifest_list_get_entries():
    # Ensure entries match expected typing and length
    manifest_list = ContainerImageManifestListV2S2(
        json.dumps(
            copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
        ).encode('utf-8')
    )
    entries = manifest_list.get_v2s2_entries()
    assert isinstance(entries, list)
    assert len(entries) == 2
    assert isinstance(entries[0], ContainerImageManifestListEntryV2S2)
    assert isinstance(entries[1], ContainerImageManifestListEntryV2S2)

    # Ensure if we invalidate a property of a manifest entry, it's invalid
    exc = None
    manifest_list.manifest_list["manifests"][0]["digest"] = "notadigest"
    try:
        entries = manifest_list.get_v2s2_entries()
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

def test_container_image_v2s2_manifest_list_get_manifests(mocker):
    # Mock the ContainerImageRegistryClient.get_manifest function which is
    # called in the implementation of ContainerImageManifestList.get_size
    mocker.patch(
        "image.containerimage.ContainerImageRegistryClient.get_manifest",
        mock_get_manifest
    )
    manifest_list = ContainerImageManifestListV2S2(
        json.dumps(
            copy.deepcopy(REDHAT_MANIFEST_LIST_EXAMPLE)
        ).encode('utf-8')
    )
    manifests = manifest_list.get_v2s2_manifests(
        MOCK_IMAGE_NAME, MOCK_REGISTRY_CREDS
    )
    expected_manifests = [
        ContainerImageManifestV2S2(
            json.dumps(REDHAT_AMD64_MANIFEST).encode('utf-8')
        ),
        ContainerImageManifestV2S2(
            json.dumps(REDHAT_ARM64_MANIFEST).encode('utf-8')
        ),
        ContainerImageManifestV2S2(
            json.dumps(REDHAT_PPC64LE_MANIFEST).encode('utf-8')
        ),
        ContainerImageManifestV2S2(
            json.dumps(REDHAT_S390X_MANIFEST).encode('utf-8')
        )
    ]
    assert json.dumps(manifests) == json.dumps(expected_manifests)

"""
ContainerImageManifestListEntryV2S2 tests

Unit tests for the ContainerImageManifestListEntryV2S2 class
"""
def test_container_image_v2s2_manifest_list_entry_static_validation():
    # Empty dict should be invalid
    empty_dict_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        {}
    )
    assert empty_dict_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Valid CNCF example should be valid
    cncf_example_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        copy.deepcopy(CNCF_MANIFEST_LIST_ENTRY_EXAMPLE)
    )
    assert cncf_example_valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # No mediaType should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_ENTRY_EXAMPLE)
    cncf_example_mut.pop("mediaType")
    no_mt_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        cncf_example_mut
    )
    assert no_mt_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # No digest should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_ENTRY_EXAMPLE)
    cncf_example_mut.pop("digest")
    no_dig_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        cncf_example_mut
    )
    assert no_dig_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Invalid digest type should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_ENTRY_EXAMPLE)
    cncf_example_mut["digest"] = 1234
    no_dig_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        cncf_example_mut
    )
    assert no_dig_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Invalid digest value should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_ENTRY_EXAMPLE)
    cncf_example_mut["digest"] = "notadigest"
    inv_dig_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        cncf_example_mut
    )
    assert inv_dig_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # No size should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_ENTRY_EXAMPLE)
    cncf_example_mut.pop("size")
    no_size_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        cncf_example_mut
    )
    assert no_size_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Invalid size type should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_ENTRY_EXAMPLE)
    cncf_example_mut["size"] = "abcd"
    inv_size_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        cncf_example_mut
    )
    assert inv_size_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # No platform should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_ENTRY_EXAMPLE)
    cncf_example_mut.pop("platform")
    no_plt_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        cncf_example_mut
    )
    assert no_plt_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Invalid platform type should be invalid
    cncf_example_mut = copy.deepcopy(CNCF_MANIFEST_LIST_ENTRY_EXAMPLE)
    cncf_example_mut["platform"] = 1234
    inv_plt_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        cncf_example_mut
    )
    assert inv_plt_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Valid RedHat example should be valid
    rh_example_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        copy.deepcopy(REDHAT_MANIFEST_LIST_ENTRY_EXAMPLE)
    )
    assert rh_example_valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # Invalid OCI example should be invalid
    oci_example_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
        copy.deepcopy(DOCKER_BUILDX_ATTESTATION_INDEX_ENTRY)
    )
    assert oci_example_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

def test_container_image_v2s2_manifest_list_entry_instantiation():
    # Ensure exception is thrown on instantiation using invalid schema
    exc = None
    try:
        entry = ContainerImageManifestListEntryV2S2({})
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure ContainerImageManifestListEntryV2S2 is returned on instantiation
    # using valid schema
    entry = ContainerImageManifestListEntryV2S2(
        CNCF_MANIFEST_LIST_ENTRY_EXAMPLE
    )
    assert isinstance(entry, ContainerImageManifestListEntryV2S2)

    # Ensure a generic ContainerImageManifestListEntry can convert to a
    # ContainerImageManifestListEntryV2S2
    generic_entry = ContainerImageManifestListEntry(
        CNCF_MANIFEST_LIST_ENTRY_EXAMPLE
    )
    entry = ContainerImageManifestListEntryV2S2.from_manifest_list_entry(
        generic_entry
    )
    assert isinstance(entry, ContainerImageManifestListEntryV2S2)

def test_container_image_v2s2_manifest_list_entry_instance_validation():
    # Ensure ContainerImageManifestListEntryV2S2 instantiates and is valid
    # post-instantiation
    entry = ContainerImageManifestListEntryV2S2(
        copy.deepcopy(CNCF_MANIFEST_LIST_ENTRY_EXAMPLE)
    )
    valid, err = entry.validate()
    assert valid == True
    assert isinstance(err, str)

    # Ensure if we modify a property of the ContainerImageManifestListEntryV2S2
    # to be invalid, it becomes invalid
    entry.entry["digest"] = 1234
    valid, err = entry.validate()
    assert valid == False
    assert isinstance(err, str)
