
import bpy
import sys
import os
from multiprocessing import Pool
import time
import random

sys.path.append("/usr/local/lib/python3.6/site-packages")
sys.path.append("/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages")
sys.path.append("/Library/Python/2.7/site-packages")

import mysql.connector

dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)
    sys.path.append(dir+'/Morphs/')
    sys.path.append(dir+'/Primitives/')

import config
from config import *

from infoTransfer import informationTransfer
from delete import deleteTool
from aldenMesh import aldenConstructor

import objectDetailMorph
import orientationMorph
import materialMorph
import opticalPropertyMorph
import sceneDetailMorph
import contextMorph

from chooseMorph import morphStimulus


class applyMorph:

    def __init__(self):

        self.whichMorphs = []
        self.alden = None
        self.env = None
        self.infoTransfer = None

    def morph(self,descId):

        infoTransfer = informationTransfer()
        infoTransfer.startImport(descId)

        self.alden = infoTransfer.alden
        self.env = infoTransfer.env

        whichContext = self.env.context
        findMorph = morphStimulus(whichContext)
        self.whichMorphs = findMorph.whichMorphs

        self.infoTransfer = infoTransfer
        self.completeMorph(descId)
        print(descId,' DONE ',[m for m in self.env.morph],self.env.parentID,self.env.stimulusID)
        return

    def completeMorph(self,descId):

        alden = self.alden
        env = self.env

        if 'Environment' in env.context:
            env.context = 'Environment'

        elif 'Object' in env.context:
            env.context = 'Object'

        for whichMorph in self.whichMorphs:

            ###
            ###     OBJECT DETAIL MORPH
            ###

            if whichMorph in ['GenerateNewObject','DeleteExistingObject','SwitchBlockiness','AlterSymmetry','MorphExistingObject','RestoreBSpec']:

                morph = objectDetailMorph.objectDetailMorph(alden)

                if whichMorph == 'GenerateNewObject':
                    morph.generateNewObject()

                elif whichMorph == 'DeleteExistingObject':
                    morph.deleteExistingObject()

                elif whichMorph == 'SwitchBlockiness':
                    morph.switchBlockiness()

                elif whichMorph == 'AlterSymmetry':
                    morph.alterSymmetry()

                    if sum(alden.makePrecarious) == False:

                        if alden.mirrored[2]:

                            if random.random() <= 0.8:                                              # 80% chance of additional Z rotation if bilaterally symmetric (to offset starkness of symmetry)
                                alden.makePrecarious = [0.0,0.0,random.random()*60-30,1.0]          # pre-rotation in Z for bilaterally symmetric stimuli; random value between -30.0 and 30.0 degrees

                elif whichMorph == 'MorphExistingObject':
                    morph.morphExistingObject()

                elif whichMorph == 'RestoreBSpec':
                    morph.restoreBSpec()

            ###
            ###     ORIENTATION MORPH
            ###

            elif whichMorph in ['PotentialMorph','PrecariousnessMorph','ImplantationMorph','ScaleShiftInDepth']:

                morph = orientationMorph.orientationMorph(alden)

                if whichMorph == 'PotentialMorph':
                    morph.potentialMorph()

                elif whichMorph == 'PrecariousnessMorph':
                    morph.precariousnessMorph()

                elif whichMorph == 'ImplantationMorph':
                    morph.implantationMorph()

                elif whichMorph == 'ScaleShiftInDepth':
                    morph.scaleShiftInDepth()

            ###
            ###     MATERIAL MORPH
            ###

            elif whichMorph in ['BodyBase','SeparateLimb','RestoreLimb','ChangeLimb','ViralLimbBase','ViralLimbRetain','CannedTransition']:

                morph = materialMorph.materialMorph(alden)

                if whichMorph == 'BodyBase':
                    morph.newBodyBaseMaterial()

                elif whichMorph == 'SeparateLimb':
                    morph.separateLimb()

                elif whichMorph == 'RestoreLimb':
                    morph.restoreLimb()

                elif whichMorph == 'ChangeLimb':
                    morph.changeLimb()

                elif whichMorph == 'ViralLimbBase':
                    morph.viralLimb(True)

                elif whichMorph == 'ViralLimbRetain':
                    morph.viralLimb(False)

                elif whichMorph == 'CannedTransition':
                    morph.cannedMaterialTransition()

                if alden.affectedLimbs:
                    alden.densityUniform = 0

                else:
                    alden.densityUniform = 1

            ###
            ###     OPTICAL PROPERTY MORPH
            ###

            elif whichMorph in ['AlterIOR','AlterAttenuation','AlterBLColor','AlterTranslucency','AlterTransparency','AlterRoughness','AlterReflectivity','OpticsTransition']:

                morph = opticalPropertyMorph.opticalPropertyMorph(alden)

                if whichMorph == 'AlterIOR':
                    morph.alterIOR()

                elif whichMorph == 'AlterAttenuation':
                    morph.alterAttenuation()

                elif whichMorph == 'AlterBLColor':
                    morph.alterBLColor()

                elif whichMorph == 'AlterTranslucency':
                    morph.alterTranslucency()

                elif whichMorph == 'AlterTransparency':
                    morph.alterTransparency()

                elif whichMorph == 'AlterRoughness':
                    morph.alterRoughness()

                elif whichMorph == 'AlterReflectivity':
                    morph.alterReflectivity()

                elif whichMorph == 'OpticsTransition':
                    morph.opticsTransition()

            ###
            ###     SCENE DETAIL MORPH
            ###

            elif whichMorph in ['NewHorizonMaterial','AlterTimeOfDay','AlterHorizonTilt','AperturePresent']:

                morph = sceneDetailMorph.sceneDetailMorph(env)

                if whichMorph == 'NewHorizonMaterial':
                    morph.newHorizonMaterial()

                elif whichMorph == 'AlterTimeOfDay':
                    morph.alterTimeOfDay()

                elif whichMorph == 'AlterHorizonTilt':
                    morph.alterHorizonTilt()

                elif whichMorph == 'AperturePresent':
                    morph.aperturePresent()

            ###
            ###     CONTEXT MORPH
            ###

            elif whichMorph in ['ObjectPosition','NewStructureMaterial','ChangeDistance']:

                morph = contextMorph.contextMorph(env)

                if whichMorph == 'ObjectPosition':
                    morph.changeRelativeObjectPosition(alden)

                elif whichMorph == 'NewStructureMaterial':
                    morph.newStructureMaterial()

                elif whichMorph == 'ChangeDistance':
                    morph.changeDistance()

            # ARCHITECTURE

            elif whichMorph in ['ArchitectureCompositionAlden','ArchitectureComposition','ClingHang','AlterThickness']:

                morph = contextMorph.contextMorph_Architecture(env)

                if whichMorph == 'ArchitectureCompositionAlden':
                    morph.changeArchitectureCompositionAlden(alden)

                elif whichMorph == 'ArchitectureComposition':
                    morph.changeArchitectureComposition()

                elif whichMorph == 'ClingHang':
                    morph.clingORhang(alden)

                elif whichMorph == 'AlterThickness':
                    morph.alterThickness()

            # GRASSGRAVITY

            elif whichMorph in ['ChangeHorizonTilt','ChangeHorizonSlant','ChangeGravityDirection']:

                morph = contextMorph.contextMorph_GrassGravity(env)

                if whichMorph == 'ChangeHorizonTilt':
                    morph.changeHorizonTilt()

                elif whichMorph == 'ChangeHorizonSlant':
                    morph.changeHorizonSlant()

                elif whichMorph == 'ChangeGravityDirection':
                    morph.changeGravityDirection()


            else:
                print('No morph match found:',whichMorph)

            env.morph.append(whichMorph)

        if alden.present:
            aldenConstr = aldenConstructor()
            aldenConstr.aldenSpec = alden
            aldenConstr.aldenComplete()

        self.infoTransfer.exportXML(descId)
        return


