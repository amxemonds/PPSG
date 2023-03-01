
import bpy
import sys
import os

import numpy as NP
import random
import math

dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)

import config
from config import *


###
###     ORIENTATION MORPH
###

class orientationMorph:

    def __init__(self,alden):

        self.alden = alden

    def potentialMorph(self):

        self.alden.lowPotentialEnergy = int(not self.alden.lowPotentialEnergy)
        self.alden.rotation = []
        return 

    # def precariousnessMorph(self):
    #     # this rotates in exactly the same fashion as changeFinalRotation() in MatchStick.java
    #     # putting it here gives me more convenient control
    #     # must disable ChangeRotationVolatileRate in MatchStick.java for this to function properly

    #     foundSuitableMorph = False

    #     while not foundSuitableMorph:
    #         rotX = random.random()*60-30                        # random value between -30.0 and 30.0 degrees
    #         rotY = random.random()*60-30                        # random value between -30.0 and 30.0 degrees
    #         rotZ = random.random()*60-30                        # random value between -30.0 and 30.0 degrees

    #         sumDegrees = abs(rotX)+abs(rotY)+abs(rotZ)

    #         if sumDegrees >= 30.0 and sumDegrees <= 60.0:
    #             self.alden.makePrecarious[0] += rotX*math.pi/180
    #             self.alden.makePrecarious[1] += rotY*math.pi/180
    #             self.alden.makePrecarious[2] += rotZ*math.pi/180
    #             foundSuitableMorph = True
    #             self.alden.rotation = []

    #     return

    def precariousnessMorph(self):
        # this rotates in exactly the same fashion as changeFinalRotation() in MatchStick.java
        # putting it here gives me more convenient control
        # must disable ChangeRotationVolatileRate in MatchStick.java for this to function properly

        foundSuitableMorph = False

        # spherical coordinates
        comVector = self.alden.comVector
        r = math.sqrt(comVector[0]**2+comVector[1]**2+comVector[2]**2)
        theta = math.acos(comVector[2]/r)
        phi = math.atan(comVector[1]/comVector[0])
        precariousIncreaseORDecrease = random.sample([-1,1],1)[0]

        while not foundSuitableMorph:
            rotX = random.random()*60-30                        # random value between -30.0 and 30.0 degrees
            rotY = random.random()*60-30                        # random value between -30.0 and 30.0 degrees
            rotZ = random.random()*60-30                        # random value between -30.0 and 30.0 degrees

            sumDegrees = abs(rotX)+abs(rotY)+abs(rotZ)

            if sumDegrees >= 30.0 and sumDegrees <= 60.0:
                # do transformation on comVector and ensure that theta is increasing or decreasing as desired
                # rotation in makePrecariousMesh function (physics.py) is rot x, rot y, rot z

                # rot x
                rotX = rotX*math.pi/180
                comVectorMorphX = [comVector[0],comVector[1]*math.cos(rotX)-comVector[2]*math.sin(rotX),comVector[1]*math.sin(rotX)+comVector[2]*math.cos(rotX)]

                # rot y
                rotY = rotY*math.pi/180
                comVectorMorphXY = [comVectorMorphX[0]*math.cos(rotY)+comVectorMorphX[2]*math.sin(rotY),comVectorMorphX[1],-comVectorMorphX[0]*math.sin(rotY)+comVectorMorphX[2]*math.cos(rotY)]

                # rot z
                rotZ = rotZ*math.pi/180
                comVectorMorphXYZ = [comVectorMorphXY[0]*math.cos(rotZ)-comVectorMorphXY[1]*math.sin(rotZ),comVectorMorphXY[0]*math.sin(rotZ)+comVectorMorphXY[1]*math.cos(rotZ),comVectorMorphXY[2]]

                rMorph = math.sqrt(comVectorMorphXYZ[0]**2+comVectorMorphXYZ[1]**2+comVectorMorphXYZ[2]**2)
                thetaMorph = math.acos(comVectorMorphXYZ[2]/rMorph)

                if (thetaMorph-theta)*precariousIncreaseORDecrease > 0:
                    self.alden.makePrecarious[0] += rotX
                    self.alden.makePrecarious[1] += rotY
                    self.alden.makePrecarious[2] += rotZ
                    foundSuitableMorph = True
                    self.alden.rotation = []

        return

    def implantationMorph(self):

        foundSuitableMorph = False

        while not foundSuitableMorph:
            implantation = random.sample(burialDepth[1:],1)[0]

            if self.alden.implantation == implantation:
                continue

            self.alden.implantation = implantation
            foundSuitableMorph = True

        return

    def scaleShiftInDepth(self):

        foundSuitableMorph = False

        while not foundSuitableMorph:
            exponent = random.randint(0,3)

            if self.alden.scaleShiftInDepth == exponent:
                continue

            self.alden.scaleShiftInDepth = exponent
            foundSuitableMorph = True

        return
