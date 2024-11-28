#!/usr/bin/env python
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, time, random, csv, datetime
import ImportObject
import PIL.Image as Image
import jeep, cone, deadtree , trafficlight

# List to hold all dead trees
all_deadtrees = []
treeamount = 100

# Animation variables
animation_textures = []  # To store loaded textures
animation_frame = 0  # Current frame to be displayed
animation_active = False  # Is animation currently active?
animation_start_time = 0  # When the animation started
collision_position = (0, 0)  # Position of the collision
animation_duration = 0.5  # Total duration of animation (in seconds)
trafficlightObj = trafficlight.TrafficLight(0,15,30)

windowSize = 600
helpWindow = False
helpWin = 0
mainWin = 0
centered = True

beginTime = 0
countTime = 0
score = 0
finalScore = 0
canStart = False
overReason = ""

#for wheel spinning
tickTime = 0

#creating objects
objectArray = []
jeep1Obj = jeep.jeep('p')
jeep2Obj = jeep.jeep('g')
jeep3Obj = jeep.jeep('r')
deadtreeObj = deadtree.DeadTree(10,0,-100)

allJeeps = [jeep1Obj, jeep2Obj, jeep3Obj]
jeepNum = 0
jeepObj = allJeeps[jeepNum]
#personObj = person.person(10.0,10.0)

#concerned with camera
eyeX = 0.0
eyeY = 2.0
eyeZ = 10.0
midDown = False
topView = False
behindView = False

#concerned with panning
nowX = 0.0
nowY = 0.0

angle = 0.0
radius = 10.0
phi = 0.0

#concerned with scene development
land = 30
gameEnlarge = 10
roadTextureID2 = None

#concerned with obstacles (cones) & rewards (stars)
coneAmount = 30
starAmount = 5 #val = -10 pts
diamondAmount = 1 #val = deducts entire by 1/2
# diamondObj = diamond.diamond(random.randint(-land, land), random.randint(10.0, land*gameEnlarge))
usedDiamond = False

allcones = []
allstars = []
obstacleCoord = []
rewardCoord = []
ckSense = 5.0

#concerned with lighting#########################!!!!!!!!!!!!!!!!##########
applyLighting = True

fov = 30.0
attenuation = 1.0

light0_Position = [0.0, 1.0, 1.0, 1.0]
light0_Intensity = [0.75, 0.75, 0.75, 0.25]

light1_Position = [0.0, 0.0, 0.0, 0.0]
light1_Intensity = [0.25, 0.25, 0.25, 0.25]

matAmbient = [1.0, 1.0, 1.0, 1.0]
matDiffuse = [0.5, 0.5, 0.5, 1.0]
matSpecular = [0.5, 0.5, 0.5, 1.0]
matShininess  = 100.0

def load_animation_textures():
    global animation_textures

    texture_files = ["./img/f1.jpg", "./img/f2.jpg", "./img/f3.jpg", "./img/f4.jpg", "./img/f5.jpg", "./img/f6.jpg", "./img/f7.jpg", "./img/f8.jpg", "./img/f9.jpg"]
    for file in texture_files:
        texture_id = loadTexture(file)
        animation_textures.append(texture_id)

class AcceleratingRibbon:
    def __init__(self, x, z, width, length):
        self.x = x  # Center position of the ribbon on the X-axis
        self.z = z  # Center position of the ribbon on the Z-axis
        self.width = width
        self.length = length

    def draw(self):
        glEnable(GL_TEXTURE_2D)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
        glBindTexture(GL_TEXTURE_2D, roadTextureID2)

        glPushMatrix()
        glColor3f(1.0, 0.0, 0.0)  # Red color for the ribbon
        glBegin(GL_QUADS)
        glVertex3f(self.x - self.width / 2, 0.01, self.z - self.length / 2)  # Bottom-left corner
        glVertex3f(self.x + self.width / 2, 0.01, self.z - self.length / 2)  # Bottom-right corner
        glVertex3f(self.x + self.width / 2, 0.01, self.z + self.length / 2)  # Top-right corner
        glVertex3f(self.x - self.width / 2, 0.01, self.z + self.length / 2)  # Top-left corner
        glEnd()
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

    def is_jeep_on_ribbon(self, jeep_obj):
        # Check if the jeep's position is within the bounds of the ribbon
        return (
            self.x - self.width / 2 <= jeep_obj.posX <= self.x + self.width / 2 and
            self.z - self.length / 2 <= jeep_obj.posZ <= self.z + self.length / 2
        )

