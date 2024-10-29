#!/usr/bin/ env python3
import argparse
import glob
import sys
import subprocess
import os
from argparse import Namespace
from scipy import interpolate
from pathlib import Path
from ase import io
import re
import numpy as np

class Config:

    def __init__(self):
        """
        Initialize the Config class, setting up the argument parser, adding
        arguments, and validating flags.
        """
        # Passed arguments
        self.parser = argparse.ArgumentParser(description='Pymatnest post analysis package.',
                                              usage='python main.py --rdf --qw -M 0.1 -n 2000 -D 1')
        self._add_arguments()
        self.args = self.parser.parse_args()
        self._validate_flags()
        # Initialize non-passed arguments to None
        self.live_points = None
        self.prefix = None
        self.num_of_trajectories = None


    def _add_arguments(self):
        """
        Define command-line arguments for the application.

        Flags:
            --qw: Enable QW calculation.
            --rdf: Enable RDF calculation.
            -M (float): Minimum temperature for heat capacity calculation.
            -n (int): Number of temperature steps for heat capacity calculation.
            -D (float): Temperature step for heat capacity calculation.
        """

        self.parser.add_argument('--qw', action='store_true', help='Enable QW calculation')
        self.parser.add_argument('--rdf', action='store_true', help='Enable RDF calculation')
        self.parser.add_argument('-M', type=float, help='Heat capacity calculation: Minimum temperature')
        self.parser.add_argument('-n', type=int, help='Heat capacity calculation: Number of temperature steps')
        self.parser.add_argument('-D', type=float, help='Heat capacity calculation: Temperature step')
        self.parser.add_argument('-k', type=float, default=8.6173324e-5, help='Boltzmann constant (default is (eV/K)')
        self.parser.add_argument('--mask1', type=str, help='Atom type 1 for rdf calculation')
        self.parser.add_argument('--mask2', type=str, help='Atom type 2 for rdf calculation')
        self.parser.add_argument('--r_cut', type=float, default=6, help='Cutoff for rdf calculation')
        self.parser.add_argument('--bin_width', type=float, default=0.05, help='Bin width for rdf calculation')
        self.parser.add_argument('--concat', action='store_true', help='Concatenate all trajectories by iteration number.')
        self.parser.add_argument('--qw_cut', type=float, help='Cutoff for QW calculation')
    def get_args(self):
        """
        Return parsed command-line arguments.
        User defined inputs then accessed as config.args.

        Returns:
            Namespace: The parsed arguments as attributes of a Namespace object.
        """
        return self.args

    def _validate_flags(self):
        """
        If any of the flags for calculating the partition function are present, ensure they are all present.
        If a mask parameter is present for rdf calculation, ensure they're both present.
        If calculating QW, ensure also calculating the RDF if no cutoff provided for the qw calculation.
        """
        if any(flag is not None for flag in [self.args.M, self.args.n, self.args.D, self.args.k]):
            if None in [self.args.M, self.args.n, self.args.D]:
                sys.exit("Error: All three flags (--M, --n, --D) must be set together.")

        """
        If any of the flags for rdf atom type, ensure they are both present.
        If not present will determine atom type from file.
        """
        if any (flag is not None for flag in [self.args.mask1, self.args.mask2]):
            if None in [self.args.mask1, self.args.mask2]:
                sys.exit('If any mask (atom type) is defined for rdf calculation, both must be defined.')

        """
        We use the first shell from the RDF for qw calculation if no QW cutoff set.
        """
        if self.args.qw is True and self.args.qw_cut is None:
            self.args.rdf = True

        """
        Turning on concatenation if not already defined for the QW calculation
        """
        if self.args.qw is True and self.args.concat is False:
            self.args.concat = True
            print('Turning on concatenation of all trajectories, this is needed for the QW calculation.')

    def read_in_number_of_live_points_and_prefix(self):
        """
        Read in number of live points from .energies file and the file prefix

        Returns:
            int: The number of live points from the .energies file.
            prefix: File prefix of the .energies file,

        Raises:
            RuntimeError: If multiple .energies files are found.
            FileNotFoundError: If no .energies file are found.
        """
        energy_files = glob.glob('*.energies')

        if len(energy_files) > 1:
            raise RuntimeError("Multiple .energies files found. Please ensure only one exists.")
        elif not energy_files:
            raise FileNotFoundError("No .energies file found.")

        energy_file = energy_files[0]

        # Extract the prefix (file name without the .energies extension)
        prefix = os.path.splitext(os.path.basename(energy_file))[0]
        self.prefix = prefix

        with open(energy_file, 'r') as file:
            self.live_points = int(file.readline().split()[0])

    def read_in_num_of_trajectories(self):
        """
        # Determine the number of trajectories.

        param:
            config: Configuration object with parameters
        returns:
            int: The number of trajectories.

        """
        # Construct the regex pattern
        pattern = rf'{re.escape(self.prefix)}\.traj\.(\d+)\.extxyz'

        try:
            self.num_of_trajectories = max(
                int(re.search(pattern, f).group(1))
                for f in os.listdir('.')  # List files in the current directory
                if re.search(pattern, f)
            ) + 1  # +1 as first trajectory is 0
        except ValueError:
            print("No matching files found.")

    def determine_atom_type(self):
        """
        Determines atom type for RDF calculation if not provided as an argument with mask1 and mask2.
        Will only return one atom type, for binary system it must be user defined.

        param:
            config: Configuration object with parameters
        return:
            mask1 (str): Atom type 1 for rdf calculation.
            mask2 (str): Atom type 2 for rdf calculation.
        """

        configuration = (io.read(f'{self.prefix}.traj.{self.num_of_trajectories - 1}.extxyz', index='-1'))
        self.args.mask1 = configuration[0].symbol
        self.args.mask2 = configuration[1].symbol


