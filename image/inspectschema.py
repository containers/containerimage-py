CONTAINER_IMAGE_LAYER_INSPECT_SCHEMA = {
    "type": "object",
    "description": "The JSON schema for a container image layer inspect " + \
        "dictionary.",
    "required": [ "MIMEType", "Digest", "Size" ],
    "additionalProperties": False,
    "properties": {
        "MIMEType": {
            "type": "string",
            "description": "This REQUIRED property is the MIME type, or " + \
                "media type, of this container image layer"
        },
        "Digest": {
            "type": "string",
            "description": "This REQUIRED property is the digest of this " + \
                "container image layer"
        },
        "Size": {
            "type": "integer",
            "description": "This REQUIRED property is the size of this " + \
                "container image layer measured in bytes"
        },
        "Annotations": {
            "anyOf": [
                {
                    "type": "object",
                    "description": "This OPTIONAL property is the set of " + \
                        "annotations belonging to this container image",
                    "patternProperties": {
                        "(^.*$)": { "type": "string" }
                    }
                },
                {
                    "type": "null"
                }
            ]
        }
    }
}
"""
The JSON schema for validating a container image layer inspect dictionary
Ref: https://github.com/containers/image/blob/main/types/types.go#L491-L497

:meta hide-value:
"""

CONTAINER_IMAGE_INSPECT_SCHEMA = {
    "type": "object",
    "description": "The JSON schema for a container image inspect dictionary",
    "required": [ 
        "Digest", "Created", "DockerVersion", "Labels", "Architecture", "Os",
        "Layers", "LayersData", "Env"
    ],
    "additionalProperties": False,
    "properties": {
        "Name": {
            "type": "string",
            "description": "This OPTIONAL property is the name of this " + \
                "container image"
        },
        "Digest": {
            "type": "string",
            "description": "This REQUIRED property is the digest of this " + \
                "container image"
        },
        "Tag": {
            "type": "string",
            "description": "This OPTIONAL property is the tag of this " + \
                "container image"
        },
        "RepoTags": {
            "type": "array",
            "description": "This OPTIONAL property is the list of tags " + \
                "for this container image in the remote registry",
            "items": {
                "type": "string"
            }
        },
        "Created": {
            "type": "string",
            "description": "This REQUIRED property is the date this " + \
                "container image was built"
        },
        "DockerVersion": {
            "type": "string",
            "description": "This REQUIRED property is the version of " + \
                "docker used to build this container image"
        },
        "Labels": {
            "anyOf": [
                {
                    "type": "object",
                    "description": "This REQUIRED property is the set of labels " + \
                        "applied to this container image at build time",
                    "patternProperties": {
                        "(^.*$)": { "type": "string" }
                    }
                },
                {
                    "type": "null"
                }
            ]
        },
        "Architecture": {
            "type": "string",
            "description": "This REQUIRED property is the architecture " + \
                "for which this container image was built"
        },
        "Variant": {
            "type": "string",
            "description": "This OPTIONAL property is the variant of the " + \
                "OS and architecture for which this container image was built"
        },
        "Os": {
            "type": "string",
            "description": "This REQUIRED property is the operating system" + \
                "for which this container image was built"
        },
        "Layers": {
            "type": "array",
            "description": "This REQUIRED property contains information " + \
                "on the set of layers belonging to this container image",
            "items": {
                "type": "string"
            }
        },
        "LayersData": {
            "type": "array",
            "description": "This REQUIRED property contains information " + \
                "on the set of layers belonging to this container image",
            "items": CONTAINER_IMAGE_LAYER_INSPECT_SCHEMA
        },
        "Env": {
            "type": "array",
            "description": "This REQUIRED property contains information " + \
                "on the set of environment variables set at build time " + \
                "in this container image",
            "items": {
                "type": "string"
            }
        },
        "Author": {
            "type": "string",
            "description": "This OPTIONAL property is the author who " + \
                "built the container image"
        }
    }
}
"""
The JSON schema for validating a container image inspect dictionary
Ref:
- https://github.com/containers/image/blob/main/types/types.go#L474-L489
- https://github.com/containers/image/blob/main/types/types.go#L474-L489

:meta hide-value:
"""
