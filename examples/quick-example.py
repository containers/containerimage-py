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

from image.containerimage import ContainerImage

# Initialize a ContainerImage given a tag reference
my_image = ContainerImage("registry.k8s.io/pause:3.5")

# Display some basic information about the container image
print(
    f"Size of {str(my_image)}: " + \
    my_image.get_size_formatted(auth={}) # 499.91 MB
)
print(
    f"Digest for {str(my_image)}: " + \
    my_image.get_digest(auth={}) # sha256:1ff6c18fbef2045af6b9c16bf034cc421a29027b800e4f9b68ae9b1cb3e9ae07
)
