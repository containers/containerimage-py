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

from image.auth import AUTH
from image.containerimage import ContainerImage
from image.linter import  *
from lint.config import LinterConfig

# Initialize a ContainerImage given a tag reference
my_image = ContainerImage("registry.k8s.io/pause:3.5")

# Initialize the linter and linter config
linter = ContainerImageLinter()
config = DEFAULT_CONTAINER_IMAGE_LINTER_CONFIG

# Lint the container image and print results
results = linter.lint(my_image, config=config, auth=AUTH)
for result in results:
    print(result)
