"""
Contains a base ContainerImageManifest class which is extended by the docker
v2s2 and OCI specifications for their respective manifest implementations
"""

import json
from typing             import  Dict, Any, List
from image.descriptor   import  ContainerImageDescriptor

class ContainerImageManifest:
    """
    Represents an arch manifest returned from the distribution registry API.
    This is a base class extended by the ContainerImageManifestV2S2 and
    ContainerImageManifestOCI since the two specs are very similar, with the
    v2s2 spec being more restrictive than the OCI spec.
    """
    def __init__(self, manifest: bytes):
        """
        Constructor for the ContainerImageManifest class

        Args:
            manifest (bytes): The raw manifest bytes
        """
        self.raw_manifest = manifest
        self.manifest = json.loads(manifest)

    def get_layer_descriptors(self) -> List[ContainerImageDescriptor]:
        """
        Returns a list of the container image's layer descriptors, defaults to
        empty list

        Returns:
            List[ContainerImageDescriptor]: The container image's layer descriptors
        """
        # Get the layers of the image manifest
        layer_meta_list = list(self.manifest.get("layers"))
        if len(layer_meta_list) == 0:
            raise ValueError("No layers found")

        # Instantiate as ContainerImageDescriptor list and return
        layers = []
        for layer_meta in layer_meta_list:
            layer = ContainerImageDescriptor(layer_meta)
            layers.append(layer)
        return layers

    def get_config_descriptor(self) -> ContainerImageDescriptor:
        """
        Returns the container image manifest config descriptor

        Returns:
            ContainerImageDescriptor: The container image manifest config descriptor
        """
        # Get the container image manifest config
        config = dict(self.manifest.get("config"))
        return ContainerImageDescriptor(config)
    
    def get_media_type(self) -> str:
        """
        Returns the mediaType of the container image manifest

        Returns:
            str: The container image manifest mediaType
        """
        return str(self.manifest.get("mediaType"))

    def get_size(self) -> int:
        """
        Returns the container image manifest size in bytes

        Returns:
            int: The container image manifest size in bytes
        """
        # Get the config size
        config = self.get_config_descriptor()
        config_size = config.get_size()

        # Deduplicate the layers in a dict
        layers = self.get_layer_descriptors()
        layer_dict = {}
        for layer in layers:
            digest = layer.get_digest()
            size = layer.get_size()
            layer_dict[digest] = size

        # Get the deduplicated layer sizes
        layer_size = 0
        for digest in layer_dict.keys():
            layer_size += layer_dict[digest]

        # Add and return the size of the manifest
        return config_size + layer_size

    def raw(self) -> bytes:
        """
        Returns the raw, unmodified manifest bytes

        Returns:
            bytes: The raw, unmodified manifest bytes
        """
        return self.raw_manifest

    def __str__(self) -> str:
        """
        Formats the ContainerImageManifest as a string

        Returns:
            str: The ContainerImageManifest formatted as a string
        """
        return json.dumps(self.manifest, indent=3, sort_keys=False)

    def __json__(self) -> Dict[str, Any]:
        """
        Formats the ContainerImageManifest as a JSON dictionary

        Returns:
            Dict[str, Any]: The ContainerImageManifest formatted as a JSON dict
        """
        return self.manifest
