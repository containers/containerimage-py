import argparse
import json
import sys
from image.auth import AUTH_FILE_PATH_DEFAULT
from image.containerimage import ContainerImage
from image.linter import ContainerImageLinter, DEFAULT_CONTAINER_IMAGE_LINTER_CONFIG
from lint.config import LinterConfig
from lint.status import LintStatus
from typing import Union

def inspect(
        ref: str,
        auth: str=AUTH_FILE_PATH_DEFAULT
    ):
    """
    Inspect a container image
    """
    try:
        # Initialize the image
        image = ContainerImage(ref)

        # Load the auth
        img_auth = {}
        with open(auth, 'r') as auth_file:
            img_auth = json.load(auth_file)
        
        # Inspect the image
        print(image.inspect(auth=img_auth))
    except Exception as e:
        print(
            f"{type(e).__name__} while linting image: {str(e)}"
        )
        sys.exit(1)

def lint(
        ref: str,
        config: Union[str, None],
        auth: str=AUTH_FILE_PATH_DEFAULT
    ):
    """
    Lint a container image using the ContainerImageLinter
    """
    try:
        # Initialize the image
        image = ContainerImage(ref)

        # Load the auth
        img_auth = {}
        with open(auth, 'r') as auth_file:
            img_auth = json.load(auth_file)
        
        # Load the config
        img_config = DEFAULT_CONTAINER_IMAGE_LINTER_CONFIG
        if config is not None:
            with open(config, 'r') as config_file:
                img_config = LinterConfig(json.load(config_file))
        
        # Initialize the linter and lint the image
        linter = ContainerImageLinter()
        results = linter.lint(image, config=img_config, auth=img_auth)
        errors = [
            result for result in results if result.status == LintStatus.ERROR
        ]
        warnings = [
            result for result in results if result.status == LintStatus.WARNING
        ]

        # Print the results
        print(f"Encountered {len(errors)} errors and {len(warnings)} warnings")
        for result in errors:
            print(f"- {result}")
        for result in warnings:
            print(f"- {result}")
        if len(errors) > 0:
            sys.exit(1)
    except Exception as e:
        print(
            f"{type(e).__name__} while linting image: {str(e)}"
        )
        sys.exit(1)

def main(argv=None):
    """
    Main command executed on entry in the containerimage-py CLI
    """
    # Initialize the root command and subcommand parsers
    parser = argparse.ArgumentParser(
        prog="containerimage-py",
        description="A CLI for interacting with container images and " + \
            "container image registries based on the containerimage-py " + \
            "python library."
    )
    parser.add_argument(
        '--auth',
        dest='auth',
        required=False,
        default=AUTH_FILE_PATH_DEFAULT,
        help='A path to an image pull secret with access to your registry'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Initialize the inspect subcommand
    inspect_subcommand = subparsers.add_parser('inspect', help='Inspect a container image')
    inspect_subcommand.add_argument(
        'image',
        type=str,
        help='The container image reference to inspect'
    )

    # Initialize the lint subcommand
    lint_subcommand = subparsers.add_parser('lint', help='Lint a container image')
    lint_subcommand.add_argument(
        'image',
        type=str,
        help='The container image reference to lint'
    )
    lint_subcommand.add_argument(
        '--config',
        dest='config',
        required=False,
        default=None,
        help='A path to a linter config file for linting the container image'
    )

    # Execute the subcommand
    args = parser.parse_args(argv)
    if args.command == "lint":
        lint(
            ref=args.image,
            config=args.config,
            auth=args.auth
        )
    elif args.command == "inspect":
        inspect(
            ref=args.image,
            auth=args.auth
        )
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
