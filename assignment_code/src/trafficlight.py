from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import ImportObject


class TrafficLight:
    obj = 0
    displayList = 0
    
    posX = 0.0
    posY = 0.0
    posZ = 0.0

    sizeX = 1.0
    sizeY = 1.0
    sizeZ = 1.0

    rotation = 0.0

    def __init__(self, x, y, z):
        self.obj = ImportObject.ImportedObject("./objects/trafficlight")
        self.posX = x
        self.posY = y
        self.posZ = z

    def makeDisplayLists(self):
        self.obj.loadOBJ()

        self.displayList = glGenLists(1)
        glNewList(self.displayList, GL_COMPILE)
        self.obj.drawObject()
        glEndList()

    def draw(self):
        glPushMatrix()
        
        glTranslatef(self.posX,self.posY,self.posZ)
        glRotatef(90 ,  0, self.posY , 0)
        #glRotatef(self.rotation,0.0,1.0,0.0)
        glScalef(self.sizeX,self.sizeY,self.sizeZ)

        glCallList(self.displayList)
        glPopMatrix()