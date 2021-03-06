from typing import Dict

from rio_tiler.types import ColorMapType

lidar_colormaps: Dict[str, ColorMapType] = {
    "lidar-classification": {
        -9999: (0, 0, 0, 0),
        0: (211, 211, 211, 255),
        2: (139, 51, 38, 255),
        3: (143, 201, 157, 255),
        4: (5, 159, 43, 255),
        5: (47, 250, 11, 255),
        6: (209, 151, 25, 255),
        7: (232, 41, 7, 255),
        8: (197, 0, 204, 255),
        9: (26, 44, 240, 255),
        10: (165, 160, 173, 255),
        11: (81, 87, 81, 255),
        12: (203, 210, 73, 255),
        13: (209, 228, 214, 255),
        14: (160, 168, 231, 255),
        15: (220, 213, 164, 255),
        16: (214, 211, 143, 255),
        17: (151, 98, 203, 255),
        18: (236, 49, 74, 255),
        19: (185, 103, 45, 255),
        21: (58, 55, 9, 255),
        22: (76, 46, 58, 255),
        23: (20, 76, 38, 255),
        26: (78, 92, 32, 255),
    },
    "lidar-returns": [
        ((-900, 1), (0, 0, 0, 0)),
        ((1, 2), (247, 252, 245, 255)),
        ((2, 3), (201, 234, 194, 255)),
        ((3, 4), (123, 199, 124, 255)),
        ((4, 5), (42, 146, 75, 255)),
        ((5, 6), (0, 68, 27, 255)),
        ((6, 7), (0, 51, 17, 255)),
        ((7, 100), (0, 26, 9, 255)),
    ],
    "lidar-hag": [
        ((-900, 1), (0, 0, 0, 0)),
        ((1, 2), (205, 224, 241, 255)),
        ((2, 3), (175, 209, 231, 255)),
        ((3, 4), (137, 190, 220, 255)),
        ((4, 5), (96, 166, 210, 255)),
        ((5, 6), (34, 114, 181, 255)),
        ((6, 7), (10, 84, 158, 255)),
        ((7, 100), (8, 48, 107, 255)),
    ],
    "lidar-hag-alternative": [
        ((-900, 0), (0, 0, 0, 0)),
        ((0, 1), (11, 44, 122, 255)),
        ((1, 2), (19, 87, 133, 255)),
        ((2, 4), (26, 129, 143, 255)),
        ((4, 6), (31, 156, 137, 255)),
        ((6, 8), (22, 181, 104, 255)),
        ((8, 10), (10, 204, 46, 255)),
        ((10, 12), (33, 222, 0, 255)),
        ((12, 14), (123, 237, 0, 255)),
        ((14, 16), (221, 250, 0, 255)),
        ((16, 18), (250, 229, 5, 255)),
        ((18, 20), (242, 192, 12, 255)),
        ((20, 22), (237, 164, 19, 255)),
        ((22, 25), (224, 129, 34, 255)),
        ((25, 30), (209, 102, 48, 255)),
        ((30, 100), (194, 82, 60, 255)),
    ],
    "lidar-intensity": [
        ((0, 16), (0, 0, 0, 255)),
        ((16, 32), (17, 17, 17, 255)),
        ((32, 48), (34, 34, 34, 255)),
        ((48, 64), (51, 51, 51, 255)),
        ((64, 80), (68, 68, 68, 255)),
        ((80, 96), (85, 85, 85, 255)),
        ((96, 112), (102, 102, 102, 255)),
        ((112, 128), (119, 119, 119, 255)),
        ((128, 144), (137, 137, 137, 255)),
        ((144, 160), (154, 154, 154, 255)),
        ((160, 176), (171, 171, 171, 255)),
        ((176, 192), (188, 188, 188, 255)),
        ((192, 208), (205, 205, 205, 255)),
        ((208, 224), (222, 222, 222, 255)),
        ((224, 240), (239, 239, 239, 255)),
        ((240, 256), (255, 255, 255, 255)),
        ((256, 4096), (0, 0, 0, 255)),
        ((4096, 8192), (17, 17, 17, 255)),
        ((8192, 12288), (34, 34, 34, 255)),
        ((12288, 16384), (51, 51, 51, 255)),
        ((16384, 20480), (68, 68, 68, 255)),
        ((20480, 24576), (85, 85, 85, 255)),
        ((24576, 28672), (102, 102, 102, 255)),
        ((28672, 32768), (119, 119, 119, 255)),
        ((32768, 36864), (137, 137, 137, 255)),
        ((36864, 40960), (154, 154, 154, 255)),
        ((40960, 45056), (171, 171, 171, 255)),
        ((45056, 49152), (188, 188, 188, 255)),
        ((49152, 53248), (205, 205, 205, 255)),
        ((53248, 57344), (222, 222, 222, 255)),
        ((57344, 61440), (239, 239, 239, 255)),
        ((61440, 65536), (255, 255, 255, 255)),
    ],
}

"""
Standard USGS LiDAR Classification color set
0 211 211 211 255 None
2 139 51 38 255 Ground
3 143 201 157 255 Low Veg
4 5 159 43 255 Med Veg
5 47 250 11 255 High Veg
6 209 151 25 255 Building
7 232 41 7 255 Low Point
8 197 0 204 255 Reserved
9 26 44 240 255 Water
10 165 160 173 255 Rail
11 81 87 81 255 Road
12 203 210 73 255 Reserved
13 209 228 214 255 Wire - Guard (Shield)
14 160 168 231 255 Wire - Conductor (Phase)
15 220 213 164 255 Transmission Tower
16 214 211 143 255 Wire-Structure Connector (Insulator)
17 151 98 203 255 Bridge Deck
18 236 49 74 255 High Noise
19 185 103 45 255 Reserved
21 58 55 9 255 255 Reserved
22 76 46 58 255 255 Reserved
23 20 76 38 255 255 Reserved
26 78 92 32 255 255 Reserved
"""
