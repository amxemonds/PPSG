
import bpy

import mysql.connector
import shutil
import os

import config
from config import *


###
###     RENDER
###

class stimulusRender:

    kind = 'Render Toolkit'

    def __init__(self,aldenObjectSpec,enviroSpec):

        self.alden = aldenObjectSpec
        self.env = enviroSpec

    def __renderSetup(self):

        # use cycles render engine
        scn.render.engine = 'CYCLES'

        # use GPU for rendering
        scn.cycles.device = 'GPU'
        bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'

        for d in bpy.context.user_preferences.addons['cycles'].preferences.devices:
            print(d.type)
            if d.type == 'CUDA':
                d.use = True
            else:
                d.use = False

        # light/raytrace settings
        scn.frame_set(0)
        scn.cycles.samples = 128
        scn.cycles.progressive = 'PATH'
        scn.cycles.max_bounces = 4
        scn.cycles.min_bounces = 3
        scn.cycles.diffuse_bounces = 4
        scn.cycles.glossy_bounces = 4
        scn.cycles.transmission_bounces = 12
        scn.cycles.volume_bounces = 1
        scn.cycles.transparent_max_bounces = 8
        scn.cycles.transparent_min_bounces = 8
        scn.cycles.use_progressive_refine = False
        scn.cycles.debug_use_spatial_splits = True
        scn.cycles.tile_order = 'CENTER'
        scn.render.use_save_buffers = True
        scn.render.use_persistent_data = True
        scn.cycles.blur_glossy = 0.5
        scn.cycles.sample_clamp_indirect = 2.0

        # colors, resolution
        scn.render.tile_x = 256
        scn.render.tile_y = 256
        #scn.ats_settings.use_advanced_ui = True
        scn.render.use_file_extension = True
        scn.render.image_settings.compression = 15
        scn.render.image_settings.color_mode = 'RGBA'
        scn.render.image_settings.file_format = 'PNG'
        scn.render.resolution_x = resolutionX #1400
        scn.render.resolution_y = resolutionY #1050
        scn.render.resolution_percentage = 100#30#100
        scn.frame_end = totalFrames
        return

    def renderStill(self):

        if not self.alden or not self.env:
            print('Class instance contains insufficient data to render. Render aborted.')
            return

        self.__renderSetup()
        scn.frame_current = 0
        scn.frame_set(0)
        scn.update()

        if 'GrassGravityStimulus' in self.env.context:
            deContext = self.env.context.split('_')[1]
            whichCombo = deContext.split('-')
            whichTilt = int(whichCombo[0])
            gravity = int(whichCombo[1])
            secondHorizon = int(whichCombo[2])
            hasBall = int(whichCombo[3])
            ballBuried = int(whichCombo[4])

            if secondHorizon:

                if '2' not in self.env.context:

                    if 'Grass_Gravity_Library_t-2_g-1_h-1_b-0_u-0' not in self.env.parentID:
                        scn.use_nodes = True
                        compositor = scn.node_tree

                        foreground = compositor.nodes[1]
                        compositeNode = compositor.nodes[0]

                        background = bpy.data.images.load(grassGravLibrary + 'Grass_Gravity_Library_t-2_g-1_h-1_b-0_u-0.png')
                        backgroundNode = compositor.nodes.new(type='CompositorNodeImage')
                        backgroundNode.image = background

                        alphaNode = compositor.nodes.new(type='CompositorNodeAlphaOver')
                        compositor.links.new(foreground.outputs[0],alphaNode.inputs[2])
                        compositor.links.new(backgroundNode.outputs[0],alphaNode.inputs[1])
                        compositor.links.new(alphaNode.outputs[0],compositeNode.inputs[0])
                        scn.view_settings.view_transform = 'Default'

                else:
                    scn.use_nodes = True
                    compositor = scn.node_tree

                    foreground = compositor.nodes[1]
                    compositeNode = compositor.nodes[0]

                    background = bpy.data.images.load(grassGravLibrary + 'GS2_' + str(self.env.horizonMaterial) + '.png')
                    backgroundNode = compositor.nodes.new(type='CompositorNodeImage')
                    backgroundNode.image = background

                    alphaNode = compositor.nodes.new(type='CompositorNodeAlphaOver')
                    compositor.links.new(foreground.outputs[0],alphaNode.inputs[2])
                    compositor.links.new(backgroundNode.outputs[0],alphaNode.inputs[1])
                    compositor.links.new(alphaNode.outputs[0],compositeNode.inputs[0])
                    scn.view_settings.view_transform = 'Default'

            elif len(whichCombo) > 6:
                hasBack = int(whichCombo[6])

                if not hasBack:
                    scn.use_nodes = True
                    compositor = scn.node_tree

                    foreground = compositor.nodes[1]
                    compositeNode = compositor.nodes[0]

                    background = bpy.data.images.load(grassGravLibrary + 'GS2_BLANK.png')
                    backgroundNode = compositor.nodes.new(type='CompositorNodeImage')
                    backgroundNode.image = background

                    alphaNode = compositor.nodes.new(type='CompositorNodeAlphaOver')
                    compositor.links.new(foreground.outputs[0],alphaNode.inputs[2])
                    compositor.links.new(backgroundNode.outputs[0],alphaNode.inputs[1])
                    compositor.links.new(alphaNode.outputs[0],compositeNode.inputs[0])
                    scn.view_settings.view_transform = 'Default'

        if stereoscopic:

            print('Rendering Stills...')

            if self.env.aperture == 1:
                bpy.data.objects['ApertureCameraR'].cycles_visibility.camera = False
                bpy.data.objects['ApertureCameraL'].cycles_visibility.camera = True
                bpy.data.objects['ApertureCameraM'].cycles_visibility.camera = False
                scn.update()

            if usesOccluder:
                bpy.data.objects['OccluderCameraR'].cycles_visibility.camera = False
                bpy.data.objects['OccluderCameraL'].cycles_visibility.camera = True
                bpy.data.objects['OccluderCameraM'].cycles_visibility.camera = False
                scn.update()

            pngName = stills + str(self.env.stimulusID) + '_L' + '.png'
            scn.render.filepath = pngName
            scn.camera = self.env.cameraL
            bpy.ops.render.render(write_still=True)

            if self.env.aperture == 1:
                bpy.data.objects['ApertureCameraR'].cycles_visibility.camera = True
                bpy.data.objects['ApertureCameraL'].cycles_visibility.camera = False
                bpy.data.objects['ApertureCameraM'].cycles_visibility.camera = False
                scn.update()

            if usesOccluder:
                bpy.data.objects['OccluderCameraR'].cycles_visibility.camera = True
                bpy.data.objects['OccluderCameraL'].cycles_visibility.camera = False
                bpy.data.objects['OccluderCameraM'].cycles_visibility.camera = False
                scn.update()

            pngName = stills + str(self.env.stimulusID) + '_R' + '.png'
            scn.render.filepath = pngName
            scn.camera = self.env.cameraR
            bpy.ops.render.render(write_still=True)

        else:

            print('Rendering Still...')

            if self.env.aperture == 1:
                bpy.data.objects['ApertureCameraR'].cycles_visibility.camera = False
                bpy.data.objects['ApertureCameraL'].cycles_visibility.camera = False
                bpy.data.objects['ApertureCameraM'].cycles_visibility.camera = True
                scn.update()

            if usesOccluder:
                bpy.data.objects['OccluderCameraR'].cycles_visibility.camera = False
                bpy.data.objects['OccluderCameraL'].cycles_visibility.camera = False
                bpy.data.objects['OccluderCameraM'].cycles_visibility.camera = True
                scn.update()

            pngName = stills + str(self.env.stimulusID) + '.png'
            scn.render.filepath = pngName
            scn.camera = self.env.cameraM
            bpy.ops.render.render(write_still=True)

        self.renderFinished()
        return

    def renderStillLeft(self):

        if not self.alden or not self.env:
            print('Class instance contains insufficient data to render. Render aborted.')
            return

        self.__renderSetup()
        scn.frame_current = 0
        scn.frame_set(0)
        scn.update()

        print('Rendering Left Still...')

        if self.env.aperture == 1:
            bpy.data.objects['ApertureCameraR'].cycles_visibility.camera = False
            bpy.data.objects['ApertureCameraL'].cycles_visibility.camera = True
            bpy.data.objects['ApertureCameraM'].cycles_visibility.camera = False
            scn.update()

        if usesOccluder:
            bpy.data.objects['OccluderCameraR'].cycles_visibility.camera = False
            bpy.data.objects['OccluderCameraL'].cycles_visibility.camera = True
            bpy.data.objects['OccluderCameraM'].cycles_visibility.camera = False
            scn.update()

        pngName = stills + str(self.env.stimulusID) + '_L' + '.png'
        scn.render.filepath = pngName
        scn.camera = self.env.cameraL
        bpy.ops.render.render(write_still=True)
        return

    def renderStillRight(self):

        if not self.alden or not self.env:
            print('Class instance contains insufficient data to render. Render aborted.')
            return

        self.__renderSetup()
        scn.frame_current = 0
        scn.frame_set(0)
        scn.update()

        print('Rendering Right Still...')

        if self.env.aperture == 1:
            bpy.data.objects['ApertureCameraR'].cycles_visibility.camera = True
            bpy.data.objects['ApertureCameraL'].cycles_visibility.camera = False
            bpy.data.objects['ApertureCameraM'].cycles_visibility.camera = False
            scn.update()

        if usesOccluder:
            bpy.data.objects['OccluderCameraR'].cycles_visibility.camera = True
            bpy.data.objects['OccluderCameraL'].cycles_visibility.camera = False
            bpy.data.objects['OccluderCameraM'].cycles_visibility.camera = False
            scn.update()

        pngName = stills + str(self.env.stimulusID) + '_R' + '.png'
        scn.render.filepath = pngName
        scn.camera = self.env.cameraR
        bpy.ops.render.render(write_still=True)
        return

    def renderAnimation(self,duplicate=True,frames=15,duplicateForStill=False): # was frames=5

        self.__renderSetup()
        scn.frame_current = 0
        scn.frame_set(0)
        scn.update()

        scn.frame_start = 1
        scn.frame_end = frames

        if 'GrassGravityStimulus' in self.env.context:
            deContext = self.env.context.split('_')[1]
            whichCombo = deContext.split('-')
            whichTilt = int(whichCombo[0])
            gravity = int(whichCombo[1])
            secondHorizon = int(whichCombo[2])
            hasBall = int(whichCombo[3])
            ballBuried = int(whichCombo[4])

            if secondHorizon:

                if '2' not in self.env.context:

                    if 'Grass_Gravity_Library_t-2_g-1_h-1_b-0_u-0' not in self.env.parentID:
                        scn.use_nodes = True
                        compositor = scn.node_tree

                        foreground = compositor.nodes[1]
                        compositeNode = compositor.nodes[0]

                        background = bpy.data.images.load(grassGravLibrary + 'Grass_Gravity_Library_t-2_g-1_h-1_b-0_u-0.png')
                        backgroundNode = compositor.nodes.new(type='CompositorNodeImage')
                        backgroundNode.image = background

                        alphaNode = compositor.nodes.new(type='CompositorNodeAlphaOver')
                        compositor.links.new(foreground.outputs[0],alphaNode.inputs[2])
                        compositor.links.new(backgroundNode.outputs[0],alphaNode.inputs[1])
                        compositor.links.new(alphaNode.outputs[0],compositeNode.inputs[0])
                        scn.view_settings.view_transform = 'Default'

                else:
                    scn.use_nodes = True
                    compositor = scn.node_tree

                    foreground = compositor.nodes[1]
                    compositeNode = compositor.nodes[0]

                    background = bpy.data.images.load(grassGravLibrary + 'GS2_' + str(self.env.horizonMaterial) + '.png')
                    backgroundNode = compositor.nodes.new(type='CompositorNodeImage')
                    backgroundNode.image = background

                    alphaNode = compositor.nodes.new(type='CompositorNodeAlphaOver')
                    compositor.links.new(foreground.outputs[0],alphaNode.inputs[2])
                    compositor.links.new(backgroundNode.outputs[0],alphaNode.inputs[1])
                    compositor.links.new(alphaNode.outputs[0],compositeNode.inputs[0])
                    scn.view_settings.view_transform = 'Default'
                    
            elif len(whichCombo) > 6:
                hasBack = int(whichCombo[6])

                if not hasBack:
                    scn.use_nodes = True
                    compositor = scn.node_tree

                    foreground = compositor.nodes[1]
                    compositeNode = compositor.nodes[0]

                    background = bpy.data.images.load(grassGravLibrary + 'GS2_BLANK.png')
                    backgroundNode = compositor.nodes.new(type='CompositorNodeImage')
                    backgroundNode.image = background

                    alphaNode = compositor.nodes.new(type='CompositorNodeAlphaOver')
                    compositor.links.new(foreground.outputs[0],alphaNode.inputs[2])
                    compositor.links.new(backgroundNode.outputs[0],alphaNode.inputs[1])
                    compositor.links.new(alphaNode.outputs[0],compositeNode.inputs[0])
                    scn.view_settings.view_transform = 'Default'

        # store all images in a folder
        os.makedirs(animations + str(self.env.stimulusID))

        if stereoscopic:

            print('Rendering Animations...')

            if self.env.aperture == 1:
                bpy.data.objects['ApertureCameraR'].cycles_visibility.camera = False
                bpy.data.objects['ApertureCameraL'].cycles_visibility.camera = True
                bpy.data.objects['ApertureCameraM'].cycles_visibility.camera = False
                scn.update()

            if usesOccluder:
                bpy.data.objects['OccluderCameraR'].cycles_visibility.camera = False
                bpy.data.objects['OccluderCameraL'].cycles_visibility.camera = True
                bpy.data.objects['OccluderCameraM'].cycles_visibility.camera = False
                scn.update()

            pngNameL = animations + str(self.env.stimulusID) + '/' + str(self.env.stimulusID) + '_L_'
            scn.render.filepath = pngNameL
            scn.camera = self.env.cameraL
            bpy.ops.render.render(animation=True)

            if self.env.aperture == 1:
                bpy.data.objects['ApertureCameraR'].cycles_visibility.camera = True
                bpy.data.objects['ApertureCameraL'].cycles_visibility.camera = False
                bpy.data.objects['ApertureCameraM'].cycles_visibility.camera = False
                scn.update()

            if usesOccluder:
                bpy.data.objects['OccluderCameraR'].cycles_visibility.camera = True
                bpy.data.objects['OccluderCameraL'].cycles_visibility.camera = False
                bpy.data.objects['OccluderCameraM'].cycles_visibility.camera = False
                scn.update()

            pngNameR = animations + str(self.env.stimulusID) + '/' + str(self.env.stimulusID) + '_R_'
            scn.render.filepath = pngNameR
            scn.camera = self.env.cameraR
            bpy.ops.render.render(animation=True)

            if duplicate:
                oldFileVal = [str(r).zfill(4) for r in range(1,frames+1)]
                newFileVal = [str(r).zfill(4) for r in range(frames*2,frames,-1)]
                # oldFileVal = ['0001','0002','0003','0004','0005']
                # newFileVal = ['0010','0009','0008','0007','0006']

                for fileVal in range(len(oldFileVal)):
                    shutil.copyfile(pngNameL+oldFileVal[fileVal]+'.png',pngNameL+newFileVal[fileVal]+'.png')
                    shutil.copyfile(pngNameR+oldFileVal[fileVal]+'.png',pngNameR+newFileVal[fileVal]+'.png')

            if duplicateForStill:

                previousId = self.env.stimulusID.split("_s-")
                genlin = previousId[0]
                previousId = int(previousId[1])-1
                previousId = genlin + '_s-' + str(previousId)

                shutil.copyfile(pngNameL+'0001.png',stills + previousId + '_L' + '.png')
                shutil.copyfile(pngNameR+'0001.png',stills + previousId + '_R' + '.png')

        else:

            print('Rendering Animation...')

            if self.env.aperture == 1:
                bpy.data.objects['ApertureCameraR'].cycles_visibility.camera = False
                bpy.data.objects['ApertureCameraL'].cycles_visibility.camera = False
                bpy.data.objects['ApertureCameraM'].cycles_visibility.camera = True
                scn.update()

            if usesOccluder:
                bpy.data.objects['OccluderCameraR'].cycles_visibility.camera = False
                bpy.data.objects['OccluderCameraL'].cycles_visibility.camera = False
                bpy.data.objects['OccluderCameraM'].cycles_visibility.camera = True
                scn.update()

            pngName = animations + str(self.env.stimulusID) + '/' + str(self.env.stimulusID) + '_'
            scn.render.filepath = pngName
            scn.camera = self.env.cameraM
            bpy.ops.render.render(animation=True)

            if duplicate:
                oldFileVal = [str(r).zfill(4) for r in range(1,frames+1)]
                newFileVal = [str(r).zfill(4) for r in range(frames*2,frames,-1)]
                # oldFileVal = ['0001','0002','0003','0004','0005']
                # newFileVal = ['0010','0009','0008','0007','0006']

                for fileVal in range(len(oldFileVal)):
                    shutil.copyfile(pngName+oldFileVal[fileVal]+'.png',pngName+newFileVal[fileVal]+'.png')

            if duplicateForStill:

                previousId = self.env.stimulusID.split("_s-")
                genlin = previousId[0]
                previousId = int(previousId[1])-1
                previousId = genlin + '_s-' + str(previousId)

                shutil.copyfile(pngName+'0001.png',stills + previousId + '.png')

        self.renderFinished()
        return

    def copyFromLibrary(self,libraryPath=grassGravLibrary):

        if stereoscopic:
            shutil.copyfile(libraryPath + str(self.env.parentID) + '_L.png',stills + str(self.env.stimulusID) + '_L.png')
            shutil.copyfile(libraryPath + str(self.env.parentID) + '_R.png',stills + str(self.env.stimulusID) + '_R.png')

        else:
            shutil.copyfile(libraryPath + str(self.env.parentID) + '.png',stills + str(self.env.stimulusID) + '.png')

        self.renderFinished()
        return

    def copyAnimationFromLibrary(self,frameExtent=41,libraryPath=ballLibrary,libraryPrefix='Roll_Animation_Library_'):

        frames = [str(r).zfill(4) for r in range(1,frameExtent)] #['000'+str(k) for k in range(1,10)] + ['00'+str(k) for k in range(10,41)]

        # store all images in a folder
        os.makedirs(animations + str(self.env.stimulusID))

        oldFile = libraryPath + str(self.env.parentID).split(libraryPrefix,1)[1] + '/' + str(self.env.parentID).split(libraryPrefix,1)[1]
        newFile = animations + str(self.env.stimulusID) + '/' + str(self.env.stimulusID)

        if stereoscopic:

            for frame in frames:
                shutil.copyfile(oldFile + '_L_' + frame + '.png', newFile + '_L_' + frame + '.png')
                shutil.copyfile(oldFile + '_R_' + frame + '.png', newFile + '_R_' + frame + '.png')

        else:

            for frame in frames:
                shutil.copyfile(oldFile + '_' + frame + '.png', newFile + '_' + frame + '.png')

        self.renderFinished()
        return

    def renderFinished(self):

        db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
        cursor = db.cursor()

        renderFinished = "UPDATE StimObjData SET renderFinished = '" +str(1)+ "' WHERE descId = '" + str(self.env.stimulusID) + "'"
        cursor.execute(renderFinished)

        preRunGen = self.env.stimulusID.split("_s-")[0]

        howManyInGen = "SELECT count(id) FROM StimObjData WHERE instr(descId,'" +preRunGen+ "')"
        cursor.execute(howManyInGen)
        numInGen = int(cursor.fetchone()[0]) - 1 # (one blank)

        howManyRendered = "SELECT count(id) FROM StimObjData WHERE instr(descId,'" +preRunGen+ "') AND renderFinished = 1"
        cursor.execute(howManyRendered)
        numRendered = int(cursor.fetchone()[0])

        print(numInGen,numRendered)

        if numRendered == numInGen:
            splitPreRunGenP = preRunGen.split("_r-")
            splitPreRunGenR = splitPreRunGenP[1].split("_g-")
            splitPreRunGenG = splitPreRunGenR[1].split("_l-")
            splitPreRunGenL = splitPreRunGenG[1].split("_s-")

            prefix = splitPreRunGenP[0]
            gaRun = splitPreRunGenR[0]
            genNum = splitPreRunGenG[0]
            linNum = splitPreRunGenL[0]

            print(prefix,gaRun,genNum,linNum)

            updateDescinfoRendersFinished = "UPDATE DescriptiveInfo SET rendersFinished = '" +str(1)+ "' WHERE prefix = '" + prefix + "' AND gaRun = '" + gaRun + "' AND genNum = '" + genNum + "' AND linNum = '" + linNum + "'"
            cursor.execute(updateDescinfoRendersFinished)

        db.commit()
        db.close()
        return

