"""Pixel scenery for the four corners of the board, painted at native resolution."""
from PIL import Image, ImageDraw


def grass_tuft(d, x, y, dark="#91ae74", light="#d3e1a3"):
    d.line([(x,y),(x-2,y-3)], dark)
    d.line([(x+1,y),(x+2,y-5)], dark)
    d.line([(x+3,y),(x+5,y-2)], dark)
    d.point((x+3,y-4), light)


def lawn(d):
    d.rectangle((0,0,71,71), fill="#c0d69c")
    d.polygon([(6,16),(9,14),(13,14),(15,13),(20,13),(21,14),(18,15),
               (13,15),(11,17),(7,17)], "#b8d097")
    d.polygon([(34,49),(38,47),(42,47),(45,46),(51,46),(52,47),(47,48),
               (42,49),(39,50),(35,50)], "#b8d097")
    for x,y in [(17,18),(54,46),(32,68)]:
        grass_tuft(d, x, y, "#a6bf86", "#d6e5aa")
    for x,y in [(4,36),(25,3),(39,28),(63,16),(9,56),(49,63)]:
        d.line([(x,y),(x+2,y)], "#cee0a7")
        d.point((x+3,y-1), "#b1ca8d")


def fence(d, x, y):
    edge, wood, light = "#7f805b", "#dfd8a5", "#f4e6b9"
    for level in (8,16):
        d.rectangle((x,y+level,x+38,y+level+3), fill=wood, outline=edge)
    for pos, lift in [(1,1),(12,0),(23,1),(34,-1)]:
        a, b = x+pos, y+lift
        d.polygon([(a,b+4),(a+2,b+1),(a+4,b+3),(a+4,b+20),(a,b+20)], wood, edge)
        d.line([(a+1,b+5),(a+1,b+18)], light)
        d.point((a+3,b+9), "#a9a07b")


def coop(d):
    grass_tuft(d, 92, 39)
    d.ellipse((-9,37,77,55), fill="#a1ba7d")
    d.ellipse((2,39,61,52), fill="#90ab70")
    fence(d, 57, 15)
    timber, dark = "#e9ac66", "#78573f"
    # Two walls with vertical boards and a small shuttered side window.
    d.polygon([(4,24),(24,8),(45,24),(45,47),(4,47)], timber, dark)
    d.polygon([(45,23),(68,16),(68,40),(45,47)], "#c98952", dark)
    for x in (9,15,21,28,35,41):
        d.line([(x,25),(x,45)], "#cc8952")
        d.line([(x+1,26),(x+1,43)], "#f8c27c")
    for x in (49,54,60,65):
        top = 24 - (x-44)//4
        d.line([(x,top),(x,top+20)], "#aa714a")
    d.polygon([(49,27),(60,24),(60,33),(49,36)], "#574543", dark)
    d.line([(50,27),(59,25)], "#f6c983", 2)
    d.line([(55,27),(55,33)], "#cc985d")
    d.line([(50,31),(59,28)], "#cc985d")
    # Sunlit rafters and a dark doorway for the chickens.
    d.line([(5,25),(43,25)], dark, 2)
    d.polygon([(15,45),(15,33),(17,30),(21,28),(26,28),(30,32),(30,45)], "#5a4940", dark)
    d.polygon([(17,44),(17,34),(20,30),(26,30),(23,33),(22,44)], "#493d39")
    d.line([(4,46),(44,46),(67,39)], "#8a6141", 2)
    d.line([(5,44),(14,44)], "#ffcf89")
    d.polygon([(17,44),(29,44),(41,54),(23,55)], "#d29e5b", dark)
    for y, left in [(47,20),(50,22),(53,24)]:
        d.line([(left,y),(left+12,y-1)], "#916640", 2)
    # Clay roof with a stepped ridge, tile courses and discrete reflected light.
    d.polygon([(0,24),(16,8),(22,3),(46,0),(52,1),(73,15),(73,18),
               (46,25),(24,10),(5,28),(0,28)], "#754740", "#56433d")
    d.polygon([(24,4),(48,1),(69,15),(45,21)], "#cc7557")
    d.polygon([(27,6),(47,3),(50,4),(30,8)], "#e99d71")
    d.line([(31,10),(54,6)], "#a95a4c", 2)
    d.line([(37,15),(61,10)], "#b56450", 2)
    d.line([(43,19),(67,14)], "#ad594a", 2)
    for x,y in [(34,6),(43,5),(38,11),(49,9),(46,16),(56,14)]:
        d.line([(x,y),(x+3,y+2)], "#b86850")
    d.line([(2,24),(21,6),(24,5),(44,20)], "#eb9b6e", 2)
    d.line([(4,28),(24,10),(43,25)], "#a97955")
    d.rectangle((22,16,26,20), fill="#77543e")
    d.line([(23,17),(25,17)], "#b57d4f")
    for x,y in [(4,50),(44,50),(71,42),(85,40)]:
        grass_tuft(d, x, y)