ribbon = AcceleratingRibbon(0, 50, 100, 50)

class MovingCone:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.direction = random.choice([0, 90, 180, 270])  # degrees
        self.speed = 0.05  # Speed of movement

    def update_position(self):
        # Move in the direction the cone is facing
        self.x += self.speed * math.cos(math.radians(self.direction))
        self.z += self.speed * math.sin(math.radians(self.direction))

        # Change randomly
        if random.random() < 0.05: 
            self.direction += random.choice([-90, 90])

        # Keep the cone within bounds
        self.x = max(-land, min(land, self.x))
        self.z = max(-land, min(land * gameEnlarge, self.z))
        
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        glRotatef(-90, 1, 0, 0)
        glutSolidCone(1, 2, 20, 20)  # Draw the cone
        glPopMatrix()

# Initialize moving cones
moving_cones = [MovingCone(random.randint(-land, land), random.randint(10, land * gameEnlarge)) for _ in range(coneAmount)]

def update_cones():
    for cone in moving_cones:
        cone.update_position()

def collisionCheckMovingCones():
    global moving_cones, animation_active, collision_position, animation_start_time
    cones_to_remove = []

    for cone in moving_cones:
        # Calculate  distance between jeep and cone
        distance = dist((jeepObj.posX, jeepObj.posZ), (cone.x, cone.z))
        if distance <= ckSense:  # If collision
            cones_to_remove.append(cone)
            print("Collision detected with a moving cone!")
            
            # Trigger animation
            if not animation_active:
                animation_active = True
                animation_start_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0  # Get current time in seconds
                collision_position = (cone.x, cone.z)  # Set the collision position

    # Remove all collided cones
    for cone in cones_to_remove:
        moving_cones.remove(cone)

def render_animation():
    global animation_frame, animation_active, animation_start_time
    if not animation_active:
        return  # Do nothing if animation is not active

    # Calculate the elapsed time
    current_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0
    elapsed_time = current_time - animation_start_time

    num_frames = len(animation_textures)
    frame_duration = animation_duration / num_frames
    animation_frame = int(elapsed_time / frame_duration)

    if animation_frame >= num_frames:
        # Animation is complete
        animation_active = False
        return

    glBindTexture(GL_TEXTURE_2D, animation_textures[animation_frame])

    x, z = collision_position
    size = 20.0 
    glPushMatrix()
    glTranslatef(x, 1, z) 
    glRotatef(-90, 1, 0, 0)
    glEnable(GL_TEXTURE_2D)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(-size / 2, 0, -size / 2)
    glTexCoord2f(1, 0)
    glVertex3f(size / 2, 0, -size / 2)
    glTexCoord2f(1, 1)
    glVertex3f(size / 2, 0, size / 2)
    glTexCoord2f(0, 1)
    glVertex3f(-size / 2, 0, size / 2)
    glEnd()
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()



#--------------------------------------developing scene---------------
class Scene:
    axisColor = (0.5, 0.5, 0.5, 0.5)
    axisLength = 50   # Extends to positive and negative on all axes
    landColor = (.47, .53, .6, 0.5) #Light Slate Grey
    landLength = land  # Extends to positive and negative on x and y axis
    landW = 1.0
    landH = 0.0
    cont = gameEnlarge
    
    def draw(self):
        self.drawAxis()
        self.drawLand()

    def drawAxis(self):
        glColor4f(self.axisColor[0], self.axisColor[1], self.axisColor[2], self.axisColor[3])
        glBegin(GL_LINES)
        glVertex(-self.axisLength, 0, 0)
        glVertex(self.axisLength, 0, 0)
        glVertex(0, -self.axisLength, 0)
        glVertex(0, self.axisLength, 0)
        glVertex(0, 0, -self.axisLength)
        glVertex(0, 0, self.axisLength)
        glEnd()

    def drawLand(self):
        glEnable(GL_TEXTURE_2D)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
        glBindTexture(GL_TEXTURE_2D, roadTextureID)

        glBegin(GL_POLYGON)

        glTexCoord2f(self.landH, self.landH)
        glVertex3f(self.landLength, 0, self.cont * self.landLength)

        glTexCoord2f(self.landH, self.landW)
        glVertex3f(self.landLength, 0, -self.landLength)

        glTexCoord2f(self.landW, self.landW)
        glVertex3f(-self.landLength, 0, -self.landLength)

        glTexCoord2f(self.landW, self.landH)
        glVertex3f(-self.landLength, 0, self.cont * self.landLength)
        glEnd()

        glDisable(GL_TEXTURE_2D)

