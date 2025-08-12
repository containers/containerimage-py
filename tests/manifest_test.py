import copy
import json
from jsonschema         import  ValidationError
from image.descriptor   import  ContainerImageDescriptor
from image.manifest     import  ContainerImageManifest

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

# Example manifest from RedHat UBI 9
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

def test_container_image_manifest_get_config_descriptor():
    # Ensure valid config equals expected config
    manifest = ContainerImageManifest(
        copy.deepcopy(OCI_MANIFEST_EXAMPLE)
    )
    config = manifest.get_config_descriptor()
    assert isinstance(config, ContainerImageDescriptor)
    assert config.descriptor == manifest.manifest["config"]

    # Ensure if we invalidate a property of the manifest config,
    # an error is thrown
    manifest.manifest["config"]["digest"] = "notadigest"
    exc = None
    try:
        desc = manifest.get_config_descriptor()
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

def test_container_image_manifest_get_layer_descriptors():
    # Ensure valid layers equal expected layers
    manifest = ContainerImageManifest(
        copy.deepcopy(OCI_MANIFEST_EXAMPLE)
    )
    layers = manifest.get_layer_descriptors()
    assert isinstance(layers, list)
    assert len(layers) == 3
    assert isinstance(layers[0], ContainerImageDescriptor)
    assert layers[0].descriptor == manifest.manifest["layers"][0]
    assert isinstance(layers[1], ContainerImageDescriptor)
    assert layers[1].descriptor == manifest.manifest["layers"][1]
    assert isinstance(layers[2], ContainerImageDescriptor)
    assert layers[2].descriptor == manifest.manifest["layers"][2]

    # Ensure if we invalidate a property of a layer, an error is thrown
    manifest.manifest["layers"][0]["digest"] = "notadigest"
    exc = None
    try:
        layers = manifest.get_layer_descriptors()
    except Exception as e:
        exc = e
    assert exc != None
    assert isinstance(exc, ValidationError)

def test_container_image_manifest_get_size():
    # Ensure size matches expected size
    expected_size = OCI_MANIFEST_EXAMPLE["config"]["size"] + \
                    OCI_MANIFEST_EXAMPLE["layers"][0]["size"] + \
                    OCI_MANIFEST_EXAMPLE["layers"][1]["size"] + \
                    OCI_MANIFEST_EXAMPLE["layers"][2]["size"]
    manifest = ContainerImageManifest(
        copy.deepcopy(OCI_MANIFEST_EXAMPLE)
    )
    size = manifest.get_size()
    assert size == expected_size

    # Ensure size matches expected size
    expected_size = REDHAT_MANIFEST_EXAMPLE["config"]["size"] + \
                    REDHAT_MANIFEST_EXAMPLE["layers"][0]["size"]
    manifest = ContainerImageManifest(
        copy.deepcopy(REDHAT_MANIFEST_EXAMPLE)
    )
    size = manifest.get_size()
    assert size == expected_size

def test_container_image_manifest_to_string():
    manifest_str = json.dumps(OCI_MANIFEST_EXAMPLE, indent=3, sort_keys=False)
    manifest = ContainerImageManifest(OCI_MANIFEST_EXAMPLE)
    assert str(manifest) == manifest_str

def test_container_image_manifest_to_json():
    manifest = ContainerImageManifest(OCI_MANIFEST_EXAMPLE)
    assert json.dumps(manifest) == json.dumps(OCI_MANIFEST_EXAMPLE)
