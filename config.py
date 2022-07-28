
import math
import bpy
import os


###
###     SETUP AND COMMONLY REFERENCED VARIABLES
### 

monkey = 'Merri'
# monkey = 'Gizmo'
# monkey = 'Dobby'

#.#.#.#.#.#.#
# RENDERING PREFERENCES
#.#.#.#.#.#.#

scn = bpy.context.scene
totalFrames = 60                                                   # 60 for 60 fps
headless = True
lens = 55                   # in mm
sensorWidth = 63.5          # in mm
usesOccluder = False
resolutionX = 3840 #1400
resolutionY = 2160 #1050
stereoscopic = False

#.#.#.#.#.#.#
# USER INFORMATION
#.#.#.#.#.#.#

root = os.path.dirname(bpy.data.filepath) + '/'
specSource = root + 'SpecSource/'
materialResources = root + 'MaterialResources/'

# stills = '/home/alexandriya/blendRend/Rendered/'
# animations = '/home/alexandriya/blendRend/Rendered/'
# ballLibrary = '/home/alexandriya/blendRend/RollingBallLibrary/'
# grassGravLibrary = '/home/alexandriya/blendRend/GrassGravityLibrary/'

stills = '/home/alexandriya/workingBlendRend/Rendered/'
animations = '/home/alexandriya/workingBlendRend/Rendered/'
ballLibrary = '/home/alexandriya/workingBlendRend/RollingBallLibrary/'
grassGravLibrary = '/home/alexandriya/workingBlendRend/GrassGravityLibrary/'
sphericalSamplingLibrary = '/home/alexandriya/workingBlendRend/SphericalSamplingLibrary/'
stereotypedBalanceLibrary = '/home/alexandriya/workingBlendRend/StereotypedBalanceLibrary/'
randomStimulusLibrary = '/home/alexandriya/workingBlendRend/RandomStimulusLibrary/'
preHocStimulusLibrary = '/home/alexandriya/workingBlendRend/PreHocStimulusLibrary/'
tallStimulusLibrary = '/home/alexandriya/workingBlendRend/TallStimulusLibrary/'

closeOceanLibrary = '/home/alexandriya/workingBlendRend/CloseOceanLibrary/'
viscousPourLibrary = '/home/alexandriya/workingBlendRend/ViscousPourLibrary/'
wallDropsLibrary = '/home/alexandriya/workingBlendRend/WallDropsLibrary/'

snowLibrary = '/home/alexandriya/workingBlendRend/SnowLibrary/'
randomStimDatabaseName = 'alexandriya_180218_random_stimulus_library_3'
phLibraryName = 'alexandriya_180218_ph_stimulus_library'
tallLibraryName = 'alexandriya_180218_tall_stimulus_library'
librarySize = 200
phLibrarySize = 50

databaseName = 'alexandriya_180218_test'
# databaseIP = '172.30.6.31'

# databaseName = 'alexandriya_180218_20-09-20'#'alexandriya_180218_noTDT_19-08-01'
databaseIP = '172.30.6.80'

#.#.#.#.#.#.#
# MONKEY MEASUREMENTS
#.#.#.#.#.#.#

monkeyPerspectiveAngle = 22.5*math.pi/180                           # in radians
monkeyDistanceY = 3.0#1.5#3#6.6                                               # meters (feet)
monkeyDistanceZ = monkeyDistanceY*math.tan(monkeyPerspectiveAngle)  # in meters
monkeyEyeDistance = 0.036#0.05#0.164#0.05                                            # meters (feet)
projectorHoriz = 6.6                                                # meters 
distanceMeasurements = 'Y'                                          # options: H (hypotenuse) or Y (y-axis)

#.#.#.#.#.#.#
# STRUCTURE OPTIONS
#.#.#.#.#.#.#

structureMaterialOptions = ['tile08','rock02','stone02','metal01','glass04','concrete04','concrete07','tileOG','wireframe']
# 'onyx01'

architectureScale = 1.5                                            # in meters (radii of basic planes for architecture)
lengthScale = 1.2
heightScale = 1.0
architectureDistanceOptions = [-0.25,4.0]                           # in meters [inside, outside]
desiredFocalLength = 3 # hypotenuse 1.5 m (~5 ft)

#.#.#.#.#.#.#
# ALDEN OPTIONS
#.#.#.#.#.#.#

stimulusScale = 4
monikers = range(91,99)

