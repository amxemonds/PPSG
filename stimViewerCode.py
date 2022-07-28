
import bpy
import sys
import os

import mathutils
from mathutils import Vector,Euler
from multiprocessing import Pool

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


class stimViewer:

    def __init__(self):

        self.stimID = None
        self.renderToolkit = None

    def see(self,stimID):
        scn = bpy.context.scene

        self.stimID = stimID
        self.renderToolkit = informationTransfer()
        self.renderToolkit.importXMLexactlyAsIs(self.stimID)

        try:
            if 'Object' in self.renderToolkit.env.context:
                # only continue if stimulus is an object

                alden = self.renderToolkit.alden

                # move center of mass of volume as specified in blender to origin (so, without burial)
                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = alden.mesh
                alden.mesh.select = True

                scn.update()
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')

                # store present vertex location information for later
                vertsLocal = alden.mesh.data.vertices
                vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]

                alden.mesh.location = Vector((0,0,0))

                # generate particle system of empties and parent all empties to object
                comEmpties = self.comParticleSystem()
                
                # record empty locations
                # momentString = ''

                # for ce in comEmpties:
                #     momentString += str(ce.location[0])+','+str(ce.location[1])+','+str(ce.location[2])+'\n'

                # storing individual verts takes too much space...
                # store the I matrix instead
                Xs = [ce.location[0] for ce in comEmpties]
                Ys = [ce.location[1] for ce in comEmpties]
                Zs = [ce.location[2] for ce in comEmpties]
                mk = alden.mass/len(Xs)

                Ixx = sum([mk*(Ys[idx]**2+Zs[idx]**2) for idx in range(len(Xs))])
                Iyy = sum([mk*(Xs[idx]**2+Zs[idx]**2) for idx in range(len(Xs))])
                Izz = sum([mk*(Xs[idx]**2+Ys[idx]**2) for idx in range(len(Xs))])

                Ixy = -sum([mk*Xs[idx]*Ys[idx] for idx in range(len(Xs))])
                Ixz = -sum([mk*Xs[idx]*Zs[idx] for idx in range(len(Xs))])
                Iyz = -sum([mk*Ys[idx]*Zs[idx] for idx in range(len(Xs))])

                # record inertia tensors
                inertiaTensor = ''
                inertiaTensor += str(Ixx)+','+str(Ixy)+','+str(Ixz)+'\n'
                inertiaTensor += str(Ixy)+','+str(Iyy)+','+str(Iyz)+'\n'
                inertiaTensor += str(Ixz)+','+str(Iyz)+','+str(Izz)+'\n'

                # -----

                # using global vertices extracted prior to alden mesh location, 
                # identify all global vertices below the designated burial depth (as usual)
                # and save that information in the form of local vertex coordinates
                bumpStrength = 0.1
                underGroundLocal = [vertsLocal[v] for v in range(len(vertsGlobal)) if vertsGlobal[v][2] <= 0.0+bumpStrength]

                # now that the alden mesh has been moved, use the new alden.mesh.matrix_world 
                # to find the locations of these points in appropriate space
                underGroundGlobal = [alden.mesh.matrix_world * v.co for v in underGroundLocal]

                # record loose pivot (vertex with smallest z)
                allZs = [v[2] for v in underGroundGlobal]
                loosePivot = underGroundGlobal[allZs.index(min(allZs))]
                inertiaTensor += str(loosePivot[0])+','+str(loosePivot[1])+','+str(loosePivot[2])+'\n'

                # find average position of underground vertex
                numUndergroundPoints = max([1,len(underGroundGlobal)])
                xAvg = sum([u[0] for u in underGroundGlobal])/numUndergroundPoints
                yAvg = sum([u[1] for u in underGroundGlobal])/numUndergroundPoints
                zAvg = sum([u[2] for u in underGroundGlobal])/numUndergroundPoints

                # record adjusted pivot
                inertiaTensor += str(xAvg)+','+str(yAvg)+','+str(zAvg)+'\n'

                # -----
                
                databaseName = 'alexandriya_180218_test'#'alexandriya_180218_20-09-20'#
                databaseIP = '172.30.6.80' # '10.161.240.80'

                db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
                cursor = db.cursor()

                transferMomentLocations = "UPDATE StimObjData SET inertiaTensor = '" + inertiaTensor + "' WHERE descId = '" + str(self.renderToolkit.env.stimulusID) + "'"
                cursor.execute(transferMomentLocations)

                db.commit()
                db.close()

                print(self.stimID,' DONE')

            else:
                print(self.stimID,' SKIPPED, ',self.renderToolkit.env.context)
        except:
            print(self.stimID,' SKIPPED')

        return

    def comParticleSystem(self):

        scn = bpy.context.scene
        whichMesh = self.renderToolkit.alden.mesh

        bpy.ops.object.particle_system_add()
        particleSystems = [m for m in whichMesh.particle_systems if m.name.startswith('ParticleSystem')]
        particleSystem = particleSystems[-1]
        particleSystem.name = 'comFill'

        particleGroups = [m for m in bpy.data.particles if m.name.startswith('ParticleSettings')]
        particleGroup = particleGroups[-1]
        particleGroup.name = 'comFill'

        particleGroup.type = 'EMITTER'
        particleGroup.count = 2000
        particleGroup.frame_start = 1
        particleGroup.frame_end = 1
        particleGroup.emit_from = 'VOLUME'
        particleGroup.use_emit_random = False
        particleGroup.use_even_distribution = True
        particleGroup.distribution = 'RAND'
        particleGroup.use_modifier_stack = True
        particleGroup.normal_factor = -1
        particleGroup.physics_type = 'NO'
        particleGroup.use_render_emitter = False
        particleGroup.effector_weights.gravity = 0

        # create a single empty anywhere
        # name that empty to join later...

        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=0.1, location=(0,0,0))
        comEmpty = bpy.data.objects['Empty']
        comEmpty.name = 'COMEmpty'

        particleGroup.render_type = 'OBJECT'
        particleGroup.dupli_object = comEmpty
        particleGroup.frame_end = 1

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = whichMesh
        whichMesh.select = True

        bpy.ops.object.duplicates_make_real()
        bpy.ops.object.select_all(action='DESELECT')

        comEmpties = [m for m in bpy.data.objects if m.name.startswith('COMEmpty')]

        for ce in comEmpties:
            ce.select = True
            
        scn.objects.active = comEmpties[0]
        bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
        return comEmpties


if __name__ == "__main__":

    scn = bpy.context.scene
    scn.view_settings.view_transform = 'Filmic'

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

    # clear cache, delete objects
    bpy.ops.ptcache.free_bake_all()
    deleteToolkit = deleteTool()
    deleteToolkit.deleteAllMaterials()
    deleteToolkit.deleteAllObjects()

    databaseName = 'alexandriya_180218_test'#'alexandriya_180218_20-09-20'#'alexandriya_180218_noTDT_19-08-01'#
    databaseIP = '172.30.6.80' # '10.161.240.80'

    db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
    cursor = db.cursor()

    getStim = "SELECT descId FROM StimObjData ORDER BY id ASC"
    cursor.execute(getStim)

    # only choose descIds within particular runs and stuff

    descIds = [str(a[0]) for a in cursor.fetchall()]
    print(len(descIds))

    jobNum = int(sys.argv[6])

    db.commit()
    db.close()

    view = stimViewer()
    view.see(descIds[jobNum])

    # # disable output redirection
    # os.close(1)
    # os.dup(old)
    # os.close(old)


