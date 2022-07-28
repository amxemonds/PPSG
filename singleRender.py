
import bpy
import sys
import os

sys.path.append("/usr/local/lib/python3.6/site-packages")
sys.path.append("/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages")
sys.path.append("/Library/Python/2.7/site-packages")
sys.path.append("/home/alexandriya/blendRend")
sys.path.append("/usr/lib/python2.7/site-packages")
sys.path.append("/usr/lib/python3.4/site-packages")

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


class stimulusLoad:

    def __init__(self,stimID):

        self.stimID = stimID
        self.generate()

    def generate(self):

        print(self.stimID,' STARTING')
        renderToolkit = informationTransfer()
        renderToolkit.importXMLRenderExactlyAsIs(self.stimID)
        print(self.stimID,' DONE')
        return

def main():

    # use cycles render engine
    scn.render.engine = 'CYCLES'

    # use CPU for physics computations
    scn.cycles.device = 'CPU'

    bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
    for d in bpy.context.user_preferences.addons['cycles'].preferences.devices:
        print(d.type)
        if d.type != 'CUDA':
            d.use = True
        else:
            d.use = False

    scn.frame_end = totalFrames
    scn.view_settings.view_transform = 'Filmic'

    # clear cache, delete objects
    bpy.ops.ptcache.free_bake_all()
    deleteToolkit = deleteTool()
    deleteToolkit.deleteAllMaterials()
    deleteToolkit.deleteAllObjects()

    db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
    cursor = db.cursor()

    jobNum = int(sys.argv[6])
    prefixRunGen = sys.argv[7]
    print(prefixRunGen)
    print(jobNum)

    allDescIds = "SELECT descId FROM StimObjData WHERE instr(descId,'" + prefixRunGen +"')"
    print(allDescIds)
    cursor.execute(allDescIds)
    descIdsTemp = [str(a[0]) for a in cursor.fetchall()]
    descIds = []
    db.commit()
    db.close()

    for descId in descIdsTemp:
        if 'BLANK' not in descId:
            descIds.append(descId)

    print(descIds)
    descId = descIds[jobNum]

    # clear cache, delete objects
    bpy.ops.ptcache.free_bake_all()
    deleteToolkit = deleteTool()
    deleteToolkit.deleteAllMaterials()
    deleteToolkit.deleteAllObjects()
    load = stimulusLoad(descId)

    

if __name__ == "__main__":
    main()