#--------------------------------------populating scene----------------
def staticObjects():
    global objectArray
    objectArray.append(Scene())
    print ('append')


def display():
    global jeepObj, canStart, score, beginTime, countTime, deadtreeObj
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    if (applyLighting == True):
        glPushMatrix()
        glLoadIdentity()
        gluLookAt(0.0, 3.0, 5.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

        glLightfv(GL_LIGHT0, GL_POSITION, light0_Position)
        pointPosition = [0.0,-10.0,0.0]

        glDisable(GL_LIGHTING)

        glColor3f(light0_Intensity[0], light0_Intensity[1], light0_Intensity[2])

        glTranslatef(light0_Position[0], light0_Position[1], light0_Position[2])

        glutSolidSphere(0.025, 36, 24)

        glTranslatef(-light0_Position[0], -light0_Position[1], -light0_Position[2])
        glEnable(GL_LIGHTING)
        glMaterialfv(GL_FRONT, GL_AMBIENT, matAmbient)
        for x in range(1,4):
            for z in range(1,4):
                 matDiffuse = [float(x) * 0.3, float(x) * 0.3, float(x) * 0.3, 1.0] 
                 matSpecular = [float(z) * 0.3, float(z) * 0.3, float(z) * 0.3, 1.0]  
                 matShininess = float(z * z) * 10.0
                 ## Set the material diffuse values for the polygon front faces. 
                 glMaterialfv(GL_FRONT, GL_DIFFUSE, matDiffuse)

                 ## Set the material specular values for the polygon front faces. 
                 glMaterialfv(GL_FRONT, GL_SPECULAR, matSpecular)

                 ## Set the material shininess value for the polygon front faces. 
                 glMaterialfv(GL_FRONT, GL_SHININESS, matShininess)

                 ## Draw a glut solid sphere with inputs radius, slices, and stacks
                 glutSolidSphere(0.25, 72, 64)
                 glTranslatef(1.0, 0.0, 0.0)

            glTranslatef(-3.0, 0.0, 1.0)
        glPopMatrix()
   
    beginTime = 6-score
    countTime = score-6
    if (score <= 5):
        canStart = False
        glColor3f(1.0,0.0,1.0)
        text3d("Begins in: "+str(beginTime), jeepObj.posX, jeepObj.posY + 3.0, jeepObj.posZ)
    elif (score == 6):
        canStart = True
        glColor(1.0,0.0,1.0)
        text3d("GO!", jeepObj.posX, jeepObj.posY + 3.0, jeepObj.posZ)
    else:
        canStart = True
        glColor3f(0.0,1.0,1.0)
        text3d("Scoring: "+str(countTime), jeepObj.posX, jeepObj.posY + 3.0, jeepObj.posZ)

    for obj in objectArray:
        obj.draw()
    for cone in allcones:
        cone.draw()

    for tree in all_deadtrees:
        tree.draw()

    ribbon.draw()

    # if (usedDiamond == False):
    #     diamondObj.draw()

    update_cones()
    for cone in moving_cones:
        cone.draw()
    
    jeepObj.draw()
    jeepObj.drawW1()
    jeepObj.drawW2()
    jeepObj.drawLight()
    trafficlightObj.draw()

    deadtreeObj.draw()

    render_animation()
    #personObj.draw()
    glutSwapBuffers()

def idle():#--------------with more complex display items like turning wheel---
    global tickTime, prevTime, score, jeepObj, ribbon
    jeepObj.rotateWheel(-0.1 * tickTime)    
    # updateCamera()
    glutPostRedisplay()
    
    curTime = glutGet(GLUT_ELAPSED_TIME)
    tickTime =  curTime - prevTime
    prevTime = curTime
    score = curTime/1000

    # Check if the jeep is on the ribbon
    if ribbon.is_jeep_on_ribbon(jeepObj):
        jeepObj.speed = 2.0  # Accelerate the jeep (you can adjust the speed value)
    else:
        jeepObj.speed = 1.0  # Default speed

    # Update positions of moving cones
    update_cones()

    # Check for collisions with moving cones
    collisionCheckMovingCones()

    

#---------------------------------setting camera----------------------------
def setView():
    global eyeX, eyeY, eyeZ
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(90, 1, 0.1, 100)
    if (topView == True):
        gluLookAt(0, 10, land*gameEnlarge/2, 0, jeepObj.posY, land*gameEnlarge/2, 0, 1, 0)
    elif (behindView ==True):
        gluLookAt(jeepObj.posX, jeepObj.posY + 1.0, jeepObj.posZ - 2.0, jeepObj.posX, jeepObj.posY, jeepObj.posZ, 0, 1, 0) 
    else:
        gluLookAt(eyeX, eyeY, eyeZ, 0, 0, 0, 0, 1, 0)
    glMatrixMode(GL_MODELVIEW)
    
    glutPostRedisplay()   

# camera_distance = 10.0
# camera_angle = 0.0
# camera_height = 2.0
# zoom_speed = 0.5
# angle_speed = 0.0001

# def updateCamera():
#     global eyeX, eyeY, eyeZ, camera_angle, camera_distance
#     # Calculate camera position based on angle and distance
#     eyeX = jeepObj.posX + camera_distance * math.sin(camera_angle)
#     eyeY = jeepObj.posY + camera_height
#     eyeZ = jeepObj.posZ + camera_distance * math.cos(camera_angle) 
tryme = 10

def setObjView():
    # things to do
    # realize a view following the jeep
    # refer to setview
    global eyeX, eyeY, eyeZ ,tryme
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(90, 1, 0.1, 100)
    # Set camera to follow the jeep
    gluLookAt(eyeX + jeepObj.posX, eyeY + jeepObj.posY + 5, eyeZ + jeepObj.posZ - tryme,jeepObj.posX, jeepObj.posY, jeepObj.posZ, 0, 1, 0)
    glMatrixMode(GL_MODELVIEW)
    glutPostRedisplay()

#-------------------------------------------user inputs------------------
def mouseHandle(button, state, x, y):
    global midDown
    if (button == GLUT_MIDDLE_BUTTON and state == GLUT_DOWN):
        midDown = True
        print ('pushed')
    else:
        midDown = False    

def motionHandle(x,y):
    # global camera_angle, camera_distance
    # if midDown:
    #     # Adjust camera angle and distance based on mouse movement
    #     dx = x - windowSize / 2
    #     dy = y - windowSize / 2
    #     camera_angle += dx * angle_speed
    #     camera_distance -= dy * zoom_speed
    #     camera_distance = max(5.0, min(20.0, camera_distance))  # Limit zoom
    #     updateCamera()
    #     setObjView()
    global nowX, nowY, angle, eyeX, eyeY, eyeZ, phi
    if (midDown == True):
        pastX = nowX
        pastY = nowY 
        nowX = x
        nowY = y
        if (nowX - pastX > 0):
            angle -= 0.025
        elif (nowX - pastX < 0):
            angle += 0.025
        elif (nowY - pastY > 0): #look into looking over and under object...
            phi += 0.025
        elif (nowX - pastY <0):
            phi -= 0.025
        eyeX = radius * math.sin(angle) 
        eyeZ = radius * math.cos(angle)
        eyeY = radius * math.sin(phi)
    if centered == False:
        setView()
    elif centered == True:
        setObjView()
    #print eyeX, eyeY, eyeZ, nowX, nowY, radius, angle
    #print "getting handled"



def specialKeys(keypress, mX, mY):
    # things to do
    # this is the function to move the car
    global jeepObj ,tryme
    move_speed = jeepObj.speed  # Use the jeep's current speed

    if keypress == GLUT_KEY_UP or keypress == b'w':  # Forward
        jeepObj.posZ += move_speed
        jeepObj.wheelDir = 'fwd'
    elif keypress == GLUT_KEY_DOWN or keypress == b's':  # Backward
        jeepObj.posZ -= move_speed
        jeepObj.wheelDir = 'back'
    elif keypress == GLUT_KEY_LEFT or keypress == b'a':  # Left
        jeepObj.posX += move_speed
        jeepObj.wheelDir = 'fwd'
        # jeepObj.angle += 5  # Adjust angle for left turn
    elif keypress == GLUT_KEY_RIGHT or keypress == b'd':  # Right
        jeepObj.posX -= move_speed
        jeepObj.wheelDir = 'fwd'
        # jeepObj.angle -= 5  # Adjust angle for right turn
    elif keypress == b'q':  # zoom-in
        tryme -= 0.5  
    elif keypress == b'e':  # zoom-out
        tryme += 0.5

    collisionCheck()  # Check for collisions after moving
    setObjView()  # Update the camera view
    glutPostRedisplay()

def myKeyboard(key, mX, mY):
    global eyeX, eyeY, eyeZ, angle, radius, helpWindow, centered, helpWin, overReason, topView, behindView
    if key == b"h":
        print ("h pushed"+ str(helpWindow))
        winNum = glutGetWindow()
        if helpWindow == False:
            helpWindow = True
            glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
            glutInitWindowSize(500,300)
            glutInitWindowPosition(600,0)
            helpWin = glutCreateWindow(b'Help Guide')
            glutDisplayFunc(showHelp)
            glutKeyboardFunc(myKeyboard)
            glutMainLoop()
        elif helpWindow == True and winNum!=1:
            helpWindow = False
            print (glutGetWindow())
            glutHideWindow()
            #glutDestroyWindow(helpWin)
            glutMainLoop()
    elif key in [b'w', b'a', b's', b'd', b'q' , b'e']:
        specialKeys(key, mX, mY)  # Call specialKeys for WASD
    # things can do
    # this is the part to set special functions, such as help window.

#-------------------------------------------------tools----------------------       
def drawTextBitmap(string, x, y): #for writing text to display
    glRasterPos2f(x, y)
    for char in string:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

def text3d(string, x, y, z):
    glRasterPos3f(x,y,z)
    for char in string:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

def dist(pt1, pt2):
    a = pt1[0]
    b = pt1[1]
    x = pt2[0]
    y = pt2[1]
    return math.sqrt((a-x)**2 + (b-y)**2)

def noReshape(newX, newY): #used to ensure program works correctly when resized
    glutReshapeWindow(windowSize,windowSize)

aspect_ratio = 1.0  # Global variable for the aspect ratio

def reshape(width, height):
    global aspect_ratio
    if height == 0:  # Prevent division by zero
        height = 1
    aspect_ratio = width / height  # Update the aspect ratio

    glViewport(0, 0, width, height)  # Set the viewport to match the new window size
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    # Maintain the same field of view and adjust the aspect ratio
    gluPerspective(60, aspect_ratio, 0.1, 100.0)  # 60-degree FOV, dynamic aspect ratio
    glMatrixMode(GL_MODELVIEW)

#--------------------------------------------making game more complex--------
def addCone(x,z):
    allcones.append(cone.cone(x,z))
    obstacleCoord.append((x,z))

def addDeadTree(x,y,z):
    all_deadtrees.append(deadtree.DeadTree(x,y,z))

def collisionCheck():
    global overReason, score, usedDiamond, countTime
    for obstacle in obstacleCoord:
        if dist((jeepObj.posX, jeepObj.posZ), obstacle) <= ckSense:
            overReason = "You hit an obstacle!"
            gameOver()
    if (jeepObj.posX >= land or jeepObj.posX <= -land):
        overReason = "You ran off the road!"
        gameOver()

    # if (dist((jeepObj.posX, jeepObj.posZ), (diamondObj.posX, diamondObj.posZ)) <= ckSense and usedDiamond ==False):
    #     print ("Diamond bonus!")
    #     countTime /= 2
    #     usedDiamond = True
    if (jeepObj.posZ >= land*gameEnlarge):
        gameSuccess()
        
#----------------------------------multiplayer dev (using tracker)-----------
def recordGame():
    with open('results.csv', 'wt') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        print(st)
        spamwriter.writerow([st] + [finalScore])
    
#-------------------------------------developing additional windows/options----
def gameOver():
    global finalScore
    print ("Game completed!")
    finalScore = score-6
    #recordGame() #add to excel
    glutHideWindow()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutInitWindowSize(200,200)
    glutInitWindowPosition(600,100)
    overWin = glutCreateWindow("Game Over!")
    glutDisplayFunc(overScreen)
    glutMainLoop()
    
def gameSuccess():
    global finalScore
    print ("Game success!")
    finalScore = score-6
    #recordGame() #add to excel
    glutHideWindow()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutInitWindowSize(200,200)
    glutInitWindowPosition(600,100)
    overWin = glutCreateWindow("Complete!")
    glutDisplayFunc(winScreen)
    glutMainLoop()

def winScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glColor3f(0.0,1.0,0.0)
    drawTextBitmap("Completed Trial!" , -0.6, 0.85)
    glColor3f(0.0,1.0,0.0)
    drawTextBitmap("Your score is: ", -1.0, 0.0)
    glColor3f(1.0,1.0,1.0)
    drawTextBitmap(str(finalScore), -1.0, -0.15)
    glutSwapBuffers()


def overScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glColor3f(1.0,0.0,1.0)
    drawTextBitmap("Incomplete Trial" , -0.6, 0.85)
    glColor3f(0.0,1.0,0.0)
    drawTextBitmap("Because you..." , -1.0, 0.5)
    glColor3f(1.0,1.0,1.0)
    drawTextBitmap(overReason, -1.0, 0.35)
    glColor3f(0.0,1.0,0.0)
    drawTextBitmap("Your score stopped at: ", -1.0, 0.0)
    glColor3f(1.0,1.0,1.0)
    drawTextBitmap(str(finalScore), -1.0, -0.15)
    glutSwapBuffers()

def showHelp():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glColor3f(1.0,0.0,0.0)
    drawTextBitmap("Help Guide" , -0.2, 0.85)
    glColor3f(0.0,0.0,1.0)
    drawTextBitmap("describe your control strategy." , -1.0, 0.7)
    glutSwapBuffers()

#----------------------------------------------texture development-----------
def loadTexture(imageName):
    texturedImage = Image.open(imageName)
    try:
        imgX = texturedImage.size[0]
        imgY = texturedImage.size[1]
        img = texturedImage.tobytes("raw","RGBX",0,-1)#tostring("raw", "RGBX", 0, -1)
    except Exception:
        print ("Error:")
        print ("Switching to RGBA mode.")
        imgX = texturedImage.size[0]
        imgY = texturedImage.size[1]
        img = texturedImage.tobytes("raw","RGB",0,-1)#tostring("raw", "RGBA", 0, -1)

    tempID = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tempID)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(GL_TEXTURE_2D, 0, 3, imgX, imgY, 0, GL_RGBA, GL_UNSIGNED_BYTE, img)
    return tempID