def shrub(d, x, y):
    silhouette = [(0,19),(2,14),(6,12),(6,8),(10,5),(14,6),(17,2),(23,1),
                  (27,5),(31,4),(35,7),(35,10),(40,12),(42,16),(41,21),
                  (37,23),(31,24),(27,26),(19,25),(14,27),(8,24),(3,24)]
    def cluster(points, color, edge=None):
        d.polygon([(x+a,y+b) for a,b in points], color, edge)
    cluster(silhouette, "#699567", "#537b59")
    cluster([(2,19),(6,13),(11,12),(10,15),(13,14),(15,9),(18,7),
             (22,7),(21,10),(26,9),(31,6),(34,8),(34,13),(30,16),(27,16),
             (24,20),(20,19),(17,21),(12,20),(8,23),(4,22)], "#84ae70")
    for a,b in [(7,14),(12,10),(19,5),(25,10),(31,8),(28,18),(17,16),(5,19)]:
        d.line([(x+a,y+b),(x+a+2,y+b-2),(x+a+4,y+b-2)], "#afc77b", 2)
    for a,b in [(10,17),(21,13),(31,15),(23,20),(14,11)]:
        d.rectangle((x+a,y+b,x+a+2,y+b+2), fill="#b76556")
        d.point((x+a,y+b), "#e8a071")


def hedge(d):
    d.ellipse((15,9,83,41), fill="#a1bb7e")
    fence(d, 12, 5)
    shrub(d, 47, 0)
    shrub(d, 29, 10)
    shrub(d, 62, 4)
    grass_tuft(d, 25, 35)
    grass_tuft(d, 59, 42)


def flower(d, x, y, petal="#fff1c6", centre="#e9af51"):
    d.line([(x,y+2),(x,y+8)], "#588458")
    d.line([(x,y+6),(x-3,y+4)], "#6f9a60", 2)
    d.rectangle((x-1,y-4,x+1,y-2), fill=petal)
    d.rectangle((x-1,y+2,x+1,y+4), fill=petal)
    d.rectangle((x-4,y-1,x-2,y+1), fill=petal)
    d.rectangle((x+2,y-1,x+4,y+1), fill=petal)
    d.rectangle((x-1,y-1,x+1,y+1), fill=centre)
    d.point((x,y), "#ffe38b")


def daisies(d):
    d.polygon([(0,23),(10,21),(17,23),(29,22),(36,25),(48,25),(55,28),
               (65,29),(65,32),(0,32)], "#9cb77a")
    for x,y in [(2,23),(10,27),(21,28),(29,24),(39,27),(47,30),(60,29)]:
        grass_tuft(d, x, y, "#68935e", "#bad489")
    for x,y in [(6,13),(19,18),(31,12),(46,21)]:
        flower(d, x, y)
    flower(d, 12, 25, "#ecc368", "#b68343")
    d.polygon([(48,29),(51,25),(57,24),(61,26),(62,29),(59,31),(50,31)],
              "#9eaa88", "#7b9175")
    d.line([(51,28),(54,26),(57,26)], "#c7c9a1", 2)


def garden(d):
    # A vegetable bed and a little enamel watering can.
    d.polygon([(25,28),(49,13),(73,16),(80,24),(80,38),(37,38)],
              "#b58967", "#917451")
    for x,y in [(34,28),(45,28),(51,21),(61,24),(66,19),(70,31)]:
        d.line([(x-3,y+1),(x,y-1),(x+4,y)], "#927653", 2)
        d.polygon([(x,y),(x-4,y-2),(x-5,y-5),(x-2,y-5),(x+1,y-2),
                   (x+2,y-6),(x+5,y-7),(x+5,y-4)], "#6e9c60", "#4d7954")
        d.point((x+3,y-5), "#b6cb7f")
    d.ellipse((8,28,37,35), fill="#99b379")
    d.arc((22,14,37,27), 255, 110, fill="#4e7674", width=3)
    d.polygon([(12,22),(7,16),(5,15),(4,17),(9,25),(14,29)], "#76aaa0", "#4a7171")
    d.line([(4,14),(7,13)], "#567e77", 3)
    d.polygon([(13,20),(26,18),(29,20),(29,30),(26,32),(16,32),(12,29)], "#69a29b", "#4c7170")
    d.polygon([(14,22),(18,22),(18,29),(15,29)], "#99c1a8")
    d.ellipse((13,17,28,22), fill="#85b3a6", outline="#4c7170")
    d.line([(17,19),(24,18)], "#527e7a")
    for x,y in [(3,34),(34,35),(62,37),(75,36)]:
        grass_tuft(d, x, y)


def stamp(d):
    rows = [
        "............###.", "..........#####.", "........#####.#.", ".......#####.##.",
        "......#####.###.", "......####.###..", ".....####.##....", "....####.####...",
        "....###.####....", "...###.###......", "...##.##........", "....###.........",
        "...###..........", "..##............", ".##.............", "................",
    ]
    for y, row in enumerate(rows):
        for x, dot in enumerate(row):
            if dot == "#":
                d.point((x, y), "white")


def paint_yard(assets):
    for name, size, paint in [
        ("lawn",(72,72),lawn), ("coop",(98,57),coop), ("hedge",(84,44),hedge),
        ("daisies",(66,33),daisies), ("garden",(80,39),garden), ("quill-stamp",(16,16),stamp),
    ]:
        image = Image.new("RGBA", size)
        paint(ImageDraw.Draw(image))
        image.save(assets / (name + ".png"), optimize=True)
