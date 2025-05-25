import json
from image.byteunit             import  ByteUnit
from image.errors               import  ContainerImageError
from image.v2s2                 import  ContainerImageManifestV2S2
from image.oci                  import  ContainerImageManifestOCI
from image.containerimage       import  ContainerImage, \
                                        ContainerImageManifestListV2S2, \
                                        ContainerImageIndexOCI
from tests.registryclientmock   import  MOCK_IMAGE_NAME, \
                                        MOCK_REGISTRY_CREDS, \
                                        REDHAT_MANIFEST_LIST_EXAMPLE, \
                                        REDHAT_AMD64_MANIFEST, \
                                        REDHAT_ARM64_MANIFEST, \
                                        REDHAT_PPC64LE_MANIFEST, \
                                        REDHAT_S390X_MANIFEST, \
                                        ATTESTATION_MANIFEST_LIST_EXAMPLE, \
                                        ATTESTATION_AMD64_MANIFEST, \
                                        ATTESTATION_S390X_MANIFEST, \
                                        ATTESTATION_AMD64_ATTESTATION_MANIFEST, \
                                        ATTESTATION_S390X_ATTESTATION_MANIFEST, \
                                        mock_get_manifest, \
                                        mock_list_tags

def test_container_image_static_validation():
    # Ensure the empty string is invalid
    valid, err = ContainerImage.validate_static(
        ""
    )
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0

    # Ensure a valid container image reference by tag is valid
    valid, err = ContainerImage.validate_static(
        "this.is/a/valid/image:v1.2.3"
    )
    assert valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # Ensure an image name is valid, as tag is implied to be latest
    valid, err = ContainerImage.validate_static(
        "this.is/an/image/name"
    )
    assert valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # Ensure a digest ref is valid
    valid, err = ContainerImage.validate_static(
        "this.is/an/image/by-digest@" + \
        "sha256:f5d2c6a1e0c86e4234ea601552dbabb4ced0e013a1efcbfb439f1f6a7a9275b0"
    )
    assert valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # Ensure an invalid conatiner image is invalid
    valid, err = ContainerImage.validate_static(
        "Not a container image"
    )
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0

def test_container_image_instantiation():
    # Ensure an exception is thrown if invalid
    exc = None
    try:
        image = ContainerImage("")
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ContainerImageError)

    # Ensure a ContainerImage is returned if valid
    image = ContainerImage("this.is/a/valid/image:v1.2.3")
    assert isinstance(image, ContainerImage)

def test_container_image_instance_validation():
    # Ensure a valid ContainerImage is valid
    image = ContainerImage("this.is/a/valid/image:v1.2.3")
    valid, err = image.validate()
    assert valid == True
    assert isinstance(err, str)
    assert len(err) == 0

    # Ensure if we invalidate the ContainerImage ref, it's invalid
    image.ref = ""
    valid, err = image.validate()
    assert valid == False
    assert isinstance(err, str)
    assert len(err) > 0

def test_container_image_is_digest_ref():
    # Ensure a digest ref is a digest ref
    image = ContainerImage(
        "this.is/a/valid/image@" + \
        "sha256:f5d2c6a1e0c86e4234ea601552dbabb4ced0e013a1efcbfb439f1f6a7a9275b0"
    )
    is_digest = image.is_digest_ref()
    assert is_digest == True

    # Ensure a tag ref is not a digest ref
    image = ContainerImage("this.is/a/valid/image:v1.2.3")
    is_digest = image.is_digest_ref()
    assert is_digest == False

    # Ensure an image name is not a digest ref
    image = ContainerImage("this.is/a/valid/image")
    is_digest = image.is_digest_ref()
    assert is_digest == False

    # Ensure a tag and digest ref is a digest ref
    image = ContainerImage(
        "this.is/a/valid/image:" + \
        "v1.2.3@" + \
        "sha256:f5d2c6a1e0c86e4234ea601552dbabb4ced0e013a1efcbfb439f1f6a7a9275b0"
    )
    is_digest = image.is_digest_ref()
    assert is_digest == True

    # Ensure if we invalidate the image ref, an exception is thrown
    exc = None
    image.ref = ""
    try:
        is_digest = image.is_digest_ref()
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ContainerImageError)

