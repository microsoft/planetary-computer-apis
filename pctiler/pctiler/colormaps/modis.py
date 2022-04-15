from typing import Dict

from rio_tiler.types import ColorMapType

modis_colormaps: Dict[str, ColorMapType] = {
    "modis-10A1": [
        ((0,25),(43, 140, 190, 255)),
        ((25,50),(116, 169, 207, 255)),
        ((50,75),(189, 201, 225, 255)),
        ((75,100),(241, 238, 246, 255)),
        ((101,255),(0, 0, 0, 0)), 
    ],
    "modis-10A2": {
        0: (0, 0, 0, 0),
        1: (0, 0, 0, 0),
        11: (99, 99, 99, 255),
        25: (20, 91, 22, 255),
        37: (0, 11, 128, 255),
        39: (0, 11, 128,255),
        50: (128, 128, 128, 255),
        100: (0, 254, 237, 255),
        200: (204, 115, 255, 255),
        254: (0, 0, 0, 0),
        255: (0, 0, 0, 0),
    },
    "modis-13A1|Q1": [
        ((0,0), (255, 255, 255, 255)),
        ((0,1300), (214, 196, 181, 255)),
        ((13000,2600), (172, 137, 106, 255)),
        ((2600,3900), (233, 234, 220, 255)),
        ((3900,5200), (183, 204, 173, 255)),
        ((5200,6500), (134, 173, 126, 255)),
        ((6500,7800), (84, 143, 79, 255)),
        ((7800,9000), (38, 114, 36, 255)),
        ((9000,10000), (0, 91, 0, 255)),
    ],
    "modis-14A1|A2": {
        0: (255, 255, 255, 255),
        1: (255, 255, 255, 255),
        2: (255, 255, 255, 255),
        3: (255, 255, 255, 0),
        4: (128, 128, 128, 255),
        5: (255, 255, 255, 0),
        6: (255, 255, 255, 0),
        7: (247, 160, 10, 255),
        8: (222, 96, 0, 255),
        9: (242, 4, 0, 255),
    },
    "modis-15A2H|A3H": [
        ((0,0.5), (99, 190, 53)),
        ((0.5,3), (73, 158, 52, 255)),
        ((3,6), (49, 120, 34, 255)),
        ((6,10), (24, 83, 17, 255)),
        ((10,100), (0, 46, 0, 255)),
        ((100,255), (0, 0, 0, 0)),
    ],
    "modis-16A3GF-ET": [
        ((0,1500),(255, 234, 70, 255)),
        ((1500,3000),(230, 212, 84, 255)),
        ((3000,4500),(204, 190, 99, 255)),
        ((4500,6000),(179, 167, 113, 255)),
        ((6000,7500),(158, 150, 119, 255)),
        ((7500,9000),(135, 132, 120, 255)),
        ((10500,12000),(99, 103, 112, 255)),
        ((12000,65500),(54, 66, 89, 255)),
        ((65500,65535),(0, 0, 0, 0)),
    ],
     "modis-16A3GF-PET": [
        ((0,2500),(255, 234, 70, 255)),
        ((2500,5000),(230, 212, 84, 255)),
        ((5000,7500),(204, 190, 99, 255)),
        ((7500,10000),(179, 167, 113, 255)),
        ((10000,12500),(158, 150, 119, 255)),
        ((12500,15000),(135, 132, 120, 255)),
        ((15000,17500),(99, 103, 112, 255)),
        ((17500,65500),(54, 66, 89, 255)),
        ((65500,65535),(0, 0, 0, 0)),
    ],
    "modis-17A2H|A2HGF": [
        ((-4,1),(254, 201, 141, 255)),
        ((1,7),(253, 149, 103, 255)),
        ((7,12),(241, 96, 93, 255)),
        ((12,18),(205, 63, 113, 255)),
        ((18,23),(158, 47, 127, 255)),
        ((23,29),(114, 31, 129, 255)),
        ((29,34),(69, 15, 118, 255)),
        ((34,30000),(24, 15, 62, 255)),
        ((30000,32767),(0, 0, 0, 0)),
    ],
    "modis-17A3HGF": [
        ((0,4000),(254, 201, 141, 255)),
        ((4000,8000),(253, 149, 103, 255)),
        ((8000,12000),(241, 96, 93, 255)),
        ((12000,16000),(205, 63, 113, 255)),
        ((16000,20000),(158, 47, 127, 255)),
        ((20000,24000),(114, 31, 129, 255)),
        ((24000,28000),(69, 15, 118, 255)),
        ((28000,32700),(24, 15, 62, 255)),
        ((32700,32767),(0, 0, 0, 0)),
    ], 
    "modis-64A1": [
        ((-2,0),(0, 0, 0, 0)),
        ((1,32),(255, 255, 178, 255)),
        ((32,60),(255, 236, 147, 255)),
        ((60,91),(254, 218, 115, 255)),
        ((91,121),(254, 198, 89, 255)),
        ((121,152),(254, 175, 77, 255)),
        ((152,182),(253, 152, 66, 255)),
        ((182,213),(251, 126, 55, 255)),
        ((213,244),(246, 96, 45, 255)),
        ((244,274),(241, 66, 35, 255)),
        ((274,305),(226, 43, 34, 255)),
        ((305,335),(208, 21, 36, 255)),
        ((335,366),(189, 0, 38, 255)),
    ],
}
