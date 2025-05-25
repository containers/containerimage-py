"""
Contains the ContainerImageRegistryClient class, which accepts and parses
ContainerImageReference objects, then makes calls against the reference's
distribution registry API.
"""

import hashlib
import json
import re
import requests
import urllib
from image.descriptor   import  ContainerImageDescriptor
from image.errors       import  ContainerImageError
from image.mediatypes   import  DOCKER_V2S2_MEDIA_TYPE, \
                                DOCKER_V2S2_LIST_MEDIA_TYPE, \
                                OCI_INDEX_MEDIA_TYPE, \
                                OCI_MANIFEST_MEDIA_TYPE, \
                                DOCKER_V2S1_MEDIA_TYPE, \
                                DOCKER_V2S1_SIGNED_MEDIA_TYPE
from image.reference    import  ContainerImageReference
from image.regex        import  ANCHORED_DIGEST
from typing             import  Dict, Tuple, Any, Union

DEFAULT_REQUEST_MANIFEST_MEDIA_TYPES = [
    DOCKER_V2S2_LIST_MEDIA_TYPE,
    DOCKER_V2S2_MEDIA_TYPE,
    OCI_INDEX_MEDIA_TYPE,
    OCI_MANIFEST_MEDIA_TYPE,
    DOCKER_V2S1_MEDIA_TYPE,
    DOCKER_V2S1_SIGNED_MEDIA_TYPE
]
"""
The default accepted mediaTypes for querying manifests
"""

