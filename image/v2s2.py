"""
Contains docker v2s2-specific implementations of the container image manifest,
manifest list entry, and manifest list classes
"""

import json
import re
from typing import Dict, Any, Tuple, List
from jsonschema import validate, ValidationError
from image.descriptor           import  ContainerImageDescriptor
from image.manifest             import  ContainerImageManifest
from image.manifestlist         import  ContainerImageManifestList
from image.manifestlistentry    import  ContainerImageManifestListEntry
from image.mediatypes           import  OCI_INDEX_MEDIA_TYPE, \
                                        OCI_MANIFEST_MEDIA_TYPE
from image.platform             import  ContainerImagePlatform
from image.regex                import  ANCHORED_DIGEST
from image.v2s2schema           import  MANIFEST_V2_SCHEMA, \
                                        MANIFEST_LIST_V2_SCHEMA, \
                                        MANIFEST_LIST_V2_ENTRY_SCHEMA

# See doc comments below
UNSUPPORTED_V2S2_MANIFEST_MEDIA_TYPES = [
    OCI_MANIFEST_MEDIA_TYPE
]
"""
A list of mediaTypes which are not supported by the v2s2 manifest spec.
This mainly just includes the OCI manifest mediaType.
"""

# See doc comments below
UNSUPPORTED_V2S2_MANIFEST_LIST_MEDIA_TYPES = [
    OCI_INDEX_MEDIA_TYPE
]
"""
A list of mediaTypes which are not supported by the v2s2 manifest list
spec.  This mainly just includes the OCI index mediaType.
"""

