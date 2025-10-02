"""
Contains the ContainerImage object, which is the main object intended for use
by end-users of containerimage-py.  As a user of this object, you can pass in
a reference to a container image in a remote registry.  Then through the object
interface you can interact with the container image & registry, fetching
metadata and mutating the image through the registry API.
"""

from __future__ import annotations
import asyncio
import json
import requests
from typing                         import  List, Dict, Any, \
                                            Union, Type, Iterator
from image.byteunit                 import  ByteUnit
from image.client                   import  ContainerImageRegistryClient, \
                                            DEFAULT_CHUNK_SIZE, \
                                            DEFAULT_TIMEOUT
from image.config                   import  ContainerImageConfig
from image.containerimageinspect    import  ContainerImageInspect
from image.descriptor               import  ContainerImageDescriptor
from image.errors                   import  ContainerImageError
from image.manifest                 import  ContainerImageManifest
from image.manifestfactory          import  ContainerImageManifestFactory
from image.manifestlist             import  ContainerImageManifestList
from image.oci                      import  ContainerImageManifestOCI, \
                                            ContainerImageIndexOCI
from image.platform                 import  ContainerImagePlatform
from image.reference                import  ContainerImageReference
from image.v2s2                     import  ContainerImageManifestV2S2, \
                                            ContainerImageManifestListV2S2

#########################################
# Classes for managing container images #
#########################################

# Override the default JSON encoder function to enable
# serializing classes as JSON
def wrapped_default(self, obj):
    return getattr(obj.__class__, "__json__", wrapped_default.default)(obj)
wrapped_default.default = json.JSONEncoder().default
json.JSONEncoder.original_default = json.JSONEncoder.default
json.JSONEncoder.default = wrapped_default

