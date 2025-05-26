![containerimage-py](https://raw.githubusercontent.com/containers/containerimage-py/main/doc/source/_static/container-image-py.png)

# containerimage-py

[![Test](https://github.com/containers/containerimage-py/actions/workflows/test.yaml/badge.svg)](https://github.com/containers/containerimage-py/actions/workflows/test.yaml) [![Sec](https://github.com/containers/containerimage-py/actions/workflows/sec.yaml/badge.svg)](https://github.com/containers/containerimage-py/actions/workflows/sec.yaml) [![Doc](https://github.com/containers/containerimage-py/actions/workflows/doc.yaml/badge.svg)](https://github.com/containers/containerimage-py/actions/workflows/doc.yaml) [![Build](https://github.com/containers/containerimage-py/actions/workflows/build.yaml/badge.svg)](https://github.com/containers/containerimage-py/actions/workflows/build.yaml)

A python library for interacting with container images and container image registries

**Docs**: https://containers.github.io/containerimage-py/

**Contributing**: [CONTRIBUTING.md](https://github.com/containers/containerimage-py/blob/main/CONTRIBUTING.md)

## Quick Example

Here is a quick motivating example for how you might use `containerimage-py` in your python scripts to fetch basic information about a container image.
```python
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

# Inspect the container image image for a more consolidated summary
print(
    f"Inspect for {str(my_image)}:\n" + \
    str(my_image.inspect(auth={})) # Same as skopeo inspect docker://registry.k8s.io/pause:3.5
)
```

To run this example, simply execute the following from the root of this repository
```sh
python3 examples/quick-example.py
```

## Installation

### Using Pip

Run the following command to install the latest version of this package

```
pip install containerimage-py
```

### Local Install

1. Clone this repository
2. [Build the project from source](#build)
3. Locate the `.whl` (wheel) file in the `dist` folder
    - It should be named something like so: `containerimage_py-1.0.0b1-py3-none-any.whl`
4. Run the following command from the root of the repository, replacing the name of the `.whl` file if necessary
    ```
    pip install dist/containerimage_py-1.0.0b1-py3-none-any.whl
    ```

## Build

From the root of this repository, execute
```sh
make build
```

Under the hood, this will execute `python3 -m build` and produce a `.whl` (wheel) and `.tgz` (TAR-GZip archive) file in the `dist` subdirectory.  For more on this project's make recipes, see [CONTRIBUTING.md](https://github.com/containers/containerimage-py/blob/main/CONTRIBUTING.md#other-make-recipes).
