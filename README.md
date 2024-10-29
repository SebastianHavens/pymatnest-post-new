# Pymatnest post analysis

Package for the analysis of pymatnest calculations which can calculate a variety of properties.
These properties can be used to identify solid-liquid and solid-solid phase transitions.

## Properties calculated
- Partition function
- Radial distribution function
- Steinhardt (QW) bond order parameters
- Temperature of each configuration

## Usaage
An example input is as follow:
```bash
python main.py --rdf --qw -M 0.1 -n 2000 -D 1 
```
`-M 0.1 -n 2000 -D 1`. Providing  `-M`, `-n` and `-D` turns on calculating the partition function. In this example it will start at T= 0.1K (`-M`), and will calculate it across 2000 temperature steps (`-N`) with temeprature spacing of 1~K.\
(`-d`), calculating the partition function from 0.1K to 2000.1K.\
`--rdf` Turns on calculating the radial distribution function.\
`--qw` Turns on calculating the Steinhardt (QW) bond order parameters.

Trajectory file names do not need to be provided. 

### Partiton function
Usage of the partition function is descrived above and all three options must be provided.
A .energies file does not need to be provided as this will be found my the package.
The output of the partition function will be written to *analyse.dat*.
The default Boltzmann constant is ****** if a different Boltzmann constants is to be used in the calculation this can be provided with `-k`.\
```bash
python main.py  -M 0.1 -n 200 -D 1 -k
```

### RDF calculation

By default a cutoff of 6Å will be used. A user defined cutoff can be provided with `--rdf_cut`
```bash
python main.py  --rdf --rdf_cut 9
```

By defualt it will determine the atom type by the first atom in the last configuration of the trajectory files. If you are using a single element this is fine. If you are looking at a multi component system and want to define two different atom types for the calculation could can define these with `--mask1` and `--mask2`.\
```bash
python main.py --rdf --mask1 Cu --mask2 Au
``` 

### Steinhardt (QW) bond order calculations
If the `--qw` option is provided the rdf calcultion will be turned on if `--qw_cut` is not provided. This is done as the deafult cutoff used is the mid way point between the first and second shell determined from the rdf calculation of the last configuration.\
```bash
python main.py --qw --qw_cut 2
``` 