class ContainerImage(ContainerImageReference):
    """
    Extends the ContainerImageReference class and uses the
    ContainerImageRegistryClient class to provide a convenient interface
    through which users can specify their image reference, then query the
    registry API for information about the image.
    """
    @staticmethod
    def is_manifest_list_static(
            manifest: Union[
                ContainerImageManifestV2S2,
                ContainerImageManifestListV2S2,
                ContainerImageManifestOCI,
                ContainerImageIndexOCI
            ]
        ) -> bool:
        """
        Determine if an arbitrary manifest object is a manifest list

        Args:
            manifest (Union[ContainerImageManifestV2S2,ContainerImageManifestListV2S2,ContainerImageManifestOCI,ContainerImageIndexOCI]): The manifest object, generally from get_manifest method

        Returns:
            bool: Whether the manifest object is a list or single-arch
        """
        return isinstance(manifest, ContainerImageManifestList)
    
    @staticmethod
    def is_oci_static(
            manifest: Union[
                ContainerImageManifestV2S2,
                ContainerImageManifestListV2S2,
                ContainerImageManifestOCI,
                ContainerImageIndexOCI
            ]
        ) -> bool:
        """
        Determine if an arbitrary manifest object is an OCI manifest or image
        index.

        Args:
            manifest (Union[ContainerImageManifestV2S2,ContainerImageManifestListV2S2,ContainerImageManifestOCI,ContainerImageIndexOCI]): The manifest object, generally from get_manifest method

        Returns:
            bool: Whether the manifest object is in the OCI format
        """
        return isinstance(manifest, ContainerImageManifestOCI) or \
                isinstance(manifest, ContainerImageIndexOCI)
    
    @staticmethod
    def get_host_platform_manifest_static(
            ref: ContainerImageReference,
            manifest: Union[
                ContainerImageManifestV2S2,
                ContainerImageManifestListV2S2,
                ContainerImageManifestOCI,
                ContainerImageIndexOCI
            ],
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> Union[
            ContainerImageManifestV2S2,
            ContainerImageManifestOCI
        ]:
        """
        Given an image's reference and manifest, this static method checks if
        the manifest is a manifest list, and attempts to get the manifest from
        the list matching the host platform.

        Args:
            ref (ContainerImageReference): The image reference corresponding to the manifest
            manifest (Union[ContainerImageManifestV2S2,ContainerImageManifestListV2S2,ContainerImageManifestOCI,ContainerImageIndexOCI]): The manifest object, generally from get_manifest method
            auth (Dict[str, Any]): A valid docker config JSON with auth into the ref's registry
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            Union[ContainerImageManifestV2S2,ContainerImageManifestOCI]: The manifest response from the registry API

        Raises:
            ContainerImageError: Error if the image is a manifest list without a manifest matching the host platform
        """
        host_manifest = manifest

        # If manifest list, get the manifest matching the host platform
        if ContainerImage.is_manifest_list_static(manifest):
            found = False
            host_entry_digest = None
            host_plt = ContainerImagePlatform.get_host_platform()
            entries = manifest.get_entries()
            for entry in entries:
                if entry.get_platform() == host_plt:
                    found = True
                    host_entry_digest = entry.get_digest()
            if not found:
                raise ContainerImageError(
                    "no image found in manifest list for platform: " + \
                    f"{str(host_plt)}"
                )
            host_ref = ContainerImage(
                f"{ref.get_name()}@{host_entry_digest}"
            )
            host_manifest = host_ref.get_manifest(
                auth=auth,
                skip_verify=skip_verify,
                http=http,
                timeout=timeout
            )
        
        # Return the manifest matching the host platform
        return host_manifest

    @staticmethod
    def get_config_static(
            ref: ContainerImageReference,
            manifest: Union[
                ContainerImageManifestV2S2,
                ContainerImageManifestListV2S2,
                ContainerImageManifestOCI,
                ContainerImageIndexOCI
            ],
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> ContainerImageConfig:
        """
        Given an image's manifest, this static method fetches that image's
        config from the distribution registry API.  If the image is a manifest
        list, then it gets the config corresponding to the manifest matching
        the host platform.

        Args:
            ref (ContainerImageReference): The image reference corresponding to the manifest
            manifest (Union[ContainerImageManifestV2S2,ContainerImageManifestListV2S2,ContainerImageManifestOCI,ContainerImageIndexOCI]): The manifest object, generally from get_manifest method
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            ContainerImageConfig: The config for this image

        Raises:
            ContainerImageError: Error if the image is a manifest list without a manifest matching the host platform
        """
        # If manifest list, get the manifest matching the host platform
        manifest = ContainerImage.get_host_platform_manifest_static(
            ref,
            manifest,
            auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )
        
        # Get the image's config
        return ContainerImageConfig(
            ContainerImageRegistryClient.get_config(
                ref,
                manifest.get_config_descriptor(),
                auth=auth,
                skip_verify=skip_verify,
                http=http,
                timeout=timeout
            )
        )

    def __init__(self, ref: str):
        """
        Constructor for the ContainerImage class

        Args:
            ref (str): The image reference
        """
        # Validate the image reference
        valid, err = ContainerImage.validate_static(ref)
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
        return ContainerImage.validate_static(self.ref)
    
    def get_digest(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> str:
        """
        Parses the digest from the reference if digest reference, or fetches
        it from the registry if tag reference

        Args:
            auth (Dict[str, Any]): A valid docker config JSON
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            str: The image digest
        """
        if self.is_digest_ref():
            return self.get_identifier()
        return ContainerImageRegistryClient.get_digest(
            self,
            auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )
    
    def get_platforms(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> List[
            ContainerImagePlatform
        ]:
        """
        Returns the supported platform(s) for the image as a list of
        ContainerImagePlatforms

        Args:
            auth (Dict[str, Any]): A valid docker config JSON
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            List[ContainerImagePlatform]: The supported platforms
        """
        # If manifest, get the config and get its platform
        manifest = self.get_manifest(
            auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )
        platforms = []
        if not ContainerImage.is_manifest_list_static(manifest):
            config_desc = manifest.get_config_descriptor()
            config_dict = ContainerImageRegistryClient.get_config(
                self,
                config_desc,
                auth,
                skip_verify=skip_verify,
                http=http,
                timeout=timeout
            )
            config = ContainerImageConfig(config_dict)
            platforms = [ config.get_platform() ]
        else:
            for entry in manifest.get_entries():
                platforms.append(entry.get_platform())
        return platforms

    def get_manifest(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> Union[
            ContainerImageManifestV2S2,
            ContainerImageManifestListV2S2,
            ContainerImageManifestOCI,
            ContainerImageIndexOCI
        ]:
        """
        Fetches the manifest from the distribution registry API

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)

        Returns:
            Union[ContainerImageManifestV2S2,ContainerImageManifestListV2S2,ContainerImageManifestOCI,ContainerImageIndexOCI]: The manifest or manifest list response from the registry API
        """
        # Ensure the ref is valid, if not raise an exception
        valid, err = self.validate()
        if not valid:
            raise ContainerImageError(err)
        
        # Use the container image registry client to get the manifest
        return ContainerImageManifestFactory.create(
            ContainerImageRegistryClient.get_manifest(
                self, auth, skip_verify=skip_verify, http=http, timeout=timeout
            )
        )
    
    def get_host_platform_manifest(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> Union[
            ContainerImageManifestOCI,
            ContainerImageManifestV2S2
        ]:
        """
        Fetches the manifest from the distribution registry API.  If the
        manifest is a manifest list, then it attempts to fetch the manifest
        in the list matching the host platform.  If not found, an exception is
        raised.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            Union[ContainerImageManifestV2S2,ContainerImageManifestOCI]: The manifest response from the registry API

        Raises:
            ContainerImageError: Error if the image is a manifest list without a manifest matching the host platform
        """
        # Get the container image's manifest
        manifest = self.get_manifest(
            auth=auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )
        
        # Return the host platform manifest
        return ContainerImage.get_host_platform_manifest_static(
            self,
            manifest,
            auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )

    def get_config(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> ContainerImageConfig:
        """
        Fetches the image's config from the distribution registry API.  If the
        image is a manifest list, then it gets the config corresponding to the
        manifest matching the host platform.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            ContainerImageConfig: The config for this image

        Raises:
            ContainerImageError: Error if the image is a manifest list without a manifest matching the host platform
        """
        # Get the image's manifest
        manifest = self.get_manifest(
            auth=auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )

        # Use the image's manifest to get the image's config
        config = ContainerImage.get_config_static(
            self,
            manifest,
            auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )

        # Return the image's config
        return config

    def list_tags(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> Dict[str, Any]:
        """
        Fetches the list of tags for the image from the distribution registry
        API.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
        
        Returns:
            Dict[str, Any]: The tag list loaded into a dict
        """
        return ContainerImageRegistryClient.list_tags(
            self, auth, skip_verify=skip_verify, http=http, timeout=timeout
        )

    def exists(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> bool:
        """
        Determine if the image reference corresponds to an image in the remote
        registry.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            bool: Whether the image exists in the registry
        """
        try:
            ContainerImageRegistryClient.get_manifest(
                self, auth, skip_verify=skip_verify, http=http, timeout=timeout
            )
        except requests.HTTPError as he:
            if he.response.status_code == 404:
                return False
            else:
                raise he
        return True

    def is_manifest_list(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> bool:
        """
        Determine if the image is a manifest list

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            bool: Whether the image is a manifest list or single-arch
        """
        return ContainerImage.is_manifest_list_static(
            self.get_manifest(
                auth,
                skip_verify=skip_verify,
                http=http,
                timeout=timeout
            )
        )

    def is_oci(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> bool:
        """
        Determine if the image is in the OCI format

        Args:
            auth (Dict[str, Any]): A valid docker config JSON with auth into this image's registry
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            bool: Whether the image is in the OCI format
        """
        return ContainerImage.is_oci_static(
            self.get_manifest(
                auth,
                skip_verify=skip_verify,
                http=http,
                timeout=timeout
            )
        )

    def get_media_type(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> str:
        """
        Gets the image's mediaType from its manifest

        Args:
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            str: The image's mediaType
        """
        return self.get_manifest(
            auth, skip_verify=skip_verify, http=http, timeout=timeout
        ).get_media_type()

    def get_size(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> int:
        """
        Calculates the size of the image by fetching its manifest metadata
        from the registry.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            int: The size of the image in bytes
        """
        # Get the manifest and calculate its size
        manifest = self.get_manifest(
            auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )
        if ContainerImage.is_manifest_list_static(manifest):
            return manifest.get_size(
                self.get_name(),
                auth,
                skip_verify=skip_verify,
                http=http,
                timeout=timeout
            )
        else:
            return manifest.get_size()

    def get_size_formatted(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> str:
        """
        Calculates the size of the image by fetching its manifest metadata
        from the registry.  Formats as a human readable string (e.g. 3.14 KB)

        Args:
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification

        Returns:
            str: The size of the image in bytes in human readable format (1.25 GB)
        """
        return ByteUnit.format_size_bytes(
            self.get_size(
                auth,
                skip_verify=skip_verify,
                http=http,
                timeout=timeout
            )
        )
    
    def inspect(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> ContainerImageInspect:
        """
        Returns a collection of basic information about the image, equivalent
        to skopeo inspect.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            ContainerImageInspect: A collection of information about the image
        """
        # Get the image's manifest
        manifest = self.get_host_platform_manifest(
            auth=auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )

        # Use the image's manifest to get the image's config
        config = ContainerImage.get_config_static(
            self,
            manifest,
            auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )

        # List the image's tags
        tags = self.list_tags(
            auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )

        # Format the inspect dictionary
        inspect = {
            "Name": self.get_name(),
            "Digest": self.get_digest(
                auth=auth, skip_verify=skip_verify, http=http, timeout=timeout
            ),
            "RepoTags": tags["tags"],
            # TODO: Implement v2s1 manifest extension - only v2s1 manifests use this value
            "DockerVersion": "",
            "Created": config.get_created_date(),
            "Labels": config.get_labels(),
            "Architecture": config.get_architecture(),
            "Os": config.get_os(),
            "Layers": [ 
                layer.get_digest() \
                for layer \
                in manifest.get_layer_descriptors()
            ],
            "LayersData": [
                {
                    "MIMEType": layer.get_media_type(),
                    "Digest": layer.get_digest(),
                    "Size": layer.get_size(),
                    "Annotations": layer.get_annotations() or {}
                } for layer in manifest.get_layer_descriptors()
            ],
            "Env": config.get_env()
        }

        # Set the variant in the inspect dict if found
        variant = config.get_variant()
        if variant:
            inspect["Variant"] = variant

        # Set the tag in the inspect dict
        if self.is_tag_ref():
            inspect["Tag"] = self.get_identifier()
        return ContainerImageInspect(inspect)

    def download(
            self,
            path: str,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Downloads the image onto the filesystem

        Args:
            path (str): The destination path on the filesystem
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        # Get the source manifest or manifests
        manifest = self.get_manifest(
            auth=auth, skip_verify=skip_verify, http=http, timeout=timeout
        )
        if ContainerImage.is_manifest_list_static(manifest):
            for entry in manifest.get_entries():
                # Create a new ContainerImage for each manifest
                manifest_img = ContainerImage(
                    f"{self.get_name()}@{entry.get_digest()}"
                )

                # Download each manifest and save as <digest>.manifest.json
                arch_manifest = manifest_img.get_manifest(
                    auth, skip_verify=skip_verify, http=http, timeout=timeout
                )
                with open(
                        f"{path}/{entry.get_digest().split(':')[-1]}.manifest.json", 'w'
                    ) as arch_manifest_file:
                    arch_manifest_file.write(str(arch_manifest))

                # Download each layer and save as <digest>
                arch_layer_desc = arch_manifest.get_layer_descriptors()
                for desc in arch_layer_desc:
                    layer = ContainerImageRegistryClient.get_blob(
                        self,
                        desc,
                        auth,
                        skip_verify=skip_verify,
                        http=http,
                        timeout=timeout
                    )
                    with open(
                            f"{path}/{desc.get_digest().split(':')[-1]}", 'wb'
                        ) as layer_file:
                        layer_file.write(layer)
        else:
            # Download each layer and save as <digest>
            layer_desc = manifest.get_layer_descriptors()
            for desc in layer_desc:
                layer = ContainerImageRegistryClient.get_blob(
                    self,
                    desc,
                    auth,
                    skip_verify=skip_verify,
                    http=http,
                    timeout=timeout
                )
                with open(
                        f"{path}/{desc.get_digest().split(':')[-1]}", 'wb'
                    ) as layer_file:
                    layer_file.write(layer)
        
        # Save the top-level manifest as manifest.json
        with open(f"{path}/manifest.json", 'w') as manifest_file:
            manifest_file.write(str(manifest))

    def copy_blob(
            self,
            dest: Union[str, ContainerImageReference],
            desc: ContainerImageDescriptor,
            auth: Dict[str, Any],
            chunked: bool=True,
            chunk_size: int=DEFAULT_CHUNK_SIZE,
            src_skip_verify: bool=False,
            dest_skip_verify: bool=False,
            src_http: bool=False,
            dest_http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Copies a blob to a new registry

        Args:
            dest (Union[str, ContainerImageReference]): The destination location to copy the blob
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            chunked (bool): Whether to upload blobs in chunks or monolithically
            chunk_size (int): The chunk size to use for chunked blob uploads, measured in bytes
            src_skip_verify (bool): Insecure, skip TLS cert verification for the source reference
            dest_skip_verify (bool): Insecure, skip TLS cert verification for the destination reference
            src_http (bool): Insecure, whether to use HTTP (not HTTPs) for the source reference
            dest_http (bool): Insecure, whether to use HTTP (not HTTPs) for the destination reference
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        # Exit early if the blob exists in the destination registry
        if ContainerImageRegistryClient.blob_exists(
                dest,
                desc,
                auth,
                skip_verify=dest_skip_verify,
                http=dest_http,
                timeout=timeout
            ):
            return
        
        # If this is not a chunked upload, then upload the blob monolothically
        if not chunked:
            blob = ContainerImageRegistryClient.get_blob(
                self,
                desc,
                auth,
                skip_verify=src_skip_verify,
                http=src_http,
                timeout=timeout
            )
            upload_url = ContainerImageRegistryClient.initialize_upload(
                dest,
                auth,
                skip_verify=dest_skip_verify,
                http=dest_http,
                timeout=timeout
            )
            ContainerImageRegistryClient.upload_blob(
                dest,
                upload_url,
                desc,
                blob,
                chunked=False,
                auth=auth,
                skip_verify=dest_skip_verify,
                http=dest_http,
                timeout=timeout
            )
            return
        
        # If this is a chunked upload, stream and upload the blob in chunks
        chunks_read = 0
        blob_upload_url = None
        res = ContainerImageRegistryClient.query_blob(
            self,
            desc,
            auth,
            skip_verify=src_skip_verify,
            stream=True,
            http=src_http,
            timeout=timeout
        )
        for chunk in res.iter_content(chunk_size=chunk_size):
            # Initialize a blob upload for the blob
            if blob_upload_url is None:
                blob_upload_url = ContainerImageRegistryClient.initialize_upload(
                    dest,
                    auth,
                    skip_verify=dest_skip_verify,
                    http=dest_http,
                    timeout=timeout
                )
            
            # Upload the chunk
            chunk_start = chunks_read * chunk_size
            is_last_chunk = chunk_start >= (desc.get_size() - chunk_size)
            next_upload_url = ContainerImageRegistryClient.upload_chunk(
                dest,
                blob_upload_url,
                desc,
                chunk,
                chunk_start=chunk_start,
                last_chunk=is_last_chunk,
                auth=auth,
                skip_verify=dest_skip_verify,
                timeout=timeout
            )
            if next_upload_url is not None:
                blob_upload_url = next_upload_url
            chunks_read += 1
        
        # Close the stream
        res.close()

    async def _copy_blobs_parallel(
            self,
            dest: Union[str, ContainerImageReference],
            descriptors: list[ContainerImageDescriptor],
            auth: Dict[str, Any],
            chunked: bool=True,
            chunk_size: int=DEFAULT_CHUNK_SIZE,
            src_skip_verify: bool=False,
            dest_skip_verify: bool=False,
            src_http: bool=False,
            dest_http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Copies a collection of blobs to a new registry in parallel

        Args:
            dest (Union[str, ContainerImageReference]): The destination location to copy the blobs
            descriptors (list[ContainerImageDescriptor]): The blob descriptors to copy
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            chunked (bool): Whether to upload blobs in chunks or monolithically
            chunk_size (int): The chunk size to use for chunked blob uploads, measured in bytes
            src_skip_verify (bool): Insecure, skip TLS cert verification for the source reference
            dest_skip_verify (bool): Insecure, skip TLS cert verification for the destination reference
            src_http (bool): Insecure, whether to use HTTP (not HTTPs) for the source reference
            dest_http (bool): Insecure, whether to use HTTP (not HTTPs) for the destination reference
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        coroutines = []
        for desc in descriptors:
            coroutine = asyncio.to_thread(
                self.copy_blob,
                dest=dest,
                desc=desc,
                auth=auth,
                chunked=chunked,
                chunk_size=chunk_size,
                src_skip_verify=src_skip_verify,
                dest_skip_verify=dest_skip_verify,
                src_http=src_http,
                dest_http=dest_http,
                timeout=timeout
            )
            coroutines.append(coroutine)
        await asyncio.gather(*coroutines)

    def _copy_blobs_sequential(
            self,
            dest: Union[str, ContainerImageReference],
            descriptors: list[ContainerImageDescriptor],
            auth: Dict[str, Any],
            chunked: bool=True,
            chunk_size: int=DEFAULT_CHUNK_SIZE,
            src_skip_verify: bool=False,
            dest_skip_verify: bool=False,
            src_http: bool=False,
            dest_http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Copies a collection of blobs to a new registry sequentially

        Args:
            dest (Union[str, ContainerImageReference]): The destination location to copy the blobs
            descriptors (list[ContainerImageDescriptor]): The blob descriptors to copy
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            chunked (bool): Whether to upload blobs in chunks or monolithically
            chunk_size (int): The chunk size to use for chunked blob uploads, measured in bytes
            src_skip_verify (bool): Insecure, skip TLS cert verification for the source reference
            dest_skip_verify (bool): Insecure, skip TLS cert verification for the destination reference
            src_http (bool): Insecure, whether to use HTTP (not HTTPs) for the source reference
            dest_http (bool): Insecure, whether to use HTTP (not HTTPs) for the destination reference
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        for desc in descriptors:
            self.copy_blob(
                dest=dest,
                desc=desc,
                auth=auth,
                chunked=chunked,
                chunk_size=chunk_size,
                src_skip_verify=src_skip_verify,
                dest_skip_verify=dest_skip_verify,
                src_http=src_http,
                dest_http=dest_http,
                timeout=timeout
            )

    def copy_manifest(
            self,
            dest: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            manifest: Union[ContainerImageManifest, None]=None,
            parallel: bool=True,
            chunked: bool=True,
            chunk_size: int=DEFAULT_CHUNK_SIZE,
            src_skip_verify: bool=False,
            dest_skip_verify: bool=False,
            src_http: bool=False,
            dest_http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Copies an architecture manifest to a new registry

        Args:
            dest (Union[str, ContainerImageReference]): The destination location to copy the image
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            manifest (Union[ContainerImageManifest, None]): Optionally pass in the manifest up-front
            parallel (bool): Whether to upload blobs in parallel
            chunked (bool): Whether to upload blobs in chunks or monolithically
            chunk_size (int): The chunk size to use for chunked blob uploads, measured in bytes
            src_skip_verify (bool): Insecure, skip TLS cert verification for the source reference
            dest_skip_verify (bool): Insecure, skip TLS cert verification for the destination reference
            src_http (bool): Insecure, whether to use HTTP (not HTTPs) for the source reference
            dest_http (bool): Insecure, whether to use HTTP (not HTTPs) for the destination reference
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        if manifest is None:
            # Download the architecture manifest
            manifest = self.get_manifest(
                auth,
                skip_verify=src_skip_verify,
                http=src_http,
                timeout=timeout
            )

        # Ensure this is a single-arch manifest
        if ContainerImage.is_manifest_list_static(manifest):
            raise ContainerImageError(
                f"Expected manifest, got manifest list: {str(self)}"
            )

        # Copy each blob
        descriptors = manifest.get_layer_descriptors()
        arch_config_desc = manifest.get_config_descriptor()
        descriptors.append(arch_config_desc)
        if parallel:
            asyncio.run(
                self._copy_blobs_parallel(
                    dest=dest,
                    descriptors=descriptors,
                    auth=auth,
                    chunked=chunked,
                    chunk_size=chunk_size,
                    src_skip_verify=src_skip_verify,
                    dest_skip_verify=dest_skip_verify,
                    src_http=src_http,
                    dest_http=dest_http,
                    timeout=timeout
                )
            )
        else:
            self._copy_blobs_sequential(
                dest=dest,
                descriptors=descriptors,
                auth=auth,
                chunked=chunked,
                chunk_size=chunk_size,
                src_skip_verify=src_skip_verify,
                dest_skip_verify=dest_skip_verify,
                src_http=src_http,
                dest_http=dest_http,
                timeout=timeout
            )

        # Upload each manifest
        ContainerImageRegistryClient.upload_manifest(
            dest,
            manifest.raw(),
            manifest.get_media_type(),
            auth,
            skip_verify=dest_skip_verify,
            http=dest_http,
            timeout=timeout
        )

    async def _copy_manifests_parallel(
            self,
            dest: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            manifest_list: Union[ContainerImageManifestList, None],
            chunked: bool=True,
            chunk_size: int=DEFAULT_CHUNK_SIZE,
            src_skip_verify: bool=False,
            dest_skip_verify: bool=False,
            src_http: bool=False,
            dest_http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Copies a manifest list's manifests in parallel using asyncio

        Args:
            dest (Union[str, ContainerImageReference]): The destination location to copy the image
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            manifest_list (Union[ContainerImageManifestList, None]): Optionally pass in the manifest list up-front
            chunked (bool): Whether to upload blobs in chunks or monolithically
            chunk_size (int): The chunk size to use for chunked blob uploads, measured in bytes
            src_skip_verify (bool): Insecure, skip TLS cert verification for the source reference
            dest_skip_verify (bool): Insecure, skip TLS cert verification for the destination reference
            src_http (bool): Insecure, whether to use HTTP (not HTTPs) for the source reference
            dest_http (bool): Insecure, whether to use HTTP (not HTTPs) for the destination reference
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        coroutines = []
        for entry in manifest_list.get_entries():
            manifest_src = ContainerImage(
                f"{self.get_name()}@{entry.get_digest()}"
            )
            manifest_dest = ContainerImage(
                f"{dest.get_name()}@{entry.get_digest()}"
            )
            if manifest_dest.exists(
                auth=auth,
                skip_verify=dest_skip_verify,
                http=dest_http,
                timeout=timeout
            ):
                continue
            coroutine = asyncio.to_thread(
                manifest_src.copy_manifest,
                dest=manifest_dest,
                auth=auth,
                manifest=None,
                parallel=True,
                chunked=chunked,
                chunk_size=chunk_size,
                src_skip_verify=src_skip_verify,
                dest_skip_verify=dest_skip_verify,
                src_http=src_http,
                dest_http=dest_http,
                timeout=timeout
            )
            coroutines.append(coroutine)
        await asyncio.gather(*coroutines)

    def _copy_manifests_sequential(
            self,
            dest: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            manifest_list: Union[ContainerImageManifestList, None],
            chunked: bool=True,
            chunk_size: int=DEFAULT_CHUNK_SIZE,
            src_skip_verify: bool=False,
            dest_skip_verify: bool=False,
            src_http: bool=False,
            dest_http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Copies a manifest list's manifests sequentially

        Args:
            dest (Union[str, ContainerImageReference]): The destination location to copy the image
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            manifest_list (Union[ContainerImageManifestList, None]): Optionally pass in the manifest list up-front
            chunked (bool): Whether to upload blobs in chunks or monolithically
            chunk_size (int): The chunk size to use for chunked blob uploads, measured in bytes
            src_skip_verify (bool): Insecure, skip TLS cert verification for the source reference
            dest_skip_verify (bool): Insecure, skip TLS cert verification for the destination reference
            src_http (bool): Insecure, whether to use HTTP (not HTTPs) for the source reference
            dest_http (bool): Insecure, whether to use HTTP (not HTTPs) for the destination reference
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        for entry in manifest_list.get_entries():
            # Create a new ContainerImage for each manifest
            manifest_src = ContainerImage(
                f"{self.get_name()}@{entry.get_digest()}"
            )
            manifest_dest = ContainerImage(
                f"{dest.get_name()}@{entry.get_digest()}"
            )
            if manifest_dest.exists(
                auth=auth,
                skip_verify=dest_skip_verify,
                http=dest_http,
                timeout=timeout
            ):
                continue

            # Copy the manifest
            manifest_src.copy_manifest(
                dest=manifest_dest,
                auth=auth,
                manifest=None,
                parallel=False,
                chunked=chunked,
                chunk_size=chunk_size,
                src_skip_verify=src_skip_verify,
                dest_skip_verify=dest_skip_verify,
                src_http=src_http,
                dest_http=dest_http,
                timeout=timeout
            )

    def copy_manifest_list(
            self,
            dest: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            manifest_list: Union[ContainerImageManifestList, None],
            parallel: bool=True,
            chunked: bool=True,
            chunk_size: int=DEFAULT_CHUNK_SIZE,
            src_skip_verify: bool=False,
            dest_skip_verify: bool=False,
            src_http: bool=False,
            dest_http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Copies a manifest list to a new registry

        Args:
            dest (Union[str, ContainerImageReference]): The destination location to copy the image
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            manifest_list (Union[ContainerImageManifestList, None]): Optionally pass in the manifest list up-front
            parallel (bool): Whether to upload blobs in parallel
            chunked (bool): Whether to upload blobs in chunks or monolithically
            chunk_size (int): The chunk size to use for chunked blob uploads, measured in bytes
            src_skip_verify (bool): Insecure, skip TLS cert verification for the source reference
            dest_skip_verify (bool): Insecure, skip TLS cert verification for the destination reference
            src_http (bool): Insecure, whether to use HTTP (not HTTPs) for the source reference
            dest_http (bool): Insecure, whether to use HTTP (not HTTPs) for the destination reference
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        if manifest_list is None:
            # Download the manifest list
            manifest_list = self.get_manifest(
                auth,
                skip_verify=src_skip_verify,
                http=src_http,
                timeout=timeout
            )

        # Ensure this is a manifest list
        if not ContainerImage.is_manifest_list_static(manifest_list):
            raise ContainerImageError(
                f"Expected manifest list, got manifest: {str(self)}"
            )

        # Copy each manifest
        if parallel:
            asyncio.run(
                self._copy_manifests_parallel(
                    dest,
                    auth,
                    manifest_list=manifest_list,
                    chunked=chunked,
                    chunk_size=chunk_size,
                    src_skip_verify=src_skip_verify,
                    dest_skip_verify=dest_skip_verify,
                    src_http=src_http,
                    dest_http=dest_http,
                    timeout=timeout
                )
            )
        else:
            self._copy_manifests_sequential(
                dest,
                auth,
                manifest_list=manifest_list,
                chunked=chunked,
                chunk_size=chunk_size,
                src_skip_verify=src_skip_verify,
                dest_skip_verify=dest_skip_verify,
                src_http=src_http,
                dest_http=dest_http,
                timeout=timeout
            )
        
        # Upload the top-level manifest list
        ContainerImageRegistryClient.upload_manifest(
            dest,
            manifest_list.raw(),
            manifest_list.get_media_type(),
            auth,
            skip_verify=dest_skip_verify,
            http=dest_http,
            timeout=timeout
        )

    def copy(
            self,
            dest: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            parallel: bool=True,
            chunked: bool=True,
            chunk_size: int=DEFAULT_CHUNK_SIZE,
            src_skip_verify: bool=False,
            dest_skip_verify: bool=False,
            src_http: bool=False,
            dest_http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Copies the image to a new registry

        Args:
            dest (Union[str, ContainerImageReference]): The destination location to copy the image
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            parallel (bool): Whether to upload blobs in parallel
            chunked (bool): Whether to upload blobs in chunks or monolithically
            chunk_size (int): The chunk size to use for chunked blob uploads, measured in bytes
            src_skip_verify (bool): Insecure, skip TLS cert verification for the source reference
            dest_skip_verify (bool): Insecure, skip TLS cert verification for the destination reference
            src_http (bool): Insecure, whether to use HTTP (not HTTPs) for the source reference
            dest_http (bool): Insecure, whether to use HTTP (not HTTPs) for the destination reference
        """
        # Ensure the destination image is a tag reference
        if isinstance(dest, str):
            dest = ContainerImage(dest)
        if not dest.is_tag_ref():
            raise ContainerImageError(
                f"Destination must be a tag reference, got: {str(dest)}"
            )
        
        # Get the source manifest or manifests
        manifest = self.get_manifest(
            auth=auth,
            skip_verify=src_skip_verify,
            http=src_http,
            timeout=timeout
        )
        if ContainerImage.is_manifest_list_static(manifest):
            self.copy_manifest_list(
                dest=dest,
                auth=auth,
                manifest_list=manifest,
                parallel=parallel,
                chunked=chunked,
                chunk_size=chunk_size,
                src_skip_verify=src_skip_verify,
                dest_skip_verify=dest_skip_verify,
                src_http=src_http,
                dest_http=dest_http,
                timeout=timeout
            )
        else:
            self.copy_manifest(
                dest=dest,
                auth=auth,
                manifest=manifest,
                parallel=parallel,
                chunked=chunked,
                chunk_size=chunk_size,
                src_skip_verify=src_skip_verify,
                dest_skip_verify=dest_skip_verify,
                src_http=src_http,
                dest_http=dest_http,
                timeout=timeout
            )

    def delete(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Deletes the image from the registry.

        Args:
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        # Ensure the ref is valid, if not raise an exception
        valid, err = self.validate()
        if not valid:
            raise ContainerImageError(err)
        ContainerImageRegistryClient.delete(
            self, auth, skip_verify=skip_verify, http=http, timeout=timeout
        )

class ContainerImageList:
    """
    Represents a list of ContainerImages. Enables performing bulk actions
    against many container images at once.
    """
    def __init__(self):
        """
        Constructor for ContainerImageList class
        """
        self.images = []
    
    def __len__(self) -> int:
        """
        Returns the length of the ContainerImageList

        Returns:
            int: The length of the ContainerImageList
        """
        return len(self.images)
    
    def __iter__(self) -> Iterator[ContainerImage]:
        """
        Returns an iterator over the ContainerImageList 

        Returns:
            Iterator[ContainerImage]: The iterator over the ContainerImageList
        """
        return iter(self.images)
    
    def append(self, image: Type[ContainerImage]):
        """
        Append a new ContainerImage to the ContainerImageList

        Args:
            image (Type[ContainerImage]): The ContainerImage to add
        """
        self.images.append(image)

    def get_size(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> int:
        """
        Get the deduplicated size of all container images in the list

        Args:
            auth (Dict[str, Any]): A valid docker config JSON dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            int: The deduplicated size of all container images in the list
        """
        # Aggregate all layer and config digests, sum manifest list entries
        entry_sizes = 0
        layers = {}
        configs = {}

        # Loop through each image in the list
        for image in self.images:
            # Get the image's manifest
            manifest = image.get_manifest(
                auth, skip_verify=skip_verify, http=http, timeout=timeout
            )

            # If a manifest list, get its configs, entry sizes, layers
            image_layers = []
            image_configs = []
            if ContainerImage.is_manifest_list_static(manifest):
                entry_sizes += manifest.get_entry_sizes()
                image_layers = manifest.get_layer_descriptors(
                    image.get_name(),
                    auth,
                    skip_verify=skip_verify,
                    http=http,
                    timeout=timeout
                )
                image_configs = manifest.get_config_descriptors(
                    image.get_name(),
                    auth,
                    skip_verify=skip_verify,
                    http=http,
                    timeout=timeout
                )
            # If an arch manifest, get its config, layers
            else:
                image_configs = [manifest.get_config_descriptor()]
                image_layers = manifest.get_layer_descriptors()
            
            # Append the configs & layers to the aggregated dicts
            for image_config in image_configs:
                config_digest = image_config.get_digest()
                config_size = image_config.get_size()
                configs[config_digest] = config_size
            for image_layer in image_layers:
                layer_digest = image_layer.get_digest()
                layer_size = image_layer.get_size()
                layers[layer_digest] = layer_size
        
        # Calculate the layer and config sizes
        layer_sizes = 0
        config_sizes = 0
        for digest in layers.keys():
            layer_sizes += layers[digest]
        for digest in configs.keys():
            config_sizes += configs[digest]
        
        # Return the summed size
        return layer_sizes + config_sizes + entry_sizes
    
    def get_size_formatted(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> str:
        """
        Get the deduplicated size of all container images in the list,
        formatted as a human readable string (e.g. 3.14 MB)

        Args:
            auth (Dict[str, Any]): A valid docker config JSON dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            str: List size in bytes formatted to nearest unit (ex. "1.23 MB")
        """
        return ByteUnit.format_size_bytes(
            self.get_size(
                auth,
                skip_verify=skip_verify,
                http=http,
                timeout=timeout
            )
        )
    
    def delete(
            self,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Delete all of the container images in the list from the registry

        Args:
            auth (Dict[str, Any]): A valid docker config JSON dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        for image in self.images:
            image.delete(
                auth,
                skip_verify=skip_verify,
                http=http,
                timeout=timeout
            )

    def diff(self, previous: Type[ContainerImageList]) -> Type[ContainerImageListDiff]:
        """
        Compare this ContainerImageList with another and identify images which
        were added, removed, updated, and common across both instances.  Here,
        the receiver ContainerImageList is viewed as the current version, while
        the argument ContainerImageList is viewed as the previous version.

        Args:
            previous (Type[ContainerImageList]): The "previous" ContainerImageList

        Returns:
            Type[ContainerImageListDiff]: The diff between the ContainerImageLists
        """
        # Initialize a ContainerImageListDiff
        diff = ContainerImageListDiff()

        # Construct a mapping of image name to current and prev image instance
        images = {}
        for image in self.images:
            image_name = image.get_name()
            if image_name not in images:
                images[image_name] = {}
            images[image_name]['current'] = image
        for image in previous.images:
            image_name = image.get_name()
            if image_name not in images:
                images[image_name] = {}
            images[image_name]['previous'] = image

        # Use the mapping to populate the diff
        for image_name, keys in images.items():
            if 'current' in keys and 'previous' in keys:
                current_identifier = images[image_name]['current'].get_identifier()
                previous_identifier = images[image_name]['previous'].get_identifier()
                if current_identifier == previous_identifier:
                    diff.common.append(images[image_name]['current'])
                    continue
                diff.updated.append(images[image_name]['current'])
            elif 'current' in images[image_name]:
                diff.added.append(images[image_name]['current'])
            elif 'previous' in images[image_name]:
                diff.removed.append(images[image_name]['previous'])
        return diff

class ContainerImageListDiff:
    """
    Represents a diff between two ContainerImageLists
    """
    def __init__(self):
        """
        Constructor for the ContainerImageListDiff class
        """
        self.added = ContainerImageList()
        self.removed = ContainerImageList()
        self.updated = ContainerImageList()
        self.common = ContainerImageList()

    def __str__(self) -> str:
        """
        Formats a ContainerImageListDiff as a string

        Returns:
            str: The ContainerImageListDiff formatted as a string
        """
        # Format the summary
        summary =   f"Added:\t{len(self.added)}\n" + \
                    f"Removed:\t{len(self.removed)}\n" + \
                    f"Updated:\t{len(self.updated)}\n" + \
                    f"Common:\t{len(self.common)}"
        
        # Format the added, removed, updated, and common sections
        added = "\n".join([str(img) for img in self.added])
        removed = "\n".join([str(img) for img in self.removed])
        updated = "\n".join([str(img) for img in self.updated])
        common = "\n".join([str(img) for img in self.common])

        # Format the stringified diff
        diff_str =  f"Summary\n{summary}\n\nAdded\n{added}\n\n" + \
                    f"Removed\n{removed}\n\nUpdated\n{updated}\n\n" + \
                    f"Common\n{common}"
        return diff_str
