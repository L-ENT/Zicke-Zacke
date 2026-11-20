"""Original 48-pixel hens. Each frame is drawn in layers from feet to comb."""
from PIL import Image, ImageDraw

INK = "#403337"
# Shadow, midtone, body, light, glint. Feather colors identify their original owner.
PLUMAGE = [
    ("#a16937", "#dfa249", "#f3c65b", "#ffe292", "#fff3be"),
    ("#98484b", "#c96058", "#e88570", "#ffad8a", "#ffd2ab"),
    ("#356669", "#4b9089", "#71b6a4", "#a7d9b9", "#def2cb"),
    ("#6e4d79", "#91709e", "#b891c2", "#dcb5db", "#f6d9e9"),
]


# Four individual quills, traced from their roots out to four separated tips.
# Each has its own stepped outline, shaft and barb. The body covers their roots.
QUILLS = [
    ([(19,29),(15,23),(13,18),(12,10),(13,6),(16,2),(18,2),(20,6),
      (20,12),(18,15),(20,14),(20,22),(22,27)],
     [(19,25),(16,17),(16,8)], [(14,11),(15,7),(17,5)], [(17,17),(19,13)]),
    ([(19,29),(14,24),(10,20),(7,15),(5,10),(6,6),(9,6),(13,9),
      (16,13),(16,16),(14,15),(17,18),(19,22),(21,27)],
     [(18,25),(13,17),(8,10)], [(7,10),(7,8),(10,9)], [(12,17),(9,16)]),
    ([(19,30),(13,27),(8,24),(4,21),(1,16),(1,13),(5,13),(9,15),
      (12,17),(12,19),(10,18),(15,21),(18,24),(21,28)],
     [(17,26),(10,21),(4,16)], [(3,15),(5,15),(8,17)], [(9,22),(5,21)]),
    ([(19,31),(12,32),(7,31),(3,29),(0,26),(0,23),(5,23),(10,24),
      (13,25),(12,27),(15,26),(20,28)],
     [(17,29),(10,28),(3,25)], [(2,24),(5,24),(8,25)], [(9,29),(6,29)]),
]
FANS = ((), (2,), (1,3), (0,2,3), (0,1,2,3))

# Row order is shared with web/yard-motion.js.
POSES = ("rest", "breathe", "look", "lean", "peck", "stride", "pass",
         "stride_back", "crouch", "wing_up", "wing_down", "land")
BOB = (0, -1, 0, 1, 2, 0, -2, 0, 3, -1, 0, 2)


class Brush:
    def __init__(self, drawing, x=0, y=0):
        self.d, self.x, self.y = drawing, x, y

    def at(self, x=0, y=0):
        return Brush(self.d, self.x+x, self.y+y)

    def points(self, points):
        return [(self.x+x, self.y+y) for x, y in points]

    def shape(self, points, fill, edge=None):
        self.d.polygon(self.points(points), fill, edge)

    def line(self, points, color, width=1):
        self.d.line(self.points(points), color, width)

    def box(self, x, y, x2, y2, color):
        self.d.rectangle((self.x+x,self.y+y,self.x+x2,self.y+y2), color)


def quills(b, colors, view):
    slots = FANS[len(colors)]
    tips = ((), ((-13,-22),), ((-13,-22),(12,-21)),
            ((-16,-19),(-4,-25),(13,-21)), ((-17,-18),(-8,-25),(5,-25),(16,-18)))
    for index,(slot,owner) in enumerate(zip(slots, colors)):
        deep, _, color, pale, _ = PLUMAGE[owner]
        if view == "side":
            outline, shaft, shine, barb = QUILLS[slot]
        else:
            dx,dy = tips[len(colors)][index]
            def blade(path):
                return [(round(24+dx*v/24-dy*u/24),round(26+dy*v/24+dx*u/24)) for u,v in path]
            outline = blade([(0,0),(-2,4),(-3,10),(-4,16),(-3,21),(-1,24),(1,24),
                             (3,21),(4,17),(3,14),(1,12),(3,13),(2,8),(1,4)])
            shaft = blade([(0,3),(0,13),(0,21)])
            shine = blade([(-2,15),(-2,19),(-1,22)])
            barb = blade([(1,10),(2,13)])
        b.shape(outline, color, INK)
        b.line(shaft, deep)
        b.line(shine, pale, 2)
        b.line(barb, deep)


