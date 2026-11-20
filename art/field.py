"""Native-resolution farm map, carved tiles and timber UI borders."""
import math
import random
from PIL import Image, ImageDraw
from yard import coop, daisies, garden, grass_tuft, stamp


def orchard(d, x, y):
    def shape(points, color, edge=None):
        d.polygon([(x+a,y+b) for a,b in points], color, edge)
    def line(points,color,width=1):
        d.line([(x+a,y+b) for a,b in points], color, width)
    d.ellipse((x+14,y+44,x+60,y+59),fill="#6e864f")
    shape([(32,56),(35,48),(34,39),(26,33),(27,29),(37,35),(42,29),
           (45,30),(41,38),(41,49),(46,54),(41,54),(37,52),(35,56)],"#986c46","#584c3d")
    line([(37,50),(38,41),(36,38)],"#c6945a",2)
    shape([(0,26),(3,20),(6,18),(6,13),(12,8),(18,8),(21,3),(27,1),(33,2),
           (38,0),(47,1),(52,5),(58,5),(64,11),(65,15),(70,19),(71,26),
           (67,30),(65,35),(57,38),(51,38),(45,42),(37,41),(30,44),(23,42),
           (20,39),(12,39),(7,36),(7,33),(3,32)],"#43654d","#3c5947")
    clusters = [(6,15,20,15),(16,6,22,18),(32,2,22,18),(47,9,19,18),
                (10,23,22,15),(27,19,25,18),(44,23,20,14),(21,13,23,16)]
    for i,(a,b,w,h) in enumerate(clusters):
        shape([(a,b+6),(a+4,b+3),(a+7,b+3),(a+9,b),(a+w-5,b),
               (a+w,b+4),(a+w,b+h-5),(a+w-4,b+h-3),(a+w-8,b+h-3),
               (a+w-11,b+h),(a+5,b+h-1),(a+2,b+h-4),(a,b+h-5)],
              ["#63864e","#76954e","#92a954","#6b8e50"][i%4])
        line([(a+2,b+7),(a+5,b+5),(a+8,b+5),(a+10,b+3),(a+13,b+3)],
             "#b0bd67" if i%3 != 0 else "#92a85b",2)
    for a,b in [(9,22),(17,14),(32,25),(49,17),(52,32),(24,34)]:
        shape([(a-2,b),(a,b-2),(a+2,b-1),(a+3,b+1),(a+2,b+3),
               (a-1,b+3),(a-2,b+2)],"#cf704a","#875140")
        line([(a-1,b),(a,b-1)],"#f6be72")


def rail(d, start, end, y):
    for level in (4,10):
        d.rectangle((start,y+level,end,y+level+3), fill="#795b41")
        d.line((start,y+level,end,y+level),"#d0a367")
        d.line((start,y+level+1,end,y+level+1),"#aa7d50")
    for i,x in enumerate(range(start+6,end,25)):
        lift = (0,1,-1,0)[i%4]
        a = y+lift
        d.polygon([(x,a+1),(x+2,a-2),(x+5,a),(x+5,a+15),(x,a+15)],"#b28656","#675641")
        d.line((x+1,a+2,x+1,a+13),"#e2ba79")
        d.point((x+3,a+5),"#5d5141")
        d.point((x+3,a+11),"#5d5141")
        d.line((x+6,a+15,x+9,a+15),"#839451")


def placed(image, paint, size, x, y, scale=1):
    piece = Image.new("RGBA",size)
    paint(ImageDraw.Draw(piece))
    if scale != 1:
        piece = piece.resize(tuple(round(n*scale) for n in size),Image.Resampling.NEAREST)
    image.paste(piece,(x,y),piece)


def straw(d,x,y):
    pts = [(x,y+3),(x+5,y),(x+18,y),(x+22,y+3),(x+22,y+10),
           (x+17,y+13),(x+1,y+11)]
    d.polygon(pts,"#ca9c54","#7f6945")
    d.line([(x+2,y+3),(x+16,y+4),(x+21,y+2)],"#f0cc78",2)
    d.line([(x+7,y+2),(x+7,y+11)],"#997541",2)
    d.line([(x+15,y+2),(x+15,y+11)],"#997541",2)
    for a,b in [(3,6),(9,7),(17,6),(4,9),(11,10)]:
        d.line((x+a,y+b,x+a+2,y+b-1),"#e4b965")


