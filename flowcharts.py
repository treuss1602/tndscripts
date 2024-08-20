#!/usr/bin/python
from PIL import Image, ImageDraw, ImageFont, ImageOps

COLOR_CFS=(238,235,242)
COLOR_COMPONENT=(255,242,204)
COLOR_FP=(219,238,244)
COLOR_GREY=(217,217,217)
COLOR_BLACK=(0,0,0)
COLOR_PONR=(255,0,0)
COLOR_TRANSPARENT=(0,0,0,0)

SCALE = 20
S1 = SCALE
S2 = 2*SCALE
S3 = 3*SCALE

FONT_LARGE = ImageFont.truetype("arial.ttf", 14)
FONT_SMALL = ImageFont.truetype("arial.ttf", 11)
FONT_HUGE = ImageFont.truetype("arial.ttf", 24)
FONT_PONR = ImageFont.truetype("bauhaus.ttf", 32)
FONT_COLOR_GREY=(128,128,128)

class Element:

    def __init__(self, pt, width, height):
        self._pt = pt
        self.width = width
        self.height = height

    def x(self):
        return self._pt[0]

    def y(self):
        return self._pt[1]

    def setXPos(self, x):
        self._pt = (x, self.y())

    def setYPos(self, y):
        self._pt = (self.x(), y)

