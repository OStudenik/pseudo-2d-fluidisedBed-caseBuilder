#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
==FILE DESCRIPTION======================================================

 Assembles the cases of the mesh size independence study (MSI) under
 ../ZZ_OutputCases. Every case carries the same bed, the same initial
 fields, the same solver dictionaries and the same numerics, and only the
 mesh resolution changes, so that a difference between two cases is
 attributable to the mesh alone.

 Three parameters are editable. The mesh resolution is taken from
 MESH_RESOLUTIONS, which maps the number of cells per particle diameter
 onto the block of the mesh template, and one case is built per entry. The
 inlet velocity is patched into the inlet patch of the initial fields. The
 number of cores is written into decomposeParDict as a simple
 decomposition along the flow direction, n (1 nCores 1), which is the
 layout the study recommends.

 The ingredients live in the same folders as for the full simulations, so
 the study stays comparable with them:

     11_MSI_study/system/          blockMeshDict, controlDict and
                                   decomposeParDict of the study, the mesh
                                   template carrying no active block of its
                                   own -- the resolution is written in here
     20_solver_and_numerics/       fvSchemes, fvSolution, fvOptions and the
                                   shared constants
     30_DEM_and_transportProps/    HFDIBDEMDict_MSI, transportProperties
     40_initial_and_boundary_conditions/
                                   MSI-clearCondition/0.org, BBInfo_MSI
     01_bash_codes/                Allrun, Allclean

 The bed and the clear initial condition were prepared for an inlet
 velocity of 1.68, so keep the velocity there unless the bed is reset as
 well. Run

     ./construct_mesh_size_indipendence_study_cases.py

 from inside 00_python_codes/, as the paths are all relative.

==LICENSE===============================================================
  construct_mesh_size_indipendence_study_cases.py

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
# -- text processing
import re

# -- I/O operations
import os
from pathlib import Path
import shutil


# constants ------------------------------------------------------------
# the rule printed around the report of every built case
SEPARATOR = '-' * 69

# the mesh variants of the study, given as cells per particle diameter,
# commented out to leave a variant out of the study
MESH_RESOLUTIONS = {
    10: (83, 1333, 28),
    8: (66, 1056, 22),
    6: (50, 800, 17),
    4: (33, 533, 11),
}

# every block line of the mesh template, active or commented out
BLOCK_LINES = re.compile(
    r'(?:^[ \t]*(?://[ \t]*)?hex[ \t]*\(0 1 2 3 4 5 6 7\)[^\n]*\n)+',
    re.MULTILINE)

# the entries decomposeParDict is patched through, a literal value or the
# AAAA and BBBB placeholders the shared template carries
SUBDOMAINS = re.compile(r'(?m)^(numberOfSubdomains[ \t]+)[^;]+;')
LAYOUT = re.compile(r'(?m)^([ \t]*n[ \t]+)[^;]+;')
METHOD = re.compile(r'(?m)^method[ \t]+(\S+);')

# the value of the inlet patch of the initial fields, the brace of the
# patch being allowed to sit on a line of its own
INLET_VALUE = re.compile(r'(?s)(inlet\s*\{[^{}]*?value\s+uniform\s*\()'
                         r'[^)]*\)')


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


def rewrite_file(file_path, pattern, replacement, what):
    """
        patch one entry of a copied dictionary in place

        file_path ... path to the file to work with
        pattern ... regular expression matching the entry to patch
        replacement ... text the match is replaced with, the back
                        references of pattern being kept
        what ... name of the entry, reported when pattern misses it
    """
    file_path = Path(file_path)
    content = file_path.read_text()
    new_content, n_found = pattern.subn(replacement, content, count=1)
    if n_found == 0:
        raise FileNotFoundError(f'no {what} in {file_path}')
    if new_content != content:
        file_path.write_text(new_content)
    return n_found


def get_mesh_config():
    """
        path of the mesh template of the study, the resolution being
        patched into it case by case
    """
    return '../11_MSI_study/system/blockMeshDict'


def get_control_dict():
    """
        path of the controlDict of the study, shared by every resolution
    """
    return '../11_MSI_study/system/controlDict'


def get_decompose_config():
    """
        path of the decomposeParDict of the study, a simple decomposition
    """
    return '../11_MSI_study/system/decomposeParDict'


def get_dem_config():
    """
        path of the DEM dictionary the bed of the study is set in
    """
    return '../30_DEM_and_transportProps/HFDIBDEMDict_MSI'


def get_transport_properties():
    """
        path of the shared transport properties dictionary
    """
    return '../30_DEM_and_transportProps/transportProperties'


def get_initial_conditions():
    """
        paths of the initial fields and of the initial bed of the study
    """
    return ['../40_initial_and_boundary_conditions/MSI-clearCondition/0.org/',
            '../40_initial_and_boundary_conditions/BBInfo_MSI/bodiesInfo/']


