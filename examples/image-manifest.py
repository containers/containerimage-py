######
# Hack
#
# Make sibling modules visible to this nested executable
import os, sys
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__)
        )
    )
)
# End Hack
######

import hashlib
from image.auth import AUTH
from image.containerimage import ContainerImage

# Initialize a ContainerImage given a tag reference
my_image = ContainerImage("registry.k8s.io/pause:3.5")

# Display the inspect information for the container image
manifest = my_image.get_manifest(auth=AUTH)
digest = hashlib.sha256(manifest.raw()).hexdigest()
print(f"Digest: {digest}")
print(manifest)
