import bpy
import sys
import os
import random
from multiprocessing import Pool
import time
import traceback

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

from aldenMesh import aldenConstructor
from environmentPrimitives import environmentSpec, environmentConstructor, enclosureConstructor
from infoTransfer import informationTransfer
from delete import deleteTool


class newBSpec:

    def __init__(self):

        self.descId = None

    def generate(self,information):

        descId = information[0]
        stimType = information[1]
        whichStim = information[2]

        try:

            env = environmentSpec()
            enviroConstr = environmentConstructor(env)
            enclosConstr = enclosureConstructor(env)
            aldenConstr = aldenConstructor()

            edges,faces,verts = aldenConstr.fetchMesh(descId)
            # edges = None 
            # faces = None 
            # verts = None
            mesh = [edges,faces,verts]
            hasMesh = verts != None

            if stimType != 'LIBRARY':

                if stimType == 'PH_LIBRARY':
                    prefix  = '190705_r-47_g-1_l-0_s-'
                    descIdConversion = prefix+str(whichStim)

                    infoTransfer = informationTransfer()
                    infoTransfer.startImport(descIdConversion,database='PH_LIBRARY')

                    if len(infoTransfer.alden.stabRot):
                        infoTransfer.alden.rotation = [r for r in infoTransfer.alden.stabRot]

                    else:
                        infoTransfer.alden.rotation = [0,0,0]

                    infoTransfer.alden.id = descId
                    infoTransfer.env.context = 'PreHocStimulusLibrary'
                    infoTransfer.env.parentID = 'PreHoc_Stimulus_Library-' + str(whichStim)
                    infoTransfer.env.stimulusID = descId
                    infoTransfer.transferMStickSpec(descIdConversion,phLibraryName,descId,databaseName)
                    infoTransfer.transferVertFaceSpecs(descIdConversion,phLibraryName,descId,databaseName)

                    alden = infoTransfer.alden
                    env = infoTransfer.env
                    print(descId,' DONE ')

                elif stimType == 'TALL_LIBRARY':
                    prefix  = '190819_r-205_g-1_l-0_s-'
                    descIdConversion = prefix+str(whichStim)

                    infoTransfer = informationTransfer()
                    infoTransfer.startImport(descIdConversion,database='TALL_LIBRARY')

                    if len(infoTransfer.alden.stabRot):
                        infoTransfer.alden.rotation = [r for r in infoTransfer.alden.stabRot]

                    else:
                        infoTransfer.alden.rotation = [0,0,0]

                    infoTransfer.alden.id = descId
                    infoTransfer.env.context = 'TallStimulusLibrary'
                    infoTransfer.env.parentID = 'Tall_Stimulus_Library-' + str(whichStim)
                    infoTransfer.env.stimulusID = descId
                    infoTransfer.transferMStickSpec(descIdConversion,tallLibraryName,descId,databaseName)
                    infoTransfer.transferVertFaceSpecs(descIdConversion,tallLibraryName,descId,databaseName)

                    alden = infoTransfer.alden
                    env = infoTransfer.env
                    print(descId,' DONE ')

                else:
                    enviroConstr.gaRandomEnvironmentSpec(hasMesh)
                    alden = aldenConstr.gaRandomAlden(descId,mesh,deleteMesh=0)
                    alden.id = descId
                    env.compositeKeepAlden = 1
                    
                    if hasMesh:
                        distBackMultiplier = enviroConstr.setFixationPointAtDesiredFocalLength(alden)
                        fp = enviroConstr.fitFixationPoint(alden,fpMultiplier=2**alden.scaleShiftInDepth)

                    else:
                        enviroConstr.slantScene()

                        fp = enviroConstr.fitFixationPointObjectless()

                        enviroConstr.grassGravity()
                        enviroConstr.tiltScene()

            elif stimType == 'LIBRARY':
                # here, choose a random number and assign that library stimulus as parentID
                # whichStim = random.randint(0,librarySize-1)

                # whichStim between 0 and 49:       190304_r-618_g-1_l-0_s-
                if 0 <= whichStim < 50:
                    prefix  = '190706_r-49_g-1_l-0_s-'
                    descIdConversion = prefix+str(whichStim)

                # whichStim between 50 and 99:      190304_r-619_g-1_l-0_s-
                elif 50 <= whichStim < 100:
                    prefix  = '190706_r-49_g-1_l-1_s-'
                    descIdConversion = prefix+str(whichStim-50)

                # whichStim between 100 and 149:    190304_r-620_g-1_l-0_s-
                elif 100 <= whichStim < 150:
                    prefix  = '190706_r-51_g-1_l-0_s-'
                    descIdConversion = prefix+str(whichStim-100)

                # whichStim between 150 and 199:    190304_r-621_g-1_l-0_s-
                elif 150 <= whichStim < 200:
                    prefix  = '190706_r-51_g-1_l-1_s-'
                    descIdConversion = prefix+str(whichStim-150)

                infoTransfer = informationTransfer()
                infoTransfer.startImport(descIdConversion,database='LIBRARY')

                if len(infoTransfer.alden.stabRot):
                    infoTransfer.alden.rotation = [r for r in infoTransfer.alden.stabRot]

                else:
                    infoTransfer.alden.rotation = [0,0,0]

                infoTransfer.alden.id = descId
                infoTransfer.env.context = 'RandomStimulusLibrary'
                infoTransfer.env.parentID = 'Random_Stimulus_Library-' + str(whichStim)
                infoTransfer.env.stimulusID = descId
                infoTransfer.transferMStickSpec(descIdConversion,randomStimDatabaseName,descId,databaseName)
                infoTransfer.transferVertFaceSpecs(descIdConversion,randomStimDatabaseName,descId,databaseName)

                alden = infoTransfer.alden
                env = infoTransfer.env
                print(descId,' DONE ')

            else:
                print(descId,'FAILED')
            #     # blank spec
            #     enviroConstr.noEnvironment()
            #     alden = aldenConstr.gaRandomAlden(descId,mesh,deleteMesh=0)
            #     alden.id = descId
            #     env.compositeKeepAlden = 1
            #     env.context = 'RandomStimulusLibrary'

            #     fp = enviroConstr.makeTarget([0,0,0])

            #     # here, choose a random number and assign that library stimulus as parentID
            #     whichStim = random.randint(0,librarySize-1)
            #     env.parentID = 'Random_Stimulus_Library-' + str(whichStim)

            # need to save to XML, perhaps render
            exportToolkit = informationTransfer()
            exportToolkit.alden = alden
            exportToolkit.env = env
            exportToolkit.exportXML(descId)
            print(descId,' DONE')

        except Exception as e:
            print(descId,'FAILED')
            print(e)
            pass
            # logfile = 'logfile_random_spec_'+descId+'.log'
            # logf = open(logfile, 'a')
            # logf.write(str(e))
            # logf.write(traceback.format_exc())
            # logf.write('It was bad.')
            # logf.close()

        return


