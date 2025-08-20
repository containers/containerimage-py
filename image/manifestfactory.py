"""
Contains a base factory pattern implementation in which a generic manifest dict
can be passed in, and the factory can determine which manifest type to return
"""

import json
from image.errors   import  ContainerImageError
from image.oci      import  ContainerImageManifestOCI, \
                            ContainerImageIndexOCI
from image.v2s2     import  ContainerImageManifestV2S2, \
                            ContainerImageManifestListV2S2
from typing         import  Union

class ContainerImageManifestFactory:
    """
    A factory pattern implementation.  Given a distribution registry manifest
    response, this class can instantiate any of the following types, based on the
    manifest's format
    - ContainerImageManifestListV2S2
    - ContainerImageManifestV2S2
    - ContainerImageIndexOCI
    - ContainerImageManifestOCI
    """
    def create_v2s2_manifest(manifest: bytes) -> ContainerImageManifestV2S2:
        """
        Given a manifest response from the distribution registry API, create
        a ContainerImageManifestV2S2, or raise an exception if it's invalid

        Args:
            manifest (bytes): Raw v2s2 manifest bytes

        Returns:
            ContainerImageManifestV2S2: A v2s2 manifest object
        """
        return ContainerImageManifestV2S2(manifest)

    def create_v2s2_manifest_list(manifest_list: bytes) -> ContainerImageManifestListV2S2:
        """
        Given a manifest list response from the distribution registry API,
        create a ContainerImageManifestListV2S2, or raise an exception if it's
        invalid

        Args:
            manifest_list (bytes): Raw v2s2 manifest list bytes

        Returns:
            ContainerImageManifestListV2S2: A v2s2 manifest list object
        """
        return ContainerImageManifestListV2S2(manifest_list)

    def create_oci_manifest(manifest: bytes) -> ContainerImageManifestOCI:
        """
        Given a manifest response from the distribution registry API,
        create a ContainerImageManifestOCI, or raise an exception if it's
        invalid

        Args:
            manifest (bytes): Raw OCI manifest bytes

        Returns:
            ContainerImageManifestOCI: An OCI manifest object
        """
        return ContainerImageManifestOCI(manifest)

    def create_oci_image_index(index: bytes) -> ContainerImageIndexOCI:
        """
        Given an image index response from the distribution registry API,
        create a ContainerImageIndexOCI, or raise an exception if it's invalid

        Args:
            index (bytes): Raw OCI image index bytes

        Returns:
            ContainerImageIndexOCI: An OCI image index object
        """
        return ContainerImageIndexOCI(index)

    def create(manifest_or_list: bytes) -> Union[
            ContainerImageManifestV2S2,
            ContainerImageManifestListV2S2,
            ContainerImageManifestOCI,
            ContainerImageIndexOCI
        ]:
        """
        Given a manifest response from the distribution registry API, create
        the appropriate type of manifest / manifest list object based on the
        response schema
        - ContainerImageManifestV2S2
        - ContainerImageManifestListV2S2
        - ContainerImageManifestOCI
        - ContainerImageIndexOCI

        Args:
            manifest_or_list (bytes): Raw manifest or manifest list bytes

        Returns:
            Union[ContainerImageManifestV2S2,ContainerImageManifestListV2S2,ContainerImageManifestOCI,ContainerImageIndexOCI]: Manifest or manifest list objects for the OCI & v2s2 specs
        """
        loaded = json.loads(manifest_or_list)

        # Validate whether this is a v2s2 manifest
        is_v2s2_manifest, vm_err = ContainerImageManifestV2S2.validate_static(
            loaded
        )
        if is_v2s2_manifest:
            return ContainerImageManifestV2S2(manifest_or_list)

        # If not, validate whether this is a v2s2 manifest list
        is_v2s2_list, l_err = ContainerImageManifestListV2S2.validate_static(
            loaded
        )
        if is_v2s2_list:
            return ContainerImageManifestListV2S2(manifest_or_list)
        
        # If not, validate whether this is an OCI manifest
        is_oci_manifest, om_err = ContainerImageManifestOCI.validate_static(
            loaded
        )
        if is_oci_manifest:
            return ContainerImageManifestOCI(manifest_or_list)

        # If not, validate whether this is an OCI image index
        is_oci_index, i_err = ContainerImageIndexOCI.validate_static(
            loaded
        )
        if is_oci_index:
            return ContainerImageIndexOCI(manifest_or_list)

        # If neither, raise a ValidationError
        raise ContainerImageError(
            "Invalid schema, not v2s2 or OCI manifest or list: " + \
                f"{json.dumps(json.loads(manifest_or_list))}"
        )
