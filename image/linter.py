from datetime import datetime, timezone
from image.auth import AUTH
from image.byteunit import ByteUnit
from image.config import ContainerImageConfig
from image.containerimage import ContainerImage
from image.manifest import ContainerImageManifest
from image.manifestlist import ContainerImageManifestList
from image.mediatypes import *
from lint.config import LinterConfig, LintRuleConfig
from lint.linter import Linter
from lint.result import LintResult
from lint.rule import LintRule, DEFAULT_LINT_RULE_CONFIG
from lint.status import LintStatus

DEFAULT_CONTAINER_IMAGE_LINTER_CONFIG = LinterConfig({
    "ManifestListSupportsRequiredPlatforms": {
        "enabled": True
    },
    "ManifestListSupportsRequiredMediaTypes": {
        "enabled": True
    },
    "ManifestSupportsRequiredMediaTypes": {
        "enabled": True
    },
    "ConfigIsLessThanNDaysOld": {
        "enabled": True
    },
    "ContainerImageIsLessThanSizeLimit": {
        "enabled": True
    }
})

class ManifestSupportsRequiredMediaTypes(
        LintRule[ContainerImageManifest]
    ):
    """
    A lint rule ensuring a manifest and its layers each support the required
    media types
    """
    def lint(
            self,
            artifact: ContainerImageManifest,
            config: LintRuleConfig=DEFAULT_LINT_RULE_CONFIG,
            **kwargs
        ) -> LintResult:
        """
        Implementation of the ManifestLayersSupportRequiredMediaTypes lint rule
        """
        # Validate the manifest mediaType
        manifest_media_type = artifact.get_media_type()
        expected_manifest_media_types = config.config.get(
            "manifest-media-types",
            [
                DOCKER_V2S2_MEDIA_TYPE,
                OCI_MANIFEST_MEDIA_TYPE
            ]
        )
        if manifest_media_type not in expected_manifest_media_types:
            return LintResult(
                status=LintStatus.ERROR,
                message=f"({self.name()})" + \
                    f" manifest has mediaType {manifest_media_type}, " + \
                    f"expected one of {expected_manifest_media_types}"
            )

        # Validate each layer mediaType
        expected_layer_media_types = config.config.get(
            "layer-media-types",
            [
                COMPRESSED_LAYER_MEDIA_TYPE
            ]
        )
        for layer in artifact.get_layer_descriptors():
            layer_media_type = layer.get_media_type()
            if layer_media_type not in expected_layer_media_types:
                return LintResult(
                    status=LintStatus.ERROR,
                    message=f"({self.name()}) " + \
                        f"layer {layer.get_digest()} has mediaType " + \
                        f"{layer_media_type}, expected one of " + \
                        str(expected_layer_media_types)
                )
        return LintResult(
            message= f"({self.name()}) " + \
                "manifest and layers support expected mediaTypes"
        )

class ContainerImageManifestLinter(
        Linter[ContainerImageManifest]
    ):
    """
    A linter for container image manifests
    """
    pass

class ManifestListSupportsRequiredPlatforms(
        LintRule[ContainerImageManifestList]
    ):
    """
    A lint rule ensuring a manifest list supports the required platforms
    """
    def lint(
            self,
            artifact: ContainerImageManifestList,
            config: LintRuleConfig=DEFAULT_LINT_RULE_CONFIG
        ) -> LintResult:
        """
        Implementation of the ManifestListSupportsRequiredPlatforms lint rule
        """
        required = config.config.get("platforms", [ "linux/amd64" ])
        platforms = set(
            str(entry.get_platform()) for entry in artifact.get_entries()
        )
        missing = list(set(required).difference(platforms))
        if len(missing) > 0:
            return LintResult(
                status=LintStatus.ERROR,
                message=f"({self.name()}) manifest list does not support " + \
                    "the following required platforms: " + \
                    str([ str(platform) for platform in missing ])
            )
        return LintResult(
            status=LintStatus.INFO,
            message=f"({self.name()}) " + \
                "manifest list supports all required platforms"
        )

