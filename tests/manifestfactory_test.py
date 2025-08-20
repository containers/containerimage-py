import copy
import json
from jsonschema                 import  ValidationError
from image.errors               import  ContainerImageError
from image.oci                  import  ContainerImageManifestOCI
from image.v2s2                 import  ContainerImageManifestV2S2
from image.containerimage       import  ContainerImageManifestFactory, \
                                        ContainerImageManifestListV2S2, \
                                        ContainerImageIndexOCI
from tests.registryclientmock   import  ATTESTATION_MANIFEST_LIST_EXAMPLE, \
                                        ATTESTATION_AMD64_ATTESTATION_MANIFEST

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

def test_container_image_manifest_factory_create_v2s2_manifest():
    # Ensure exception is thrown when empty dict is passed
    exc = None
    try:
        manifest = ContainerImageManifestFactory.create_v2s2_manifest(
            json.dumps({}).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure manifest is created when valid v2s2 manifest is passed
    manifest = ContainerImageManifestFactory.create_v2s2_manifest(
        json.dumps(copy.deepcopy(CNCF_MANIFEST_EXAMPLE)).encode('utf-8')
    )
    assert isinstance(manifest, ContainerImageManifestV2S2)

    # Ensure exception is thrown when v2s2 manifest list is passed
    exc = None
    try:
        manifest = ContainerImageManifestFactory.create_v2s2_manifest(
            json.dumps(
                copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure exception is thrown when OCI manifest is passed
    exc = None
    try:
        manifest = ContainerImageManifestFactory.create_v2s2_manifest(
            json.dumps(
                copy.deepcopy(ATTESTATION_AMD64_ATTESTATION_MANIFEST)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure exception is thrown when OCI image index is passed
    exc = None
    try:
        manifest = ContainerImageManifestFactory.create_v2s2_manifest(
            json.dumps(
                copy.deepcopy(ATTESTATION_MANIFEST_LIST_EXAMPLE)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

def test_container_image_manifest_factory_create_oci_manifest():
    # Ensure exception is thrown when empty dict is passed
    exc = None
    try:
        manifest = ContainerImageManifestFactory.create_oci_manifest(
            json.dumps({}).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure manifest is created when valid OCI manifest is passed
    manifest = ContainerImageManifestFactory.create_oci_manifest(
        json.dumps(
            copy.deepcopy(ATTESTATION_AMD64_ATTESTATION_MANIFEST)
        ).encode('utf-8')
    )
    assert isinstance(manifest, ContainerImageManifestOCI)

    # Ensure exception is thrown when OCI image index is passed
    exc = None
    try:
        manifest = ContainerImageManifestFactory.create_oci_manifest(
            json.dumps(
                copy.deepcopy(ATTESTATION_MANIFEST_LIST_EXAMPLE)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure exception is thrown when v2s2 manifest is passed
    exc = None
    try:
        manifest = ContainerImageManifestFactory.create_oci_manifest(
            json.dumps(
                copy.deepcopy(CNCF_MANIFEST_EXAMPLE)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure exception is thrown when v2s2 manifest list is passed
    exc = None
    try:
        manifest = ContainerImageManifestFactory.create_oci_manifest(
            json.dumps(
                copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

def test_container_image_manifest_factory_create_v2s2_manifest_list():
    # Ensure exception is thrown when empty dict is passed
    exc = None
    try:
        manifest_list = ContainerImageManifestFactory.create_v2s2_manifest_list(
            json.dumps(
                {}
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure manifest list is created when valid v2s2 manifest list is passed
    manifest_list = ContainerImageManifestFactory.create_v2s2_manifest_list(
        json.dumps(
            copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
        ).encode('utf-8')
    )
    assert isinstance(manifest_list, ContainerImageManifestListV2S2)

    # Ensure exception is thrown when v2s2 manifest is passed
    exc = None
    try:
        manifest_list = ContainerImageManifestFactory.create_v2s2_manifest_list(
            json.dumps(
                copy.deepcopy(CNCF_MANIFEST_EXAMPLE)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure exception is thrown when OCI image index is passed
    exc = None
    try:
        manifest_list = ContainerImageManifestFactory.create_v2s2_manifest_list(
            json.dumps(
                copy.deepcopy(ATTESTATION_MANIFEST_LIST_EXAMPLE)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure exception is thrown when OCI manifest is passed
    exc = None
    try:
        manifest_list = ContainerImageManifestFactory.create_v2s2_manifest_list(
            json.dumps(
                copy.deepcopy(ATTESTATION_AMD64_ATTESTATION_MANIFEST)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

def test_container_image_manifest_factory_create_oci_image_index():
    # Ensure exception is thrown when empty dict is passed
    exc = None
    try:
        manifest_list = ContainerImageManifestFactory.create_oci_image_index(
            json.dumps({}).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure image index is created when valid OCI image index is passed
    manifest_list = ContainerImageManifestFactory.create_oci_image_index(
        json.dumps(
            copy.deepcopy(ATTESTATION_MANIFEST_LIST_EXAMPLE)
        ).encode('utf-8')
    )
    assert isinstance(manifest_list, ContainerImageIndexOCI)

    # Ensure exception is thrown when v2s2 manifest is passed
    exc = None
    try:
        manifest_list = ContainerImageManifestFactory.create_oci_image_index(
            json.dumps(
                copy.deepcopy(CNCF_MANIFEST_EXAMPLE)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure exception is thrown when OCI manifest is passed
    exc = None
    try:
        manifest_list = ContainerImageManifestFactory.create_oci_image_index(
            json.dumps(
                copy.deepcopy(ATTESTATION_AMD64_ATTESTATION_MANIFEST)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

    # Ensure exception is thrown when v2s2 manifest list is passed
    exc = None
    try:
        manifest_list = ContainerImageManifestFactory.create_oci_image_index(
            json.dumps(
                copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
            ).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

def test_container_image_manifest_factory_create():
    # Ensure exception is thrown when empty dict is passed
    exc = None
    try:
        nothing = ContainerImageManifestFactory.create(
            json.dumps({}).encode('utf-8')
        )
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ContainerImageError)

    # Ensure v2s2 manifest list is created when valid v2s2 manifest list is passed
    manifest_list = ContainerImageManifestFactory.create(
        json.dumps(
            copy.deepcopy(CNCF_MANIFEST_LIST_EXAMPLE)
        ).encode('utf-8')
    )
    assert isinstance(manifest_list, ContainerImageManifestListV2S2)

    # Ensure v2s2 manifest is created when valid v2s2 manifest is passed
    v2s2_manifest = ContainerImageManifestFactory.create(
        json.dumps(
            copy.deepcopy(CNCF_MANIFEST_EXAMPLE)
        ).encode('utf-8')
    )
    assert isinstance(v2s2_manifest, ContainerImageManifestV2S2)

    # Ensure OCI image index is created when valid OCI image index is passed
    image_index = ContainerImageManifestFactory.create(
        json.dumps(
            copy.deepcopy(ATTESTATION_MANIFEST_LIST_EXAMPLE)
        ).encode('utf-8')
    )
    assert isinstance(image_index, ContainerImageIndexOCI)

    # Ensure OCI manifest is created when valid OCI manifest is passed
    oci_manifest = ContainerImageManifestFactory.create(
        json.dumps(
            copy.deepcopy(ATTESTATION_AMD64_ATTESTATION_MANIFEST)
        ).encode('utf-8')
    )
    assert isinstance(oci_manifest, ContainerImageManifestOCI)
