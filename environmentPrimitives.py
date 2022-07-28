
import bpy

import bmesh
import math


from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
import mathutils
from mathutils import Vector,Euler
import numpy as NP
import random

import config
from config import *

from addonMaterials import materialTool, scrubTool, massTool
from physics import physicsTool
from delete import deleteTool


from stimulusRender import finalizeMaterials


###
###     SPEC
###

class environmentSpec:

    kind = 'Environment Stimulus Specification'

    def __init__(self):

        self.stimulusID = None
        self.parentID = None
        self.morph = []

        self.horizon = None                                                         # Blender mesh object
        self.horizonTilt = None                                                     # in radians
        self.horizonSlant = None                                                    # in radians
        self.horizonMaterial = None                                                 # string
        self.secondHorizon = None                                                   # Blender mesh object

        self.context = None                                                         # 'Environment', 'Object', 'Composite'
        self.compositeKeepAlden = None
        self.gravity = None 
        self.monkeyTilt = 0                                                        # downward (0), perpendicular to horizon (1) 

        self.architecture = None                                                    # Blender mesh object
        self.floor = None                                                           # no floor (0), floor (1)
        self.ceiling = None                                                         # no ceiling (0), ceiling (1)
        self.wallL = None                                                           # no left wall (0), left wall (1)
        self.wallR = None                                                           # no right wall (0), right wall (1)
        self.wallB = None                                                           # no back wall (0), back wall (1)
        self.architectureThickness = None                                           # 2/100

        self.distance = None                                                        # in blender units, distance of structure
        self.structureMaterial = None                                               # string

        self.sky = None                                                             # Blender object
        self.cameraL = None                                                         # Blender object
        self.cameraR = None                                                         # Blender object
        self.cameraM = None
        self.fixationPointDepth = None
        self.sun = []                                                               # rotation of the sun in radians

        self.aperture = None

        self.materialToolkit = materialTool()
        self.scrubToolkit = scrubTool()
        self.massToolkit = massTool()
        self.physicsToolkit = physicsTool()
        self.deleteToolkit = deleteTool()


###
###     GRASS GRAVITY & ENVIRONMENT
###