def worn_path(im, mask):
    w,h = im.size
    # Soft corners are drawn on the same pixel grid as the dirt and the egg shells.
    knots = [(.17,.17),(.32,.145),(.51,.15),(.69,.15),(.84,.18),(.93,.30),
             (.94,.50),(.93,.69),(.83,.84),(.68,.88),(.49,.875),(.31,.88),
             (.17,.84),(.07,.71),(.06,.50),(.07,.30)]
    knots = [(x*w,y*h) for x,y in knots]
    path = []
    for i,(x,y) in enumerate(knots):
        px,py = knots[i-1]
        nx,ny = knots[(i+1)%len(knots)]
        for j in range(12):
            t = j/12
            path.append((round((1-t)**2*(px+x)/2 + 2*t*(1-t)*x + t*t*(x+nx)/2),
                         round((1-t)**2*(py+y)/2 + 2*t*(1-t)*y + t*t*(y+ny)/2)))
    track = im.copy()
    p = ImageDraw.Draw(track)
    for width,color in [(17,"#dbb980"),(13,"#d7b37b"),(8,"#d4b079")]:
        p.line(path+[path[0]],fill=color,width=width,joint="curve")
    im.paste(track,mask=mask)


def grain_scoop(d,x,y):
    # A weathered wooden grain scoop and the handful of corn it has spilled.
    d.ellipse((x-9,y+3,x+10,y+6),"#cba976")
    d.polygon([(x-10,y-1),(x-6,y-5),(x,y-5),(x+4,y-2),(x+4,y+2),
               (x,y+5),(x-5,y+5),(x-9,y+2)],"#bb9563","#9b7b56")
    d.polygon([(x-8,y-1),(x-5,y-3),(x,y-3),(x+2,y-1),(x,y+1),
               (x-4,y+2),(x-7,y+1)],"#997e55")
    d.line([(x-7,y+2),(x-4,y+3),(x,y+2)],"#dfbd82")
    d.line([(x+2,y),(x+7,y-3),(x+11,y-7)],"#9a7855",3)
    d.line([(x+4,y-2),(x+9,y-6)],"#d1ac72")
    for a,b in [(-9,6),(-5,8),(-1,6),(3,8),(-8,10),(-14,9),(-3,12)]:
        d.line((x+a,y+b,x+a+1,y+b),"#b38f56")
        d.point((x+a,y+b-1),"#efd098")


def fieldstones(d,x,y):
    for dx,dy,s in [(-8,1,5),(1,-2,8),(8,3,4)]:
        a,b = x+dx,y+dy
        d.polygon([(a,b),(a+2,b-3),(a+s-2,b-4),(a+s,b-2),(a+s+1,b),
                   (a+s-1,b+2),(a+1,b+2)],"#9e9c7b","#8c896d")
        d.line([(a+1,b-1),(a+3,b-3),(a+s-2,b-3)],"#c4bd95")
        d.line((a+2,b+3,a+s+2,b+3),"#c6a778")
    grass_tuft(d,x+11,y-1,"#909559","#bdba76")


