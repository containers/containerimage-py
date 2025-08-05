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

SRC_REF = os.environ.get("SRC_REF", "registry.k8s.io/pause:3.5")
DEST_REF = os.environ.get("DEST_REF")

from image.auth import AUTH
from image.containerimage import ContainerImage

# Initialize source and dest ContainerImage refs
src_image = ContainerImage(SRC_REF)
dest_image = ContainerImage(DEST_REF)

# Copy the source image underneath the dest ref
src_image.copy(
    dest_image,
    auth=AUTH
)
