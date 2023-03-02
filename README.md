# PPSG
Photorealistic Parametric Scene Generator (Blender API) source, Python

Welcome to the Photorealistic Parametric Scene Generator, a Python suite designed to generate and morph random objects, environments, and scenes!

PPSG relies upon communication with a SQL database for image generation, extracting vertex and face information generated using a complementary Java-based system to assemble base meshes. Scene details are extracted from and written to SQL database ```databaseName``` at ```databaseIP``` (see ```config.py```).

```stimViewer.blend``` is a Blender environment pre-equipped to run ```seeStim.py```, which allows for the viewing of scenes whose vertex-, face-, and blend-spec details are already parametrically stored in ```databaseName```. Stimulus selection is controlled through specification of the parameter ```descId``` in ```seeStim.py```.

If you really want to generate novel objects and scenes but have no SQL database, you can feed comma-separated face and vertex lists directly into ```randomSpec.py```. Comment out line 49 (```edges,faces,verts = aldenConstr.fetchMesh(descId)```) and set the ```faces``` and ```verts``` values manually. (Empty ```faces``` and ```verts``` lists will default to objectless scene generation.) Set ```stimType = None```.

Note: the "MaterialResources" folder here is incomplete—it should also contain a set of proprietary ```.blend``` files purchased as CMV (The Cycles Material Vault) from https://cyclesmaterialvault.gumroad.com/l/Yrhkx 

Unfortunately, due to licensing restrictions, I cannot share these files publically. For more information, please contact me at aliya.emonds@gmail.com.

