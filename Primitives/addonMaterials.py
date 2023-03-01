
import bpy
import bmesh

import math
import mathutils
from mathutils import Vector

import os
import sys

import config
from config import *


###
###     MATERIAL EDITING TOOLS
###

class materialTool:

    kind = 'Material Toolkit'

    def __init__(self):

        self.whichMesh = None

    def tryUVUnwrap(self,whichMesh,kind='Smart'):

        self.whichMesh = whichMesh

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = whichMesh
        whichMesh.select = True

        if len(whichMesh.data.uv_layers) == 0:
                bpy.ops.object.mode_set(mode='EDIT')
                scn.objects.active = whichMesh
                bpy.ops.mesh.select_all(action='SELECT')

                if kind == 'Smart':
                    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.0)

                elif kind == 'Sphere':
                    bpy.ops.uv.sphere_project()

                elif kind == 'Cylinder':
                    bpy.ops.uv.cylinder_project()

                elif kind == 'Cube':
                    bpy.ops.uv.cube_project()

                bpy.ops.object.mode_set(mode='OBJECT')
        return

    def useNodes(self,whichMesh):

        self.whichMesh = whichMesh

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = self.whichMesh
        self.whichMesh.select = True

        mat = bpy.data.materials.new('Mat')
        mat.use_nodes = True
        mat.node_tree.nodes.remove(mat.node_tree.nodes[1])

        bpy.ops.object.material_slot_add()
        self.whichMesh.material_slots[0].material = mat
        bpy.ops.object.material_slot_assign()
        return mat

    def __assignMaterial(self,mat):

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = self.whichMesh
        self.whichMesh.select = True

        bpy.ops.object.material_slot_add()
        self.whichMesh.material_slots[-1].material = mat
        bpy.ops.object.material_slot_assign()
        return

    def __loadBlendMaterial(self,kind):

        blendfile = materialResources + kind + '.blend'
        section = '\\Material\\'
        directory = blendfile + section
        filename  = kind
        bpy.ops.wm.append(filename=filename, directory=directory)
        mat = bpy.data.materials[kind]

        bpy.ops.object.material_slot_add()
        self.whichMesh.material_slots[-1].material = mat
        bpy.ops.object.material_slot_assign()

        mats = [m for m in bpy.data.materials if m.name.startswith('Mat')]
        mat = mats[-1]

        loadGroup = mat.node_tree.nodes.new('ShaderNodeGroup')
        loadGroup.name = kind
        whichNodeGroups = [n for n in bpy.data.node_groups if n.name.startswith(kind)]
        loadGroup.node_tree = whichNodeGroups[-1]
        outputGroup = loadGroup
        return outputGroup

    ###
    ###     CYCLES MATERIAL NODES
    ###

    def makeOptics(self,alden):

        scn.objects.active = alden.mesh
        bpy.ops.object.select_all(action='DESELECT')
        alden.mesh.select = True

        penultimate = None
        penultimateVolume = None
        penultimateDisplacement = None

        self.tryUVUnwrap(alden.mesh)
        mat = alden.mat

        # control glassy detail and absorption
        lightPath = mat.node_tree.nodes.new('ShaderNodeLightPath')
        geometry = mat.node_tree.nodes.new('ShaderNodeNewGeometry')

        multiply1 = mat.node_tree.nodes.new('ShaderNodeMath')
        multiply1.operation = 'MULTIPLY'

        multiply2 = mat.node_tree.nodes.new('ShaderNodeMath')
        multiply2.operation = 'MULTIPLY'
        multiply2.inputs[0].default_value = 1.0

        multiply3 = mat.node_tree.nodes.new('ShaderNodeMath')
        multiply3.operation = 'MULTIPLY'
        multiply3.inputs[0].default_value = -30.0                                       # optical attenuation control: alden.opticalAttenuation
        alden.opticalAttenuation = -30.0

        power = mat.node_tree.nodes.new('ShaderNodeMath')
        power.operation = 'POWER'
        power.inputs[0].default_value = math.exp(1)

        mixVolumeSurface = mat.node_tree.nodes.new('ShaderNodeMixRGB')
        mixVolumeSurface.blend_type = 'MIX'
        mixVolumeSurface.inputs[2].default_value = (1.0,1.0,1.0,1.0) 

        glassy = self.__loadBlendMaterial('Chocofur_Glass_Advanced')
        glassy.inputs[3].default_value = (1.0,1.0,1.0,1.0) 
        glassy.inputs[4].default_value = 0.0
        glassy.inputs[5].default_value = alden.opticalIOR

        # control reflectivity of surface
        reflectivity = mat.node_tree.nodes.new('ShaderNodeValue')
        reflectivity.outputs[0].default_value = alden.opticalReflectivity 

        reflectivityMultiply10 = mat.node_tree.nodes.new('ShaderNodeMath')
        reflectivityMultiply10.operation = 'MULTIPLY'
        reflectivityMultiply10.inputs[1].default_value = 10.0

        # control roughness of surface
        roughness = mat.node_tree.nodes.new('ShaderNodeValue')
        roughness.outputs[0].default_value = alden.opticalRoughness 

        roughnessDivide10 = mat.node_tree.nodes.new('ShaderNodeMath')
        roughnessDivide10.operation = 'DIVIDE'
        roughnessDivide10.inputs[1].default_value = 10.0

        # object surface color (capable of changing)
        rgbSurface = mat.node_tree.nodes.new('ShaderNodeRGB')

        lRGB = []
        for c in alden.opticalBeerLambertColor:
            a = 0.055
            if c <= 0.04045:
                lRGB.append(c/12)
            else:
                lRGB.append(((c+a)/(1+a))**2.4)

        rgbSurface.outputs[0].default_value = lRGB+[1.0]

        # diffuse and glossy nodes and incorporation
        diffuse = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
        glossy = mat.node_tree.nodes.new('ShaderNodeBsdfGlossy')
        mixDiffuseGlossy = mat.node_tree.nodes.new('ShaderNodeMixShader')

        # incorporation of transparency
        mixDGTGlass = mat.node_tree.nodes.new('ShaderNodeMixShader')
        
        if alden.opticalTransparency > 1:
            mixDGTGlass.inputs[0].default_value = 0
            musgraveFlag = 1
        else:
            mixDGTGlass.inputs[0].default_value = alden.opticalTransparency
            musgraveFlag = 0

        penultimate = mixDGTGlass

        # color for glass (absorption)
        mat.node_tree.links.new(lightPath.outputs[7],multiply1.inputs[0])
        mat.node_tree.links.new(geometry.outputs[6],multiply1.inputs[1])
        mat.node_tree.links.new(multiply1.outputs[0],multiply2.inputs[1])
        mat.node_tree.links.new(multiply2.outputs[0],multiply3.inputs[1])
        mat.node_tree.links.new(multiply3.outputs[0],power.inputs[1])
        mat.node_tree.links.new(power.outputs[0],mixVolumeSurface.inputs[0])
        mat.node_tree.links.new(rgbSurface.outputs[0],mixVolumeSurface.inputs[1])
        mat.node_tree.links.new(mixVolumeSurface.outputs[0],glassy.inputs[0])

        # color for diffuse to glossy (surface)
        mat.node_tree.links.new(rgbSurface.outputs[0],diffuse.inputs[0])
        mat.node_tree.links.new(rgbSurface.outputs[0],glossy.inputs[0])

        # incorporation of reflectivity (diffuse to mirrored scale)
        mat.node_tree.links.new(reflectivity.outputs[0],reflectivityMultiply10.inputs[0])
        mat.node_tree.links.new(reflectivityMultiply10.outputs[0],glassy.inputs[7])
        mat.node_tree.links.new(reflectivity.outputs[0],mixDiffuseGlossy.inputs[0])
        mat.node_tree.links.new(diffuse.outputs[0],mixDiffuseGlossy.inputs[1])
        mat.node_tree.links.new(glossy.outputs[0],mixDiffuseGlossy.inputs[2])

        # incorporation of roughness (smooth to rough scale)
        mat.node_tree.links.new(roughness.outputs[0],roughnessDivide10.inputs[0])
        mat.node_tree.links.new(roughnessDivide10.outputs[0],diffuse.inputs[1])
        mat.node_tree.links.new(roughnessDivide10.outputs[0],glossy.inputs[1])
        mat.node_tree.links.new(roughnessDivide10.outputs[0],glassy.inputs[6])
        mat.node_tree.links.new(roughnessDivide10.outputs[0],glassy.inputs[8])

        # incorporation of opacity (opaque to transparent scale)
        mat.node_tree.links.new(mixDiffuseGlossy.outputs[0],mixDGTGlass.inputs[1])
        mat.node_tree.links.new(glassy.outputs[0],mixDGTGlass.inputs[2])
        mat.node_tree.links.new(mixDGTGlass.outputs[0],mat.node_tree.nodes[0].inputs[0])
        
        # musgrave flag will be horizon material
        # musgraveFlag = 'sandOG'

        if musgraveFlag:
            musgrave = mat.node_tree.nodes.new('ShaderNodeTexMusgrave')
            musgrave.inputs[1].default_value = 20
            musgrave.inputs[2].default_value = 5

            musgraveColorRamp = mat.node_tree.nodes.new('ShaderNodeValToRGB')

            if musgraveFlag == 'ground02':
                groundColor = 0         
            elif musgraveFlag == 'ground03':
                groundColor = 1
            elif musgraveFlag == 'ground08':
                groundColor = 2
            elif musgraveFlag == 'sandOG':
                groundColor = 3
            else:
                groundColor = 1

            groundColor = groundColors[groundColor]
            # musgraveColorRamp.color_ramp.elements[0].color = ([(lRGB[r]*255*3+groundColor[r])/4/255 for r in range(len(lRGB))]+[1.0]) # 75% original color, 25% ground
            musgraveColorRamp.color_ramp.elements[0].color = ([groundColor[r]/255 for r in range(3)]+[1.0])
            musgraveColorRamp.color_ramp.elements[1].color = (166/255,178/255,187/255,1.0)

            mat.node_tree.links.new(musgrave.outputs[0],musgraveColorRamp.inputs[0])
            mat.node_tree.links.new(musgraveColorRamp.outputs[0],diffuse.inputs[0])
            mat.node_tree.links.new(musgraveColorRamp.outputs[0],glossy.inputs[0])
            mat.node_tree.links.new(musgraveColorRamp.outputs[0],mixVolumeSurface.inputs[0])
        return penultimate, penultimateVolume, penultimateDisplacement

    def makeNodes(self,mat,kind,do__assignMaterial,details=None):

        scn.objects.active = self.whichMesh
        bpy.ops.object.select_all(action='DESELECT')
        self.whichMesh.select = True

        self.tryUVUnwrap(self.whichMesh)
        
        penultimate = None
        penultimateVolume = None
        penultimateDisplacement = None

        tool = scrubTool()

        ###
        ###     GROUND WITH PARTICLE SYSTEM
        ###

        if kind in ['sand01','ground02','ground03','ground05','ground08']:
            outputGroup = self.__loadBlendMaterial(kind)
            penultimate = outputGroup

            outputGroup.inputs[0].default_value = 60.0#40.0 # scale
            tool.makeScrub(self.whichMesh)

            blendfile = materialResources + kind + '.blend'
            section = '\\Texture\\'
            directory = blendfile + section
            filename  = kind + '.disp'
            bpy.ops.wm.append(filename=filename, directory=directory)

        elif kind == 'sandOG':
            imageName = 'sandOG.jpg'

            mapping = mat.node_tree.nodes.new('ShaderNodeMapping')
            mapping.vector_type = 'TEXTURE'
            mapping.scale[0] = 0.012#0.02
            mapping.scale[1] = 0.012#0.02
            mapping.scale[2] = 0.012#0.02

            im = mat.node_tree.nodes.new('ShaderNodeTexImage')
            im.image = bpy.data.images.load(materialResources+imageName)
            im.extension = 'REPEAT'
            diffuse = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            texCoord = mat.node_tree.nodes.new('ShaderNodeTexCoord')

            mat.node_tree.links.new(im.outputs[0],diffuse.inputs[0])
            mat.node_tree.links.new(mapping.outputs[0],im.inputs[0])
            mat.node_tree.links.new(texCoord.outputs[2],mapping.inputs[0])
            penultimate = diffuse

            bpy.ops.object.material_slot_add()
            self.whichMesh.material_slots[-1].material = mat
            bpy.ops.object.material_slot_assign()

            self.whichMesh.material_slots[0].material = mat
            bpy.ops.object.material_slot_assign()

            tool.makeScrub(self.whichMesh)

        ###
        ###     GROUND WITHOUT PARTICLE SYSTEM
        ###

        elif kind in ['pavement01','wood_planks02','tile05','tarmac02']:
            outputGroup = self.__loadBlendMaterial(kind)
            penultimate = outputGroup

            if kind == 'pavement01':
                outputGroup.inputs[0].default_value = 30.0 # scale

            elif kind == 'wood_planks02':
                outputGroup.inputs[0].default_value = 40.0 # scale

            elif kind == 'tile05':
                outputGroup.inputs[0].default_value = 100.0 # scale

            elif kind == 'tarmac02':
                outputGroup.inputs[0].default_value = 30.0 # scale

        elif kind == 'industrialOG':
            imageName = 'industrialOG.jpg'

            mapping = mat.node_tree.nodes.new('ShaderNodeMapping')
            mapping.vector_type = 'TEXTURE'
            mapping.scale[0] = 0.02 # 0.01
            mapping.scale[1] = 0.01
            mapping.scale[2] = 0.01

            im = mat.node_tree.nodes.new('ShaderNodeTexImage')
            im.image = bpy.data.images.load(materialResources+imageName)
            im.extension = 'REPEAT'
            diffuse = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            texCoord = mat.node_tree.nodes.new('ShaderNodeTexCoord')

            mat.node_tree.links.new(im.outputs[0],diffuse.inputs[0])
            mat.node_tree.links.new(mapping.outputs[0],im.inputs[0])
            mat.node_tree.links.new(texCoord.outputs[2],mapping.inputs[0])
            penultimate = diffuse

            self.whichMesh.material_slots[0].material = mat
            bpy.ops.object.material_slot_assign()

            tool.makeScrub(self.whichMesh) # for ease of use... will cause problems if gs9 used as grass gravity without grass (grassGravity function fails)

        elif kind == 'musgrave':
            musgrave = mat.node_tree.nodes.new('ShaderNodeTexMusgrave')
            musgrave.inputs[1].default_value = 500 # scale (or 30)
            musgrave.inputs[2].default_value = 10 # detail
            musgrave.inputs[3].default_value = 1.0 # dimension
            musgrave.inputs[4].default_value = 1.5 # lacunarity
            musgrave.inputs[5].default_value = 0 # offset
            musgrave.inputs[6].default_value = 1 # gain

            diffuse = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')

            mat.node_tree.links.new(musgrave.outputs[0],diffuse.inputs[0])
            penultimate = diffuse

            self.whichMesh.material_slots[0].material = mat
            bpy.ops.object.material_slot_assign()

            tool.makeScrub(self.whichMesh) # for ease of use... will cause problems if gs9 used as grass gravity without grass (grassGravity function fails)

        elif kind == 'tetragonal':
            outputGroup = self.__loadBlendMaterial('tile08')
            penultimate = outputGroup

            outputGroup.inputs[0].default_value = 200.0 # scale

            tool.makeScrub(self.whichMesh) # for ease of use... will cause problems if gs9 used as grass gravity without grass (grassGravity function fails)


        ###
        ###     ARCHITECTURE
        ###

        elif kind in ['tile08','rock02','stone02','onyx01','metal01','glass04','concrete04','concrete07']:
            outputGroup = self.__loadBlendMaterial(kind)
            penultimate = outputGroup

            if kind == 'tile08':
                outputGroup.inputs[0].default_value = 15.0  # scale
                outputGroup.inputs[8].default_value = 0.0  # roughness

            elif kind == 'rock02':

                if details == 'Small':
                    outputGroup.inputs[0].default_value = 5.0   # scale

                else:
                    outputGroup.inputs[0].default_value = 1.0   # scale

            elif kind == 'stone02':

                if details == 'Small':
                    outputGroup.inputs[0].default_value = 3.0   # scale

                else:
                    outputGroup.inputs[0].default_value = 1.0 # scale

            elif kind == 'onyx01':
                outputGroup.inputs[0].default_value = 2.0   # scale

            elif kind == 'metal01':
                outputGroup.inputs[0].default_value = 0.5   # scale

            elif kind == 'concrete04':

                if details == 'Small':
                    outputGroup.inputs[0].default_value = 3.0   # scale

                else:
                    outputGroup.inputs[0].default_value = 1.0   # scale

            elif kind == 'concrete07':

                if details == 'Small':
                    outputGroup.inputs[0].default_value = 2.5   # scale

                else:
                    outputGroup.inputs[0].default_value = 0.5   # scale

        elif kind == 'tileOG':
            imageName = 'tileOG.jpg'

            mapping = mat.node_tree.nodes.new('ShaderNodeMapping')
            mapping.vector_type = 'TEXTURE'

            im = mat.node_tree.nodes.new('ShaderNodeTexImage')
            im.image = bpy.data.images.load(materialResources+imageName)
            im.extension = 'REPEAT'
            diffuse = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            texCoord = mat.node_tree.nodes.new('ShaderNodeTexCoord')

            mat.node_tree.links.new(im.outputs[0],diffuse.inputs[0])
            mat.node_tree.links.new(mapping.outputs[0],im.inputs[0])
            mat.node_tree.links.new(texCoord.outputs[2],mapping.inputs[0])
            penultimate = diffuse

            self.whichMesh.material_slots[0].material = mat
            bpy.ops.object.material_slot_assign()

        elif kind == 'wireframe':
            wireMat = bpy.data.materials.new('wireframe')
            wireMat.use_nodes = True

            diffuse = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            mat.node_tree.links.new(diffuse.outputs[0],mat.node_tree.nodes[0].inputs[0])
            penultimate = diffuse

        ###
        ###     MAN-MADE OBJECT
        ###

        elif kind in ['bubble01','car_paint01','clay01','cork01','plastic01','rubber01']:
            outputGroup = self.__loadBlendMaterial(kind)
            penultimate = outputGroup

            if kind == 'clay01':
                outputGroup.inputs[1].default_value = 5.0 # texture scale
                outputGroup.inputs[2].default_value = 5.0 # fingerprint scale
                outputGroup.inputs[3].default_value = 0.3 # fingerprint intensity
                outputGroup.inputs[6].default_value = 0.35 # displacement

            elif kind == 'cork01':
                outputGroup.inputs[1].default_value = 3.0 # scale

        ###
        ###     ROCK OR MINERAL OBJECT
        ###

        elif kind in ['amber01','emerald01','marble04']:
            outputGroup = self.__loadBlendMaterial(kind)
            penultimate = outputGroup

            if kind == 'emerald01':
                outputGroup.inputs[1].default_value = 2.5 # scale

        elif kind == 'marbleOG':
            imageName = 'marbleOG.jpg'
            textureImage = materialResources + imageName
            penultimate = self.__seamBlend(mat,textureImage,kind)

        ###
        ###     METAL OBJECT
        ###

        elif kind in ['gold01','copper01','bronze01','chrome01','aluminum_foil01']:
            outputGroup = self.__loadBlendMaterial(kind)
            penultimate = outputGroup

            if kind == 'gold01':
                outputGroup.inputs[0].default_value = (0.436,0.338,0.115,1.0)  # metal base color
                outputGroup.inputs[1].default_value = (0.353,0.132,0.032,1.0)  # patina base color

            elif kind == 'bronze01':
                outputGroup.inputs[0].default_value = (0.335,0.162,0.069,1.0)  # metal base color
                outputGroup.inputs[1].default_value = (0.253,0.594,0.278,1.0)  # patina base color

            elif kind == 'aluminum_foil01':
                blendfile = materialResources + kind + '.blend'
                section = '\\Texture\\'
                directory = blendfile + section
                filename  = 'aluminum_foil01.disp'
                bpy.ops.wm.append(filename=filename, directory=directory)

                texture = bpy.data.textures['aluminum_foil01.disp']
                texture.noise_scale = 0.03
                texture.intensity = 1.1
                texture.contrast = 0.3
                texture.noise_intensity = 1.01

                bpy.ops.object.modifier_add(type='DISPLACE')
                crush = bpy.context.object.modifiers['Displace']
                crush.name = 'aluminum_foil'
                crush.texture = bpy.data.textures['aluminum_foil01.disp']
                crush.strength = 0.135

        ###
        ###     EDIBLE OBJECT
        ###

        elif kind in ['calamondin01','apple01','lemon01','orange01','tomato01','gelatin01','honey01','peanut_butter01','chocolate02']:
            outputGroup = self.__loadBlendMaterial(kind)
            penultimate = outputGroup

            if kind == 'lemon01':
                outputGroup.inputs[0].default_value = (0.833,0.625,0.044,1.0)  # base color
                outputGroup.inputs[2].default_value = (0.317,0.219,0.014,1.0)  # pit color
                outputGroup.inputs[3].default_value = (0.632,0.360,0.011,1.0)  # subsurface scattering color

            elif kind == 'orange01':
                outputGroup.inputs[0].default_value = (0.800,0.170,0.021,1.0)  # base color
                outputGroup.inputs[2].default_value = (0.800,0.416,0.031,1.0)  # pit color
                outputGroup.inputs[3].default_value = (0.920,0.501,0.114,1.0)  # subsurface scattering color

            if kind == 'gelatin01':
                outputGroup.inputs[6].default_value = 3.0 # scale of jiggle
                outputGroup.inputs[7].default_value = 0.5 # intensity of jiggle

            elif kind == 'peanut_butter01':
                outputGroup.inputs[4].default_value = 2.0 # scale
                outputGroup.inputs[9].default_value = 1.0 # bump intensity


        ###
        ###     SQUISH or STIFF
        ###

        elif kind in ['squish01','squish02','squish03','squish04','squish05']:
            outputGroup = self.__loadBlendMaterial(kind)
            penultimate = outputGroup

        elif kind in ['stiff01','stiff02','stiff03','stiff04','stiff05']:
            outputGroup = self.__loadBlendMaterial(kind)
            penultimate = outputGroup

        ###
        ###     LIVING OBJECT
        ###

        elif kind in ['hedgehog01','fur01','cactus01']:

            blendfile = materialResources + kind + '.blend'
            section = '\\ParticleSettings\\'
            directory = blendfile + section

            if kind == 'hedgehog01':
                # spike material
                spikeGroup = self.__loadBlendMaterial(kind)
                spikeMat = bpy.data.materials[kind]
                spikeMat.name = 'hedgehog_spike'

                # skin material
                outputGroup = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
                penultimate = outputGroup
                outputGroup.inputs[0].default_value = (0.657,0.403,0.244,1.0)
                outputGroup.name = 'hedgehog_skin'

                # do spikes
                filename  = 'hedgehog01.spikes'
                bpy.ops.wm.append(filename=filename, directory=directory)

                bpy.ops.object.particle_system_add()
                particleSystems = [m for m in self.whichMesh.particle_systems if m.name.startswith('ParticleSystem')]
                particleSystem = particleSystems[-1]
                particleSystem.name = 'hedgehog01'
                particleSystem.settings = bpy.data.particles['hedgehog01.spikes']

                particleGroup = bpy.data.particles['hedgehog01.spikes']
                particleGroup.type = 'HAIR'
                particleGroup.name = 'hedgehog01'
                particleGroup.material_slot = 'hedgehog_spike'
                particleGroup.count = 1500
                particleGroup.hair_length = 0.05
                particleGroup.normal_factor = 0.013
                particleGroup.factor_random = 0.0
                particleGroup.brownian_factor = 0.1
                particleGroup.roughness_endpoint = 0.177
                particleGroup.roughness_2 = 0.0
                particleGroup.child_roundness = 1.0
                particleGroup.child_radius = 0.0
                particleGroup.child_length = 0.01
                particleGroup.cycles.root_width = 0.9
                particleGroup.cycles.tip_width = 0.1

            elif kind == 'fur01':
                # spike material
                furGroup = self.__loadBlendMaterial(kind)
                furMat = bpy.data.materials[kind]
                furMat.name = 'fur_spike'

                # skin material
                outputGroup = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
                penultimate = outputGroup
                outputGroup.inputs[0].default_value = (0.800,0.405,0.273,1.0)
                outputGroup.name = 'fur_skin'

                # do spikes
                filename  = 'fur'
                bpy.ops.wm.append(filename=filename, directory=directory)

                bpy.ops.object.particle_system_add()
                particleSystems = [m for m in self.whichMesh.particle_systems if m.name.startswith('ParticleSystem')]
                particleSystem = particleSystems[-1]
                particleSystem.name = 'fur01'
                particleSystem.settings = bpy.data.particles['fur']

                particleGroup = bpy.data.particles['fur']
                particleGroup.type = 'HAIR'
                particleGroup.name = 'fur01'
                particleGroup.material_slot = 'fur_spike'
                particleGroup.count = 1500
                particleGroup.object_align_factor[2] = 0.0
                particleGroup.child_length = 0.6
                particleGroup.hair_length = 0.004
                particleGroup.normal_factor = 0.001
                particleGroup.cycles.root_width = 1.0

            elif kind == 'cactus01':
                # spike material
                cactusMat = bpy.data.materials.new('cactus_spike')
                cactusMat.use_nodes = True
        
                bpy.ops.object.material_slot_add()
                self.whichMesh.material_slots[-1].material = cactusMat
                bpy.ops.object.material_slot_assign()

                hairInfo = cactusMat.node_tree.nodes.new('ShaderNodeHairInfo')
                glossy = cactusMat.node_tree.nodes.new('ShaderNodeBsdfGlossy')
                diffuse = cactusMat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')

                gradient = cactusMat.node_tree.nodes.new('ShaderNodeValToRGB')
                gradient.color_ramp.elements[0].position = 0.0
                gradient.color_ramp.elements[0].color = (0.169,0.123,0.024,1.0)
                gradient.color_ramp.elements[1].position = 0.093
                gradient.color_ramp.elements[1].color = (0.564,0.404,0.071,1.0)
                gradient.color_ramp.elements.new(position=0.665)
                gradient.color_ramp.elements[2].color = (0.595,0.578,0.243,1.0)
                gradient.color_ramp.elements.new(position=0.844)
                gradient.color_ramp.elements[3].color = (0.860,0.720,0.327,1.0)
                gradient.color_ramp.elements.new(position=0.981)
                gradient.color_ramp.elements[4].color = (0.0,0.0,0.0,1.0)

                mix = cactusMat.node_tree.nodes.new('ShaderNodeMixShader')
                mix.inputs[0].default_value = 0.030

                cactusMat.node_tree.links.new(hairInfo.outputs[1],gradient.inputs[0])
                cactusMat.node_tree.links.new(gradient.outputs[0],diffuse.inputs[0])
                cactusMat.node_tree.links.new(diffuse.outputs[0],mix.inputs[1])
                cactusMat.node_tree.links.new(glossy.outputs[0],mix.inputs[2])
                cactusMat.node_tree.links.new(mix.outputs[0],cactusMat.node_tree.nodes[0].inputs[0])

                # skin material
                outputGroup = self.__loadBlendMaterial(kind)
                penultimate = outputGroup
                outputGroup.name = 'cactus_skin'
                outputGroup.inputs[1].default_value = 3.0
                outputGroup.inputs[2].default_value = 0.5

                # do spikes
                filename  = 'thorns'
                bpy.ops.wm.append(filename=filename, directory=directory)

                bpy.ops.object.particle_system_add()
                particleSystems = [m for m in self.whichMesh.particle_systems if m.name.startswith('ParticleSystem')]
                particleSystem = particleSystems[-1]
                particleSystem.name = 'cactus01'
                particleSystem.settings = bpy.data.particles['thorns']

                particleGroup = bpy.data.particles['thorns']
                particleGroup.type = 'HAIR'
                particleGroup.name = 'cactus01'
                particleGroup.material_slot = 'cactus_spike'
                particleGroup.count = 66

        ###
        ###     GLASS
        ###

        elif kind in ['glass02','glass04']:
            outputGroup = self.__loadBlendMaterial(kind)
            penultimate = outputGroup

        elif kind in ['uncorrugatedOG','corrugatedOG']:
            col = mat.node_tree.nodes.new('ShaderNodeBsdfGlass')
            col.inputs[2].default_value = 2.0                       # index of refraction

            if kind == 'corrugatedOG': # "ice"
                bpy.context.scene.update()
                vertsGlobal = [self.whichMesh.matrix_world * v.co for v in self.whichMesh.data.vertices]
                x = [v[0] for v in vertsGlobal]
                y = [v[1] for v in vertsGlobal]
                z = [v[2] for v in vertsGlobal]
                multiplier = max([abs(max(x)-min(x)),abs(max(y)-min(y)),abs(max(z)-min(z))])/100

                corrugationTexture = bpy.data.textures.new('corrugation',type='CLOUDS')
                corrugationTexture.noise_scale = 0.0001
                corrugationTexture.nabla = 0.03
                corrugationTexture.noise_depth = 2.0
                corrugationTexture.contrast = 5.0

                bpy.ops.object.modifier_add(type='DISPLACE')
                corrugation = bpy.context.object.modifiers['Displace']
                corrugation.name = 'corrugation'
                corrugation.texture = corrugationTexture
                corrugation.strength = multiplier

            col.name = kind
            penultimate = col

        ###
        ###     WOOD OBJECT
        ###

        elif kind == 'woodOG':
            imageName = 'woodOG.jpg'
            textureImage = materialResources + imageName
            penultimate = self.__seamBlend(mat,textureImage,kind)

        elif kind == 'paperOG':
            imageName = 'paperOG.jpg'
            textureImage = materialResources + imageName
            penultimate = self.__seamBlend(mat,textureImage,kind)

        ###
        ###     ASSIGN MATERIAL
        ###

        if penultimate.type == 'GROUP':

            if 'Volume' not in [vol.name for vol in outputGroup.node_tree.outputs]:
                outputGroup.node_tree.outputs.new('NodeSocketShader','Volume')

            if 'Displacement' not in [disp.name for disp in outputGroup.node_tree.outputs]:
                outputGroup.node_tree.outputs.new('NodeSocketColor','Displacement')

            outputGroupNode = [n for n in outputGroup.node_tree.nodes if n.name.startswith('Group Output')][0]
            materialOutput = [n for n in outputGroup.node_tree.nodes if n.name.startswith('Material Output')]

            if materialOutput:
                materialOutput = materialOutput[0]

                if do__assignMaterial:
                    mat.node_tree.links.new(outputGroup.outputs[0],mat.node_tree.nodes[0].inputs[0])

                if materialOutput.inputs[1].links:
                    penultimateVolume = materialOutput.inputs[1].links[0].from_node
                    outputGroup.node_tree.links.new(penultimateVolume.outputs[0],outputGroupNode.inputs[1])

                    if do__assignMaterial:
                        mat.node_tree.links.new(outputGroup.outputs[1],mat.node_tree.nodes[0].inputs[1])

                if materialOutput.inputs[2].links:
                    penultimateDisplacement = materialOutput.inputs[2].links[0].from_node
                    outputGroup.node_tree.links.new(penultimateDisplacement.outputs[0],outputGroupNode.inputs[2])

                    if do__assignMaterial:
                        mat.node_tree.links.new(outputGroup.outputs[2],mat.node_tree.nodes[0].inputs[2])

                outputGroup.node_tree.nodes.remove(materialOutput)

            else:
                mat.node_tree.links.new(penultimate.outputs[0],mat.node_tree.nodes[0].inputs[0])

                if do__assignMaterial:
                    mat.node_tree.links.new(outputGroup.outputs[0],mat.node_tree.nodes[0].inputs[0])

                if outputGroup.inputs[1].links:
                    penultimateVolume = outputGroup.inputs[1].links[0].from_node

                    if do__assignMaterial:
                        mat.node_tree.links.new(outputGroup.outputs[1],mat.node_tree.nodes[0].inputs[1])

                if outputGroup.inputs[2].links:
                    penultimateDisplacement = outputGroup.inputs[2].links[0].from_node

                    if do__assignMaterial:
                        mat.node_tree.links.new(outputGroup.outputs[2],mat.node_tree.nodes[0].inputs[2])

        else:

            if do__assignMaterial:
                mat.node_tree.links.new(penultimate.outputs[0],mat.node_tree.nodes[0].inputs[0])

                if penultimateVolume:
                    mat.node_tree.links.new(penultimateVolume.outputs[0],mat.node_tree.nodes[0].inputs[1])

                if penultimateDisplacement:
                    mat.node_tree.links.new(penultimateDisplacement.outputs[0],mat.node_tree.nodes[0].inputs[2])

        return penultimate, penultimateVolume, penultimateDisplacement # may be a group or a shader

    ###
    ###     SEAM BLEND PROTOCOL
    ###

    def __seamBlend(self,mat,textureImage,kind):

        texTree = mat.node_tree.nodes
        makeLink = mat.node_tree.links

        # NODE GROUP
        # Dorsal Stream
        texCoord = texTree.new('ShaderNodeTexCoord')
        normal_1 = texTree.new('ShaderNodeNormal')
        normal_1.outputs[0].default_value = (0.05,-0.998,-0.05)
        multiply_1 = texTree.new('ShaderNodeMath')
        multiply_1.operation = 'MULTIPLY'
        multiply_1.inputs[1].default_value = -1.0
        add_1 = texTree.new('ShaderNodeMixRGB')
        add_1.blend_type = 'ADD'
        add_1.inputs[0].default_value = 1.0
        mix_1 = texTree.new('ShaderNodeMixRGB')
        mix_1.blend_type = 'MIX'
        colorRamp_1_1 = texTree.new('ShaderNodeValToRGB')
        colorRamp_1_1.color_ramp.interpolation = 'EASE'
        colorRamp_1_1.color_ramp.elements[0].position = 0.423
        colorRamp_1_1.color_ramp.elements[1].position = 0.882
        colorRamp_1_2 = texTree.new('ShaderNodeValToRGB')
        colorRamp_1_2.color_ramp.interpolation = 'EASE'
        colorRamp_1_2.color_ramp.elements[0].position = 0.514
        colorRamp_1_2.color_ramp.elements[1].position = 0.923

        makeLink.new(texCoord.outputs[1],normal_1.inputs[0])
        makeLink.new(normal_1.outputs[1],colorRamp_1_1.inputs[0])
        makeLink.new(normal_1.outputs[1],multiply_1.inputs[0])
        makeLink.new(multiply_1.outputs[0],colorRamp_1_2.inputs[0])
        makeLink.new(colorRamp_1_1.outputs[0],add_1.inputs[1])
        makeLink.new(colorRamp_1_2.outputs[0],add_1.inputs[2])
        makeLink.new(add_1.outputs[0],mix_1.inputs[0])

        # NODE GROUP
        # Ventral Stream
        diffuse = texTree.new('ShaderNodeBsdfDiffuse')
        normal_2 = texTree.new('ShaderNodeNormal')
        normal_2.outputs[0].default_value = (-0.992,-0.1,-0.129)
        multiply_2 = texTree.new('ShaderNodeMath')
        multiply_2.operation = 'MULTIPLY'
        multiply_2.inputs[1].default_value = -1.0
        add_2 = texTree.new('ShaderNodeMixRGB')
        add_2.blend_type = 'ADD'
        add_2.inputs[0].default_value = 1.0
        mix_2 = texTree.new('ShaderNodeMixRGB')
        mix_2.blend_type = 'MIX'
        colorRamp_2_1 = texTree.new('ShaderNodeValToRGB')
        colorRamp_2_1.color_ramp.interpolation = 'EASE'
        colorRamp_2_1.color_ramp.elements[0].position = 0.305
        colorRamp_2_1.color_ramp.elements[1].position = 0.668
        colorRamp_2_2 = texTree.new('ShaderNodeValToRGB')
        colorRamp_2_2.color_ramp.interpolation = 'EASE'
        colorRamp_2_2.color_ramp.elements[0].position = 0.286
        colorRamp_2_2.color_ramp.elements[1].position = 0.741

        makeLink.new(texCoord.outputs[1],normal_2.inputs[0])
        makeLink.new(normal_2.outputs[1],colorRamp_2_1.inputs[0])
        makeLink.new(normal_2.outputs[1],multiply_2.inputs[0])
        makeLink.new(multiply_2.outputs[0],colorRamp_2_2.inputs[0])
        makeLink.new(colorRamp_2_1.outputs[0],add_2.inputs[1])
        makeLink.new(colorRamp_2_2.outputs[0],add_2.inputs[2])
        makeLink.new(add_2.outputs[0],mix_2.inputs[0])
        makeLink.new(mix_2.outputs[0],mix_1.inputs[1])
        makeLink.new(mix_1.outputs[0],diffuse.inputs[0])

        # INPUTS TO NODE GROUP
        texCoord_2 = texTree.new('ShaderNodeTexCoord')
        front = texTree.new('ShaderNodeTexImage')
        front.image = bpy.data.images.load(textureImage)
        front.texture_mapping.mapping_x = 'X'
        front.texture_mapping.mapping_y = 'Z'
        front.texture_mapping.mapping_z = 'Z'
        top = texTree.new('ShaderNodeTexImage')
        top.image = bpy.data.images.load(textureImage)
        top.texture_mapping.mapping_x = 'Y'
        top.texture_mapping.mapping_y = 'X'
        top.texture_mapping.mapping_z = 'Z'
        side = texTree.new('ShaderNodeTexImage')
        side.image = bpy.data.images.load(textureImage)
        side.texture_mapping.mapping_x = 'Y'
        side.texture_mapping.mapping_y = 'Z'
        side.texture_mapping.mapping_z = 'Z'

        makeLink.new(texCoord_2.outputs[0],front.inputs[0])
        makeLink.new(texCoord_2.outputs[0],top.inputs[0])
        makeLink.new(texCoord_2.outputs[0],side.inputs[0])
        makeLink.new(front.outputs[0],mix_1.inputs[2])
        makeLink.new(top.outputs[0],mix_2.inputs[1])
        makeLink.new(side.outputs[0],mix_2.inputs[2])

        if kind == 'paperOG':
            paperTexture = bpy.data.textures.new('paper',type='MUSGRAVE')
            paperTexture.intensity = 1.0
            paperTexture.contrast = 0.1
            paperTexture.lacunarity = 3.0
            paperTexture.noise_intensity = 1.01
            paperTexture.noise_scale = 0.0001

            bpy.ops.object.modifier_add(type='DISPLACE')
            crush = bpy.context.object.modifiers['Displace']
            crush.name = 'paper'
            crush.texture = paperTexture
            crush.texture_coords = 'UV'
            crush.strength = 0.1

        diffuse.name = kind
        penultimate = diffuse
        return penultimate