class ManifestListSupportsRequiredMediaTypes(
        LintRule[ContainerImageManifestList]
    ):
    """
    A lint rule ensuring a manifest list and its manifests support the required
    media types
    """
    def lint(
            self,
            artifact: ContainerImageManifestList,
            config: LintRuleConfig=DEFAULT_LINT_RULE_CONFIG,
            **kwargs
        ) -> LintResult:
        """
        Implementation of the ManifestListSupportsRequiredMediaTypes lint rule
        """
        list_media_type = artifact.get_media_type()
        expected_list_media_types = config.config.get(
            "manifest-list-media-types",
            [
                DOCKER_V2S2_LIST_MEDIA_TYPE,
                OCI_INDEX_MEDIA_TYPE
            ]
        )
        if not list_media_type in expected_list_media_types:
            return LintResult(
                status=LintStatus.ERROR,
                message=f"({self.name()}) " + \
                    f"manifest list has mediaType {list_media_type}, " + \
                    f"expected one of {str(expected_list_media_types)}"
            )
        for entry in artifact.get_entries():
            manifest_media_type = entry.get_media_type()
            expected_media_types = config.config.get(
                "manifest-media-types",
                [
                    DOCKER_V2S2_MEDIA_TYPE,
                    OCI_MANIFEST_MEDIA_TYPE
                ]
            )
            if not manifest_media_type in expected_media_types:
                return LintResult(
                    status=LintStatus.ERROR,
                    message=f"({self.name()}) " + \
                        f"manifest {entry.get_platform()} has mediaType " + \
                        f"{manifest_media_type}, expected one of " + \
                        str(expected_media_types)
                )
        return LintResult(
            message=f"({self.name()}) " + \
                "manifest list and manifests support expected maediaTypes"
        )

class ContainerImageManifestListLinter(
        Linter[ContainerImageManifestList]
    ):
    """
    A linter for container image manifest lists
    """
    pass

class ConfigIsLessThanNDaysOld(
        LintRule[ContainerImageConfig]
    ):
    """
    A lint rule ensuring a container image config's created date is less than N
    days old
    """
    def lint(
            self,
            artifact: ContainerImageConfig,
            config: LintRuleConfig=DEFAULT_LINT_RULE_CONFIG,
            **kwargs
        ) -> LintResult:
        """
        Implementation of the ConfigIsLessThanNDaysOld lint rule
        """
        current_datetime = datetime.now()

        # Get the created date and convert to a backward-compatible
        # python-parseable format
        created_date = artifact.get_created_date()
        created_date.replace('Z', '')
        dt, frac = created_date.split('.')
        frac = frac[:6]
        iso_str = f"{dt}.{frac}"
        config_created_datetime = datetime.fromisoformat(iso_str)

        diff = current_datetime - config_created_datetime
        error_threshold = config.config.get("error-threshold", 60)
        warning_threshold = config.config.get("warning-threshold", 30)
        message = f"({self.name()}) created date is {diff.days} days old"
        if diff.days > error_threshold:
            return LintResult(
                status=LintStatus.ERROR,
                message=message
            )
        elif diff.days > warning_threshold:
            return LintResult(
                status=LintStatus.WARNING,
                message=message
            )
        return LintResult(message=message)

class ContainerImageConfigLinter(
        Linter[ContainerImageConfig]
    ):
    """
    A linter for container image configs
    """
    pass

