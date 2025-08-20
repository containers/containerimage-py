"""
Contains OCI-specific implementations of the container image manifest,
manifest list entry, and manifest list classes
"""

import json
import re
from typing                     import  Dict, Any, Tuple, List
from jsonschema                 import  validate, ValidationError
from image.descriptor           import  ContainerImageDescriptor
from image.manifest             import  ContainerImageManifest
from image.manifestlist         import  ContainerImageManifestList
from image.manifestlistentry    import  ContainerImageManifestListEntry
from image.mediatypes           import  DOCKER_V2S2_LIST_MEDIA_TYPE, \
                                        DOCKER_V2S2_MEDIA_TYPE
from image.platform             import  ContainerImagePlatform
from image.regex                import  ANCHORED_DIGEST
from image.ocischema            import  MANIFEST_OCI_SCHEMA, \
                                        IMAGE_INDEX_OCI_SCHEMA, \
                                        IMAGE_INDEX_ENTRY_OCI_SCHEMA

# See doc comments below
UNSUPPORTED_OCI_INDEX_MEDIA_TYPES = [
    DOCKER_V2S2_LIST_MEDIA_TYPE
]
"""
A list of mediaTypes which are not supported by the OCI image index spec.
This mainly just includes the Docker v2s2 manifest list mediaType.
"""

# See doc comments below
UNSUPPORTED_OCI_MANIFEST_MEDIA_TYPES = [
    DOCKER_V2S2_MEDIA_TYPE
]
"""
A list of mediaTypes which are not supported by the OCI manifest spec.
This mainly just includes the Docker v2s2 manifest mediaType.
"""

class ContainerImageManifestOCI(ContainerImageManifest):
    """
    Represents an arch manifest returned from the distribution registry API.
    Contains validation logic and getters for manifest metadata following the
    manifest OCI specification.
    """
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
            validate(instance=manifest, schema=MANIFEST_OCI_SCHEMA)
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
        
        # If there is a mediaType, ensure it is not a v2s2 manifest
        if "mediaType" in manifest.keys():
            if manifest["mediaType"] in UNSUPPORTED_OCI_MANIFEST_MEDIA_TYPES:
                return False, f"Unsupported mediaType: {manifest['mediaType']}"

        # If all are valid, return True with empty error message
        return True, ""

    @staticmethod
    def from_manifest(manifest: ContainerImageManifest):
        """
        Converts a generic ContainerImageManifest into an OCI manifst instance

        Args:
            manifest (ContainerImageManifest): The generic manifest

        Returns:
            ContainerImageManifestOCI: The OCI manifest instance
        """
        return ContainerImageManifestOCI(manifest.raw())

    def __init__(self, manifest: bytes):
        """
        Constructor for the ContainerImageManifestOCI class

        Args:
            manifest (bytes): The raw manifest bytes
        """
        # Load the manifest as a dict
        loaded = json.loads(manifest)

        # Validate the image manifest
        valid, err = ContainerImageManifestOCI.validate_static(loaded)
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
        return ContainerImageManifestOCI.validate_static(self.manifest)

