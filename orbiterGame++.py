#! /usr/bin/env python3.7
import os
import math
import random
import pygame as pg
from time import sleep
     
currentPath = os.path.dirname(__file__)

##Setup color table
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 255, 0)
ltBlue = (173, 216, 230)

class Satellite(pg.sprite.Sprite):
    """Satellite object that rotates to face planet & crashes & burns."""
    
    def __init__(self, background):
        super().__init__()
        self.background = background
        currentPath = os.path.dirname(__file__)
        self.imageSat = pg.image.load(os.path.join(currentPath, "satellite.png")).convert()
        self.imageCrash = pg.image.load(os.path.join(currentPath, "satellite_crash.png")).convert()
        self.image = self.imageSat
        self.rect = self.image.get_rect()
        self.image.set_colorkey(black)  # sets transparent color
        self.x = random.randrange(315, 425)
        self.y = random.randrange(70, 180) 
        self.dx = random.choice([-3, 3])
        self.dy = 0
        self.heading = 0  # initializes dish orientation
        self.fuel = 100
        self.mass = 1
        self.distance = 0  # initializes distance between satellite & planet
        self.thrust = pg.mixer.Sound(os.path.join(currentPath,'thrust_audio.ogg'))
        self.thrust.set_volume(0.07)  # valid values are 0-1

    def thruster(self, dx, dy):
        """Execute actions associated with firing thrusters."""
        self.dx += dx
        self.dy += dy
        self.fuel -= 2
        self.thrust.play()     

    def checkKeys(self):
        """Check if user presses arrow keys & call thruster() method."""
        keys = pg.key.get_pressed()       
        # fire thrusters
        if keys[pg.K_RIGHT]:
            self.thruster(dx=0.05, dy=0)
        elif keys[pg.K_LEFT]:
            self.thruster(dx=-0.05, dy=0)
        elif keys[pg.K_UP]:
            self.thruster(dx=0, dy=-0.05)  
        elif keys[pg.K_DOWN]:
            self.thruster(dx=0, dy=0.05)
            
    def locate(self, planet):
        """Calculate distance & heading to planet."""
        px, py = planet.x, planet.y
        distx = self.x - px
        disty = self.y - py
        # get direction to planet to point dish
        planetDirRadians = math.atan2(distx, disty)
        self.heading = planetDirRadians * 180 / math.pi
        self.heading -= 90  # sprite is traveling tail-first       
        self.distance = math.hypot(distx, disty)

    def rotate(self):
        """Rotate satellite using degrees so dish faces planet."""
        self.image = pg.transform.rotate(self.imageSat, self.heading)
        self.rect = self.image.get_rect()

    def path(self):
        """Update satellite's position & draw line to trace orbital path."""
        lastCenter = (self.x, self.y)
        self.x += self.dx
        self.y += self.dy
        pg.draw.line(self.background, white, lastCenter, (self.x, self.y))

    def update(self):
        """Update satellite object during game."""
        self.checkKeys()
        self.rotate()
        self.path()
        self.rect.center = (self.x, self.y)        
        # change image to fiery red if in atmosphere
        if self.dx == 0 and self.dy == 0:
            self.image = self.imageCrash
            self.image.set_colorkey(black)
            
