"""
Contains the ContainerImageReference class, which can validate and parse
references to container images in remote registries
"""

import re
from image.errors   import  ContainerImageError
from image.regex    import  REFERENCE_PAT, \
                            ANCHORED_DIGEST, \
                            ANCHORED_TAG, \
                            ANCHORED_NAME, \
                            ANCHORED_DOMAIN
from typing         import  Tuple, Dict, Any, Union

class ContainerImageReference:
    """
    Represents a container image reference. Contains logic for validating and
    parsing container image references.
    """
    @staticmethod
    def validate_static(ref: str) -> Tuple[bool, str]:
        """
        Validates an image reference

        Args:
            ref (str): The image reference

        Returns:
            Tuple[bool, str]: Whether the reference is valid, error message
        """
        valid = bool(re.match(REFERENCE_PAT, ref))
        if not valid:
            return False, f"Invalid reference: {ref}"
        return True, ""

    def __init__(self, ref: str):
        """
        Constructor for the ContainerImage class

        Args:
            ref (str): The image reference
        """
        # Validate the image reference
        valid, err = ContainerImageReference.validate_static(ref)
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
        return ContainerImageReference.validate_static(self.ref)

    def is_digest_ref(self) -> bool:
        """
        Determines if the image reference is a digest reference

        Returns:
            bool: Whether the image is a digest reference
        """
        # Ensure the ref is valid, if not raise an exception
        valid, err = self.validate()
        if not valid:
            raise ContainerImageError(err)
        
        # Check for an "@" character, if not found then it is not a digest ref
        if "@" not in self.ref:
            return False
        
        # Parse out the digest and validate it, if valid then its a digest ref
        digest = self.ref.split("@")[-1]
        return bool(re.match(ANCHORED_DIGEST, digest))

    def is_tag_ref(self) -> bool:
        """
        Determine if the image reference is a tag reference

        Returns:
            bool: Whether the image is a tag referenece
        """
        # Ensure the ref is valid, if not raise an exception
        valid, err = self.validate()
        if not valid:
            raise ContainerImageError(err)

        # If the image is a digest ref, then it is not a tag ref
        if self.is_digest_ref():
            return False

        # Parse out the tag and validate it, if valid then it is a tag ref
        tag = "latest"
        if ":" in self.ref:
            tag = self.ref.split(":")[-1]
        return bool(re.match(ANCHORED_TAG, tag))

    def get_tag(self) -> Union[str, None]:
        """
        Returns the image tag if found in the reference, otherwise returns None

        Returns:
            str | None: The image tag, or None if not given
        """
        # Check if tag and digest ref
        if self.is_digest_ref():
            try:
                maybe_tag_ref = ContainerImageReference(self.ref.split("@")[0])
                if ":" in maybe_tag_ref.ref:
                    return maybe_tag_ref.get_identifier()
                return None
            except ContainerImageError:
                return None
        
        # Tag ref - we can just return the identifier
        return self.get_identifier()

    def get_identifier(self) -> str:
        """
        Gets the image identifier, which can be either a tag or a digest,
        based on whether the image is a tag or digest ref

        Returns:
            str: The image identifier, either a tag or digest
        """
        # Ensure the ref is valid, if not raise an exception
        valid, err = self.validate()
        if not valid:
            raise ContainerImageError(err)

        # Get either the tag or digest as the identifier for the image
        # Raise an exception if neither a valid tag or digest is found
        if self.is_digest_ref():
            return self.ref.split("@")[-1]
        elif self.is_tag_ref():
            if ":" in self.ref:
                return self.ref.split(":")[-1]
            return "latest"
        else:
            raise Exception(f"Not a valid tag or digest ref: {self.ref}")

    def get_name(self) -> str:
        """
        Gets the image name, which is the image registry and path but without
        an identifier (tag or digest)

        Returns:
            str: The image name
        """
        # Ensure the ref is valid, if not raise an exception
        valid, err = self.validate()
        if not valid:
            raise ContainerImageError(err)
        
        # Split the domain out of the image path
        components = self.ref.split("/")
        domain = components.pop(0)
        path = "/".join(components)
        
        # Parse out any digests or tags
        digestless_path = path.split("@")[0]
        tagless_path = digestless_path.split(":")[0]

        # Recombine into a name
        name = f"{domain}/{tagless_path}"

        # Validate the image name, if valid then return
        valid = bool(re.match(ANCHORED_NAME, name))
        if not valid:
            raise ContainerImageError(f"Invalid name: {name}")
        return name

    def get_registry(self) -> str:
        """
        Gets the image registry domain from the image reference

        Returns:
            str: The image registry domain
        """
        # Get the image name
        name = self.get_name()

        # Split the path off and isolate the registry domain
        registry = name.split("/")[0]

        # Validate the registry domain, return if valid
        valid = bool(re.match(ANCHORED_DOMAIN, registry))
        if not valid:
            raise ContainerImageError(f"Invalid domain: {registry}")
        return registry
    
    def get_path(self) -> str:
        """
        Gets the image path from the image name.  This is the path only,
        with no inclusion of the registry domain.

        Returns:
            str: The image path
        """
        # Get the image name
        name = self.get_name()

        # Split the path off and isolate the path
        name_comp = name.split("/")
        name_comp.pop(0) # Remove the registry

        # Reconstruct and return the path
        return "/".join(name_comp)
    
    def get_short_name(self) -> str:
        """
        Gets the image short name, which is the component of the image name
        following the final forward slash.  For example, for image name
        "ingress-nginx/controller", the image short name is just "controller"

        Returns:
            str: The image short name
        """
        return self.get_name().split("/")[-1]
    
    def __str__(self) -> str:
        """
        Formats the ContainerImage as a string

        Returns:
            str: The ContainerImage as a string
        """
        return self.ref

    def __json__(self) -> Dict[str, Any]:
        """
        Formats the ContainerImage as a JSON dict

        Returns:
            Dict[str, Any]: The ContainerImage as a JSON dict
        """
        return { "ref": self.ref }
