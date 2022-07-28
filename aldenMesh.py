
import bpy
import xml.etree.ElementTree as ET
import sys

sys.path.append("/usr/local/lib/python3.6/site-packages")
sys.path.append("/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages")
sys.path.append("/Library/Python/2.7/site-packages")

import mysql.connector

import csv
import math
import random
from mathutils import Vector
from mathutils import Euler
import numpy as NP

import subprocess

import config
from config import *

from addonMaterials import materialTool, massTool
from physics import physicsTool
from delete import deleteTool


class aldenObjectSpec:

    kind = 'Alden Object Stimulus Specification'

    def __init__(self):

        self.mesh = None                                                            # Blender mesh object
        self.id = None
        self.present = None
        self.blocky = None                                                          # not blocky (0), transformed into block-approximated structure (1)
        self.mirrored = []                                                          # symmetry along [x,y,z] axes

        self.armature = None
        self.skeleton = None                                                        # Blender mesh object rig
        self.juncEndPt = []                                                         # all unique junction or endpoints in mesh object rig
        self.comps = None                                                           # number of components in skeleton
        self.compOrder = []
        self.taggedComps = None                                                     # list of pairs of merged components in skeleton 
        self.fixationPoint = []                                                     # geo center (0), closest to geo center (1) juncPt/endPt index (ind = val-2,...)

        self.surfaceAreas = None
        self.wholeWeightSurfaceArea = None

        self.headsTails = []                                                        # all head/tail pairs in mesh object rig
        self.boneTags = []
        self.whichWiggle = None

        self.location = None                                                        # floor (0), ceiling (1), left wall (2), right wall (3), back wall (4)
        self.wallInteraction = None                                                 # clings to surface of architecture (-1), proximal but unsupported (0), hangs from architecture (1)
        self.implantation = None                                                    # fraction of stimulus buried
        self.scaleShiftInDepth = None                                               # logarithmic depth change and compensatory scaling: 2^(0),(1),(2),(3)
        self.consistentRetinalSize = 1

        self.mat = None                                                             # object material storage (for convenience)
        self.material = None
        self.densityUniform = None                                                  # limb-by-limb density assignment (0), uniform density (1) 
        self.affectedLimbs = []                                                     # if density is nonuniform, limbs with influenced density
        self.limbMaterials = []                                                     # nonuniform density is cued by a material transition
        self.massManipulationLimb = 0

        self.optical = None                                                         # material properties manipulation (0), optical properties manipulation (1)
        self.opticalIOR = None                                                      # index of refraction from 1.0 to 2.0
        self.opticalAttenuation = None                                              # attenuation of ray/intensity of absorption (more negative -> more dense)
        self.opticalBeerLambertColor = []
        self.opticalTranslucency = None                                             # no subsurface scattering to subsurface scattering, sliding scale 0.0 to 1.0
        self.opticalTransparency = None                                             # opaque to transparent, sliding scale 0.0 to 1.0
        self.opticalRoughness = None                                                # not rough surface to rough surface, sliding scale 0.0 to 1.0
        self.opticalReflectivity = None                                             # not reflective to reflective, sliding scale 0.0 to 1.0

        self.lowPotentialEnergy = None                                              # not dropped (0), dropped (1)
        self.makePrecarious = []                                                    # additional rotation in radians; final value boolean indication of whether precariousness is final transformation
        self.rotation = []                                                          # store lowPotentialEnergy rotation or default rotation
        self.stabRot = []

        self.boundingBoxLongAxis = None
        self.comVector = []
        self.horizonNormal = []
        self.mass = None
        
        self.materialToolkit = materialTool()
        self.massToolkit = massTool()
        self.physicsToolkit = physicsTool()
        self.deleteToolkit = deleteTool()


###
###     ALDEN STIMULUS CONSTRUCTOR
###