def test_container_image_is_tag_ref():
    # Ensure a tag ref is a tag ref
    image = ContainerImage("this.is/a/valid/image:v1.2.3")
    is_tag = image.is_tag_ref()
    assert is_tag == True

    # Ensure an image name is a tag ref
    image = ContainerImage("this.is/a/valid/image")
    is_tag = image.is_tag_ref()
    assert is_tag == True

    # Ensure a digest ref is not a tag ref
    image = ContainerImage(
        "this.is/a/valid/image@" + \
        "sha256:f5d2c6a1e0c86e4234ea601552dbabb4ced0e013a1efcbfb439f1f6a7a9275b0"
    )
    is_tag = image.is_tag_ref()
    assert is_tag == False

    # Ensure a tag and digest ref is a not a tag ref
    image = ContainerImage(
        "this.is/a/valid/image:" + \
        "v1.2.3@" + \
        "sha256:f5d2c6a1e0c86e4234ea601552dbabb4ced0e013a1efcbfb439f1f6a7a9275b0"
    )
    is_tag = image.is_tag_ref()
    assert is_tag == False

    # Ensure if we invalidate the image ref, an exception is thrown
    exc = None
    image.ref = ""
    try:
        is_tag = image.is_tag_ref()
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ContainerImageError)

def test_container_image_get_identifier():
    # Ensure identifier matches for tag ref
    image = ContainerImage("this.is/a/valid/image:v1.2.3")
    identifier = image.get_identifier()
    assert identifier == "v1.2.3"

    # Ensure identifier matches for implied tag ref (latest)
    image = ContainerImage("this.is/a/valid/image")
    identifier = image.get_identifier()
    assert identifier == "latest"

    # Ensure identifier matches for digest ref
    digest = "sha256:f5d2c6a1e0c86e4234ea601552dbabb4ced0e013a1efcbfb439f1f6a7a9275b0"
    image = ContainerImage(
        "this.is/a/valid/image@" + \
        digest
    )
    identifier = image.get_identifier()
    assert identifier == digest

    # Ensure identifier matches for tag and digest ref
    # It should be a digest in this case
    image = ContainerImage(
        "this.is/a/valid/image:" + \
        "v1.2.3@" + \
        digest
    )
    identifier = image.get_identifier()
    assert identifier == digest

    # Ensure if we invalidate the image ref, an exception is thrown
    exc = None
    image.ref = ""
    try:
        identifier = image.get_identifier()
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ContainerImageError)

def test_container_image_get_name():
    # Ensure name matches for tag ref
    image = ContainerImage("this.is/a/valid/image:v1.2.3")
    name = image.get_name()
    assert name == "this.is/a/valid/image"

    # Ensure name matches for tag ref with different registry
    image = ContainerImage("another.com/registry/path/and-image-name:v1.2.3")
    name = image.get_name()
    assert name == "another.com/registry/path/and-image-name"

    # Ensure name matches for implied tag ref
    image = ContainerImage("this.is/another/valid/image")
    name = image.get_name()
    assert name == "this.is/another/valid/image"

    # Ensure name matches for digest ref
    image = ContainerImage(
        "quay.io/example/image@" + \
        "sha256:f5d2c6a1e0c86e4234ea601552dbabb4ced0e013a1efcbfb439f1f6a7a9275b0"
    )
    name = image.get_name()
    assert name == "quay.io/example/image"

    # Ensure name matches for tag and digest ref
    image = ContainerImage(
        "icr.io/cpopen/cp4waiops/bcdr:" + \
        "v1.2.3@" + \
        "sha256:f5d2c6a1e0c86e4234ea601552dbabb4ced0e013a1efcbfb439f1f6a7a9275b0"
    )
    name = image.get_name()
    assert name == "icr.io/cpopen/cp4waiops/bcdr"

    # Ensure if we invalidate the image ref, an exception is thrown
    exc = None
    image.ref = ""
    try:
        name = image.get_name()
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ContainerImageError)

def test_container_image_list_tags(mocker):
    mocker.patch(
        "image.containerimage.ContainerImageRegistryClient.list_tags",
        mock_list_tags
    )

    # Ensure the tag list response matches the expected
    image = ContainerImage(f"{MOCK_IMAGE_NAME}:latest")
    tags = image.list_tags(MOCK_REGISTRY_CREDS)
    assert tags["name"] == MOCK_IMAGE_NAME
    assert tags["tags"] == [ "latest", "latest-dup", "latest-attestation" ]

