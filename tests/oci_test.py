import copy
import json
from jsonschema                 import  ValidationError
from image.containerimage       import  ContainerImageIndexOCI
from image.manifest             import  ContainerImageManifest
from image.oci                  import  ContainerImageIndexEntryOCI, \
                                        ContainerImageManifestOCI
from tests.registryclientmock   import  ATTESTATION_MANIFEST_LIST_EXAMPLE, \
                                        ATTESTATION_AMD64_MANIFEST, \
                                        ATTESTATION_AMD64_ATTESTATION_MANIFEST, \
                                        ATTESTATION_S390X_MANIFEST, \
                                        ATTESTATION_S390X_ATTESTATION_MANIFEST, \
                                        REDHAT_MANIFEST_LIST_EXAMPLE, \
                                        MOCK_IMAGE_NAME, \
                                        MOCK_REGISTRY_CREDS, \
                                        mock_get_manifest

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
# This is a v2s2 manifest, so it should be invalid
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

# An example image index from the OCI image index spec
# Ref: https://github.com/opencontainers/image-spec/blob/v1.0.1/image-index.md
OCI_IMAGE_INDEX_EXAMPLE = {
    "schemaVersion": 2,
    "manifests": [
        {
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "size": 7143,
            "digest": "sha256:e692418e4cbaf90ca69d05a66403747baa33ee08806650b51fab815ad7fc331f",
            "platform": {
                "architecture": "ppc64le",
                "os": "linux"
            }
        },
        {
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "size": 7682,
            "digest": "sha256:5b0bcabd1ed22e9fb1310cf6c2dec7cdef19f0ad69efa1f392e94a4333501270",
            "platform": {
                "architecture": "amd64",
                "os": "linux"
            }
        }
    ],
    "annotations": {
        "com.example.key1": "value1",
        "com.example.key2": "value2"
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

"""
ContainerImageIndexEntryOCI tests

Unit tests for the ContainerImageIndexEntryOCI class
"""
def test_container_image_oci_image_index_entry_static_validation():
    # Empty dict should be invalid
    empty_dict_valid, err = ContainerImageIndexEntryOCI.validate_static(
        {}
    )
    assert empty_dict_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Valid OCI example should be valid
    oci_example_mut = copy.deepcopy(DOCKER_BUILDX_ATTESTATION_INDEX_ENTRY)
    oci_example_valid, err = ContainerImageIndexEntryOCI.validate_static(
        oci_example_mut
    )
    assert oci_example_valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # No mediaType should be invalid
    oci_example_mut.pop("mediaType")
    no_mt_valid, err = ContainerImageIndexEntryOCI.validate_static(
        oci_example_mut
    )
    assert no_mt_valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    oci_example_mut["mediaType"] = copy.copy(
        DOCKER_BUILDX_ATTESTATION_INDEX_ENTRY["mediaType"]
    )

    # No digest should be invalid
    oci_example_mut.pop("digest")
    no_dig_valid, err = ContainerImageIndexEntryOCI.validate_static(
        oci_example_mut
    )
    assert no_dig_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Invalid digest type should be invalid
    oci_example_mut["digest"] = 1234
    inv_dig_valid, err = ContainerImageIndexEntryOCI.validate_static(
        oci_example_mut
    )
    assert inv_dig_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Invalid digest value should be invalid
    oci_example_mut["digest"] = "notadigest"
    inv_dig_valid, err = ContainerImageIndexEntryOCI.validate_static(
        oci_example_mut
    )
    assert inv_dig_valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    oci_example_mut["digest"] = copy.copy(
        DOCKER_BUILDX_ATTESTATION_INDEX_ENTRY["digest"]
    )

    # No size should be invalid
    oci_example_mut.pop("size")
    no_size_valid, err = ContainerImageIndexEntryOCI.validate_static(
        oci_example_mut
    )
    assert no_size_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Invalid size type should be invalid
    oci_example_mut["size"] = "abcd"
    inv_size_valid, err = ContainerImageIndexEntryOCI.validate_static(
        oci_example_mut
    )
    assert inv_size_valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    oci_example_mut["size"] = copy.copy(
        DOCKER_BUILDX_ATTESTATION_INDEX_ENTRY["size"]
    )

    # No platform should be valid
    oci_example_mut.pop("platform")
    no_plt_valid, err = ContainerImageIndexEntryOCI.validate_static(
        oci_example_mut
    )
    assert no_plt_valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # Invalid platform type should be invalid
    oci_example_mut["platform"] = 1234
    inv_plt_valid, err = ContainerImageIndexEntryOCI.validate_static(
        oci_example_mut
    )
    assert inv_plt_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

def test_container_image_oci_image_index_entry_instantiation():
    # Invalid entry should raise ValidationError
    exc = None
    try:
        entry = ContainerImageIndexEntryOCI(
            {}
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Valid entry should be a ContainerImageIndexEntryOCI instance
    entry = ContainerImageIndexEntryOCI(
        copy.deepcopy(DOCKER_BUILDX_ATTESTATION_INDEX_ENTRY)
    )
    assert isinstance(entry, ContainerImageIndexEntryOCI)

def test_container_image_oci_image_index_entry_instance_validation():
    # Ensure ContainerImageIndexEntryOCI instantiates and is valid
    # post-instantiation
    entry = ContainerImageIndexEntryOCI(
        copy.deepcopy(DOCKER_BUILDX_ATTESTATION_INDEX_ENTRY)
    )
    valid, err = entry.validate()
    assert valid == True
    assert isinstance(err, str)

    # Ensure if we modify a property of the ContainerImageIndexEntryOCI
    # to be invalid, it becomes invalid
    entry.entry["digest"] = 1234
    valid, err = entry.validate()
    assert valid == False
    assert isinstance(err, str)

"""
ContainerImageIndexOCI tests

Unit tests for the ContainerImageIndexOCI class
"""
def test_container_image_oci_manifest_list_static_validation():
    # Empty dict should be invalid
    empty_dict_valid, err = ContainerImageIndexOCI.validate_static({})
    assert empty_dict_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Valid OCI example should be valid
    oci_example_mut = copy.deepcopy(OCI_IMAGE_INDEX_EXAMPLE)
    oci_example_valid, err = ContainerImageIndexOCI.validate_static(
        oci_example_mut
    )
    assert oci_example_valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # No schemaVersion should be invalid
    oci_example_mut.pop("schemaVersion")
    no_sv_valid, err = ContainerImageIndexOCI.validate_static(
        oci_example_mut
    )
    assert no_sv_valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    oci_example_mut["schemaVersion"] = copy.copy(
        OCI_IMAGE_INDEX_EXAMPLE["schemaVersion"]
    )

    # With OCI index mediaType should be valid
    oci_example_mut["mediaType"] = "application/vnd.oci.image.index.v1+json"
    oci_mt_valid, err = ContainerImageIndexOCI.validate_static(
        oci_example_mut
    )
    assert oci_mt_valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # With v2s2 manifest list mediaType should be invalid
    oci_example_mut["mediaType"] = "application/vnd.docker.distribution.manifest.list.v2+json"
    v2s2_mt_valid, err = ContainerImageIndexOCI.validate_static(
        oci_example_mut
    )
    assert v2s2_mt_valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    oci_example_mut.pop("mediaType")

    # Manifest missing digest should be invalid
    oci_example_mut["manifests"][0].pop("digest")
    no_dig_valid, err = ContainerImageIndexOCI.validate_static(
        oci_example_mut
    )
    assert no_dig_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Manifest with invalid digest should be invalid
    oci_example_mut["manifests"][0]["digest"] = "notadigest"
    inv_dig_valid, err = ContainerImageIndexOCI.validate_static(
        oci_example_mut
    )
    assert inv_dig_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # No manifests should be invalid
    oci_example_mut.pop("manifests")
    no_mf_valid, err = ContainerImageIndexOCI.validate_static(
        oci_example_mut
    )
    assert no_mf_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Ensure v2s2 manifest list is invalid
    v2s2_valid, err = ContainerImageIndexOCI.validate_static(
        REDHAT_MANIFEST_LIST_EXAMPLE
    )
    assert v2s2_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

def test_container_image_oci_manifest_list_instantiation():
    # Ensure exception is thrown on instantiation using invalid schema
    exc = None
    try:
        manifest_list = ContainerImageIndexOCI(
            json.dumps({}).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure ContainerImageIndexOCI is returned when using valid schema
    manifest_list = ContainerImageIndexOCI(
        json.dumps(
            copy.deepcopy(OCI_IMAGE_INDEX_EXAMPLE)
        ).encode('utf-8')
    )
    assert isinstance(manifest_list, ContainerImageIndexOCI)

def test_container_image_oci_manifest_list_instance_validation():
    # Ensure ContainerImageIndexOCI instantiates and is valid post-instantiation
    manifest_list = ContainerImageIndexOCI(
        json.dumps(
            copy.deepcopy(OCI_IMAGE_INDEX_EXAMPLE)
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
    manifest_list.manifest_list.pop("mediaType")

    # Ensure if we drop a required property of the manifest, it's invalid
    manifest_list.manifest_list.pop("schemaVersion")
    valid, err = manifest_list.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest_list.manifest_list["schemaVersion"] = copy.copy(
        OCI_IMAGE_INDEX_EXAMPLE["schemaVersion"]
    )

    # Ensure if we invalidate a property of a manifest entry, it's invalid
    manifest_list.manifest_list["manifests"][0]["digest"] = "notadigest"
    valid, err = manifest_list.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest_list.manifest_list["manifests"][0]["digest"] = copy.copy(
        OCI_IMAGE_INDEX_EXAMPLE["manifests"][0]["digest"]
    )

def test_container_image_oci_manifest_list_get_entries():
    # Ensure entries match expected typing and length
    manifest_list = ContainerImageIndexOCI(
        json.dumps(
            copy.deepcopy(OCI_IMAGE_INDEX_EXAMPLE)
        ).encode('utf-8')
    )
    entries = manifest_list.get_oci_entries()
    assert isinstance(entries, list)
    assert len(entries) == 2
    assert isinstance(entries[0], ContainerImageIndexEntryOCI)
    assert isinstance(entries[1], ContainerImageIndexEntryOCI)

    # Ensure if we invalidate a property of a manifest entry, it's invalid
    exc = None
    manifest_list.manifest_list["manifests"][0]["digest"] = "notadigest"
    try:
        entries = manifest_list.get_oci_entries()
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

def test_container_image_oci_manifest_list_get_manifests(mocker):
    # Mock the ContainerImageRegistryClient.get_manifest function which is
    # called in the implementation of ContainerImageManifestList.get_size
    mocker.patch(
        "image.containerimage.ContainerImageRegistryClient.get_manifest",
        mock_get_manifest
    )

    # Ensure the OCI index manifests can be retrieved
    manifest_list = ContainerImageIndexOCI(
        json.dumps(
            copy.deepcopy(ATTESTATION_MANIFEST_LIST_EXAMPLE)
        ).encode('utf-8')
    )
    manifests = manifest_list.get_oci_manifests(
        MOCK_IMAGE_NAME, MOCK_REGISTRY_CREDS
    )
    expected_manifests = [
        ContainerImageManifestOCI(
            json.dumps(ATTESTATION_AMD64_MANIFEST).encode('utf-8')
        ),
        ContainerImageManifestOCI(
            json.dumps(ATTESTATION_S390X_MANIFEST).encode('utf-8')
        ),
        ContainerImageManifestOCI(
            json.dumps(ATTESTATION_AMD64_ATTESTATION_MANIFEST).encode('utf-8')
        ),
        ContainerImageManifestOCI(
            json.dumps(ATTESTATION_S390X_ATTESTATION_MANIFEST).encode('utf-8')
        )
    ]
    assert json.dumps(manifests) == json.dumps(expected_manifests)

"""
ContainerImageManifestOCI tests

Unit tests for the ContainerImageManifestOCI class
"""
def test_container_image_oci_manifest_static_validation():
    # Empty dict should be invalid
    empty_dict_valid, err = ContainerImageManifestOCI.validate_static({})
    assert empty_dict_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Valid OCI example manifest should be valid
    oci_manifest_valid, err = ContainerImageManifestOCI.validate_static(
        copy.deepcopy(OCI_MANIFEST_EXAMPLE)
    )
    assert oci_manifest_valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # No schemaVersion should be invalid
    oci_example_mut = copy.deepcopy(OCI_MANIFEST_EXAMPLE)
    oci_example_mut.pop("schemaVersion")
    no_sv_valid, err = ContainerImageManifestOCI.validate_static(
        oci_example_mut
    )
    assert no_sv_valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    oci_example_mut["schemaVersion"] = copy.deepcopy(
        OCI_MANIFEST_EXAMPLE["schemaVersion"]
    )

    # No config should be invalid
    oci_example_mut.pop("config")
    no_conf_valid, err = ContainerImageManifestOCI.validate_static(
        oci_example_mut
    )
    assert no_conf_valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    oci_example_mut["config"] = copy.deepcopy(
        OCI_MANIFEST_EXAMPLE["config"]
    )

    # No layers should be invalid
    oci_example_mut.pop("layers")
    no_layers_valid, err = ContainerImageManifestOCI.validate_static(
        oci_example_mut
    )
    assert no_layers_valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    oci_example_mut["layers"] = copy.copy(
        OCI_MANIFEST_EXAMPLE["layers"]
    )

    # V2S2 RedHat example should be invalid
    rh_example_valid, err = ContainerImageManifestOCI.validate_static(
        copy.deepcopy(REDHAT_MANIFEST_EXAMPLE)
    )
    assert rh_example_valid == False
    assert isinstance(err, str)
    assert len(err) > 0

def test_container_image_oci_manifest_instantiation():
    # Ensure exception is thrown on instantiation using invalid schema
    exc = None
    try:
        manifest = ContainerImageManifestOCI(
            json.dumps({}).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure ContainerImageManifestOCI is returned when using valid schema
    manifest = ContainerImageManifestOCI(
        json.dumps(
            copy.deepcopy(OCI_MANIFEST_EXAMPLE)
        ).encode('utf-8')
    )
    assert isinstance(manifest, ContainerImageManifestOCI)

    # Ensure a generic manifest can be converted into an OCI manifest
    generic_manifest = ContainerImageManifest(
        json.dumps(
            copy.deepcopy(OCI_MANIFEST_EXAMPLE)
        ).encode('utf-8')
    )
    manifest = ContainerImageManifestOCI.from_manifest(
        generic_manifest
    )
    assert isinstance(manifest, ContainerImageManifestOCI)

def test_container_image_oci_manifest_instance_validation():
    # Ensure ContainerImageManifestOCI instantiates and is valid post-instantiation
    manifest = ContainerImageManifestOCI(
        json.dumps(
            copy.deepcopy(OCI_MANIFEST_EXAMPLE)
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
    manifest.manifest.pop("mediaType")

    # Ensure if we invalidate a property of the manifest config, it's invalid
    manifest.manifest["config"]["digest"] = "notadigest"
    valid, err = manifest.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest.manifest["config"]["digest"] = copy.copy(
        OCI_MANIFEST_EXAMPLE["config"]["digest"]
    )

    # Ensure if we invalidate a property of the manifest config, it's invalid
    manifest.manifest["config"]["size"] = "1234"
    valid, err = manifest.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest.manifest["config"]["digest"] = copy.copy(
        OCI_MANIFEST_EXAMPLE["config"]["size"]
    )

    # Ensure if we invalidate a property of a manifest layer, it's invalid
    manifest.manifest["layers"][0]["digest"] = "notadigest"
    valid, err = manifest.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest.manifest["layers"][0]["digest"] = copy.copy(
        OCI_MANIFEST_EXAMPLE["layers"][0]["digest"]
    )

    # Ensure if we invalidate a property of a manifest layer, it's invalid
    manifest.manifest["layers"][0]["size"] = "1234"
    valid, err = manifest.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0
    manifest.manifest["layers"][0]["size"] = copy.copy(
        OCI_MANIFEST_EXAMPLE["layers"][0]["size"]
    )
