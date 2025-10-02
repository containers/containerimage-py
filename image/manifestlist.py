"""
Contains a base ContainerImageManifestList class which is extended by the
docker v2s2 and OCI specifications for their respective manifest list
implementations
"""

import re
import json
from image.client               import ContainerImageRegistryClient, DEFAULT_TIMEOUT
from image.descriptor           import ContainerImageDescriptor
from image.manifest             import ContainerImageManifest
from image.manifestlistentry    import ContainerImageManifestListEntry
from image.regex                import ANCHORED_NAME
from typing                     import Dict, Any, List

class ContainerImageManifestList:
    """
    Represents a manifest list returned from the distribution registry API.
    This is a base class extended by the ContainerImageManifestListV2S2 and
    ContainerImageManifestListOCI since the two specs are very similar, with the
    v2s2 spec being more restrictive than the OCI spec.
    """
    def __init__(self, manifest_list: bytes):
        """
        Constructor for the ContainerImageManifestList class

        Args:
            manifest_list (bytes): The raw manifest list bytes
        """
        self.raw_manifest_list = manifest_list
        self.manifest_list = json.loads(manifest_list)

    def get_entries(self) -> List[ContainerImageManifestListEntry]:
        """
        Returns the manifest list entries as ContainerImageManifestListEntry
        instances

        Returns:
            List[ContainerImageManifestListEntry]: The entries
        """
        # Loop through each entry in the manifest list and append to the list
        entries = []
        manifest_entries = list(self.manifest_list.get("manifests"))
        for entry in manifest_entries:
            entries.append(
                ContainerImageManifestListEntry(entry)
            )
        
        # Return the list of manifest list entries
        return entries

    def get_entry_sizes(self) -> int:
        """
        Returns the combined size of each of the entries in the list

        Returns:
            int: The combined size of each of the entries in the list
        """
        # Loop through each entry in the manifest list and add its size
        # into the total
        size = 0
        entries = self.get_entries()
        for entry in entries:
            size += entry.get_size()
        return size

    def get_manifests(
            self,
            name: str,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> List[
            ContainerImageManifest
        ]:
        """
        Fetches the arch manifests from the distribution registry API

        Args:
            name (str): A valid image name, the name of the manifest
            auth (Dict[str, Any]): A valid docker config JSON dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            List[ContainerImageManifest]: The arch manifests
        """
        # Validate the image name
        valid = bool(re.match(ANCHORED_NAME, name))
        if not valid:
            return False, f"Invalid name: {name}"

        # Loop through each manifest in the manifest list
        manifests = []
        manifest_entries = self.get_entries()
        for entry in manifest_entries:
            # Construct and validate the arch image ref
            manifest_digest = entry.get_digest()
            ref = f"{name}@{manifest_digest}"

            # Get the arch image's manifest from the registry, append to list
            manifest_dict = ContainerImageRegistryClient.get_manifest(
                ref, auth, skip_verify=skip_verify, http=http, timeout=timeout
            )
            manifest = ContainerImageManifest(manifest_dict)
            manifests.append(manifest)
        
        # Return the list of manifests
        return manifests

    def get_layer_descriptors(
            self,
            name: str,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> List[
            ContainerImageDescriptor
        ]:
        """
        Retrieves the layer descriptors for each manifest image combined
        into a list

        Args:
            name (str): A valid image name, the name of the manifest
            auth (Dict[str, Any]): A valid docker config JSON dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            int: The list of layer descriptors across each of the manifests
        """
        layers = []
        manifests = self.get_manifests(
            name, auth, skip_verify=skip_verify, http=http, timeout=timeout
        )
        for manifest in manifests:
            layers.extend(
                manifest.get_layer_descriptors()
            )
        return layers

    def get_config_descriptors(
            self,
            name: str,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> List[
            ContainerImageDescriptor
        ]:
        """
        Retrieves the config descriptors for each manifest image combined
        into a list

        Args:
            name (str): A valid image name, the name of the manifest
            auth (Dict[str, Any]): A valid docker config JSON dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            List[ContainerImageDescriptor]: The list of config descriptors across each of the manifests
        """
        configs = []
        manifests = self.get_manifests(
            name, auth, skip_verify=skip_verify, http=http, timeout=timeout
        )
        for manifest in manifests:
            configs.append(manifest.get_config_descriptor())
        return configs
    
    def get_media_type(self) -> str:
        """
        Returns the mediaType of the container image manifest list

        Returns:
            str: The container image manifest list mediaType
        """
        return str(self.manifest_list.get("mediaType"))

    def get_size(
            self,
            name: str,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> int:
        """
        Calculates the size of the image using the distribution registry API

        Args:
            name (str): A valid image name, the name of the manifest
            auth (Dict[str, Any]): A valid docker config JSON dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            int: The size of the manifest list in bytes
        """
        # Validate the image name
        valid = bool(re.match(ANCHORED_NAME, name))
        if not valid:
            return False, f"Invalid name: {name}"

        # Loop through each manifest in the manifest list
        configs = {}
        layers = {}
        entry_sizes = 0
        manifest_entries = self.get_entries()
        for entry in manifest_entries:
            # Get the manifest list entry size
            entry_sizes += entry.get_size()

            # Construct and validate the arch image ref
            manifest_digest = entry.get_digest()
            ref = f"{name}@{manifest_digest}"

            # Get the arch image's manifest from the registry
            manifest_dict = ContainerImageRegistryClient.get_manifest(
                ref, auth, skip_verify=skip_verify, http=http, timeout=timeout
            )
            manifest = ContainerImageManifest(manifest_dict)

            # Get the arch image's layer and config descriptors
            manifest_layers = manifest.get_layer_descriptors()
            manifest_config = manifest.get_config_descriptor()

            # Append config to configs dict
            config_digest = manifest_config.get_digest()
            config_size = manifest_config.get_size()
            configs[config_digest] = config_size

            # Append layers to layers dict
            for layer in manifest_layers:
                layer_digest = layer.get_digest()
                layer_size = layer.get_size()
                layers[layer_digest] = layer_size

        # Sum the deduplicated size
        manifest_list_size = entry_sizes
        for digest in configs.keys():
            manifest_list_size += configs[digest]
        for digest in layers.keys():
            manifest_list_size += layers[digest]
        
        # Return the list of manifests
        return manifest_list_size

    def raw(self) -> bytes:
        """
        Returns the raw manifest list bytes

        Returns:
            bytes: The raw manifest list bytes
        """
        return self.raw_manifest_list

    def __str__(self) -> str:
        """
        Formats the ContainerImageManifestListV2S2 as a string

        Returns:
            str: The ContainerImageManifestListV2S2 formatted as a string
        """
        return json.dumps(self.manifest_list, indent=3, sort_keys=False)

    def __json__(self) -> Dict[str, Any]:
        """
        Formats the ContainerImageManifestListV2S2 as a JSON dict

        Returns:
            Dict[str, Any]: The ContainerImageManifestListV2S2 formatted as a JSON dict
        """
        return self.manifest_list
