def get_bbox(DX, DY, DZ, OX, OY, max_commits):
    # week = 0, day = 0
    py_min = OY - (max_commits * DZ) - DY
    
    # week = 53, day = 6
    py_max = (53 + 6) * DY + OY + DY
    
    return py_min, py_max

print("BBox 250:", get_bbox(14, 8, 3, 150, 250, 50))
