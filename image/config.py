"""
Contains the ContainerImageConfig class, which specifies the runtime
configuration for a container image.
"""

from typing import Dict, Any, Tuple, Type, Union, List
from jsonschema import validate, ValidationError
from image.configschema import CONTAINER_IMAGE_CONFIG_SCHEMA
from image.platform import ContainerImagePlatform

class ContainerImageConfig:
    """
    The runtime configuration for a container image
    """
    def validate_static(config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates a container image config loaded into a dict

        Args:
            config (Dict[str, Any]): The config loaded into a dict

        Returns:
            Tuple[bool, str]: Whether the config is valid, error message
        """
        try:
            validate(
                instance=config,
                schema=CONTAINER_IMAGE_CONFIG_SCHEMA
            )
        except Exception as e:
            return False, str(e)
        return True, ""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Constructor for the ContainerImageConfig class

        Args:
            config (Dict[str, Any]): The config loaded into a dict
        """
        # Validate the config
        valid, err = ContainerImageConfig.validate_static(config)
        if not valid:
            raise ValidationError(err)

        # If valid, then save as an object property
        self.config = config

    def validate(self) -> Tuple[bool, str]:
        """
        Validates a ContainerImageConfig instance

        Returns:
            Tuple[bool, str]: Whether the config is valid, error message
        """
        return ContainerImageConfig.validate_static(self.config)

    def get_architecture(self) -> str:
        """
        Returns the config's architecture

        Returns:
            str: The config's architecture
        """
        arch = self.config.get("architecture")
        if arch == None:
            raise TypeError(f"Invalid architecture: {arch}")
        return arch

    def get_os(self) -> str:
        """
        Returns the config's operating system name

        Returns:
            str: The config's operating system name
        """
        os = self.config.get("os")
        if os == None:
            raise TypeError(f"Invalid operating system: {os}")
        return os

    def get_variant(self) -> Union[str, None]:
        """
        Returns the platform's variant, None if not found

        Returns:
            Union[str, None]: The platform variant, None if not found
        """
        variant = self.config.get("variant")
        if variant == None:
            return None
        return str(variant)
    
    def get_platform(self) -> Type[ContainerImagePlatform]:
        """
        Returns the platform of the config as a ContainerImagePlatform

        Returns:
            Type[ContainerImagePlatform]: The platform
        """
        platform_dict = {
            "os": self.get_os(),
            "architecture": self.get_architecture(),
        }
        variant = self.get_variant()
        if variant != None:
            platform_dict["variant"] = variant
        return ContainerImagePlatform(platform_dict)
    
    def get_labels(self) -> Dict[str, str]:
        """
        Returns the container image labels from the config

        Returns:
            Dict[str, str]: The labels from the config
        """
        return self.get_runtime_config().get("Labels", {})

    def get_created_date(self) -> str:
        """
        Returns the created date of the container image from the config

        Returns:
            str: The created date, as a string
        """
        return self.config.get("created", "")

    def get_runtime_config(self) -> Dict[str, Any]:
        """
        Returns the runtime config for the container image from its config

        Returns:
            Dict[str, Any]: The container image runtime config
        """
        return self.config.get("config", {})

    def get_env(self) -> List[str]:
        """
        Returns the list of environment variables set for the container image
        at build time from the container image runtime config

        Returns:
            List[str]: The list of environment variables
        """
        return self.get_runtime_config().get("Env", [])

    def get_author(self) -> str:
        """
        Returns the author of the container image from its config

        Returns:
            str: The container image author
        """
        return self.config.get("author", "")