class Planet(pg.sprite.Sprite):
    """Planet object that rotates & projects gravity field."""
    
    def __init__(self):
        super().__init__()
        currentPath = os.path.dirname(__file__)
        self.imageMars = pg.image.load(os.path.join(currentPath,"mars.png")).convert()
        self.imageWater = pg.image.load(os.path.join(currentPath,"mars_water.png")).convert() 
        self.imageCopy = pg.transform.scale(self.imageMars, (100, 100)) 
        self.imageCopy.set_colorkey(black) 
        self.rect = self.imageCopy.get_rect()
        self.image = self.imageCopy
        self.mass = 2000 
        self.x = 400 
        self.y = 320
        self.rect.center = (self.x, self.y)
        self.angle = math.degrees(0)
        self.rotateBy = math.degrees(0.01)

    def rotate(self):
        """Rotate the planet image with each game loop."""
        lastCenter = self.rect.center
        self.image = pg.transform.rotate(self.imageCopy, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = lastCenter
        self.angle += self.rotateBy

    def gravity(self, satellite):
        """Calculate impact of gravity on the satellite."""
        G = 1.0  # gravitational constant for game
        distx = self.x - satellite.x
        disty = self.y - satellite.y
        distance = math.hypot(distx, disty)     
        # normalize to a unit vector
        distx /= distance
        disty /= distance
        # apply gravity
        force = G * (satellite.mass * self.mass) / (math.pow(distance, 2))
        satellite.dx += (distx * force)
        satellite.dy += (disty * force)
        
    def update(self):
        """Call the rotate method."""
        self.rotate()

def calcEccentricity(distList):
    """Calculate & return eccentricity from list of radii."""
    apoapsis = max(distList)
    periapsis = min(distList)
    eccentricity = (apoapsis - periapsis) / (apoapsis + periapsis)
    return eccentricity

def instructLabel(screen, text, color, x, y):
    """Take screen, list of strings, color, & origin & render text to screen."""
    instructFont = pg.font.SysFont(None, 25)
    lineSpacing = 22
    for index, line in enumerate(text):
        label = instructFont.render(line, True, color, black)
        screen.blit(label, (x, y + index * lineSpacing))

def boxLabel(screen, text, dimensions):
    """Make fixed-size label from screen, text & left, top, width, height."""
    readoutFont = pg.font.SysFont(None, 27)
    base = pg.Rect(dimensions)
    pg.draw.rect(screen, white, base, 0)
    label = readoutFont.render(text, True, black)
    labelRect = label.get_rect(center=base.center)
    screen.blit(label, labelRect)

def mappingOn(planet):
    """Show soil moisture image on Mars."""
    lastCenter = planet.rect.center
    planet.imageCopy = pg.transform.scale(planet.imageWater, (100, 100))
    planet.imageCopy.set_colorkey(black)
    planet.rect = planet.imageCopy.get_rect()
    planet.rect.center = lastCenter

def mappingOff(planet):
    """Restore normal planet image."""
    planet.imageCopy = pg.transform.scale(planet.imageMars, (100, 100))
    planet.imageCopy.set_colorkey(black)

def castShadow(screen):
    """Add optional terminator & shadow behind planet to screen."""
    shadow = pg.Surface((400, 100), flags=pg.SRCALPHA)  # tuple is w,h
    shadow.fill((0, 0, 0, 210))  # last number sets transparency
    screen.blit(shadow, (0, 270))  # tuple is top left coordinates

def main():
    """Set-up labels & instructions, create objects & run the game loop."""
    pg.init()  # initialize pygame
    
    # set-up display
    os.environ['SDL_VIDEO_WINDOW_POS'] = '700, 100'  # set game window origin
    screen = pg.display.set_mode((800, 645), pg.FULLSCREEN) 
    pg.display.set_caption("Mars Orbiter")
    background = pg.Surface(screen.get_size())
    
    # enable sound mixer
    pg.mixer.init()

    introText = [
        ' The BNP Orbiter experienced an error during Orbit insertion.',
        ' Use thrusters to correct to a circular mapping orbit without',
        ' running out of propellant or burning up in the atmosphere.'
        ]
 
    instructText1 = [
        'Orbital altitude must be within 69-120 miles',
        'Orbital Eccentricity must be < 0.1',
        'Avoid top of atmosphere at 68 miles'    
        ]

    instructText2 = [
        'Left Arrow = Decrease Dx', 
        'Right Arrow = Increase Dx', 
        'Up Arrow = Decrease Dy', 
        'Down Arrow = Increase Dy', 
        'Space Bar = Clear Path',
        'Escape = Exit Full Screen'        
        ]  

    # instantiate planet and satellite objects
    planet = Planet()
    planetSprite = pg.sprite.Group(planet)
    sat = Satellite(background)    
    satSprite = pg.sprite.Group(sat)

    # for circular orbit verification
    distList = []  
    eccentricity = 1
    eccentricityCalcInterval = 5  # optimized for 120 mile altitude
    
    # time-keeping
    clock = pg.time.Clock()
    fps = 30
    tickCount = 0

    # for soil moisture mapping functionality
    mappingEnabled = False
    running = True
    while running:
        clock.tick(fps)
        tickCount += 1
        distList.append(sat.distance)

        # get keyboard input
        for event in pg.event.get():
            if event.type == pg.QUIT:  # close window
                running = False
            elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                screen = pg.display.set_mode((800, 645))  # exit full screen
            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                background.fill(black)  # clear path
            elif event.type == pg.KEYUP:
                sat.thrust.stop()  # stop sound
                mappingOff(planet)  # turn-off moisture map view
            elif mappingEnabled:
                if event.type == pg.KEYDOWN and event.key == pg.K_m:
                    mappingOn(planet)

        # get heading & distance to planet & apply gravity               
        sat.locate(planet)  
        planet.gravity(sat)

        # calculate orbital eccentricity
        if tickCount % (eccentricityCalcInterval * fps) == 0:
            eccentricity = calcEccentricity(distList)
            distList = []              
        
        ##Loading Screen
        if pg.time.get_ticks() <= 7000:  # time in milliseconds
            loadScrn = pg.image.load(os.path.join(currentPath,"loadingScrn.png")).convert() 
            screen.blit(loadScrn, (0,0))

        # re-blit background for drawing command - prevents clearing path
        screen.blit(background, (0, 0))

        # Fuel/Altitude fail conditions
        if sat.fuel <= 0:
            instructLabel(screen, ['Fuel Depleted!'], red, 340, 195)
            sat.fuel = 0
            sat.dx = 2
        elif sat.distance <= 68:
            instructLabel(screen, ['Atmospheric Entry!'], red, 320, 195)
            sat.dx = 0
            sat.dy = 0

        # enable mapping functionality
        if eccentricity < 0.1 and sat.distance >= 69 and sat.distance <= 120:
            mapInstruct = ['Press & hold M to map soil moisture']
            instructLabel(screen, mapInstruct, ltBlue, 250, 175)
            mappingEnabled = True
        else:
            mappingEnabled = False

        planetSprite.update()
        planetSprite.draw(screen)
        satSprite.update()
        satSprite.draw(screen)

        # display intro text for 15 seconds      
        if pg.time.get_ticks() <= 15000:  # time in milliseconds
            instructLabel(screen, introText, green, 145, 100)

        # display telemetry and instructions
        boxLabel(screen, 'Dx', (70, 20, 75, 20))
        boxLabel(screen, 'Dy', (150, 20, 80, 20))
        boxLabel(screen, 'Altitude', (240, 20, 160, 20))
        boxLabel(screen, 'Fuel', (410, 20, 160, 20))
        boxLabel(screen, 'Eccentricity', (580, 20, 150, 20))
        
        boxLabel(screen, '{:.1f}'.format(sat.dx), (70, 50, 75, 20))     
        boxLabel(screen, '{:.1f}'.format(sat.dy), (150, 50, 80, 20))
        boxLabel(screen, '{:.1f}'.format(sat.distance), (240, 50, 160, 20))
        boxLabel(screen, '{}'.format(sat.fuel), (410, 50, 160, 20))
        boxLabel(screen, '{:.8f}'.format(eccentricity), (580, 50, 150, 20))
          
        instructLabel(screen, instructText1, white, 10, 575)
        instructLabel(screen, instructText2, white, 570, 510)
      
        # add terminator & border
        castShadow(screen)
        pg.draw.rect(screen, white, (1, 1, 798, 643), 1)

        pg.display.flip()

if __name__ == "__main__":
    main()