
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
###     OPTICAL PROPERTY MORPH
###

class opticalPropertyMorph:

    def __init__(self,alden):

        self.alden = alden
        self.alden.optical = 1
        self.highLowProbability = [0.0,0.20,0.60,1.0]           # {0.0,0.20,0.60,1.0} {20%,40%,40%} {random medium value,lowest value,highest value}

    def alterIOR(self):

        maxIOR = 2.3
        minIOR = 1.3

        newIOR = self.__alterOptics(maxIOR,minIOR,self.alden.opticalIOR)
        self.alden.opticalIOR = newIOR
        return

    def alterAttenuation(self):

        maxAttenuation = 0.0
        minAttenuation = -5.0

        newAttenuation = self.__alterOptics(maxAttenuation,minAttenuation,self.alden.opticalAttenuation)
        self.alden.opticalAttenuation = newAttenuation
        return

    def alterTranslucency(self):

        maxTranslucency = 1.0
        minTranslucency = 0.0

        newTranslucency = self.__alterOptics(maxTranslucency,minTranslucency,self.alden.opticalTranslucency)
        self.alden.opticalTranslucency = newTranslucency
        return

    def alterTransparency(self):

        maxTransparency = 1.0
        minTransparency = 0.0

        newTransparency = self.__alterOptics(maxTransparency,minTransparency,self.alden.opticalTransparency)
        self.alden.opticalTransparency = newTransparency
        return

    def alterRoughness(self):

        maxRoughness = 1.0
        minRoughness = 0.0

        newRoughness = self.__alterOptics(maxRoughness,minRoughness,self.alden.opticalRoughness)
        self.alden.opticalRoughness = newRoughness
        return

    def alterReflectivity(self):

        maxReflectivity = 1.0
        minReflectivity = 0.0

        newReflectivity = self.__alterOptics(maxReflectivity,minReflectivity,self.alden.opticalReflectivity)
        self.alden.opticalReflectivity = newReflectivity
        return
    
    def __alterOptics(self,maxValue,minValue,whichValue):

        foundSuitableMorph = False

        while not foundSuitableMorph:
            valueChoice = random.random()

            if valueChoice < self.highLowProbability[1]:                            # random value between lowest and highest possible
                randomValue = random.random()*(maxValue-minValue)+minValue

                if randomValue == whichValue:
                    continue

                newValue = randomValue
                foundSuitableMorph = True

            elif valueChoice < self.highLowProbability[2]:                          # lowest possible value
                if minValue == whichValue:
                    continue

                newValue = minValue
                foundSuitableMorph = True

            elif valueChoice < self.highLowProbability[3]:                          # highest possible value
                if maxValue == whichValue:
                    continue

                newValue = maxValue
                foundSuitableMorph = True

        return newValue

    def alterBLColor(self):

        foundSuitableMorph = False

        while not foundSuitableMorph:
            randomBLColor = [random.random(),random.random(),random.random()]

            if randomBLColor == self.alden.opticalBeerLambertColor:
                continue

            self.alden.opticalBeerLambertColor = randomBLColor
            foundSuitableMorph = True

        return

    def opticsTransition(self):

        self.alden.optical = 1
        restore = random.randint(0,1)

        if restore:
            # just restore previously held optical properties

            return

        else:
            # random new optical properties
            
            self.alterIOR()
            self.alterReflectivity()
            self.alterRoughness()
            self.alterBLColor()
            self.alterTransparency()

        return
