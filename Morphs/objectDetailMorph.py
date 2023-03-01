
import bpy
import sys
import os

import numpy as NP
import random

import subprocess

dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)

import config
from config import *

from aldenMesh import aldenConstructor
from delete import deleteTool


###
###     OBJECT DETAIL MORPH
###

class objectDetailMorph:

    def __init__(self,alden):

        self.alden = alden

    def generateNewObject(self):

        self.restoreBSpec()
        return

    def morphExistingObject(self):
        
        self.restoreBSpec()
        return 

    def deleteExistingObject(self):

        self.alden.mesh = 0
        return 

    def restoreBSpec(self):

        self.alden.densityUniform = 1
        self.alden.affectedLimbs = []
        self.alden.limbMaterials = []
        self.alden.rotation = []
        self.alden.fixationPoint = 1
        self.__switchMesh()
        return

    def switchBlockiness(self):

        self.alden.blocky = int(not self.alden.blocky)
        self.__switchMesh()
        return

    def alterSymmetry(self):

        self.alden.mirrored = [int(not self.alden.mirrored[0]),0,0]
        return

    def __switchMesh(self):

        aldenConstr = aldenConstructor()
        edges,faces,verts = aldenConstr.fetchMesh(self.alden.id)
        mesh = [edges,faces,verts]

        alden2 = aldenConstr.draw(self.alden.id,mesh,0,0,0,blocky=self.alden.blocky)
        deleteMesh = self.alden.mesh
        deleteToolbox = deleteTool()
        deleteToolbox.deleteSingleObject(deleteMesh)

        self.alden.mesh = alden2.mesh
        return