def test_container_image_get_manifest(mocker):
    mocker.patch(
        "image.containerimage.ContainerImageRegistryClient.get_manifest",
        mock_get_manifest
    )

    # Ensure for a v2s2 manifest list, a v2s2 manifest list is returned
    image = ContainerImage(f"{MOCK_IMAGE_NAME}:latest")
    manifest_list = image.get_manifest(MOCK_REGISTRY_CREDS)
    assert isinstance(manifest_list, ContainerImageManifestListV2S2)

    # Ensure for a v2s2 manifest, a v2s2 manifest is returned
    image = ContainerImage(
        f"{MOCK_IMAGE_NAME}@{REDHAT_MANIFEST_LIST_EXAMPLE['manifests'][0]['digest']}"
    )
    manifest = image.get_manifest(MOCK_REGISTRY_CREDS)
    assert isinstance(manifest, ContainerImageManifestV2S2)

    # Ensure for an OCI image index, an OCI image index is returned
    image = ContainerImage(f"{MOCK_IMAGE_NAME}:latest-attestation")
    oci_index = image.get_manifest(MOCK_REGISTRY_CREDS)
    assert isinstance(oci_index, ContainerImageIndexOCI)

    # Ensure for an OCI manifest, an OCI manifest is returned
    image = ContainerImage(
        f"{MOCK_IMAGE_NAME}@{ATTESTATION_MANIFEST_LIST_EXAMPLE['manifests'][0]['digest']}"
    )
    oci_manifest = image.get_manifest(MOCK_REGISTRY_CREDS)
    assert isinstance(oci_manifest, ContainerImageManifestOCI)

    # Ensure if we invalidate the image ref, an exception is thrown
    exc = None
    image.ref = ""
    try:
        manifest = image.get_manifest(MOCK_REGISTRY_CREDS)
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ContainerImageError)

def test_container_image_is_manifest_list(mocker):
    mocker.patch(
        "image.containerimage.ContainerImageRegistryClient.get_manifest",
        mock_get_manifest
    )

    # Ensure for a v2s2 manifest list, it is seen as a manifest list
    image = ContainerImage(f"{MOCK_IMAGE_NAME}:latest")
    is_manifest_list = image.is_manifest_list(MOCK_REGISTRY_CREDS)
    assert is_manifest_list == True

    # Ensure for a v2s2 manifest, it is not seen as a manifest list
    image = ContainerImage(
        f"{MOCK_IMAGE_NAME}@{REDHAT_MANIFEST_LIST_EXAMPLE['manifests'][0]['digest']}"
    )
    is_manifest_list = image.is_manifest_list(MOCK_REGISTRY_CREDS)
    assert is_manifest_list == False

    # Ensure for an OCI image index, it is seen as a manifest list
    image = ContainerImage(f"{MOCK_IMAGE_NAME}:latest-attestation")
    is_manifest_list = image.is_manifest_list(MOCK_REGISTRY_CREDS)
    assert is_manifest_list == True

    # Ensure for an OCI manifest, it is not seen as a manifest list
    image = ContainerImage(
        f"{MOCK_IMAGE_NAME}@{ATTESTATION_MANIFEST_LIST_EXAMPLE['manifests'][0]['digest']}"
    )
    is_manifest_list = image.is_manifest_list(MOCK_REGISTRY_CREDS)
    assert is_manifest_list == False

    # Ensure if we invalidate the image ref, an exception is thrown
    exc = None
    image.ref = ""
    try:
        manifest = image.get_manifest(MOCK_REGISTRY_CREDS)
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ContainerImageError)