aldenMaterialOptions = ['bubble01','car_paint01','clay01','cork01','plastic01','rubber01',
                        'amber01','emerald01','marble04','marbleOG',
                        'gold01','copper01','bronze01','chrome01','aluminum_foil01',
                        'calamondin01','apple01','lemon01','orange01','tomato01','gelatin01','honey01','peanut_butter01','chocolate02',
                        'hedgehog01','fur01','cactus01',
                        'glass02','glass04','uncorrugatedOG','corrugatedOG',
                        'woodOG','paperOG']
culledAldenMaterialOptions = ['clay01','plastic01','rubber01',
                        'amber01','emerald01','marble04','marbleOG',
                        'gold01','copper01','bronze01','chrome01','aluminum_foil01','car_paint01',
                        'calamondin01','apple01','lemon01','orange01','tomato01','gelatin01','chocolate02',
                        'hedgehog01','fur01','cactus01',
                        'glass02','glass04','uncorrugatedOG','corrugatedOG',
                        'woodOG','paperOG','cork01']

# whichGummyWiggleOptions = ['squish01','squish02','squish03','squish04','squish05']
# whichRigidWiggleOptions = ['stiff01','stiff02','stiff03','stiff04','stiff05']

whichGummyWiggleOptions = ['clay01','fur01','gelatin01','plastic01','rubber01']
whichRigidWiggleOptions = ['amber01','marble04','bronze01','woodOG','glass04']

#.#.#.#.#.#.#
# ENVIRONMENT OPTIONS
#.#.#.#.#.#.#

horizonMaterialOptions = ['sand01','ground02','ground03','ground08','sandOG','pavement01','wood_planks02','tile05','tarmac02','industrialOG']
horizonGrassMaterialOptions = ['ground02','ground03','ground08','sandOG'] # removed 'sand01'
groundColors = [[110,94,72],[115,102,77],[142,139,132],[130,126,122]]
backdropTextureOptions = ['musgrave','tetragonal','industrialOG']

lightingOptions = []
possibleAngles = [5,15,25,35,45,135,145,155,165,175]                # in degrees (angle between sun and horizon, center of unit circle [0,0,0])

for alpha in possibleAngles:  
    x = math.cos(alpha*math.pi/180)
    z = math.sin(alpha*math.pi/180)
    lightingOptions.append([x,-0.5,z])

# horizonTiltOptions = [v/4*(20)*math.pi/180 for v in range(-4,5)]    # parenthetical max (+) and min (-) tilt in degrees
# horizonSlantOptions = [v/8*(36)*math.pi/180 for v in range(-8,1)]   # parenthetical max slant in degrees

horizonTiltOptions = [-45*math.pi/180,-22.5*math.pi/180,0,22.5*math.pi/180,45*math.pi/180]      # radians
horizonTiltOptions2 = [-25*math.pi/180,-20*math.pi/180,-15*math.pi/180,-10*math.pi/180,-5*math.pi/180,0,5*math.pi/180,10*math.pi/180,15*math.pi/180,20*math.pi/180,25*math.pi/180]      # radians
# horizonTiltOptions3 = [-30*math.pi/180,0,30*math.pi/180]                                          # radians
horizonTiltOptions3 = [-25*math.pi/180,0,25*math.pi/180]   
# want random horizonTiltOptions between -22.5 and +22.5
# objectRotationExtents = [-60*math.pi/180,-45*math.pi/180,-30*math.pi/180,-15*math.pi/180,0,15*math.pi/180,30*math.pi/180,45*math.pi/180,60*math.pi/180]
objectRotationExtents = [-50*math.pi/180,-37.5*math.pi/180,-25*math.pi/180,-12.5*math.pi/180,0,12.5*math.pi/180,25*math.pi/180,37.5*math.pi/180,50*math.pi/180]
objectRotationExtentsrevised = [-115*math.pi/180,-100*math.pi/180,-75*math.pi/180,-50*math.pi/180,-25*math.pi/180,0,25*math.pi/180,50*math.pi/180,75*math.pi/180,100*math.pi/180,115*math.pi/180]

horizonSlantOptions = [-22.5*math.pi/180,0,22.5*math.pi/180]   
# burialDepth = [0,1/10,1/8,1/4,1/2]
# burialDepth = [0,1/10,1/20]
burialDepth = [0,1/10,1/8]
bumpStrength = 0.1
compositeCompensatoryRot = True
perturbationLeans = [22.5*math.pi/180,45*math.pi/180]
perturbationDepths = [1/10,1/4]

###.
