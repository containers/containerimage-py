.. containerimage-py documentation master file, created by
   sphinx-quickstart on Sun Apr 20 10:49:22 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

containerimage-py documentation
===============================

A python library for interacting with container images and container image registries

.. toctree::
   :maxdepth: 2
   :caption: Reference

   image/modules

Quick example
=============

Here is a quick motivating example for how you might use ``containerimage-py`` in your python scripts to fetch basic information about a container image.

.. code-block:: python
   :linenos:

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

Installation
============

**Using Pip**

Run the following command to install the latest version of this package using pip

.. code-block:: shell

   pip install containerimage-py

**Local Install**

1. Clone `the source repository <https://github.com/containers/containerimage-py>`_
2. Build the project from source following `the build instructions <Build_>`_
3. Locate the ``.whl`` (wheel) file in the ``dist`` folder. It should be named something like so: ``containerimage_py-1.1.0-py3-none-any.whl``
4. Run the following command from the root of the repository, replacing the name of the ``.whl`` file if necessary

.. code-block:: shell

   pip install dist/containerimage_py-1.1.0-py3-none-any.whl


Build
=====

From the root of `the source repository <https://github.com/containers/containerimage-py>`_, execute

.. code-block:: shell
   
   make build


Under the hood, this will execute ``python3 -m build`` and produce a ``.whl`` (wheel) and ``.tgz`` (TAR-GZip archive) file in the ``dist`` subdirectory.

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
