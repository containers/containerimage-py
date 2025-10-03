"""
Contains the ContainerImageRegistryClient class, which accepts and parses
ContainerImageReference objects, then makes calls against the reference's
distribution registry API.
"""

import hashlib
import re
import requests
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
from urllib.parse       import  urlparse, urlencode, parse_qs, urlunparse

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

DEFAULT_CHUNK_SIZE = 1024 * 1024 * 16
"""
The default chunk size for chunked blob uploads, 16 MB
"""

DEFAULT_TIMEOUT = 10
"""
The default read / connect timeout for requests against the registry
"""

class ContainerImageRegistryClient:
    """
    A CNCF distribution registry API client
    """
    @staticmethod
    def get_registry_base_url(
            str_or_ref: Union[str, ContainerImageReference],
            http: bool=False
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
            http (bool): Whether to use HTTP

        Returns:
            str: The distribution registry API base URL
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Get the domain and image name from the ref
        domain = ref.get_registry()
        path = ref.get_path()

        # If the domain is docker.io, then convert it to registry-1.docker.io
        if domain == 'docker.io':
            domain = 'registry-1.docker.io'

        # Format and return the registry URL base image
        transport = "https" if not http else "http"
        return f"{transport}://{domain}/v2/{path}"
    
    @staticmethod
    def append_query_params(url: str, params: dict[str, Any]) -> str:
        """
        Helper method which appends query parameters to a URL in a safe manner

        Args:
            url (str): The URL to append to
            params (dict): The params to append

        Returns:
            str: The updated URL
        """
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        for key, val in params.items():
            query_params[key] = query_params.get(key, []) + [val]
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse(parsed._replace(query=new_query))
        return new_url

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
            reg_auth: str,
            skip_verify: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> Tuple[str, str]:
        """
        The response from the distribution registry API, which MUST be a 401
        response, and MUST include the www-authenticate header

        Args:
            res (requests.Response): The response from the registry API
            reg_auth (str): The auth retrieved for the registry
            skip_verify (bool): Insecure, skip TLS cert verification
            timeout (int): The timeout in seconds for establishing a connection with the registry

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
        # Splits on all commas not separated by double-quotes
        # Ex, we may get a token with scope pull,push
        # Naively splitting on the comma character will break us
        query_param_components = re.split(
            r',(?=(?:[^"]*"[^"]*")*[^"]*$)',
            auth_components[1]
        )
        for param in query_param_components:
            param_components = param.split("=")
            query_params[param_components[0]] = param_components[1].replace("\"", "")
        
        # Pop the realm value out of the dict and encode as a query string
        # Format into the auth service URL to request
        realm = query_params.pop("realm")
        auth_url = ContainerImageRegistryClient.append_query_params(
            realm,
            query_params
        )

        # Send the request to the auth service, parse the token from the
        # response
        headers = {}
        if len(reg_auth) > 0:
            headers = {
                'Authorization': f"Basic {reg_auth}"
            }
        token_res = requests.get(
            auth_url,
            headers=headers,
            verify=not skip_verify,
            timeout=timeout
        )
        token_res.raise_for_status()
        token_json = token_res.json()
        token = token_json['token']
        return auth_scheme, token
    
    @staticmethod
    def query_blob(
            str_or_ref: Union[str, ContainerImageReference],
            desc: ContainerImageDescriptor,
            auth: Dict[str, Any]={},
            skip_verify: bool=False,
            stream: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> requests.Response:
        """
        Fetches a blob from the registry API and returns as a requests response
        object

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference corresponding to the blob descriptor
            desc (ContainerImageDescriptor): A blob descriptor
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            requests.Response: The registry API blob response
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the API URL for querying the blob
        api_base_url = ContainerImageRegistryClient.get_registry_base_url(
            ref,
            http=http
        )
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
        res = requests.get(
            api_url,
            headers=headers,
            verify=not skip_verify,
            stream=stream,
            timeout=timeout
        )
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res, reg_auth, skip_verify=skip_verify, timeout=timeout
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.get(
                api_url,
                headers=headers,
                verify=not skip_verify,
                stream=stream,
                timeout=timeout
            )

        # Raise exceptions on error status codes
        res.raise_for_status()
        return res

    @staticmethod
    def get_blob(
            str_or_ref: Union[str, ContainerImageReference],
            desc: ContainerImageDescriptor,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> bytes:
        """
        Fetches a blob from the registry API and returns as bytes

        Args:
            str_or_ref (Union[str, ContainerImageReference]): The reference corresponding to the blob descriptor
            desc (ContainerImageDescriptor): A blob descriptor
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            bytes: The blob as bytes
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)

        # Query the blob and capture the response
        res = ContainerImageRegistryClient.query_blob(
            ref,
            desc,
            auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )

        # Load the blob content and return
        return res.content

    @staticmethod
    def initialize_upload(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> str:
        """
        Initializes a blob upload and returns the upload URL

        Args:
            str_or_ref (Union[str, ContainerImageReference]): A reference under which to upload the blob
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            str: The blob upload URL
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the API URL for initializing the blob upload
        api_base_url = ContainerImageRegistryClient.get_registry_base_url(
            ref,
            http=http
        )
        api_url = f'{api_base_url}/blobs/uploads/'

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
        res = requests.post(
            api_url,
            headers=headers,
            verify=not skip_verify,
            timeout=timeout
        )
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res, reg_auth, skip_verify=skip_verify, timeout=timeout
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.post(
                api_url,
                headers=headers,
                verify=not skip_verify,
                timeout=timeout
            )

        # Extract the upload UUID from the request response
        res.raise_for_status()
        return res.headers["Location"]

    @staticmethod
    def blob_exists(
            str_or_ref: Union[str, ContainerImageReference],
            desc: ContainerImageDescriptor,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> bool:
        """
        Queries the registry API for whether a blob exists before uploading

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference under which to upload the blob
            desc (ContainerImageDescriptor): A blob descriptor
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            bool: Whether the blob already exists in the registry
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the API URL for querying for existence of the blob
        api_base_url = ContainerImageRegistryClient.get_registry_base_url(
            ref,
            http=http
        )
        api_url = f'{api_base_url}/blobs/{desc.get_digest()}'

        # Construct the headers for querying the blob
        headers = {
            "Content-Type": desc.get_media_type()
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
        res = requests.head(
            api_url,
            headers=headers,
            verify=not skip_verify,
            timeout=timeout
        )
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res, reg_auth, skip_verify=skip_verify, timeout=timeout
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.head(
                api_url,
                headers=headers,
                verify=not skip_verify,
                timeout=timeout
            )

        # Return true if a 200 response is returned
        # Ref: https://distribution.github.io/distribution/spec/api/#existing-layers
        return res.status_code == 200

    @staticmethod
    def upload_chunk(
            str_or_ref: Union[str, ContainerImageReference],
            upload_url: str,
            desc: ContainerImageDescriptor,
            chunk: bytes,
            chunk_start: int=0,
            last_chunk: bool=False,
            auth: Dict[str, Any]={},
            skip_verify: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> Union[str, None]:
        """
        Uploads a single blob chunk to the registry API

        Args:
            str_or_ref (Union[str, ContainerImageReference]): The reference under which to upload the blob chunk
            upload_url (str): The URL of the upload, get from initialize_upload
            desc (ContainerImageDescriptor): The blob descriptor for the blob chunk being uplaoded
            content (bytes): The chunk to upload
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            str | None: The next uplaod URL, or none if this is the last chunk
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the headers for uploading the blob
        headers = {}

        # Get the matching auth for the image from the docker config JSON
        reg_auth, found = ContainerImageRegistryClient.get_registry_auth(
            ref,
            auth
        )
        if found:
            headers['Authorization'] = f'Basic {reg_auth}'

        # Prepare the required chunk upload headers
        upper = chunk_start + len(chunk)
        headers["Content-Type"] = "application/octet-stream"
        headers["Content-Length"] = str(len(chunk))
        headers["Content-Range"] = f"{chunk_start}-{upper - 1}"

        # If this is the last chunk, we need to upload using a different
        # HTTP method and include additional query parameters on the request
        # to signify to the API that the upload is complete
        chunk_upload_url = upload_url
        if last_chunk:
            fin_api_url = ContainerImageRegistryClient.append_query_params(
                url=chunk_upload_url,
                params={
                    "digest": desc.get_digest()
                }
            )
            res = requests.put(
                fin_api_url,
                headers=headers,
                data=chunk,
                verify=not skip_verify,
                timeout=timeout
            )
            if res.status_code == 401 and \
                'www-authenticate' in res.headers.keys():
                # Do Oauth dance if basic auth fails
                # Ref: https://distribution.github.io/distribution/spec/auth/token/
                scheme, token = ContainerImageRegistryClient.get_auth_token(
                    res, reg_auth, skip_verify=skip_verify, timeout=timeout
                )
                headers['Authorization'] = f'{scheme} {token}'
                res = requests.put(
                    fin_api_url,
                    headers=headers,
                    data=chunk,
                    verify=not skip_verify,
                    timeout=timeout
                )
            return None
        else:
            res = requests.patch(
                chunk_upload_url,
                headers=headers,
                data=chunk,
                verify=not skip_verify,
                timeout=timeout
            )
            if res.status_code == 401 and \
                'www-authenticate' in res.headers.keys():
                # Do Oauth dance if basic auth fails
                # Ref: https://distribution.github.io/distribution/spec/auth/token/
                scheme, token = ContainerImageRegistryClient.get_auth_token(
                    res, reg_auth, skip_verify=skip_verify, timeout=timeout
                )
                headers['Authorization'] = f'{scheme} {token}'
                res = requests.patch(
                    chunk_upload_url,
                    headers=headers,
                    data=chunk,
                    verify=not skip_verify,
                    timeout=timeout
                )
            return res.headers.get("Location")

    @staticmethod
    def _upload_blob_monolithic(
            str_or_ref: Union[str, ContainerImageReference],
            upload_url: str,
            desc: ContainerImageDescriptor,
            content: bytes,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Uploads a blob to the registry API underneath the given reference
        in a single request

        Args:
            str_or_ref (Union[str, ContainerImageReference]): The reference under which to upload the blob
            upload_url (str): The URL of the upload, get from initialize_upload
            desc (ContainerImageDescriptor): A blob descriptor
            content (bytes): The blob content to upload
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the API URL for uploading the blob
        api_url = ContainerImageRegistryClient.append_query_params(
            url=upload_url,
            params={
                "digest": desc.get_digest()
            }
        )

        # Construct the headers for uploading the blob
        headers = {
            "Content-Type": "application/octet-stream",
            "Content-Length": str(desc.get_size()),
            "Content-Range": f"0-{str(desc.get_size())}"
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
        res = requests.put(
            api_url,
            headers=headers,
            data=content,
            verify=not skip_verify,
            timeout=timeout
        )
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res, reg_auth, skip_verify=skip_verify, timeout=timeout
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.post(
                api_url,
                headers=headers,
                data=content,
                verify=not skip_verify,
                timeout=timeout
            )
        
        # Raise exceptions if any HTTP error response codes are returned
        res.raise_for_status()
    
    @staticmethod
    def _upload_blob_chunked(
            str_or_ref: Union[str, ContainerImageReference],
            upload_url: str,
            desc: ContainerImageDescriptor,
            content: bytes,
            chunk_size: int=DEFAULT_CHUNK_SIZE,
            auth: Dict[str, Any]={},
            skip_verify: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Uploads a blob to the registry API underneath the given reference
        in a sequence of chunks

        Args:
            str_or_ref (Union[str, ContainerImageReference]): The reference under which to upload the blob
            upload_url (str): The URL of the upload, get from initialize_upload
            desc (ContainerImageDescriptor): A blob descriptor
            content (bytes): The blob content to upload
            chunk_size (int): The size of the chunks to upload
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the headers for uploading the blob
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
        chunk_upload_url = upload_url
        for i in range(0, len(content), chunk_size):
            upper = min(i + chunk_size, len(content))
            chunk = content[i:upper]
            headers["Content-Type"] = "application/octet-stream"
            headers["Content-Length"] = str(len(chunk))
            headers["Content-Range"] = f"{i}-{upper - 1}"
            if upper == len(content):
                fin_api_url = ContainerImageRegistryClient.append_query_params(
                    url=chunk_upload_url,
                    params={
                        "digest": desc.get_digest()
                    }
                )
                res = requests.put(
                    fin_api_url,
                    headers=headers,
                    data=chunk,
                    verify=not skip_verify,
                    timeout=timeout
                )
                if res.status_code == 401 and \
                    'www-authenticate' in res.headers.keys():
                    # Do Oauth dance if basic auth fails
                    # Ref: https://distribution.github.io/distribution/spec/auth/token/
                    scheme, token = ContainerImageRegistryClient.get_auth_token(
                        res, reg_auth, skip_verify=skip_verify, timeout=timeout
                    )
                    headers['Authorization'] = f'{scheme} {token}'
                    res = requests.put(
                        fin_api_url,
                        headers=headers,
                        data=chunk,
                        verify=not skip_verify,
                        timeout=timeout
                    )
            else:
                res = requests.patch(
                    chunk_upload_url,
                    headers=headers,
                    data=chunk,
                    verify=not skip_verify,
                    timeout=timeout
                )
                if res.status_code == 401 and \
                    'www-authenticate' in res.headers.keys():
                    # Do Oauth dance if basic auth fails
                    # Ref: https://distribution.github.io/distribution/spec/auth/token/
                    scheme, token = ContainerImageRegistryClient.get_auth_token(
                        res, reg_auth, skip_verify=skip_verify, timeout=timeout
                    )
                    headers['Authorization'] = f'{scheme} {token}'
                    res = requests.patch(
                        chunk_upload_url,
                        headers=headers,
                        data=chunk,
                        verify=not skip_verify,
                        timeout=timeout
                    )
                chunk_upload_url = res.headers.get("Location")
            
            # Raise exceptions if any HTTP error response codes are returned
            res.raise_for_status()

    @staticmethod
    def upload_blob(
            str_or_ref: Union[str, ContainerImageReference],
            upload_url: str,
            desc: ContainerImageDescriptor,
            content: bytes,
            chunked: bool=True,
            chunk_size: int=DEFAULT_CHUNK_SIZE,
            auth: Dict[str, Any]={},
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Uploads a blob to the registry API underneath the given reference

        Args:
            str_or_ref (Union[str, ContainerImageReference]): The reference under which to upload the blob
            upload_url (str): The URL of the upload, get from initialize_upload
            desc (ContainerImageDescriptor): A blob descriptor
            content (bytes): The blob content to upload
            chunked (bool): Whether to upload the blob in chunks
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        # If the blob already exists, then no need to re-upload
        if ContainerImageRegistryClient.blob_exists(
                str_or_ref,
                desc,
                auth,
                skip_verify=skip_verify,
                http=http,
                timeout=timeout
            ):
            return
        
        # Upload either monolithically or chunked based on user preferences
        if chunked:
            ContainerImageRegistryClient._upload_blob_chunked(
                str_or_ref,
                upload_url,
                desc,
                content,
                chunk_size=chunk_size,
                auth=auth,
                skip_verify=skip_verify,
                timeout=timeout
            )
        else:
            ContainerImageRegistryClient._upload_blob_monolithic(
                str_or_ref,
                upload_url,
                desc,
                content,
                auth,
                skip_verify,
                timeout=timeout
            )

    @staticmethod
    def get_config(
            str_or_ref: Union[str, ContainerImageReference],
            config_desc: ContainerImageDescriptor,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> Dict[str, Any]:
        """
        Fetches a config blob from the registry API and returns as a dict

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference corresponding to the config descriptor
            config_desc (ContainerImageDescriptor): A blob descriptor
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            Dict[str, Any]: The config as a dict
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Query the blob, get the config response
        res = ContainerImageRegistryClient.query_blob(
            ref,
            config_desc,
            auth,
            skip_verify=skip_verify,
            http=http,
            timeout=timeout
        )

        # Load the config into a dict and return
        config = res.json()
        return config

    @staticmethod
    def query_tags(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> requests.Response:
        """
        Fetches the list of tags for a reference from the registry API and
        returns as a dict
        
        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            requests.Response: The registry API tag list response
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)

        # Construct the API URL for querying the image manifest
        api_base_url = ContainerImageRegistryClient.get_registry_base_url(
            ref,
            http=http
        )
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
        res = requests.get(
            api_url,
            headers=headers,
            verify=not skip_verify,
            timeout=timeout
        )
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res,
                reg_auth,
                skip_verify=skip_verify,
                timeout=timeout
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.get(
                api_url,
                headers=headers,
                verify=not skip_verify,
                timeout=timeout
            )

        # Raise exceptions on error status codes
        res.raise_for_status()
        return res

    @staticmethod
    def list_tags(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> Dict[str, Any]:
        """
        Fetches the list of tags for a reference from the registry API and
        returns as a dict

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        
        Returns:
            Dict[str, Any]: The config as a dict
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)

        # Query the tags, get the tag list response
        res = ContainerImageRegistryClient.query_tags(
            ref, auth, skip_verify=skip_verify, http=http, timeout=timeout
        )

        # Load the tag list into a dict and return
        tags = res.json()
        return tags

    @staticmethod
    def query_manifest(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> requests.Response:
        """
        Fetches the manifest from the registry API and returns as a requests
        response object

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            requests.Response: The registry API response
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the API URL for querying the image manifest
        api_base_url = ContainerImageRegistryClient.get_registry_base_url(
            ref,
            http=http
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
        res = requests.get(
            api_url,
            headers=headers,
            verify=not skip_verify,
            timeout=timeout
        )
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res, reg_auth, skip_verify=skip_verify, timeout=timeout
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.get(
                api_url,
                headers=headers,
                verify=not skip_verify,
                timeout=timeout
            )

        # Raise exceptions on error status codes
        res.raise_for_status()
        return res

    @staticmethod
    def get_manifest(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> bytes:
        """
        Fetches the manifest from the registry API and returns as raw bytes

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            bytes: The raw manifest bytes
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Query the manifest, get the manifest response, return raw response
        res = ContainerImageRegistryClient.query_manifest(
            ref, auth, skip_verify=skip_verify, http=http, timeout=timeout
        )
        return res.content
    
    @staticmethod
    def upload_manifest(
            str_or_ref: Union[str, ContainerImageReference],
            manifest: bytes,
            media_type: str,
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Uploads a manifest to the registry API underneath the given reference

        Args:
            str_or_ref (Union[str, ContainerImageReference]): The image reference under which to push the manifest
            manifest (bytes): The raw manifest bytes to upload
            media_type (str): The manifest media type as a string
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the API URL for uploading the manifest
        api_base_url = ContainerImageRegistryClient.get_registry_base_url(
            ref,
            http=http
        )
        api_url = f'{api_base_url}/manifests/{ref.get_identifier()}'

        # Construct the headers for uploading the manifest
        headers = {
            "Content-Type": media_type
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
        res = requests.put(
            api_url,
            headers=headers,
            data=manifest,
            verify=not skip_verify,
            timeout=timeout
        )
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res, reg_auth, skip_verify=skip_verify, timeout=timeout
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.put(
                api_url,
                headers=headers,
                data=manifest,
                verify=not skip_verify,
                timeout=timeout
            )
        
        # Raise exceptions if any HTTP error response codes are returned
        res.raise_for_status()

    @staticmethod
    def get_digest(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ) -> str:
        """
        Fetches the digest from the registry API

        Args:
            str_or_ref (Union[str, ContainerImageReference]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry

        Returns:
            str: The image digest
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Query the manifest, get the manifest response
        res = ContainerImageRegistryClient.query_manifest(
            ref, auth, skip_verify=skip_verify, http=http, timeout=timeout
        )

        # Load the digest header if given, otherwise compute the digest
        digest = ""
        digest_header = 'Docker-Content-Digest'
        if digest_header in res.headers.keys():
            digest = str(res.headers['Docker-Content-Digest'])
        else:
            digest = hashlib.sha256(res.content).hexdigest()

        # Validate the digest, return if valid
        if not bool(re.match(ANCHORED_DIGEST, digest)):
            raise ContainerImageError(
                f"Invalid digest: {digest}"
            )
        return digest

    @staticmethod
    def delete(
            str_or_ref: Union[str, ContainerImageReference],
            auth: Dict[str, Any],
            skip_verify: bool=False,
            http: bool=False,
            timeout: int=DEFAULT_TIMEOUT
        ):
        """
        Deletes the reference from the registry using the registry API

        Args:
            str_or_ref (Union[str, ContainerImage]): An image reference
            auth (Dict[str, Any]): A valid docker config JSON loaded into a dict
            skip_verify (bool): Insecure, skip TLS cert verification
            http (bool): Insecure, whether to use HTTP (not HTTPs)
            timeout (int): The timeout in seconds for establishing a connection with the registry
        """
        # If given a str, then load as a ref
        ref = str_or_ref
        if isinstance(str_or_ref, str):
            ref = ContainerImageReference(str_or_ref)
        
        # Construct the API URL for querying the image manifest
        api_base_url = ContainerImageRegistryClient.get_registry_base_url(
            ref,
            http=http
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
        res = requests.delete(
            api_url,
            headers=headers,
            verify=not skip_verify,
            timeout=timeout
        )
        if res.status_code == 401 and \
            'www-authenticate' in res.headers.keys():
            # Do Oauth dance if basic auth fails
            # Ref: https://distribution.github.io/distribution/spec/auth/token/
            scheme, token = ContainerImageRegistryClient.get_auth_token(
                res, reg_auth, skip_verify=skip_verify, timeout=timeout
            )
            headers['Authorization'] = f'{scheme} {token}'
            res = requests.delete(
                api_url,
                headers=headers,
                verify=not skip_verify,
                timeout=timeout
            )

        # Raise exceptions on error status codes
        res.raise_for_status()
