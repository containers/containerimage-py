MANIFEST_V1_FS_LAYER = {
    "type": "object",
    "description": "An object containing a checksum for each layer",
    "required": [ "blobSum" ],
    "properties": {
        "blobSum": {
            "type": "string",
            "description": "The checksum of the layer"
        }
    }
}

MANIFEST_V1_HISTORY = {
    "type": "object",
    "description": "An object containing a serialized v1 compatibility object",
    "required": [ "v1Compatibility" ],
    "properties": {
        "v1Compatibility": {
            "type": "string",
            "description": "The v1 compatibility object serialized as a string"
        }
    }
}

MANIFEST_V1_SIGNATURE = {
    "type": "object",
    "description": "A signature on a docker v1 manifest",
    "required": [ "header", "signature", "protected" ],
    "properties": {
        "header": {
            "type": "object",
            "description": "The signature header"
        },
        "signature": {
            "type": "string",
            "description": "The signature"
        },
        "protected": {
            "type": "string"
        }
    }
}

MANIFEST_V1_SCHEMA = {
    "type": "object",
    "description": "Docker v1 manifest schema (deprecated)",
    "required": [ 
        "schemaVersion", "name", "tag", "architecture", "fsLayers", "history"
    ],
    "properties": {
        "schemaVersion": {
            "type": "int",
            "description": "The schema version"
        },
        "name": {
            "type": "string",
            "description": "The name of the container image"
        },
        "tag": {
            "type": "string",
            "description": "The tag of the container image"
        },
        "architecture": {
            "type": "string",
            "description": "The architecture of the container image"
        },
        "fsLayers": {
            "type": "array",
            "description": "The container image layers",
            "items": MANIFEST_V1_FS_LAYER
        },
        "history": {
            "type": "array",
            "description": "A list of v1 compatibility objects",
            "items": MANIFEST_V1_HISTORY
        },
        "signatures": {
            "type": "array",
            "description": "A list of signature objects",
            "items": MANIFEST_V1_SIGNATURE
        }
    }
}
