
import bpy

import config
from config import *


###
###     DELETE TOOLS
###

class deleteTool:

    kind = 'Delete Toolkit'

    def __init__(self):

        self.whichMesh = None

    def deleteAllObjects(self):

        while bpy.context.scene.objects:

            for whichMesh in bpy.context.scene.objects:
                self.deleteSingleObject(whichMesh)

        while bpy.data.materials:

            for m in bpy.data.materials:
                bpy.data.materials.remove(m)

        self.deleteAllNodes()
        return

    def deleteAllNodes(self):

        if bpy.context.scene.world.node_tree:

            for node in bpy.context.scene.world.node_tree.nodes:

                if node not in [bpy.context.scene.world.node_tree.nodes[0],bpy.context.scene.world.node_tree.nodes[1]]:
                    bpy.context.scene.world.node_tree.nodes.remove(node)

        return

    def deleteAllMaterials(self):

        if bpy.data.materials:

            for m in bpy.data.materials:

                # if m.users:
                #     m.user_clear()

                bpy.data.materials.remove(m)
        return

    def deleteSingleObject(self,whichMesh):

        self.whichMesh = whichMesh

        bpy.context.scene.objects.active = whichMesh
        bpy.ops.object.select_all(action='DESELECT')
        whichMesh.select = True
        bpy.ops.object.delete(use_global=False)
        return

    def deleteSingleObjectMaterials(self,whichMesh):

        self.whichMesh = whichMesh

        bpy.context.scene.objects.active = whichMesh
        bpy.ops.object.select_all(action='DESELECT')
        whichMesh.select = True

        if whichMesh.data.materials:

            while len([m for m in self.whichMesh.data.materials]) > 0:
                whichMesh.active_material_index = 0
                bpy.ops.object.material_slot_remove()

        return

