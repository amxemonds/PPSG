
import bpy
import xml.etree.cElementTree as ET
from xml.dom import minidom

from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
import mathutils
from mathutils import Vector
from mathutils import Euler
import numpy as NP

import sys

sys.path.append("/usr/local/lib/python3.6/site-packages")

import mysql.connector

import config
from config import *

from environmentPrimitives import environmentSpec, environmentConstructor, enclosureConstructor, animation
from aldenMesh import aldenObjectSpec, aldenConstructor, aldenSkeleton
from physics import physicsTool
from delete import deleteTool
from stimulusRender import stimulusRender, finalizeMaterials


class informationTransfer:

    kind = 'Information Transfer Toolkit'

    def __init__(self):

        self.alden = None
        self.env = None
        self.deleteToolkit = deleteTool()

        self.enviroConstr = environmentConstructor(None)
        self.enclosConstr = enclosureConstructor(None)
        self.aldenConstr = aldenConstructor()

    ###
    ###     EXPORTS
    ###

    def saveDae(self):

        if not self.alden:
            print('Alden object identifier undefined. Save aborted.')
            return

        daeName = stills + str(self.alden.id) + '.dae'
        bpy.ops.wm.collada_export(filepath=daeName)
        return

    def exportXML(self,descId):

        alden = self.alden
        env = self.env

        if not alden or not env:
            print('XML spec incomplete. Export aborted.')
            return

        blenderRoot = ET.Element('BlenderSpec')

        ###
        ###     CONFIGURATION CONSTANTS (for distant future reference)
        ###
        env.stimulusID = descId
        ET.SubElement(blenderRoot, 'stimulusID').text = str(env.stimulusID)
        ET.SubElement(blenderRoot, 'parentID').text = str(env.parentID)

        morph = ET.SubElement(blenderRoot, 'morph')
        morphNumber = 0

        for whichMorph in env.morph:
            ET.SubElement(morph, 'morph'+str(morphNumber)).text = str(whichMorph)
            morphNumber += 1

        ET.SubElement(blenderRoot, 'monkeyID').text = str(monkey)
        ET.SubElement(blenderRoot, 'monkeyPerspectiveAngle').text = str(monkeyPerspectiveAngle)
        ET.SubElement(blenderRoot, 'monkeyDistanceY').text = str(monkeyDistanceY)
        ET.SubElement(blenderRoot, 'monkeyDistanceZ').text = str(monkeyDistanceZ)
        ET.SubElement(blenderRoot, 'eyeSeparation').text = str(monkeyEyeDistance)

        ET.SubElement(blenderRoot, 'cameraLens_mm').text = str(lens)
        ET.SubElement(blenderRoot, 'cameraSensorWidth_mm').text = str(sensorWidth)
        ET.SubElement(blenderRoot, 'architectureScale').text = str(architectureScale)
        ET.SubElement(blenderRoot, 'overallScale').text = str(1)

        ###
        ###     ALDEN MEDIAL AXIS STIMULUS
        ###

        aldenSub = ET.SubElement(blenderRoot,'AldenSpec')

        # *alden.mesh -> aldenPresent
        # *aldenPresent = int/bool
        ET.SubElement(aldenSub, 'aldenPresent').text = str(alden.present)

        # *alden.id
        # *moniker = string
        ET.SubElement(aldenSub, 'id').text = str(alden.id)

        # *alden.blocky
        # *blocky = int/bool
        ET.SubElement(aldenSub, 'blocky').text = str(alden.blocky)

        # *alden.mirrored
        # *mirrored = [0,0,0]
        symmetry = ET.SubElement(aldenSub, 'bilateralSymmetry')
        ET.SubElement(symmetry, 'x').text = str(alden.mirrored[0])
        ET.SubElement(symmetry, 'y').text = str(alden.mirrored[1])
        ET.SubElement(symmetry, 'z').text = str(alden.mirrored[2])
        

        # *alden.fixationPoint
        # *fixationPoint = int/bool
        ET.SubElement(aldenSub, 'fixationPoint').text = str(alden.fixationPoint)

        # *alden.whichWiggle
        # *alden.whichWiggle = string
        ET.SubElement(aldenSub, 'whichWiggle').text = str(alden.whichWiggle)


        # *alden.location
        # *alden.location = int
        ET.SubElement(aldenSub, 'location').text = str(alden.location)

        # *alden.wallInteraction
        # *alden.wallInteraction = int
        ET.SubElement(aldenSub, 'wallInteraction').text = str(alden.wallInteraction)

        # *alden.implantation
        # *alden.implantation = float
        ET.SubElement(aldenSub, 'implantation').text = str(alden.implantation)

        # *alden.scaleShiftInDepth
        # *alden.scaleShiftInDepth = int
        ET.SubElement(aldenSub, 'scaleShiftInDepth').text = str(alden.scaleShiftInDepth)
        ET.SubElement(aldenSub, 'consistentRetinalSize').text = str(alden.consistentRetinalSize)

        # *alden.material
        # *alden.material = string
        ET.SubElement(aldenSub, 'material').text = str(alden.material)

        # *alden.densityUniform
        # *densitySeparation = int/bool
        ET.SubElement(aldenSub, 'densityUniform').text = str(alden.densityUniform)

        howManyAffectedLimbs = len(alden.affectedLimbs)
        ET.SubElement(aldenSub, 'howMany').text = str(howManyAffectedLimbs)

        # *alden.affectedLimbs
        # *alden.affectedLimbs = [int,int,int,...]
        affectedLimbs = ET.SubElement(aldenSub,'affectedLimbs')

        for ind in range(howManyAffectedLimbs):
            ET.SubElement(affectedLimbs, 'int').text = str(alden.affectedLimbs[ind])

        # *alden.limbMaterials
        # *alden.limbMaterials = ['string','string','string',...]
        limbMaterials = ET.SubElement(aldenSub,'limbMaterials') 

        for ind in range(howManyAffectedLimbs):
            ET.SubElement(limbMaterials, 'limbMaterial').text = str(alden.limbMaterials[ind])

        # *alden.massManipulationLimb
        # *alden.massManipulationLimb = string
        ET.SubElement(aldenSub, 'massManipulationLimb').text = str(alden.massManipulationLimb)

        # *alden.optical
        # *alden.optical = int/bool
        ET.SubElement(aldenSub, 'optical').text = str(alden.optical)

        # *alden.opticalBeerLambertColor
        # *alden.opticalBeerLambertColor = [0,0,0]
        opticalColor = ET.SubElement(aldenSub,'opticalBeerLambertColor')
        ET.SubElement(opticalColor, 'red').text = str(alden.opticalBeerLambertColor[0])
        ET.SubElement(opticalColor, 'green').text = str(alden.opticalBeerLambertColor[1])
        ET.SubElement(opticalColor, 'blue').text = str(alden.opticalBeerLambertColor[2])
        
        # *alden.opticalIOR
        # *alden.opticalIOR = float
        ET.SubElement(aldenSub, 'opticalIOR').text = str(alden.opticalIOR)

        # *alden.opticalTranslucency
        # *alden.opticalTranslucency = float
        ET.SubElement(aldenSub, 'opticalTranslucency').text = str(alden.opticalTranslucency)

        # *alden.opticalAttenuation
        # *alden.opticalAttenuation = float
        ET.SubElement(aldenSub, 'opticalAttenuation').text = str(alden.opticalAttenuation)

        # *alden.opticalTransparency
        # *alden.opticalTransparency = float
        ET.SubElement(aldenSub, 'opticalTransparency').text = str(alden.opticalTransparency)

        # *alden.opticalRoughness
        # *alden.opticalRoughness = float
        ET.SubElement(aldenSub, 'opticalRoughness').text = str(alden.opticalRoughness)

        # *alden.opticalReflectivity
        # *alden.opticalReflectivity = float
        ET.SubElement(aldenSub, 'opticalReflectivity').text = str(alden.opticalReflectivity)


        # *alden.lowPotentialEnergy
        # *alden.lowPotentialEnergy = int/bool
        ET.SubElement(aldenSub, 'lowPotentialEnergy').text = str(alden.lowPotentialEnergy)

        # *alden.makePrecarious
        # *alden.makePrecarious = [0,0,0]
        precarious = ET.SubElement(aldenSub,'makePrecarious') 
        ET.SubElement(precarious, 'x').text = str(alden.makePrecarious[0])
        ET.SubElement(precarious, 'y').text = str(alden.makePrecarious[1])
        ET.SubElement(precarious, 'z').text = str(alden.makePrecarious[2])

        # *alden.makePrecarious[3]
        # *alden.makePrecarious[3] = int/bool
        ET.SubElement(aldenSub, 'makePrecariousFinal').text = str(alden.makePrecarious[3])

        # *alden.rotation
        # *alden.rotation = [0,0,0]
        rotation = ET.SubElement(aldenSub,'rotation') 
        ET.SubElement(rotation, 'x').text = str(alden.rotation[0])
        ET.SubElement(rotation, 'y').text = str(alden.rotation[1])
        ET.SubElement(rotation, 'z').text = str(alden.rotation[2])
        
        if env.horizon:

            if alden.present:
                junctionFocusLoc = self.enviroConstr.findClosestJunction(alden)

                # unparent alden object and apply transform
                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = alden.mesh
                alden.mesh.select = True
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                scn.update()
                bpy.ops.object.transform_apply(rotation=True)

                # unparent horizon and apply transform
                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = env.horizon
                env.horizon.select = True
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                scn.update()
                bpy.ops.object.transform_apply(rotation=True)

                # angle of bounding box for long axis in XZ plane
                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = alden.mesh
                alden.mesh.select = True
                bpy.ops.object.transform_apply(scale=True)

                com = alden.physicsToolkit.centerOfMassByVolume(alden)

                xMin,xMax,yMin,yMax,zMin,zMax,leeway = alden.physicsToolkit.findBoundingBox(alden.mesh)
                alden.boundingBoxLongAxis = math.atan((xMax-xMin)/(zMax-zMin))
                #...can be multiple points of contact, though...
                
                # look for all points on mesh below the surface of the ground/touching the surface of the ground
                scn.update()
                vertsLocal = alden.mesh.data.vertices
                vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]

                # find the place on the ground (z) corresponding to the crossing
                underGround = [Vector((v[0],v[1],0)) for v in vertsGlobal if v[2] <= 0.0+bumpStrength] # !!! DOESN'T WORK IF HORIZON ISN'T FLAT

                # vector from places on ground to com
                allContactVectors = [com-u for u in underGround]
                numContactVectors = max([1,len(allContactVectors)])

                # sum vectors to produce comVector
                alden.comVector = Vector((sum([cv[0] for cv in allContactVectors])/numContactVectors,sum([cv[1] for cv in allContactVectors])/numContactVectors,sum([cv[2] for cv in allContactVectors])/numContactVectors))
                print(alden.comVector)

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = alden.mesh
                alden.mesh.select = True
                bpy.ops.object.transform_apply(rotation=True,scale=True)
                whichMaterial = ''

                if not alden.optical:
                    whichMaterial = alden.material

                try:
                    alden.massToolkit.assignMass(alden.mesh,'')
                    alden.mass = alden.mesh.rigid_body.mass
                    
                except:
                    pass

            else:
                alden.boundingBoxLongAxis = 0
                alden.comVector = Vector(([0,0,0]))
                alden.mass = 0

            # horizonNormal, too...
            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = env.horizon
            env.horizon.select = True
            bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
            env.horizon = bpy.data.objects['Horizon']
            alden.horizonNormal = env.horizon.data.vertices[0].normal
            print(alden.horizonNormal)

        else:

            if not len(alden.comVector):
                alden.boundingBoxLongAxis = 0
                alden.comVector = Vector(([0,0,0]))
                alden.mass = 0
                alden.horizonNormal = Vector(([0,0,0]))

        # *boundingBoxLongAxis
        # *boundingBoxLongAxis = float
        ET.SubElement(aldenSub, 'boundingBoxLongAxis').text = str(alden.boundingBoxLongAxis)

        # *comVector
        # *comVector = [0,0,0]
        centerOfMass = ET.SubElement(aldenSub,'comVector') 
        ET.SubElement(centerOfMass, 'x').text = str(alden.comVector[0])
        ET.SubElement(centerOfMass, 'y').text = str(alden.comVector[1])
        ET.SubElement(centerOfMass, 'z').text = str(alden.comVector[2])

        # *mass
        # *mass = float
        ET.SubElement(aldenSub, 'mass').text = str(alden.mass)

        # *horizonNormal
        # *horizonNormal = [0,0,0]
        horizNormal = ET.SubElement(aldenSub,'horizonNormal') 
        ET.SubElement(horizNormal, 'x').text = str(alden.horizonNormal[0])
        ET.SubElement(horizNormal, 'y').text = str(alden.horizonNormal[1])
        ET.SubElement(horizNormal, 'z').text = str(alden.horizonNormal[2])

        ###
        ###     ENVIRONMENT AND STRUCTURE
        ###

        envSub = ET.SubElement(blenderRoot,'EnvironmentSpec')


        # *env.horizonTilt
        # *env.horizonTilt = float
        ET.SubElement(envSub, 'horizonTilt').text = str(env.horizonTilt)

        # *env.horizonSlant
        # *env.horizonSlant = float
        ET.SubElement(envSub, 'horizonSlant').text = str(env.horizonSlant)

        # *env.horizonMaterial
        # *env.horizonMaterial = string
        ET.SubElement(envSub, 'horizonMaterial').text = str(env.horizonMaterial)

        # *env.gravity
        # *env.gravity = int/bool
        ET.SubElement(envSub, 'gravity').text = str(env.gravity)

        # *env.monkeyTilt
        # *env.monkeyTilt = float
        ET.SubElement(envSub, 'monkeyTilt').text = str(env.monkeyTilt)

        # *env.context
        # *env.context = int
        ET.SubElement(envSub, 'context').text = str(env.context)

        # *env.compositeKeepAlden
        # *env.compositeKeepAlden = int/bool
        ET.SubElement(envSub, 'compositeKeepAlden').text = str(env.compositeKeepAlden)

        if env.architecture:
            envArchitecture = 1
        else:
            envArchitecture = 0

        # *env.architecture -> envArchitecture
        # *envArchitecture = int/bool
        ET.SubElement(envSub, 'architecture').text = str(envArchitecture)

        # *env.floor
        # *env.floor = int/bool
        ET.SubElement(envSub, 'floor').text = str(env.floor)

        # *env.ceiling 
        # *env.ceiling = int/bool
        ET.SubElement(envSub, 'ceiling').text = str(env.ceiling)

        # *env.wallL
        # *env.wallL = int/bool
        ET.SubElement(envSub, 'wallL').text = str(env.wallL)

        # *env.wallR 
        # *env.wallR = int/bool
        ET.SubElement(envSub, 'wallR').text = str(env.wallR)

        # *env.wallB
        # *env.wallB = int/bool
        ET.SubElement(envSub, 'wallB').text = str(env.wallB)

        # *env.architectureThickness
        # *env.architectureThickness = float
        ET.SubElement(envSub, 'architectureThickness').text = str(env.architectureThickness)

        # *env.distance
        # *env.distance = float
        ET.SubElement(envSub, 'distance').text = str(env.distance)

        # *env.structureMaterial
        # *env.structureMaterial = string
        ET.SubElement(envSub, 'structureMaterial').text = str(env.structureMaterial)

        # *env.aperture
        # *env.aperture = int/bool
        
        if ('3_' in env.context) or ('5_' in env.context) or ('6_' in env.context) or ('8_' in env.context) or ('9_' in env.context) or ('10_' in env.context) or ('11_' in env.context):
            ET.SubElement(envSub, 'aperture').text = str(0) #str(1)

        else:
            ET.SubElement(envSub, 'aperture').text = str(env.aperture)

        if env.cameraM:
            # *env.cameraM.location
            # *env.cameraM.location = [0,0,0]
            cameraLocation = ET.SubElement(envSub,'cameraLocation') 
            ET.SubElement(cameraLocation, 'x').text = str(env.cameraM.location[0])
            ET.SubElement(cameraLocation, 'y').text = str(env.cameraM.location[1])
            ET.SubElement(cameraLocation, 'z').text = str(env.cameraM.location[2])

        # *env.sun
        # *env.sun = [0,0,0]
        sun = ET.SubElement(aldenSub,'sun') 
        ET.SubElement(sun, 'x').text = str(env.sun[0])
        ET.SubElement(sun, 'y').text = str(env.sun[1])
        ET.SubElement(sun, 'z').text = str(env.sun[2])

        # *env.fixationPointDepth
        # *env.fixationPointDepth = float
        ET.SubElement(envSub, 'fixationPointDepth').text = str(env.fixationPointDepth)

        ###
        ###     WRITE PRETTYPRINT
        ###

        xmlstr = minidom.parseString(ET.tostring(blenderRoot)).toprettyxml(indent="   ")
        xmlstr = xmlstr[xmlstr.find("?>")+3:]
        # fileObject = open(specSource + str(stimulusIdent) + '_bspec.xml','w')
        # fileObject.write(xmlstr)
        # fileObject.close()

        db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
        cursor = db.cursor()

        transferBspec = "UPDATE StimObjData SET blenderspec = '" + xmlstr + "' WHERE descId = '" + str(env.stimulusID) + "'"
        cursor.execute(transferBspec)
        db.commit()
        db.close()
        return
        
    ###
    ###     TRANSFERS
    ###

    def transferMStickSpec(self,fromDescId,fromDatabase,toDescId,toDatabase):

        db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=fromDatabase,charset='utf8',use_unicode=True)
        cursor = db.cursor()

        queryAlden = "SELECT mstickspec FROM StimObjData WHERE descId = '" + fromDescId + "'"

        try:
            cursor.execute(queryAlden)
            blendSpec = cursor.fetchone()
            blendSpec = blendSpec[0]

            if len(blendSpec):
                self.env.context += '_Object'
                fixJavaSpec = 'LIBRARY_OBJECT'

            else:
                blendSpec = None
                self.env.context += '_Environment'
                fixJavaSpec = 'LIBRARY_ENVT'

            db.commit()
            db.close()

        except:
            print("Error: unable to fetch MStickSpec data. Perhaps not stimType OBJECT.")
            blendSpec = None
            self.env.context += '_Environment'
            fixJavaSpec = 'LIBRARY_ENVT'
            db.commit()
            db.close()

        db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=toDatabase,charset='utf8',use_unicode=True)
        cursor = db.cursor()

        if blendSpec:
            transferMSspec = "UPDATE StimObjData SET mstickspec = '" + blendSpec + "' WHERE descId = '" + toDescId + "'"
            cursor.execute(transferMSspec)

        queryJavaSpec = "SELECT javaspec FROM StimObjData WHERE descId = '" + toDescId + "'"

        try:
            cursor.execute(queryJavaSpec)
            javaSpec = cursor.fetchone()
            javaSpec = javaSpec[0]

            javaRoot = ET.ElementTree(ET.fromstring(javaSpec))
            presentStimType = str(javaRoot.findtext('stimType'))

            if presentStimType == 'PH_LIBRARY':
                fixJavaSpec = 'PH_LIBRARY_OBJECT'

            elif presentStimType == 'TALL_LIBRARY':
                fixJavaSpec = 'TALL_LIBRARY_OBJECT'

            if 'LIBRARY' in presentStimType:
                newJavaRoot = ET.Element('PngObjectSpec')
                ET.SubElement(newJavaRoot,'id').text = str(javaRoot.findtext('id'))
                ET.SubElement(newJavaRoot,'descId').text = str(javaRoot.findtext('descId'))
                ET.SubElement(newJavaRoot,'stimType').text = fixJavaSpec
                ET.SubElement(newJavaRoot,'gaPrefix').text = str(javaRoot.findtext('gaPrefix'))
                ET.SubElement(newJavaRoot,'gaRunNum').text = str(javaRoot.findtext('gaRunNum'))
                ET.SubElement(newJavaRoot,'doStickGen').text = str(javaRoot.findtext('doStickGen'))
                ET.SubElement(newJavaRoot,'doStickMorph').text = str(javaRoot.findtext('doStickMorph'))
                ET.SubElement(newJavaRoot,'doBlenderMorph').text = str(javaRoot.findtext('doBlenderMorph'))
                ET.SubElement(newJavaRoot,'doControlledStickMorph').text = str(javaRoot.findtext('doControlledStickMorph'))

                xmlstr = minidom.parseString(ET.tostring(newJavaRoot)).toprettyxml(indent="   ")
                xmlstr = xmlstr[xmlstr.find("?>")+3:]

                updateJavaSpec = "UPDATE StimObjData SET javaspec = '" + xmlstr + "' WHERE descId = '" + toDescId + "'"
                cursor.execute(updateJavaSpec)

        except:
            print("Error in retrieving javaspec for descId " + toDescId)
            pass

        db.commit()
        db.close()
        return

    def transferVertFaceSpecs(self,fromDescId,fromDatabase,toDescId,toDatabase):

        db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=fromDatabase,charset='utf8',use_unicode=True)
        cursor = db.cursor()

        queryVert = "SELECT vertspec FROM StimObjDataVert WHERE descId = '" + fromDescId + "'"
        queryFace = "SELECT faceSpec FROM StimObjDataVert WHERE descId = '" + fromDescId + "'"

        try:
            cursor.execute(queryVert)
            vertSpec = cursor.fetchone()
            vertSpec = vertSpec[0].decode("utf-8")

            cursor.execute(queryFace)
            faceSpec = cursor.fetchone()
            faceSpec = faceSpec[0].decode("utf-8")

            db.commit()
            db.close()

        except:
            print("Error: unable to fetch vert and face specs. Perhaps not stimType OBJECT.")
            db.commit()
            db.close()
            return

        db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=toDatabase,charset='utf8',use_unicode=True)
        cursor = db.cursor()

        getid = "SELECT id FROM StimObjData WHERE descId = '" + toDescId + "'"
        cursor.execute(getid)
        timestamp = cursor.fetchone()
        timestamp = timestamp[0]
        transferSpecs = "INSERT INTO StimObjDataVert(id,descId,vertspec,faceSpec) VALUES ("+str(timestamp)+",'"+str(toDescId)+"','"+vertSpec+"','"+faceSpec+"')"
        cursor.execute(transferSpecs)

        db.commit()
        db.close()
        return

    ###
    ###     IMPORTS
    ###

    def importXML(self,descId):

        self.startImport(descId)
        self.gaFinishImport()
        return

    def importXMLexactlyAsIs(self,descId):

        try:
            self.startImport(descId,replaceID=0)
            self.gaFinishImport()
        except:
            pass
        return

    def importXMLRender(self,descId):

        self.startImport(descId)
        self.gaFinishImportRender()
        return

    def importXMLRenderExactlyAsIs(self,descId):
        
        self.startImport(descId,replaceID=0)
        self.gaFinishImportRender()
        return

    def startImport(self,descId,instantImport=0,replaceID=1,database='DEFAULT'):

        self.deleteToolkit.deleteAllMaterials()
        self.deleteToolkit.deleteAllObjects()

        if database == 'DEFAULT':
            # from Ram's dbExchange.py
            db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
        
        elif database == 'PH_LIBRARY':
            # pre-hoc stimulus library database
            db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=phLibraryName,charset='utf8',use_unicode=True)

        elif database == 'TALL_LIBRARY':
            # pre-hoc stimulus library database
            db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=tallLibraryName,charset='utf8',use_unicode=True)

        else:
            # random stimulus library database
            db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=randomStimDatabaseName,charset='utf8',use_unicode=True)

        cursor = db.cursor()

        queryAlden = "SELECT blenderspec FROM StimObjData WHERE descId = '" + descId + "'"

        try:
            cursor.execute(queryAlden)
            blendSpec = cursor.fetchone()
            blendSpec = blendSpec[0]
        except:
            print("Error: unable to fetch data")

        db.commit()
        db.close()

        try:
            blenderRoot = ET.ElementTree(ET.fromstring(blendSpec))
        except:
            print(descId,' FAILED')
            print("Error: no blendSpec")
            return

        ###
        ###     ALDEN MEDIAL AXIS STIMULUS
        ###

        aldenSub = blenderRoot.find('AldenSpec')

        moniker = descId
        blocky = int(aldenSub.findtext('blocky'))
        present = int(aldenSub.findtext('aldenPresent'))

        if replaceID:
            aldenId = moniker

        else:
            aldenId = str(aldenSub.findtext('id'))
        
        if not instantImport:
            aldenConstr = aldenConstructor()
            edges,faces,verts = aldenConstr.fetchMesh(aldenId)
            mesh = [edges,faces,verts]

            if present:
                alden = self.aldenConstr.draw(moniker,mesh,0,0,0,blocky=blocky)
                alden.id = aldenId

            else:
                alden = aldenObjectSpec()
                self.aldenConstr.aldenSpec = alden
                alden.mesh = 0
                alden.id = aldenId
                alden.blocky = blocky

        else:
            alden = aldenObjectSpec()
            self.aldenConstr.aldenSpec = alden

            bpy.ops.mesh.primitive_cube_add(radius=1,location=(0,0,1), rotation=(0,0,0))
            dummyMesh = [b for b in scn.objects if b.name.startswith('Cube')][0]
            dummyMesh.name = 'AldenObject'
            alden.mesh = dummyMesh

            skeletonConstr = aldenSkeleton(alden)
            skeleton = skeletonConstr.makeSkeleton(moniker,0,0,0,blocky,skipBlocky=1)
            alden.id = aldenId
            alden.blocky = blocky

        alden.present = present

        symmetry = aldenSub.find('bilateralSymmetry')
        alden.mirrored.append(float(symmetry.findtext('x')))
        alden.mirrored.append(float(symmetry.findtext('y')))
        alden.mirrored.append(float(symmetry.findtext('z')))  

        alden.fixationPoint = int(aldenSub.findtext('fixationPoint'))
        alden.whichWiggle = str(aldenSub.findtext('whichWiggle'))

        alden.location = int(aldenSub.findtext('location'))
        alden.wallInteraction = int(aldenSub.findtext('wallInteraction'))
        alden.implantation = float(aldenSub.findtext('implantation'))

        alden.scaleShiftInDepth = round(float(aldenSub.findtext('scaleShiftInDepth')),2)

        try:
            alden.consistentRetinalSize = int(aldenSub.findtext('consistentRetinalSize'))
        except:
            alden.consistentRetinalSize = 1

        alden.material = str(aldenSub.findtext('material'))
        alden.densityUniform = int(aldenSub.findtext('densityUniform'))

        howMany = int(aldenSub.findtext('howMany'))

        if howMany > 0:
            whichLimbs = [int(m.text) for m in aldenSub.find('affectedLimbs')]
            alden.affectedLimbs = whichLimbs

            whichMaterials = [m.text for m in aldenSub.find('limbMaterials')]
            alden.limbMaterials = whichMaterials

        alden.massManipulationLimb = int(aldenSub.findtext('massManipulationLimb'))

        alden.optical = int(aldenSub.findtext('optical'))

        colorBase = aldenSub.find('opticalBeerLambertColor')
        alden.opticalBeerLambertColor.append(float(colorBase.findtext('red')))
        alden.opticalBeerLambertColor.append(float(colorBase.findtext('green')))
        alden.opticalBeerLambertColor.append(float(colorBase.findtext('blue')))
        
        alden.opticalIOR = float(aldenSub.findtext('opticalIOR'))
        alden.opticalTranslucency = float(aldenSub.findtext('opticalTranslucency'))
        alden.opticalAttenuation = float(aldenSub.findtext('opticalAttenuation'))
        alden.opticalTransparency = float(aldenSub.findtext('opticalTransparency'))
        alden.opticalRoughness = float(aldenSub.findtext('opticalRoughness'))
        alden.opticalReflectivity = float(aldenSub.findtext('opticalReflectivity'))

        alden.lowPotentialEnergy = int(aldenSub.findtext('lowPotentialEnergy'))

        precarious = aldenSub.find('makePrecarious')
        alden.makePrecarious.append(float(precarious.findtext('x')))
        alden.makePrecarious.append(float(precarious.findtext('y')))
        alden.makePrecarious.append(float(precarious.findtext('z')))  
        alden.makePrecarious.append(float(aldenSub.findtext('makePrecariousFinal')))

        rotationBase = aldenSub.find('rotation')
        alden.rotation.append(float(rotationBase.findtext('x')))
        alden.rotation.append(float(rotationBase.findtext('y')))
        alden.rotation.append(float(rotationBase.findtext('z')))  

        if present:
            alden.stabRot = [r for r in alden.rotation]
            alden.rotation = []   

        alden.boundingBoxLongAxis = float(aldenSub.findtext('boundingBoxLongAxis'))

        alden.mass = float(aldenSub.findtext('mass'))

        comVector = aldenSub.find('comVector')
        alden.comVector.append(float(comVector.findtext('x')))
        alden.comVector.append(float(comVector.findtext('y')))
        alden.comVector.append(float(comVector.findtext('z')))  

        horizonNormal = aldenSub.find('horizonNormal')
        alden.horizonNormal.append(float(horizonNormal.findtext('x')))
        alden.horizonNormal.append(float(horizonNormal.findtext('y')))
        alden.horizonNormal.append(float(horizonNormal.findtext('z')))     

        ###
        ###     ENVIRONMENT AND STRUCTURE
        ###

        envSub = blenderRoot.find('EnvironmentSpec')

        env = environmentSpec()

        env.stimulusID = descId
        pastStimId = str(blenderRoot.findtext('stimulusID'))

        if pastStimId != descId:
            env.parentID = pastStimId

        else:
            env.parentID = str(blenderRoot.findtext('parentID'))

        env.horizonTilt = float(envSub.findtext('horizonTilt'))
        env.horizonSlant = float(envSub.findtext('horizonSlant'))
        env.horizonMaterial = str(envSub.findtext('horizonMaterial'))
        env.gravity = int(envSub.findtext('gravity'))

        try:
            env.monkeyTilt = int(envSub.findtext('monkeyTilt'))
        except:
            env.monkeyTilt = 0

        env.context = str(envSub.findtext('context'))
        env.compositeKeepAlden = int(envSub.findtext('compositeKeepAlden'))

        env.architecture = int(envSub.findtext('architecture'))
        env.floor = int(envSub.findtext('floor'))
        env.ceiling = int(envSub.findtext('ceiling')) 
        env.wallL = int(envSub.findtext('wallL'))
        env.wallR = int(envSub.findtext('wallR'))
        env.wallB = int(envSub.findtext('wallB')) 
        env.architectureThickness = float(envSub.findtext('architectureThickness'))

        env.distance = float(envSub.findtext('distance'))
        env.structureMaterial = str(envSub.findtext('structureMaterial'))

        env.aperture = int(envSub.findtext('aperture'))

        sunBase = aldenSub.find('sun')
        env.sun.append(float(sunBase.findtext('x')))
        env.sun.append(float(sunBase.findtext('y')))
        env.sun.append(float(sunBase.findtext('z')))

        env.fixationPointDepth = float(envSub.findtext('fixationPointDepth'))

        self.alden = alden
        self.env = env
        self.enviroConstr.enviroSpec = self.env
        self.enclosConstr.enviroSpec = self.env
        self.aldenConstr.aldenSpec = self.alden       
        return

    def gaFinishImport(self):

        alden = self.alden
        env = self.env
        enviroConstr = self.enviroConstr
        enclosConstr = self.enclosConstr

        if 'GrassGravityStimulus' in env.context:
            deContext = env.context.split('_')[1]
            whichCombo = deContext.split('-')
            whichTilt = int(whichCombo[0])
            gravity = int(whichCombo[1])
            secondHorizon = int(whichCombo[2])
            hasBall = int(whichCombo[3])
            ballBuried = int(whichCombo[4])
            stimOri = int(whichCombo[5])

            try:
                comCompensation = int(whichCombo[8])
            except:
                comCompensation = 1

            try:
                backdropTexture = int(whichCombo[9])
                hasBackdrop = 1

            except:
                backdropTexture = None
                hasBackdrop = 0

            if len(whichCombo) > 6:
                hasBack = int(whichCombo[6])
                hasStim = int(whichCombo[7])

            else:
                hasBack = 1
                hasStim = 1

            if ('2_' not in env.context) and ('3_' not in env.context) and ('5_' not in env.context) and ('6_' not in env.context) and ('8_' not in env.context) and ('9_' not in env.context) and ('10_' not in env.context) and ('11_' not in env.context):
                env.horizonMaterial = 'ground08'

            if '9_' in env.context:
                env.horizonMaterial = backdropTextureOptions[backdropTexture]

            if '10_' in env.context:
                env.horizonMaterial = 'sandOG' #'ground08'

            if '11_' not in env.context:    
                env.horizon = enviroConstr.tiltHorizon(backdrop=hasBackdrop)
                mat = env.materialToolkit.useNodes(env.horizon)
                penultimate,penultimateVolume,penultimateDisplacement = env.materialToolkit.makeNodes(mat,env.horizonMaterial,True)
            
            else:
                alden.implantation = 0

                # create pedestal and plant particle base
                bpy.ops.mesh.primitive_cylinder_add(vertices=100, location=(0,0,0))
                pedestal = [p for p in scn.objects if p.name.startswith('Cylinder')][0]
                pedestal.name = 'Pedestal'
                env.horizon = pedestal

                bpy.ops.object.shade_smooth()

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = pedestal
                pedestal.select = True

                bpy.ops.transform.resize(value=(0.5,0.5,1),constraint_axis=(True, True, True))
                pedestal.location = (0,0,0)

                matPedestal = bpy.data.materials.new('PedestalMat')
                matPedestal.use_nodes = True
                matPedestal.node_tree.nodes[1].inputs[0].default_value = (1.0,1.0,1.0,1.0)
                env.horizonMaterial = 'diffusePedestal' # matPedestal

                bpy.ops.object.material_slot_add()
                pedestal.material_slots[0].material = matPedestal
                bpy.ops.object.material_slot_assign()
                
                bpy.ops.object.modifier_add(type='BEVEL')
                pedestal.modifiers['Bevel'].width = 0.02
                pedestal.modifiers['Bevel'].segments = 5
                pedestal.modifiers['Bevel'].use_clamp_overlap = False
                bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Bevel')

                bpy.ops.mesh.primitive_plane_add(radius=1, location=pedestal.location, rotation=(0,0,0))
                planeLeft = [b for b in scn.objects if b.name.startswith('Plane')][0]
                planeLeft.location[0] -= 1.5
                planeLeft.location[2] -= 1
                planeLeft.name = 'PlaneL'

                bpy.ops.mesh.primitive_plane_add(radius=1, location=pedestal.location, rotation=(0,0,0))
                planeRight = [b for b in scn.objects if b.name.startswith('Plane')][0]
                planeRight.location[0] += 1.5
                planeRight.location[2] -= 1
                planeRight.name = 'PlaneR'

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = planeLeft
                planeLeft.select = True
                planeRight.select = True
                bpy.ops.object.join()
                planeLeft.name = 'PlantParticleBase'
                planeLeft.location[2] -= (3-alden.scaleShiftInDepth)*0.3

                # bpy.ops.object.select_all(action='DESELECT')
                # scn.objects.active = pedestal
                # pedestal.select = True
                # planeLeft.select = True
                # bpy.ops.object.parent_set(type='OBJECT')

                ballBuried = 0

            # if '10_' in env.context:
            #     bpy.ops.object.select_all(action='DESELECT')
            #     scn.objects.active = env.horizon
            #     env.horizon.select = True

            #     matSpotlight = bpy.data.materials.new('SpotlightMat')
            #     matSpotlight.use_nodes = True
            #     matSpotlight.node_tree.nodes[1].inputs[0].default_value = (1.0,1.0,1.0,1.0)
            #     env.horizonMaterial = 'diffuseSpotlight' # matPedestal

            #     bpy.ops.object.material_slot_add()
            #     env.horizon.material_slots[0].material = matSpotlight
            #     bpy.ops.object.material_slot_assign()

            if hasBall:
                self.aldenConstr.aldenComplete()
                finalize = finalizeMaterials(alden)
                finalize.applyAllMaterials()

                sphereRadius = 0.15
                
                # for if ball is actually ball...
                # alden.mesh.location = Vector((0,0,env.horizon.location[2]+sphereRadius))

                if ballBuried:
                    scn.update()
                    vertsLocal = alden.mesh.data.vertices
                    vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]
                    zOptions = [v[2] for v in vertsGlobal]
                    meshSize = max(zOptions)-min(zOptions)
                    alden.mesh.location[2] -= min(zOptions)
                    alden.mesh.location[2] -= 0.1*meshSize
                    alden.mesh.location[2] += bumpStrength

                else:
                    xMin,xMax,yMin,yMax,zMin,zMax,leeway = alden.physicsToolkit.findBoundingBox(alden.mesh)
                    alden.mesh.location -= Vector((0,0,zMin))

                otherMesh = alden.mesh

            animator = animation(env)
            enviroConstr.tiltPeripherals()

            if '11_' in env.context: 
                skyEmpty = bpy.data.objects['SkyEmpty']
                skyEmpty.rotation_euler = (-30*math.pi/180,0,0)
                skyEmpty.rotation_euler[0] -= ((3-alden.scaleShiftInDepth)*4)*math.pi/180

            if '10_' in env.context:
                scn.cycles.blur_glossy = True

                bpy.ops.object.lamp_add(type='SPOT')
                spot = bpy.data.objects['Spot']

                # edit spotlight settings
                cameraM = bpy.data.objects['CameraM']
                spot.data.node_tree.nodes['Emission'].inputs[1].default_value = 3000
                spot.location = cameraM.location
                spot.location[2] = 2 #7
                spot.rotation_euler = cameraM.rotation_euler
                spot.data.spot_blend = 1
                spot.data.spot_size = 30*math.pi/180
                spot.data.cycles.cast_shadow = True

                # make environment black
                blackEnvironment = scn.world.node_tree.nodes.new('ShaderNodeRGB')
                blackEnvironment.outputs[0].default_value = (0,0,0,0)
                scn.world.node_tree.links.new(blackEnvironment.outputs[0],scn.world.node_tree.nodes['Background'].inputs[0])

            saveSun = env.sun
            animator.tiltSkySetup()

            env.horizonSlant = 0
            
            if '2_' in env.context:
                env.horizonTilt = horizonTiltOptions2[whichTilt]

            elif ('3_' in env.context) or ('4_' in env.context) or ('5_' in env.context) or ('6_' in env.context) or ('8_' in env.context) or ('9_' in env.context) or ('10_' in env.context) or ('11_' in env.context):
                env.horizonTilt = horizonTiltOptions3[whichTilt]

            else:
                env.horizonTilt = horizonTiltOptions[whichTilt]

            env.gravity = gravity
            env.secondHorizon = secondHorizon
            env.compositeKeepAlden = 1

            enviroConstr.slantScene()
            # fp = enviroConstr.fitFixationPointObjectless(otherMesh=otherMesh)
            fp = enviroConstr.fitFixationPoint(alden)
            scn.world.node_tree.nodes['Sky Texture'].sun_direction = (saveSun[0],saveSun[1],saveSun[2])

            if hasBall:
                # for if ball is actually ball...
                # thetaFP = math.atan((fp.location[1]-env.cameraL.location[1])/(env.cameraL.location[2]-fp.location[2]))
                # shiftBall = (alden.mesh.location[2]-fp.location[2])*math.tan(thetaFP)
                # alden.mesh.location[1] = fp.location[1]-shiftBall

                if stimOri:

                    if ('3_' in env.context) or ('4_' in env.context) or ('5_' in env.context) or ('6_' in env.context) or ('8_' in env.context) or ('9_' in env.context) or ('10_' in env.context) or ('11_' in env.context):
                        scn.world.node_tree.nodes['Sky Texture'].sun_direction = (saveSun[0],saveSun[1],saveSun[2])

                        # rotate COM to [0,0,1], then rotate about y axis as specified
                        # always counter-rotate object
                        finished = False
                        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1.0, view_align=False, location=[0,0,0])
                        comEmpty = [e for e in scn.objects if e.name.startswith('Empty')][0]
                        comEmpty.name = 'COMControl'
                        com = alden.physicsToolkit.centerOfMassByVolume(alden)
                        scn.update()

                        while not finished:

                            xMin,xMax,yMin,yMax,zMin,zMax,leeway = alden.physicsToolkit.findBoundingBox(alden.mesh)
                            alden.mesh.location -= Vector((0,0,zMin))

                            vertsLocal = alden.mesh.data.vertices
                            vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]

                            zOptions = [v[2] for v in vertsGlobal]
                            meshSize = max(zOptions)-min(zOptions)
                            alden.mesh.location[2] -= 0.1*meshSize
                            scn.update()

                            vertsLocal = alden.mesh.data.vertices
                            vertsGlobal = [alden.mesh.matrix_world * v.co for v in vertsLocal]

                            # find the place on the ground (z) corresponding to the crossing
                            underGround = [Vector((v[0],v[1],0)) for v in vertsGlobal if v[2] <= 0.0] # !!! DOESN'T WORK IF HORIZON ISN'T FLAT
                            averageUnderground = [sum([v[0] for v in underGround])/len(underGround),sum([v[1] for v in underGround])/len(underGround),0]
                            comEmpty.location = averageUnderground

                            allContactVectors = [com-u for u in underGround]
                            numContactVectors = max([1,len(allContactVectors)])

                            # sum vectors to produce comVector
                            comVector = Vector((sum([cv[0] for cv in allContactVectors])/numContactVectors,sum([cv[1] for cv in allContactVectors])/numContactVectors,sum([cv[2] for cv in allContactVectors])/numContactVectors))

                            bpy.ops.object.select_all(action='DESELECT')
                            scn.objects.active = comEmpty
                            comEmpty.select = True
                            alden.mesh.select = True
                            bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)

                            bpy.ops.object.select_all(action='DESELECT')
                            scn.objects.active = comEmpty
                            comEmpty.select = True

                            if comCompensation:
                                diffX = comVector[0]
                                diffY = comVector[1]
                                diffZ = comVector[2]

                                # rotX and rotY should be only rots, really...
                                rotX = NP.arctan(diffY/diffZ)
                                rotY = -NP.arctan(diffX/diffZ)

                                comEmpty.rotation_euler[0] += rotX
                                comEmpty.rotation_euler[1] += rotY

                                bpy.ops.object.select_all(action='DESELECT')
                                scn.objects.active = alden.mesh
                                alden.mesh.select = True
                                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                                scn.update()
                                bpy.ops.object.transform_apply(rotation=True)

                                # d = math.sqrt((averageUnderground[0]-alden.mesh.location[0])**2)
                                d = math.sqrt((averageUnderground[0]-alden.mesh.location[0])**2+(averageUnderground[1]-alden.mesh.location[1])**2)

                            else:
                                bpy.ops.object.select_all(action='DESELECT')
                                scn.objects.active = alden.mesh
                                alden.mesh.select = True
                                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                                scn.update()
                                bpy.ops.object.transform_apply(rotation=True)
                                d = 0

                            if d < 0.0001:
                                finished = True
                                fp = enviroConstr.fitFixationPoint(alden)

                        bpy.ops.object.select_all(action='DESELECT')
                        scn.objects.active = comEmpty
                        comEmpty.select = True
                        alden.mesh.select = True
                        bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)

                        # bpy.ops.object.select_all(action='DESELECT')
                        # scn.objects.active = comEmpty
                        # comEmpty.select = True

                        # if ('revised' in env.context):
                        #     rotationExtent = objectRotationExtentsrevised[stimOri-1]
                        # else:
                        #     rotationExtent = objectRotationExtents[stimOri-1]
                            
                        # comEmpty.rotation_euler[1] += rotationExtent

                        # bpy.ops.object.select_all(action='DESELECT')
                        # scn.objects.active = alden.mesh
                        # alden.mesh.select = True
                        # bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                        # scn.update()
                        # bpy.ops.object.transform_apply(rotation=True)

                        if ('revised' in env.context):
                            rotationExtent = objectRotationExtentsrevised[stimOri-1]

                            # bpy.ops.object.select_all(action='DESELECT')
                            # scn.objects.active = alden.mesh
                            # alden.mesh.select = True

                            # x = env.cameraM.matrix_world[0][2]
                            # y = env.cameraM.matrix_world[1][2]
                            # z = env.cameraM.matrix_world[2][2]

                            # bpy.ops.transform.rotate(value=-rotationExtent,axis=(x,y,z),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')

                        else:
                            rotationExtent = objectRotationExtents[stimOri-1]

                            # bpy.ops.object.select_all(action='DESELECT')
                            # scn.objects.active = comEmpty
                            # comEmpty.select = True

                            # comEmpty.rotation_euler[1] += rotationExtent

                        bpy.ops.object.select_all(action='DESELECT')
                        scn.objects.active = alden.mesh
                        alden.mesh.select = True

                        x = env.cameraM.matrix_world[0][2]
                        y = env.cameraM.matrix_world[1][2]
                        z = env.cameraM.matrix_world[2][2]

                        bpy.ops.transform.rotate(value=-rotationExtent,axis=(x,y,z),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')
                        

                        bpy.ops.object.select_all(action='DESELECT')
                        scn.objects.active = alden.mesh
                        alden.mesh.select = True
                        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                        scn.update()
                        bpy.ops.object.transform_apply(rotation=True)


                    # counter-rotate object.

                    if '10_' in env.context:

                        # parent spotlight to horizon
                        bpy.ops.object.select_all(action='DESELECT')
                        scn.objects.active = env.horizon
                        env.horizon.select = True
                        spot.select = True
                        bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)

                    # 1. rotate scene about (0,y,z) of camera rotation (tilt)
                    bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1.0, view_align=False, location=(0, env.cameraL.location[1], env.cameraL.location[2]))
                    tiltEmpty = [e for e in scn.objects if e.name.startswith('Empty')][0]
                    tiltEmpty.name = 'TiltObject'

                    bpy.ops.object.select_all(action='DESELECT')
                    scn.objects.active = tiltEmpty
                    tiltEmpty.select = True
                    alden.mesh.select = True
                    bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)

                    bpy.ops.object.select_all(action='DESELECT')
                    scn.objects.active = tiltEmpty
                    tiltEmpty.select = True

                    x = env.cameraM.matrix_world[0][2]
                    y = env.cameraM.matrix_world[1][2]
                    z = env.cameraM.matrix_world[2][2]
                    bpy.ops.transform.rotate(value=-env.horizonTilt,axis=(x,y,z),constraint_axis=(True,True,True),constraint_orientation='GLOBAL')

                    bpy.ops.object.select_all(action='DESELECT')
                    scn.objects.active = alden.mesh
                    alden.mesh.select = True
                    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                    scn.update()

                    # apply transform.
                    bpy.ops.object.transform_apply(rotation=True)

                if ballBuried:
                    enclosConstr.noEnclosure(alden=alden)
                    # enviroConstr.implantMesh(alden.mesh)

                else:
                    enclosConstr.noEnclosure(alden=alden,hasImplant=0)
                    # enviroConstr.bumpForm(alden.mesh)

                # fp = enviroConstr.fitFixationPointObjectless(otherMesh=otherMesh)
                fp = enviroConstr.fitFixationPoint(alden)

            if '11_' not in env.context:
                enviroConstr.grassGravity()
                particles = bpy.data.particles['scrub']
                particles.hair_length = 2.0

            else:
                xMin,xMax,yMin,yMax,zMin,zMax,leeway = env.physicsToolkit.findBoundingBox(alden.mesh)
                env.horizon.scale[0] *= alden.mesh.scale[0]
                env.horizon.scale[1] *= alden.mesh.scale[1]
                env.horizon.scale[2] *= alden.mesh.scale[2]
                env.horizon.location = alden.mesh.location
                env.horizon.location[2] = zMin - alden.mesh.scale[0]
            
            if '10_' in env.context:
                spot.data.spot_size = 30*(alden.scaleShiftInDepth+1)*math.pi/180 #10
                spot.data.node_tree.nodes['Emission'].inputs[1].default_value = 500*(alden.scaleShiftInDepth+1) #10000
                spot.data.shadow_soft_size = 0.2*(alden.scaleShiftInDepth+1)

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = alden.mesh
                alden.mesh.select = True

                focusLoc = alden.juncEndPt[alden.fixationPoint-2]

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = spot
                spot.select = True

                orientLoc = spot.matrix_world.translation

                distDiffX = focusLoc[0]-orientLoc[0]
                distDiffY = focusLoc[1]-orientLoc[1]
                distDiffZ = focusLoc[2]-orientLoc[2]

                rotZ = -math.atan(distDiffX/distDiffY)
                rotX = math.pi/2 + math.atan(distDiffZ/(math.sqrt(distDiffY**2+distDiffX**2)))

                spot.rotation_euler[2] = rotZ
                spot.rotation_euler[0] = rotX

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = env.horizon
            env.horizon.select = True
            alden.mesh.select = True

            if '11_' in env.context:
                bpy.data.objects['PlantParticleBase'].select = True
            
            bpy.ops.object.parent_set(type='OBJECT')
            enviroConstr.tiltScene()

            # find lowest pt on object
            # find closest pt on horizon
            # lift horizon to that point...

            if env.secondHorizon and env.horizonTilt != 0:

                # remove visibility of environment (for image superposition)
                w = scn.world
                output = w.node_tree.nodes['World Output']
                background = w.node_tree.nodes['Background']
                mix = w.node_tree.nodes['Mix Alpha']
                lightPath = w.node_tree.nodes['Alpha Background']
                w.node_tree.links.new(lightPath.outputs[0],mix.inputs[0])
                w.node_tree.links.new(background.outputs[0],mix.inputs[1])
                w.node_tree.links.new(mix.outputs[0],output.inputs[0])
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

            if not hasBack:

                # remove the background while maintaining lighting influence on object
                scn.cycles.film_transparent = True
                env.horizon.cycles_visibility.camera = False

                grasses = [p for p in bpy.data.objects if p.name.startswith('Plant')]

                for grass in grasses:
                    grass.cycles_visibility.camera = False

            if '4_' in env.context:
                # previous size 1.0
                bpy.ops.mesh.primitive_ico_sphere_add(size=0.1, view_align=False, enter_editmode=False, location=(0,0,-100), rotation=(0,0,0))
                snowflake = [s for s in scn.objects if s.name.startswith('Icosphere')][0]
                snowflake.name = 'Snowflake'

                bpy.context.scene.objects.active = snowflake
                bpy.ops.object.select_all(action='DESELECT')
                snowflake.select = True
                bpy.ops.object.shade_smooth()

                flakeMat = bpy.data.materials.new('Mat')
                flakeMat.use_nodes = True
                flakeMat.node_tree.nodes[1].inputs[0].default_value = (1,1,1,1)

                glass = flakeMat.node_tree.nodes.new('ShaderNodeBsdfGlass')
                flakeMat.node_tree.links.new(glass.outputs[0],flakeMat.node_tree.nodes[0].inputs[0])

                bpy.ops.object.material_slot_add()
                snowflake.material_slots[0].material = flakeMat
                bpy.ops.object.material_slot_assign()

                bpy.ops.mesh.primitive_plane_add(radius=1, location=(0,30,27), rotation=(0,0,0))
                snowPlane = [p for p in scn.objects if p.name.startswith('Plane')][0]
                bpy.ops.transform.resize(value=(50,30,50),constraint_axis=(True, True, True))
                snowPlane.name = 'SnowPlane'

                bpy.context.scene.objects.active = snowPlane
                bpy.ops.object.select_all(action='DESELECT')
                snowPlane.select = True

                particlesOrig = [p for p in bpy.data.particles]
                bpy.ops.object.particle_system_add()
                particleSystems = [m for m in snowPlane.particle_systems if m.name.startswith('ParticleSystem')]
                particleSystem = particleSystems[-1]
                particleSystem.name = 'snow' 
                snowPlane.data.update()

                particles = [p for p in bpy.data.particles]
                particleGroup = [p for p in particles if p not in particlesOrig][0]
                particleGroup.type = 'EMITTER'
                particleGroup.name = 'snow'
                particleGroup.frame_start = -500
                particleGroup.frame_end = 240
                particleGroup.lifetime = 1000
                particleGroup.count = 1000000#1000000#100000
                particleGroup.emit_from = 'FACE'
                particleGroup.render_type = 'OBJECT'
                particleGroup.dupli_object = snowflake
                particleGroup.use_render_emitter = False
                particleGroup.timestep = 0.015#0.008#0.03

                env.horizonTilt = horizonTiltOptions3[whichTilt]

                # unparent horizon and apply transform
                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = env.horizon
                env.horizon.select = True
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                scn.update()
                bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
                print(alden.horizonNormal)

                gravityVector = env.horizon.data.vertices[0].normal
                scn.gravity[0] = gravityVector[0]*-9.81
                scn.gravity[1] = gravityVector[1]*-9.81
                scn.gravity[2] = gravityVector[2]*-9.81

                if alden.mesh:
                    # make alden object a passive thingy so it doesn't slide during snowfall animation
                    alden.mesh.rigid_body.type = 'PASSIVE'

            if alden.mesh and not hasStim:
                self.deleteToolkit.deleteSingleObject(alden.mesh)

            if ('3_' in env.context) or ('5_' in env.context) or ('6_' in env.context) or ('8_' in env.context) or ('9_' in env.context) or ('10_' in env.context):
                particles.hair_length = 0.0
                particles.child_type = 'NONE'

            if '11_' in env.context:
                bpy.ops.wm.collada_import(filepath=materialResources+'pedestalPlants.dae')

                blendfile = materialResources + 'pedestalPlants.blend'
                section = '\\Material\\'
                directory = blendfile + section

                # create group for plants
                previousGroups = [g for g in bpy.data.groups]
                bpy.ops.object.group_add()
                newGroups = [g for g in bpy.data.groups]
                plantGroup = [g for g in newGroups if g not in previousGroups][0]
                plantGroup.name = 'PedestalPlantGroup'

                # BASE LEAF generation and material assignment
                bl = bpy.data.objects['Base_Leaf']
                bpy.ops.wm.append(filename='BaseLeaf', directory=directory)
                matBaseLeaf = bpy.data.materials['BaseLeaf']

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = bl
                bl.select = True

                bpy.ops.object.material_slot_add()
                bl.material_slots[0].material = matBaseLeaf
                bpy.ops.object.material_slot_assign()

                # BASE STEM generation and material assignment
                bs = bpy.data.objects['Base_Stem']
                bs.location[2] -= 100
                bpy.ops.wm.append(filename='BaseStem', directory=directory)
                matBaseStem = bpy.data.materials['BaseStem']

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = bs
                bs.select = True

                bpy.ops.object.material_slot_add()
                bs.material_slots[0].material = matBaseStem
                bpy.ops.object.material_slot_assign()

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = bs
                bs.select = True
                bl.select = True
                bpy.ops.object.join()
                bs.name = 'BasePlant'
                bs.rotation_euler[1] = -math.pi/2

                bpy.ops.object.group_link(group='PedestalPlantGroup')

                # FAT LEAF generation and material assignment
                fl = bpy.data.objects['Fat_Leaf']
                bpy.ops.wm.append(filename='FatLeaf', directory=directory)
                matFatLeaf = bpy.data.materials['FatLeaf']

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = fl
                fl.select = True

                bpy.ops.object.material_slot_add()
                fl.material_slots[0].material = matFatLeaf
                bpy.ops.object.material_slot_assign()

                # FAT STEM generation and material assignment
                fs = bpy.data.objects['Fat_Stem']
                fs.location[2] -= 100
                bpy.ops.wm.append(filename='FatStem', directory=directory)
                matFatStem = bpy.data.materials['FatStem']

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = fs
                fs.select = True

                bpy.ops.object.material_slot_add()
                fs.material_slots[0].material = matFatStem
                bpy.ops.object.material_slot_assign()

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = fs
                fs.select = True
                fl.select = True
                bpy.ops.object.join()
                fs.name = 'FatPlant'
                fs.rotation_euler[1] = -math.pi/2

                bpy.ops.object.group_link(group='PedestalPlantGroup')

                # THIN LEAF generation and material assignment
                tl = bpy.data.objects['Thin_Leaf']
                bpy.ops.wm.append(filename='ThinLeaf', directory=directory)
                matThinLeaf = bpy.data.materials['ThinLeaf']

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = tl
                tl.select = True

                bpy.ops.object.material_slot_add()
                tl.material_slots[0].material = matThinLeaf
                bpy.ops.object.material_slot_assign()

                # THIN STEM generation and material assignment
                ts = bpy.data.objects['Thin_Stem']
                ts.location[2] -= 100
                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = ts
                ts.select = True

                bpy.ops.object.material_slot_add()
                ts.material_slots[0].material = matFatStem
                bpy.ops.object.material_slot_assign()

                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = ts
                ts.select = True
                tl.select = True
                bpy.ops.object.join()
                ts.name = 'ThinPlant'
                ts.rotation_euler[1] = -math.pi/2

                bpy.ops.object.group_link(group='PedestalPlantGroup')

                # plant particle system population
                bpy.ops.object.select_all(action='DESELECT')
                particleBase = bpy.data.objects['PlantParticleBase']
                scn.objects.active = particleBase
                particleBase.select = True

                particlesOrig = [p for p in bpy.data.particles]
                bpy.ops.object.particle_system_add()
                particleSystems = [m for m in particleBase.particle_systems if m.name.startswith('ParticleSystem')]
                particleSystem = particleSystems[-1]
                particleSystem.name = 'PedestalPlants'
                particleSystem.seed = 1 #5
                particleBase.data.update()

                particles = [p for p in bpy.data.particles]
                particleGroup = [p for p in particles if p not in particlesOrig][0]
                particleGroup.type = 'HAIR'
                particleGroup.name = 'PedestalPlantParticles'

                particleGroup.render_type = 'GROUP'
                particleGroup.dupli_group = plantGroup
                particleGroup.use_rotation_dupli = True
                particleGroup.use_scale_dupli = True

                particleGroup.hair_length = 2.0
                particleGroup.size_random = 0.0
                particleGroup.particle_size = 0.1
                particleGroup.child_type = 'NONE'

                particleGroup.use_advanced_hair = True
                particleGroup.use_rotations = True
                particleGroup.rotation_mode = 'OB_Z'
                particleGroup.phase_factor = 0.5
                particleGroup.phase_factor_random = 1.0

                particleGroup.count = 20
                particleGroup.use_render_emitter = False
                particleGroup.distribution = 'JIT'

        elif env.context == 'GrassGravity':
            animator = animation(env)

            pt1 = env.parentID.split('_t-') #'Grass_Gravity_Library', str(whichTilt) + '_g-' + str(gravity) + '_h-' + str(secondHorizon) + '_b-' + str(hasBall) + '_u-' + str(ballBuried)
            pt2 = pt1[1].split('_g-') #str(whichTilt), str(gravity) + '_h-' + str(secondHorizon) + '_b-' + str(hasBall) + '_u-' + str(ballBuried)
            pt3 = pt2[1].split('_h-') #str(gravity), str(secondHorizon) + '_b-' + str(hasBall) + '_u-' + str(ballBuried)
            pt4 = pt3[1].split('_b-') #str(secondHorizon), str(hasBall) + '_u-' + str(ballBuried)
            pt5 = pt4[1].split('_u-') #str(hasBall), str(ballBuried)

            whichTilt = int(pt2[0])
            gravity = int(pt3[0])
            secondHorizon = int(pt4[0])
            hasBall = int(pt5[0])
            ballBuried = int(pt5[1])
            animator.tiltTests(whichTilt,gravity,secondHorizon,hasBall,ballBuried)

        elif env.context == 'SphericalSampling':
            animator = animation(env)

            pt1 = env.parentID.split('_b-') #'Spherical_Sampling_Library', str(blockiness) + '_o-' + str(whichOri) + '_r-' + str(whichRot)
            pt2 = pt1[1].split('_o-') #str(blockiness), str(whichOri) + '_r-' + str(whichRot)
            pt3 = pt2[1].split('_r-') # str(whichOri), str(whichRot)

            blockiness = int(pt2[0])
            whichOri = int(pt3[0])
            whichRot = int(pt3[1])
            animator.sphericalSampling(blockiness,whichOri,whichRot)

        elif env.context == 'StereotypedBalance':
            animator = animation(env)

            pt1 = env.parentID.split('_o-') #'Stereotyped_Balance_Library', str(whichOri) + '_r-' + str(whichRot)
            pt2 = pt1[1].split('_r-') #str(whichOri), str(whichRot)

            whichOri = int(pt2[0])
            whichRot = int(pt2[1])
            animator.stereotypedBalance(whichOri,whichRot)

        elif env.context == 'RandomStimulusLibrary':
            pass

        elif env.context == 'CloseOceanLibrary':
            pass

        elif env.context == 'ViscousPourLibrary':
            pass

        elif env.context == 'WallDropsLibrary':
            pass

        else:
            enviroConstr.assembleEnvironment()
            hasRotation = alden.rotation

            if (env.context == 'Mass') or (env.context == 'Perturbation'):
                alden.rotation = alden.stabRot

            if alden.mesh:
                self.aldenConstr.aldenComplete()
                finalize = finalizeMaterials(alden)
                finalize.applyAllMaterials()

                particles = bpy.data.particles['scrub']
                particles.hair_length = 0.0
                particles.child_type = 'NONE'

            else:
                aldenObjects = [a for a in scn.objects if a.name.startswith('AldenObject')]

                if len(aldenObjects) > 0:
                    self.deleteToolkit.deleteSingleObject(aldenObjects[0])

        if 'Environment' in env.context:
            enclosConstr.assembleEnclosure()

            if alden.mesh:
                self.deleteToolkit.deleteSingleObject(alden.mesh)

            enviroConstr.slantScene()

            fp = enviroConstr.fitFixationPointObjectless()

            enviroConstr.grassGravity()
            enviroConstr.tiltScene()

        elif env.context == 'Composite':
            enclosConstr.assembleEnclosure()

            if alden.mesh:

                if not hasRotation:
                    physicsToolkit = physicsTool()
                    physicsToolkit.wallInteraction(alden)

                fp = enclosConstr.aldenStimulusLocationEnclosure(alden)

            else:
                fp = enviroConstr.fitFixationPointObjectless()

            enviroConstr.grassGravity()
            enviroConstr.tiltScene()

            if alden.mesh:
                bpy.ops.object.select_all(action='DESELECT')
                scn.objects.active = alden.mesh
                alden.mesh.select = True
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                scn.update()

                if not env.compositeKeepAlden:
                    self.deleteToolkit.deleteSingleObject(alden.mesh)
                    self.deleteToolkit.deleteSingleObject(alden.skeleton)
                    isBump = [b for b in env.horizon.modifiers if b.name.startswith('soilBump')]

                    if isBump:
                        isBump[0].strength = 0

                    self.deleteToolkit.deleteSingleObject(fp)
                    fp = enviroConstr.fitFixationPointObjectless()

        elif env.context == 'Animate':
            enclosConstr.noEnclosure(alden=alden)
            alden.massToolkit.makeRigidBody(alden.mesh,'PASSIVE')
            animator = animation(env)
            animator.postHocWiggle(alden)

        elif 'Symmetry' in env.context:
            # [bilateral symmetry, rotate 180, mirror]

            symmetryMod = env.context.split('-')
            rot180 = int(symmetryMod[1])
            mirror = int(symmetryMod[2])

            bpy.ops.object.select_all(action='DESELECT')
            scn.objects.active = alden.mesh
            alden.mesh.select = True

            if rot180:
                bpy.ops.transform.rotate(value=math.pi,axis=(0,0,1),constraint_axis=(False,False,True),constraint_orientation='GLOBAL')

            if mirror:
                bpy.ops.transform.mirror(constraint_axis=(True,False,False),constraint_orientation='GLOBAL')

        elif env.context == 'RandomStimulusLibrary':
            pass

        elif env.context == 'CloseOceanLibrary':
            pass

        elif env.context == 'ViscousPourLibrary':
            pass

        elif env.context == 'WallDropsLibrary':
            pass

        elif 'GrassGravity' not in env.context:

            if env.context not in ['Ball','SphericalSampling','StereotypedBalance']:
                enclosConstr.noEnclosure(alden=alden)

                # bpy.ops.object.select_all(action='DESELECT')
                # scn.objects.active = alden.mesh
                # alden.mesh.select = True
                # bpy.ops.object.transform_apply(scale=True)
                # alden.massToolkit.assignMass(alden.mesh,'')

        if usesOccluder:
            enviroConstr.gaussianOccluder()

        if env.aperture:
            enviroConstr.aperture()

        if not stereoscopic:
            fps = [fp for fp in scn.objects if fp.name.startswith('FixationPoint')]

            for fp in fps:
                self.deleteToolkit.deleteSingleObject(fp)

        return

    def gaFinishImportRender(self):

        self.gaFinishImport()
        render = stimulusRender(self.alden,self.env)

        if self.env.context == 'Animate':

            # previous stimulus type still or animate?
            previousId = self.env.stimulusID.split("_s-")
            genlin = previousId[0]
            previousId = int(previousId[1])-1
            previousId = genlin + '_s-' + str(previousId)

            db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
            cursor = db.cursor()

            queryAnimacy = "SELECT javaspec FROM StimObjData WHERE descId = '" + previousId + "'"

            try:
                cursor.execute(queryAnimacy)
                javaSpec = cursor.fetchone()
                javaSpec = javaSpec[0]

            except:
                print("Error: unable to fetch data")

            db.commit()
            db.close()

            javaRoot = ET.ElementTree(ET.fromstring(javaSpec))
            previousStimType = str(javaRoot.findtext('stimType'))

            if previousStimType == 'ANIMACY_STILL':
                render.renderAnimation(duplicateForStill=True)

            else:
                render.renderAnimation()

        elif self.env.context == 'GrassGravity':
            render.copyFromLibrary()

        elif 'GrassGravityStimulus4_' in self.env.context:
            # render.copyAnimationFromLibrary(frameExtent=240,libraryPath=snowLibrary,libraryPrefix='Snow_Animation_Library_')
            render.renderAnimation(duplicate=False,frames=240)

        elif self.env.context == 'SphericalSampling':
            render.copyFromLibrary(libraryPath=sphericalSamplingLibrary)

        elif self.env.context == 'StereotypedBalance':
            render.copyFromLibrary(libraryPath=stereotypedBalanceLibrary)

        elif 'RandomStimulusLibrary' in self.env.context:
            render.copyFromLibrary(libraryPath=randomStimulusLibrary)

        elif 'PreHocStimulusLibrary' in self.env.context:
            render.copyFromLibrary(libraryPath=preHocStimulusLibrary)

        elif 'TallStimulusLibrary' in self.env.context:
            render.copyFromLibrary(libraryPath=tallStimulusLibrary)

        elif 'CloseOceanLibrary' in self.env.context:
            render.copyFromLibrary(libraryPath=closeOceanLibrary)

        elif 'ViscousPourLibrary' in self.env.context:
            render.copyFromLibrary(libraryPath=viscousPourLibrary)

        elif 'WallDropsLibrary' in self.env.context:
            render.copyFromLibrary(libraryPath=wallDropsLibrary)

        elif self.env.context == 'Ball':
            render.copyAnimationFromLibrary()

        elif 'Object' in self.env.context:

            # current stimulus type ANIMACY_STILL? if so, skip render. *need to edit this to keep the stiff stimuli...*
            currentId = self.env.stimulusID

            db = mysql.connector.connect(user='xper_rw', password='up2nite', host=databaseIP, database=databaseName,charset='utf8',use_unicode=True)
            cursor = db.cursor()

            queryAnimacy = "SELECT javaspec FROM StimObjData WHERE descId = '" + currentId + "'"

            try:
                cursor.execute(queryAnimacy)
                javaSpec = cursor.fetchone()
                javaSpec = javaSpec[0]

            except:
                print("Error: unable to fetch data")

            javaRoot = ET.ElementTree(ET.fromstring(javaSpec))
            currentStimType = str(javaRoot.findtext('stimType'))

            if currentStimType == 'ANIMACY_STILL':

                nextId = self.env.stimulusID.split("_s-")
                genlin = nextId[0]
                nextId = int(nextId[1])+1
                nextId = genlin + '_s-' + str(nextId)

                queryAnimacy = "SELECT javaspec FROM StimObjData WHERE descId = '" + nextId + "'"

                try:
                    cursor.execute(queryAnimacy)
                    javaSpec = cursor.fetchone()
                    javaSpec = javaSpec[0]

                except:
                    print("Error: unable to fetch data")
                    javaSpec = False
                
                if javaSpec:

                    javaRoot = ET.ElementTree(ET.fromstring(javaSpec))
                    nextStimType = str(javaRoot.findtext('stimType'))

                    if nextStimType == 'ANIMACY_ANIMATE':
                        render.renderFinished()

                    else:
                        render.renderStill()

                else:
                    render.renderStill()
                    
            else:
                render.renderStill()

            db.commit()
            db.close()

        else:
            render.renderStill()

        return

