def generate_voxels(grid_size):
    """O(N^3) triple nested loop."""
    voxels = []
    for x in range(grid_size):
        for y in range(grid_size):
            for z in range(grid_size):
                voxels.append((x, y, z, 1.0))
    return voxels
