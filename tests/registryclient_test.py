import copy
import json
from image.containerimage       import  ContainerImageRegistryClient
from tests.registryclientmock   import  REDHAT_AMD64_MANIFEST, \
                                        REDHAT_MANIFEST_LIST_EXAMPLE, \
                                        MOCK_REGISTRY_CREDS

MOCK_IMAGE_REF = "quay.io/ibm/software/cloudpak/hello-world:latest"
MOCK_BASE_URL = "https://quay.io/v2/ibm/software/cloudpak/hello-world"
MOCK_REGISTRY_AUTH = {
    "auths": {
        "not.my/registry": {
            "auth": "dGVzdHVzZXIxOnRlc3RwYXNzMQ==",
            "username": "testuser1",
            "password": "testpass1",
            "email": "testuser1@test.com"
        },
        "quay.io/ibm/software": {
            "auth": "dGVzdHVzZXIyOnRlc3RwYXNzMg==",
            "username": "testuser2",
            "password": "testpass2",
            "email": "testuser2@test.com"
        },
        "quay.io": {
            "auth": "dGVzdHVzZXIzOnRlc3RwYXNzMw==",
            "username": "testuser3",
            "password": "testpass3",
            "email": "testuser3@test.com"
        },
        "quay.io/ibm": {
            "auth": "dGVzdHVzZXI0OnRlc3RwYXNzNA==",
            "username": "testuser4",
            "password": "testpass4",
            "email": "testuser4@test.com"
        },
        "also.not/my/registry": {
            "auth": "dGVzdHVzZXI1OnRlc3RwYXNzNQ==",
            "username": "testuser5",
            "password": "testpass5",
            "email": "testuser5@test.com"
        },
        "quay.io/ibm/software/cloudpak": {
            "auth": "dGVzdHVzZXI2OnRlc3RwYXNzNg==",
            "username": "testuser6",
            "password": "testpass6",
            "email": "testuser6@test.com"
        }
    }
}

"""
ContainerImageRegistryClient tests

Unit tests for the ContainerImageRegistryClient class
"""
def test_container_image_registry_client_get_registry_base_url():
    # Ensure the example from the type hint comment works as intended
    base_url = ContainerImageRegistryClient.get_registry_base_url(
        copy.copy(MOCK_IMAGE_REF)
    )
    assert base_url == MOCK_BASE_URL

    # Ensure an invalid ref throws an error
    exc = None
    try:
        base_url = ContainerImageRegistryClient.get_registry_base_url(
            "not an image"
        )
    except Exception as e:
        exc = e
    assert exc != None

def test_container_image_registry_client_get_registry_auth():
    # Ensure the longest matching registry prefix is chosen
    auth, found = ContainerImageRegistryClient.get_registry_auth(
        copy.copy(MOCK_IMAGE_REF),
        copy.deepcopy(MOCK_REGISTRY_AUTH)
    )
    expected_auth = MOCK_REGISTRY_AUTH["auths"]\
        ["quay.io/ibm/software/cloudpak"]\
        ["auth"]
    assert found == True
    assert auth == expected_auth

    # Ensure a nonexistent auth is not found
    auth, found = ContainerImageRegistryClient.get_registry_auth(
        "non.existent/registry/i-dont-exist:nonexistent",
        copy.deepcopy(MOCK_REGISTRY_AUTH)
    )
    assert found == False

    # Ensure the expected auth is chosen for a different included image ref
    auth, found = ContainerImageRegistryClient.get_registry_auth(
        "not.my/registry/nor-my-image:not-my-tag-either",
        copy.deepcopy(MOCK_REGISTRY_AUTH)
    )
    expected_auth = MOCK_REGISTRY_AUTH["auths"]\
        ["not.my/registry"]\
        ["auth"]
    assert found == True
    assert auth == expected_auth

def test_container_image_registry_client_get_manifest(mocker):
    # Ensure bytes are returned when valid manifest is given
    mock_response = mocker.MagicMock()
    mock_response.content = json.dumps(
        copy.deepcopy(REDHAT_AMD64_MANIFEST)
    ).encode('utf-8')
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.get", return_value=mock_response)
    manifest = ContainerImageRegistryClient.get_manifest(
        "registry.access.redhat.com/ubi9/ubi-minimal@" + \
            REDHAT_MANIFEST_LIST_EXAMPLE["manifests"][0]["digest"],
        MOCK_REGISTRY_CREDS
    )
    assert isinstance(manifest, bytes)

def test_container_image_registry_client_delete(mocker):
    # Ensure no exceptions are raised when image is successfully deleted
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.delete", return_value=mock_response)
    exc = None
    try:
        manifest = ContainerImageRegistryClient.delete(
            "registry.access.redhat.com/ubi9/ubi-minimal@" + \
                REDHAT_MANIFEST_LIST_EXAMPLE["manifests"][0]["digest"],
            MOCK_REGISTRY_CREDS
        )
    except Exception as e:
        exc = e
    assert exc == None