def terrain(width,height,portrait=False):
    rng = random.Random(119 if portrait else 61)
    im = Image.new("RGB",(width,height),"#98aa65")
    d = ImageDraw.Draw(im)
    # Hand-traced, asymmetric edge of a well-trodden clearing.
    verge = [(0,.34),(.03,.29),(.035,.22),(.08,.19),(.10,.13),(.17,.12),(.20,.075),
             (.27,.075),(.31,.048),(.43,.062),(.5,.045),(.59,.065),(.68,.05),(.75,.074),
             (.8,.09),(.84,.15),(.88,.17),(.9,.22),(.95,.25),(.96,.32),(1,.37),
             (1,.70),(.965,.75),(.95,.80),(.90,.83),(.86,.88),(.8,.90),(.77,.945),
             (.7,.94),(.64,.962),(.55,.945),(.49,.97),(.4,.95),(.32,.965),(.27,.935),
             (.21,.94),(.17,.90),(.12,.89),(.10,.84),(.055,.81),(.047,.75),(0,.71)]
    pts = []
    for i,(a,b) in enumerate(verge):
        x1,y1 = round(a*width), round(b*height)
        c,e = verge[(i+1)%len(verge)]
        n = max(1,round(math.hypot((c-a)*width,(e-b)*height)/4))
        for j in range(n):
            t = j/n
            pts.append((round(x1+(c-a)*width*t)+rng.choice([-1,0,0,1]),
                        round(y1+(e-b)*height*t)+rng.choice([-1,0,0,1])))
    for i in range(width*height//125):
        x,y = rng.randrange(width),rng.randrange(height)
        d.line((x,y,x+rng.randrange(2,6),y),rng.choice(["#9fae6a","#889c60","#aaba71"]))
        if i%5 == 0:
            grass_tuft(d,x,y,"#80965b","#bec77b")
    d.polygon(pts,fill="#c49c65")
    d.line(pts+[pts[0]],fill="#b6a86a",width=3)
    inner = [(round((x-width/2)*.981+width/2),round((y-height/2)*.976+height/2)) for x,y in pts]
    d.polygon(inner,fill="#dfbe84")
    mask = Image.new("1",im.size)
    ImageDraw.Draw(mask).polygon(inner,fill=1)
    worn_path(im,mask)
    for _ in range(width*height//65):
        x,y = rng.randrange(width),rng.randrange(height)
        if not mask.getpixel((x,y)):
            continue
        ink = rng.choice(["#d7b47a","#d7b47a","#e5c78f","#dab980"])
        n = rng.choice([1,2,3,5])
        d.line((x,y,x+n,y),ink)
        if n == 5:
            d.line((x+1,y-1,x+3,y-1),ink)
    for a,b in [(.19,.33),(.23,.68),(.79,.66),(.73,.32),(.12,.56),(.56,.76),(.42,.23)]:
        x,y = round(a*width), round(b*height)
        d.line((x,y,x+6,y),"#cba775")
        d.line((x+4,y-2,x+12,y-2),"#e9cd97")
        d.point((x-3,y+1),"#bc986b")
    rail(d,0,width,0)
    placed(im,coop,(96,57),-3,-4,.72 if portrait else .89)
    straw(d,round(width*.14)-8,9 if portrait else 4)
    orchard(d,width-(46 if portrait else 59),-16)
    placed(im,daisies,(66,33),-2,height-30,.84 if portrait else 1)
    placed(im,garden,(80,39),width-(62 if portrait else 80),height-(31 if portrait else 38),.82 if portrait else 1)
    if portrait:
        # Keep both narrow strips beside the tiles clear on a small screen.
        fieldstones(d,int(width*.165),int(height*.64))
    else:
        grain_scoop(d,int(width*.204),int(height*.60))
        fieldstones(d,int(width*.806),int(height*.425))
    for a,b in [(.22,.98),(.81,.95),(.96,.16),(.02,.77),(.17,.062),(.68,.047)]:
        grass_tuft(d,int(a*width),int(b*height),"#718a54","#c0c677")
    return im


def frame_tile():
    # The central 16 pixels repeat on the long sides of a nine-sliced wooden frame.
    im = Image.new("RGBA",(32,32),"#a77547")
    d = ImageDraw.Draw(im)
    for inset,color in [(0,"#342f2b"),(1,"#624834"),(2,"#d3a267"),(3,"#bd8c56"),
                        (4,"#a67447"),(5,"#ae7c4c"),(6,"#7a573a"),(7,"#503e30")]:
        d.rectangle((inset,inset,31-inset,31-inset),outline=color)
    for x in (9,14,23):
        d.line((x,4,x+2,4),"#96673e")
        d.line((x-2,27,x,27),"#cb955c")
    for x,y,dx,dy in [(0,0,1,1),(31,0,-1,1),(0,31,1,-1),(31,31,-1,-1)]:
        d.line((x+dx,y+dy,x+7*dx,y+7*dy),"#765338")
        d.point((x+4*dx,y+4*dy),"#463f37")
        d.point((x+3*dx,y+3*dy),"#eed09a")
    return im


def egg_tile(kind):
    im = Image.new("RGBA",(34,38))
    d = ImageDraw.Draw(im)
    silhouette = [(13,1),(21,1),(21,2),(24,2),(24,4),(26,4),(26,6),(28,6),
                  (28,9),(30,9),(30,13),(32,16),(32,24),(31,24),(31,28),
                  (29,28),(29,30),(26,33),(22,35),(12,35),(8,33),(5,30),
                  (3,27),(2,24),(2,17),(4,12),(6,8),(9,5),(9,4),(13,2)]
    d.polygon([(x,y+2) for x,y in silhouette],"#a88b61")
    border,fill,shadow,shine = {
        "plain":("#927a58","#f8e9c1","#dcc499","#fff2cf"),
        "target":("#894c31","#f7c45d","#d69a48","#fff0a4"),
        "home":("#957e59","#d9bf8e","#c1a77d","#e9d4a5")}[kind]
    d.polygon(silhouette,fill,border)
    d.line([(5,24),(7,28),(11,31),(15,33),(21,33),(26,31),(29,27)],shadow,2)
    d.line([(5,17),(7,12),(10,8),(14,5),(17,4)],shine,2)
    for x,y in [(8,21),(10,29),(24,7),(26,25)]:
        d.point((x,y),shadow)
    return im


def card_tile(front=False):
    im = Image.new("RGBA",(40,42))
    d = ImageDraw.Draw(im)
    edge = [(6,0),(33,0),(39,6),(39,34),(34,40),(6,40),(0,35),(0,6)]
    d.polygon([(x,y+1) for x,y in edge],"#67563e")
    d.polygon(edge,"#bc965e" if front else "#435a43","#4d4935" if front else "#36483b")
    face = [(6,2),(33,2),(37,6),(37,32),(33,37),(6,37),(2,33),(2,6)]
    d.polygon(face,"#f0d8a9" if front else "#52786a")
    d.line(face[:3],"#fce6b9" if front else "#9cae84")
    d.line([(2,32),(6,36),(33,36),(36,33)],"#c5a274" if front else "#39594e")
    inner = [(7,5),(32,5),(34,7),(34,30),(31,33),(8,33),(5,30),(5,8),(7,5)]
    d.line(inner,"#d0b181" if front else "#899980")
    for x,y in [(8,8),(31,8),(8,30),(31,30)]:
        d.point((x,y),"#aa895f" if front else "#bfbc8f")
    if not front:
        # Each back carries a little two-colour woodcut of a feather.
        d.polygon([(12,22),(14,19),(15,14),(19,10),(25,8),(28,8),(27,12),
                   (25,15),(23,15),(23,17),(19,20),(16,20),(13,23)],"#e4cf96","#334f46")
        d.line([(13,22),(17,18),(21,15),(25,11)],"#8c9169")
        d.line([(16,15),(19,12),(24,10)],"#f6e0a6")
        d.line([(10,23),(11,23)],"#94a381")
        d.line([(28,19),(30,19)],"#94a381")
    return im


def wind():
    im = Image.new("RGBA",(24*4,16))
    for i,lean in enumerate([0,1,2,1]):
        tile = Image.new("RGBA",(24,16))
        d = ImageDraw.Draw(tile)
        for x,y,h in [(2,14,4),(5,14,8),(8,13,5),(14,14,10),(18,15,5),(21,14,7)]:
            d.line([(x,y),(x,y-3),(x+lean-2,y-h)],"#618251",2)
            d.point((x+lean-2,y-h),"#b9bf75")
        for x,y in [(5+lean-2,5),(14+lean-2,3)]:
            d.line((x-1,y,x+1,y),"#f2d896",2)
            d.point((x,y),"#bd8b4c")
        im.paste(tile,(i*24,0))
    return im


def dust():
    im = Image.new("RGBA",(30*5,14))
    for i in range(5):
        tile = Image.new("RGBA",(30,14))
        d = ImageDraw.Draw(tile)
        for x,dx,dy in [(10,-2,-1),(13,-1,-2),(19,2,-1),(21,2,-2),(15,0,-2)]:
            xx,yy = x+dx*i,11+dy*i
            size = (1,3,3,2,1)[i]
            d.rectangle((xx,yy,xx+size,yy+size-1),"#b68e62")
            d.line((xx,yy-1,xx+size-1,yy-1),"#f2d7a3")
        im.paste(tile,(30*i,0))
    return im


def tool_icons():
    # One-colour woodcut marks, laid out left to right as four columns.
    strokes = [
        [[(1,3),(5,3),(8,5),(11,3),(15,3),(15,12),(11,12),(8,14),(5,12),(1,12),(1,3)],[(8,5),(8,13)]],
        [[(1,6),(4,6),(8,2),(8,14),(4,10),(1,10),(1,6)],[(11,5),(12,6),(12,10),(11,11)],[(13,2),(15,5),(15,11),(13,14)]],
        [[(1,6),(4,6),(8,2),(8,14),(4,10),(1,10),(1,6)],[(11,6),(15,10)],[(15,6),(11,10)]],
        [[(1,6),(1,1),(6,1)],[(10,1),(15,1),(15,6)],[(15,10),(15,15),(10,15)],[(6,15),(1,15),(1,10)]],
        [[(1,6),(6,6),(6,1)],[(10,1),(10,6),(15,6)],[(15,10),(10,10),(10,15)],[(6,15),(6,10),(1,10)]],
        [[(7,2),(7,13)],[(2,7),(13,7)]],
        [[(3,3),(12,12)],[(12,3),(3,12)]],
        [[(13,5),(10,2),(6,2),(3,4),(2,7),(2,10),(4,13),(9,14),(13,11)],[(14,1),(14,6),(9,6)]],
        [[(5,2),(8,2),(10,4),(10,6),(8,8),(5,8),(3,6),(3,4),(5,2)],
         [(1,14),(2,11),(5,10),(8,10),(11,11),(12,14)],[(12,3),(14,4),(14,6),(12,8)],[(13,10),(15,12),(15,14)]],
        [[(4,2),(12,2),(12,6),(11,9),(9,11),(7,11),(5,9),(4,6),(4,2)],
         [(3,3),(1,3),(1,6),(4,8)],[(13,3),(15,3),(15,6),(12,8)],[(8,11),(8,14)],[(4,15),(12,15)]],
        [[(4,8),(4,2),(6,1),(7,2),(7,7),(8,5),(10,5),(10,7),(11,6),(13,6),(14,8),(14,11),
          (12,14),(8,15),(5,14),(1,10),(1,8),(3,8),(5,10)]],
        [[(1,8),(6,12),(14,3)]],
        [[(7,1),(9,1),(15,13),(15,14),(1,14),(1,13),(7,1)],[(8,5),(8,9)],[(8,11),(8,12)]],
    ]
    sheet = Image.new("RGBA",(64,64))
    for i,paths in enumerate(strokes):
        d = ImageDraw.Draw(sheet)
        for path in paths:
            d.line([(i%4*16+x,i//4*16+y) for x,y in path],"white",2 if i in (3,4,5,6,11) else 1)
    return sheet


def paint_field(assets):
    terrain(448,272).save(assets/"farm.png",optimize=True)
    terrain(288,300,True).save(assets/"farm-tall.png",optimize=True)
    yard = Image.new("RGB",(48,48),"#c8d4a0")
    d = ImageDraw.Draw(yard)
    d.polygon([(0,15),(6,10),(9,11),(15,6),(21,9),(26,8),(33,11),(38,7),
               (43,9),(48,8),(48,27),(0,27)],"#9fb17a")
    d.rectangle((0,22,48,48),"#acb977")
    d.polygon([(0,41),(6,37),(14,37),(19,33),(30,35),(36,32),(48,31),(48,48),(0,48)],"#d6b681")
    rail(d,-3,49,16)
    grass_tuft(d,3,38,"#7e945e","#c0c67e")
    d.line((32,43,41,43),"#c3a573")
    yard.save(assets/"roost.png")
    frame_tile().save(assets/"timber.png")
    for kind in ("plain","target","home"):
        egg_tile(kind).save(assets/f"egg-{kind}.png")
    card_tile().save(assets/"tile-back.png")
    card_tile(True).save(assets/"tile-face.png")
    wind().save(assets/"wind.png")
    dust().save(assets/"dust.png")
    tool_icons().save(assets/"tool-icons.png")
    fabric = Image.new("RGB",(48,48),"#293e36")
    d = ImageDraw.Draw(fabric)
    for x,y in [(2,9),(18,30),(34,7),(41,25),(8,43),(27,17)]:
        d.line((x,y,x+3,y-2),"#2d4239")
        d.point((x-1,y+2),"#263b33")
    fabric.save(assets/"cloth.png")
    paper = Image.new("RGBA",(48,48))
    d = ImageDraw.Draw(paper)
    for x,y in [(4,12),(26,37),(41,18),(17,23),(38,46)]:
        d.line((x,y,x+2,y),(130,95,52,20))
    paper.save(assets/"paper.png")
    mark = Image.new("RGBA",(16,16))
    stamp(ImageDraw.Draw(mark))
    mark.save(assets/"quill-stamp.png")
