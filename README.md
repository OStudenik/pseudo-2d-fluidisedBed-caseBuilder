# Simulation builder for digital twin of pseudo-2D fluidized-bed

This repository assembles OpenFOAM cases for the study **Particle-resolved
direct numerical simulation of fluidized bed: Analysis of collision dynamics**,
by Ondřej Studeník, Jarmila Terpáková, Petr Kočí, Jan Haidl and Martin Isoz.

The study validates openHFDIB-DEM [[1]](#references) against the experimental
data of Jiang *et al.* [[2]](#references), and examines particle collision
dynamics in a pseudo-2D fluidized bed.

The repository does **not** ship ready-to-run cases. It contains case
ingredients—meshes, solver dictionaries, DEM and transport properties, and
initial and boundary conditions—plus Python scripts that assemble them into
complete cases. It includes builders for a single-particle drag assessment, a
mesh size independence study, and full-bed simulations.

## Contents

- [Repository layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [1. Compile the solver](#1-compile-the-solver)
- [2. Generate the cases](#2-generate-the-cases)
- [3. Run a case](#3-run-a-case)
- [4. Post-processing](#4-post-processing)
- [Notes](#notes)
- [License](#license)
- [References](#references)

## Repository layout

| Path | Contents |
| --- | --- |
| [`00_python_codes/`](00_python_codes) | Case builders and post-processing utilities. Run the builders from this directory. |
| [`01_bash_codes/`](01_bash_codes) | `Allrun` and `Allclean`, copied into each generated case. |
| [`10_drag_study/`](10_drag_study) | Mesh template and settings for the single-sphere drag assessment. |
| [`11_MSI_study/`](11_MSI_study) | Mesh template and settings for the mesh size independence study. |
| [`12_full_system_simulations/`](12_full_system_simulations) | Full-bed meshes, one per inlet velocity. |
| [`20_solver_and_numerics/`](20_solver_and_numerics) | Shared solver and numerics dictionaries, constants, and per-velocity `controlDict` files. |
| [`30_DEM_and_transportProps/`](30_DEM_and_transportProps) | `HFDIBDEMDict` files per case family and shared `transportProperties`. |
| [`40_initial_and_boundary_conditions/`](40_initial_and_boundary_conditions) | Initial fields and bed positions per case family and velocity. |
| [`AA_OF_codes/openHFDIB-DEM/`](AA_OF_codes/openHFDIB-DEM) | Bundled openHFDIB-DEM source used by the simulations. Compile it before running a case. |

Generated cases are written to `ZZ_OutputCases/` in the repository root. The
builders create this directory if needed; generated cases are not tracked by
this repository.

## Prerequisites

- **OpenFOAM v8** from [openfoam.org](https://openfoam.org) — the bundled solver
  was developed against it. Source the OpenFOAM environment so
  `$WM_PROJECT_DIR` is set before compiling or running cases.
- **Python 3** — the case builders use the standard library only.
- **NumPy** — needed only for `convert_bodies_info_into_vtk.py`.
- **ParaView** — optional, for inspecting results.

## 1. Compile the solver

From the repository root, compile the bundled openHFDIB-DEM sources once before
running any case:

```bash
cd AA_OF_codes/openHFDIB-DEM
./compileAll.sh
cd ../..
```

This builds the HFDIB-DEM library and the `pimpleHFDIBFoam` and `HFDIBDEMFoam`
solvers used by the generated cases. The final command returns to the
repository root. With the OpenFOAM environment still sourced, confirm the
solvers are available on `PATH`:

```bash
command -v pimpleHFDIBFoam
command -v HFDIBDEMFoam
```

## 2. Generate the cases

From the repository root, enter `00_python_codes/` and run the builder or
builders for the studies you need. The scripts use paths relative to that
directory:

```bash
cd 00_python_codes
./construct_drag_msi_study_cases.py                    # drag assessment
./construct_mesh_size_indipendence_study_cases.py      # mesh size independence
./construct_full_sim_cases.py                          # full fluidized bed
```

Edit the parameters near the start of each script before running it. The
builders take their settings from these editable values:

| Parameter | Where | Meaning |
| --- | --- | --- |
| `MESH_RESOLUTIONS` | Drag and MSI builders | Cells per particle diameter. The shipped settings include 4, 6, 8 and 10; one case is built per entry. |
| `N_CORES` | Drag and MSI builders | Number of subdomains along the flow direction. The builders write the layout as `(1 n 1)` in `decomposeParDict`. |
| `cores` | Full-simulation builder | Three-value `(x, y, z)` decomposition layout. The number of MPI subdomains is the product `x × y × z`. |
| `vel_type` | Full-simulation and MSI builders | Inlet-velocity tag. Shipped values are `1.12`, `1.4` and `1.68`. |
| `clear_conditions` | Full-simulation builder | `True` starts from the clear initial condition; `False` uses the fluidized-bed initial condition for that velocity. |
| `date` | All builders | Date label used in the case name. The shipped values use `YYYYMMDD` format. |

In the full-simulation builder, edit the active block in `main()` to choose
which case to build. In the drag and MSI builders, cases are created for each
entry in `MESH_RESOLUTIONS`.

> **Warning:** If a generated case directory with the same name already exists,
> its contents are deleted and replaced. This can remove simulation results.
> Back up any files you need, or choose a different `date` (and therefore a
> different case name) before rebuilding.

Cases are written to `ZZ_OutputCases/` with names that record how they were
built. Each receives `Allrun`, `Allclean` and the relevant post-processing
scripts:

| Study | Case name pattern |
| --- | --- |
| Drag assessment | `<date>_drag_test_res<resolution>_nCores<n>` |
| Mesh size independence | `<date>_MSI_vel<velocity>_res<resolution>_nCores<n>` |
| Full simulations | `<date>_FullCase_vel<velocity>_nCores<n>` |

**Check a generated case:** each case should contain `system/blockMeshDict`,
`system/controlDict`, `system/decomposeParDict`, and
`constant/HFDIBDEMDict` plus `constant/transportProperties`. The initial fields
are in `0/` for the drag study and `0.01/` for MSI and full simulations. Full
simulations also include `bodiesInfo/`.

## 3. Run a case

From the repository root, move into a generated case directory and start it:

```bash
cd ZZ_OutputCases/<case-name>
./Allrun      # blockMesh, decomposePar, then the solver in parallel
```

`Allrun` uses the decomposition settings written by the builder and starts the
parallel solver in the background. It may return before the simulation
finishes. Monitor the solver output/logs in the case directory and wait for
the solver's MPI processes to exit before post-processing or cleaning the case.
On a cluster, also ensure the OpenFOAM environment, MPI setup, and scheduler
allocation are appropriate for the case's configured number of subdomains.

To remove generated mesh, decomposition, and result files, run the clean
script from the case directory **only after saving anything you want to keep**:

```bash
./Allclean
```

## 4. Post-processing

The case builders copy the post-processing utilities they need into the
generated case. Run them from inside that case directory, after the solver has
finished.

- `rename_time_folders_for_display.py` renumbers time directories to consecutive
  integers so the CFD and DEM outputs can be displayed together in ParaView.
  **Run this only on a copy of the results if the original time-directory names
  need to be preserved.**
- `convert_bodies_info_into_vtk.py` converts the per-body dictionaries under
  `bodiesInfo/` into one ASCII POLYDATA file per time level in `VTKReconstruct/`,
  carrying the point fields `id`, `static`, `r`, `v` and `omega`. Non-spherical
  bodies are skipped. ParaView cannot read the solver's `.info` files directly.
  Install NumPy to use this utility. Set `n_present` in the script to resume an
  interrupted conversion.

## Notes

- The bed and clear initial condition of the MSI study were prepared for an
  inlet velocity of `1.68`. Keep the velocity at this value unless the bed is
  reset as well.
- The full-bed initial fields ship as `.zip` archives under
  `40_initial_and_boundary_conditions/vel*-full/`. The builder unpacks them into
  the case, so no manual step is needed.
- Further instructions are in the `==FILE DESCRIPTION==` block at the head of
  every Python script.

## License

This repository is released under the **GNU General Public License v3.0** —
see [LICENSE](LICENSE). The Python scripts carry the corresponding header and
are copyright of Ondřej Studeník and Martin Isoz.

The bundled sources under [`AA_OF_codes/openHFDIB-DEM/`](AA_OF_codes/openHFDIB-DEM)
are based on upstream openHFDIB-DEM [[1]](#references) and include repository
changes. Their file headers identify them as **GNU Lesser General Public
License v3.0 (LGPL-3.0)**; those files remain subject to that license. The
repository's GPL-3.0 license does not replace the license notices on the
bundled sources. Refer to the individual file headers and repository history
for source and change details.

## References

[1] **openHFDIB-DEM** — a coupled immersed-boundary / discrete element solver
    for OpenFOAM. Repository: <https://github.com/techMathGroup/openHFDIB-DEM>

[2] Z. Jiang, T. Hagemeier, A. Buck, E. Tsotsas, *Experimental measurements of
    particle collision dynamics in a pseudo-2D gas–solid fluidized bed*,
    Chemical Engineering Science **167** (2017) 297–316.
    <https://doi.org/10.1016/j.ces.2017.04.024>

---

Maintained by [Ondřej Studeník](https://github.com/OStudenik) and
[Martin Isoz](https://github.com/MartinIsoz).
