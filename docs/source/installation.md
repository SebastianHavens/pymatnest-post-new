## Installation

### [QUIP](https://github.com/libAtoms/QUIP)
This package uses the RDF and QW calcualtors which are provided with the QUIP package.
For these two calculators to be utilies [QUIP](https://github.com/libAtoms/QUIP) must be installed on your machine and have the installation directory in your PATH.

### [Pymatnest](https://github.com/libAtoms/pymatnest)
For the partition function calcution, we use the ns_analyse calculator provided with [pymatnest](https://github.com/libAtoms/pymatnest).
This must be in your PATH, or you must have a symbolic link to it in your current directory.

### Python requirements
The python package requirements for this script can be found in *requirements.txt*
These packages can be installed with
```bash
pip install -r requirements.txt
```