def loadSceneTextures():
    global roadTextureID , roadTextureID2
    roadTextureID = loadTexture("./img/road2.png")
    roadTextureID2 = loadTexture("./img/old.png")
    
#-----------------------------------------------lighting work--------------

def set_ambient_light():

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glDisable(GL_LIGHT1)
    glDisable(GL_LIGHT2)
    glDisable(GL_LIGHT3)

    ambient_light = [0.3, 0.2, 0.2, 1.0]  
    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient_light)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.7, 0.7, 0.7, 1.0])  
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])  

    print("Ambient light enabled.")

def set_point_light():

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT1)
    glDisable(GL_LIGHT0)
    glDisable(GL_LIGHT2)
    glDisable(GL_LIGHT3)

    point_light_position = [0.0, 10.0, 0.0, 1.0]  
    point_light_diffuse = [1.0, 1.0, 1.0, 1.0]  
    point_light_specular = [0.5, 0.5, 0.5, 1.0]  

    glLightfv(GL_LIGHT1, GL_POSITION, point_light_position)
    glLightfv(GL_LIGHT1, GL_DIFFUSE, point_light_diffuse)
    glLightfv(GL_LIGHT1, GL_SPECULAR, point_light_specular)

    print("Point light enabled.")

def set_directional_light():

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT2)
    glDisable(GL_LIGHT1)
    glDisable(GL_LIGHT0)
    glDisable(GL_LIGHT3)

    directional_light_direction = [0.0, 50.0, -1.0, 0.0]  
    directional_light_diffuse = [1.0, 1.0, 1.0, 1.0]  
    directional_light_specular = [0.5, 0.5, 0.5, 1.0]  

    glLightfv(GL_LIGHT2, GL_POSITION, directional_light_direction)
    glLightfv(GL_LIGHT2, GL_DIFFUSE, directional_light_diffuse)
    glLightfv(GL_LIGHT2, GL_SPECULAR, directional_light_specular)

    print("Directional light enabled.")

