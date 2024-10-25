#!/usr/bin/ env python3
import argparse
import glob
import sys
import subprocess
import os
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
        self.parser = argparse.ArgumentParser(description='Pymatnest post analysis package.')
        self._add_arguments()
        self.args = self.parser.parse_args()
        #print(self.args.M)
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

        self.parser.add_argument('-qw', action='store_true', help='Enable QW calculation')
        self.parser.add_argument('-rdf', action='store_true', help='Enable RDF calculation')
        self.parser.add_argument('-M', type=float, help='Heat capacity calculation: Minimum temperature')
        self.parser.add_argument('-n', type=int, help='Heat capacity calculation: Number of temperature steps')
        self.parser.add_argument('-D', type=float, help='Heat capacity calculation: Temperature step')

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
        If any of the flags for calculating the partition function are present, ensure they are all present
        """
        if any(flag is not None for flag in [self.args.M, self.args.n, self.args.D]):
            if None in [self.args.M, self.args.n, self.args.D]:
                sys.exit("Error: All three flags (--M, --n, --D) must be set together.")


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

def calculate_partition_function(config):
    """
    Calculate the partition function from the .energies file.
    param:
        config: Configuration object with parameters
    return: None
    """
    with open("analyse.dat", "w") as output_file:
        try:
            # Try running the command directly
            subprocess.run(
                ['ns_analyse', f'{config.prefix}.energies', '-M', str(config.args.M), '-n', str(config.args.n), '-D',
                 str(config.args.D)], stdout=output_file, check=True)
        except FileNotFoundError:
            # Fallback to './ns_analyse' if 'ns_analyse' is not found
            subprocess.run(
                ['./ns_analyse', f'{config.prefix}.energies', '-M', str(config.args.M), '-n', str(config.args.n), '-D',
                 str(config.args.D)], stdout=output_file, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with error: {e}")
            exit(e.returncode)



def concat_all_traj_by_iteration(config):
    data = []
    struc_store = []
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




def main():

    config = Config()
    config.read_in_number_of_live_points_and_prefix()
    config.read_in_num_of_trajectories()

    concat_all_traj_by_iteration(config)
    # If arguments given calculate the partition function
    # if config.args.M is not None:
    #     calculate_partition_function(config)

    



if __name__ == '__main__':
    main()