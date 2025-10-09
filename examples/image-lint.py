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

# Initialize each linter
manifest_linter = ContainerImageManifestLinter(
    [
        ManifestLayersSupportRequiredMediaTypes()
    ]
)
manifest_list_linter = ContainerImageManifestListLinter(
    [
        ManifestListSupportsRequiredPlatforms(),
        ManifestListSupportsRequiredMediaTypes()
    ]
)
config_linter = ContainerImageConfigLinter(
    [
        ConfigIsLessThanNDaysOld()
    ]
)

# Initialize each linter config
manifest_list_linter_config = LinterConfig({
    "ManifestListSupportsRequiredPlatforms": {
        "enabled": True
    },
    "ManifestListSupportsRequiredMediaTypes": {
        "enabled": True
    }
})
manifest_linter_config = LinterConfig({
    "ManifestLayersSupportRequiredMediaTypes": {
        "enabled": True
    }
})
config_linter_config = LinterConfig({
    "ConfigIsLessThanNDaysOld": {
        "enabled": True
    }
})

# Fetch the container image manifests and config, lint them as we go
results = []
manifest = my_image.get_manifest(auth=AUTH)
if ContainerImage.is_manifest_list_static(manifest):
    results.extend(
        manifest_list_linter.lint(manifest, manifest_list_linter_config)
    )
    for entry in manifest.get_entries():
        arch_image = ContainerImage(
            f"{my_image.get_name()}@{entry.get_digest()}"
        )
        arch_manifest = arch_image.get_manifest(auth=AUTH)
        results.extend(
            manifest_linter.lint(arch_manifest, manifest_linter_config)
        )
        arch_config = ContainerImage.get_config_static(
            ref=arch_image,
            manifest=arch_manifest,
            auth=AUTH
        )
        results.extend(
            config_linter.lint(arch_config, config_linter_config)
        )
else:
    results.extend(manifest_linter.lint(manifest, manifest_linter_config))
    config = ContainerImage.get_config_static(
        ref=my_image,
        manifest=manifest,
        auth=AUTH
    )
    results.extend(config_linter.lint(config, config_linter_config))

for result in results:
    print(result)
