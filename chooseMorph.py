
import bpy
import random


class morphStimulus:

    def __init__(self,whichContext,didStickMorph=0):

        self.context = whichContext
        self.minMorphs = 1
        self.maxMorphs = 2
        self.didStickMorph = didStickMorph
        self.whichMorphs = None
        self.__findMorph()

    def __findMorph(self):

        howManyMorphs = random.randint(self.minMorphs,self.maxMorphs)
        whichMorphs = []

        if 'Object' in self.context:

            while len(whichMorphs) < howManyMorphs:

                # CDF_ObjectMorph = [0,7,14,24,34,44]                         # [7%,7%,10%,10%,10%] [blockiness, bilateral symmetry, base material, orientation, shift scale]
                CDF_ObjectMorph = [0,8,8,20,32,44]                         # [8%,0%,12%,12%,12%] [blockiness, bilateral symmetry, base material, orientation, shift scale]
                idx = self.__getIdx(CDF_ObjectMorph,random.randint(0,44))

                if idx == 1:
                    # blockiness
                    chosenMorph = 'SwitchBlockiness'

                elif idx == 2:
                    # bilateral symmetry
                    chosenMorph = 'AlterSymmetry'

                elif idx == 3:
                    # base material

                    CDF_BaseMaterialMorphInit = [0.0,0.20,1.0]                  # [20%,80%] [canned material, optics]
                    idx = self.__getIdx(CDF_BaseMaterialMorphInit,random.random())

                    if idx == 1:
                        # canned material

                        CDF_CannedDestiny = [0.0,0.20,1.0]                          # [20%,80%] [new canned material, optics transition]
                        idx = self.__getIdx(CDF_CannedDestiny,random.random())

                        if idx == 1:
                            # new canned material
                            chosenMorph = 'BodyBase'

                        elif idx == 2:
                            # optics transition
                            chosenMorph = 'OpticsTransition'

                    elif idx == 2:
                        # optics

                        CDF_OpticsDestiny = [0.0,0.20,1.0]                          # [20%,80%] [new optics, canned material transition]
                        idx = self.__getIdx(CDF_OpticsDestiny,random.random())

                        if idx == 1:
                            # new optics

                            CDF_OpticsMorphType = [0.0,0.20,0.40,0.60,0.80,1.0]    # [20%,20%,20%,20%,20%] [roughness, reflectivity, transparency, index of refraction, color]
                            idx = self.__getIdx(CDF_OpticsMorphType,random.random())

                            if idx == 1:
                                # roughness
                                chosenMorph = 'AlterRoughness'

                            elif idx == 2:
                                # reflectivity
                                chosenMorph = 'AlterReflectivity'

                            elif idx == 3:
                                # transparency
                                chosenMorph = 'AlterTransparency'

                            elif idx == 4:
                                # index of refraction
                                chosenMorph = 'AlterIOR'

                            elif idx == 5:
                                # color
                                chosenMorph = 'AlterBLColor'

                        elif idx == 2:
                            # canned material transition
                            chosenMorph = 'CannedTransition'

                elif idx == 4:
                    # orientation

                    chosenMorph = 'PrecariousnessMorph'

                elif idx == 5:
                    # shift scale in depth

                    chosenMorph = 'ScaleShiftInDepth'

                if chosenMorph not in whichMorphs:
                    whichMorphs.append(chosenMorph)


        elif 'Environment' in self.context:

            for alteration in range(howManyMorphs):

                CDF_EnvironmentMorph = [0.0,0.25,0.40,0.55,0.65,0.80,0.95,1.0] # [25%,15%,15%,10%,15%,15%,5%] [architecture, tilt, slant, lighting, structure material, horizon material, structure distance]
                idx = self.__getIdx(CDF_EnvironmentMorph,random.random())

                if idx == 1:
                    # architecture
                    whichMorphs.append('ArchitectureComposition')

                elif idx == 2:
                    # tilt
                    whichMorphs.append('ChangeHorizonTilt')

                elif idx == 3:
                    # slant
                    whichMorphs.append('ChangeHorizonSlant')

                elif idx == 4:
                    # lighting
                    whichMorphs.append('AlterTimeOfDay')

                elif idx == 5:
                    # structure material
                    whichMorphs.append('NewStructureMaterial')

                elif idx == 6:
                    # horizon material
                    whichMorphs.append('NewHorizonMaterial')

                elif idx == 7:
                    # structure distance
                    whichMorphs.append('ChangeDistance')
                
        elif self.context == 'Composite':
            # object/architecture interactions

            CDF_CompositeMorph = [0.0,0.5,1.0]                           # [50%,50%] [object location, architecture]
            idx = self.__getIdx(CDF_CompositeMorph,random.random())

            if idx == 1:
                whichMorphs.append('ObjectPosition')

            elif idx == 2:
                whichMorphs.append('ArchitectureCompositionAlden')

        # elif self.context == 'Post-Hoc':
        #     # gravity directions are from a library...

        #     whichMorphs.append('ChangeGravityDirection')

        #     whichMorphs.append('ImplantationMorph')
        #     whichMorphs.append('PotentialMorph')

        #     whichMorphs.append('SeparateLimb')
        #     whichMorphs.append('RestoreLimb')
        #     whichMorphs.append('ChangeLimb')
        #     whichMorphs.append('ViralLimbBase')
        #     whichMorphs.append('ViralLimbRetain')
        #     whichMorphs.append('CannedTransition')

        self.whichMorphs = whichMorphs
        return

    def __getIdx(self,cdf,randomVal):

        idx = 0

        while idx < len(cdf):

            if randomVal <= cdf[idx]:
                return idx

            else:
                idx += 1

        return idx

