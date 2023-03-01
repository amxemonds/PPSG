
import bpy
import sys
import os

import numpy as NP
import random

dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)

import config
from config import *


class contextMorph:

    def __init__(self,env):

        self.env = env

    # def changeRelativeObjectPosition(self,alden):
        
    #     foundSuitableMorph = False

    #     while not foundSuitableMorph:
    #         randomLocation = random.randint(0,16)

    #         if randomLocation == alden.location:
    #             continue

    #         alden.location = randomLocation
    #         foundSuitableMorph = True

    #     return

    def changeRelativeObjectPosition(self,alden):

        possiblePositions = [0]

        if self.env.ceiling:
            possiblePositions.append(2)
            possiblePositions.append(4)
            possiblePositions.append(9)
            possiblePositions.append(11)

            if self.env.wallR:
                possiblePositions.append(6)
                possiblePositions.append(14)

            if self.env.wallL:
                possiblePositions.append(7)
                possiblePositions.append(15)

        if self.env.wallR:
            possiblePositions.append(1)
            possiblePositions.append(10)
            possiblePositions.append(5)
            possiblePositions.append(13)

        if self.env.wallL:
            possiblePositions.append(3)
            possiblePositions.append(8)
            possiblePositions.append(12)
            possiblePositions.append(16)

        if not sum([self.env.floor,self.env.ceiling,self.env.wallL,self.env.wallR]):

            if self.env.wallB:
                possiblePositions.append(4)
                possiblePositions.append(9)

        foundSuitableMorph = False

        while not foundSuitableMorph:
            newPosition = random.sample(possiblePositions,1)[0]

            if alden.location == newPosition:
                continue

            alden.location = newPosition
            foundSuitableMorph = True

        return

    def newStructureMaterial(self):

        foundSuitableMorph = False

        while not foundSuitableMorph:
            structureMaterial = random.sample(structureMaterialOptions,1)[0]

            if structureMaterial == self.env.structureMaterial:
                continue

            self.env.structureMaterial = structureMaterial
            foundSuitableMorph = True

        return

    def changeDistance(self):

        foundSuitableMorph = False

        while not foundSuitableMorph:
            randomDistance = random.sample(architectureDistanceOptions,1)[0]

            if self.env.distance == randomDistance:
                continue

            else:
                self.env.distance = randomDistance
                foundSuitableMorph = True

        return


###
###     CONTEXT MORPH - ARCHITECTURE
###

class contextMorph_Architecture:

    def __init__(self,env):

        self.env = env

    def changeArchitectureComposition(self):

        indexChange = random.randint(0,4)

        if indexChange == 0:                                    # switch floor
            self.env.floor = int(not self.env.floor)

        elif indexChange == 1:                                  # switch ceiling
            self.env.ceiling = int(not self.env.ceiling)

        elif indexChange == 2:                                  # switch left wall
            self.env.wallL = int(not self.env.wallL)

        elif indexChange == 3:                                  # switch right wall
            self.env.wallR = int(not self.env.wallR)

        elif indexChange == 4:                                  # new random structure
            self.env.floor = random.randint(0,1)
            self.env.ceiling = random.randint(0,1)
            self.env.wallL = random.randint(0,1)
            self.env.wallR = random.randint(0,1)

        if sum([self.env.floor,self.env.ceiling,self.env.wallL,self.env.wallR]):
            self.env.wallB = 1

        else:
            self.env.wallB = random.randint(0,1)                # switch back wall

        return 

    def changeArchitectureCompositionAlden(self,alden):

        canChange = [1,1,1,1,1]

        if alden.location in [2,6,7,11,14,15]:      # ceiling stays
            canChange[1] = 0

        if alden.location in [3,7,8,12,15,16]:      # wallL stays
            canChange[2] = 0

        if alden.location in [1,5,6,10,13,14]:      # wallR stays
            canChange[3] = 0

        if sum([self.env.floor,self.env.ceiling,self.env.wallL,self.env.wallR]):        # wallB stays
            canChange[4] = 0

        foundSuitableMorph = False

        while not foundSuitableMorph:
            indexChange = random.randint(0,4)
            
            if canChange[indexChange] == 0:
                continue

            if indexChange == 0:                                    # switch floor
                self.env.floor = int(not self.env.floor)

            elif indexChange == 1:                                  # switch ceiling
                self.env.ceiling = int(not self.env.ceiling)

            elif indexChange == 2:                                  # switch left wall
                self.env.wallL = int(not self.env.wallL)

            elif indexChange == 3:                                  # switch right wall
                self.env.wallR = int(not self.env.wallR)

            elif indexChange == 4:                                  # switch back wall
                self.env.wallB = int(not self.env.wallB)

            if sum([self.env.floor,self.env.ceiling,self.env.wallL,self.env.wallR]):
                self.env.wallB = 1

            foundSuitableMorph = True

        return

    def clingORhang(self,alden):
        
        foundSuitableMorph = False

        while not foundSuitableMorph:
            wallInteraction = random.randint(-1,1)

            if wallInteraction == alden.wallInteraction:
                continue

            alden.wallInteraction = wallInteraction
            foundSuitableMorph = True
            alden.rotation = []

        return

    def alterThickness(self):

        print('Not Implemented')
        return
        

###
###     CONTEXT MORPH - GRASSGRAVITY
###

class contextMorph_GrassGravity:

    def __init__(self,env):

        self.env = env

    def changeHorizonTilt(self):

        foundSuitableMorph = False

        while not foundSuitableMorph:
            randomTilt = random.sample(horizonTiltOptions,1)[0]

            if self.env.horizonTilt == randomTilt:
                continue

            self.env.horizonTilt = randomTilt
            foundSuitableMorph = True

        return

    def changeHorizonSlant(self):

        foundSuitableMorph = False

        while not foundSuitableMorph:
            randomSlant = random.sample(horizonSlantOptions,1)[0]

            if self.env.horizonSlant == randomSlant:
                continue

            self.env.horizonSlant = randomSlant
            foundSuitableMorph = True

        return

    def changeGravityDirection(self):

        self.env.gravity = int(not self.env.gravity)
        return 