"""
ContainerImageIndexEntryOCI class

Represents an image index entry in an OCI image index response from the
distribution registry API. Contains validation logic and getters for entry
metadata following the OCI image index specification.
"""
class ContainerImageIndexEntryOCI(ContainerImageManifestListEntry):
    @staticmethod
    def validate_static(entry: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates an image index entry

        Args:
            entry (Dict[str, Any]): The index entry to validate

        Returns:
            Tuple[bool, str]: Whether the index entry is valid, error msg
        """
        # Validate the image index entry
        try:
            validate(instance=entry, schema=IMAGE_INDEX_ENTRY_OCI_SCHEMA)
        except Exception as e:
            return False, str(e)
        
        # Validate the image index entry digest
        digest_valid = bool(re.match(ANCHORED_DIGEST, entry["digest"]))
        if not digest_valid:
            return False, f"Invalid digest: {entry['digest']}"

        # Validate the index entry platform, if given
        if "platform" in entry.keys():
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
        Converts a generic ContainerImageManifestListEntry into an OCI image
        index entry

        Args:
            entry (ContainerImageManifestListEntry): The generic entry

        Returns:
            ContainerImageIndexEntryOCI: The OCI image index entry
        """
        return ContainerImageIndexEntryOCI(entry.entry)

    def __init__(self, entry: Dict[str, Any]):
        """
        Constructor for the ContainerImageIndexEntryOCI class

        Args:
            entry (Dict[str, Any]): The index entry loaded into a dict
        """
        # Validate the image index entry
        valid, err = ContainerImageIndexEntryOCI.validate_static(
            entry
        )
        if not valid:
            raise ValidationError(err)

        # If both valid, instantiate the index entry
        super().__init__(entry)

    def validate(self) -> Tuple[bool, str]:
        """
        Validates an image index entry instance

        Returns:
            Tuple[bool, str]: Whether the index entry is valid, error msg
        """
        # Validate the image index
        return ContainerImageIndexEntryOCI.validate_static(
            self.entry
        )

"""
ContainerImageIndexOCI class

Represents an OCI image index returned from the distribution registry API.
Contains validation logic and getters for image index metadata following the
OCI image index specification.
"""
class ContainerImageIndexOCI(ContainerImageManifestList):
    @staticmethod
    def validate_static(manifest_list: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates an OCI image index

        Args:
            manifest_list (Dict[str, Any]): The image index to validate

        Returns:
            Tuple[bool, str]: Whether the image index valid, error message
        """
        # Validate the image index
        try:
            validate(instance=manifest_list, schema=IMAGE_INDEX_OCI_SCHEMA)
        except Exception as e:
            return False, str(e)
        
        # Validate the image index entries
        for entry in manifest_list["manifests"]:
            entry_valid, err = ContainerImageIndexEntryOCI.validate_static(
                entry
            )
            if not entry_valid:
                return entry_valid, err
        
        # Validate the mediaType, if unsupported then error
        if "mediaType" in manifest_list.keys():
            if manifest_list["mediaType"] in UNSUPPORTED_OCI_INDEX_MEDIA_TYPES:
                return False, f"Unsupported mediaType: {manifest_list['mediaType']}"

        # Success if both valid
        return True, ""
    
    @staticmethod
    def from_manifest_list(
            manifest_list: ContainerImageManifestList
        ) -> "ContainerImageIndexOCI":
        """
        Convert a ContainerImageManifestList to an OCI image index instance

        Args:
            manifest_list (ContainerImageManifestList): The generic manifest list instance
        
        Returns:
            ContainerImageIndexOCI: The OCI image index instance
        """
        return ContainerImageIndexOCI(manifest_list.raw())

    def __init__(self, index: bytes):
        """
        Constructor for the ContainerImageIndexOCI class

        Args:
            manifest_list (bytes): The raw image index bytes
        """
        # Load the image index as a dict
        loaded = json.loads(index)

        # Validate the image index
        valid, err = ContainerImageIndexOCI.validate_static(loaded)
        if not valid:
            raise ValidationError(err)

        # If both valid, instantiate the image index
        super().__init__(index)

    def validate(self) -> Tuple[bool, str]:
        """
        Validates an OCI image index instance

        Returns:
            Tuple[bool, str]: Whether the image index is valid, error message
        """
        # Validate the image manifest list
        return ContainerImageIndexOCI.validate_static(
            self.manifest_list
        )

    def get_oci_entries(self) -> List[
            ContainerImageIndexEntryOCI
        ]:
        """
        Returns the manifest list entries as ContainerImageIndexEntryOCI
        instances

        Returns:
            List[ContainerImageIndexEntryOCI]: The entries
        """
        entries = self.get_entries()
        for i in range(len(entries)):
            # Convert each entry to an OCI entry
            entries[i] = ContainerImageIndexEntryOCI.from_manifest_list_entry(
                entries[i]
            )
        return entries

    def get_oci_manifests(
            self, name: str, auth: Dict[str, Any]
        ) -> List[ContainerImageManifestOCI]:
        """
        Fetches the arch manifests from the distribution registry API and
        returns as a list of ContainerImageManifestOCI instances

        Args:
            name (str): A valid image name, the name of the manifest
            auth (Dict[str, Any]): A valid docker config JSON dict

        Returns:
            List[ContainerImageManifestOCI]: The arch manifests
        """
        manifests = self.get_manifests(name, auth)
        for i in range(len(manifests)):
            # Convert each manifest to an OCI manifest
            manifests[i] = ContainerImageManifestOCI.from_manifest(
                manifests[i]
            )
        return manifests