"""
ContainerImageManifestV2S2 class

Represents an arch manifest returned from the distribution registry API.
Contains validation logic and getters for manifest metadata following the
manifest v2s2 specification.
"""
class ContainerImageManifestV2S2(ContainerImageManifest):
    @staticmethod
    def validate_static(manifest: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates an image manifest

        Args:
            manifest (Dict[str, Any]): The manifest to validate

        Returns:
            Tuple[bool, str]: Whether the manifest is valid, error message
        """
        # Validate the image manifest
        try:
            validate(instance=manifest, schema=MANIFEST_V2_SCHEMA)
        except Exception as e:
            return False, str(e)
        
        # Validate the image manifest config
        config_valid, err = ContainerImageDescriptor.validate_static(
            manifest["config"]
        )
        if not config_valid:
            return config_valid, err

        # Validate the image layers
        for layer in manifest["layers"]:
            layer_valid, err = ContainerImageDescriptor.validate_static(layer)
            if not layer_valid:
                return layer_valid, err
        
        # Validate the mediaType
        if manifest["mediaType"] in UNSUPPORTED_V2S2_MANIFEST_MEDIA_TYPES:
            return False, f"Unsupported mediaType: {manifest['mediaType']}"

        # If all are valid, return True with empty error message
        return True, ""
    
    @staticmethod
    def from_manifest(manifest: ContainerImageManifest):
        """
        Convert a ContainerImageManifest to a v2s2 manifest instance

        Args:
            manifest_list (ContainerImageManifest): The generic manifest instance
        
        Returns:
            ContainerImageManifestV2S2: The v2s2 manifest instance
        """
        return ContainerImageManifestV2S2(manifest.raw())

    def __init__(self, manifest: bytes):
        """
        Constructor for the ContainerImageManifestV2S2 class

        Args:
            manifest (bytes): The raw manifest bytes
        """
        # Load the manifest as a dict
        loaded = json.loads(manifest)

        # Validate the image manifest
        valid, err = ContainerImageManifestV2S2.validate_static(loaded)
        if not valid:
            raise ValidationError(err)

        # If valid, instantiate the manifest
        super().__init__(manifest)

    def validate(self) -> Tuple[bool, str]:
        """
        Validates an image manifest instance

        Returns:
            Tuple[bool, str]: Whether the manifest is valid, error message
        """
        # Validate the image manifest
        return ContainerImageManifestV2S2.validate_static(self.manifest)

"""
ContainerImageManifestListEntryV2S2 class

Represents a manifest list entry in a manifest list response from the
distribution registry API. Contains validation logic and getters for entry
metadata following the manifest v2s2 specification.
"""
class ContainerImageManifestListEntryV2S2(ContainerImageManifestListEntry):
    @staticmethod
    def validate_static(entry: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates an image manifest list entry

        Args:
            entry (Dict[str, Any]): The manifest list entry to validate

        Returns:
            Tuple[bool, str]: Whether the manifest list entry is valid, error msg
        """
        # Validate the image manifest list entry
        try:
            validate(instance=entry, schema=MANIFEST_LIST_V2_ENTRY_SCHEMA)
        except Exception as e:
            return False, str(e)
        
        # Validate the image manifest list entry digest
        digest_valid = bool(re.match(ANCHORED_DIGEST, entry["digest"]))
        if not digest_valid:
            return False, f"Invalid digest: {entry['digest']}"

        # Validate the manifest list entry platform
        platform_valid, err = ContainerImagePlatform.validate_static(
            entry["platform"]
        )
        if not platform_valid:
            return platform_valid, err

        # Valid if all of the above are valid
        return True, ""

    @staticmethod
    def from_manifest_list_entry(entry: ContainerImageManifestListEntry):
        """
        Convert a ContainerImageManifestListEntry to a v2s2 manifest list entry
        instance

        Args:
            manifest_list (ContainerImageManifestList): The generic manifest list entry instance
        
        Returns:
            ContainerImageManifestListEntryV2S2: The v2s2 manifest list entry instance
        """
        return ContainerImageManifestListEntryV2S2(entry.entry)

    def __init__(self, entry: Dict[str, Any]):
        """
        Constructor for the ContainerImageManifestListEntryV2S2 class

        Args:
            entry (Dict[str, Any]): The manifest list entry loaded into a dict
        """
        # Validate the image manifest list entry
        valid, err = ContainerImageManifestListEntryV2S2.validate_static(
            entry
        )
        if not valid:
            raise ValidationError(err)

        # If both valid, instantiate the manifest list entry
        super().__init__(entry)

    def validate(self) -> Tuple[bool, str]:
        """
        Validates an image manifest list entry instance

        Returns:
            Tuple[bool, str]: Whether the manifest list entry is valid, error msg
        """
        # Validate the image manifest list
        return ContainerImageManifestListEntryV2S2.validate_static(
            self.entry
        )

"""
ContainerImageManifestListV2S2 class

Represents a manifest list returned from the distribution registry API.
Contains validation logic and getters for manifest list metadata following the
manifest v2s2 specification.
"""
class ContainerImageManifestListV2S2(ContainerImageManifestList):
    @staticmethod
    def validate_static(manifest_list: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates an image manifest list

        Args:
            manifest_list (Dict[str, Any]): The manifest list to validate

        Returns:
            Tuple[bool, str]: Whether the manifest list is valid, error message
        """
        # Validate the image manifest list
        try:
            validate(instance=manifest_list, schema=MANIFEST_LIST_V2_SCHEMA)
        except Exception as e:
            return False, str(e)
        
        # Validate the manifest list entries
        for entry in manifest_list["manifests"]:
            entry_valid, err = ContainerImageManifestListEntryV2S2.validate_static(
                entry
            )
            if not entry_valid:
                return entry_valid, err
        
        # Validate the mediaType, if unsupported then error
        if manifest_list["mediaType"] in UNSUPPORTED_V2S2_MANIFEST_LIST_MEDIA_TYPES:
            return False, f"Unsupported mediaType: {manifest_list['mediaType']}"

        # Success if both valid
        return True, ""
    
    @staticmethod
    def from_manifest_list(
            manifest_list: ContainerImageManifestList
        ) -> "ContainerImageManifestListV2S2":
        """
        Convert a ContainerImageManifestList to a v2s2 manifest list instance

        Args:
            manifest_list ContainerImageManifestList: The generic manifest list instance
        
        Returns:
            ContainerImageManifestListV2S2: The v2s2 manifest list instance
        """
        return ContainerImageManifestListV2S2(manifest_list.raw())

    def __init__(self, manifest_list: bytes):
        """
        Constructor for the ContainerImageManifestListV2S2 class

        Args:
            manifest_list (bytes): The raw manifest list bytes
        """
        # Load the manifest list as a dict
        loaded = json.loads(manifest_list)

        # Validate the image manifest list
        valid, err = ContainerImageManifestListV2S2.validate_static(loaded)
        if not valid:
            raise ValidationError(err)

        # If both valid, instantiate the manifest list
        super().__init__(manifest_list)

    def validate(self) -> Tuple[bool, str]:
        """
        Validates an image manifest list instance

        Returns:
            Tuple[bool, str]: Whether the manifest list is valid, error message
        """
        # Validate the image manifest list
        return ContainerImageManifestListV2S2.validate_static(
            self.manifest_list
        )

    def get_v2s2_entries(self) -> List[
            ContainerImageManifestListEntryV2S2
        ]:
        """
        Returns the manifest list entries as ContainerImageManifestListEntryV2S2
        instances

        Returns:
            List[ContainerImageManifestListEntryV2S2]: The entries
        """
        entries = self.get_entries()
        for i in range(len(entries)):
            # Convert each entry to a v2s2 entry
            entries[i] = ContainerImageManifestListEntryV2S2.from_manifest_list_entry(
                entries[i]
            )
        return entries

    def get_v2s2_manifests(
            self, name: str, auth: Dict[str, Any]
        ) -> List[ContainerImageManifestV2S2]:
        """
        Fetches the arch manifests from the distribution registry API and
        returns as a list of ContainerImageManifestV2S2s

        Args:
            name (str): A valid image name, the name of the manifest
            auth (Dict[str, Any]): A valid docker config JSON dict

        Returns:
            List[ContainerImageManifestV2S2]: The arch manifests
        """
        manifests = self.get_manifests(name, auth)
        for i in range(len(manifests)):
            # Convert each manifest to a v2s2 manifest
            manifests[i] = ContainerImageManifestV2S2.from_manifest(
                manifests[i]
            )
        return manifests