def set_mesh_resolution(file_path, resolution):
    """
        write the block of one resolution into the mesh template, replacing
        the whole set of variants it offers

        file_path ... mesh dictionary to patch
        resolution ... cells per particle diameter, a key of
                       MESH_RESOLUTIONS
    """
    n_x, n_y, n_z = MESH_RESOLUTIONS[resolution]
    block = (f'    hex (0 1 2 3 4 5 6 7) ({n_x} {n_y} {n_z}) '
             f'simpleGrading (1 1 1) '
             f'// {resolution} cells per particle diameter\n')
    rewrite_file(file_path, BLOCK_LINES, block, 'mesh block')
    return


def set_inlet_velocity(file_path, vel):
    """
        write the inlet velocity into the inlet patch of the initial fields

        file_path ... initial velocity field to patch
        vel ... inlet velocity of the case, such as 1.68
    """
    rewrite_file(file_path, INLET_VALUE, f'\\g<1>0.0 {vel} 0)',
                 'inlet velocity')
    return


def set_subdomains(file_path, n_cores):
    """
        write the number of subdomains and their layout into the
        decomposition dictionary, one subdomain per core along the flow

        file_path ... decomposition dictionary to patch
        n_cores ... number of cores the case decomposes to
    """
    rewrite_file(file_path, SUBDOMAINS, f'\\g<1>{n_cores};',
                 'number of subdomains')
    rewrite_file(file_path, LAYOUT, f'\\g<1>(1 {n_cores} 1);',
                 'subdomain layout')
    method = METHOD.search(Path(file_path).read_text())
    if method is None:
        raise FileNotFoundError(f'no decomposition method in {file_path}')
    if method.group(1) != 'simple':
        print('-- Warning: the case decomposes by ' + method.group(1) +
              ', the study recommends the simple decomposition')
    return


def create_case_directory(case_name, vel, resolution, n_cores):
    """
        assemble one case of the study under ../ZZ_OutputCases

        case_name ... name of the case directory to create
        vel ... inlet velocity of the case, such as 1.68
        resolution ... cells per particle diameter, a key of
                       MESH_RESOLUTIONS
        n_cores ... number of cores the case decomposes to
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
    shutil.copy(get_control_dict(), case_dir + '/system/controlDict')
    shutil.copy(get_decompose_config(), case_dir + '/system/decomposeParDict')
    shutil.copy(get_mesh_config(), case_dir + '/system/blockMeshDict')
    initial_conditions = get_initial_conditions()
    shutil.copytree(initial_conditions[0], case_dir + '0.01')
    shutil.copytree(initial_conditions[1], case_dir + 'bodiesInfo')

    # the three adjustable parameters, patched into the copied dictionaries
    set_mesh_resolution(case_dir + '/system/blockMeshDict', resolution)
    set_inlet_velocity(case_dir + '/0.01/U', vel)
    set_subdomains(case_dir + '/system/decomposeParDict', n_cores)

    shutil.copy(get_dem_config(), case_dir + '/constant/HFDIBDEMDict')
    shutil.copy(get_transport_properties(),
                case_dir + '/constant/transportProperties')

    shutil.copy('../01_bash_codes/Allrun', case_dir)
    shutil.copy('../01_bash_codes/Allclean', case_dir)

    # the fast visualization script, so the case can be inspected on its own
    shutil.copy('../00_python_codes/convert_bodies_info_into_vtk.py',
                case_dir)


# main -----------------------------------------------------------------


def main():
    """
        build one case per mesh resolution of MESH_RESOLUTIONS, the bed, the
        initial fields and the numerics being common to all of them

        vel_type ... inlet velocity, shared by every case of the study
        date ... date stamp the cases are named by
        N_CORES ... number of cores of each resolution, decomposed as
                    n (1 n_cores 1), one entry per resolution
    """
    # EDITABLE -- shared by every case of the study
    vel_type = 1.68
    date = '20261027'

    # the number of cores of each resolution, along the flow direction
    N_CORES = {
        10: 64,
        8: 32,
        6: 16,
        4: 16,
    }

    # EDITABLE -- one case per resolution of MESH_RESOLUTIONS
    for resolution in MESH_RESOLUTIONS:
        n_cores = N_CORES[resolution]
        case_name = (f'{date}_MSI_vel{vel_type}_res{resolution}'
                     f'_nCores{n_cores}')
        create_case_directory(case_name, vel_type, resolution, n_cores)
        print(SEPARATOR)
        print(f'Case {case_name} created successfully.')
        print(f'Mesh: {MESH_RESOLUTIONS[resolution]} cells, '
              f'{resolution} per particle diameter.')
        print('See ZZ_OutputCases folder for the case directory.')
        print(SEPARATOR)


# launcher -------------------------------------------------------------
if __name__ == "__main__":
    main()
