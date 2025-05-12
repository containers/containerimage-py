import json
from image.errors import ContainerImageError
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
        # Validate the container image inspect dict
        try:
            validate(
                instance=inspect,
                schema=CONTAINER_IMAGE_INSPECT_SCHEMA
            )
        except Exception as e:
            return False, str(e)
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