class aldenConstructor:

    def __init__(self):

        self.aldenSpec = None

    def draw(self,moniker,mesh,x=0,y=0,z=0,blocky=0):
        # load and draw a medial axis form

        self.aldenSpec = aldenObjectSpec()
        alden = self.aldenSpec
        alden.blocky = blocky
            
        edges = mesh[0]
        faces = mesh[1]
        verts = mesh[2]

        if verts:

            me = bpy.data.meshes.new('AldenMesh')
            me.from_pydata(verts,edges,faces)
            alden.mesh = bpy.data.objects.new('AldenObject', me)                            # assemble Alden medial axis object
            
            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.link(alden.mesh)                                                    # link object to scene
            scn.objects.active = alden.mesh                                                 # make object active
            alden.mesh.select = True
            alden.mesh.location = Vector((x,y,z))                                           # locate within environment
            
            # remove doubles from mesh and smooth surface
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.remove_doubles()
            bpy.ops.mesh.fill_holes()
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.mesh.faces_shade_smooth()
            bpy.ops.mesh.mark_sharp(clear=True, use_verts=True)
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.transform.resize(value=(0.001*stimulusScale,0.001*stimulusScale,0.001*stimulusScale),constraint_axis=(True, True, True))
            # 0.001 for transformation of units from Blender units (1BU = 1m) into millimeters
            # 6 for arbitrary, preference-based object rescaling
            bpy.ops.object.transform_apply(scale=True)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

            bpy.ops.object.select_all(action='DESELECT')

            skeleton = aldenSkeleton(alden)
            skeleton.makeSkeleton(moniker,x,y,z,blocky)

            # auto weight paint
            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = alden.skeleton
            alden.mesh.select = True
            alden.skeleton.select = True
            bpy.ops.object.parent_set(type='ARMATURE_AUTO')
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

            scn.objects.active = alden.mesh
            bpy.ops.object.modifier_remove(modifier='Armature')
            bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)

            #alden.deleteToolkit.deleteSingleObject(alden.skeleton)
            #alden.skeleton = 0

            alden.present = 1

        else:
            alden.present = 0

        return alden

    def fetchMesh(self,descId):

        # from Ram's dbExchange.py
        db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
        cursor = db.cursor()

        queryVert = "SELECT vertspec FROM StimObjDataVert WHERE descId = '" + descId + "'"
        queryFace = "SELECT facespec FROM StimObjDataVert WHERE descId = '" + descId + "'"

        try:
            # vertspec
            cursor.execute(queryVert)
            vertspecStr = cursor.fetchone()
            vertspecStr = vertspecStr[0]
            vertspecStr = vertspecStr.decode('UTF-8')
            vertspecStr = vertspecStr.split('\n')
            vertSpec = [];
            for vertTriad in vertspecStr[:-1]:
                triad = vertTriad.split(',')
                triadNum = [float(triad[0]),float(triad[1]),float(triad[2])]
                vertSpec.append(triadNum)

            # facespec
            cursor.execute(queryFace)
            facespecStr = cursor.fetchone()
            facespecStr = facespecStr[0]
            facespecStr = facespecStr.decode('UTF-8')
            facespecStr = facespecStr.split('\n')
            faceSpec = [];
            for vertTriad in facespecStr[:-1]:
                triad = vertTriad.split(',')
                triadNum = [float(triad[0]),float(triad[1]),float(triad[2])]
                faceSpec.append(triadNum)

            # load stimulus attributes
            edges = []

            faces = []
            for face in faceSpec:
                faces.append((int(face[0])-1,int(face[1])-1,int(face[2])-1))

            verts = []
            for vertex in vertSpec:
                verts.append((float(vertex[0]),float(vertex[1]),float(vertex[2])))

        except:
            edges = faces = verts = None

        db.commit()
        db.close()
        return edges,faces,verts

    def gaRandomAlden(self,moniker,mesh,deleteMesh=0):

        # new alden stimulus
        # blocky = random.randint(0,9) == 9
        # blocky = random.randint(0,1)
        blocky = 0

        alden = self.draw(moniker,mesh,0,0,0,blocky=blocky)

        if alden.present:
            self.gaAldenStart(deleteMesh=0)

        else:
            self.noAldenStimulus()

        return alden

    def gaAldenStart(self,deleteMesh=0):

        alden = self.aldenSpec

        # mirrorX = random.randint(0,10) # random.randint(0,1)
        mirrorX = 3

        if mirrorX >= 3:
            mirrorX = 0

        else:
            mirrorX = 1

        mirrorY = 0
        mirrorZ = 0
        alden.mirrored = [mirrorX,mirrorY,mirrorZ]

        # defaults for first alden generation
        alden.lowPotentialEnergy = 1
        alden.lowPotentialEnergy = 0
        alden.densityUniform = 1 
        alden.affectedLimbs = []
        alden.limbMaterials = []

        alden.location = 0
        alden.wallInteraction = 0

        precarious = random.randint(0,1)

        while precarious:
            rotX = random.random()*60-30                        # random value between -30.0 and 30.0 degrees
            rotY = random.random()*60-30                        # random value between -30.0 and 30.0 degrees
            rotZ = random.random()*60-30                        # random value between -30.0 and 30.0 degrees

            sumDegrees = abs(rotX)+abs(rotY)+abs(rotZ)

            if sumDegrees >= 30.0 and sumDegrees <= 60.0:
                alden.makePrecarious = [rotX*math.pi/180,rotY*math.pi/180,rotZ*math.pi/180]
                break

        if not precarious:
            alden.makePrecarious = [0.0,0.0,0.0]

            if mirrorX:

                if random.random() <= 0.8:                                          # 80% chance of additional Z rotation if bilaterally symmetric (to offset starkness of symmetry)
                    alden.makePrecarious = [0.0,0.0,random.random()*60-30]          # pre-rotation in Z for bilaterally symmetric stimuli; random value between -30.0 and 30.0 degrees

        alden.makePrecarious.append(1.0)                                            # precariousness is final operation
        # alden.implantation = burialDepth[1]
        alden.implantation = random.sample(burialDepth[1:],1)[0]
        alden.rotation = []

        deleteMesh = random.randint(0,10)
        deleteMesh = 0

        # variables for first alden generation
        alden.scaleShiftInDepth = 0 #random.randint(0,3)

        alden.optical = random.randint(0,1)

        alden.opticalIOR = random.random()*(2.3-1.3)+1.3
        alden.opticalAttenuation = random.randint(-5,0)                                 # -5.0 : 1.0 : 0.0
        alden.opticalBeerLambertColor = [random.random(),random.random(),random.random()]
        alden.opticalTranslucency = 0.1*random.randint(0,10)
        alden.opticalTransparency = 0.1*random.randint(0,10)
        alden.opticalRoughness = 0.1*random.randint(0,10)
        alden.opticalReflectivity = 0.1*random.randint(0,10)

        alden.material = random.sample(culledAldenMaterialOptions,1)[0]

        if deleteMesh == 1:
            alden.deleteToolkit.deleteSingleObject(alden.mesh)
            alden.mesh = 0

        else:
            self.aldenComplete()

        alden.fixationPoint = 1
        return alden      

    def aldenComplete(self):

        alden = self.aldenSpec
        skeletonTool = aldenSkeleton(alden)

        xMin,xMax,yMin,yMax,zMin,zMax,leeway = alden.physicsToolkit.findBoundingBox(alden.mesh)
        alden.mesh.location -= Vector((0,0,zMin))

        if not alden.densityUniform:
            alden.massToolkit.separateForDensityAssignment(alden)

        else:
            alden.massToolkit.makeRigidBody(alden.mesh,'ACTIVE')

            if not alden.optical:
                alden.massToolkit.assignMass(alden.mesh,alden.material)

            else:
                alden.massToolkit.assignMass(alden.mesh,'optical')

        if not alden.rotation:

            if alden.lowPotentialEnergy:
                skeletonTool.bilateralSymmetry()
                alden.physicsToolkit.evaluateTimecourse(alden)
                alden.physicsToolkit.makePrecariousMesh(alden)

            else:
                
                if not alden.densityUniform:
                    alden.physicsToolkit.joinDensityPartition(alden)

                skeletonTool.bilateralSymmetry()
                alden.physicsToolkit.makePrecariousMesh(alden)

        else:

            if not alden.densityUniform:
                alden.physicsToolkit.joinDensityPartition(alden)

            skeletonTool.bilateralSymmetry()
            alden.mesh.rotation_euler = alden.rotation

        return

    def noAldenStimulus(self):

        if not self.aldenSpec:
            alden = aldenObjectSpec()
            self.aldenSpec = alden

        else:
            alden = self.aldenSpec

        alden.present = 0
        alden.mesh = 0
        alden.juncEndPt = []
        alden.fixationPoint = 0

        alden.blocky = 0
        alden.mirrored = [0,0,0]

        alden.lowPotentialEnergy = 0
        alden.densityUniform = 1
        alden.affectedLimbs = []
        alden.limbMaterials = []

        alden.location = 0
        alden.wallInteraction = 0
        alden.implantation = 0

        alden.makePrecarious = [0,0,0,0]
        alden.rotation = [0,0,0]
        alden.scaleShiftInDepth = 0

        alden.optical = 0

        alden.opticalIOR = 0 
        alden.opticalAttenuation = 0
        alden.opticalBeerLambertColor = [0,0,0]
        alden.opticalTranslucency = 0
        alden.opticalTransparency = 0
        alden.opticalRoughness = 0
        alden.opticalReflectivity = 0

        alden.material = ''
        return alden