def calculate_partition_function(config):
    """
    Calculate the partition function from the .energies file.

    Parameters
    ----------
    config : object
        Configuration object with parameters.

    Returns
    -------
    None
    """
    print("Calculating the partition function.")
    with open("analyse.dat", "w") as output_file:
        try:
            # Try running the command directly
            subprocess.run(
                ['ns_analyse', f'{config.prefix}.energies', '-M', str(config.args.M), '-n', str(config.args.n), '-D',
                 str(config.args.D), '-k', str(config.args.k)], stdout=output_file, check=True)
        except FileNotFoundError:
            # Fallback to './ns_analyse' if 'ns_analyse' is not found
            subprocess.run(
                ['./ns_analyse', f'{config.prefix}.energies', '-M', str(config.args.M), '-n', str(config.args.n), '-D',
                 str(config.args.D), '-k', str(config.args.k)], stdout=output_file, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with error: {e}")
            exit(e.returncode)



def concat_all_traj_by_iteration(config):
    """
    Concatenates trajectory files by iteration and writes them to a new file.

    Parameters
    ----------
    config : object
        A configuration object containing:

        - `num_of_trajectories` (int): The number of trajectory files to process.
        - `prefix` (str): The prefix used in the file names to be read and written.

    Returns
    -------
    None
    """
    data = []
    struc_store = []
    print(f"Concatenating all trajectories by iteration number")
    for i in range(config.num_of_trajectories):
        strucs = io.read(f"{config.prefix}.traj.{i}.extxyz", index=':')

        for j in range(len(strucs)):
            struc = strucs[j]
            itera = struc.info['iter']
            data.append(itera)
        struc_store += strucs
    data = np.array(data)
    sort_ind = np.argsort(data)
    strucs_sorted = [struc_store[i] for i in sort_ind]
    io.write(f"{config.prefix}.traj.ordered.extxyz", strucs_sorted, format='extxyz')

def calculate_rdf(config):
    """
    Calculate rdf from last configuration in trajectory file.
    Will use atom types from input arguments mask1 and mask2 for atom types. If not defined the atom type is determined
    from a trajectory file before this function is called.

    If config.args.qw is True, calculate radius between shell 1 and 2 and set it as qw_cut for QW calculation.

    Parameters:
        config : object
        A configuration object containing:
        - `prefix` (str): The prefix used in the file names to be read and written.
        - 'mask1' (str): The first atom type to be used to calculate RDF.
        - 'mask2' (str): The second atom type to be used to calculate RDF.

    Requires:
        QUIP rdf to be in path
    """
    # extract and write last configuration from a trajectory file. -1 as it is the total number of trajectories and
    # counting starts at 0.
    last_configuration = (io.read(f'{config.prefix}.traj.{config.num_of_trajectories - 1}.extxyz', index='-1'))
    io.write(f'{config.prefix}.traj.last_config.extxyz', last_configuration, format='extxyz')

    # Run rdf calculation on last configuration in trajectory file
    try:
        print(f"Calculating rdf of atom types {config.args.mask1} and {config.args.mask2}, with a cutoff of"
              f" {config.args.r_cut} and bin width of {config.args.bin_width}.")
        subprocess.run(['rdf',
                             f'xyzfile={config.prefix}.traj.last_config.extxyz',
                             'datafile=rdf.data',
                             f'mask1={config.args.mask1}',
                             f'mask2={config.args.mask2}',
                             f'r_cut={config.args.r_cut}',
                             f'bin_width={config.args.bin_width}'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        exit(e.returncode)

    # file

    if config.args.qw is True and config.args.qw_cut is None:
        r, value = np.loadtxt('allrdf.out', unpack=True, usecols=(0, 1))
        found = False

        index_end_of_first_shell = None
        index_start_of_second_shell = None
        # Find index of end of first shell and start of second shell
        for i in range(1, len(r)):
            if value[i] == 0 and value[i - 1] != 0:
                index_end_of_first_shell = i
                found = True
            if found and value[i] != 0:
                index_start_of_second_shell = i
                break

        # Abort if we fail to distinguish first and second coordination shell
        if index_end_of_first_shell is None or index_start_of_second_shell is None:
            print("Failed to find end of first shell and start of second shell in rdf calculation, aborting!")
            exit()

        # Take mid-point between two shells for cutoff
        index= round(
            ((index_start_of_second_shell - index_end_of_first_shell) / 2) + index_end_of_first_shell)
        config.args.qw_cut = r[index]
        print(f"Radius between first and second coordination shell is {config.args.qw_cut}, this will be used for the "
              f"QW calculation.")

def calculate_qw(config):
    """Calculating the QW bond order parameters.
       We use the user provided cutoff value or if not provided the first shell from the RDF calculation which is
       determined before this function is called.

    Parameters:
        config : object
        A configuration object containing:
        - `prefix` (str): The prefix used in the file names to be read and written.
        - 'mask1' (str): The first atom type to be used to calculate RDF.
        - 'mask2' (str): The second atom type to be used to calculate RDF.

    Requires:
        QUIP rdf to be in path
        All trajectories to be concatenated.
        qw_cut to be provided as an argument or rdf to have been calculated.
    """

    print(f"Calculating QW order parameter with a cutoff of {config.args.qw_cut}")
    print("Calculating Q4 W4")
    try:
        subprocess.run(
            [
                'get_qw',
                f'atfile_in={config.prefix}.traj.ordered.extxyz',
                f'r_cut={config.args.qw_cut}',
                'l=4',
                'calc_QWave=T'
            ],
            stdout=open(f'{config.prefix}_ordered.qw4', 'w'),
            stderr=subprocess.PIPE,  # Captures any error messages
            check=True  # Raises an error if the command fails
        )
        print("Calculating Q6 W6")
        subprocess.run(
            [
                'get_qw',
                f'atfile_in={config.prefix}.traj.ordered.extxyz',
                f'r_cut={config.args.qw_cut}',
                'l=6',
                'calc_QWave=T'
            ],
            stdout=open(f'{config.prefix}_ordered.qw6', 'w'),
            stderr=subprocess.PIPE,  # Captures any error messages
            check=True  # Raises an error if the command fails
        )
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        exit(e.returncode)

def calculate_temperature_of_each_configuration(config):
    """
    Calculate temperature for every configuration in the trajectory using its enthalpy, temperature is calculated
    by comparing this to the enthalpy and temperature's calculated using the partition function.

    Parameters
    ----------
    config : object
        A configuration object containing:
        - `prefix` (str): The prefix used in the file names to be read and written.
    Returns
    -------
    Temperature (list) : A list of temperatures corresponding to each configuration

    """
    print(f"Calculating temperature of all configurations")
    # Read in trajectory file
    traj = io.read(f'{config.prefix}.traj.ordered.extxyz', index=':')
    ns_energy = [i.info['ns_energy'] for i in traj]

    # Load in temperature and potential energy for ns_analyse output
    T, U = np.loadtxt('analyse.dat', comments='#', usecols=(0, 3), unpack=True)
    # Create interpolation function to get T from U
    f = interpolate.interp1d(U, T, fill_value='extrapolate')
    #print(T, U)
    # Get T for each configuration in trajectory file
    temperature = [f(ns_energy[i]) for i in range(len(traj))]

    return temperature

def write_datafile(config):
    # Calculate temperature of each configuration

    ns_temp = calculate_temperature_of_each_configuration(config)

    traj = io.read(f'{config.prefix}.traj.ordered.extxyz', index=':')

    # Create lists of all NS values for each configuration in the trajectory file
    ns_energy = [i.info['ns_energy'] for i in traj]
    ns_volume = [i.info['volume'] for i in traj]
    ns_iter = [i.info['iter'] for i in traj]
    ns_ke = [i.info['ns_KE'] for i in traj]

    # Read in qw values
    q4, w4 = np.loadtxt(f'{config.prefix}_ordered.qw4', unpack=True, skiprows=11, usecols=(0, 1),
                        comments='libAtoms')
    q6, w6 = np.loadtxt(f'{config.prefix}_ordered.qw6', unpack=True, skiprows=11, usecols=(0, 1),
                        comments='libAtoms')

    # Write data to file
    output = open(f'{config.prefix}.data', 'a')
    for i in range(len(q4)):
        output.write(
            f'{ns_iter[i]} {ns_energy[i]} {ns_ke[i]} {ns_volume[i]} {ns_temp[i]} {q4[i]} {w4[i]} {q6[i]} {w6[i]} \
            \n')

    output.close()

def clean_up(config):
    file_paths = [Path(f"{config.prefix}.traj.last_config.extxyz.idx"),
                  Path(f"{config.prefix}.traj.ordered.extxyz.idx")]
    for file_path in file_paths:
        if file_path.is_file():
            file_path.unlink()


def main():

    config = Config()
    config.read_in_number_of_live_points_and_prefix()
    config.read_in_num_of_trajectories()

    # Concatenate all trajectories into one file by iteration number.
    if config.args.concat:
        concat_all_traj_by_iteration(config)

    # If arguments given calculate the partition function
    if config.args.M is not None:
        calculate_partition_function(config)

    # Calculate the RDF
    if config.args.rdf:
        # If atom types aren't given for the RDF calculation, we determine the atom types from a trajectory file.
        # Will only identify one atom type.
        if config.args.mask1 is None or config.args.mask2 is None:
            (config.determine_atom_type())
        calculate_rdf(config)

    # Calculate the QW parameters
    if config.args.qw:
        calculate_qw(config)

    # write data file:
    write_datafile(config)

    # Cleanup
    clean_up(config)



if __name__ == '__main__':
    main()