class environmentConstructor:

    kind = 'Environment Constructor'

    def __init__(self,environmentSpec):

        self.enviroSpec = environmentSpec

    def __stereotypicalPeripherals(self):

        env = self.enviroSpec

        theta = math.pi/2 - NP.arctan(2*monkeyDistanceY/monkeyEyeDistance)
        phi = NP.arctan(monkeyDistanceY/monkeyDistanceZ)

        cameraL = self.__cameraInstance(-monkeyEyeDistance/2,-monkeyDistanceY,monkeyDistanceZ,1000,phi,0,-theta)
        cameraL.name = 'CameraL'
        env.cameraL = cameraL
        cameraR = self.__cameraInstance(monkeyEyeDistance/2,-monkeyDistanceY,monkeyDistanceZ,1000,phi,0,theta)
        cameraR.name = 'CameraR'
        env.cameraR = cameraR
        cameraM = self.__cameraInstance(0,-monkeyDistanceY,monkeyDistanceZ,1000,phi,0,0)
        cameraM.name = 'CameraM'
        env.cameraM = cameraM

        cameraL.data.show_limits = True
        cameraR.data.show_limits = True

        env.sky = self.__makeBasicSkyTexture()
        return  

    def tiltPeripherals(self):

        env = self.enviroSpec

        theta = math.pi/2 - NP.arctan(2*monkeyDistanceY/monkeyEyeDistance)

        sphereRadius = 0.15
        angleOfInterest = NP.arccos(monkeyDistanceZ/(desiredFocalLength*2))

        cameraL = self.__cameraInstance(-monkeyEyeDistance/2,-monkeyDistanceY,monkeyDistanceZ,1000,angleOfInterest,0,-theta)
        cameraL.name = 'CameraL'
        env.cameraL = cameraL
        cameraR = self.__cameraInstance(monkeyEyeDistance/2,-monkeyDistanceY,monkeyDistanceZ,1000,angleOfInterest,0,theta)
        cameraR.name = 'CameraR'
        env.cameraR = cameraR
        cameraM = self.__cameraInstance(0,-monkeyDistanceY,monkeyDistanceZ,1000,angleOfInterest,0,0)
        cameraM.name = 'CameraM'
        env.cameraM = cameraM

        cameraL.data.show_limits = True
        cameraR.data.show_limits = True

        env.sky = self.__makeBasicSkyTexture()
        return

    def __cameraInstance(self,x,y,z,clip,rx,ry,rz):

        # create camera
        camerasOrig = [c for c in scn.objects if c.name.startswith('Camera')]
        bpy.ops.object.camera_add(view_align=True, enter_editmode=False, location=(x,y,z), rotation=(rx,ry,rz))
        cameras = [c for c in scn.objects if c.name.startswith('Camera')]
        camera = [c for c in cameras if c not in camerasOrig][0]

        camera.data.type = 'PERSP'
        camera.data.sensor_fit = 'HORIZONTAL'
        camera.data.clip_end = clip
        camera.data.lens = lens
        camera.data.sensor_width = sensorWidth
        scn.camera = camera
        camera.data.show_guide = {'CENTER'}
        
        camera.data.keyframe_insert('lens',frame=0)
        #scn.use_denoising = True
        return camera

    def __makeBasicSkyTexture(self):

        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1.0, location=(0,0,0))
        skyEmpty = bpy.data.objects['Empty']
        skyEmpty.name = 'SkyEmpty'

        w = scn.world
        w.use_nodes = True

        sky = w.node_tree.nodes.new('ShaderNodeTexSky')
        sky.turbidity = 6.0
        sky.ground_albedo = 0.5
        sky.sun_direction = (0.0,-1.0,0.5)
        alpha = 20
        x = 1
        z = x*math.tan(alpha)
        sky.sun_direction = (x,-1.0,z)
        background = w.node_tree.nodes[1]
        background.inputs[1].default_value = 4.5
        mapping = w.node_tree.nodes.new('ShaderNodeMapping')
        mapping.vector_type = 'POINT'
        mapping.scale[0] = 1.0
        mapping.scale[1] = 1.0
        mapping.scale[2] = 1.0
        texCoord = w.node_tree.nodes.new('ShaderNodeTexCoord')
        texCoord.object = skyEmpty

        w.node_tree.links.new(sky.outputs[0],background.inputs[0])
        w.node_tree.links.new(mapping.outputs[0],sky.inputs[0])
        w.node_tree.links.new(texCoord.outputs[3],mapping.inputs[0])
        scn.update()

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = skyEmpty
        skyEmpty.select = True
        skyEmpty.rotation_euler = (0,0,0)
        skyEmpty.rotation_euler = (-10*math.pi/180,0,0)
        return skyEmpty

    def randomSunDirection(self):

        env = self.enviroSpec

        env.sun = random.sample(lightingOptions,1)[0]

        w = scn.world
        w.node_tree.nodes['Sky Texture'].sun_direction = (env.sun[0],env.sun[1],env.sun[2])
        return

    def changeSunDirection(self):

        env = self.enviroSpec

        w = scn.world
        w.node_tree.nodes['Sky Texture'].sun_direction = (env.sun[0],env.sun[1],env.sun[2])
        return

    def __triHorizon(self,backdrop=0):

        fov = 72/180*math.pi
        height = 60 # meters
        width = math.sin(fov/2)*height*2.3
        centerX = 0

        if backdrop:
            edges = []
            verts = [(centerX,-monkeyDistanceY*2,0),(centerX+width,-monkeyDistanceY*2+height,0),(centerX-width,-monkeyDistanceY*2+height,0)]
            faces = [(0,1,2)]

        else:
            edges = []
            verts = [(centerX,-monkeyDistanceY*2,0),(centerX+width,-monkeyDistanceY*2+height,0),(centerX-width,-monkeyDistanceY*2+height,0)]
            faces = [(0,1,2)]

        me = bpy.data.meshes.new('Horizon')
        me.from_pydata(verts,edges,faces)
        horizon = bpy.data.objects.new('Horizon', me) # generate horizon plane
        
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.link(horizon) # link horizon to scene
        scn.objects.active = horizon # make horizon active
        horizon.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=100)
        bpy.ops.mesh.faces_shade_smooth()
        bpy.ops.object.mode_set(mode='OBJECT')

        self.enviroSpec.massToolkit.makeRigidBody(horizon,'PASSIVE')

        if backdrop:

            bpy.context.scene.objects.active = horizon
            bpy.ops.object.select_all(action='DESELECT')
            horizon.select = True

            accessWP = [sv for sv in horizon.vertex_groups if sv.name.startswith('backdrop')]

            if len(accessWP) == 0:
                horizon.vertex_groups.new(name='backdrop')
                accessWP = [sv for sv in horizon.vertex_groups if sv.name.startswith('backdrop')]

            weightVertexGroup = accessWP[0]
            weightVerts = horizon.data.vertices

            backdropGaussianWidth = 100
            backdropGaussianCenter = 1-monkeyDistanceY*2+height # far end of horizon plane

            for vertex in weightVerts:
                weightVertexGroup.add(
                    [vertex.index],1/math.sqrt(backdropGaussianWidth*2*math.pi)*math.exp(-0.5*(vertex.co.y-backdropGaussianCenter)**2/backdropGaussianWidth),'REPLACE')

            bpy.ops.object.modifier_add(type='DISPLACE')
            backdropDisplace = horizon.modifiers['Displace']
            backdropDisplace.name = 'backdrop'   

            backdropTexture = bpy.data.textures.new('backdrop',type='NONE')
            backdropDisplace.texture = bpy.data.textures['backdrop']
            backdropDisplace.vertex_group = 'backdrop'
            backdropDisplace.strength = -1000
            backdropDisplace.mid_level = 1.0

            bpy.ops.object.modifier_apply(apply_as='DATA',modifier='backdrop')

        return horizon

    def tiltHorizon(self,backdrop=0):

        horizon = self.__triHorizon(backdrop=backdrop)
        return horizon

    def makeSecondHorizon(self):

        env = self.enviroSpec
        env.secondHorizon = self.__triHorizon()
        mat = env.materialToolkit.useNodes(env.secondHorizon)
        penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,env.horizonMaterial,True)
        bpy.data.particles[-1].hair_length = 1.0
        return

    def loadSecondHorizon(self,whichTilt,whichView):

        env = self.enviroSpec
        bpy.ops.import_scene.obj(filepath=materialResources+'SecondHorizons/tilt_'+str(whichTilt)+'_'+str(whichView)+'.obj')
        env.secondHorizon = [h for h in bpy.context.scene.objects if h.name.startswith('Horizon')][0]
        mat = env.materialToolkit.useNodes(env.secondHorizon)
        penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,env.horizonMaterial,True)
        bpy.data.particles[-1].hair_length = 1.0

        env.secondHorizon.cycles_visibility.shadow = False
        env.secondHorizon.cycles_visibility.diffuse = False
        return

    def orientToMesh(self,whichMesh):

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = whichMesh
        whichMesh.select = True

        focusLoc = whichMesh.matrix_world.translation
        self.orientTo(focusLoc)
        return

    def orientToClosestJunction(self,alden):

        junctionFocusLoc = self.findClosestJunction(alden)
        self.orientTo(junctionFocusLoc)
        return

    def findClosestJunction(self,alden):

        self.findBoneLocations(alden)

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.mesh
        alden.mesh.select = True

        focusLoc = alden.mesh.matrix_world.translation
        junctionDistances = [math.sqrt((focusLoc[0]-fj[0])**2+(focusLoc[1]-fj[1])**2+(focusLoc[2]-fj[2])**2) for fj in alden.juncEndPt]
        closestJunction = junctionDistances.index(min(junctionDistances))
        junctionFocusLoc = alden.juncEndPt[closestJunction]
        alden.fixationPoint = closestJunction+2
        return junctionFocusLoc

    def orientTo(self,focusLoc):

        env = self.enviroSpec

        for orientOb in [c for c in bpy.data.objects if c.name.startswith('Camera')]:#[env.cameraL,env.cameraR]:

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = orientOb
            orientOb.select = True

            orientLoc = orientOb.matrix_world.translation

            distDiffX = focusLoc[0]-orientLoc[0]
            distDiffY = focusLoc[1]-orientLoc[1]
            distDiffZ = focusLoc[2]-orientLoc[2]

            rotZ = -NP.arctan(distDiffX/distDiffY)
            rotX = math.pi/2 + NP.arctan(distDiffZ/(math.sqrt(distDiffY**2+distDiffX**2)))

            orientOb.rotation_euler[2] = rotZ
            orientOb.rotation_euler[0] = rotX

        # # correct stereoscopy
        # angleDiffZ = env.cameraR.rotation_euler[2] - env.cameraL.rotation_euler[2]
        # env.cameraR.rotation_euler[2] -= angleDiffZ/2
        # env.cameraL.rotation_euler[2] += angleDiffZ/2
        return

    def orientAsAppropriate(self,alden):

        if alden.fixationPoint == 0:
            self.orientToMesh(alden.mesh)

        elif alden.fixationPoint == 1:
            self.orientToClosestJunction(alden)

        else:
            self.findBoneLocations(alden)
            self.orientTo(alden.juncEndPt[alden.fixationPoint-2])

        return

    def aperture(self):

        env = self.enviroSpec

        for camera in [env.cameraL,env.cameraR,env.cameraM]:
            bpy.ops.mesh.primitive_cube_add(radius=1, view_align=False, enter_editmode=False, location=camera.location, rotation=(0,0,0))
            aperture = [p for p in scn.objects if p.name.startswith('Cube')][0]
            bpy.ops.transform.resize(value=(1,0.01,1),constraint_axis=(False, True, False))
            aperture.name = 'Aperture' + camera.name

            # size was 0.4 with original aspect ratio
            bpy.ops.mesh.primitive_uv_sphere_add(segments=100, ring_count=100, size=0.3, view_align=False, enter_editmode=False, location=camera.location, rotation=(0,0,0))
            hole = [s for s in scn.objects if s.name.startswith('Sphere')][0]
            hole.name = 'Hole'
            bpy.ops.object.shade_smooth()

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = aperture
            aperture.select = True
            
            bpy.ops.object.modifier_add(type='BOOLEAN')
            aperture.modifiers['Boolean'].object = hole
            aperture.modifiers['Boolean'].operation = 'DIFFERENCE'
            bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Boolean')

            env.deleteToolkit.deleteSingleObject(hole)
            
            aperture.rotation_euler = camera.rotation_euler
            aperture.rotation_euler[0] += math.pi/2

            distDown = 1
            aperture.location[0] += distDown * math.cos(math.pi/2-camera.rotation_euler[0]) * math.tan(-camera.rotation_euler[2])
            aperture.location[1] += distDown * math.cos(math.pi/2-camera.rotation_euler[0])
            aperture.location[2] -= distDown * math.sin(math.pi/2-camera.rotation_euler[0])

            aperture.cycles_visibility.shadow = False
            aperture.cycles_visibility.scatter = False
            aperture.cycles_visibility.transmission = False
            aperture.cycles_visibility.glossy = False
            aperture.cycles_visibility.diffuse = False

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = aperture
            aperture.select = True

            mat = bpy.data.materials.new('ApertureMat')
            mat.use_nodes = True
            mat.node_tree.nodes[1].inputs[0].default_value = (0.0,0.0,0.0,1.0)

            bpy.ops.object.material_slot_add()
            aperture.material_slots[0].material = mat
            bpy.ops.object.material_slot_assign()

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = camera
            camera.select = True
            aperture.select = True
            bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)

        return

    def gaussianOccluder(self):

        for camera in [self.enviroSpec.cameraL, self.enviroSpec.cameraR, self.enviroSpec.cameraM]:

            bpy.ops.mesh.primitive_plane_add(radius=0.5, location=camera.location, rotation=(0,0,0))
            occluder = [p for p in scn.objects if p.name.startswith('Plane')][0]
            bpy.ops.transform.resize(value=(1.333,1,1),constraint_axis=(True, False, False))
            occluder.name = 'Occluder' + camera.name

            occluder.rotation_euler = camera.rotation_euler

            distDown = 1
            occluder.location = camera.matrix_world * Vector((0,0,-distDown))

            occluder.cycles_visibility.shadow = False
            occluder.cycles_visibility.scatter = False
            occluder.cycles_visibility.transmission = False
            occluder.cycles_visibility.glossy = False
            occluder.cycles_visibility.diffuse = False

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = occluder
            occluder.select = True

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.subdivide(number_cuts=100)
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # do a gaussian color layers manipulation
            verts = occluder.data.vertices
            occluder.vertex_groups.new(name='Occluder')
            accessWP = [sv for sv in occluder.vertex_groups if sv.name.startswith('Occluder')]
            obVertexGroup = accessWP[0]

            for vertex in verts:
                effectiveX = (1-(vertex.co.x+0.5))*86
                whichWeightX = 5.828*math.exp(-((effectiveX-43.22)/19.49)**2) # horizontal

                effectiveY = (vertex.co.y-0.5)*65
                # whichWeightY = 6.334*math.exp(-((effectiveY+20.34)/18.68)**2) # vertical

                # difference between sight and projection 4 cm
                # want 2 cm above middle...
                whichWeightY = 6.334*math.exp(-((effectiveY+65/2-2)/18.68)**2) # vertical

                whichWeight = whichWeightX*whichWeightY/5.828

                # if whichWeight/7 > 0.9:
                #     obVertexGroup.add([vertex.index],1,'REPLACE')

                # else:
                #     obVertexGroup.add([vertex.index],0,'REPLACE')

                obVertexGroup.add([vertex.index],whichWeight/7,'REPLACE')

            occluder.data.vertex_colors.new('WeightColorOccluder')
            color_layer = occluder.data.vertex_colors[-1]
            ii = 0

            for poly in occluder.data.polygons: 

                vertInd = poly.vertices 
                vertIdent = [verts[v] for v in vertInd]

                for vert in vertIdent:
                    weight = vert.groups[0].weight
                    color_layer.data[ii].color = (weight,weight,weight,1.0)
                    ii += 1

            mat = bpy.data.materials.new('OccluderMat')
            mat.use_nodes = True

            diffuse = mat.node_tree.nodes[1]
            diffuse.inputs[0].default_value = (0.0,0.0,0.0,1.0)
            transparent = mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
            mixDiffuseTransparent = mat.node_tree.nodes.new('ShaderNodeMixShader')
            attribute = mat.node_tree.nodes.new('ShaderNodeAttribute')
            attribute.attribute_name = 'WeightColorOccluder'
            
            mat.node_tree.links.new(attribute.outputs[0],mixDiffuseTransparent.inputs[0])
            mat.node_tree.links.new(diffuse.outputs[0],mixDiffuseTransparent.inputs[2])
            mat.node_tree.links.new(transparent.outputs[0],mixDiffuseTransparent.inputs[1])
            mat.node_tree.links.new(mixDiffuseTransparent.outputs[0],mat.node_tree.nodes[0].inputs[0])

            bpy.ops.object.material_slot_add()
            occluder.material_slots[0].material = mat
            bpy.ops.object.material_slot_assign()

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = camera
            camera.select = True
            occluder.select = True
            bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)

        return 

    def fitFixationPointWholeObj(self,alden,fpMultiplier=1):

        env = self.enviroSpec
        self.orientAsAppropriate(alden)

        if alden.implantation:
            scn.update()
            vertsLocal = alden.mesh.data.vertices
            vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]

            zOptions = [v[2] for v in vertsGlobal]
            aldenSize = max(zOptions)-min(zOptions)
            alden.mesh.location[2] -= alden.implantation*aldenSize-bumpStrength

        self.findBoneLocations(alden)
        jpl = alden.juncEndPt[alden.fixationPoint-2]
        fp = self.makeTarget(jpl,fpMultiplier=2**alden.scaleShiftInDepth)

        mockCameraX = (env.cameraL.location[0]+env.cameraR.location[0])/2
        mockCameraY = (env.cameraL.location[1]+env.cameraR.location[1])/2
        mockCameraZ = (env.cameraL.location[2]+env.cameraR.location[2])/2

        rotMockCameraX = (env.cameraL.rotation_euler[0]+env.cameraR.rotation_euler[0])/2
        rotMockCameraY = (env.cameraL.rotation_euler[1]+env.cameraR.rotation_euler[1])/2
        rotMockCameraZ = (env.cameraL.rotation_euler[2]+env.cameraR.rotation_euler[2])/2

        env.cameraM.location = Vector((mockCameraX,mockCameraY,mockCameraZ))
        env.cameraM.rotation_euler = Euler((rotMockCameraX,rotMockCameraY,rotMockCameraZ))
        fp.rotation_euler = Euler((rotMockCameraX,rotMockCameraY,rotMockCameraZ))
        env.cameraM.data.show_limits = True
        env.cameraM.data.show_guide = {'CENTER'}

        finishedAdjustments = False
        scn.update()

        while not finishedAdjustments:
            print()
            rayCast = self.rayVisibility(mockCamera,Vector((jpl)),alden.mesh)
            fp.location = rayCast[0]
            visibleVertices = self.evaluateVisibility(alden.mesh)

            self.orientTo(fp.location)
            fp.rotation_euler = [m for m in mockCamera.rotation_euler]

            scn.update()
            allZmockCamera = []

            for i,v in enumerate(visibleVertices):
                visibleToCamera = mockCamera.matrix_world.inverted() * Vector((v))
                allZmockCamera.append(visibleToCamera[2])

            closestVisibleVertex = visibleVertices[allZmockCamera.index(max(allZmockCamera))]

            fpCamera = mockCamera.matrix_world.inverted() * Vector((fp.location))
            fpNew = Vector((fpCamera[0],fpCamera[1],max(allZmockCamera)))
            fp.location = mockCamera.matrix_world * fpNew

            desiredSeparation_h = desiredFocalLength*(2**alden.scaleShiftInDepth)                   # check desiredFocalLength compatibility
            env.fixationPointDepth = desiredSeparation_h

            raw = math.sqrt((mockCamera.location[2]-jpl[2])**2+(math.sqrt((mockCamera.location[0]-jpl[0])**2+(mockCamera.location[1]-jpl[1])**2))**2)
            shift_j = math.sqrt((fp.location[2]-jpl[2])**2+(math.sqrt((fp.location[0]-jpl[0])**2+(fp.location[1]-jpl[1])**2))**2)
            effective_h = raw-shift_j
            print('EFFECTIVE FIX PT DISTANCE: ',round(effective_h,2))

            if round(effective_h,2) == desiredSeparation_h:
                finishedAdjustments = True

            else:
                new_h = desiredSeparation_h + shift_j
                projectionXY = math.sqrt((new_h)**2-(mockCamera.location[2]-jpl[2])**2)
                projectionXY_old = math.sqrt((raw)**2-(mockCamera.location[2]-jpl[2])**2)

                thetaXY = -math.atan((jpl[0]-mockCameraX)/(jpl[1]-mockCameraY))
                yComp = projectionXY * math.cos(thetaXY)
                yComp_old = projectionXY_old * math.cos(thetaXY)
                xComp = projectionXY * math.sin(thetaXY)
                xComp_old = projectionXY_old * math.sin(thetaXY)
                thetaZ = math.asin((mockCamera.location[2]-jpl[2])/new_h)

                alden.mesh.location[0] += xComp-xComp_old
                alden.mesh.location[1] += yComp-yComp_old
                fp.location[0] += xComp-xComp_old
                fp.location[1] += yComp-yComp_old

                self.findBoneLocations(alden)
                jpl = alden.juncEndPt[alden.fixationPoint-2]
                self.orientTo(jpl)

        self.orientTo(fp.location)

        if alden.implantation:
            alden.mesh.location[2] += alden.implantation*aldenSize-bumpStrength
        
        print()
        return fp

    def fitFixationPoint(self,alden,fpMultiplier=1):

        env = self.enviroSpec
        self.orientAsAppropriate(alden)

        if not alden.optical and alden.material in ['aluminum_foil01','hedgehog01','fur01','paperOG']:
            compensator = 0.05

        elif alden.scaleShiftInDepth > 1:
            compensator = 0.05

        else:
            compensator = 0

        if env.context == 'Composite':

            if alden.implantation and alden.location in [0,5,8,9,13,16]:
                scn.update()
                vertsLocal = alden.mesh.data.vertices
                vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]

                zOptions = [v[2] for v in vertsGlobal]
                aldenSize = max(zOptions)-min(zOptions)
                alden.mesh.location[2] -= alden.implantation*aldenSize-bumpStrength

        else:

            if alden.implantation:
                scn.update()
                vertsLocal = alden.mesh.data.vertices
                vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]

                zOptions = [v[2] for v in vertsGlobal]
                aldenSize = max(zOptions)-min(zOptions)
                alden.mesh.location[2] -= alden.implantation*aldenSize-bumpStrength

        mockCameraX = (env.cameraL.location[0]+env.cameraR.location[0])/2
        mockCameraY = (env.cameraL.location[1]+env.cameraR.location[1])/2
        mockCameraZ = (env.cameraL.location[2]+env.cameraR.location[2])/2

        rotMockCameraX = (env.cameraL.rotation_euler[0]+env.cameraR.rotation_euler[0])/2
        rotMockCameraY = (env.cameraL.rotation_euler[1]+env.cameraR.rotation_euler[1])/2
        rotMockCameraZ = (env.cameraL.rotation_euler[2]+env.cameraR.rotation_euler[2])/2

        env.cameraM.location = Vector((mockCameraX,mockCameraY,mockCameraZ))
        env.cameraM.rotation_euler = Euler((rotMockCameraX,rotMockCameraY,rotMockCameraZ))
        env.cameraM.data.show_limits = True
        env.cameraM.data.show_guide = {'CENTER'}
        mockCamera = env.cameraM

        self.findBoneLocations(alden)
        jpl = alden.juncEndPt[alden.fixationPoint-2]

        fp = self.makeTarget(jpl,fpMultiplier=2**alden.scaleShiftInDepth)
        fp.rotation_euler = Euler((rotMockCameraX,rotMockCameraY,rotMockCameraZ))
        previousScaling = 2**alden.scaleShiftInDepth
        
        finishedAdjustments = False
        scn.update()

        try:
            previousEffectiveFixPt = None
            previousEffectiveFixPt2Back = None

            while not finishedAdjustments:
                # print()
                rayCast = self.rayVisibility(mockCamera,Vector((jpl)),alden.mesh)
                fp.location = rayCast[0]
                visibleVertices = self.evaluateVisibility(alden.mesh)

                scn.update()
                size = len(visibleVertices)
                kd = mathutils.kdtree.KDTree(size)

                for i,v in enumerate(visibleVertices):
                    visibleToCamera = mockCamera.matrix_world.inverted() * Vector((v))
                    vertex = Vector((visibleToCamera[0],visibleToCamera[1],0))
                    kd.insert(vertex,i)

                kd.balance()
                finishedCorrection = False

                while not finishedCorrection:
                    scn.update()
                    fpGlobal = [fp.matrix_world * v.co for v in fp.data.vertices]
                    correction = 0
                    diffIndices = []
                    howManyReferences = 0

                    for i,v in enumerate(fpGlobal):
                        fpGlobalToCamera = mockCamera.matrix_world.inverted() * Vector((v))
                        co,index,dist = kd.find(Vector((fpGlobalToCamera[0],fpGlobalToCamera[1],0)))

                        if index not in diffIndices:
                            diffIndices.append(index)
                            howManyReferences+=1

                        # visible vertex loc in camera space
                        zSurface = mockCamera.matrix_world.inverted() * Vector((visibleVertices[index]))    # world coordinates to local camera coordinates

                        # plane pt loc in camera space
                        zFixation = mockCamera.matrix_world.inverted() * Vector((v))                        # world coordinates to local camera coordinates

                        if zSurface[2]-zFixation[2] > correction:                                           # compare distance along camera vector
                            correction = zSurface[2]-zFixation[2]

                    scn.update()

                    newLocationLocal =  mockCamera.matrix_world.inverted() * Vector((fp.location)) + Vector((0,0,correction)) + Vector((0,0,compensator))
                    newLocationGlobal = mockCamera.matrix_world * newLocationLocal
                    fp.location = newLocationGlobal

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.scene.objects.active = fp
                    fp.select = True

                    newScaling = -newLocationLocal[2]/desiredFocalLength
                    # print(newScaling)
                    bpy.ops.transform.resize(value=(newScaling/previousScaling,newScaling/previousScaling,newScaling/previousScaling),constraint_axis=(True, True, True))
                    previousScaling = newScaling

                    # print('NUM REFERENCE INDICES: ',howManyReferences)
                    # print('CORRECTION: ',correction)
                    
                    if round(correction,4) == 0:
                        finishedCorrection = True

                if env.context != 'Composite' and alden.mesh:
                    desiredSeparation_h = desiredFocalLength*(2**alden.scaleShiftInDepth)                   # check desiredFocalLength compatibility
                    env.fixationPointDepth = desiredSeparation_h

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.scene.objects.active = fp
                    fp.select = True

                    newScaling = 2**alden.scaleShiftInDepth
                    # print(newScaling)
                    bpy.ops.transform.resize(value=(newScaling/previousScaling,newScaling/previousScaling,newScaling/previousScaling),constraint_axis=(True, True, True))
                    previousScaling = newScaling

                    raw = math.sqrt((mockCamera.location[2]-jpl[2])**2+(math.sqrt((mockCamera.location[0]-jpl[0])**2+(mockCamera.location[1]-jpl[1])**2))**2)
                    shift_j = math.sqrt((fp.location[2]-jpl[2])**2+(math.sqrt((fp.location[0]-jpl[0])**2+(fp.location[1]-jpl[1])**2))**2)
                    effective_h = raw-shift_j
                    print('EFFECTIVE FIX PT DISTANCE: ',round(effective_h,2))
                    print('DESIRED SEPARATION: ',desiredSeparation_h)

                    if round(effective_h,2) == desiredSeparation_h:
                        finishedAdjustments = True

                    elif previousEffectiveFixPt2Back == round(effective_h,2):
                        finishedAdjustments = True

                    else:
                        new_h = desiredSeparation_h + shift_j
                        projectionXY = math.sqrt((new_h)**2-(mockCamera.location[2]-jpl[2])**2)
                        projectionXY_old = math.sqrt((raw)**2-(mockCamera.location[2]-jpl[2])**2)

                        thetaXY = -math.atan((jpl[0]-mockCameraX)/(jpl[1]-mockCameraY))
                        yComp = projectionXY * math.cos(thetaXY)
                        yComp_old = projectionXY_old * math.cos(thetaXY)
                        xComp = projectionXY * math.sin(thetaXY)
                        xComp_old = projectionXY_old * math.sin(thetaXY)
                        thetaZ = math.asin((mockCamera.location[2]-jpl[2])/new_h)

                        alden.mesh.location[0] += xComp-xComp_old
                        alden.mesh.location[1] += yComp-yComp_old
                        fp.location[0] += xComp-xComp_old
                        fp.location[1] += yComp-yComp_old

                        self.findBoneLocations(alden)
                        jpl = alden.juncEndPt[alden.fixationPoint-2]
                        self.orientTo(jpl)

                    previousEffectiveFixPt2Back = previousEffectiveFixPt
                    previousEffectiveFixPt = round(effective_h,2)

                else:
                    env.fixationPointDepth = desiredFocalLength
                    finishedAdjustments = True

        except Exception as e:
            # save to file the error that caused this???

            try:
                logfile = 'logfile_random_spec_'+str(int(time.time()))+'.log'
                open(logfile, 'a').close()
                old = os.dup(1)
                sys.stdout.flush()
                os.close(1)
                os.open(logfile, os.O_WRONLY)
                print(e)
                os.close(1)
                os.dup(old)
                os.close(old)

            except:
                pass

            self.fitFixationPointFixedDepth(alden)

        self.orientTo(fp.location)

        if env.context == 'Composite':

            if alden.implantation and alden.location in [0,5,8,9,13,16]:
                alden.mesh.location[2] += alden.implantation*aldenSize-bumpStrength

        else:

            if alden.implantation:
                alden.mesh.location[2] += alden.implantation*aldenSize-bumpStrength
        
        # print()
        #after implantation need a raycast to determine whether pt is below ground...
        
        return fp

    def fitFixationPointSpecific(self,distance):

        env = self.enviroSpec

        # camera already pointed in correct direction
        mockCameraX = (env.cameraL.location[0]+env.cameraR.location[0])/2
        mockCameraY = (env.cameraL.location[1]+env.cameraR.location[1])/2
        mockCameraZ = (env.cameraL.location[2]+env.cameraR.location[2])/2

        rotMockCameraX = (env.cameraL.rotation_euler[0]+env.cameraR.rotation_euler[0])/2
        rotMockCameraY = (env.cameraL.rotation_euler[1]+env.cameraR.rotation_euler[1])/2
        rotMockCameraZ = (env.cameraL.rotation_euler[2]+env.cameraR.rotation_euler[2])/2

        env.cameraM.location = Vector((mockCameraX,mockCameraY,mockCameraZ))
        env.cameraM.rotation_euler = Euler((rotMockCameraX,rotMockCameraY,rotMockCameraZ))
        env.cameraM.data.show_limits = True
        env.cameraM.data.show_guide = {'CENTER'}
        mockCamera = env.cameraM

        camDist = mockCamera.matrix_world * Vector((0,0,-distance))
        fp = self.makeTarget(camDist)
        fp.rotation_euler = Euler((rotMockCameraX,rotMockCameraY,rotMockCameraZ))

        newScaling = distance/desiredFocalLength
        bpy.ops.transform.resize(value=(newScaling,newScaling,newScaling),constraint_axis=(True, True, True))
        self.orientTo(fp.location)
        env.fixationPointDepth = distance
        print('FIX PT SPECIFIED DEPTH: '+ str(distance))

        return fp

    def fitFixationPointObjectless(self,otherMesh=None):

        env = self.enviroSpec

        # camera already pointed in correct direction
        mockCameraX = (env.cameraL.location[0]+env.cameraR.location[0])/2
        mockCameraY = (env.cameraL.location[1]+env.cameraR.location[1])/2
        mockCameraZ = (env.cameraL.location[2]+env.cameraR.location[2])/2

        rotMockCameraX = (env.cameraL.rotation_euler[0]+env.cameraR.rotation_euler[0])/2
        rotMockCameraY = (env.cameraL.rotation_euler[1]+env.cameraR.rotation_euler[1])/2
        rotMockCameraZ = (env.cameraL.rotation_euler[2]+env.cameraR.rotation_euler[2])/2

        env.cameraM.location = Vector((mockCameraX,mockCameraY,mockCameraZ))
        env.cameraM.rotation_euler = Euler((rotMockCameraX,rotMockCameraY,rotMockCameraZ))
        env.cameraM.data.show_limits = True
        env.cameraM.data.show_guide = {'CENTER'}
        mockCamera = env.cameraM

        # look for horizon *and* architecture
        fp = self.makeTarget(Vector((0,0,0)))
        fp.rotation_euler = Euler((rotMockCameraX,rotMockCameraY,rotMockCameraZ))
        previousScaling = 1

        rayCast = self.rayVisibility(mockCamera,mockCamera.matrix_world*Vector((0,0,-20)),env.horizon)

        if env.architecture:
            rayCastArchi = self.rayVisibility(mockCamera,mockCamera.matrix_world*Vector((0,0,-20)),env.architecture)

        else:
            rayCastArchi = (None,None,None,None)

        if (None in rayCast) and (None in rayCastArchi) and (None in [otherMesh]):
            # unless an architecture is present, put fixation point at "infinite distance"
            fp.location = mockCamera.matrix_world*Vector((0,0,-60))

            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = fp
            fp.select = True

            newScaling = 60/desiredFocalLength
            # print(newScaling)
            bpy.ops.transform.resize(value=(newScaling/previousScaling,newScaling/previousScaling,newScaling/previousScaling),constraint_axis=(True, True, True))
            previousScaling = newScaling
            env.fixationPointDepth = 60

        else:

            if None not in rayCast:
                fp.location = rayCast[0]
                camDist = mockCamera.matrix_world.inverted() * Vector((rayCast[0]))
                whichMesh = env.horizon

            if env.architecture:

                if None not in rayCastArchi:
                    camArchi = mockCamera.matrix_world.inverted() * Vector((rayCastArchi[0]))

                    if None not in rayCast:
                        camHoriz = mockCamera.matrix_world.inverted() * Vector((rayCast[0]))

                        if camArchi[2] >= camHoriz[2]:
                            fp.location = rayCastArchi[0]
                            camDist = camArchi
                            whichMesh = env.architecture

                    else:
                        fp.location = rayCastArchi[0]
                        camDist = camArchi
                        whichMesh = env.architecture

            if otherMesh:
                rayCastOther = self.rayVisibility(mockCamera,mockCamera.matrix_world*Vector((0,0,-20)),otherMesh)

                if None not in rayCastOther:
                    camOther = mockCamera.matrix_world.inverted() * Vector((rayCastOther[0]))

                    if camOther[2] >= camDist[2]:
                        fp.location = rayCastOther[0]
                        camDist = camOther
                        whichMesh = otherMesh

            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = fp
            fp.select = True

            newScaling = -camDist[2]/desiredFocalLength
            # print(newScaling)
            bpy.ops.transform.resize(value=(newScaling/previousScaling,newScaling/previousScaling,newScaling/previousScaling),constraint_axis=(True, True, True))
            previousScaling = newScaling

            finishedAdjustments = False
            scn.update()

            while not finishedAdjustments:
                verts = [fp.matrix_world * v.co for v in fp.data.vertices]
                correction = 0

                for vert in verts:
                    rayCast = self.rayVisibilityCustom(mockCamera,Vector((vert)),(mockCamera.location-mockCamera.matrix_world*Vector((0,0,-20))).normalized(),whichMesh)

                    if None not in rayCast:
                        zSurface = mockCamera.matrix_world.inverted() * Vector((rayCast[0]))
                        zFixation = mockCamera.matrix_world.inverted() * Vector((vert))

                        if zSurface[2]-zFixation[2] > correction:                                           # compare distance along camera vector
                            correction = zSurface[2]-zFixation[2]

                scn.update()
                # print('CORRECTION: ',correction)

                newLocationLocal =  mockCamera.matrix_world.inverted() * Vector((fp.location)) + Vector((0,0,correction))
                newLocationGlobal = mockCamera.matrix_world * newLocationLocal
                fp.location = newLocationGlobal

                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.scene.objects.active = fp
                fp.select = True

                newScaling = -newLocationLocal[2]/desiredFocalLength
                bpy.ops.transform.resize(value=(newScaling/previousScaling,newScaling/previousScaling,newScaling/previousScaling),constraint_axis=(True, True, True))
                previousScaling = newScaling
                # print(newScaling)

                if round(correction,4) == 0:
                    finishedAdjustments = True
                    compensator = 0.01
                    newLocationLocal =  mockCamera.matrix_world.inverted() * Vector((fp.location)) + Vector((0,0,compensator))
                    newLocationGlobal = mockCamera.matrix_world * newLocationLocal
                    fp.location = newLocationGlobal
                    env.fixationPointDepth = -newLocationLocal[2]

        print('OBJECTLESS FIX PT DISTANCE: '+ str(round(env.fixationPointDepth,2)))
        self.orientTo(fp.location)
        return fp

    def fitFixationPointFixedDepth(self,alden):

        env = self.enviroSpec

        unfinished = True
        fp = self.makeTarget(Vector((0,0,0)))

        if alden.implantation and alden.location in [0,5,8,9,13,16]:
            scn.update()
            vertsLocal = alden.mesh.data.vertices
            vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]

            zOptions = [v[2] for v in vertsGlobal]
            aldenSize = max(zOptions)-min(zOptions)
            alden.mesh.location[2] -= alden.implantation*aldenSize-bumpStrength

        self.findBoneLocations(alden)
        jpl = alden.juncEndPt[alden.fixationPoint-2]
        self.orientTo(jpl)

        mockCameraX = (env.cameraL.location[0]+env.cameraR.location[0])/2
        mockCameraY = (env.cameraL.location[1]+env.cameraR.location[1])/2
        mockCameraZ = (env.cameraL.location[2]+env.cameraR.location[2])/2

        rotMockCameraX = (env.cameraL.rotation_euler[0]+env.cameraR.rotation_euler[0])/2
        rotMockCameraY = (env.cameraL.rotation_euler[1]+env.cameraR.rotation_euler[1])/2
        rotMockCameraZ = (env.cameraL.rotation_euler[2]+env.cameraR.rotation_euler[2])/2

        env.cameraM.location = Vector((mockCameraX,mockCameraY,mockCameraZ))
        env.cameraM.rotation_euler = Euler((rotMockCameraX,rotMockCameraY,rotMockCameraZ))
        env.cameraM.data.show_limits = True
        env.cameraM.data.show_guide = {'CENTER'}
        mockCamera = env.cameraM

        fp.location = mockCamera.matrix_world * Vector((0,0,-desiredFocalLength))
        fp.rotation_euler = Euler((rotMockCameraX,rotMockCameraY,rotMockCameraZ))

        self.orientTo(fp.location)

        aldenVertsGlobal = [alden.mesh.matrix_world * v.co for v in alden.mesh.data.vertices]
        planeVertsGlobal = [fp.matrix_world * v.co for v in fp.data.vertices]

        yTranslate = 0

        for aldenVert in aldenVertsGlobal:

            for planeVert in planeVertsGlobal:

                if (planeVert[1]-aldenVert[1]) > yTranslate:
                    yTranslate = planeVert[1]-aldenVert[1]


        if compositeCompensatoryRot and env.context == 'Composite':

            # rotation to focus on center
            aldenLocHolder = alden.location
            tempMeshLoc = [l for l in alden.mesh.location]
            alden.location = 0

            enclosConstructor = enclosureConstructor(self.enviroSpec)
            shifts = enclosConstructor.calculateCompositeShifts(alden)
            alden.location = aldenLocHolder

            compositeEmpty = bpy.data.objects['CompositeShiftEmpty']

            distDiffXtoCenter = (alden.mesh.location[0]+shifts[0])-compositeEmpty.matrix_world.translation[0]
            distDiffYtoCenter = (alden.mesh.location[1]+shifts[1])-compositeEmpty.matrix_world.translation[1]
            distDiffZtoCenter = (alden.mesh.location[2]+shifts[2])-compositeEmpty.matrix_world.translation[2]

            rotXtoCenter = math.atan(distDiffZtoCenter/(math.sqrt(distDiffYtoCenter**2+distDiffXtoCenter**2)))
            rotZtoCenter = -math.atan(distDiffXtoCenter/distDiffYtoCenter)

            alden.mesh.location = Vector((tempMeshLoc))
            alden.mesh.location[1] += yTranslate

            # rotation to focus on shifted location
            distDiffX = (alden.mesh.location[0])-compositeEmpty.matrix_world.translation[0]
            distDiffY = (alden.mesh.location[1])-compositeEmpty.matrix_world.translation[1]
            distDiffZ = (alden.mesh.location[2])-compositeEmpty.matrix_world.translation[2]

            rotX = math.atan(distDiffZ/(math.sqrt(distDiffY**2+distDiffX**2)))
            rotZ = -math.atan(distDiffX/distDiffY)

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = compositeEmpty
            compositeEmpty.select = True
            alden.mesh.select = True
            bpy.ops.object.parent_set(type='OBJECT')

            # difference between rotation to focus on center and new rotation necessary
            compositeEmpty.rotation_euler[2] = rotZ - rotZtoCenter
            compositeEmpty.rotation_euler[0] = rotX - rotXtoCenter

            # remove parent
            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = alden.mesh
            alden.mesh.select = True
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

            shifts = enclosConstructor.calculateCompositeShifts(alden)
            alden.mesh.location += Vector((shifts[0],shifts[1],shifts[2]))

            alden.mesh.location[1] += yTranslate

            if alden.implantation and alden.location in [0,5,8,9,13,16]:
                scn.update()
                vertsLocal = alden.mesh.data.vertices
                vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]

                zOptions = [v[2] for v in vertsGlobal]
                aldenSize = max(zOptions)-min(zOptions)
                alden.mesh.location[2] -= alden.implantation*aldenSize-bumpStrength

        else:
            alden.mesh.location[1] += yTranslate

        self.findBoneLocations(alden)
        jpl = alden.juncEndPt[alden.fixationPoint-2]
        self.orientTo(jpl)

        fp.location = mockCamera.matrix_world * Vector((0,0,-desiredFocalLength))
        fp.rotation_euler = Euler((rotMockCameraX,rotMockCameraY,rotMockCameraZ))
        self.orientTo(fp.location)
        env.fixationPointDepth = desiredFocalLength
        print('FIX PT FIXED DEPTH: '+ str(desiredFocalLength))

        if alden.implantation and alden.location in [0,5,8,9,13,16]:
            alden.mesh.location[2] += alden.implantation*aldenSize-bumpStrength

        return fp

    def makeTarget(self,point,fpMultiplier=1):

        env = self.enviroSpec

        fps = [p for p in bpy.data.objects if p.name.startswith('FixationPoint')]

        if len(fps) == 0:
            bpy.ops.mesh.primitive_plane_add(radius=0.02/4*fpMultiplier, location=(point[0],point[1],point[2]), rotation=(0,0,0)) # was 0.02, then 0.02/2
            fp = [b for b in scn.objects if b.name.startswith('Plane')][0]
            fp.name = 'FixationPoint' 

        else:
            fp = bpy.data.objects['FixationPoint']
            fp.location = Vector((point[0],point[1],point[2]))
            fp.rotation_euler = Euler((0,0,0))

        fp.cycles_visibility.scatter = False
        fp.cycles_visibility.transmission = False
        fp.cycles_visibility.shadow = False
        fp.cycles_visibility.diffuse = False
        fp.cycles_visibility.glossy = False
        fp.cycles_visibility.camera = True

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = fp
        fp.select = True

        if len(fps) == 0:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.subdivide(number_cuts=10)
            bpy.ops.object.mode_set(mode='OBJECT')

        mat = bpy.data.materials.new('ApertureMat')
        mat.use_nodes = True
        emission = mat.node_tree.nodes.new('ShaderNodeEmission')
        # emission.inputs[0].default_value = (1.0,1.0,0.0,1.0)
        emission.inputs[0].default_value = (57/255,255/255,20/255,1.0)
        mat.node_tree.links.new(emission.outputs[0],mat.node_tree.nodes[0].inputs[0])

        bpy.ops.object.material_slot_add()
        fp.material_slots[0].material = mat
        bpy.ops.object.material_slot_assign()
        return fp

    def rayVisibility(self,camera,point,whichMesh):

        env = self.enviroSpec
        scn.update()

        cam2D = world_to_camera_view(bpy.context.scene,camera,whichMesh.location)
        worldLoc = [whichMesh.matrix_world * v.co for v in whichMesh.data.vertices]
        bvh = BVHTree.FromPolygons(worldLoc,[p.vertices for p in whichMesh.data.polygons])
        rayCast = bvh.ray_cast(camera.location,(point-camera.location).normalized())
        return rayCast

    def rayVisibilityCustom(self,camera,origin,direction,whichMesh):

        env = self.enviroSpec
        scn.update()

        cam2D = world_to_camera_view(bpy.context.scene,camera,whichMesh.location)
        worldLoc = [whichMesh.matrix_world * v.co for v in whichMesh.data.vertices]
        bvh = BVHTree.FromPolygons(worldLoc,[p.vertices for p in whichMesh.data.polygons])
        rayCast = bvh.ray_cast(origin,direction)
        return rayCast

    def evaluateVisibility(self,whichMesh):

        env = self.enviroSpec

        # derived from/courtesy "lemon," Blender Stack Exchange:
        # https://blender.stackexchange.com/questions/77607/how-to-get-the-3d-coordinates-of-the-visible-vertices-in-a-rendered-image-in-ble#77747
        limit = 0.0001

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = whichMesh
        whichMesh.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        worldLoc = [whichMesh.matrix_world * v.co for v in whichMesh.data.vertices]
        bvh = BVHTree.FromPolygons(worldLoc,[p.vertices for p in whichMesh.data.polygons])

        visible = [None for ind in range(len(worldLoc))]

        for ind,v in enumerate(worldLoc):

            for camera in [env.cameraL,env.cameraR]:
                cam2D = world_to_camera_view(bpy.context.scene,camera,v)
                rayCast = bvh.ray_cast(camera.location,(v-camera.location).normalized())

                if rayCast[0] and (v - rayCast[0]).length < limit:
                    visible[ind] = 1
                    whichMesh.data.vertices[ind].select = True

                else:
                    if visible[ind] != 1:
                        visible[ind] = 0
                        whichMesh.data.vertices[ind].select = False

        visibleVertices = [worldLoc[ind] for ind in range(len(visible)) if visible[ind] == 1]
        return visibleVertices

    def randomEnvironmentConstruct(self):

        env = self.enviroSpec

        env.horizon = self.__triHorizon()
        mat = env.materialToolkit.useNodes(env.horizon)

        env.horizonMaterial = random.sample(horizonGrassMaterialOptions,1)[0]
        penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,env.horizonMaterial,True)

        self.__stereotypicalPeripherals()
        self.randomSunDirection()

        aperture = random.randint(0,1)
        env.aperture = aperture
        env.aperture = 0

        # if env.aperture:
        #     self.__aperture()

        return

    def assembleEnvironment(self):

        env = self.enviroSpec

        env.horizon = self.__triHorizon(backdrop=0)
        mat = env.materialToolkit.useNodes(env.horizon)
        penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,env.horizonMaterial,True)

        self.__stereotypicalPeripherals()
        self.changeSunDirection()

        # env.aperture = 0

        # if env.aperture:
        #     self.__aperture()

        return

    def invisibleAssembleEnvironment(self):

        self.enviroSpec.horizon = self.__triHorizon()
        self.__stereotypicalPeripherals()
        return

    def randomTiltSlantGrassGravity(self):

        env = self.enviroSpec

        # env.horizonTilt = random.sample(horizonTiltOptions,1)[0] ###!
        env.horizonTilt = (random.random()*2-1)*22.5*math.pi/180
        env.horizonSlant = random.sample(horizonSlantOptions,1)[0]
        env.gravity = random.randint(0,1)

        if env.horizonMaterial not in horizonGrassMaterialOptions:
            env.horizonMaterial = random.sample(horizonGrassMaterialOptions,1)[0]
            env.deleteToolkit.deleteSingleObjectMaterials(env.horizon)
            mat = env.materialToolkit.useNodes(env.horizon)
            penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,env.horizonMaterial,True)

        self.tiltSlantGrassGravity()
        return

    def tiltSlantGrassGravity(self):

        self.grassGravity()
        self.tiltSlantScene()
        return

    def grassGravity(self,secondHorizon=0):

        env = self.enviroSpec

        plant1 = [p for p in scn.objects if p.name.startswith('Plant1')][0:4]
        plant2 = [p for p in scn.objects if p.name.startswith('Plant2')][0:4]
        grass = plant1 + plant2
        particles = bpy.data.particles['scrub']
        particles.hair_length = 0#4.0

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = grass[0]

        # if no gravity and no second horizon, rotate
        # if no gravity and second horizon, rotate
        # if gravity and no second horizon
        # if gravity and second horizon, rotate

        if secondHorizon:

            for clump in grass:
                # print(clump.name)
                clump.select = True

            bpy.ops.transform.rotate(value=-math.pi/2,axis=(1,0,0),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')
            bpy.ops.object.transform_apply(rotation=True)

        else:

            if not env.gravity and not env.secondHorizon:

                for clump in grass:
                    clump.select = True

                x = env.cameraM.matrix_world[0][2]
                y = env.cameraM.matrix_world[1][2]
                z = env.cameraM.matrix_world[2][2]
                bpy.ops.transform.rotate(value=env.horizonTilt,axis=(x,y,z),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')
                bpy.ops.transform.rotate(value=env.horizonSlant,axis=(1,0,0),constraint_axis=(True,False,False),constraint_orientation='GLOBAL')
                bpy.ops.object.transform_apply(rotation=True)

        return

    def tiltSlantScene(self):

        env = self.enviroSpec

        # 1. rotate scene about global x-axis (slant)
        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1.0, view_align=False, location=(0, env.cameraL.location[1], 0))
        slantEmpty = [e for e in scn.objects if e.name.startswith('Empty')][0]
        slantEmpty.name = 'Slant'

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = slantEmpty
        slantEmpty.select = True
        env.horizon.select = True
        bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = slantEmpty
        slantEmpty.select = True
        bpy.ops.transform.rotate(value=env.horizonSlant,axis=(1,0,0),constraint_axis=(True,False,False),constraint_orientation='GLOBAL')

        # 2. rotate scene about (0,y,z) of camera rotation (tilt)
        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1.0, view_align=False, location=(0, env.cameraL.location[1], env.cameraL.location[2]))
        tiltEmpty = [e for e in scn.objects if e.name.startswith('Empty')][0]
        tiltEmpty.name = 'Tilt'

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = tiltEmpty
        tiltEmpty.select = True
        slantEmpty.select = True
        bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = tiltEmpty
        tiltEmpty.select = True

        x = env.cameraM.matrix_world[0][2]
        y = env.cameraM.matrix_world[1][2]
        z = env.cameraM.matrix_world[2][2]
        bpy.ops.transform.rotate(value=env.horizonTilt,axis=(x,y,z),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')

        # 3. rotate the sky correspondingly
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = env.sky
        env.sky.select = True
        bpy.ops.transform.rotate(value=env.horizonSlant,axis=(1,0,0),constraint_axis=(True,False,False),constraint_orientation='GLOBAL')
        bpy.ops.transform.rotate(value=env.horizonTilt,axis=(x,y,z),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')
        return

    def slantScene(self):

        env = self.enviroSpec

        # 1. rotate scene about global x-axis (slant)
        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1.0, view_align=False, location=(0, env.cameraL.location[1], 0))
        slantEmpty = [e for e in scn.objects if e.name.startswith('Empty')][0]
        slantEmpty.name = 'Slant'

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = slantEmpty
        slantEmpty.select = True
        env.horizon.select = True
        bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = slantEmpty
        slantEmpty.select = True
        bpy.ops.transform.rotate(value=env.horizonSlant,axis=(1,0,0),constraint_axis=(True,False,False),constraint_orientation='GLOBAL')

        # 3. rotate the sky correspondingly
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = env.sky
        env.sky.select = True
        bpy.ops.transform.rotate(value=env.horizonSlant,axis=(1,0,0),constraint_axis=(True,False,False),constraint_orientation='GLOBAL')

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = env.horizon
        env.horizon.select = True
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        scn.update()
        return

    def tiltScene(self):

        env = self.enviroSpec

        # 1. rotate scene about (0,y,z) of camera rotation (tilt)
        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1.0, view_align=False, location=(0, env.cameraL.location[1], env.cameraL.location[2]))
        tiltEmpty = [e for e in scn.objects if e.name.startswith('Empty')][0]
        tiltEmpty.name = 'Tilt'

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = tiltEmpty
        tiltEmpty.select = True
        env.horizon.select = True
        bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = tiltEmpty
        tiltEmpty.select = True

        x = env.cameraM.matrix_world[0][2]
        y = env.cameraM.matrix_world[1][2]
        z = env.cameraM.matrix_world[2][2]
        bpy.ops.transform.rotate(value=env.horizonTilt,axis=(x,y,z),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')

        # 2. rotate the sky correspondingly
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = env.sky
        env.sky.select = True
        bpy.ops.transform.rotate(value=env.horizonTilt,axis=(x,y,z),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = env.horizon
        env.horizon.select = True
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        scn.update()
        return

    def implantStimulus(self,alden):

        scn.objects.active = alden.mesh
        bpy.ops.object.select_all(action='DESELECT')
        alden.mesh.select = True

        if alden.implantation == 0:                                                # not buried
            return

        else:
            scn.update()
            vertsLocal = alden.mesh.data.vertices
            vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]
            zOptions = [v[2] for v in vertsGlobal]
            aldenSize = max(zOptions)-min(zOptions)
            alden.mesh.location[2] -= min(zOptions)
            alden.mesh.location[2] -= alden.implantation*aldenSize

        scn.update()
        vertsLocal = alden.mesh.data.vertices
        vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]

        underGround = [(v[0],v[1]) for v in vertsGlobal if v[2] <= 0.0]
        size = len(underGround)
        kd = mathutils.kdtree.KDTree(size)

        for i,v in enumerate(underGround):
            vertex = Vector((v[0],v[1],0.0))
            kd.insert(vertex,i)

        kd.balance()

        env = self.enviroSpec
        env.scrubToolkit.bumpWeightPaint(env.horizon,kd,alden.scaleShiftInDepth,[max(burialDepth)*aldenSize])

        bpy.ops.object.modifier_add(type='DISPLACE')
        soilBump = env.horizon.modifiers['Displace']
        soilBump.name = 'soilBump'
            
        displacedSoil = bpy.data.textures.new('soilBump',type='VORONOI')
        soilBump.texture = bpy.data.textures['soilBump']
        displacedSoil.noise_scale = 0.01
        displacedSoil.noise_intensity = 0.5
        displacedSoil.weight_4 = 1.0
        displacedSoil.intensity = 1.0
        displacedSoil.contrast = 5.0

        if env.horizonMaterial == 'sand01':
            displacedSoil.contrast = 1.0

        soilBump.vertex_group = 'soilBump'
        soilBump.strength = -bumpStrength
        soilBump.mid_level = 1.0

        alden.mesh.location[2] += bumpStrength
        return

    def implantMesh(self,whichMesh):

        meshSize = self.bumpForm(whichMesh)
        whichMesh.location[2] -= 0.1*meshSize

        env = self.enviroSpec
        bpy.ops.object.modifier_add(type='DISPLACE')
        soilBump = env.horizon.modifiers['Displace']
        soilBump.name = 'soilBump'
            
        displacedSoil = bpy.data.textures.new('soilBump',type='VORONOI')
        soilBump.texture = bpy.data.textures['soilBump']
        displacedSoil.noise_scale = 0.01
        displacedSoil.noise_intensity = 0.5
        displacedSoil.weight_4 = 1.0
        displacedSoil.intensity = 1.0
        displacedSoil.contrast = 5.0

        if env.horizonMaterial == 'sand01':
            displacedSoil.contrast = 1.0

        soilBump.vertex_group = 'soilBump'
        soilBump.strength = -bumpStrength
        soilBump.mid_level = 1.0

        whichMesh.location[2] += bumpStrength
        bpy.ops.object.modifier_apply(apply_as='DATA',modifier='soilBump')
        return

    def bumpForm(self,whichMesh):

        scn.objects.active = whichMesh
        bpy.ops.object.select_all(action='DESELECT')
        whichMesh.select = True

        scn.update()
        vertsLocal = whichMesh.data.vertices
        vertsGlobal = [whichMesh.matrix_world * v.co for v in vertsLocal]
        zOptions = [v[2] for v in vertsGlobal]
        meshSize = max(zOptions)-min(zOptions)
        whichMesh.location[2] -= min(zOptions)
        whichMesh.location[2] -= 0.1*meshSize

        scn.update()
        vertsLocal = whichMesh.data.vertices
        vertsGlobal = [whichMesh.matrix_world * v.co for v in vertsLocal]

        underGround = [(v[0],v[1]) for v in vertsGlobal if v[2] <= 0.0]
        size = len(underGround)
        kd = mathutils.kdtree.KDTree(size)

        for i,v in enumerate(underGround):
            vertex = Vector((v[0],v[1],0.0))
            kd.insert(vertex,i)

        kd.balance()

        env = self.enviroSpec
        env.scrubToolkit.bumpWeightPaint(env.horizon,kd,None,[max(burialDepth)*meshSize])
        whichMesh.location[2] += 0.1*meshSize
        return meshSize

    def setFixationPointAtDesiredFocalLength(self,alden):
        # find fixation point location and determine desired alden object y position

        env = self.enviroSpec
        
        self.orientAsAppropriate(alden)
        junctionFocusLoc = alden.juncEndPt[alden.fixationPoint-2]
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = alden.mesh
        alden.mesh.select = True

        # this is y1, to be used in scaling calculation... this is y when h is smallest (alden.scaleShiftInDepth == 0)
        yDiffJuncPt = math.sqrt((desiredFocalLength)**2 - (env.cameraL.location[2]-junctionFocusLoc[2])**2) 

        if alden.scaleShiftInDepth != 0:
            zc = env.cameraL.location[2]
            y1 = yDiffJuncPt
            h1 = desiredFocalLength
            JP1 = junctionFocusLoc[2]
            n = alden.scaleShiftInDepth

            distBackMultiplierNum = zc + math.sqrt(zc**2 - (1+y1**2/JP1**2)*(zc**2-(2**n * h1)**2))
            distBackMultiplierDenom = (1+y1**2/JP1**2) * JP1
            distBackMultiplier = distBackMultiplierNum/distBackMultiplierDenom

            if alden.consistentRetinalSize:

                if alden.consistentRetinalSize == 1:
                    bpy.ops.transform.resize(value=(distBackMultiplier,distBackMultiplier,distBackMultiplier),constraint_axis=(True, True, True))
                
                elif alden.consistentRetinalSize > 1:
                    # scale bounding box to 3x3x3

                    xMin,xMax,yMin,yMax,zMin,zMax,leeway = env.physicsToolkit.findBoundingBox(alden.mesh)
                    dims = [xMax-xMin,yMax-yMin,zMax-zMin]
                    mainShrink = 3/max(dims)
                    bpy.ops.transform.resize(value=(mainShrink,mainShrink,mainShrink),constraint_axis=(True, True, True))

                    if alden.consistentRetinalSize == 2:
                        boundingBoxShrink = 1
                        bpy.ops.transform.resize(value=(boundingBoxShrink,boundingBoxShrink,boundingBoxShrink),constraint_axis=(True, True, True))

                    elif alden.consistentRetinalSize == 3:
                        boundingBoxShrink = 2**(9/7-12/7)
                        bpy.ops.transform.resize(value=(boundingBoxShrink,boundingBoxShrink,boundingBoxShrink),constraint_axis=(True, True, True))

                    elif alden.consistentRetinalSize == 4:
                        boundingBoxShrink = 2**(9/7-15/7)
                        bpy.ops.transform.resize(value=(boundingBoxShrink,boundingBoxShrink,boundingBoxShrink),constraint_axis=(True, True, True))

                    elif alden.consistentRetinalSize == 5:
                        boundingBoxShrink = 2**(9/7-18/7)
                        bpy.ops.transform.resize(value=(boundingBoxShrink,boundingBoxShrink,boundingBoxShrink),constraint_axis=(True, True, True))
            
            self.findBoneLocations(alden)
            junctionFocusLoc = alden.juncEndPt[alden.fixationPoint-2]

            h2 = desiredFocalLength*(2**n)
            yDiffJuncPt = math.sqrt(h2**2 - (env.cameraL.location[2]-junctionFocusLoc[2])**2) # y to proper depth in fov

        else:
            distBackMultiplier = 1

        xMin,xMax,yMin,yMax,zMin,zMax,leeway = env.physicsToolkit.findBoundingBox(alden.mesh)
        alden.mesh.location[2] -= zMin

        # then, move to final location
        finalObjectPosition = yDiffJuncPt + env.cameraL.location[1] + (alden.mesh.location[1] - junctionFocusLoc[1])
        alden.mesh.location[1] = finalObjectPosition

        self.orientAsAppropriate(alden)
        return distBackMultiplier

    def performScaleShiftInDepth(self,alden,compensatoryRot=0):

        env = self.enviroSpec

        xMin,xMax,yMin,yMax,zMin,zMax,leeway = env.physicsToolkit.findBoundingBox(alden.mesh)
        distBackMultiplier = 2**alden.scaleShiftInDepth

        self.orientAsAppropriate(alden)
        camRotationStart = env.cameraL.rotation_euler[0]

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = alden.mesh
        alden.mesh.select = True

        aldenDist = alden.mesh.location[1]-env.cameraL.location[1]
        alden.mesh.location[1] = aldenDist*distBackMultiplier + env.cameraL.location[1]

        if alden.consistentRetinalSize:

            if alden.consistentRetinalSize == 1:
                bpy.ops.transform.resize(value=(distBackMultiplier,distBackMultiplier,distBackMultiplier),constraint_axis=(True, True, True))
            
            elif alden.consistentRetinalSize > 1:
                # scale bounding box to 3x3x3

                xMin,xMax,yMin,yMax,zMin,zMax,leeway = env.physicsToolkit.findBoundingBox(alden.mesh)
                dims = [xMax-xMin,yMax-yMin,zMax-zMin]
                mainShrink = 3/max(dims)
                bpy.ops.transform.resize(value=(mainShrink,mainShrink,mainShrink),constraint_axis=(True, True, True))

                if alden.consistentRetinalSize == 2:
                    boundingBoxShrink = 1
                    bpy.ops.transform.resize(value=(boundingBoxShrink,boundingBoxShrink,boundingBoxShrink),constraint_axis=(True, True, True))

                elif alden.consistentRetinalSize == 3:
                    boundingBoxShrink = 2**(9/7-12/7)
                    bpy.ops.transform.resize(value=(boundingBoxShrink,boundingBoxShrink,boundingBoxShrink),constraint_axis=(True, True, True))

                elif alden.consistentRetinalSize == 4:
                    boundingBoxShrink = 2**(9/7-15/7)
                    bpy.ops.transform.resize(value=(boundingBoxShrink,boundingBoxShrink,boundingBoxShrink),constraint_axis=(True, True, True))

                elif alden.consistentRetinalSize == 5:
                    boundingBoxShrink = 2**(9/7-18/7)
                    bpy.ops.transform.resize(value=(boundingBoxShrink,boundingBoxShrink,boundingBoxShrink),constraint_axis=(True, True, True))

            # bpy.ops.object.transform_apply(scale=True) ###### REMOVE TO RESOLVE MATERIAL ISSUES.

        xMin,xMax,yMin,yMax,zMin,zMax,leeway = env.physicsToolkit.findBoundingBox(alden.mesh)
        alden.mesh.location[2] -= zMin

        self.orientAsAppropriate(alden)

        if compensatoryRot:
            camRotationFinish = env.cameraL.rotation_euler[0]

            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = alden.mesh
            alden.mesh.select = True

            deltaCameraRotationX = camRotationFinish-camRotationStart
            bpy.ops.transform.rotate(value=deltaCameraRotationX,axis=(1,0,0),constraint_axis=(True,False,False),constraint_orientation='GLOBAL')

            scn.update()
            vertsLocal = alden.mesh.data.vertices
            vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]
            zOptions = [v[2] for v in vertsGlobal]
            zMin = min(zOptions)
            alden.mesh.location[2] -= zMin
            self.orientAsAppropriate(alden)

        # self.tweakAldenProjectionWeightPaint(alden)
        return

    def tweakAldenProjectionWeightPaint(self,alden):

        env = self.enviroSpec

        scn.objects.active = alden.mesh
        bpy.ops.object.select_all(action='DESELECT')
        alden.mesh.select = True

        alden.mesh.location[2] -= 0.2

        scn.update()
        vertsLocal = alden.mesh.data.vertices
        vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]
        underGround = [(v[0],v[1]) for v in vertsGlobal if v[2] <= 0.0]

        xOptions = [v[0] for v in underGround]
        yOptions = [v[1] for v in underGround]
        aldenXmin = min(xOptions)
        aldenXmax = max(xOptions)
        aldenYmin = min(yOptions)
        aldenYmax = max(yOptions)
        leewayY = (aldenYmax-aldenYmin)/2
        leewayX = (aldenXmax-aldenXmin)/2
        aldenLeeway = max([leewayX,leewayY])

        env.scrubToolkit.editDensityWeightPaint(env.horizon,[aldenXmin,aldenXmax,aldenYmin,aldenYmax,aldenLeeway])
        alden.mesh.location[2] += 0.2
        return

    def findBoneLocations(self,alden):

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.skeleton
        alden.skeleton.select = True
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        scn.update()

        alden.juncEndPt = []
        alden.headsTails = []

        for boneInstance in alden.skeleton.data.bones:

            head = alden.skeleton.matrix_world*boneInstance.head
            tail = alden.skeleton.matrix_world*boneInstance.tail

            headBreak = [head[0],head[1],head[2]]
            tailBreak = [tail[0],tail[1],tail[2]]

            alden.headsTails.append([headBreak,tailBreak])

            if headBreak not in alden.juncEndPt:
                alden.juncEndPt.append(headBreak)

            if tailBreak not in alden.juncEndPt:
                alden.juncEndPt.append(tailBreak)

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.mesh
        alden.mesh.select = True
        alden.skeleton.select = True
        bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
        return

    def gaRandomEnvironment(self,hasMesh):

        if hasMesh:
            self.gaAldenEnvironmentStart()

        else:
            self.gaEnvironmentStart()

        return

    def gaAldenEnvironmentStart(self):

        env = self.enviroSpec

        env.horizon = self.__triHorizon()
        mat = env.materialToolkit.useNodes(env.horizon)

        # env.horizonMaterial = random.sample(horizonGrassMaterialOptions,1)[0]
        env.horizonMaterial = 'ground03'
        penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,env.horizonMaterial,True)

        self.__stereotypicalPeripherals()
        enclConstr = enclosureConstructor(self.enviroSpec)
        enclConstr.noEnclosure()

        w = scn.world
        env.sun = lightingOptions[2]
        w.node_tree.nodes['Sky Texture'].sun_direction = (env.sun[0],env.sun[1],env.sun[2])

        env.horizonTilt = 0
        env.horizonSlant = 0
        env.gravity = 1 
        env.distance = -0.25

        env.aperture = 0

        # if env.aperture:
        #     self.__aperture()

        self.enviroSpec.context = 'Object'
        return

    def gaEnvironmentStart(self):

        self.randomEnvironmentConstruct()

        enclConstr = enclosureConstructor(self.enviroSpec)
        enclConstr.randomEnclosureConstruct()

        self.randomTiltSlantGrassGravity()

        self.enviroSpec.context = 'Environment'
        return

    def noEnvironment(self):

        env = self.enviroSpec

        self.__stereotypicalPeripherals()
        env.sun = [0,0,0]
        env.aperture = 0

        enclConstr = enclosureConstructor(self.enviroSpec)
        enclConstr.noEnclosure()

        env.horizonTilt = 0
        env.horizonSlant = 0
        env.gravity = 0
        env.horizonMaterial = ''
        env.fixationPointDepth = 0
        return

    def gaRandomEnvironmentSpec(self,hasMesh):

        env = self.enviroSpec
        env.horizonMaterial = random.sample(horizonGrassMaterialOptions,1)[0]

        if hasMesh:
            env.sun = lightingOptions[2]
            env.horizonTilt = 0
            env.horizonSlant = 0
            env.gravity = 1 
            env.distance = -0.25

            self.assembleEnvironment()

            enclConstr = enclosureConstructor(self.enviroSpec)
            enclConstr.noEnclosure()
            self.enviroSpec.context = 'Object'

        else:
            env.sun = random.sample(lightingOptions,1)[0]
            # env.horizonTilt = random.sample(horizonTiltOptions,1)[0] ###!
            env.horizonTilt = (random.random()*2-1)*22.5*math.pi/180
            env.horizonSlant = random.sample(horizonSlantOptions,1)[0]
            env.gravity = random.randint(0,1)

            if env.horizonMaterial not in horizonGrassMaterialOptions:
                env.horizonMaterial = random.sample(horizonGrassMaterialOptions,1)[0]

            self.assembleEnvironment()

            enclConstr = enclosureConstructor(self.enviroSpec)
            # enclConstr.randomEnclosure()
            enclConstr.randomEnclosureConstruct()
            self.enviroSpec.context = 'Environment'

        env.aperture = random.randint(0,1)
        env.aperture = 0

        # if env.aperture:
        #     self.__aperture()
            
        return
   