###
###     ALDEN STIMULUS BONES
###

class aldenSkeleton:

    def __init__(self,aldenObjectSpec):

        self.aldenSpec = aldenObjectSpec

    def makeSkeleton(self,moniker,x,y,z,blocky,skipBlocky=0):
        # generate an armature from Alden stimulus xml and position it appropriately
        # find corresponding bone mesh control weight paint map using auto feature (auto vertex groups)

        alden = self.aldenSpec

        amt = bpy.data.armatures.new('Skeleton')
        alden.armature = amt
        alden.skeleton = bpy.data.objects.new('SkeletonObject',amt)
        alden.skeleton.show_x_ray = True                                                # visualize bones through mesh
        alden.skeleton.data.draw_type = 'STICK'                                         # visualize bones as sticks
        amt.show_names = True                                                           # show armature names
        
        scn.objects.link(alden.skeleton)                                                # link object to scene
        scn.objects.active = alden.skeleton                                             # make object active
        alden.skeleton.select = True
        
        scale = 0.001*stimulusScale*30 
        # 0.001 for transformation of units from Blender units (1BU = 1m) into millimeters
        # 6 for arbitrary, preference-based object rescaling
        # 30 is true Alden scale xml multiplier

        # load Alden stimulus xml from database
        medAxisSpec = self.fetchStimSpec(moniker)
        tree = ET.ElementTree(ET.fromstring(medAxisSpec))

        # import general medial axis data
        mAxis = tree.find('mAxis')
        nComponentsTotal = int(mAxis.findtext('nComponent'))
        nEndPt = int(mAxis.findtext('nEndPt'))
        nJuncPt = int(mAxis.findtext('nJuncPt'))

        nBoneVertices = nEndPt

        for pt in range(1,nJuncPt+1):
            data = mAxis.find('JuncPt')[pt]
            nBoneVertices = nBoneVertices + int(data.findtext('nComp'))

        # store starting points and end points for each component
        youngBones = NP.zeros((nBoneVertices,6))
        boneVertex = 0
        boneVertex,youngBones = self.__pointParse(boneVertex,youngBones,'EndPt',nEndPt,mAxis,scale)
        boneVertex,youngBones = self.__pointParse(boneVertex,youngBones,'JuncPt',nJuncPt,mAxis,scale)
        youngBones = youngBones[NP.lexsort((youngBones[:, 1], ))]                       # sort by uNdx
        youngBones = youngBones[NP.lexsort((youngBones[:, 0], ))]                       # sort by component number

        # document which bone pairs are actually single uNdx-fragmented components              #!!! need support for >2 joined fragments?
        taggedComps = []  

        # based on XML-extracted data, position bones
        for comp in range(1,nComponentsTotal+1):
            workingComp = youngBones[NP.where(youngBones[:,0]==comp),2:5][0]
            workingCompType = youngBones[NP.where(youngBones[:,0]==comp),5][0]
            index = 0
            
            while index+1 < len(workingComp[:,0]):

                try:
                    parent

                except NameError:
                    parent = None

                scn.objects.active = alden.skeleton                                     # make armature active
                alden.skeleton.select = True

                head = workingComp[index,0:3]
                headType = workingCompType[index]
                tail = workingComp[index+1,0:3]
                tailType = workingCompType[index+1]

                if 1 in [headType,tailType]:
                    alden.boneTags.append(1)

                else:
                    alden.boneTags.append(0)

                # if it turns out that what is currently considered to be a tail is actually a head, switch designations
                if headType == 1:                                                       # if headType is 'EndPt'...
                    headTemp = head
                    head = tail                                                         # make tail location that of previous head
                    tail = headTemp                                                     # make head location that of previous tail

                alden.compOrder.append(comp)
                parent = self.__boneGen(amt,head,tail)

                if index == 1:
                    taggedComps.append([amt.edit_bones[-1].name,amt.edit_bones[-2].name])

                index += 1

        alden.taggedComps = taggedComps
        alden.comps = nComponentsTotal
        bpy.ops.object.mode_set(mode='OBJECT')

        # import shift in depth for focus
        shift = [float(s.text)*0.001*stimulusScale for s in mAxis.find('finalShiftinDepth')]

        # final rotation
        rotation = [float(r.text)/180*math.pi for r in mAxis.find('finalRotation')[0:3]]
    
        # move skeleton to location of mesh
        alden.skeleton.location = Vector((x-shift[0],y-shift[1],z-shift[2]))

        # parent bones using binary search tree-like algorithm
        # self.__parentSequence(youngBones)

        if not skipBlocky:

            if blocky:
                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = alden.mesh
                alden.mesh.select = True

                bpy.ops.transform.rotate(value=-rotation[0],axis=(1,0,0))
                bpy.ops.transform.rotate(value=-rotation[1],axis=(0,1,0))
                bpy.ops.transform.rotate(value=-rotation[2],axis=(0,0,1))
                bpy.ops.object.transform_apply(rotation=True)

                self.__makeBlocky()

                bpy.ops.transform.rotate(value=rotation[2],axis=(0,0,1))
                bpy.ops.transform.rotate(value=rotation[1],axis=(0,1,0))
                bpy.ops.transform.rotate(value=rotation[0],axis=(1,0,0))
                bpy.ops.object.transform_apply(rotation=True)

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.skeleton
        alden.skeleton.select = True
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        return

    def fetchStimSpec(self,descId):

        # from Ram's dbExchange.py
        db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
        cursor = db.cursor()

        queryAlden = "SELECT mstickspec FROM StimObjData WHERE descId = '" + descId + "'"

        try:
            cursor.execute(queryAlden)
            medAxisSpec = cursor.fetchone()
            medAxisSpec = medAxisSpec[0]

        except:
            print("Error: unable to fetch data")

        db.commit()
        db.close()
        return medAxisSpec

    def __pointParse(self,boneVertex,youngBones,pointType,totalNumber,mAxis,scale):
        # pointType can be 'EndPt', 'JuncPt'
        # totalNumber can be nEndPt, nJuncPt

        if pointType == 'EndPt':
            pointCode = 1

        elif pointType == 'JuncPt':
            pointCode = 0

        for pt in range(1,totalNumber+1):
            data = mAxis.find(pointType)[pt]
            pos = [float(p.text)*scale for p in data.find('pos')]
            
            comp = data.find('comp')
            
            if len(comp) == 0:
                comp = int(comp.text)
                youngBones[boneVertex,0] = comp

            else:
                temp = comp
                comp = [int(c.text) for c in data.find('comp')]
                comp = comp[1:]
                youngBones[boneVertex:boneVertex+len(comp),0] = comp
                
            uNdx = data.find('uNdx')
            
            if len(uNdx) == 0:
                uNdx = int(uNdx.text)
                youngBones[boneVertex,1] = uNdx
                youngBones[boneVertex,2:5] = pos
                youngBones[boneVertex,5] = pointCode
                boneVertex += 1

            else:
                temp = comp
                uNdx = [int(u.text) for u in data.find('uNdx')]
                uNdx = uNdx[1:]
                youngBones[boneVertex:boneVertex+len(uNdx),1] = uNdx
                youngBones[boneVertex:boneVertex+len(uNdx),2:5] = pos
                youngBones[boneVertex:boneVertex+len(uNdx),5] = pointCode
                boneVertex = boneVertex+len(uNdx)
        return boneVertex,youngBones

    def __boneGen(self,amt,head,tail):
        # create a single bone in an armature

        bpy.ops.object.mode_set(mode='EDIT')
        boneInstance = amt.edit_bones.new('Comp')
        boneInstance.head = head
        boneInstance.tail = tail
        boneInstance.use_connect = True
        return boneInstance
        
    def __parentSequence(self,youngBones):
        # establish the bone lineage: determine parent bones and their children (for limb and body Alden stimulus animation, if ever implemented)

        alden = self.aldenSpec

        bpy.ops.object.mode_set(mode='EDIT')
        scn.objects.active = alden.skeleton                                             # make armature active
        alden.skeleton.select = True

        bonesCollective = [bone for bone in alden.skeleton.data.edit_bones]
        
        heads = [bone.head for bone in alden.skeleton.data.edit_bones]
        tails = [bone.tail for bone in alden.skeleton.data.edit_bones]
        headsTails = heads + tails

        for ii in range(len(bonesCollective)):
            
            if headsTails.count(heads[ii]) == 1:
                seedBone = bonesCollective[ii]
                break
                
            elif headsTails.count(tails[ii]) == 1:
                seedBone = bonesCollective[ii]
                oldHead = Vector(([float(m) for m in seedBone.head]))
                oldTail = Vector(([float(m) for m in seedBone.tail]))
                seedBone.head = oldTail
                seedBone.tail = oldHead
                break

        seedBones = [seedBone]
        noParent = [seedBone]
        hasParent = []

        allParents = len(bonesCollective)

        while len(hasParent+noParent) != allParents:

            for seedBone in seedBones:

                for ii in range(len(bonesCollective)):

                    if bonesCollective[ii] != seedBone:
                        oldHead = Vector(([float(m) for m in bonesCollective[ii].head]))
                        oldTail = Vector(([float(m) for m in bonesCollective[ii].tail]))
                        bonesCollective[ii].select = True

                        if NP.all(oldTail == seedBone.tail):
                            bonesCollective[ii].head = oldTail
                            bonesCollective[ii].tail = oldHead

                            if bonesCollective[ii].parent == None:
                                bonesCollective[ii].parent = seedBone

                            if bonesCollective[ii] not in hasParent:
                                hasParent.append(bonesCollective[ii])

                        elif NP.all(oldHead == seedBone.tail):

                            if bonesCollective[ii].parent == None:
                                bonesCollective[ii].parent = seedBone
                    
                            if bonesCollective[ii] not in hasParent:
                                hasParent.append(bonesCollective[ii])
                            
                        bonesCollective[ii].select = False

            seedBones = hasParent

        bpy.ops.object.mode_set(mode='OBJECT')
        return

    def __makeBlocky(self):

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = self.aldenSpec.mesh
        self.aldenSpec.mesh.select = True

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

        bpy.ops.object.modifier_add(type='REMESH')
        self.aldenSpec.mesh.modifiers['Remesh'].mode = 'BLOCKS'
        self.aldenSpec.mesh.modifiers['Remesh'].octree_depth = 4
        bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Remesh')
        return

    def bilateralSymmetry(self):

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = self.aldenSpec.mesh
        self.aldenSpec.mesh.select = True

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

        bpy.ops.object.transform_apply(rotation=True)

        bpy.ops.object.modifier_add(type='MIRROR')
        mirrorMod = self.aldenSpec.mesh.modifiers['Mirror']

        mirrorMod.use_x = self.aldenSpec.mirrored[0]
        mirrorMod.use_y = self.aldenSpec.mirrored[1]
        mirrorMod.use_z = self.aldenSpec.mirrored[2]
        bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Mirror')
        return


