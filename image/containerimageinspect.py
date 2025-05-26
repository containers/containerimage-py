import json
import re
from image.errors import ContainerImageError
from image.regex import ANCHORED_DIGEST, ANCHORED_NAME
from image.inspectschema import CONTAINER_IMAGE_INSPECT_SCHEMA
from jsonschema import validate
from typing import Dict, Any, Tuple

class ContainerImageInspect:
    """
    Represents a collection of basic informataion about a container image.
    This object is equivalent to the output of skopeo inspect.
    """
    @staticmethod
    def validate_static(inspect: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a container image inspect dict using its json schema

        Args:
            inspect (dict): The container image inspect dict to validate

        Returns:
            bool: Whether the container image inspect dict was valid
            str: Error message if it was invalid
        """
        # Validate the container image inspect dict against its json schema
        try:
            validate(
                instance=inspect,
                schema=CONTAINER_IMAGE_INSPECT_SCHEMA
            )
        except Exception as e:
            return False, str(e)
        
        # Validate the name and digest
        if len(inspect["Name"]) > 0 and not bool(re.match(ANCHORED_NAME, inspect["Name"])):
            return False, f"Invalid Name: {inspect['Name']}"
        if not bool(re.match(ANCHORED_DIGEST, inspect["Digest"])):
            return False, f"Invalid Digest: {inspect['Digest']}"

        # Validate the layer and layersdata digests
        for digest in inspect["Layers"]:
            if not bool(re.match(ANCHORED_DIGEST, digest)):
                return False, f"Invalid digest in Layers: {digest}"
        for layerdata in inspect["LayersData"]:
            if not bool(re.match(ANCHORED_DIGEST, layerdata["Digest"])):
                return False, f"Invalid digest in LayersData: {layerdata['Digest']}"
        
        # If all pass then the inspect is valid
        return True, ""

    def __init__(self, inspect: Dict[str, Any]) -> "ContainerImageInspect":
        """
        Constructor for the ContainerImageInspect class

        Args:
            inspect (dict): The container image inspect dict

        Returns:
            ContainerImageInspect: The ContainerImageInspect instance
        """
        valid, err = ContainerImageInspect.validate_static(inspect)
        if not valid:
            raise ContainerImageError(f"Invalid inspect dictionary: {err}")
        self.inspect = inspect

    def validate(self) -> Tuple[bool, str]:
        """
        Validate a container image inspect instance

        Returns:
            bool: Whether the container image inspect dict was valid
            str: Error message if it was invalid
        """
        return ContainerImageInspect.validate_static(self.inspect)

    def __str__(self) -> str:
        """
        Stringifies a ContainerImageInspect instance

        Args:
        None

        Returns:
        str: The stringified inspect
        """
        return json.dumps(self.inspect, indent=2, sort_keys=False)

    def __json__(self) -> Dict[str, Any]:
        """
        JSONifies a ContainerImageInspect instance

        Args:
        None

        Returns:
        Dict[str, Any]: The JSONified descriptor
        """
        return self.inspect
