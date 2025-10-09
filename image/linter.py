from image.config import ContainerImageConfig
from image.containerimage import ContainerImage
from image.manifest import ContainerImageManifest
from image.manifestlist import ContainerImageManifestList
from lint.linter import Linter
from lint.result import LintResult
from lint.rule import LintRule

class ManifestListSupportsRequiredPlatforms(
        LintRule[ContainerImageManifestList]
    ):
    """
    A lint rule ensuring a manifest list supports the required platforms
    """
    def lint(self, artifact: ContainerImageManifestList):
        # TODO: Ability to accept lint rule-specific config
        return LintResult(message="Not yet implemented")

class ContainerImageManifestLinter(
        Linter[ContainerImageManifest]
    ):
    """
    A linter for container image manifests
    """
    pass

class ContainerImageManifestListLinter(
        Linter[ContainerImageManifestList]
    ):
    """
    A linter for container image manifest lists
    """
    pass

class ContainerImageConfigLinter(
        Linter[ContainerImageConfig]
    ):
    """
    A linter for container image configs
    """
    pass

class ContainerImageLinter(
        Linter[ContainerImage]
    ):
    """
    A linter for container images
    """
    pass