def test_container_image_get_size(mocker):
    mocker.patch(
        "image.containerimage.ContainerImageRegistryClient.get_manifest",
        mock_get_manifest
    )

    # Ensure size matches expected size for a v2s2 manifest list
    image = ContainerImage(f"{MOCK_IMAGE_NAME}:latest")
    size = image.get_size(MOCK_REGISTRY_CREDS)
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

    # Ensure formatted size matches expected value for a v2s2 manifest list
    size_formatted = image.get_size_formatted(MOCK_REGISTRY_CREDS)
    assert size_formatted == ByteUnit.format_size_bytes(expected_size)

    # Ensure size matches expected size for a v2s2 manifest
    image = ContainerImage(
        f"{MOCK_IMAGE_NAME}@" + \
        "sha256:f5d2c6a1e0c86e4234ea601552dbabb4ced0e013a1efcbfb439f1f6a7a9275b0"
    )
    size = image.get_size(MOCK_REGISTRY_CREDS)
    expected_size = REDHAT_AMD64_MANIFEST["config"]["size"] + \
                    REDHAT_AMD64_MANIFEST["layers"][0]["size"]
    assert size == expected_size

    # Ensure formatted size matches expected value for a v2s2 manifest
    size_formatted = image.get_size_formatted(MOCK_REGISTRY_CREDS)
    assert size_formatted == ByteUnit.format_size_bytes(expected_size)

    # Ensure size matches expected size for an OCI manifest list
    image = ContainerImage(f"{MOCK_IMAGE_NAME}:latest-attestation")
    size = image.get_size(MOCK_REGISTRY_CREDS)
    expected_size = ATTESTATION_MANIFEST_LIST_EXAMPLE["manifests"][0]["size"] + \
                    ATTESTATION_MANIFEST_LIST_EXAMPLE["manifests"][1]["size"] + \
                    ATTESTATION_MANIFEST_LIST_EXAMPLE["manifests"][2]["size"] + \
                    ATTESTATION_MANIFEST_LIST_EXAMPLE["manifests"][3]["size"] + \
                    ATTESTATION_AMD64_MANIFEST["config"]["size"] + \
                    ATTESTATION_AMD64_MANIFEST["layers"][0]["size"] + \
                    ATTESTATION_AMD64_MANIFEST["layers"][1]["size"] + \
                    ATTESTATION_AMD64_MANIFEST["layers"][2]["size"] + \
                    ATTESTATION_S390X_MANIFEST["config"]["size"] + \
                    ATTESTATION_S390X_MANIFEST["layers"][0]["size"] + \
                    ATTESTATION_AMD64_ATTESTATION_MANIFEST["config"]["size"] + \
                    ATTESTATION_AMD64_ATTESTATION_MANIFEST["layers"][0]["size"] + \
                    ATTESTATION_S390X_ATTESTATION_MANIFEST["config"]["size"] + \
                    ATTESTATION_S390X_ATTESTATION_MANIFEST["layers"][0]["size"]
    # Above, layers 2 and 3 of the s390x manifest are shared with the amd64
    # manifest, hence, they are deduplicated in the expected size calculation
    assert size == expected_size

    # Ensure formatted size matches expected value for an OCI manifest list
    size_formatted = image.get_size_formatted(MOCK_REGISTRY_CREDS)
    assert size_formatted == ByteUnit.format_size_bytes(expected_size)

    # Ensure size matches expected size for an OCI manifest
    image = ContainerImage(
        f"{MOCK_IMAGE_NAME}@{ATTESTATION_MANIFEST_LIST_EXAMPLE['manifests'][0]['digest']}"
    )
    size = image.get_size(MOCK_REGISTRY_CREDS)
    expected_size = ATTESTATION_AMD64_MANIFEST["config"]["size"]
    for layer in ATTESTATION_AMD64_MANIFEST["layers"]:
        expected_size += layer["size"]
    assert size == expected_size
    
    # Ensure formatted size matches expected value for an OCI manifest
    size_formatted = image.get_size_formatted(MOCK_REGISTRY_CREDS)
    assert size_formatted == ByteUnit.format_size_bytes(expected_size)

    # Ensure if we invalidate the image ref, an exception is thrown
    exc = None
    image.ref = ""
    try:
        size = image.get_size(MOCK_REGISTRY_CREDS)
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ContainerImageError)

def test_container_image_delete(mocker):
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.delete", return_value=mock_response)

    # Ensure no exceptions are raised when image is successfully deleted
    image = ContainerImage(f"{MOCK_IMAGE_NAME}:latest")
    exc = None
    try:
        image.delete(MOCK_REGISTRY_CREDS)
    except Exception as e:
        exc = e
    assert exc == None

def test_container_image_to_string():
    # Ensure ref matches expected ref
    image = ContainerImage("this.is/a/valid/image:v1.2.3")
    assert str(image) == "this.is/a/valid/image:v1.2.3"

def test_container_image_to_json():
    # Ensure JSON conversion matches expected JSON conversion
    image = ContainerImage("this.is/a/valid/image:v1.2.3")
    assert json.dumps(image) == json.dumps(
        {
            "ref": "this.is/a/valid/image:v1.2.3"
        }
    )
