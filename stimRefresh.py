
import bpy
import sys
import os
from multiprocessing import Pool
import time

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

from morphSpec import applyMorph
import singleRender


class stimRefresh:
    # right now, just stick morph or just blender morph.

    def __init__(self):
        pass

    def refreshSpec(self,descId):

        infoTransfer = informationTransfer()
        infoTransfer.startImport(descId)
        infoTransfer.alden.rotation = [r for r in infoTransfer.alden.stabRot]
        infoTransfer.env.context = 'Mass'
        infoTransfer.exportXML(descId)
        print(descId,' DONE ')
        return

def main():

    # redirect output to log file
    # logfile = '/Users/ecpc31/Documents/logfile_render.log'
    # open(logfile, 'a').close()
    # old = os.dup(1)
    # sys.stdout.flush()
    # os.close(1)
    # os.open(logfile, os.O_WRONLY)

    # use cycles render engine
    scn.render.engine = 'CYCLES'
    bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
    bpy.context.user_preferences.addons['cycles'].preferences.devices[0].use = True
    # bpy.context.user_preferences.addons['cycles'].preferences.devices[1].use = True
    # bpy.context.user_preferences.addons['cycles'].preferences.devices[2].use = True
    scn.frame_end = totalFrames
    scn.view_settings.view_transform = 'Filmic'

    # clear cache, delete objects
    bpy.ops.ptcache.free_bake_all()
    deleteToolkit = deleteTool()
    deleteToolkit.deleteAllMaterials()
    deleteToolkit.deleteAllObjects()

    db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
    cursor = db.cursor()

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

    objCounts = int(sys.argv[6])

    forbiddendescIds1 = [str(prefix)+"_r-"+str(runNum)+"_g-"+str(genNum)+"_l-"+str(linNum)+"_s-"+str(n) for n in range(objCounts)]

    getStim = "SELECT descId FROM StimObjData WHERE instr(descId,'" +str(prefix)+"_r-"+str(runNum)+"_g-"+str(genNum)+"_l-"+str(linNum)+"')"

    cursor.execute(getStim)
    descIdsTemp = [str(a[0]) for a in cursor.fetchall()]
    descIds = []

    for descId in descIdsTemp:
        if 'BLANK' not in descId:
            if descId not in forbiddendescIds1:
                descIds.append(descId)

    db.commit()
    db.close()

    startTime = time.time()

    p = Pool(4) # what is the correct number here?
    rm = stimRefresh()
    p.map(rm.refreshSpec,descIds)

    endTime = time.time()

    print(endTime-startTime)

    # disable output redirection
    # os.close(1)
    # os.dup(old)
    # os.close(old)

    # doRender = singleRender.main()

if __name__ == "__main__":
    main()
