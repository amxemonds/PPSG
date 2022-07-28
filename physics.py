
import bpy

import math
from mathutils import Vector
from mathutils import Euler

import config
from config import *

from delete import deleteTool
from addonMaterials import massTool


class physicsTool:

    kind = 'Physics Toolkit'

    def __init__(self):
        self.aldenPhys = None

        self.massToolkit = massTool()
        self.deleteToolkit = deleteTool()

    def findBoundingBox(self,workingMesh):
        # find the bounding box of any mesh

        scn.update()
        vertsLocal = workingMesh.data.vertices
        vertsGlobal = [workingMesh.matrix_world * v.co for v in vertsLocal]
        xOptions = [v[0] for v in vertsGlobal]
        yOptions = [v[1] for v in vertsGlobal]
        zOptions = [v[2] for v in vertsGlobal]
        xMin = min(xOptions)
        xMax = max(xOptions)
        yMin = min(yOptions)
        yMax = max(yOptions)
        zMin = min(zOptions)
        zMax = max(zOptions)
        leewayY = (yMax-yMin)/3
        leewayX = (xMax-xMin)/3
        leeway = max([leewayX,leewayY])
        return xMin,xMax,yMin,yMax,zMin,zMax,leeway

    def evaluateTimecourse(self,alden):

        self.aldenPhys = alden

        scn.frame_end = 200

        particleSystems = [m for m in bpy.context.object.modifiers if m.name.startswith('ParticleSystem')]

        for particleSystem in particleSystems:
            particleSystem.show_render = False
            particleSystem.show_viewport = False

        scn.objects.active = alden.mesh
        bpy.ops.object.select_all(action='DESELECT')
        alden.mesh.select = True

        for aldenObject in [a for a in bpy.data.objects if a.name.startswith('AldenObject')]:
            aldenObject.select = True

        bpy.ops.nla.bake(frame_start=1,frame_end=scn.frame_end,visual_keying=True,bake_types={'OBJECT'})

        # scn.frame_current = scn.frame_end
        scn.frame_set(scn.frame_end)
        scn.update()
        alden.mesh.data.update()

        location = Vector(([float(l) for l in alden.mesh.location]))
        rotation = Euler(([float(l) for l in alden.mesh.rotation_euler]))

        # scn.frame_current = 1
        scn.frame_set(1)
        scn.frame_end = totalFrames
        scn.rigidbody_world.time_scale = 1
        scn.update()

        bpy.context.active_object.animation_data_clear()

        aldenObjects = [a for a in bpy.data.objects if a.name.startswith('AldenObject')]

        # join density-partitioned stimulus
        if len(aldenObjects) > 1:
            bpy.ops.object.select_all(action='DESELECT')

            for aldenObject in aldenObjects:
                aldenObject.select = True

            scn.objects.active = alden.mesh
            bpy.ops.object.join()

        alden.mesh.location = location
        alden.mesh.rotation_euler = rotation
        alden.rotation = [r for r in alden.mesh.rotation_euler]

        if not alden.densityUniform:
           self.deleteToolkit.deleteSingleObject(bpy.data.objects['SeparationConstraint'])

        for particleSystem in particleSystems:
            particleSystem.show_render = True
            particleSystem.show_viewport = True

        return

    def joinDensityPartition(self,alden):
        
        aldenObjects = [a for a in bpy.data.objects if a.name.startswith('AldenObject')]

        # join density-partitioned stimulus
        if len(aldenObjects) > 1:
            bpy.ops.object.select_all(action='DESELECT')

            for aldenObject in aldenObjects:
                aldenObject.select = True

            scn.objects.active = alden.mesh
            bpy.ops.object.join()

        self.deleteToolkit.deleteSingleObject(bpy.data.objects['SeparationConstraint'])
        return

    def makePrecariousMesh(self,alden):

        self.aldenPhys = alden

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.mesh
        alden.mesh.select = True

        bpy.ops.transform.rotate(value=alden.makePrecarious[0],axis=(1,0,0),constraint_axis=(True,False,False),constraint_orientation='GLOBAL')
        bpy.ops.transform.rotate(value=alden.makePrecarious[1],axis=(0,1,0),constraint_axis=(False,True,False),constraint_orientation='GLOBAL')
        bpy.ops.transform.rotate(value=alden.makePrecarious[2],axis=(0,0,1),constraint_axis=(False,False,True),constraint_orientation='GLOBAL')

        alden.rotation = [r for r in alden.mesh.rotation_euler]
        
        xMin,xMax,yMin,yMax,zMin,zMax,leeway = self.findBoundingBox(alden.mesh)
        alden.mesh.location -= Vector((0,0,zMin))

        if not alden.makePrecarious[3]:# and alden.lowPotentialEnergy:                        # if not intended to be final transformation
            self.evaluateTimecourse(alden)

            xMin,xMax,yMin,yMax,zMin,zMax,leeway = self.findBoundingBox(alden.mesh)
            alden.mesh.location -= Vector((0,0,zMin))

        return

    def wallInteraction(self,alden):

        self.aldenPhys = alden

        if alden.location != 0:

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = alden.mesh
            alden.mesh.select = True

            if alden.wallInteraction == 1:                          # hanging condition
                self.__hang(alden)
                alden.mesh.location[2] = 0.0

            if alden.wallInteraction == -1:                         # clinging condition
                bpy.ops.transform.rotate(value=-math.pi/2*alden.location,axis=(0,1,0),constraint_axis=(True,True,True),constraint_orientation='GLOBAL') ### PROBLEMATIC... ALREADY ROTATED
                alden.rotation = [r for r in alden.mesh.rotation_euler]

            xMin,xMax,yMin,yMax,zMin,zMax,leeway = self.findBoundingBox(alden.mesh)
            alden.mesh.location -= Vector((0,0,zMin))

        return

    def __hang(self,alden):

        self.aldenPhys = alden

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.mesh
        alden.mesh.select = True
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

        scn.update()
        vertsLocal = alden.mesh.data.vertices
        vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]
        xOptions = [v[0] for v in vertsGlobal]
        yOptions = [v[1] for v in vertsGlobal]
        zOptions = [v[2] for v in vertsGlobal]

        if alden.location == 1: # right wall center
            vertexX = max(xOptions)
            vertexIndex = xOptions.index(vertexX)
            vertexY = yOptions[vertexIndex]
            vertexZ = zOptions[vertexIndex]
            rotationY = math.pi/2

        elif alden.location == 2: # ceiling center
            vertexZ = max(zOptions)
            vertexIndex = zOptions.index(vertexZ)
            vertexX = xOptions[vertexIndex]
            vertexY = yOptions[vertexIndex]
            rotationY = 0

        elif alden.location == 3: # left wall center
            vertexX = min(xOptions)
            vertexIndex = xOptions.index(vertexX)
            vertexY = yOptions[vertexIndex]
            vertexZ = zOptions[vertexIndex]
            rotationY = math.pi/2

        else:
            return

        bpy.ops.mesh.primitive_plane_add(radius=3,location=(vertexX,vertexY,vertexZ+10),rotation=(0,rotationY,0))
        mockWall = bpy.data.objects['Plane']
        mockWall.name = 'MockWall'
        self.massToolkit.makeRigidBody(mockWall,'PASSIVE')

        bpy.ops.mesh.primitive_plane_add(radius=0.1,location=(vertexX,vertexY,vertexZ+10),rotation=(0,rotationY,0))
        controlPlane = bpy.data.objects['Plane']
        controlPlane.name = 'ControlPlane'
        self.massToolkit.makeRigidBody(controlPlane,'ACTIVE')

        alden.mesh.location[2] += 10

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = controlPlane
        controlPlane.select = True
        alden.mesh.select = True
        bpy.ops.rigidbody.connect(con_type='FIXED',pivot_type='ACTIVE')
        constraint1 = bpy.data.objects['Constraint']
        constraint1.name = 'ControlToAlden'

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = controlPlane
        controlPlane.select = True
        mockWall.select = True
        bpy.ops.rigidbody.connect(con_type='POINT',pivot_type='ACTIVE')
        constraint2 = bpy.data.objects['Constraint']
        constraint2.name = 'ControlToWall'

        if not alden.densityUniform:
            self.massToolkit.separateForDensityAssignment(alden)

        self.evaluateTimecourse(alden)

        self.deleteToolkit.deleteSingleObject(mockWall)
        self.deleteToolkit.deleteSingleObject(controlPlane)
        self.deleteToolkit.deleteSingleObject(constraint1)
        self.deleteToolkit.deleteSingleObject(constraint2)
        return

    def centerOfMassByVolume(self,alden):

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.mesh
        alden.mesh.select = True
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')

        scn.update()
        return alden.mesh.location
