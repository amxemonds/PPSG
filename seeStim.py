
import bpy
import sys
import os

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


class stimViewer:

    def __init__(self,stimID):

        self.stimID = stimID
        self.see()

    def see(self):

        renderToolkit = informationTransfer()
        renderToolkit.importXMLexactlyAsIs(self.stimID)

        print(self.stimID,' DONE')
        return


if __name__ == "__main__":

    # # redirect output to log file
    # logfile = '/Users/ecpc31/Documents/logfile_visualize.log'
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

    descId = '180629_r-186_g-1_l-0_s-5'#'180626_r-178_g-3_l-1_s-8'#'180626_r-178_g-1_l-1_s-3' #'180626_r-178_g-4_l-0_s-1';
    print(descId)
    load = stimViewer(descId)

    # # disable output redirection
    # os.close(1)
    # os.dup(old)
    # os.close(old)
