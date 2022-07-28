
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


class restoreMorph:
    # right now, just stick morph or just blender morph.

    def __init__(self):
        pass

    def restoreSpec(self,descId):

        restore = applyMorph()

        infoTransfer = informationTransfer()
        infoTransfer.startImport(descId)

        restore.alden = infoTransfer.alden
        restore.env = infoTransfer.env

        restore.whichMorphs.append('RestoreBSpec')

        restore.infoTransfer = infoTransfer
        restore.completeMorph(descId)
        print(descId,' DONE ')
        return


if __name__ == "__main__":

    # # redirect output to log file
    # logfile = 'logfile_restore_spec.log'
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

    # toMorph = [1521674429391161, 1521674430193895]
    # for a in toMorph:

    #     getDescId = "SELECT descId FROM stimobjdata WHERE id = '" + str(a) + "'"
    #     cursor.execute(getDescId)
    #     descIds.append(cursor.fetchone()[0])

    db.commit()
    db.close()

    startTime = time.time()

    p = Pool(8) # what is the correct number here?
    rm = restoreMorph()
    p.map(rm.restoreSpec,descIds)

    endTime = time.time()

    print(endTime-startTime)

    # # disable output redirection
    # os.close(1)
    # os.dup(old)
    # os.close(old)

