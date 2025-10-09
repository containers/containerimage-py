"""
Contains various mediaType constants across the OCI, docker v2s2, and docker
v2s1 specifications
"""

# See doc comments below
DOCKER_V2S2_MEDIA_TYPE = "application/vnd.docker.distribution.manifest.v2+json"
"""
The mediaType for a docker v2s2 manifest
"""

# See doc comments below
DOCKER_V2S1_SIGNED_MEDIA_TYPE = "application/vnd.docker.distribution.manifest.v1+prettyjws"
"""
The mediaType for a signed docker v2s1 manifest
"""

# See doc comments below
DOCKER_V2S1_MEDIA_TYPE = "application/vnd.docker.distribution.manifest.v1+json"
"""
The mediaType for an unsigned docker v2s1 manifest
"""

# See doc comments below
DOCKER_V2S2_LIST_MEDIA_TYPE = "application/vnd.docker.distribution.manifest.list.v2+json"
"""
The mediaType for a docker v2s2 manifest list, also known as a multi-arch image
"""

# See doc comments below
OCI_MANIFEST_MEDIA_TYPE = "application/vnd.oci.image.manifest.v1+json"
"""
The mediaType for an OCI manifest
"""

# See doc comments below
OCI_INDEX_MEDIA_TYPE = "application/vnd.oci.image.index.v1+json"
"""
The mediaType for an OCI image index, also known as a multi-arch image
"""

# See doc comments below
COMPRESSED_LAYER_MEDIA_TYPE = "application/vnd.docker.image.rootfs.diff.tar.gzip"
"""
The mediaType for a container image layer that has been TGZ compressed
"""