###
###         SCRUB TOOL
###

class scrubTool:

    kind = 'Scrub Generation Toolkit'

    def __init__(self):

        self.surface = None
        self.groups = []

    def makeScrub(self,whichMesh):

        self.surface = whichMesh

        self.__stereotypicalGrass()

        bpy.context.scene.objects.active = self.surface
        bpy.ops.object.select_all(action='DESELECT')
        whichMesh.select = True

        particlesOrig = [p for p in bpy.data.particles]
        bpy.ops.object.particle_system_add()
        particleSystems = [m for m in self.surface.particle_systems if m.name.startswith('ParticleSystem')]
        particleSystem = particleSystems[-1]
        particleSystem.name = 'scrub'
        whichMesh.data.update()

        #particleSystem.vertex_group_density = 'Sv_VGroup'

        particles = [p for p in bpy.data.particles]
        particleGroup = [p for p in particles if p not in particlesOrig][0]
        particleGroup.type = 'HAIR'
        particleGroup.name = 'scrub'

        particleGroup.render_type = 'GROUP'
        particleGroup.dupli_group = self.groups[-1]
        particleGroup.use_rotation_dupli = True

        particleGroup.hair_length = 0.5#2.0 #4.0
        particleGroup.size_random = 1.0
        particleGroup.particle_size = 0.03#0.03
        particleGroup.child_type = 'INTERPOLATED'
        particleGroup.child_length = 0.5
        particleGroup.roughness_1_size = 10
        particleGroup.clump_factor = -0.118518

        particleGroup.use_advanced_hair = True
        particleGroup.use_rotations = True
        particleGroup.rotation_mode = 'OB_X'

        particleGroup.count = 150
        particleGroup.child_nbr = 200#100 #75
        particleGroup.rendered_child_count = 200#100 #75

        bpy.ops.texture.new()
        tex = bpy.data.textures[0]
        tex.type = 'VORONOI'
        slot = particleGroup.texture_slots.add()
        slot.texture = tex
        slot.use_map_length = True
        slot.use_map_clump = True
        return

    def __stereotypicalGrass(self):

        # load plants for grouping
        numVarieties = 4

        # # redirect output to log file
        # logfile = 'blender_render.log'
        # open(logfile, 'a').close()
        # old = os.dup(1)
        # sys.stdout.flush()
        # os.close(1)
        # os.open(logfile, os.O_WRONLY)

        for hue in range(numVarieties):
            bpy.ops.wm.collada_import(filepath=materialResources+'scrubBlockPlantFinal.dae')

        # add plants to group
        plants1 = [p for p in bpy.context.scene.objects if p.name.startswith('Plant1')][0:4]
        plants2 = [p for p in bpy.context.scene.objects if p.name.startswith('Plant2')][0:4]

        previousGroups = [g for g in bpy.data.groups]
        bpy.ops.object.group_add()
        newGroups = [g for g in bpy.data.groups]
        newGroup = [g for g in newGroups if g not in previousGroups][0]

        newGroup.name = 'Grasses'
        self.groups.append(newGroup)

        # resize and color plant1
        for hue in range(numVarieties):
            plant = plants1[hue]

            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = plant
            plant.select = True
            plant.location = Vector((0,0,4000))
            bpy.ops.transform.resize(value=(1.5,1.5,1.5),constraint_axis=(True, True, True))
            bpy.ops.object.transform_apply(scale=True)
            bpy.ops.object.group_link(group=newGroup.name)
            self.__plantHue(plant,hue)

        # resize and color plant2
        for hue in range(numVarieties):
            plant = plants2[hue]

            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = plant
            plant.select = True
            plant.location = Vector((0,0,4000))
            bpy.ops.transform.resize(value=(1.5,1.5,1.5),constraint_axis=(True, True, True))
            bpy.ops.object.transform_apply(scale=True)
            bpy.ops.object.group_link(group=newGroup.name)
            self.__plantHue(plant,hue+4)

        # # disable output redirection
        # os.close(1)
        # os.dup(old)
        # os.close(old)

        return

    def __plantHue(self,plant,plantHue):

        lighten = 0.0 # maximum 1.0 - 0.289 (0.711)
        sand = (0.402,0.309,0.283,1.0)

        if plantHue == 0:
            middle = (0.208+lighten,0.160+lighten,0.145+lighten,1.0)
            dark = (0.014,0.010,0.007,1.0)
            light = (0.143+lighten,0.086+lighten,0.039+lighten,1.0)
            plant.rotation_euler[2] = math.pi*0/2

        elif plantHue == 1:
            middle = (0.228+lighten,0.162+lighten,0.145+lighten,1.0)
            dark = (0.054,0.014,0.007,1.0)
            light = (0.100+lighten,0.085+lighten,0.040+lighten,1.0)
            plant.rotation_euler[2] = math.pi*1/2

        elif plantHue == 2:
            middle = (0.213+lighten,0.160+lighten,0.145+lighten,1.0)
            dark = (0.024,0.010,0.007,1.0)
            light = (0.130+lighten,0.100+lighten,0.045+lighten,1.0)
            plant.rotation_euler[2] = math.pi*2/2

        elif plantHue == 3:
            middle = (0.213+lighten,0.160+lighten,0.145+lighten,1.0)
            dark = (0.024,0.010,0.007,1.0)
            light = (0.289+lighten,0.220+lighten,0.095+lighten,1.0)
            plant.rotation_euler[2] = math.pi*3/2

        elif plantHue == 4:
            middle = (0.218+lighten,0.160+lighten,0.145+lighten,1.0)
            dark = (0.034,0.010,0.007,1.0)
            light = (0.050+lighten,0.039+lighten,0.019+lighten,1.0)
            plant.rotation_euler[2] = math.pi*0/2

        elif plantHue == 5:
            middle = (0.214+lighten,0.158+lighten,0.144+lighten,1.0)
            dark = (0.026,0.007,0.005,1.0)
            light = (0.183+lighten,0.140+lighten,0.062+lighten,1.0)
            plant.rotation_euler[2] = math.pi*1/2

        elif plantHue == 6:
            middle = (0.222+lighten,0.160+lighten,0.145+lighten,1.0)
            dark = (0.042,0.010,0.007,1.0)
            light = (0.084+lighten,0.044+lighten,0.021+lighten,1.0)
            plant.rotation_euler[2] = math.pi*2/2

        elif plantHue == 7:
            middle = (0.241+lighten,0.182+lighten,0.152+lighten,1.0)
            dark = (0.080,0.054,0.021,1.0)
            light = (0.130+lighten,0.110+lighten,0.055+lighten,1.0)
            plant.rotation_euler[2] = math.pi*3/2

        matGradient = bpy.data.materials.new('Mat')
        matGradient.use_nodes = True

        texCoord = matGradient.node_tree.nodes.new('ShaderNodeTexCoord')
        texGradient = matGradient.node_tree.nodes.new('ShaderNodeTexGradient')

        mix = matGradient.node_tree.nodes.new('ShaderNodeMixShader')
        subsurf = matGradient.node_tree.nodes.new('ShaderNodeSubsurfaceScattering')
        diffuse = matGradient.node_tree.nodes[1]

        mapping = matGradient.node_tree.nodes.new('ShaderNodeMapping')
        mapping.rotation[0] = 0.0
        mapping.rotation[1] = math.pi/2
        mapping.rotation[2] = 275 * math.pi/180

        gradient = matGradient.node_tree.nodes.new('ShaderNodeValToRGB')
        gradient.color_ramp.elements[0].position = 0.0
        gradient.color_ramp.elements[0].color = sand
        gradient.color_ramp.elements[1].position = 0.050
        gradient.color_ramp.elements[1].color = middle
        gradient.color_ramp.elements.new(position=0.209)
        gradient.color_ramp.elements[2].color = dark
        gradient.color_ramp.elements.new(position=1.0)
        gradient.color_ramp.elements[3].color = light

        matGradient.node_tree.links.new(texCoord.outputs[0],mapping.inputs[0])
        matGradient.node_tree.links.new(mapping.outputs[0],texGradient.inputs[0])
        matGradient.node_tree.links.new(texGradient.outputs[1],gradient.inputs[0])
        matGradient.node_tree.links.new(gradient.outputs[0],diffuse.inputs[0])
        matGradient.node_tree.links.new(gradient.outputs[0],subsurf.inputs[0])
        matGradient.node_tree.links.new(diffuse.outputs[0],mix.inputs[1])
        matGradient.node_tree.links.new(subsurf.outputs[0],mix.inputs[2])
        matGradient.node_tree.links.new(mix.outputs[0],matGradient.node_tree.nodes[0].inputs[0])

        bpy.ops.object.material_slot_add()
        plant.material_slots[0].material = matGradient
        bpy.ops.object.material_slot_assign()

        bpy.ops.object.modifier_add(type='SOLIDIFY')
        solidify = bpy.context.object.modifiers['Solidify']
        solidify.thickness = 0.1
        bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Solidify')

        bpy.ops.object.modifier_add(type='SMOOTH')
        smooth = bpy.context.object.modifiers['Smooth']
        smooth.factor = 0.5
        bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Smooth')
        return

    def editDensityWeightPaint(self,whichMesh,details):

        self.surface = whichMesh

        scn.objects.active = self.surface
        bpy.ops.object.select_all(action='DESELECT')
        whichMesh.select = True

        verts = whichMesh.data.vertices
        xMin = details[0]
        xMax = details[1]
        yMin = details[2]
        yMax = details[3]
        leeway = details[4]

        # bpy.ops.paint.weight_gradient() api context problem
        # workaround: Ko. on blenderartists.org forum: https://blenderartists.org/forum/showthread.php?400534-Weight-Paint-Scripting-Context-Issue

        accessWP = [sv for sv in whichMesh.vertex_groups if sv.name.startswith('Sv_VGroup')]

        if len(accessWP) == 0:
            whichMesh.vertex_groups.new(name='Sv_VGroup')
            accessWP = [sv for sv in whichMesh.vertex_groups if sv.name.startswith('Sv_VGroup')]

        obVertexGroup = accessWP[0]

        for vertex in verts:
            vertGlobal = whichMesh.matrix_world * vertex.co

            if details[0] == None:
                obVertexGroup.add([vertex.index],1.1-(vertex.co.y+1)/50,'REPLACE')

            else:

                if vertGlobal[0] > (xMin-leeway) and vertGlobal[0] < (xMax+leeway) and vertGlobal[1] > (yMin-leeway) and vertGlobal[1] < (yMax+leeway):
                    obVertexGroup.add([vertex.index],0.0,'REPLACE')

                else:
                    obVertexGroup.add([vertex.index],1.1-(vertex.co.y+1)/50,'REPLACE')

        existingParticleSystemUser = [m for m in whichMesh.particle_systems if m.name.startswith('scrub')]

        if existingParticleSystemUser:
            existingParticleSystemUser[0].vertex_group_density = 'Sv_VGroup'

        return

    def sphericalBessel(self,whichMesh,xOffset,yOffset):

        self.surface = whichMesh

        bpy.context.scene.objects.active = self.surface
        bpy.ops.object.select_all(action='DESELECT')
        whichMesh.select = True

        protrusion = 5
        # positive protrusion is convex
        # negative protrusion is concave
        # 0 is flat plane

        saturation = 5 
        # normalization factor

        verts = whichMesh.data.vertices
        accessWP = [sv for sv in whichMesh.vertex_groups if sv.name.startswith('soilMound')]

        if len(accessWP) == 0:
            whichMesh.vertex_groups.new(name='soilMound')
            accessWP = [sv for sv in whichMesh.vertex_groups if sv.name.startswith('soilMound')]

        obVertexGroup = accessWP[0]

        for vertex in verts:
            obVertexGroup.add([vertex.index],((protrusion*(1-((vertex.co.x+xOffset)**2+(vertex.co.y+yOffset)**2)))/saturation+1)/2,'REPLACE')

        return

    def bumpWeightPaint(self,whichMesh,kd,shiftDistance,bounds):

        self.surface = whichMesh

        scn.objects.active = self.surface
        bpy.ops.object.select_all(action='DESELECT')
        whichMesh.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.tris_convert_to_quads()

        accessWP = [sv for sv in whichMesh.vertex_groups if sv.name.startswith('soilBump')]

        if len(accessWP) == 0:
            whichMesh.vertex_groups.new(name='soilBump')
            accessWP = [sv for sv in whichMesh.vertex_groups if sv.name.startswith('soilBump')]

        weightVertexGroup = accessWP[0]

        scn.update()
        weightVerts = whichMesh.data.vertices
        weightVertsGlobal = [whichMesh.matrix_world * v.co for v in weightVerts]

        imp = bounds[0]
        threshold = 0.3
        # threshold = 0.65

        fullIndices = []

        for i,v in enumerate(weightVertsGlobal):
            vertex = Vector((v[0],v[1],0.0))
            co,index,dist = kd.find(vertex)

            if dist <= imp + threshold:
                fullIndices.append(i)

            # if dist <= threshold:
            #     fullIndices.append(i)

        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        faces = bmesh.from_edit_mesh(whichMesh.data).faces

        for face in faces:
            face.select = False

            for v in face.verts:

                if v.index in fullIndices:
                    face.select = True

        if whichMesh.name == 'Pedestal':
            bpy.ops.mesh.subdivide(number_cuts=1)
        else:
            bpy.ops.mesh.subdivide(number_cuts=100)

        bpy.ops.object.mode_set(mode='OBJECT')

        weightVerts = whichMesh.data.vertices
        weightVertsGlobal = [whichMesh.matrix_world * v.co for v in weightVerts]

        for i,v in enumerate(weightVertsGlobal):
            vertex = Vector((v[0],v[1],0.0))
            co,index,dist = kd.find(vertex)
            weightVertexGroup.add([i],(1.0-(dist*5.0))*1,'REPLACE')

            if dist > 0.2*2:
                weightVertexGroup.add([i],0.0,'REPLACE')

        return