def feet(b, view, pose):
    stepping = {5: ((-4,0),(4,-2)), 6: ((0,-2),(-1,0)), 7: ((4,-2),(-4,0)),
                9: ((-3,-3),(1,-4)), 10: ((-2,-4),(3,-2))}
    offsets = stepping.get(pose, ((0,0),(0,0)))
    for i, (dx,dy) in enumerate(offsets):
        x = (19,29)[i]
        end = x + (dx if view == "side" else 0)
        y = 40 + dy + (1 if i else 0)
        if view != "side" and pose in (5,7):
            y += 2 if (pose == 5) == bool(i) else -2
        toe = 4 if view == "side" else (2 if i else -2)
        b.line([(x,34),(end,y),(end+toe,y+1)], INK, 3)
        b.line([(x,35),(end,y),(end+toe,y)], "#eba65c", 2)
        b.line([(end,y),(end-2,y+1)], "#a16c46")


def wing(b, palette, pose):
    dark, shade, base, light, glint = palette
    if pose == 9:
        b.shape([(15,27),(12,23),(9,14),(9,8),(11,7),(15,15),(14,9),
                 (16,8),(20,16),(20,12),(22,12),(25,20),(25,25),(21,29)], light, INK)
        b.line([(11,11),(15,20),(18,23)], shade, 2)
        b.line([(17,13),(20,20)], shade)
        b.line([(12,11),(14,15)], glint)
    elif pose == 10:
        b.shape([(14,24),(20,23),(24,26),(24,30),(19,34),(16,40),(14,40),
                 (14,35),(11,39),(9,38),(11,32),(8,34),(7,32),(11,26)], light, INK)
        b.line([(12,32),(16,28),(18,27)], shade, 2)
        b.line([(15,35),(19,29)], shade)
    else:
        b.shape([(12,25),(15,22),(20,21),(24,22),(27,25),(26,28),(22,30),
                 (19,32),(16,31),(14,32),(12,30)], shade, dark)
        b.line([(14,25),(16,23),(20,23),(23,24)], light, 2)
        b.line([(15,28),(17,29),(20,27),(21,28),(24,26)], base)
        b.box(15,24,16,24,glint)


def side_head(b, palette, pose):
    dark, shade, base, light, glint = palette
    if pose in (3,4):
        # The neck folds under the breast and the beak turns toward the soil.
        b = b.at(1 if pose == 3 else 2, 4 if pose == 3 else 10)
        b.shape([(29,18),(28,13),(29,10),(31,11),(31,8),(33,8),(35,12),
                 (36,10),(38,11),(38,15),(36,18)], "#c95a4d", INK)
        b.shape([(28,16),(33,14),(37,16),(40,19),(40,23),(38,26),(34,26),
                 (30,24),(26,23)], light, dark)
        b.shape([(38,23),(42,24),(41,27),(40,29),(38,28),(37,25)], "#e9a350", INK)
        b.box(36,21,37,23,INK)
        b.box(36,21,36,21,glint)
        b.box(32,23,34,23,"#dd9774")
        return
    b = b.at(1 if pose == 2 else 0, -2 if pose == 2 else (1 if pose in (5,7) else 0))
    b.shape([(25,15),(25,10),(27,7),(29,8),(30,4),(32,3),(34,5),(34,9),
             (36,6),(38,7),(38,10),(40,10),(40,13),(37,16)], "#c84e48", INK)
    b.line([(30,8),(31,5),(32,5)], "#ff9a76", 2)
    b.box(36,8,37,8,"#ed7e63")
    b.shape([(22,22),(25,18),(26,14),(29,11),(35,11),(39,13),(40,17),(39,21),
             (36,23),(34,25),(32,24),(29,27),(28,24),(25,25)], light, dark)
    b.line([(27,17),(29,14),(33,13),(35,13)], glint, 2)
    b.box(35,15,37,18,INK)
    b.box(35,15,35,15,"#fffae3")
    b.box(33,19,35,20,"#e79977")
    b.shape([(39,16),(42,16),(45,18),(45,19),(40,21),(38,20)], "#eba44c", INK)
    b.line([(40,17),(43,18)], "#ffe38d")
    b.shape([(37,21),(39,21),(40,23),(39,26),(37,26),(36,24)], "#be514d", INK)
    b.box(37,22,38,22,"#f38b6c")


def side(b, body, colors, pose):
    dark, shade, base, light, glint = palette = PLUMAGE[body]
    quills(b.at(0, -1 if pose == 4 else 0), colors, "side")
    b.shape([(10,24),(12,21),(17,20),(21,20),(26,17),(32,17),(37,20),
             (40,24),(40,29),(37,34),(33,37),(27,39),(20,39),(15,37),(11,34),
             (8,30),(7,25),(8,24)], dark, INK)
    b.shape([(9,25),(13,23),(18,21),(25,21),(30,18),(35,20),(38,23),
             (39,27),(37,31),(33,35),(27,37),(21,37),(16,35),(12,32)], base)
    b.shape([(11,29),(16,33),(20,34),(25,36),(30,35),(35,32),(38,28),
             (37,32),(33,35),(28,38),(20,37),(15,35),(12,33)], shade)
    b.line([(27,30),(29,31),(31,29)], light)
    b.box(33,27,34,27,glint)
    side_head(b,palette,pose)
    wing(b,palette,pose)