if __name__ == "__main__":

    # # redirect output to log file
    # logfile = 'logfile_random_spec.log'
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
    descIdsTemp = []

    if len(sys.argv) > 6:

        for a in range(6,len(sys.argv)):

            getDescId = "SELECT descId FROM StimObjData WHERE id = '" + str(sys.argv[a]) + "'"
            cursor.execute(getDescId)
            descIdsTemp.append(cursor.fetchone()[0])

    else:
        getPre = "SELECT prefix FROM DescriptiveInfo WHERE tstamp = (SELECT max(tstamp) FROM DescriptiveInfo)"
        getRun = "SELECT gaRun FROM DescriptiveInfo WHERE tstamp = (SELECT max(tstamp) FROM DescriptiveInfo)"
        getGen = "SELECT genNum FROM DescriptiveInfo WHERE tstamp = (SELECT max(tstamp) FROM DescriptiveInfo)"
        getLin = "SELECT linNum FROM DescriptiveInfo WHERE tstamp = (SELECT max(tstamp) FROM DescriptiveInfo)"

        cursor.execute(getPre)
        prefix = cursor.fetchone()[0]

        cursor.execute(getRun)
        runNum = cursor.fetchone()[0]

        cursor.execute(getGen)
        genNum = cursor.fetchone()[0]

        cursor.execute(getLin)
        linNum = cursor.fetchone()[0]

        getStim = "SELECT descId FROM StimObjData WHERE instr(descId,'" +str(prefix)+"_r-"+str(runNum)+"_g-"+str(genNum)+"_l-"+str(linNum)+"') ORDER BY id ASC" 
        print(getStim)

        cursor.execute(getStim)
        descIdsTemp = [str(a[0]) for a in cursor.fetchall()]

    stimType = 'NONE'

    # print(descIdsTemp)

    randomLibOrder = random.sample(range(librarySize),librarySize)
    randomLibIndex = 0

    randomPHOrder = random.sample(range(phLibrarySize),phLibrarySize)
    randomPHIndex = 0

    randomTallOrder = random.sample(range(50),50)
    randomTallIndex = 0

    for descId in descIdsTemp:

        if 'BLANK' not in descId:
            checkType = "SELECT extractValue(javaspec,'/PngObjectSpec/stimType') FROM StimObjData WHERE descId='"+str(descId)+"'"
            cursor.execute(checkType)
            stimType = cursor.fetchone()[0]

            if stimType == 'LIBRARY':
                randomLibIdentity = randomLibOrder[randomLibIndex]
                randomLibIndex += 1

            elif stimType == 'PH_LIBRARY':
                randomLibIdentity = randomPHOrder[randomPHIndex]
                randomPHIndex += 1

            elif stimType == 'TALL_LIBRARY':
                randomLibIdentity = randomTallOrder[randomTallIndex]
                randomTallIndex += 1

            else:
                randomLibIdentity = None

            descIds.append((descId,stimType,randomLibIdentity))

    print(descIds)

    # get library specs and actually put them into the database? this would involve transferring files from one large folder... and filling up the database with the specs...
    # maybe it would be better to get these post-hoc? maybe not...

    db.commit()
    db.close()

    startTime = time.time()

    p = Pool(8)
    nbs = newBSpec()
    p.map(nbs.generate,descIds)
    # for descId in descIds:    
    #     nbs.generate(descId)
    # nbs.generate(descIds[32])

    endTime = time.time()

    print(endTime-startTime)

    # # disable output redirection
    # os.close(1)
    # os.dup(old)
    # os.close(old)
