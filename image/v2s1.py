from jsonschema import validate, ValidationError
from typing import Dict, Any, Tuple
from image.v2s2 import ContainerImageManifestV2S2
from image.v2s1schema import MANIFEST_V1_SCHEMA

class ContainerImageManifestV2S1:
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
            validate(instance=manifest, schema=MANIFEST_V1_SCHEMA)
        except Exception as e:
            return False, str(e)
        return True, ""

    def __init__(
            self,
            manifest: Dict[str, Any]
        ) -> "ContainerImageManifestV2S1":
        """
        Constructor for the ContainerImageManifestV2S1 class

        Args:
            manifest (Dict[str, Any]): The manifest loaded into a dict
        
        Return:
            ContainerImageManifestV2S1: The initialized manifest object
        """
        # Validate the manifest dict
        valid, err = ContainerImageManifestV2S1.validate_static(manifest)
        if not valid:
            raise ValidationError(err)
        
        # Save the manifest dict as an object property
        self.manifest = manifest

    def validate(self) -> Tuple[bool, str]:
        """
        Validates a ContainerImageManifestV2S1 instance

        Returns:
            bool: Whether the manifest is valid
            str: Error message if the manifest is invalid
        """
        return ContainerImageManifestV2S1.validate_static(self.manifest)

    def to_v2s2(self) -> ContainerImageManifestV2S2:
        """
        Converts a ContainerImageManifestV2S1 to a ContainerImageManifestV2S2

        Returns:
            ContainerImageManifestV2S2: The manifest converted to v2
        """
        # TODO: Implement
        return ContainerImageManifestV2S2()