def set_spot_light():

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT3)
    glDisable(GL_LIGHT1)
    glDisable(GL_LIGHT2)
    glDisable(GL_LIGHT0)

    spot_light_position = [0.0, 10.0, 0.0, 1.0]  
    spot_light_direction = [0.0, -1.0, 0.0]  
    spot_light_diffuse = [1.0, 1.0, 1.0, 1.0]  
    spot_light_specular = [0.8, 0.8, 0.8, 1.0]  

    glLightfv(GL_LIGHT3, GL_POSITION, spot_light_position)
    glLightfv(GL_LIGHT3, GL_DIFFUSE, spot_light_diffuse)
    glLightfv(GL_LIGHT3, GL_SPECULAR, spot_light_specular)
    glLightfv(GL_LIGHT3, GL_SPOT_DIRECTION, spot_light_direction)
    glLightf(GL_LIGHT3, GL_SPOT_CUTOFF, 45.0)  
    glLightf(GL_LIGHT3, GL_SPOT_EXPONENT, 1.0)  

    print("Spotlight enabled.")

def set_resolution(width, height):
    glutReshapeWindow(width, height)

is_full = False

def toggle_fullscreen():
    global is_full
    if is_full:
        glutReshapeWindow(windowSize, windowSize)
        is_full = False
    else:
        glutFullScreen()
        is_full = True
        
