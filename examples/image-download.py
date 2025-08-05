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

DEST_PATH = os.environ.get(
    "DEST_PATH",
    os.getcwd()
)

from image.containerimage import ContainerImage

# Initialize a ContainerImage given a tag reference
my_image = ContainerImage("registry.k8s.io/pause:3.5")

# Download the image onto your filesystem
my_image.download(
    DEST_PATH,
    auth={}
)