###
###     ENCLOSURE
###

class enclosureConstructor:

    kind = 'Enclosure Constructor'

    def __init__(self,environmentSpec):

        self.enviroSpec = environmentSpec

    def randomEnclosure(self):

        env = self.enviroSpec

        # env.horizonTilt = 0.0
        # env.horizonSlant = 0.0
        # env.gravity = 1

        env.floor = random.randint(0,1)
        env.ceiling = random.randint(0,1)
        env.wallL = random.randint(0,1)
        env.wallR = random.randint(0,1)

        if sum([env.floor,env.ceiling,env.wallL,env.wallR]):
            env.wallB = 1

        else:
            env.wallB = random.randint(0,1)

        env.architectureThickness = 2/100
        env.distance = random.sample(architectureDistanceOptions,1)[0]
        env.structureMaterial = random.sample(structureMaterialOptions,1)[0]
        return

    def randomEnclosureConstruct(self):

        self.randomEnclosure()
        self.assembleEnclosure(noNodes=True)
        return

    def assembleEnclosure(self,noNodes=False):

        env = self.enviroSpec

        # construct the architecture using details stored in env
        lengthScaleAdjust = 2.0*(lengthScale-1.0)

        statusElement = [env.floor,env.ceiling,env.wallL,env.wallR,env.wallB]
        identities = [None,None,None,None,None]     # order: floor, ceiling, left wall, right wall, back wall

        if not sum(statusElement): # no floor, ceiling, or walls exist, so there is no architecture
            env.architecture = 0
            env.scrubToolkit.editDensityWeightPaint(env.horizon,[None,None,None,None,None])
            return

        if env.structureMaterial != 'wireframe':

            if statusElement[0]:   # floor exists
                floor = self.__architectureGen(architectureScale,0,-monkeyDistanceY+(2.0*lengthScale-lengthScaleAdjust)*architectureScale,heightScale*architectureScale*env.architectureThickness,env.architectureThickness,'F')
                identities[0] = floor

            if statusElement[1]:   # ceiling exists
                ceiling = self.__architectureGen(architectureScale,0,-monkeyDistanceY+(2.0*lengthScale-lengthScaleAdjust)*architectureScale,heightScale*architectureScale*2.0-architectureScale*env.architectureThickness,env.architectureThickness,'C')
                identities[1] = ceiling

            if statusElement[2]:   # left wall exists
                leftWall = self.__architectureGen(architectureScale,-architectureScale+architectureScale*env.architectureThickness,-monkeyDistanceY+(2.0*lengthScale-lengthScaleAdjust)*architectureScale,heightScale*architectureScale,env.architectureThickness,'L')
                identities[2] = leftWall

            if statusElement[3]:   # right wall exists
                rightWall = self.__architectureGen(architectureScale,architectureScale-architectureScale*env.architectureThickness,-monkeyDistanceY+(2.0*lengthScale-lengthScaleAdjust)*architectureScale,heightScale*architectureScale,env.architectureThickness,'R')
                identities[3] = rightWall

            if statusElement[4]:   # back wall exists
                backWall = self.__architectureGen(architectureScale,0,-monkeyDistanceY+(3.0*lengthScale-lengthScaleAdjust)*architectureScale-architectureScale*env.architectureThickness,heightScale*architectureScale,env.architectureThickness,'B')
                identities[4] = backWall

        elif env.structureMaterial == 'wireframe':

            if statusElement[0]:   # floor exists
                floor = self.__architectureGenWireframe(architectureScale,0,-monkeyDistanceY+(2.0*lengthScale-lengthScaleAdjust)*architectureScale,0.0,env.architectureThickness,'F')
                identities[0] = floor

            if statusElement[1]:   # ceiling exists
                ceiling = self.__architectureGenWireframe(architectureScale,0,-monkeyDistanceY+(2.0*lengthScale-lengthScaleAdjust)*architectureScale,heightScale*architectureScale*2.0,env.architectureThickness,'C')
                identities[1] = ceiling

            if statusElement[2]:   # left wall exists
                leftWall = self.__architectureGenWireframe(architectureScale,-architectureScale,-monkeyDistanceY+(2.0*lengthScale-lengthScaleAdjust)*architectureScale,heightScale*architectureScale,env.architectureThickness,'L')
                identities[2] = leftWall

            if statusElement[3]:   # right wall exists
                rightWall = self.__architectureGenWireframe(architectureScale,architectureScale,-monkeyDistanceY+(2.0*lengthScale-lengthScaleAdjust)*architectureScale,heightScale*architectureScale,env.architectureThickness,'R')
                identities[3] = rightWall

            if statusElement[4]:   # back wall exists
                backWall = self.__architectureGenWireframe(architectureScale,0,-monkeyDistanceY+(3.0*lengthScale-lengthScaleAdjust)*architectureScale,heightScale*architectureScale,env.architectureThickness,'B')
                identities[4] = backWall

        # join floor, ceiling, and walls (if they exist) into a single object (architecture)
        baseElement = statusElement.index(1)
        baseIdentity = identities[baseElement]

        if len(statusElement) > 1:
            for element in range(len(statusElement)):
                currentElement = statusElement[element]
                currentIdentity = identities[element]

                if currentElement and currentIdentity != baseIdentity:

                    bpy.ops.object.select_all(action='DESELECT')
                    scn.objects.active = baseIdentity
                    baseIdentity.select = True

                    if env.structureMaterial != 'wireframe':
                        # bpy.ops.object.modifier_add(type='BOOLEAN')
                        # baseIdentity.modifiers['Boolean'].object = currentIdentity
                        # baseIdentity.modifiers['Boolean'].operation = 'UNION'
                        # bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Boolean')
                        # env.deleteToolkit.deleteSingleObject(currentIdentity)
                        currentIdentity.select = True
                        bpy.ops.object.join()

                    elif env.structureMaterial == 'wireframe':
                        currentIdentity.select = True
                        bpy.ops.object.join()

        env.architecture = baseIdentity
        env.architecture.name = 'Enclosure'

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = env.architecture
        env.architecture.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.dissolve_degenerate()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

        if env.structureMaterial != 'wireframe':
            # bpy.ops.object.modifier_add(type='BEVEL')
            # env.architecture.modifiers['Bevel'].width = 0.01
            # env.architecture.modifiers['Bevel'].segments = 7
            # env.architecture.modifiers['Bevel'].use_clamp_overlap = False
            # bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Bevel')
            pass

        elif env.structureMaterial == 'wireframe':
            bpy.ops.object.modifier_add(type='SOLIDIFY')
            env.architecture.modifiers['Solidify'].thickness = env.architectureThickness
            bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Solidify')

            bpy.ops.object.modifier_add(type='WIREFRAME')
            env.architecture.modifiers['Wireframe'].thickness = env.architectureThickness
            env.architecture.modifiers['Wireframe'].use_boundary = True
            bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Wireframe')

            env.architecture.location[2] += architectureScale*env.architectureThickness/1.5

        env.architecture.location += Vector((0,env.distance,0))
        scn.update()

        xMin = None
        xMax = None
        yMin = None
        yMax = None
        leeway = None

        # take note of weight paint modification limits if an architecture exists and incorporates a floor
        if statusElement[0]:
            xMin,xMax,yMin,yMax,zMin,zMax,leeway = env.physicsToolkit.findBoundingBox(env.architecture)

        env.scrubToolkit.editDensityWeightPaint(env.horizon,[xMin,xMax,yMin,yMax,leeway])
        env.deleteToolkit.deleteSingleObjectMaterials(env.architecture)

        if not noNodes:
            mat = env.materialToolkit.useNodes(env.architecture)
            penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,env.structureMaterial,True,details='Small')

        if env.structureMaterial in ['tile08','tileOG']:
            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = env.architecture
            env.architecture.select = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.cube_project()
            bpy.ops.object.mode_set(mode='OBJECT')

        # parent enclosure and horizon
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = env.horizon
        env.horizon.select = True
        env.architecture.select = True
        bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
        return

    def __architectureGen(self,size,x,y,z,thickness,side):
        # architectural component of specified thickness

        env = self.enviroSpec

        bpy.ops.object.select_all(action='DESELECT')

        bpy.ops.mesh.primitive_cube_add(radius=size, view_align=False, enter_editmode=False, location=(x,y,z), rotation=(0,0,0))
        box = [b for b in scn.objects if b.name.startswith('Cube')][0]

        if side == 'L':
            bpy.ops.transform.resize(value=(thickness,lengthScale,heightScale),constraint_axis=(True, True, True))

        elif side == 'R':
            bpy.ops.transform.resize(value=(thickness,lengthScale,heightScale),constraint_axis=(True, True, True))

        elif side == 'B':
            bpy.ops.transform.resize(value=(1,thickness,heightScale),constraint_axis=(False, True, True))

        elif side == 'F':
            bpy.ops.transform.resize(value=(1,lengthScale,thickness),constraint_axis=(False, True, True))

        elif side == 'C':
            bpy.ops.transform.resize(value=(1,lengthScale,thickness),constraint_axis=(False, True, True))

        bpy.ops.object.transform_apply(scale=True)
        box.name = 'Surface' + side

        env.massToolkit.makeRigidBody(box,'PASSIVE')
        return box

    def __architectureGenWireframe(self,size,x,y,z,thickness,side):

        env = self.enviroSpec

        bpy.ops.object.select_all(action='DESELECT')

        bpy.ops.mesh.primitive_plane_add(radius=size, location=(x,y,z), rotation=(0,0,0))
        plane = [b for b in scn.objects if b.name.startswith('Plane')][0]

        if side == 'L':
            bpy.ops.transform.resize(value=(heightScale,lengthScale,1),constraint_axis=(True, True, True))
            bpy.ops.transform.rotate(value=math.pi/2,axis=(0,1,0),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')

        elif side == 'R':
            bpy.ops.transform.resize(value=(heightScale,lengthScale,1),constraint_axis=(True, True, True))
            bpy.ops.transform.rotate(value=math.pi/2,axis=(0,1,0),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')

        elif side == 'B':
            bpy.ops.transform.resize(value=(1,heightScale,1),constraint_axis=(False, False, True))
            bpy.ops.transform.rotate(value=math.pi/2,axis=(1,0,0),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')

        elif side == 'F':
            bpy.ops.transform.resize(value=(1,lengthScale,1),constraint_axis=(False, True, False))

        elif side == 'C':
            bpy.ops.transform.resize(value=(1,lengthScale,1),constraint_axis=(False, True, False))

        bpy.ops.object.transform_apply(scale=True,rotation=True)
        plane.name = 'Surface' + side

        env.massToolkit.makeRigidBody(plane,'PASSIVE')
        return plane

    def aldenStimulusLocationEnclosure(self,alden):

        env = self.enviroSpec

        if compositeCompensatoryRot:
            mockCameraX = (env.cameraL.location[0]+env.cameraR.location[0])/2
            mockCameraY = (env.cameraL.location[1]+env.cameraR.location[1])/2
            mockCameraZ = (env.cameraL.location[2]+env.cameraR.location[2])/2

            bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1.0, location=(mockCameraX,mockCameraY,mockCameraZ))
            compositeEmpty = bpy.data.objects['Empty']
            compositeEmpty.name = 'CompositeShiftEmpty'

            # rotation to focus on center
            aldenLocHolder = alden.location
            alden.location = 0

            shifts = self.calculateCompositeShifts(alden)
            alden.location = aldenLocHolder

            distDiffXtoCenter = (alden.mesh.location[0]+shifts[0])-compositeEmpty.matrix_world.translation[0]
            distDiffYtoCenter = (alden.mesh.location[1]+shifts[1])-compositeEmpty.matrix_world.translation[1]
            distDiffZtoCenter = (alden.mesh.location[2]+shifts[2])-compositeEmpty.matrix_world.translation[2]

            rotXtoCenter = math.atan(distDiffZtoCenter/(math.sqrt(distDiffYtoCenter**2+distDiffXtoCenter**2)))
            rotZtoCenter = -math.atan(distDiffXtoCenter/distDiffYtoCenter)

            # rotation to focus on shifted location
            shifts = self.calculateCompositeShifts(alden)

            distDiffX = (alden.mesh.location[0]+shifts[0])-compositeEmpty.matrix_world.translation[0]
            distDiffY = (alden.mesh.location[1]+shifts[1])-compositeEmpty.matrix_world.translation[1]
            distDiffZ = (alden.mesh.location[2]+shifts[2])-compositeEmpty.matrix_world.translation[2]

            rotX = math.atan(distDiffZ/(math.sqrt(distDiffY**2+distDiffX**2)))
            rotZ = -math.atan(distDiffX/distDiffY)

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = compositeEmpty
            compositeEmpty.select = True
            alden.mesh.select = True
            bpy.ops.object.parent_set(type='OBJECT')

            # difference between rotation to focus on center and new rotation necessary
            compositeEmpty.rotation_euler[2] = rotZ - rotZtoCenter
            compositeEmpty.rotation_euler[0] = rotX - rotXtoCenter

            # remove parent
            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = alden.mesh
            alden.mesh.select = True
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        shifts = self.calculateCompositeShifts(alden)
        alden.mesh.location += Vector((shifts[0],shifts[1],shifts[2]))
        enviroConstruct = environmentConstructor(self.enviroSpec)

        fp = enviroConstruct.fitFixationPoint(alden)

        # if necessary, implant stimulus
        if alden.location in [0,5,8,9,13,16] and not env.floor:
            alden.scaleShiftInDepth = 0
            enviroConstruct.implantStimulus(alden)
            enviroConstruct.orientTo(fp.location)

        # parent stimulus and architecture
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = env.horizon
        env.horizon.select = True
        alden.mesh.select = True
        bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
        return fp

    def calculateCompositeShifts(self,alden):

        env = self.enviroSpec

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.mesh
        alden.mesh.select = True
        # bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')

        alden.mesh.location[0] = 0.0
        alden.mesh.location[1] = 0.0

        xMin,xMax,yMin,yMax,zMin,zMax,leeway = env.physicsToolkit.findBoundingBox(alden.mesh)
        zMax = zMax - zMin
        alden.mesh.location[2] -= zMin
        zMin = 0

        # IDENTITIES:
        # floor center                      0
        # right wall center                 1
        # ceiling center                    2
        # left wall center                  3
        # back wall center                  4
        # floor/R wall junction             5
        # ceiling/R wall junction           6
        # ceiling/L wall junction           7
        # floor/L wall junction             8
        # floor/B wall junction             9
        # B wall/R wall junction            10
        # ceiling/B wall junction           11
        # B wall/L wall junction            12
        # floor/B wall/R wall corner        13
        # ceiling/B wall/R wall corner      14
        # ceiling/B wall/L wall corner      15
        # floor/B wall/L wall corner        16


        # any x center has x same
        # 0 2 4 9 11
        if alden.location in [0,2,4,9,11,17]:
            xShift = 0

        # any left has x same
        # has L: 3 7 8 12 15 16
        if alden.location in [3,7,8,12,15,16]:
            xShift = -architectureScale+2.0*architectureScale*env.architectureThickness-xMin

        # any right has x same
        # has R: 1 5 6 10 13 14
        if alden.location in [1,5,6,10,13,14]:
            xShift = architectureScale-2.0*architectureScale*env.architectureThickness-xMax

        # any y center has y same
        # 0 1 2 3 5 6 7 8
        if alden.location in [0,1,2,3,5,6,7,8,17]:
            yShift = -monkeyDistanceY+2.0*architectureScale+env.distance

        # any b has y same
        # has B: 4 9 10 11 12 13 14 15 16
        if alden.location in [4,9,10,11,12,13,14,15,16]:
            yShift = -monkeyDistanceY+(3.0*1.2-2.0*0.2)*architectureScale-architectureScale*env.architectureThickness+env.distance-yMax

        # any z center has z same
        # 1 3 4 10 12
        if alden.location in [1,3,4,10,12,17]:
            zShift = architectureScale-alden.mesh.location[2]

        # any floor has z same
        # has F: 0 5 8 9 13 16
        if alden.location in [0,5,8,9,13,16]:
            zShift = 2.0*architectureScale*env.architectureThickness*env.floor-zMin

            if env.floor and env.structureMaterial == 'wireframe':
                zShift = 0

            if not env.floor:
                zShift = 0
                alden.scaleShiftInDepth = 0

            else:
                alden.implantation = 0

        # any ceiling has z same
        # has C: 2 6 7 11 14 15
        if alden.location in [2,6,7,11,14,15]:
            zShift = architectureScale*2-2.0*architectureScale*env.architectureThickness-zMax

        return Vector((xShift,yShift,zShift))

    def noEnclosure(self,alden=0,hasImplant=1):

        env = self.enviroSpec
        env.architecture = 0 
        env.floor = 0 
        env.ceiling = 0 
        env.wallL = 0 
        env.wallR = 0 
        env.wallB = 0 
        env.architectureThickness = 0 
        env.structureMaterial = ''
        env.distance = 0

        if alden:
            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = alden.mesh
            alden.mesh.select = True
            # bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')

            alden.mesh.location[0] = 0.0
            alden.mesh.location[1] = 0.0
            alden.location = 0

            xMin,xMax,yMin,yMax,zMin,zMax,leeway = env.physicsToolkit.findBoundingBox(alden.mesh)
            alden.mesh.location += Vector((0,-monkeyDistanceY+2.0*architectureScale+env.distance,-zMin))
            enviroConstruct = environmentConstructor(self.enviroSpec)
            # enviroConstruct.performScaleShiftInDepth(alden)
            distBackMultiplier = enviroConstruct.setFixationPointAtDesiredFocalLength(alden)
            fp = enviroConstruct.fitFixationPoint(alden,fpMultiplier=2**alden.scaleShiftInDepth)

            if hasImplant:
                enviroConstruct.implantStimulus(alden)

            else:
                enviroConstruct.bumpForm(alden.mesh)

            enviroConstruct.orientTo(fp.location)

        return

###
###     ANIMATION
###

class animation:

    kind = 'Animation Constructor'

    def __init__(self,environmentSpec):

        self.enviroSpec = environmentSpec
        self.aldenSpec = None

    ###
    ###     SPHERICAL SAMPLING
    ###

    def sphericalSampling(self,blockiness,whichOri,whichRot):

        env = self.enviroSpec
        enviroConstr = environmentConstructor(env)
        env.horizon = enviroConstr.tiltHorizon()
        mat = env.materialToolkit.useNodes(env.horizon)
        env.horizonMaterial = 'ground08'
        penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,env.horizonMaterial,True)

        if blockiness:
            # is a number between 1 and 6, inclusive
            whichObj = sphericalSamplingLibrary + 'Spherical_Sampling_Library-' + str(whichOri) + '.obj'
            nameStartsWith = 'Smooth'

        else:
            # is a number between 7 and 12, inclusive
            whichObj = sphericalSamplingLibrary + 'Spherical_Sampling_Library-' + str(6+whichOri) + '.obj'
            nameStartsWith = 'Blocky'

        # import appropriate .obj
        bpy.ops.import_scene.obj(filepath=whichObj)
        bendyObject = [s for s in scn.objects if s.name.startswith(nameStartsWith)][0]

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = bendyObject
        bendyObject.select = True
         
        bpy.ops.transform.resize(value=(0.01,0.01,0.01),constraint_axis=(True, True, True))
        bpy.ops.transform.rotate(value=whichRot*math.pi/2+math.pi/4,axis=(0,0,1),constraint_axis=(False,False,True),constraint_orientation='GLOBAL')
        bpy.ops.object.transform_apply(scale=True)
        bendyObject.location = Vector((0,0,0)) 

        mat2 = env.materialToolkit.useNodes(bendyObject)
        penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat2,'woodOG',True)

        env.horizonSlant = 0
        env.horizonTilt = 0
        env.gravity = 1
        env.compositeKeepAlden = 1
        enviroConstr.tiltPeripherals()
        self.tiltSkySetup()

        # fp = enviroConstr.fitFixationPointObjectless(otherMesh=bendyObject)
        fp = enviroConstr.fitFixationPointSpecific(env.fixationPointDepth)

        # thetaFP = math.atan((fp.location[1]-env.cameraL.location[1])/(env.cameraL.location[2]-fp.location[2]))
        # shiftBendy = (bendyObject.location[2]-fp.location[2])*math.tan(thetaFP)
        # bendyObject.location[1] = fp.location[1]-shiftBendy

        enviroConstr.implantMesh(bendyObject)
        return

    ###
    ###     STEREOTYPED BALANCE
    ###

    def stereotypedBalance(self,whichOri,whichRot):

        env = self.enviroSpec
        enviroConstr = environmentConstructor(env)
        env.horizon = enviroConstr.tiltHorizon()
        mat = env.materialToolkit.useNodes(env.horizon)
        env.horizonMaterial = 'ground08'
        penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,env.horizonMaterial,True)

        whichObj = stereotypedBalanceLibrary + 'Stereotyped_Balance_Library-' + str(whichOri) + '.obj'

        # import appropriate .obj
        bpy.ops.import_scene.obj(filepath=whichObj)

        if whichOri > 4:
            topper = [s for s in scn.objects if s.name.startswith('topper')][0]
            base = [s for s in scn.objects if s.name.startswith('base')][0]

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = topper
            topper.select = True

            mat2 = env.materialToolkit.useNodes(topper)
            penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat2,'woodOG',True)

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = base
            base.select = True

            mat2 = env.materialToolkit.useNodes(base)
            penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat2,'woodOG',True)

            # join objects
            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = base
            base.select = True
            topper.select = True
            bpy.ops.object.parent_set(type='OBJECT')

            bendyObject = base

        else:
            bean = [s for s in scn.objects if s.name.startswith('bean')][0]

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = bean
            bean.select = True

            mat2 = env.materialToolkit.useNodes(bean)
            penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat2,'woodOG',True)

            bendyObject = bean

        # bpy.ops.transform.resize(value=(0.01,0.01,0.01),constraint_axis=(True, True, True))
        bpy.ops.transform.rotate(value=whichRot*math.pi/2+math.pi/4,axis=(0,0,1),constraint_axis=(False,False,True),constraint_orientation='GLOBAL')
        bpy.ops.object.transform_apply(scale=True)

        if whichOri > 4:
            bendyObject.location = Vector((0,0,1))

        else:
            bendyObject.location = Vector((0,0,0)) 

        env.horizonSlant = 0
        env.horizonTilt = 0
        env.gravity = 1
        env.compositeKeepAlden = 1
        enviroConstr.tiltPeripherals()
        self.tiltSkySetup()

        # fp = enviroConstr.fitFixationPointObjectless(otherMesh=bendyObject)
        fp = enviroConstr.fitFixationPointSpecific(env.fixationPointDepth)

        # thetaFP = math.atan((fp.location[1]-env.cameraL.location[1])/(env.cameraL.location[2]-fp.location[2]))
        # shiftBendy = (bendyObject.location[2]-fp.location[2])*math.tan(thetaFP)
        # bendyObject.location[1] = fp.location[1]-shiftBendy

        enviroConstr.implantMesh(bendyObject)
        return

    ###
    ###     GRASS GRAVITY WITH SECOND HORIZON
    ###

    def tiltSkySetup(self):

        env = self.enviroSpec

        enclConstr = enclosureConstructor(self.enviroSpec)
        enclConstr.noEnclosure()

        w = scn.world
        env.sun = lightingOptions[2]

        x = math.cos(90*math.pi/180)
        z = math.sin(90*math.pi/180)
        env.sun = [x,-0.5,z]

        w.node_tree.nodes['Sky Texture'].sun_direction = (env.sun[0],env.sun[1],env.sun[2])
        mix = w.node_tree.nodes.new('ShaderNodeMixShader')
        mix.name = 'Mix Alpha'
        lightPath = w.node_tree.nodes.new('ShaderNodeLightPath')
        lightPath.name = 'Alpha Background'

        env.horizonTilt = 0
        env.horizonSlant = 0
        env.gravity = 1 
        env.distance = -0.25
        # env.aperture = 0
        return

    def tiltTests(self,whichTilt,gravity,secondHorizon,hasBall,ballBuried,horizMaterial='ground08'):

        env = self.enviroSpec
        enviroConstr = environmentConstructor(env)
        env.horizon = enviroConstr.tiltHorizon()
        mat = env.materialToolkit.useNodes(env.horizon)
        env.horizonMaterial = horizMaterial
        penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,env.horizonMaterial,True)

        if hasBall:
            sphereRadius = 0.15
            bpy.ops.mesh.primitive_uv_sphere_add(size=sphereRadius, location=(0,0,env.horizon.location[2]+sphereRadius), rotation=(0,0,0))
            ball = [s for s in scn.objects if s.name.startswith('Sphere')][0]
            ball.name = 'Ball'

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.faces_shade_smooth()
            bpy.ops.object.mode_set(mode='OBJECT')

            mat = env.materialToolkit.useNodes(ball)
            penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,'woodOG',True)

            if ballBuried:
                scn.update()
                vertsLocal = ball.data.vertices
                vertsGlobal = [ball.matrix_world * v.co for v in vertsLocal]
                zOptions = [v[2] for v in vertsGlobal]
                meshSize = max(zOptions)-min(zOptions)
                ball.location[2] -= min(zOptions)
                ball.location[2] -= 0.1*meshSize
                ball.location[2] += bumpStrength

            otherMesh = ball

        else:
            otherMesh = None 

        enviroConstr.tiltPeripherals()
        self.tiltSkySetup()
        
        env.horizonSlant = 0
        env.horizonTilt = horizonTiltOptions[whichTilt]
        env.gravity = gravity
        env.secondHorizon = secondHorizon
        env.compositeKeepAlden = 1
        # env.context = 'GrassGravity'
        # env.context = 'GrassGravityStimulus_' + str(whichTilt) + '-' + str(gravity) + '-' + str(secondHorizon) + '-' + str(hasBall) + '-' + str(ballBuried)

        enviroConstr.slantScene()
        fp = enviroConstr.fitFixationPointObjectless(otherMesh=otherMesh)

        if hasBall:
            thetaFP = math.atan((fp.location[1]-env.cameraL.location[1])/(env.cameraL.location[2]-fp.location[2]))
            shiftBall = (ball.location[2]-fp.location[2])*math.tan(thetaFP)
            ball.location[1] = fp.location[1]-shiftBall

            if ballBuried:
                enviroConstr.implantMesh(ball)

            else:
                enviroConstr.bumpForm(ball)

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = env.horizon
            env.horizon.select = True
            ball.select = True
            bpy.ops.object.parent_set(type='OBJECT')

            fp = enviroConstr.fitFixationPointObjectless(otherMesh=otherMesh)

        enviroConstr.grassGravity()
        enviroConstr.tiltScene()

        if env.secondHorizon and env.horizonTilt != 0:

            # remove visibility of environment (for image superposition)
            scn.cycles.film_transparent = True

            # rotate sky back to flat (second) horizon -- necessary to keep for lighting effect on slanted plane
            x = env.cameraM.matrix_world[0][2]
            y = env.cameraM.matrix_world[1][2]
            z = env.cameraM.matrix_world[2][2]

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = env.sky
            env.sky.select = True
            bpy.ops.transform.rotate(value=-env.horizonSlant,axis=(1,0,0),constraint_axis=(True,False,False),constraint_orientation='GLOBAL')
            bpy.ops.transform.rotate(value=-env.horizonTilt,axis=(x,y,z),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')

        return

    def restoreEnvironmentVisibility(self):

        # restore visibility of environment
        scn.cycles.film_transparent = False
        return

    ###
    ###     INANIMATE ANIMATION
    ###

    def inanimateRollingLandscape(self):

        env = self.enviroSpec

        enviroConstr = environmentConstructor(env)
        enviroConstr.gaAldenEnvironmentStart() # 'ground08'

        centralLocation = -monkeyDistanceY+2.0*architectureScale+env.distance
        centralLocation = 0
        leeway = 1.0

        env = self.enviroSpec
        scn.objects.active = env.horizon
        bpy.ops.object.select_all(action='DESELECT')
        env.horizon.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        faces = bmesh.from_edit_mesh(env.horizon.data).faces

        for face in faces:
            face.select = False

            for v in face.verts:

                if v.co[0] > (-leeway*1.5) and v.co[0] < (leeway*1.5) and v.co[1] > (centralLocation-leeway*1.5) and v.co[1] < (centralLocation+leeway*1.5):
                    face.select = True

        bpy.ops.mesh.subdivide(number_cuts=100)
        bpy.ops.object.mode_set(mode='OBJECT')

        env.scrubToolkit.sphericalBessel(env.horizon,0,centralLocation)

        bpy.ops.object.modifier_add(type='DISPLACE')
        soilBump = env.horizon.modifiers['Displace']
        soilBump.name = 'soilMound'
        
        soilBump.vertex_group = 'soilMound'
        moundHeight = 0.5 # was 0.75 with projector setup
        soilBump.strength = moundHeight
        soilBump.mid_level = 0.0

        bpy.ops.object.modifier_add(type='DISPLACE')
        soilBump = env.horizon.modifiers['Displace']
        soilBump.name = 'soilTexture'
            
        displacedSoil = bpy.data.textures.new('soilTexture',type='VORONOI')
        soilBump.texture = bpy.data.textures['soilTexture']
        displacedSoil.noise_scale = 0.01
        displacedSoil.noise_intensity = 0.5
        displacedSoil.weight_4 = 1.0
        displacedSoil.intensity = 1.0
        displacedSoil.contrast = 5.0

        if env.horizonMaterial == 'sand01':
            displacedSoil.contrast = 1.0

        soilBump.vertex_group = 'soilMound'
        soilBump.strength = -0.1
        soilBump.mid_level = 0.0
        bpy.ops.object.modifier_apply(apply_as='DATA',modifier='soilMound')
        return moundHeight

    def setInanimateAnimationPath(self,whichMesh,meshRadius,moundHeight):

        env = self.enviroSpec

        bpy.ops.curve.primitive_nurbs_path_add(location=(2,0,moundHeight+meshRadius+0.001), rotation=(0,0,0))
        nurbsPath = [s for s in scn.objects if s.name.startswith('NurbsPath')][0]
        nurbsPath.name = 'RollPath'

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = nurbsPath
        nurbsPath.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.subdivide(number_cuts=10)
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        shrinkwrap = nurbsPath.modifiers['Shrinkwrap']
        shrinkwrap.target = env.horizon
        shrinkwrap.offset = meshRadius
        bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Shrinkwrap')

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = nurbsPath
        nurbsPath.select = True
        whichMesh.select = True
        bpy.ops.object.parent_set(type='FOLLOW')

        whichMesh.rigid_body.kinematic = True
        whichMesh.rigid_body.collision_shape = 'MESH'
        whichMesh.rigid_body.use_margin = True
        whichMesh.rigid_body.collision_margin = 0.001
        whichMesh.rigid_body.friction = 1.0

        env.horizon.rigid_body.collision_shape = 'MESH'
        env.horizon.rigid_body.use_margin = True
        env.horizon.rigid_body.collision_margin = 0.001
        env.horizon.rigid_body.friction = 1.0

        whichMesh.rigid_body.kinematic = True
        whichMesh.keyframe_insert('rigid_body.kinematic',frame=0)

        whichMesh.rigid_body.kinematic = False
        whichMesh.keyframe_insert('rigid_body.kinematic',frame=5)
        return nurbsPath

    ###     ROLL

    def rollTests(self,angle):

        moundHeight = self.inanimateRollingLandscape()
        self.createRollingAnimation(angle,moundHeight)
        return

    def createRollingAnimation(self,rollDirection,moundHeight):

        env = self.enviroSpec
        sphereRadius = 0.15

        bpy.ops.mesh.primitive_uv_sphere_add(size=sphereRadius, location=(0,0,moundHeight+sphereRadius+0.001), rotation=(0,0,0))
        ball = [s for s in scn.objects if s.name.startswith('Sphere')][0]
        ball.name = 'Ball'

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.faces_shade_smooth()
        bpy.ops.object.mode_set(mode='OBJECT')

        env.massToolkit.makeRigidBody(ball,'ACTIVE')
        ball.rigid_body.friction = 0.0

        # put fixation point at ball location
        enviroConstr = environmentConstructor(env)
        # enviroConstr.fitFixationPointObjectless(otherMesh=ball)
        fp = enviroConstr.fitFixationPointSpecific(2.197171449661255)

        mat = env.materialToolkit.useNodes(ball)
        penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,'woodOG',True)

        rollPath = self.setInanimateAnimationPath(ball,sphereRadius,moundHeight)
        self.makeBallRoll(ball)
        
        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1.0, location=(0,0,0))
        rollEmpty = bpy.data.objects['Empty']
        rollEmpty.name = 'RollEmpty'

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = rollEmpty
        rollEmpty.select = True
        rollPath.select = True
        bpy.ops.object.parent_set(type='OBJECT')

        rollPath.select = False
        bpy.ops.transform.rotate(value=rollDirection,axis=(0,0,1),constraint_axis=(False,False,True),constraint_orientation='GLOBAL')
        bpy.ops.object.transform_apply(rotation=True)
        return

    def makeBallRoll(self,ball):

        nurbsPath = [s for s in bpy.data.curves if s.name.startswith('NurbsPath')][-1]
        rollDriver = ball.driver_add("rotation_euler",1).driver
        rollVariable = rollDriver.variables.new()
        rollVariable.name = 'eval_time'
        rollVariable.type = 'SINGLE_PROP'
        rollVariable.targets[0].id_type = 'CURVE'
        rollVariable.targets[0].id = nurbsPath
        rollVariable.targets[0].data_path = 'eval_time'
        rollDriver.expression = '-2*4/0.15*(eval_time/10)'

        ball.rigid_body.collision_shape = 'SPHERE'
        return

    ###
    ###     ANIMATE ANIMATION
    ###

    def animalTests(self,alden):

        self.aldenSpec = alden
        self.animateAnimationLandscape()
        self.createAnimateAnimation()
        return

    def animateAnimationLandscape(self):

        enviroConstr = environmentConstructor(self.enviroSpec)
        enviroConstr.gaAldenEnvironmentStart()
        return

    def randomWiggleWhole(self,alden):

        self.aldenSpec = alden
        compName,head,tail = self.randomWhichWiggle()
        partnerBone = None

        # make a bone there as appropriate
        self.makeAbone(compName,head,tail)

        limbComps = [g.name for g in alden.mesh.vertex_groups if g.name.startswith('Comp')]

        for meld in alden.taggedComps:

            if compName in meld:
                nonmatchName = [c for c in meld if c != compName][0]               # find the name of the partner 'Comp' group
                nonmatchIndex = limbComps.index(nonmatchName)
                headPartner = alden.headsTails[nonmatchIndex][0]
                tailPartner = alden.headsTails[nonmatchIndex][1]
                self.makeAbone(nonmatchName,headPartner,tailPartner,isPartner=[head,tail])
                # print(nonmatchIndex,nonmatchName)

        return

    def randomWhichWiggle(self):

        alden = self.aldenSpec
        whichLimbs,limbComps = self.wigglePossibilities()
        whichLimb = random.sample(whichLimbs,1)[0]

        head = alden.headsTails[whichLimb][0]
        tail = alden.headsTails[whichLimb][1]
        
        compName = limbComps[whichLimb]
        alden.whichWiggle = compName
        return compName, head, tail

    def postHocWiggle(self,alden):

        self.aldenSpec = alden

        xMin,xMax,yMin,yMax,zMin,zMax,leeway = alden.physicsToolkit.findBoundingBox(alden.mesh)
        # alden.mesh.location[2] -= zMin

        enviroConstr = environmentConstructor(self.enviroSpec)
        enviroConstr.findBoneLocations(alden)

        juncPts = []
        juncEndPts = []
        boneName = []

        # if a point appears more than once in headstails, it's a junction.
        for boneInstance in alden.skeleton.data.bones:

            head = [h for h in alden.skeleton.matrix_world*boneInstance.head]
            tail = [t for t in alden.skeleton.matrix_world*boneInstance.tail]

            if head not in juncEndPts:
                juncEndPts.append(head)

            else:
                juncPts.append(head)

            if tail not in juncEndPts:
                juncEndPts.append(tail)

            else:
                juncPts.append(tail)

        for boneInstance in alden.skeleton.data.bones:

            head = [h for h in alden.skeleton.matrix_world*boneInstance.head]
            tail = [t for t in alden.skeleton.matrix_world*boneInstance.tail]

            if head in juncPts:
                boneName.append(boneInstance.name)

            if tail in juncPts:
                boneName.append(boneInstance.name)

        # choose a limb to wiggle
        hasPartnerBone = False

        limbComps = [g.name for g in alden.mesh.vertex_groups if g.name.startswith('Comp')]     # all weight paint Comp groups
        whichLimb = limbComps.index(alden.whichWiggle)
        head = alden.headsTails[whichLimb][0]
        tail = alden.headsTails[whichLimb][1]
        doubleJunctionMatch = sum([1 for n in boneName if n==alden.whichWiggle])

        for meld in alden.taggedComps:

            if alden.whichWiggle in meld:
                hasPartnerBone = True

                nonmatchName = [c for c in meld if c != alden.whichWiggle][0]               # find the name of the partner 'Comp' group
                nonmatchIndex = limbComps.index(nonmatchName)
                headPartner = alden.headsTails[nonmatchIndex][0]
                tailPartner = alden.headsTails[nonmatchIndex][1]
                doubleJunctionPartner = sum([1 for n in boneName if n==nonmatchName])

        if not hasPartnerBone:
            self.makeAbone(alden.whichWiggle,head,tail)

        elif hasPartnerBone:

            if doubleJunctionMatch == 2:
                finalHead = alden.skeleton.matrix_world*alden.skeleton.data.bones[nonmatchName].head
                finalTail = alden.skeleton.matrix_world*alden.skeleton.data.bones[nonmatchName].tail
                self.makeAbone(nonmatchName,finalHead,finalTail)

            elif doubleJunctionPartner == 2:
                finalHead = alden.skeleton.matrix_world*alden.skeleton.data.bones[alden.whichWiggle].head
                finalTail = alden.skeleton.matrix_world*alden.skeleton.data.bones[alden.whichWiggle].tail
                self.makeAbone(alden.whichWiggle,finalHead,finalTail)

            else:
                self.makeAbone(alden.whichWiggle,head,tail)
                self.makeAbone(nonmatchName,headPartner,tailPartner,isPartner=1)

        return

    def wigglePossibilities(self):

        alden = self.aldenSpec
        xMin,xMax,yMin,yMax,zMin,zMax,leeway = alden.physicsToolkit.findBoundingBox(alden.mesh)
        alden.mesh.location[2] -= zMin

        enviroConstr = environmentConstructor(self.enviroSpec)
        enviroConstr.findBoneLocations(alden)

        # choose a limb to wiggle
        whichLimbs = [ind for ind,entry in enumerate(alden.boneTags) if entry == True]          # take aside all 'Comp' group indices eligible for wiggling--bone has endpt as either head or tail
        # limbComps = [g.name for g in alden.mesh.vertex_groups if g.name.startswith('Comp')]     # all weight paint Comp groups
        limbComps = [b.name for b in alden.skeleton.data.bones if b.name.startswith('Comp')]

        if not (alden.lowPotentialEnergy and alden.makePrecarious == [0.0,0.0,0.0,1.0]):            # if not only low potential, keep support limb (remove from whichLimbs)
            whichLimbTails = [alden.headsTails[ind][1][2] for ind in whichLimbs]
            whichToRemove = whichLimbTails.index(min(whichLimbTails))                           # remove whichever bone has a tail closest to the ground
            removedIdentity = whichLimbs[whichToRemove]
            del whichLimbs[whichToRemove]                                                       # take that bone out of Comp options, too

        for meld in alden.taggedComps:                                                          # delete one index of each 'Comp' group pair in whichLimbs
            idx1 = limbComps.index(meld[0])
            idx2 = limbComps.index(meld[1])

            # if idx1 == removedIdentity:
            #     del whichLimbs[whichLimbs.index(idx2)]

            # if idx2 == removedIdentity:
            #     del whichLimbs[whichLimbs.index(idx1)]

            if idx1 in whichLimbs and idx2 in whichLimbs:
                del whichLimbs[whichLimbs.index(idx2)]

        return whichLimbs,limbComps

    def makeAbone(self,compName,head,tail,isPartner=0):

        alden = self.aldenSpec
        amt = bpy.data.armatures.new('WiggleSkeleton')
        singleBone = bpy.data.objects.new('SkeletonObject',amt)
        singleBone.show_x_ray = True                                                    # visualize bone through mesh
        
        scn.objects.link(singleBone)                                                    # link object to scene
        scn.objects.active = singleBone
        singleBone.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        boneInstance = amt.edit_bones.new('WiggleBone'+compName)
        boneInstance.head = head
        boneInstance.tail = tail
        boneInstance.use_connect = True
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.mesh
        alden.mesh.select = True
        singleBone.data.bones.active = singleBone.data.bones['WiggleBone'+compName]
        singleBone.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')

        bpy.ops.mesh.select_all(action='DESELECT')
        alden.mesh.vertex_groups.active_index = alden.mesh.vertex_groups[compName].index
        alden.mesh.vertex_groups.active = alden.mesh.vertex_groups[compName]
        bpy.ops.object.vertex_group_select()

        bpy.ops.object.hook_add_selob(use_bone=True)
        bpy.ops.object.mode_set(mode='OBJECT')

        hookMod = [h for h in alden.mesh.modifiers if h.name.startswith('Hook')][-1]
        bpy.ops.object.modifier_move_up(modifier=hookMod.name)
        hookMod.vertex_group = compName

        backForth = NP.sign(tail[0]-head[0])

        if isPartner:
            backForth = -backForth

        self.makeWiggle(singleBone,compName,backForth)
        return

    def makeWiggle(self,singleBone,compName,backForth):

        # rotate about the y axis to increase the chance of seeing the movement
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = singleBone
        singleBone.select = True
        bpy.ops.object.mode_set(mode='POSE')

        wiggle = singleBone.pose.bones['WiggleBone'+compName]

        wiggle.rotation_mode = 'XYZ'
        wiggle.keyframe_insert('rotation_euler',frame=1)

        rotationExtent = -math.pi/10

        totalTime = 60                      # frames at 60 frames/second
        timeIncrement = 30                  # frames; was 10
        currentTime = 0                     # frame

        while currentTime < totalTime:
            bpy.ops.transform.rotate(value=rotationExtent*backForth,axis=(0,1,0),constraint_axis=(False,True,False),constraint_orientation='GLOBAL')
            wiggle.keyframe_insert('rotation_euler',frame=currentTime+timeIncrement)
            currentTime += timeIncrement
            backForth = -backForth

        bpy.ops.object.mode_set(mode='OBJECT')
        return


