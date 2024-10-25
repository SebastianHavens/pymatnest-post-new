#!/usr/bin/ env python3
import argparse
import glob
import sys
import subprocess
import os

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
        self._validate_flags()

        # Non passed arguments
        self.life_points, self.prefix = self._read_in_number_of_live_points_and_prefix()
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

    def _read_in_number_of_live_points_and_prefix(self):
        """
        Read in number of live points from .energies file. and the file prefix

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
        prefix, _ = os.path.splitext(energy_file)

        with open(energy_file, 'r') as file:
            self.live_points = file.readline().split()[0]


# def run_ns_analyse(config):
#     output_file = open("analyse.dat", "w")
#     subprocess.run(
#         ['ns_analyse', f'{.prefix}.energies', '-M', param.start_temp, '-n', param.num_temp, '-D',
#          param.delta_temp],
#         stdout=output_file)
#     output_file.close()


def main():
    config = Config()


if __name__ == '__main__':
    main()