
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

from aldenMesh import aldenConstructor
from delete import deleteTool


###
###     MATERIAL MORPH
###

class materialMorph:

    def __init__(self,alden):

        self.alden = alden
        self.alden.optical = 0

    def newBodyBaseMaterial(self):

        foundSuitableMorph = False

        while not foundSuitableMorph:
            randomMaterial = random.sample(culledAldenMaterialOptions,1)[0]

            if randomMaterial == self.alden.material:
                continue

            self.alden.material = randomMaterial
            foundSuitableMorph = True

        return

    def separateLimb(self):

        foundSuitableMorph = False
        # howManyLimbs = random.randint(0,self.alden.comps-1)
        # separated = 0

        while not foundSuitableMorph:
            chosenLimb = random.randint(0,self.alden.comps-1)

            head = self.alden.headsTails[chosenLimb][0]
            tail = self.alden.headsTails[chosenLimb][1]
            isBuried = self.alden.implantation

            if chosenLimb in self.alden.affectedLimbs:
                continue

            if isBuried != 0.0 and head[2] < 0 and tail[2] < 0:
                continue

            self.alden.affectedLimbs.append(chosenLimb)
            self.alden.limbMaterials.append(random.sample(culledAldenMaterialOptions,1)[0])
            # separated += 1

            # if separated == howManyLimbs:
            foundSuitableMorph = True

        return

    def restoreLimb(self):

        chosenLimb = random.sample(self.alden.affectedLimbs,1)[0]
        indexChosenLimb = self.alden.affectedLimbs.index(chosenLimb)
        self.alden.affectedLimbs.pop(indexChosenLimb)
        self.alden.limbMaterials.pop(indexChosenLimb)
        return 

    def changeLimb(self):

        chosenLimb = random.sample(self.alden.affectedLimbs,1)[0]
        indexChosenLimb = self.alden.affectedLimbs.index(chosenLimb)
        foundSuitableMorph = False

        while not foundSuitableMorph:
            randomMaterial = random.sample(culledAldenMaterialOptions,1)[0]

            if randomMaterial == self.alden.limbMaterials[indexChosenLimb]:
                continue

            elif randomMaterial == self.alden.material:
                continue

            self.alden.limbMaterials[indexChosenLimb] = randomMaterial
            foundSuitableMorph = True

        return

    def viralLimb(self,switchLimb):

        oldLimb = random.sample(self.alden.affectedLimbs,1)[0]
        indexOldLimb = self.alden.affectedLimbs.index(oldLimb)
        materialOldLimb = self.alden.limbMaterials[indexOldLimb]
        foundSuitableMorph = False

        while not foundSuitableMorph:
            chosenLimb = random.randint(0,self.alden.comps-1)

            if chosenLimb == oldLimb:
                continue

            head = self.alden.headsTails[chosenLimb][0]
            tail = self.alden.headsTails[chosenLimb][1]
            isBuried = self.alden.implantation

            if isBuried != 0.0 and head[2] < 0 and tail[2] < 0:
                continue

            if chosenLimb in self.alden.affectedLimbs:
                indexChosenLimb = self.alden.affectedLimbs.index(chosenLimb)
                self.alden.affectedLimbs.pop(indexChosenLimb)
                self.alden.limbMaterials.pop(indexChosenLimb)

            if switchLimb == True:                                                                      # return first limb to body base material
                self.alden.affectedLimbs.pop(indexOldLimb)
                self.alden.limbMaterials.pop(indexOldLimb)

            else:                                                                                       # maintain first limb material
                pass

            self.alden.affectedLimbs.append(chosenLimb)
            self.alden.limbMaterials.append(materialOldLimb)
            foundSuitableMorph = True

        return

    def cannedMaterialTransition(self):

        self.alden.optical = 0
        restore = random.randint(0,1)

        if restore:
            # just restore previously held canned material

            self.alden.densityUniform = 1
            self.alden.affectedLimbs = []
            self.alden.limbMaterials = []
            return

        else:
            # random new canned material
            
            self.newBodyBaseMaterial()
  
        return