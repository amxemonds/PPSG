
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


###
###     SCENE DETAIL MORPH 
###

class sceneDetailMorph:

    def __init__(self,env):

        self.env = env

    def newHorizonMaterial(self):

        foundSuitableMorph = False

        while not foundSuitableMorph: 
            horizonMaterial = random.sample(horizonGrassMaterialOptions,1)[0]

            if horizonMaterial == self.env.horizonMaterial:
                continue

            self.env.horizonMaterial = horizonMaterial
            foundSuitableMorph = True

        return

    def alterTimeOfDay(self):

        foundSuitableMorph = False

        while not foundSuitableMorph:
            randomSun = random.sample(lightingOptions,1)[0]

            if randomSun == self.env.sun:
                continue

            self.env.sun = randomSun
            foundSuitableMorph = True

        return

    def alterHorizonTilt(self):

        foundSuitableMorph = False

        while not foundSuitableMorph:
            # randomTilt = random.sample(horizonTiltOptions,1)[0]
            randomTilt = (random.random()*2-1)*22.5*math.pi/180

            if randomTilt == self.env.horizonTilt:
                continue

            self.env.horizonTilt = randomTilt
            foundSuitableMorph = True

        return

    def aperturePresent(self):

        self.env.aperture = int(not self.env.aperture)
        return 

        