from typing                 import Dict, Any, Tuple, Union, List
from jsonschema             import validate, ValidationError
from image.manifestschema   import IMAGE_INDEX_ENTRY_PLATFORM_SCHEMA

"""
ContainerImagePlatform class

Represents platform metadata, which is generally specified in an OCI image
index / v2s2 manifest list entry. Contains validation logic and getters for
platform metadata following the OCI and v2s2 specifications.

Note that the OCI and v2s2 specifications do not diverge in their schema for
platform metadata, hence we reuse this class across both scenarios.
"""
class ContainerImagePlatform:
    @staticmethod
    def validate_static(platform: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates image platform metadata from an image index entry

        Args:
        platform (Dict[str, Any]): The platform metadata to validate

        Returns:
        Tuple[bool, str]: Whether the platform metadata is valid, error msg
        """
        # Validate the platform metadata
        try:
            validate(
                instance=platform,
                schema=IMAGE_INDEX_ENTRY_PLATFORM_SCHEMA
            )
        except Exception as e:
            return False, str(e)
        return True, ""

    def __init__(self, platform: Dict[str, Any]):
        """
        Constructor for the ContainerImagePlatform class

        Args:
        platform (Dict[str, Any]): The platform metadata loaded into a dict
        """
        # Validate the platform metadata
        valid, err = ContainerImagePlatform.validate_static(
            platform
        )
        if not valid:
            raise ValidationError(err)

        # If valid, instantiate the platform object
        self.platform = platform

    def validate(self) -> Tuple[bool, str]:
        """
        Validates a ContainerImagePlatform instance

        Args:
        None

        Returns:
        Tuple[bool, str]: Whether platform metadata is valid, error message
        """
        # Validate the platform metadata
        return ContainerImagePlatform.validate_static(
            self.platform
        )

    def get_architecture(self) -> str:
        """
        Returns the platform's architecture

        Args:
        None

        Returns:
        str: The platform architecture
        """
        arch = self.platform.get("architecture")
        if arch == None:
            raise TypeError(f"Invalid architecture: {arch}")
        return arch

    def get_os(self) -> str:
        """
        Returns the platform's operating system name

        Args:
        None

        Returns:
        str: The platform operating system name
        """
        os = self.platform.get("os")
        if os == None:
            raise TypeError(f"Invalid operating system: {os}")
        return os

    def get_os_version(self) -> Union[str, None]:
        """
        Returns the platform's operating system version, None if not found

        Args:
        None

        Returns:
        Union[str, None]: The platform os version, None if not found
        """
        os_ver = self.platform.get("os.version")
        if os_ver == None:
            return None
        return str(os_ver)

    def get_os_features(self) -> Union[List[str], None]:
        """
        Returns the platform's operating system features, None if not found

        Args:
        None

        Returns:
        Union[List[str], None]: The os features list, None if not found
        """
        os_features = self.platform.get("os.features")
        if os_features == None:
            return None
        return list(os_features)

    def get_variant(self) -> Union[str, None]:
        """
        Returns the platform's variant, None if not found

        Args:
        None

        Returns:
        Union[str, None]: The platform variant, None if not found
        """
        variant = self.platform.get("variant")
        if variant == None:
            return None
        return str(variant)

    def get_features(self) -> Union[List[str], None]:
        """
        Returns the platform's features, None if not found

        Args:
        None

        Returns:
        Union[List[str], None]: The features list, None if not found
        """
        os_features = self.platform.get("features")
        if os_features == None:
            return None
        return list(os_features)

    def __str__(self) -> str:
        """
        Formats the ContainerImagePlatform as a string in the form
        <os>/<arch>[/<variant>]

        Args:
        None

        Returns:
        str: The platform as a string
        """
        plt_str = f"{self.get_os()}/{self.get_architecture()}"
        variant = self.get_variant()
        if variant != None and isinstance(variant, str):
            plt_str = f"{plt_str}/{variant}"
        return plt_str

    def __json__(self) -> Dict[str, Any]:
        """
        Formats the ContainerImagePlatform as a JSON dictionary

        Args:
        None

        Returns:
        Dict[str, Any]: The ContainerImagePlatform as a JSON dictionary
        """
        return dict(self.platform)
