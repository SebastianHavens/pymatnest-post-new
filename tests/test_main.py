# tests/test_main.py
import pytest
from unittest.mock import patch, mock_open, call
from main import Config, calculate_partition_function
import sys
import glob

@pytest.fixture
def mock_sys_argv():
    original_argv = sys.argv.copy()
    sys.argv = ['program', '--qw', '--rdf', '-M', '100', '-n', '10', '-D', '5']
    yield # Temporarily use the mock argv
    sys.argv = original_argv  # Restore the original argv after the test

def test_config_class_initiation(mock_sys_argv):
    """
    Testing config class initialisation

    :param mock_sys_argv: User input as arguments
    """

    config = Config()
    assert config.args.qw is True
    assert config.args.rdf is True
    assert config.args.M == 100.0
    assert config.args.n == 10
    assert config.args.D == 5.0
    assert config.live_points is None
    assert config.prefix is None

def test_read_live_points_and_prefix(mock_sys_argv, tmp_path):
    """
    Testing Read live points and prefix

    :param mock_sys_argv: User input as arguments
    :param tmp_path: Temporary file path for pytest
    """

    # Create a temporary .energies file
    energy_file = tmp_path / "test.energies"
    energy_file.write_text("100\nAdditional content\n")

    # Change the working directory to the temporary path
    with patch('glob.glob', return_value=[str(energy_file)]):
        config = Config()
        config.read_in_number_of_live_points_and_prefix()
        assert config.live_points == 100
        assert config.prefix == 'test'

def test_calculate_partition_function_primary_path(mock_sys_argv):
    """
     Test primary execution path of calculate_partition_function.

     This test verifies that the function calls `subprocess.run` with the correct
     arguments when `ns_analyse` is available, and writes output to "analyse.dat".

     Args:
         mock_sys_argv: User input as arguments for Config initialisation
     """
    config = Config()
    config.prefix='test'
    with patch('builtins.open', mock_open()) as mocked_file:
        with patch('subprocess.run') as mock_subproc_run:
            calculate_partition_function(config)

            # Check if `subprocess.run` was called with the correct parameters
            mock_subproc_run.assert_called_once_with(
                ['ns_analyse', 'test.energies', '-M', '100.0', '-n', '10', '-D', '5.0', '-k', '8.6173324e-05'],
                stdout=mocked_file(),
                check=True
            )
def test_calculate_partition_function_fallback_to_local(mock_sys_argv):
    """
     Test fallback execution path of calculate_partition_function.

    This test simulates a FileNotFoundError for `ns_analyse` and verifies that the
    function attempts to use `./ns_analyse` instead.

     Args:
         mock_sys_argv: User input as arguments for Config initialisation
     """
    config = Config()
    config.prefix='test'
    with patch('builtins.open', mock_open()) as mocked_file:
        with patch('subprocess.run') as mock_subproc_run:
            # First call raises FileNotFoundError, the second one succeeds
            mock_subproc_run.side_effect = [FileNotFoundError, None]

            calculate_partition_function(config)

            # Check if it was called twice with the correct fallback
            expected_calls = [
                call(['ns_analyse', 'test.energies', '-M', '100.0', '-n', '10', '-D', '5.0', '-k', '8.6173324e-05'], stdout=mocked_file(), check=True),
                call(['./ns_analyse', 'test.energies', '-M', '100.0', '-n', '10', '-D', '5.0', '-k', '8.6173324e-05'], stdout=mocked_file(), check=True)
            ]
            mock_subproc_run.assert_has_calls(expected_calls)


# def test_read_in_num_of_trajectories_max_number(monkeypatch, mock_sys_argv):
#     """
#     Test to ensure read_in_number_of_trajectories_max_number returns the correct number
#      Args:
#          mock_sys_argv: User input as arguments for Config initialisation
#      """
#     config = Config()
#     config.prefix = 'test'
#     # Mock the file list in the current directory
#     monkeypatch.setattr('os.listdir', lambda _: [
#         'test.traj.0.extxyz', 'test.traj.1.extxyz', 'test.traj.2.extxyz',
#         'test.traj.3.extxyz', 'test.traj.8.extxyz'
#     ])
#     config.read_in_num_of_trajectories()
#     # Check if the function returns the highest number for base name 'test'
#     assert config.num_of_trajectories == 5
#
#
# def test_read_in_num_of_trajectories_no_match(monkeypatch, mock_sys_argv):
#     """
#     Test to ensure read_in_number_of_trajectories_max_number returns none when no file matches.
#      Args:
#          mock_sys_argv: User input as arguments for Config initialisation
#      """
#
#     config = Config()
#     config.prefix = 'test'
#     # Mock a list with no matching files
#     monkeypatch.setattr('os.listdir', lambda _: [
#         'example.traj.0.extxyz', 'example.traj.1.extxyz'
#     ])
#     config.read_in_num_of_trajectories()
#     # Check if the function returns None when no files match 'test'
#     assert config.num_of_trajectories is None