def round_view(b, body, colors, pose, view):
    dark, shade, base, light, glint = PLUMAGE[body]
    front = view == "front"
    if front:
        quills(b,colors,view)
    outline = [(8,26),(10,21),(15,18),(19,16),(28,16),(34,18),(38,21),
               (40,26),(39,31),(36,35),(31,38),(18,39),(13,37),(10,34),(8,30)]
    b.shape(outline, dark, INK)
    b.shape([(10,25),(13,21),(18,19),(22,17),(28,17),(34,20),(38,24),
             (38,29),(35,33),(29,36),(20,37),(15,35),(11,31)], base)
    for left in (True,False):
        path = [(7,26),(9,22),(12,21),(14,23),(14,28),(12,32),(9,33),(7,30)]
        if pose == 9:
            path = [(3,17),(2,10),(4,10),(7,16),(8,13),(12,16),(15,23),(13,28),(9,26)]
        elif pose == 10:
            path = [(4,29),(8,24),(12,23),(14,26),(12,32),(7,36),(7,33),(3,34)]
        if not left:
            path = [(48-x,y) for x,y in path]
        b.shape(path, light if pose in (9,10) else shade, dark)
    h = b.at(1 if pose == 2 else 0, {2:-2,3:3,4:9}.get(pose,0))
    h.shape([(17,21),(16,17),(18,13),(21,10),(28,10),(31,13),(33,17),
             (32,21),(29,24),(27,24),(24,26),(21,24),(19,24)], light if front else base, dark)
    h.line([(18,16),(20,13),(23,12)], glint, 2)
    h.shape([(20,13),(19,10),(20,6),(22,7),(23,4),(25,3),(27,5),(27,9),
             (29,7),(30,9),(29,13),(26,15),(23,14)], "#c8584c", INK)
    h.line([(23,9),(24,5),(25,5)], "#fa9875", 2)
    if front:
        h.box(19,17,20,19,INK)
        h.box(28,17,29,19,INK)
        h.box(19,17,19,17,glint)
        h.box(28,17,28,17,glint)
        h.shape([(22,20),(25,19),(27,20),(25,23),(24,24)], "#f3b453", INK)
        h.line([(23,24),(23,26),(25,26)], "#b9574d", 2)
        h.box(17,20,19,20,"#de9777")
        h.box(29,20,31,20,"#de9777")
        b.line([(20,31),(22,32),(24,30)], light)
        b.line([(26,32),(28,33),(30,31)], shade)
    else:
        h.line([(20,18),(23,20),(25,18),(28,19)], shade)
        b.line([(17,30),(21,33),(24,31),(28,32),(32,29)], shade, 2)
        quills(b.at(0,3),colors,view)


def chicken(body, feathers, pose=0, view="side"):
    image = Image.new("RGBA",(48,48))
    brush = Brush(ImageDraw.Draw(image))
    feet(brush,view,pose)
    brush = brush.at(0,BOB[pose])
    if view == "side":
        side(brush,body,feathers,pose)
    else:
        round_view(brush,body,feathers,pose,view)
    return image


def paint_birds(assets):
    portraits = Image.new("RGBA",(16*48,4*48))
    for view in ("side","front","back"):
        sheet = Image.new("RGBA",(16*48,4*len(POSES)*48))
        for body in range(4):
            for mask in range(16):
                colors = [owner for owner in range(4) if mask & (1 << owner)]
                for pose in range(len(POSES)):
                    frame = chicken(body, colors, pose, view)
                    sheet.paste(frame,(mask*48,(body*len(POSES)+pose)*48))
                    if view == "side" and pose == 0:
                        portraits.paste(frame,(mask*48,body*48))
        sheet.save(assets / f"hens-{view}.png", optimize=True)
    portraits.save(assets / "chickens.png", optimize=True)
    chicken(0,[0]).save(assets / "chicken-icon.png", optimize=True)
    feathers = Image.new("RGBA",(16*4,16))
    for owner,(dark,_,color,pale,_) in enumerate(PLUMAGE):
        b = Brush(ImageDraw.Draw(feathers),owner*16)
        b.shape([(1,14),(2,11),(4,9),(4,6),(7,3),(12,1),(14,1),(14,5),
                 (12,8),(10,8),(10,10),(7,12),(4,12),(2,15)], color, INK)
        b.line([(2,13),(6,9),(9,6),(12,4)],dark)
        b.line([(5,7),(7,4),(11,3)],pale)
    feathers.save(assets / "flying-quills.png")