class ContainerImageRegistryClient:
    """
    A CNCF distribution registry API client
    """
    @staticmethod
    def get_registry_base_url(
            str_or_ref: Union[str, ContainerImageReference]
        ) -> str:
        """
        Constructs the distribution registry API base URL from the image
        reference.
        
        For example,
        - quay.io/ibm/software/cloudpak/hello-world:latest
        
        Would become
        - https://quay.io/v2/ibm/software/cloudpak/hello-world

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference

        Returns:
            str: The distribution registry API base URL
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)

        # Split reference into slash-separated components
        # Get domain, it is the first element of the list
        # Join all but the first and last components into the path
        domain_components = ref.ref.split('/')
        domain = domain_components[0]
        path = "/".join(domain_components[1:-1])

        # Get name, it is the last element of the list
        # But if tag and/or digest, those must be parsed out of the name
        name = domain_components[-1].split("@")[0].split(":")[0]

        # If the domain is docker.io, then convert it to registry-1.docker.io
        if domain == 'docker.io':
            domain = 'registry-1.docker.io'

        # Format and return the registry URL base image
        return f"https://{domain}/v2/{path}/{name}"
    
    @staticmethod
    def get_registry_auth(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any]
        ) -> Tuple[str, bool]:
        """
        Gets the registry auth from a docker config JSON matching the registry
        for this image

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict

        Returns:
            Tuple[str, bool]: The auth, and whether an auth was found
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Track the last matching registry
        last_match = ""
        match_found = False

        # Loop through the registries in the auth
        auths = auth.get("auths", {})
        for registry in auths.keys():
            # Check if the registry is a leading substring of the image ref
            reg_str = str(registry)
            if not ref.ref.startswith(reg_str):
                continue

            # If the registry path is longer than the last match, save it
            if len(reg_str) > len(last_match):
                last_match = reg_str
                match_found = True

        # If no match was found, then return
        if not match_found:
            return "", False

        # Get the auth for the matching registry
        # Error if the auth key is not given, otherwise return it
        reg_auth_dict = auths.get(last_match, {})
        if "auth" not in reg_auth_dict:
            raise Exception(f"No auth key for registry {last_match}")
        return reg_auth_dict["auth"], True
    
    @staticmethod
    def get_auth_token(
            res: requests.Response,
            reg_auth: str
        ) -> Tuple[str, str]:
        """
        The response from the distribution registry API, which MUST be a 401
        response, and MUST include the www-authenticate header

        Args:
            res (requests.Response): The response from the registry API
            reg_auth (str): The auth retrieved for the registry

        Returns:
            str: The auth scheme for the token
            str: The token retrieved from the auth service
        """
        # Get the www-authenticate header, split into components
        www_auth_header = res.headers['www-authenticate']
        auth_components = www_auth_header.split(" ")

        # Parse the auth scheme from the header
        auth_scheme = auth_components[0]

        # Parse each key-value pair into a dict
        query_params = {}
        query_param_components = auth_components[1].split(",")
        for param in query_param_components:
            param_components = param.split("=")
            query_params[param_components[0]] = param_components[1].replace("\"", "")
        
        # Pop the realm value out of the dict and encode as a query string
        # Format into the auth service URL to request
        realm = query_params.pop("realm")
        query_string = urllib.parse.urlencode(query_params)
        auth_url = f"{realm}?{query_string}"

        # Send the request to the auth service, parse the token from the
        # response
        headers = {}
        if len(reg_auth) > 0:
            headers = {
                'Authorization': f"Basic {reg_auth}"
            }
        token_res = requests.get(auth_url, headers=headers)
        token_res.raise_for_status()
        token_json = token_res.json()
        token = token_json['token']
        return auth_scheme, token
    
    @staticmethod
    def query_blob(
            str_or_ref: Union[str, ContainerImageReference],
            desc: ContainerImageDescriptor,
            auth: Dict[str, Any]
        ) -> requests.Response:
        """
        Fetches a blob from the registry API and returns as a requests response
        object

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference corresponding to the blob descriptor
            desc (ContainerImageDescriptor): A blob descriptor
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict

        Returns:
            requests.Response: The registry API blob response
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the API URL for querying the blob
        api_base_url = ContainerImageRegistryClient.get_registry_base_url(ref)
        digest = desc.get_digest()
        api_url = f'{api_base_url}/blobs/{digest}'

        # Construct the headers for querying the image manifest
        headers = {}

        # Get the matching auth for the image from the docker config JSON
        reg_auth, found = ContainerImageRegistryClient.get_registry_auth(
            ref,
            auth
        )
        if found:
            headers['Authorization'] = f'Basic {reg_auth}'
        
        # Send the request to the distribution registry API
        # If it fails with a 401 response code and auth given, do OAuth dance
        res = requests.get(api_url, headers=headers)
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res, reg_auth
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.get(api_url, headers=headers)

        # Raise exceptions on error status codes
        res.raise_for_status()
        return res
    
    @staticmethod
    def get_config(
            str_or_ref: Union[str, ContainerImageReference],
            config_desc: ContainerImageDescriptor,
            auth: Dict[str, Any]
        ) -> Dict[str, Any]:
        """
        Fetches a config blob from the registry API and returns as a dict

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference corresponding to the config descriptor
            desc (ContainerImageDescriptor): A blob descriptor
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict

        Returns:
            Dict[str, Any]: The config as a dict
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Query the blob, get the manifest response
        res = ContainerImageRegistryClient.query_blob(
            ref, config_desc, auth
        )

        # Load the manifest into a dict and return
        config = res.json()
        return config

    @staticmethod
    def query_tags(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any]
        ) -> requests.Response:
        """
        Fetches the list of tags for a reference from the registry API and
        returns as a dict
        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
        Returns:
            requests.Response: The registry API tag list response
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)

        # Construct the API URL for querying the image manifest
        api_base_url = ContainerImageRegistryClient.get_registry_base_url(
            ref
        )
        image_identifier = ref.get_identifier()
        api_url = f'{api_base_url}/tags/list'

        # Construct the headers for querying the image manifest
        headers = {
            'Accept': 'application/json'
        }

        # Get the matching auth for the image from the docker config JSON
        reg_auth, found = ContainerImageRegistryClient.get_registry_auth(
            ref,
            auth
        )
        if found:
            headers['Authorization'] = f'Basic {reg_auth}'

        # Send the request to the distribution registry API
        # If it fails with a 401 response code and auth given, do OAuth dance
        res = requests.get(api_url, headers=headers)
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res, reg_auth
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.get(api_url, headers=headers)

        # Raise exceptions on error status codes
        res.raise_for_status()
        return res

    @staticmethod
    def list_tags(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any]
        ) -> Dict[str, Any]:
        """
        Fetches the list of tags for a reference from the registry API and
        returns as a dict
        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
        Returns:
            Dict[str, Any]: The config as a dict
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)

        # Query the tags, get the tag list response
        res = ContainerImageRegistryClient.query_tags(
            ref, auth
        )

        # Load the tag list into a dict and return
        tags = res.json()
        return tags

    @staticmethod
    def query_manifest(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any]
        ) -> requests.Response:
        """
        Fetches the manifest from the registry API and returns as a requests
        response object

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict

        Returns:
            requests.Response: The registry API response
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the API URL for querying the image manifest
        api_base_url = ContainerImageRegistryClient.get_registry_base_url(
            ref
        )
        image_identifier = ref.get_identifier()
        api_url = f'{api_base_url}/manifests/{image_identifier}'

        # Construct the headers for querying the image manifest
        headers = {
            'Accept': ','.join(DEFAULT_REQUEST_MANIFEST_MEDIA_TYPES)
        }

        # Get the matching auth for the image from the docker config JSON
        reg_auth, found = ContainerImageRegistryClient.get_registry_auth(
            ref,
            auth
        )
        if found:
            headers['Authorization'] = f'Basic {reg_auth}'
        
        # Send the request to the distribution registry API
        # If it fails with a 401 response code and auth given, do OAuth dance
        res = requests.get(api_url, headers=headers)
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res, reg_auth
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.get(api_url, headers=headers)

        # Raise exceptions on error status codes
        res.raise_for_status()
        return res

    @staticmethod
    def get_manifest(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any]
        ) -> Dict[str, Any]:
        """
        Fetches the manifest from the registry API and returns as a dict

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict

        Returns:
            Dict[str, Any]: The manifest loaded into a dict
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Query the manifest, get the manifest response
        res = ContainerImageRegistryClient.query_manifest(
            ref, auth
        )

        # Load the manifest into a dict and return
        manifest = res.json()
        return manifest
    
    @staticmethod
    def get_digest(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any]
        ) -> str:
        """
        Fetches the digest from the registry API

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict

        Returns:
            str: The image digest
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Query the manifest, get the manifest response
        res = ContainerImageRegistryClient.query_manifest(
            ref, auth
        )

        # Load the digest header if given, otherwise compute the digest
        digest = ""
        digest_header = 'Docker-Content-Digest'
        if digest_header in res.headers.keys():
            digest = str(res.headers['Docker-Content-Digest'])
        else:
            manifest = res.json()
            # Indent 3 is required to compute the correct digest
            # Important that this is not changed as the digest would change
            encoded_manifest = json.dumps(manifest, indent=3).encode('utf-8')
            digest = hashlib.sha256(encoded_manifest).hexdigest()

        # Validate the digest, return if valid
        if not bool(re.match(ANCHORED_DIGEST, digest)):
            raise ContainerImageError(
                f"Invalid digest: {digest}"
            )
        return digest

    @staticmethod
    def delete(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any]
        ):
        """
        Deletes the reference from the registry using the registry API

        Args:
            str_or_ref (Union[str, ContainerImage]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the API URL for querying the image manifest
        api_base_url = ContainerImageRegistryClient.get_registry_base_url(
            ref
        )
        image_identifier = ref.get_identifier()
        api_url = f'{api_base_url}/manifests/{image_identifier}'

        # Construct the headers for querying the image manifest
        headers = {}

        # Get the matching auth for the image from the docker config JSON
        reg_auth, found = ContainerImageRegistryClient.get_registry_auth(
            ref,
            auth
        )
        if found:
            headers['Authorization'] = f'Basic {reg_auth}'
        
        # Send the request to the distribution registry API
        # If it fails with a 401 response code and auth given, do OAuth dance
        res = requests.delete(api_url, headers=headers)
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res, reg_auth
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.delete(api_url, headers=headers)

        # Raise exceptions on error status codes
        res.raise_for_status()