###
###     ALDEN STIMULUS APPEARANCE AND MATERIAL PARTITION
###

class finalizeMaterials:

    def __init__(self,aldenObjectSpec):

        self.alden = aldenObjectSpec

    def applyAllMaterials(self):

        # use cycles render engine
        # scn.render.engine = 'CYCLES'
        # bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
        # bpy.context.user_preferences.addons['cycles'].preferences.devices[0].use = True
        # bpy.context.user_preferences.addons['cycles'].preferences.devices[1].use = True
        # bpy.context.user_preferences.addons['cycles'].preferences.devices[2].use = True

        scn.render.engine = 'CYCLES'

        # # use GPU
        # scn.cycles.device = 'GPU'

        # bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
        # devs = bpy.context.user_preferences.addons['cycles'].preferences.devices
        # for d in devs :
        #     if d.type == 'CUDA':
        #         d.use = True
        #     else:
        #         d.use = False

        scn.frame_end = totalFrames
        # scn.view_settings.view_transform = 'Filmic'

        if not self.alden.optical:
            self.__applyMaterials()

        else:
            self.__applyOptics() 

        return

    def __applyOptics(self):

        alden = self.alden

        alden.deleteToolkit.deleteSingleObjectMaterials(alden.mesh)
        alden.mat = alden.materialToolkit.useNodes(alden.mesh)

        if not alden.densityUniform:
            self.__materialGradient()

        else:
            penultimate, penultimateVolume, penultimateDisplacement = alden.materialToolkit.makeOptics(alden)

        return

    def __applyMaterials(self):

        alden = self.alden

        alden.deleteToolkit.deleteSingleObjectMaterials(alden.mesh)
        alden.mat = alden.materialToolkit.useNodes(alden.mesh)

        if not alden.densityUniform:
            self.__materialGradient()

        else:
            penultimate,penultimateVolume,penultimateDisplacement = alden.materialToolkit.makeNodes(alden.mat,alden.material,True)
            body = penultimate

            wholeWeightSurfaceArea = sum([poly.area for poly in alden.mesh.data.polygons])

            if body.name in ['hedgehog_skin','fur_skin','cactus_skin']:

                if body.name == 'hedgehog_skin':
                    particleGroup = bpy.data.particles['hedgehog01']

                elif body.name == 'fur_skin':
                    particleGroup = bpy.data.particles['fur01']

                elif body.name == 'cactus_skin':
                    particleGroup = bpy.data.particles['cactus01']
                
                particleGroup.count = wholeWeightSurfaceArea * particleGroup.count

        return

    def __materialGradient(self):
        # assign material gradient materials

        alden = self.alden

        scn.objects.active = alden.mesh
        bpy.ops.object.select_all(action='DESELECT')
        alden.mesh.select = True

        output = alden.mat.node_tree.nodes[0]
        limbGradients = [g for g in alden.mesh.data.vertex_colors if g.name.startswith('WeightColor')]

        for ind in range(len(limbGradients)):
            limbGradients = [g for g in alden.mesh.data.vertex_colors if g.name.startswith('WeightColor')]
            limbParticles = [p for p in alden.mesh.vertex_groups if p.name.startswith('WeightParticle')]

            weightPaint = limbGradients[ind]
            particlePaint = limbParticles[ind]
            limbMaterial = alden.limbMaterials[ind]
            surfaceArea = alden.surfaceAreas[ind]

            transAttribute = alden.mat.node_tree.nodes.new('ShaderNodeAttribute')
            transAttribute.attribute_name = weightPaint.name
            mix = alden.mat.node_tree.nodes.new('ShaderNodeMixShader')
            mix.inputs[0].default_value = 1.0

            penultimate, penultimateVolume, penultimateDisplacement = alden.materialToolkit.makeNodes(alden.mat,limbMaterial,False)
            transMaterial = penultimate

            if transMaterial.type == 'GROUP':

                if penultimateVolume:
                    mixShaderValue = self.__makeVolumeMix(alden.mat,transMaterial,transAttribute)

                if penultimateDisplacement:
                    mixColorValue = self.__makeDisplacementMix(alden.mat,transMaterial,transAttribute)

            if transMaterial.name in ['hedgehog_skin','fur_skin','cactus_skin']:

                if transMaterial.name == 'hedgehog_skin':
                    particleSystem = alden.mesh.particle_systems['hedgehog01']
                    particleGroup = bpy.data.particles['hedgehog01']

                elif transMaterial.name == 'fur_skin':
                    particleSystem = alden.mesh.particle_systems['fur01']
                    particleGroup = bpy.data.particles['fur01']

                elif transMaterial.name == 'cactus_skin':
                    particleSystem = alden.mesh.particle_systems['cactus01']
                    particleGroup = bpy.data.particles['cactus01']
                
                particleSystem.vertex_group_density = particlePaint.name
                particleSystem.vertex_group_length = particlePaint.name
                particleGroup.count = surfaceArea * particleGroup.count

            if transMaterial.name == 'corrugatedOG':
                corrugation = alden.mesh.modifiers['corrugation']
                corrugation.vertex_group = particlePaint.name

            if transMaterial.name == 'aluminum_foil01':
                corrugation = alden.mesh.modifiers['aluminum_foil']
                corrugation.vertex_group = particlePaint.name

            if transMaterial.name == 'paperOG':
                corrugation = alden.mesh.modifiers['paper']
                corrugation.vertex_group = particlePaint.name

            alden.mat.node_tree.links.new(transAttribute.outputs[2],mix.inputs[0])
            alden.mat.node_tree.links.new(transMaterial.outputs[0],mix.inputs[2])

        allNodes = alden.mat.node_tree.nodes
        mixShaders = [m for m in allNodes if m.name.startswith('Mix Shader')]
        mixShaderValues = [m for m in allNodes if m.name.startswith('Shader Value Mix')]
        mixColorValues = [m for m in allNodes if m.name.startswith('Color Value Mix')]

        for addNum in range(len(mixShaders)):
            add = alden.mat.node_tree.nodes.new('ShaderNodeAddShader')

        for addNum in range(len(mixShaderValues)):
            addShaderValue = alden.mat.node_tree.nodes.new('ShaderNodeAddShader')
            addShaderValue.name = 'Shader Value Add'

        for addNum in range(len(mixColorValues)):
            addColorValue = alden.mat.node_tree.nodes.new('ShaderNodeMixRGB')
            addColorValue.blend_type = 'ADD' # DARKEN
            addColorValue.name = 'Color Value Add'
            addColorValue.inputs[0].default_value = 1.0

        allNodes = alden.mat.node_tree.nodes
        addShaders = [a for a in allNodes if a.name.startswith('Add Shader')]
        addShaderValues = [a for a in allNodes if a.name.startswith('Shader Value Add')]
        addColorValues = [a for a in allNodes if a.name.startswith('Color Value Add')]

        if alden.optical:
            penultimate, penultimateVolume, penultimateDisplacement = alden.materialToolkit.makeOptics(alden)

        else:
            penultimate, penultimateVolume, penultimateDisplacement = alden.materialToolkit.makeNodes(alden.mat,alden.material,False)

        body = penultimate

        baseAttribute = alden.mat.node_tree.nodes.new('ShaderNodeAttribute')
        baseAttribute.attribute_name = 'WholeWeightColor'

        if addShaders:
            outSurface = self.__addNmix(alden.mat,addShaders,mixShaders,'shaders')

        else:
            outSurface = penultimate

        if penultimateVolume:
            mixShaderValue = self.__makeVolumeMix(alden.mat,body,baseAttribute)

            addShaderValue = alden.mat.node_tree.nodes.new('ShaderNodeAddShader')
            addShaderValue.name = 'Shader Value Add'

            mixShaderValues.append(mixShaderValue)
            addShaderValues.append(addShaderValue)

            outVolume = self.__addNmix(alden.mat,addShaderValues,mixShaderValues,'shaders')
            alden.mat.node_tree.links.new(outVolume.outputs[0],output.inputs[1])

        if penultimateDisplacement:
            mixColorValue = self.__makeDisplacementMix(alden.mat,body,baseAttribute)

            addColorValue = alden.mat.node_tree.nodes.new('ShaderNodeMixRGB')
            addColorValue.blend_type = 'ADD' # DARKEN
            addColorValue.name = 'Color Value Add'
            addColorValue.inputs[0].default_value = 1.0

            mixColorValues.append(mixColorValue)
            addColorValues.append(addColorValue)

            outDisplacement = self.__addNmix(alden.mat,addColorValues,mixColorValues,'colors')
            alden.mat.node_tree.links.new(outDisplacement.outputs[0],output.inputs[2])

        mixBase = alden.mat.node_tree.nodes.new('ShaderNodeMixShader')
        addFinal = alden.mat.node_tree.nodes.new('ShaderNodeAddShader')
        alden.mat.node_tree.links.new(baseAttribute.outputs[2],mixBase.inputs[0])
        alden.mat.node_tree.links.new(body.outputs[0],mixBase.inputs[2])
        alden.mat.node_tree.links.new(mixBase.outputs[0],addFinal.inputs[1])
        alden.mat.node_tree.links.new(outSurface.outputs[0],addFinal.inputs[0])
        alden.mat.node_tree.links.new(addFinal.outputs[0],output.inputs[0])

        if body.name in ['hedgehog_skin','fur_skin','cactus_skin']:

                if body.name == 'hedgehog_skin':
                    particleSystem = alden.mesh.particle_systems['hedgehog01']
                    particleGroup = bpy.data.particles['hedgehog01']

                elif body.name == 'fur_skin':
                    particleSystem = alden.mesh.particle_systems['fur01']
                    particleGroup = bpy.data.particles['fur01']

                elif body.name == 'cactus_skin':
                    particleSystem = alden.mesh.particle_systems['cactus01']
                    particleGroup = bpy.data.particles['cactus01']
                
                particleSystem.vertex_group_density = 'WholeWeightParticle'
                particleSystem.vertex_group_length = 'WholeWeightParticle'
                particleGroup.count = alden.wholeWeightSurfaceArea * particleGroup.count

        if body.name == 'corrugatedOG':
                corrugation = alden.mesh.modifiers['corrugation']
                corrugation.vertex_group = 'WholeWeightParticle'

        if body.name == 'aluminum_foil01':
                corrugation = alden.mesh.modifiers['aluminum_foil']
                corrugation.vertex_group = 'WholeWeightParticle'

        if body.name == 'paperOG':
                corrugation = alden.mesh.modifiers['paper']
                corrugation.vertex_group = 'WholeWeightParticle'

        return

    def __addNmix(self,mat,addList,mixList,nodeType='shaders'):

        for ind in range(len(addList)):
            currentAdd = addList[ind]
            currentMix = mixList[ind]

            if nodeType == 'shaders':
                mat.node_tree.links.new(currentMix.outputs[0],currentAdd.inputs[0])

            else:
                mat.node_tree.links.new(currentMix.outputs[0],currentAdd.inputs[1])

            if ind != len(addList)-1:
                nextAdd = addList[ind+1]

                if nodeType == 'shaders':
                    mat.node_tree.links.new(currentAdd.outputs[0],nextAdd.inputs[1])

                else:
                    mat.node_tree.links.new(currentAdd.outputs[0],nextAdd.inputs[2])

        lastAdd = currentAdd
        return lastAdd

    def __makeVolumeMix(self,mat,groupOutput,attribute):

        mixShaderValue = mat.node_tree.nodes.new('ShaderNodeMixShader')
        mixShaderValue.name = 'Shader Value Mix'
        mat.node_tree.links.new(groupOutput.outputs['Volume'],mixShaderValue.inputs[2])
        mat.node_tree.links.new(attribute.outputs[2],mixShaderValue.inputs[0])
        return mixShaderValue

    def __makeDisplacementMix(self,mat,groupOutput,attribute):

        invert = mat.node_tree.nodes.new('ShaderNodeInvert')
        invert.inputs[0].default_value = 1.0
        mixColorValue = mat.node_tree.nodes.new('ShaderNodeMixRGB')
        mixColorValue.blend_type = 'MIX' # ADD
        mixColorValue.name = 'Color Value Mix'
        mat.node_tree.links.new(groupOutput.outputs['Displacement'],mixColorValue.inputs[1])
        mat.node_tree.links.new(attribute.outputs[2],invert.inputs[1])
        mat.node_tree.links.new(invert.outputs[0],mixColorValue.inputs[0])
        return mixColorValue

