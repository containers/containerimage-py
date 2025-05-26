"""
Contains the ContainerImage object, which is the main object intended for use
by end-users of containerimage-py.  As a user of this object, you can pass in
a reference to a container image in a remote registry.  Then through the object
interface you can interact with the container image & registry, fetching
metadata and mutating the image through the registry API.
"""

from __future__ import annotations
import json
import requests
from typing                         import  List, Dict, Any, \
                                            Union, Type, Iterator
from image.byteunit                 import  ByteUnit
from image.client                   import  ContainerImageRegistryClient
from image.config                   import  ContainerImageConfig
from image.containerimageinspect    import  ContainerImageInspect
from image.errors                   import  ContainerImageError
from image.manifestfactory          import  ContainerImageManifestFactory
from image.manifestlist             import  ContainerImageManifestList
from image.oci                      import  ContainerImageManifestOCI, \
                                            ContainerImageIndexOCI
from image.platform                 import  ContainerImagePlatform
from image.reference                import  ContainerImageReference
from image.v2s2                     import  ContainerImageManifestV2S2, \
                                            ContainerImageManifestListV2S2

#########################################
# Classes for managing container images #
#########################################

# Override the default JSON encoder function to enable
# serializing classes as JSON
def wrapped_default(self, obj):
    return getattr(obj.__class__, "__json__", wrapped_default.default)(obj)
wrapped_default.default = json.JSONEncoder().default
json.JSONEncoder.original_default = json.JSONEncoder.default
json.JSONEncoder.default = wrapped_default

