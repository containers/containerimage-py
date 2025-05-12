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

# Display the inspect information for the container image
my_image_inspect = my_image.inspect(auth={})
print(
    f"Inspect of {str(my_image)}: \n" + \
    str(my_image_inspect)
)