if __name__ == "__main__":

    # # redirect output to log file
    # logfile = 'logfile_morph_spec.log'
    # open(logfile, 'a').close()
    # old = os.dup(1)
    # sys.stdout.flush()
    # os.close(1)
    # os.open(logfile, os.O_WRONLY)

    # use blender render engine
    scn.render.engine = 'BLENDER_RENDER'
    scn.frame_end = totalFrames

    # clear cache, delete objects
    bpy.ops.ptcache.free_bake_all()
    deleteToolkit = deleteTool()
    deleteToolkit.deleteAllMaterials()
    deleteToolkit.deleteAllObjects()

    db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
    cursor = db.cursor()

    descIds = []

    for a in range(6,len(sys.argv)):

        getDescId = "SELECT descId FROM StimObjData WHERE id = '" + str(sys.argv[a]) + "'"
        cursor.execute(getDescId)
        descIds.append(cursor.fetchone()[0])

    # toMorph = [1521674428853890, 1521674429389157, 1521674430188023, 1521674430190801, 1521674431464228, 1521674431465853, 1521674431467179, 1521674431877930]
    # for a in toMorph:

    #     getDescId = "SELECT descId FROM stimobjdata WHERE id = '" + str(a) + "'"
    #     cursor.execute(getDescId)
    #     descIds.append(cursor.fetchone()[0])

    db.commit()
    db.close()

    startTime = time.time()

    p = Pool(4)
    am = applyMorph()
    p.map(am.morph,descIds)

    endTime = time.time()

    print(endTime-startTime)

    # # disable output redirection
    # os.close(1)
    # os.dup(old)
    # os.close(old)
