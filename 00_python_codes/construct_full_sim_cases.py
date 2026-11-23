#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
==FILE DESCRIPTION======================================================

 Assembles ready-to-run cases under ../ZZ_OutputCases from the separate
 ingredient directories of this repository: one mesh per velocity from
 12_full_system_simulations, the solver dictionaries and the velocity
 specific controlDict from 20_solver_and_numerics, the DEM and transport
 properties from 30_DEM_and_transportProps and the clear-bed initial
 conditions from 40_initial_and_boundary_conditions. Edit the blocks in
 main() to choose which cases are built and how many cores they decompose
 to, then run

     ./construct_full_sim_cases.py

 from inside 00_python_codes/, as the paths are all relative.

==LICENSE===============================================================
  construct_full_sim_cases.py

  Copyright 2026 Ondřej Studeník - OStudenik <github.com/OStudenik>
                 Martin Isoz - MartinIsoz <github.com/MartinIsoz>

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
  MA 02110-1301, USA.

========================================================================
"""

# imports --------------------------------------------------------------
# -- I/O operations
import os
from pathlib import Path
import shutil


# constants ------------------------------------------------------------
# the rule printed around the report of every built case
SEPARATOR = '-' * 69


# auxiliary functions --------------------------------------------------


def replace_in_file(file_path, to_be_replaced, replacement):
    """
        replace a given text segment in the input file

        file_path ... path to the file to work with
        to_be_replaced ... text segment to be replaced
        replacement ... replacement segment for to_be_replaced
    """
    if file_path[-1] == '/':
        file_path = file_path[:-1]
    if not os.path.isfile(file_path):
        print(f"File {file_path} does not exist.")
        return
    file_path = Path(file_path)
    content = file_path.read_text()
    new_content = content.replace(to_be_replaced, str(replacement))
    file_path.write_text(new_content)
    return


def get_mesh_config(vel):
    """
        path of the mesh dictionary of one velocity

        vel ... velocity tag of the case, such as 1.12
    """
    # one mesh per velocity remains; the MRS 4/6/8 study has been dropped
    return '../12_full_system_simulations/vel_' + str(vel) + \
        '/system/blockMeshDict'


def get_dem_config(vel):
    """
        path of the DEM dictionary of one velocity

        vel ... velocity tag of the case, such as 1.12
    """
    return '../30_DEM_and_transportProps/HFDIBDEMDict_vel' + str(vel)


def get_transport_properties():
    """
        path of the shared transport properties dictionary
    """
    return '../30_DEM_and_transportProps/transportProperties'


def get_initial_conditions(vel, clear_conditions=True):
    """
        paths of the initial fields and of the initial bed

        vel ... velocity tag of the case, such as 1.12
        clear_conditions ... paths for the empty bed, rather than for the
                             fluidised one of the same velocity
    """
    base = '../40_initial_and_boundary_conditions/'
    if not clear_conditions:
        return [base + 'vel' + str(vel) + '-full/0.org/',
                base + 'BBInfo_vel' + str(vel) + '/bodiesInfo/']
    else:
        return [base + 'vel' + str(vel) + '-clearCondition/0.org/',
                base + 'BBInfo_vel' + str(vel) + '/bodiesInfo/']


def get_solver_control_dict(vel):
    """
        path of the controlDict written for one velocity

        vel ... velocity tag of the case, such as 1.12
    """
    return '../20_solver_and_numerics/controlDict_vel' + str(vel)


def create_case_directory(case_name, vel, cores, clear_conditions=True):
    """
        assemble one case under ../ZZ_OutputCases

        case_name ... name of the case directory to create
        vel ... velocity tag of the case, such as 1.12
        cores ... (x, y, z) number of subdomains in each direction
        clear_conditions ... start from the empty bed instead of the
                             fluidised one of the same velocity
    """
    case_dir = '../ZZ_OutputCases/' + case_name + '/'
    if os.path.isdir(case_dir):
        # ensure that the case directory is clear before filling it
        shutil.rmtree(case_dir)
    os.makedirs(case_dir)

    # the solver dictionaries, then the case specific files on top of them
    shutil.copytree('../20_solver_and_numerics/system/', case_dir + 'system')
    shutil.copytree('../20_solver_and_numerics/constant/',
                    case_dir + 'constant')
    shutil.copy(get_mesh_config(vel), case_dir + '/system/blockMeshDict')
    initial_conditions = get_initial_conditions(vel, clear_conditions)
    shutil.copytree(initial_conditions[0], case_dir + '0.01')
    if not clear_conditions:
        os.chdir(case_dir + '0.01')
        for field in ['U', 'p', 'lambda', 'f']:
            if(field == 'U'):
                os.system("cat U.zip.part-* > U.zip")
            os.system("unzip "+field+".zip ")
            os.system("rm -f "+field+".zip")
            if(field == 'U'):
                os.system("rm -f U.zip.part-*")
        os.chdir('../../../00_python_codes/')
    shutil.copytree(initial_conditions[1], case_dir + 'bodiesInfo')
    shutil.copy(get_solver_control_dict(vel),
                case_dir + '/system/controlDict')

    # the number of subdomains and their layout, patched into the template
    n_subdomains = cores[0] * cores[1] * cores[2]
    replace_in_file(case_dir + '/system/decomposeParDict', 'AAAA',
                    n_subdomains)
    replace_in_file(case_dir + '/system/decomposeParDict', 'BBBB',
                    '(' + str(cores[0]) + ' ' + str(cores[1]) + ' ' +
                    str(cores[2]) + ')')

    shutil.copy(get_dem_config(vel), case_dir + '/constant/HFDIBDEMDict')
    shutil.copy(get_transport_properties(),
                case_dir + '/constant/transportProperties')

    # shFolder = '../01_bash_codes/'     # source directory for bash codes
    # shList   = ['Allrun', 'Allclean']
    shutil.copy('../01_bash_codes/Allrun', case_dir)
    shutil.copy('../01_bash_codes/Allclean', case_dir)

    # the fast visualization script, so the case can be inspected on its own
    shutil.copy('../00_python_codes/convert_bodies_info_into_vtk.py',
                case_dir)
    shutil.copy('../00_python_codes/rename_time_folders_for_display.py',
                case_dir)


# main -----------------------------------------------------------------


def main():
    """
        build one case per block below; each block is self-contained so it
        can be edited, duplicated or deleted on its own

        clear_conditions ... start from the empty bed instead of the
                             fluidised one of the same velocity
    """
    # EDITABLE -- one block per case
    # clear_conditions = True
    clear_conditions = False

    vel_type = 1.12
    date = '20261027'
    cores = (4, 6, 2)  # number of cores in each direction
    n_cores = cores[0] * cores[1] * cores[2]
    case_name = f'{date}_FullCase_vel{vel_type}_nCores{n_cores}'
    create_case_directory(case_name, vel_type, cores, clear_conditions)
    print(SEPARATOR)
    print(f'Case {case_name} created successfully.')
    print('See ZZ_OutputCases folder for the case directory.')
    print(SEPARATOR)

    # vel_type = 1.4
    # date = '20261027'
    # cores = (4, 6, 2)  # number of cores in each direction
    # n_cores = cores[0] * cores[1] * cores[2]
    # case_name = f'{date}_FullCase_vel{vel_type}_nCores{n_cores}'
    # create_case_directory(case_name, vel_type, cores, clear_conditions)
    # print(SEPARATOR)
    # print(f'Case {case_name} created successfully.')
    # print('See ZZ_OutputCases folder for the case directory.')
    # print(SEPARATOR)

    # vel_type = 1.68
    # date = '20261027'
    # cores = (4, 12, 2)  # number of cores in each direction
    # n_cores = cores[0] * cores[1] * cores[2]
    # case_name = f'{date}_FullCase_vel{vel_type}_nCores{n_cores}'
    # create_case_directory(case_name, vel_type, cores, clear_conditions)
    # print(SEPARATOR)
    # print(f'Case {case_name} created successfully.')
    # print('See ZZ_OutputCases folder for the case directory.')
    # print(SEPARATOR)


# launcher -------------------------------------------------------------
if __name__ == "__main__":
    main()