#menu
def lightmenu(value):
    if value == 1:
        set_ambient_light()
    elif value == 2:
        set_point_light()
    elif value == 3:
        set_directional_light()
    elif value == 4:
        set_spot_light()
    elif value == 5:
        set_resolution(800, 600)
    elif value == 6:
        set_resolution(1024, 768)
    elif value == 7:
        set_resolution(1280, 720)
    elif value == 8:
        toggle_fullscreen()
    glutPostRedisplay()
    return 0

def initializeLight():
    glEnable(GL_LIGHTING)                
    glEnable(GL_LIGHT0)                 
    glEnable(GL_DEPTH_TEST)              
    glEnable(GL_NORMALIZE)               
    glClearColor(0.1, 0.1, 0.1, 0.0)
#~~~~~~~~~~~~~~~~~~~~~~~~~the finale!!!~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    glutInit()

    global prevTime, mainWin
    prevTime = glutGet(GLUT_ELAPSED_TIME)
    
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    # things to do
    # change the window resolution in the game
    glutInitWindowSize(windowSize, windowSize)
    
    glutInitWindowPosition(0, 0)
    mainWin = glutCreateWindow(b'CS4182')
    glutDisplayFunc(display)
    glutIdleFunc(idle)#wheel turn

    setView()
    glLoadIdentity()
    glEnable(GL_DEPTH_TEST)   

    glutMouseFunc(mouseHandle)
    glutMotionFunc(motionHandle)
    glutSpecialFunc(specialKeys)
    glutKeyboardFunc(myKeyboard)
    glutReshapeFunc(reshape)
    # things to do
    # add a menu 
    glutCreateMenu(lightmenu)
    glutAddMenuEntry("Ambient Light", 1)
    glutAddMenuEntry("Point Lights", 2)
    glutAddMenuEntry("Directional Lights", 3)
    glutAddMenuEntry("Spotlights", 4)
    glutAddMenuEntry("800x600", 5)
    glutAddMenuEntry("1024x768", 6)
    glutAddMenuEntry("1280x720", 7)
    glutAddMenuEntry("fullscreen on/off", 8)
    glutAttachMenu(GLUT_RIGHT_BUTTON)

    loadSceneTextures()

    load_animation_textures()

    jeep1Obj.makeDisplayLists()
    jeep2Obj.makeDisplayLists()
    jeep3Obj.makeDisplayLists()
    deadtreeObj.makeDisplayLists()
    trafficlightObj.makeDisplayLists()
    #personObj.makeDisplayLists()

    # things to do
    # add a automatic object
    for i in range(coneAmount):#create cones randomly for obstacles, making sure to give a little lag time in beginning by adding 10.0 buffer
        addCone(random.randint(-land, land), random.randint(10.0, land*gameEnlarge))

    for i in range(treeamount):#create cones randomly for obstacles, making sure to give a little lag time in beginning by adding 10.0 buffer
        addDeadTree(random.choice([i for i in range(-land - 20, land + 20) if i not in range(-land, land)]), 0, random.randint(-land, 500))
    #random.choice([i for i in range(-200, 200) if i not in range(10, land * gameEnlarge)])
    # things to do
    # add stars

    for cone in allcones:
        cone.makeDisplayLists()

    for tree in all_deadtrees:
        tree.makeDisplayLists()


    
    # diamondObj.makeDisplayLists()
    
    staticObjects()
    if (applyLighting == True):
        initializeLight()
    glutMainLoop()


#hi
    
main()