#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
==FILE DESCRIPTION======================================================

 Renames the time level directories of a case to consecutive integers, so
 that CFD and DEM output can be displayed side by side in ParaView. The
 solver writes the time as a float directory name, while the DEM side is
 only able to carry integer time values, and ParaView assigns no distinct
 time to float named directories. The directories are sorted by their
 float value and renumbered from zero upwards, which keeps their order.

 Run it inside the case directory holding the time folders. The rename is
 done through a temporary renamedDirs/ folder, and the list of sorted time
 levels is printed for confirmation before anything is moved.

     ./rename_time_folders_for_display.py

==LICENSE===============================================================
  rename_time_folders_for_display.py

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


# auxiliary functions --------------------------------------------------


def can_be_converted_to_float(value):
    """
        tell whether a input value can be read as a time value

        value ... the directory name to test
    """
    try:
        float(value)
        return True
    except ValueError:
        return False


def should_be_converted_int(value):
    """
        tell whether a input value carries no fractional part

        value ... the directory name to test
    """
    try:
        if float(value) == int(value):
            return True
        else:
            return False
    except ValueError:
        return False


def get_all_time_level_dirs():
    """
        collect the time level directories of the current folder, sorted by
        their value as floats
    """
    all_dirs = os.listdir()
    time_level_dirs = []
    for name in all_dirs:
        if can_be_converted_to_float(name):
            if should_be_converted_int(name):
                time_level_dirs.append(int(name))
            else:
                time_level_dirs.append(float(name))
    time_level_dirs.sort(key=float)
    return time_level_dirs


# main -----------------------------------------------------------------


def main():
    """
        renumber the time level directories of the current case from zero
        upwards, after showing them and asking for confirmation
    """
    # Rename all time level directories to integers
    if os.path.isdir('renamedDirs'):
        os.system("rm -r renamedDirs")
    os.system("mkdir renamedDirs")
    time_level_dirs = get_all_time_level_dirs()
    print("This is sorted time level directories: ", time_level_dirs)
    print("Do you want to rename these directories to integers? (Y/n)")
    answer = input()
    if answer == 'n' or answer == 'N':
        print("Exiting...")
        return

    i = 0  # adjust this to start from a different number
    for name in time_level_dirs:
        os.system("mv " + str(name) + " renamedDirs/" + str(i))
        i += 1
    os.system("mv renamedDirs/* .")
    os.system("rmdir renamedDirs")


# launcher -------------------------------------------------------------
if __name__ == "__main__":
    main()