class Container(Element):

    def __init__(self, pt, width, height, title, color):
        super().__init__(pt, width, height)
        self.title = title
        self.color = color
        self.embedded = []

    def draw(self, img):
        self.reposition()
        d = ImageDraw.Draw(img)
        d.rectangle([self._pt, (self.x()+self.width,self.y()+S2)], fill=COLOR_GREY, outline=COLOR_BLACK)
        d.rectangle([(self.x(), self.y()+S2), (self.x()+self.width, self.y()+self.height)], fill=self.color, outline=COLOR_BLACK)
        d.text([(self.x()+self.width//2), self.y()+S1], self.title, font=FONT_LARGE, anchor="mm", fill=COLOR_BLACK)
        for e in self.embedded:
            e.draw(img)

    def embed(self, element):
        self.embedded.append(element)
        element.pt = (self.x()+self.width, self.y()+S3)
        self.width += element.width+S1

    def reposition(self):
        if self.embedded:
            self.width = S1
            last = None
            for e in self.embedded:
                if isinstance(e, Task) and isinstance (last, Task):
                    # Vertical positioning
                    e.setXPos(last.x())
                    if e.phase is last.phase:
                        e.setYPos(last.y()+last.height+S1)
                    else:
                        e.reposition()
                else:
                    e.setXPos(self.x()+self.width)
                    if isinstance(self, CFS) and isinstance(e, FactoryProduct):
                        e.setYPos(self.y()+S3+S3) # FP alignments inside and outside of compoments
                        e.height = self.height - 8*SCALE
                    else:
                        e.setYPos(self.y()+S3)
                        if not isinstance(e, Task):
                            e.height = self.height - 4*SCALE
                    e.reposition()
                    self.width += e.width+S1
                last = e

class Task(Element):

    def __init__(self, text, phase):
        super().__init__((0,0), 9*SCALE, 2*SCALE)
        self.text = text
        self.phase = phase

    def draw(self, img):
        if self.text == "PONR":
            ponr = Image.new("RGBA", (SCALE*5, self.height), COLOR_TRANSPARENT)
            d = ImageDraw.Draw(ponr)
            d.rounded_rectangle([(0,0), (SCALE*5, self.height)], 10, None, COLOR_PONR, 7)
            d.text([SCALE*5//2, self.height//2], self.text, font=FONT_PONR, anchor="mm", align="center", fill=COLOR_PONR)
            rotated = ponr.rotate(-15, expand=1)
            img.paste(rotated, (self.x()+2*SCALE, self.y()-(rotated.height-self.height)//2), mask=rotated)
        else:
            d = ImageDraw.Draw(img)
            d.rectangle([self._pt, (self.x()+self.width,self.y()+self.height)], fill=COLOR_GREY, outline=COLOR_BLACK)
            d.multiline_text([(self.x()+self.width//2), self.y()+self.height//2], self.text, font=FONT_SMALL, anchor="mm", align="center", fill=COLOR_BLACK)

    def reposition(self):
        self.setYPos(self.phase.y()+S1)

class CFS(Container):

    def __init__(self, title, phases):
        super().__init__((S2,0), 15*SCALE, 40*SCALE, title, COLOR_CFS)
        self.phases = phases
        ypos = self.x()+7*SCALE
        for p in phases:
            p.setYPos(ypos)
            ypos += p.height
        self.height = ypos + 3*SCALE

    def createImage(self):
        self.reposition()
        out = Image.new("RGBA", (self.width+S3+1, self.height+1), (255, 255, 255))
        self.draw(out)
        for p in self.phases:
            p.width = self.width + S3
            p.draw(out)
        return out



class Component(Container):

    def __init__(self, title, sameas=None, lowcaption=False):
        super().__init__((0,0), 13*SCALE, 36*SCALE, title, COLOR_COMPONENT)
        self.sameas = sameas
        self.textypos = 11 if lowcaption else 16

    def draw(self, img):
        super().draw(img)
        if self.sameas:
            d = ImageDraw.Draw(img)
            d.multiline_text([(self.x()+self.width//2), self.y()+self.textypos*SCALE], "Same as\n{}".format(self.sameas), font=FONT_HUGE, anchor="mm", align="center", fill=COLOR_BLACK)


class FactoryProduct(Container):

    def __init__(self, title, lowcaption=False):
        super().__init__((0,0), 11*SCALE, 32*SCALE, title, COLOR_FP)
        self.textypos = 8 if lowcaption else 13

    def draw(self, img):
        super().draw(img)
        d = ImageDraw.Draw(img)
        d.multiline_text([(self.x()+self.width//2), self.y()+self.textypos*SCALE], "Generic\nRFS Flow", font=FONT_HUGE, anchor="mm", align="center", fill=FONT_COLOR_GREY)


class Phase(Element):

    def __init__(self, title, empty=False, height=7*SCALE, width=40*SCALE):
        if empty:
            height=4*SCALE
        super().__init__((0,9*SCALE), width, height)
        self.title = title
        self.empty = empty

    def draw(self, img):
        txt = Image.new("RGBA", (self.height, S1), COLOR_GREY)
        ImageDraw.Draw(txt).text([self.height//2, S1//2], self.title, font=FONT_LARGE, anchor="mm", fill=COLOR_BLACK)
        img.paste(txt.rotate(90, expand=1), self._pt)
        d = ImageDraw.Draw(img)
        d.rectangle([self._pt, (self.x()+S1,self.y()+self.height)], fill=None, outline=COLOR_BLACK)
        d.rectangle([(self.x()+S1, self.y()), (self.x()+self.width,self.y()+self.height)], fill=None, outline=COLOR_BLACK)
        if self.empty:
            for i in range(0, self.width-self.height, 10):
                d.line([self.x()+i, self.y()+self.height, self.x()+self.height+i, self.y()], COLOR_BLACK, 1)
            for i in range(0, self.height, 10):
                d.line([self.x(), self.y()+i, self.x()+i, self.y()], COLOR_BLACK, 1)
                d.line([self.x()+self.width, self.y()+i, self.x()+self.width-self.height+i, self.y()+self.height], COLOR_BLACK, 1)

if __name__ == "__main__":

    PHASE_VALIDATE = Phase("Validate")
    PHASE_PREPARE = Phase("Prepare")
    PHASE_PROVISION = Phase("Provision")
    PHASE_FINALIZE = Phase("Finalize")

    phases = [PHASE_VALIDATE, PHASE_PREPARE, PHASE_PROVISION, PHASE_FINALIZE]

    # create an image
    cfs = CFS("CFS TN_RBH_RPD_ACCESS - Create", phases)
    cfs.embed(Task("Cramer\nCreate Context", PHASE_PREPARE))
    cfs.embed(Task("Cramer\nCreate CFS Service", PHASE_PREPARE))
    cfs.embed(Task("Order Hub\nConfirm Modelling", PHASE_PROVISION))
    cfs.embed(FactoryProduct("FP PHY_SINGLE_LINK"))
    cfs.embed(Task("Cramer\nFind Or Create IRB", PHASE_PREPARE))
    comp = Component("Component RBH_RPD")
    comp.embed(Task("Cramer\nCreate Component Service", PHASE_PREPARE))
    comp.embed(Task("Cramer\nCreate L2 VPN Name", PHASE_PREPARE))
    comp.embed(FactoryProduct("FP IPVPN_CORE"))
    comp.embed(FactoryProduct("FP IPVPN_SAP"))
    comp.embed(FactoryProduct("FP ELAN_CORE"))
    comp.embed(FactoryProduct("FP ELAN_SAP"))
    cfs.embed(comp)
    cfs.embed(Task("PONR", PHASE_PREPARE))
    cfs.embed(Task("Cramer\nApply Context", PHASE_FINALIZE))

    out = cfs.createImage()
    out.show()