###
###         MASS TOOL
###

class massTool:

    kind = 'Mass Generation Toolkit'

    def __init__(self):

        self.whichMesh = None

    def __vertexColor(self,alden):
        # generate new vertex groups ('WeightParticle') which threshold auto weight map vertex groups to emphasize component ownership (application: material particle system weight maps)
        # generate corresponding bw vertex color maps ('WeightColor') (application: weight maps for basic material node group shader and property assignment)
        # generate one additional vertex group ('WholeWeightParticle') and one additional vertex color map ('WholeWeightColor') to cover body material particle system and node group assignments
        # could later expand this to support segmented multilimb single-material situations


        # easier if we just go through limbComps and delete double representation
        # then, loop through lmibComps
        # if whichComp is in tagged comps, meld will handle it.
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.mesh
        alden.mesh.select = True

        # limbCompsAll = [g.name for g in alden.mesh.vertex_groups if g.name.startswith('Comp')]
        allUVs = [g.name for g in alden.mesh.vertex_groups]
        limbCompsAll = [g.name for g in alden.mesh.vertex_groups if g.name.startswith('Comp')]
        limbComps = [g.name for g in alden.mesh.vertex_groups if g.name.startswith('Comp')]

        for meld in alden.taggedComps:
            original = meld[0]
            partner = meld[1]

            if original in limbComps and partner in limbComps:
                del limbComps[limbComps.index(partner)]

        # now only working with a list of unpartnered limbComps
        verts = alden.mesh.data.vertices
        
        maxWeightThreshold = 0.6
        vertGroupIndTaken = []
        surfaceAreas = []

        for vertGroupInd in alden.affectedLimbs:                                        # gonna need to loop through 'Comp' groups... only make weightcolors for affected limbs
            
            if limbCompsAll[vertGroupInd] in vertGroupIndTaken:                         # if the current 'Comp' group index has already been associated with a vertex group and vertex color layer,
                continue                                                                # skip this loop

            else:                                                                       # otherwise, continue the loop              
                vertGroupIndTaken.append(allUVs.index(limbCompsAll[vertGroupInd]))      # and record the index
                vertGroupIndTaken.append(limbCompsAll[vertGroupInd])                    # and record the name of the 'Comp' group associated with that index

            storeSurfaceArea = 0

            alden.mesh.vertex_groups.new('WeightParticle')                              # generate a new 'WeightParticle' layer to host the modified 'Comp' group
            particle_layer = alden.mesh.vertex_groups[-1]

            alden.mesh.data.vertex_colors.new('WeightColor')                            # generate a new 'WeightColor' layer to host the modified 'Comp' group's vertex colors
            color_layer = alden.mesh.data.vertex_colors[-1]
            ii = 0

            for poly in alden.mesh.data.polygons:                                       # for each polygon in the mesh,
                storeDataIndex = []
                storeVertIndex = []
                storeSurfaceArea += poly.area

                vertInd = poly.vertices                                                 # find the indices of the 3 vertices of the polygon within the verts list
                vertIdent = [verts[v] for v in vertInd]                                 # and extract the 3 vertices of the polygon, themselves

                for vert in vertIdent:                                                  # for each vertex of the polygon,
                    colVertGroupInd = [v.group for v in vert.groups]                    # find the indices of 'Comp' groups for which vertex is painted
                    whichComp = limbCompsAll[vertGroupInd]                                 # find the name of the 'Comp' group being considered
                    # should be good here... get one of the affected limbs' names
                    # colVertGroupInd has group indices for ALL comp groups
                    whichCompTrueIndex = allUVs.index(whichComp)
                    # whichCompTrueIndex = limbCompsAll.index(whichComp)

                    if whichCompTrueIndex in colVertGroupInd:                                 # if the current 'Comp' group index is one of these painted indices,
                        groupPosition = colVertGroupInd.index(whichCompTrueIndex)             # find which of the painted indices corresponds to the current index
                        weight = vert.groups[groupPosition].weight                      # find the weight of the vertex for the current 'Comp' group

                        if alden.blocky:                                                # binary weighting for blocky stimuli (no gradient transition)

                            if weight > maxWeightThreshold:
                                weight = 1.0

                            else:
                                weight = 0.0

                    else:                                                                       # if not,
                        weight = 0.0                                                            # apply black to the vertex colors map in the vertex position   

                    for meld in alden.taggedComps:                                              # examine each of the 'Comp' group pairs that must be joined
                        
                        if whichComp in meld:                                                   # if the 'Comp' group being considered is in one of the 'Comp' group pairs to be joined,
                            nonmatchName = [c for c in meld if c != whichComp][0]               # find the name of the partner 'Comp' group
                            vertGroupIndPartner = allUVs.index(nonmatchName)                 # find the overall index of the partner 'Comp' group
                            # vertGroupIndPartner = limbCompsAll.index(nonmatchName)    

                            if vertGroupIndPartner in colVertGroupInd:                          # if the partner 'Comp' group index is also one of the painted indices

                                if vertGroupIndPartner not in vertGroupIndTaken:                # and if the partner 'Comp' has not alreaady been associated with a vertex group and vertex color layer,
                                    vertGroupIndTaken.append(vertGroupIndPartner)               # record the index of the partner 'Comp' group
                                    vertGroupIndTaken.append(nonmatchName)                      # and record its name

                                groupPosition = colVertGroupInd.index(vertGroupIndPartner)      # find which of the painted indices corresponds to the partner index
                                weightPartner = vert.groups[groupPosition].weight               # find the weight of the vertex for the partner 'Comp' group

                                if alden.blocky:                                                # binary weighting for blocky stimuli (no gradient transition)

                                    if weightPartner > maxWeightThreshold:
                                        weightPartner = 1.0

                                    else:
                                        weightPartner = 0.0
                            
                                if weightPartner > weight:                                      # use the larger of the two weights for the final weight of the vertex in the merged vertex group and vertex color layer
                                    weight = weightPartner

                    if weight > maxWeightThreshold:                                             # above a threshold raw weight, produce a default weight of 1.0
                        weight = 1.0

                    else: 
                        weight += math.exp(weight*1.5) + (1.0 - math.exp(0.5*1.5))              # below a raw weight of 0.6, produce an exponential decrease in weight       

                    color_layer.data[ii].color = (weight,weight,weight)                     # apply the final weight (bw) to the vertex colors map in the vertex position
                    particle_layer.add([vert.index],weight,'REPLACE')                           # create a corresponding vertex group for particle density and length assignments

                    storeDataIndex.append(ii)
                    storeVertIndex.append(vert.index)
                    ii += 1

                # give materials on blocky objects hard edges 
                if alden.blocky:

                    polyWeightSum = sum([color_layer.data[dataIndex].color[0] for dataIndex in storeDataIndex])

                    if polyWeightSum > 2:
                        weight = 1.0

                    else:
                        weight = 0.0

                    for dataIndex in storeDataIndex:
                        color_layer.data[dataIndex].color = (weight,weight,weight)
                        
                    for vertIndex in storeVertIndex:
                        particle_layer.add([vertIndex],weight,'REPLACE')

            surfaceAreas.append(storeSurfaceArea)

        # outfit the remainder of the body
        wholeWeightSurfaceArea = 0

        alden.mesh.vertex_groups.new('WholeWeightParticle')                             # generate a new 'WeightParticle' layer to host the remainder of the body
        wholeParticle = alden.mesh.vertex_groups[-1]

        alden.mesh.data.vertex_colors.new('WholeWeightColor')                           # generate a new 'WeightColor' layer to host the remainder of the body
        wholeWeight = alden.mesh.data.vertex_colors[-1]
        ii = 0

        for poly in alden.mesh.data.polygons:
            vertInd = poly.vertices
            vertIdent = [verts[v] for v in vertInd]

            for vert in vertIdent:
                gradients = [g for g in alden.mesh.data.vertex_colors if g.name.startswith('WeightColor')]
                colorLayers = [color_layer.data[ii] for color_layer in gradients]
                weight = 1.0-sum([colorData.color[0] for colorData in colorLayers])
                wholeWeight.data[ii].color = (weight,weight,weight)
                wholeParticle.add([vert.index],weight,'REPLACE')
                ii += 1

            wholeWeightSurfaceArea += poly.area

        alden.surfaceAreas = surfaceAreas
        alden.wholeWeightSurfaceArea = wholeWeightSurfaceArea
        return

    def separateForDensityAssignment(self,alden):

        self.__vertexColor(alden)

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.mesh
        alden.mesh.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_clean(group_select_mode='ALL',limit=0.6)

        limbParticles = [p for p in alden.mesh.vertex_groups if p.name.startswith('WeightParticle')]

        for limb in range(len(limbParticles)):
            limbParticles = [p for p in alden.mesh.vertex_groups if p.name.startswith('WeightParticle')]

            # separate mesh into constituent meshes by selection
            bpy.ops.mesh.select_all(action='DESELECT')
            limbWeight = limbParticles[limb]
            bpy.ops.object.vertex_group_set_active(group=limbWeight.name)
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.vertex_group_deselect()

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.mesh
        alden.mesh.select = True
        self.makeRigidBody(alden.mesh,'ACTIVE')
        self.assignMass(alden.mesh,alden.material)

        aldenObjects = [a for a in bpy.data.objects if a.name.startswith('AldenObject')]

        for ind in range(1,len(aldenObjects)):
            aldenObjects = [a for a in bpy.data.objects if a.name.startswith('AldenObject')]

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = aldenObjects[ind]
            aldenObjects[ind].select = True
            self.makeRigidBody(aldenObjects[ind],'ACTIVE')
            self.assignMass(aldenObjects[ind],alden.limbMaterials[ind-1])

        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = alden.mesh

        for ind in range(len(aldenObjects)):
            aldenObjects = [a for a in bpy.data.objects if a.name.startswith('AldenObject')]
            aldenObjects[ind].select = True

        bpy.ops.rigidbody.connect(con_type='FIXED',pivot_type='ACTIVE')
        constraint = bpy.data.objects['Constraint']
        constraint.name = 'SeparationConstraint'
        return

    def assignMass(self,whichMesh,material):

        self.whichMesh = whichMesh

        if material == 'bubble01':
            den = 0.0013                                                    # g/cm3 (dry air: IUPAC stp, 0C and 100 kPa)

        elif material == 'car_paint01':
            den = 7.85                                                      # g/cm3 (steel)

        elif material == 'clay01':
            den = 2.2                                                       # g/cm3

        elif material == 'cork01':
            den = 0.22                                                      # g/cm3

        elif material == 'plastic01':
            den = 1.19                                                      # g/cm3 1.36 bakelite 1.6 cpvc

        elif material == 'rubber01':
            den = 1.2                                                       # g/cm3

        elif material == 'amber01':
            den = 1.2                                                       # g/cm3

        elif material == 'emerald01':
            den = 2.76                                                      # g/cm3

        elif material in ['marble04','marbleOG']:
            den = 2.7                                                       # g/cm3

        elif material == 'gold01':
            den = 19.32                                                     # g/cm3

        elif material == 'copper01':
            den = 8.96                                                      # g/cm3

        elif material == 'bronze01':
            den = 8.7                                                       # g/cm3

        elif material == 'chrome01':
            den = 7.19                                                      # g/cm3 (chromium)

        elif material == 'aluminum_foil01':
            den = 2.700                                                     # g/cm3

        elif material == 'calamondin01':
            den = 0.55                                                      # g/cm3 (guess based on lemon, orange)

        elif material == 'apple01':
            den = 0.61                                                      # g/cm3

        elif material == 'lemon01':
            den = 0.64                                                      # g/cm3

        elif material == 'orange01':
            den = 0.48                                                      # g/cm3

        elif material == 'tomato01':
            den = 0.48                                                      # g/cm3

        elif material == 'gelatin01':
            den = 1.3                                                       # g/cm3

        elif material == 'honey01':
            den = 1.36                                                      # g/cm3

        elif material == 'peanut_butter01':
            den = 1.09                                                      # g/cm3

        elif material == 'chocolate02':
            den = 0.56                                                      # g/cm3

        elif material == 'hedgehog01':
            den = 0.94                                                      # g/cm3 (definitely floats in water, but difficult to source)

        elif material == 'fur01':
            den = 1.02                                                      # g/cm3 (human density)

        elif material == 'cactus01':
            den = 1.5                                                       # g/cm3 (cactus pear fruit density)

        elif material in ['glass02','glass04','uncorrugatedOG']:
            den = 2.6                                                       # g/cm3

        elif material == 'corrugatedOG':
            den = 0.92                                                      # (ice)

        elif material == 'woodOG':
            den = 0.7                                                       # g/cm3

        elif material == 'paperOG':
            den = 0.7*0.1                                                   # g/cm3 (crumpled paper is at least 90% air)  ***

        else:
            den = 1.0                                                       # g/cm3 (water)

        self.__setMass(den)
        return

    def __setMass(self,den):

        # den = 1.0
        # totalVolume = self.__determineVolume()                          # in m^3
        # mass = (den*1000 * totalVolume)                                 # in kg/m^3
        # self.whichMesh.rigid_body.mass = mass                           # in kg

        scn.update()
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = self.whichMesh
        self.whichMesh.select = True
        bpy.ops.rigidbody.mass_calculate(material='Custom',density=den)
        # print('MASS',self.whichMesh.rigid_body.mass)
        return

    def __determineVolume(self):
        # Courtesy aothms via blenderartists.org forum: Thread volume m^3 in 2.5 (https://blenderartists.org/forum/showthread.php?207712-volume-m-3-in-2-5)

        triangles = []
        normals = []
        totalVolume = 0

        bpy.ops.object.mode_set(mode='EDIT')

        for face in self.whichMesh.data.polygons:
            t = [[self.whichMesh.data.vertices[vert].co for vert in face.vertices]]

            if len(t[0]) == 4:
                t = t[0]
                t = (t[0],t[1],t[2]),(t[0],t[2],t[3])

            normals.extend([face.normal] * len(t))
            triangles.extend(t)

        for triangle,normal in zip(triangles,normals):
            normalZ = normal[2]
            x1,y1,z1,x2,y2,z2,x3,y3,z3 = [dim for vert in triangle for dim in vert]
            pa = 0.5*abs((x1*(y3-y2))+(x2*(y1-y3))+(x3*(y2-y1)))
            volume = ((z1+z2+z3)/3.0)*pa

            if normalZ < 0: 
                normalZ = -1

            elif normalZ > 0: 
                normalZ = 1

            else: 
                normalZ = 0

            totalVolume += (normalZ * volume)

        bpy.ops.object.mode_set(mode='OBJECT')
        return totalVolume                                              # in cubic BU, therefore m^3

    def makeRigidBody(self,whichMesh,role):
        # make object an active or passive rigid body (role)

        self.whichMesh = whichMesh

        scn.objects.active = whichMesh
        bpy.ops.object.select_all(action='DESELECT')
        whichMesh.select = True

        bpy.ops.rigidbody.objects_add(type=role)
        
        if role == 'ACTIVE':
            whichMesh.rigid_body.collision_shape = 'CONVEX_HULL'

        elif role == 'PASSIVE':
            whichMesh.rigid_body.collision_shape = 'CONVEX_HULL'
            
        return

#   ***
# https://phys.org/news/2011-08-complexity-crumpled-paper-balls.html
# Cites Cambou, Anne Dominique and Menon, Narayanan. "Three-dimensional structure of a sheet crumpled into a ball." PNAS, 2011, vol 108, no. 36. pp. 14741-14745.