class ContainerImage(ContainerImageReference):
    """
    Extends the ContainerImageReference class and uses the
    ContainerImageRegistryClient class to provide a convenient interface
    through which users can specify their image reference, then query the
    registry API for information about the image.
    """
    @staticmethod
    def is_manifest_list_static(
            manifest: Union[
                ContainerImageManifestV2S2,
                ContainerImageManifestListV2S2,
                ContainerImageManifestOCI,
                ContainerImageIndexOCI
            ]
        ) -> bool:
        """
        Determine if an arbitrary manifest object is a manifest list

        Args:
            manifest (Union[ContainerImageManifestV2S2,ContainerImageManifestListV2S2,ContainerImageManifestOCI,ContainerImageIndexOCI]): The manifest object, generally from get_manifest method

        Returns:
            bool: Whether the manifest object is a list or single-arch
        """
        return isinstance(manifest, ContainerImageManifestList)
    
    @staticmethod
    def is_oci_static(
            manifest: Union[
                ContainerImageManifestV2S2,
                ContainerImageManifestListV2S2,
                ContainerImageManifestOCI,
                ContainerImageIndexOCI
            ]
        ) -> bool:
        """
        Determine if an arbitrary manifest object is an OCI manifest or image
        index.

        Args:
            manifest (Union[ContainerImageManifestV2S2,ContainerImageManifestListV2S2,ContainerImageManifestOCI,ContainerImageIndexOCI]): The manifest object, generally from get_manifest method

        Returns:
            bool: Whether the manifest object is in the OCI format
        """
        return isinstance(manifest, ContainerImageManifestOCI) or \
                isinstance(manifest, ContainerImageIndexOCI)
    
    @staticmethod
    def get_host_platform_manifest_static(
            ref: ContainerImageReference,
            manifest: Union[
                ContainerImageManifestV2S2,
                ContainerImageManifestListV2S2,
                ContainerImageManifestOCI,
                ContainerImageIndexOCI
            ],
            auth: Dict[str, Any]
        ) -> Union[
            ContainerImageManifestV2S2,
            ContainerImageManifestOCI
        ]:
        """
        Given an image's reference and manifest, this static method checks if
        the manifest is a manifest list, and attempts to get the manifest from
        the list matching the host platform.

        Args:
            ref (ContainerImageReference): The image reference corresponding to the manifest
            manifest (Union[ContainerImageManifestV2S2,ContainerImageManifestListV2S2,ContainerImageManifestOCI,ContainerImageIndexOCI]): The manifest object, generally from get_manifest method
            auth (Dict[str, Any]): A valid docker config JSON with auth into the ref's registry
        
        Returns:
            Union[ContainerImageManifestV2S2,ContainerImageManifestOCI]: The manifest response from the registry API

        Raises:
            ContainerImageError: Error if the image is a manifest list without a manifest matching the host platform
        """
        host_manifest = manifest

        # If manifest list, get the manifest matching the host platform
        if ContainerImage.is_manifest_list_static(manifest):
            found = False
            host_entry_digest = None
            host_plt = ContainerImagePlatform.get_host_platform()
            entries = manifest.get_entries()
            for entry in entries:
                if entry.get_platform() == host_plt:
                    found = True
                    host_entry_digest = entry.get_digest()
            if not found:
                raise ContainerImageError(
                    "no image found in manifest list for platform: " + \
                    f"{str(host_plt)}"
                )
            host_ref = ContainerImage(
                f"{ref.get_name()}@{host_entry_digest}"
            )
            host_manifest = host_ref.get_manifest(auth=auth)
        
        # Return the manifest matching the host platform
        return host_manifest

    @staticmethod
    def get_config_static(
            ref: ContainerImageReference,
            manifest: Union[
                ContainerImageManifestV2S2,
                ContainerImageManifestListV2S2,
                ContainerImageManifestOCI,
                ContainerImageIndexOCI
            ],
            auth: Dict[str, Any]
        ) -> ContainerImageConfig:
        """
        Given an image's manifest, this static method fetches that image's
        config from the distribution registry API.  If the image is a manifest
        list, then it gets the config corresponding to the manifest matching
        the host platform.

        Args:
            ref (ContainerImageReference): The image reference corresponding to the manifest
            manifest (Union[ContainerImageManifestV2S2,ContainerImageManifestListV2S2,ContainerImageManifestOCI,ContainerImageIndexOCI]): The manifest object, generally from get_manifest method
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
        
        Returns:
            ContainerImageConfig: The config for this image

        Raises:
            ContainerImageError: Error if the image is a manifest list without a manifest matching the host platform
        """
        # If manifest list, get the manifest matching the host platform
        manifest = ContainerImage.get_host_platform_manifest_static(
            ref, manifest, auth
        )
        
        # Get the image's config
        return ContainerImageConfig(
            ContainerImageRegistryClient.get_config(
                ref,
                manifest.get_config_descriptor(),
                auth=auth
            )
        )

    def __init__(self, ref: str):
        """
        Constructor for the ContainerImage class

        Args:
            ref (str): The image reference
        """
        # Validate the image reference
        valid, err = ContainerImage.validate_static(ref)
        if not valid:
            raise ContainerImageError(err)

        # Set the image reference property
        self.ref = ref
    
    def validate(self) -> bool:
        """
        Validates an image reference

        Returns:
            bool: Whether the ContainerImage's reference is valid
        """
        return ContainerImage.validate_static(self.ref)
    
    def get_digest(self, auth: Dict[str, Any]) -> str:
        """
        Parses the digest from the reference if digest reference, or fetches
        it from the registry if tag reference

        Args:
            auth (Dict[str, Any]): A valid docker config JSON

        Returns:
            str: The image digest
        """
        if self.is_digest_ref():
            return self.get_identifier()
        return ContainerImageRegistryClient.get_digest(self, auth)
    
    def get_platforms(self, auth: Dict[str, Any]) -> List[
            ContainerImagePlatform
        ]:
        """
        Returns the supported platform(s) for the image as a list of
        ContainerImagePlatforms

        Args:
            auth (Dict[str, Any]): A valid docker config JSON

        Returns:
            List[ContainerImagePlatform]: The supported platforms
        """
        # If manifest, get the config and get its platform
        manifest = self.get_manifest(auth)
        platforms = []
        if not ContainerImage.is_manifest_list_static(manifest):
            config_desc = manifest.get_config_descriptor()
            config_dict = ContainerImageRegistryClient.get_config(
                self,
                config_desc,
                auth
            )
            config = ContainerImageConfig(config_dict)
            platforms = [ config.get_platform() ]
        else:
            for entry in manifest.get_entries():
                platforms.append(entry.get_platform())
        return platforms

    def get_manifest(self, auth: Dict[str, Any]) -> Union[
            ContainerImageManifestV2S2,
            ContainerImageManifestListV2S2,
            ContainerImageManifestOCI,
            ContainerImageIndexOCI
        ]:
        """
        Fetches the manifest from the distribution registry API

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry

        Returns:
            Union[ContainerImageManifestV2S2,ContainerImageManifestListV2S2,ContainerImageManifestOCI,ContainerImageIndexOCI]: The manifest or manifest list response from the registry API
        """
        # Ensure the ref is valid, if not raise an exception
        valid, err = self.validate()
        if not valid:
            raise ContainerImageError(err)
        
        # Use the container image registry client to get the manifest
        return ContainerImageManifestFactory.create(
            ContainerImageRegistryClient.get_manifest(self, auth)
        )
    
    def get_host_platform_manifest(self, auth: Dict[str, Any]) -> Union[
            ContainerImageManifestOCI,
            ContainerImageManifestV2S2
        ]:
        """
        Fetches the manifest from the distribution registry API.  If the
        manifest is a manifest list, then it attempts to fetch the manifest
        in the list matching the host platform.  If not found, an exception is
        raised.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
        
        Returns:
            Union[ContainerImageManifestV2S2,ContainerImageManifestOCI]: The manifest response from the registry API

        Raises:
            ContainerImageError: Error if the image is a manifest list without a manifest matching the host platform
        """
        # Get the container image's manifest
        manifest = self.get_manifest(auth=auth)
        
        # Return the host platform manifest
        return ContainerImage.get_host_platform_manifest_static(
            self,
            manifest,
            auth
        )

    def get_config(self, auth: Dict[str, Any]) -> ContainerImageConfig:
        """
        Fetches the image's config from the distribution registry API.  If the
        image is a manifest list, then it gets the config corresponding to the
        manifest matching the host platform.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
        
        Returns:
            ContainerImageConfig: The config for this image

        Raises:
            ContainerImageError: Error if the image is a manifest list without a manifest matching the host platform
        """
        # Get the image's manifest
        manifest = self.get_manifest(auth=auth)

        # Use the image's manifest to get the image's config
        config = ContainerImage.get_config_static(
            self, manifest, auth
        )

        # Return the image's config
        return config

    def list_tags(self, auth: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetches the list of tags for the image from the distribution registry
        API.
        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
        
        Returns:
            Dict[str, Any]: The tag list loaded into a dict
        """
        return ContainerImageRegistryClient.list_tags(self, auth)

    def exists(self, auth: Dict[str, Any]) -> bool:
        """
        Determine if the image reference corresponds to an image in the remote
        registry.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
        
        Returns:
            bool: Whether the image exists in the registry
        """
        try:
            ContainerImageRegistryClient.get_manifest(self, auth)
        except requests.HTTPError as he:
            if he.response.status_code == 404:
                return False
            else:
                raise he
        return True

    def is_manifest_list(self, auth: Dict[str, Any]) -> bool:
        """
        Determine if the image is a manifest list

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry

        Returns:
            bool: Whether the image is a manifest list or single-arch
        """
        return ContainerImage.is_manifest_list_static(self.get_manifest(auth))

    def is_oci(self, auth: Dict[str, Any]) -> bool:
        """
        Determine if the image is in the OCI format

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
        
        Returns:
            bool: Whether the image is in the OCI format
        """
        return ContainerImage.is_oci_static(self.get_manifest(auth))

    def get_media_type(self, auth: Dict[str, Any]) -> str:
        """
        Gets the image's mediaType from its manifest

        Args:
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict

        Returns:
            str: The image's mediaType
        """
        return self.get_manifest(auth).get_media_type()

    def get_size(self, auth: Dict[str, Any]) -> int:
        """
        Calculates the size of the image by fetching its manifest metadata
        from the registry.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict

        Returns:
            int: The size of the image in bytes
        """
        # Get the manifest and calculate its size
        manifest = self.get_manifest(auth)
        if ContainerImage.is_manifest_list_static(manifest):
            return manifest.get_size(self.get_name(), auth)
        else:
            return manifest.get_size()

    def get_size_formatted(self, auth: Dict[str, Any]) -> str:
        """
        Calculates the size of the image by fetching its manifest metadata
        from the registry.  Formats as a human readable string (e.g. 3.14 KB)

        Args:
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict

        Returns:
            str: The size of the image in bytes in human readable format (1.25 GB)
        """
        return ByteUnit.format_size_bytes(self.get_size(auth))
    
    def inspect(self, auth: Dict[str, Any]) -> ContainerImageInspect:
        """
        Returns a collection of basic information about the image, equivalent
        to skopeo inspect.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
        
        Returns:
            ContainerImageInspect: A collection of information about the image
        """
        # Get the image's manifest
        manifest = self.get_host_platform_manifest(auth=auth)

        # Use the image's manifest to get the image's config
        config = ContainerImage.get_config_static(
            self, manifest, auth
        )

        # List the image's tags
        tags = self.list_tags(auth)

        # Format the inspect dictionary
        inspect = {
            "Name": self.get_name(),
            "Digest": self.get_digest(auth=auth),
            "RepoTags": tags["tags"],
            # TODO: Implement v2s1 manifest extension - only v2s1 manifests use this value
            "DockerVersion": "",
            "Created": config.get_created_date(),
            "Labels": config.get_labels(),
            "Architecture": config.get_architecture(),
            "Os": config.get_os(),
            "Layers": [ 
                layer.get_digest() \
                for layer \
                in manifest.get_layer_descriptors()
            ],
            "LayersData": [
                {
                    "MIMEType": layer.get_media_type(),
                    "Digest": layer.get_digest(),
                    "Size": layer.get_size(),
                    "Annotations": layer.get_annotations() or {}
                } for layer in manifest.get_layer_descriptors()
            ],
            "Env": config.get_env()
        }

        # Set the variant in the inspect dict if found
        variant = config.get_variant()
        if variant:
            inspect["Variant"] = variant

        # Set the tag in the inspect dict
        if self.is_tag_ref():
            inspect["Tag"] = self.get_identifier()
        
        # TODO: Get the RepoTags for the image
        return ContainerImageInspect(inspect)

    def delete(self, auth: Dict[str, Any]):
        """
        Deletes the image from the registry.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
        """
        # Ensure the ref is valid, if not raise an exception
        valid, err = self.validate()
        if not valid:
            raise ContainerImageError(err)
        ContainerImageRegistryClient.delete(self, auth)

class ContainerImageList:
    """
    Represents a list of ContainerImages. Enables performing bulk actions
    against many container images at once.
    """
    def __init__(self):
        """
        Constructor for ContainerImageList class
        """
        self.images = []
    
    def __len__(self) -> int:
        """
        Returns the length of the ContainerImageList

        Returns:
            int: The length of the ContainerImageList
        """
        return len(self.images)
    
    def __iter__(self) -> Iterator[ContainerImage]:
        """
        Returns an iterator over the ContainerImageList 

        Returns:
            Iterator[ContainerImage]: The iterator over the ContainerImageList
        """
        return iter(self.images)
    
    def append(self, image: Type[ContainerImage]):
        """
        Append a new ContainerImage to the ContainerImageList

        Args:
            image (Type[ContainerImage]): The ContainerImage to add
        """
        self.images.append(image)

    def get_size(self, auth: Dict[str, Any]) -> int:
        """
        Get the deduplicated size of all container images in the list

        Args:
            auth (Dict[str, Any]): A valid docker config JSON dict

        Returns:
            int: The deduplicated size of all container images in the list
        """
        # Aggregate all layer and config digests, sum manifest list entries
        entry_sizes = 0
        layers = {}
        configs = {}

        # Loop through each image in the list
        for image in self.images:
            # Get the image's manifest
            manifest = image.get_manifest(auth)

            # If a manifest list, get its configs, entry sizes, layers
            image_layers = []
            image_configs = []
            if ContainerImage.is_manifest_list_static(manifest):
                entry_sizes += manifest.get_entry_sizes()
                image_layers = manifest.get_layer_descriptors(image.get_name(), auth)
                image_configs = manifest.get_config_descriptors(image.get_name(), auth)
            # If an arch manifest, get its config, layers
            else:
                image_configs = [manifest.get_config_descriptor()]
                image_layers = manifest.get_layer_descriptors()
            
            # Append the configs & layers to the aggregated dicts
            for image_config in image_configs:
                config_digest = image_config.get_digest()
                config_size = image_config.get_size()
                configs[config_digest] = config_size
            for image_layer in image_layers:
                layer_digest = image_layer.get_digest()
                layer_size = image_layer.get_size()
                layers[layer_digest] = layer_size
        
        # Calculate the layer and config sizes
        layer_sizes = 0
        config_sizes = 0
        for digest in layers.keys():
            layer_sizes += layers[digest]
        for digest in configs.keys():
            config_sizes += configs[digest]
        
        # Return the summed size
        return layer_sizes + config_sizes + entry_sizes
    
    def get_size_formatted(self, auth: Dict[str, Any]) -> str:
        """
        Get the deduplicated size of all container images in the list,
        formatted as a human readable string (e.g. 3.14 MB)

        Args:
            auth (Dict[str, Any]): A valid docker config JSON dict

        Returns:
            str: List size in bytes formatted to nearest unit (ex. "1.23 MB")
        """
        return ByteUnit.format_size_bytes(self.get_size(auth))
    
    def delete(self, auth: Dict[str, Any]):
        """
        Delete all of the container images in the list from the registry

        Args:
            auth (Dict[str, Any]): A valid docker config JSON dict
        """
        for image in self.images:
            image.delete(auth)

    def diff(self, previous: Type[ContainerImageList]) -> Type[ContainerImageListDiff]:
        """
        Compare this ContainerImageList with another and identify images which
        were added, removed, updated, and common across both instances.  Here,
        the receiver ContainerImageList is viewed as the current version, while
        the argument ContainerImageList is viewed as the previous version.

        Args:
            previous (Type[ContainerImageList]): The "previous" ContainerImageList

        Returns:
            Type[ContainerImageListDiff]: The diff between the ContainerImageLists
        """
        # Initialize a ContainerImageListDiff
        diff = ContainerImageListDiff()

        # Construct a mapping of image name to current and prev image instance
        images = {}
        for image in self.images:
            image_name = image.get_name()
            if image_name not in images:
                images[image_name] = {}
            images[image_name]['current'] = image
        for image in previous.images:
            image_name = image.get_name()
            if image_name not in images:
                images[image_name] = {}
            images[image_name]['previous'] = image

        # Use the mapping to populate the diff
        for image_name, keys in images.items():
            if 'current' in keys and 'previous' in keys:
                current_identifier = images[image_name]['current'].get_identifier()
                previous_identifier = images[image_name]['previous'].get_identifier()
                if current_identifier == previous_identifier:
                    diff.common.append(images[image_name]['current'])
                    continue
                diff.updated.append(images[image_name]['current'])
            elif 'current' in images[image_name]:
                diff.added.append(images[image_name]['current'])
            elif 'previous' in images[image_name]:
                diff.removed.append(images[image_name]['previous'])
        return diff

class ContainerImageListDiff:
    """
    Represents a diff between two ContainerImageLists
    """
    def __init__(self):
        """
        Constructor for the ContainerImageListDiff class
        """
        self.added = ContainerImageList()
        self.removed = ContainerImageList()
        self.updated = ContainerImageList()
        self.common = ContainerImageList()

    def __str__(self) -> str:
        """
        Formats a ContainerImageListDiff as a string

        Returns:
            str: The ContainerImageListDiff formatted as a string
        """
        # Format the summary
        summary =   f"Added:\t{len(self.added)}\n" + \
                    f"Removed:\t{len(self.removed)}\n" + \
                    f"Updated:\t{len(self.updated)}\n" + \
                    f"Common:\t{len(self.common)}"
        
        # Format the added, removed, updated, and common sections
        added = "\n".join([str(img) for img in self.added])
        removed = "\n".join([str(img) for img in self.removed])
        updated = "\n".join([str(img) for img in self.updated])
        common = "\n".join([str(img) for img in self.common])

        # Format the stringified diff
        diff_str =  f"Summary\n{summary}\n\nAdded\n{added}\n\n" + \
                    f"Removed\n{removed}\n\nUpdated\n{updated}\n\n" + \
                    f"Common\n{common}"
        return diff_str