class ContainerImageIsLessThanSizeLimit(
        LintRule[ContainerImage]
    ):
    """
    A lint rule ensuring a container image is smaller than a given size limit
    measured in bytes
    """
    def lint(
            self,
            artifact: ContainerImage,
            config: LintRuleConfig=DEFAULT_LINT_RULE_CONFIG,
            **kwargs
        ) -> LintResult:
        """
        Implementation of the ContainerImageIsLessThanSizeLimit lint rule
        """
        # Check if manifests were passed in explicitly
        manifests = kwargs.get("manifests")

        # If so, calculate size using the given manifests and configs
        # Otherwise calculate the size using the container image
        size = 0
        if manifests is not None:
            for manifest in manifests:
                size += manifest.get_size()
        else:
            auth = kwargs.get("auth", AUTH)
            size = artifact.get_size(auth=auth)
        
        # Compare against the size limit
        error_threshold = config.config.get(
            "error-threshold",
            2147483648
        ) # 2GB
        warning_threshold = config.config.get(
            "warning-threshold",
            1073741824
        ) # 1GB
        error_threshold_formatted = ByteUnit.format_size_bytes(
            error_threshold
        )
        warning_threshold_formatted = ByteUnit.format_size_bytes(
            warning_threshold
        )
        size_formatted = ByteUnit.format_size_bytes(size)
        if size > error_threshold:
            return LintResult(
                status=LintStatus.ERROR,
                message=f"({self.name()}) " + \
                    f"image is larger than {error_threshold_formatted}: " + \
                    size_formatted
            )
        elif size > warning_threshold:
            return LintResult(
                status=LintStatus.WARNING,
                message=f"({self.name()}) " + \
                    f"image is larger than {warning_threshold_formatted} " + \
                    size_formatted
            )
        return LintResult(
            message=f"({self.name()}) image size is ok: {size_formatted}"
        )

class ContainerImageLinter(
        Linter[ContainerImage]
    ):
    """
    A linter for container images
    """
    def __init__(self):
        """
        Constructor for the ContainerImageLinter class
        """
        # Initialize the default sub-type linters
        self.manifest_linter = ContainerImageManifestLinter(
            [
                ManifestSupportsRequiredMediaTypes()
            ]
        )
        self.manifest_list_linter = ContainerImageManifestListLinter(
            [
                ManifestListSupportsRequiredPlatforms(),
                ManifestListSupportsRequiredMediaTypes()
            ]
        )
        self.config_linter = ContainerImageConfigLinter(
            [
                ConfigIsLessThanNDaysOld()
            ]
        )

        # Also include any additional rules passed in
        super().__init__([
            ContainerImageIsLessThanSizeLimit()
        ])

    def lint(
            self,
            artifact: ContainerImage,
            config: LintRuleConfig=DEFAULT_LINT_RULE_CONFIG,
            **kwargs
        ) -> list[LintResult]:
        """
        Implementation of the container image linter
        """
        results = []

        # Execute each container image lint rule
        for rule in self.rules:
            results.append(rule.lint(artifact, config))

        # Fetch the container image manifests and config, lint them as we go
        auth=kwargs.get("auth", AUTH)
        manifest = artifact.get_manifest(auth=auth)
        manifests = []
        if ContainerImage.is_manifest_list_static(manifest):
            results.extend(
                self.manifest_list_linter.lint(manifest, config)
            )
            for entry in manifest.get_entries():
                platform = entry.get_platform()
                arch_image = ContainerImage(
                    f"{artifact.get_name()}@{entry.get_digest()}"
                )
                arch_manifest = arch_image.get_manifest(auth=AUTH)
                manifests.append(arch_manifest)
                manifest_results = self.manifest_linter.lint(
                    arch_manifest, config
                )
                for result in manifest_results:
                    result.message += f" for manifest {platform}"
                results.extend(manifest_results)
                arch_config = ContainerImage.get_config_static(
                    ref=arch_image,
                    manifest=arch_manifest,
                    auth=AUTH
                )
                config_results = self.config_linter.lint(arch_config, config)
                for result in config_results:
                    result.message += f" for manifest {platform}"
                results.extend(config_results)
        else:
            manifests.append(manifest)
            results.extend(self.manifest_linter.lint(manifest, config))
            config = ContainerImage.get_config_static(
                ref=artifact,
                manifest=manifest,
                auth=AUTH
            )
            results.extend(self.config_linter.lint(config, config))
        
        # Even though it should always exist, this is protection against OOB
        if len(self.rules) > 0:
            results.append(
                self.rules[0].lint(
                    artifact,
                    config.config.get(
                        self.rules[0].name(),
                        DEFAULT_LINT_RULE_CONFIG
                    ),
                    manifests=manifests
                )
            )
        return results
