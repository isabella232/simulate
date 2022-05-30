"""
Builds map using Wave Function Collapse.
"""

import os

import numpy as np
from PIL import Image
from wfc_binding import run_wfc

import simenv as sm

from ..utils import decode_rgb


def get_sides_and_bottom(x, y, z, down):
    """
    Get a bottom basis for the structured grid.
    """
    # TODO: generate 3d mesh with all of this

    xx_0 = x[0, :]
    yx_0 = [y[0, 0]] * 2
    xx_0, yx_0 = np.meshgrid(xx_0, yx_0)
    zx_0 = np.zeros(xx_0.shape)
    zx_0[0, :] = z[0, :]
    zx_0[1, :] = down

    xx_1 = x[-1, :]
    yx_1 = [y[-1, 0]] * 2
    xx_1, yx_1 = np.meshgrid(xx_1, yx_1)
    zx_1 = np.zeros(xx_1.shape)
    zx_1[0, :] = z[-1, :]
    zx_1[1, :] = down

    yy_0 = y[:, 0]
    xy_0 = [x[0, 0]] * 2
    xy_0, yy_0 = np.meshgrid(xy_0, yy_0)
    zy_0 = np.zeros(xy_0.shape)
    zy_0[:, 0] = z[:, 0]
    zy_0[:, 1] = down

    yy_1 = y[:, -1]
    xy_1 = [x[0, -1]] * 2
    xy_1, yy_1 = np.meshgrid(xy_1, yy_1)
    zy_1 = np.zeros(xy_1.shape)
    zy_1[:, 0] = z[:, -1]
    zy_1[:, 1] = down

    # Down base
    x_down = [x[0, 0], x[0, -1]]
    y_down = [y[0, 0], y[-1, 0]]
    x_down, y_down = np.meshgrid(x_down, y_down)
    z_down = np.full(x_down.shape, down)

    structures = [
        sm.StructuredGrid(x=x_down, y=y_down, z=z_down, name="bottom_surface"),
        sm.StructuredGrid(x=xx_0, y=yx_0, z=zx_0),
        sm.StructuredGrid(x=xx_1, y=yx_1, z=zx_1),
        sm.StructuredGrid(x=xy_0, y=yy_0, z=zy_0),
        sm.StructuredGrid(x=xy_1, y=yy_1, z=zy_1),
    ]

    return structures


def generate_2d_map(
    width,
    height,
    gen_folder,
    periodic_output=True,
    N=2,
    periodic_input=False,
    ground=False,
    nb_samples=1,
    symmetry=1,
    sample_from=None,
    seed=None,
):
    """
    Generate 2d map.
    """
    # TODO: Open image if it's cached

    # Check if seed should be used
    if seed is not None:
        use_seed = True
    else:
        use_seed = False
        seed = 0

    # Otherwise, generate it
    if sample_from is not None:
        # Overlapping routine
        # Creates a new map from a previous one by sampling patterns from it
        # Need to transform string into bytes for the c++ function
        run_wfc(
            width,
            height,
            1,
            input_img=sample_from.encode("utf-8"),
            periodic_output=periodic_output,
            N=N,
            periodic_input=periodic_input,
            ground=ground,
            nb_samples=nb_samples,
            symmetry=symmetry,
            use_seed=use_seed,
            seed=seed,
            dir_path=gen_folder.encode("utf-8"),
        )
        img_path = os.path.join(gen_folder, "maps/sampled_image0.png")

    else:
        # Simpletiled routine
        # Builds map from generated tiles and respective constraints
        run_wfc(
            width,
            height,
            0,
            periodic_output=periodic_output,
            use_seed=use_seed,
            seed=seed,
            dir_path=gen_folder.encode("utf-8"),
        )
        img_path = os.path.join(gen_folder, "maps/tiles.png")

    # Read file
    img = Image.open(img_path)
    return img


def generate_map(
    width=None,
    height=None,
    periodic_output=False,
    tile_size=10,
    gen_folder=".gen_files",
    height_constant=0.2,
    specific_map=None,
    sample_from=None,
    max_height=8,
    N=2,
    periodic_input=False,
    ground=False,
    nb_samples=1,
    symmetry=1,
    seed=None,
):
    """
    Generate the map.

    Args:
        seed: The seed to use for the generation of the map.
        width: The width of the map.
        height: The height of the map.
        tile_size: The size of the resulting tiles.
        gen_folder: where to find all generation-necessary files.

    NOTE: This is a draft.
    """

    if specific_map is not None:
        # TODO: deal with images with tiles 2x2
        img = Image.open(os.path.join(gen_folder, "maps", specific_map + ".png"))
        width = img.width
        height = img.height
    else:
        img = generate_2d_map(
            width,
            height,
            gen_folder,
            sample_from=sample_from,
            periodic_output=periodic_output,
            N=N,
            periodic_input=periodic_input,
            ground=ground,
            nb_samples=nb_samples,
            symmetry=symmetry,
            seed=seed,
        )

    img_np = decode_rgb(
        img, height_constant, specific_map=specific_map, sample_from=sample_from, max_height=max_height
    )
    map_2d = img_np.copy()

    # First we will just extract the map and plot
    z_grid = img_np

    # Let's say we want tiles of tile_size x tile_size pixels, and a certain "size" on number
    # of tiles:
    # TODO: change variables and make this clearer
    # Number of divisions for each tile on the mesh
    granularity = 10

    x = np.linspace(-width * tile_size // 2, width * tile_size // 2, granularity * width)
    y = np.linspace(-height * tile_size // 2, height * tile_size // 2, granularity * height)

    x, y = np.meshgrid(x, y)

    # create z_grid
    img_np = np.array(np.hsplit(np.array(np.hsplit(img_np, width)), height))

    z_grid = np.linspace(img_np[:, :, :, 0], img_np[:, :, :, 1], granularity)
    z_grid = np.linspace(z_grid[:, :, :, 0], z_grid[:, :, :, 1], granularity)
    z_grid = np.transpose(z_grid, (2, 0, 3, 1)).reshape((height * granularity, width * granularity), order="A")

    # Create the mesh
    scene = sm.Scene()
    scene += sm.StructuredGrid(x=x, y=y, z=z_grid, name="top_surface")
    scene += get_sides_and_bottom(x, y, z_grid, down=-10)

    return (x, y, z_grid), map_2d, scene
