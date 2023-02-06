import sys
import os
import pprint
import pickle
import logging
dname = os.path.dirname(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, dname)

from kibot.EasyEDA.easyeda_3d import *

component_id = 'C181094'

if False:
    download_easyeda_3d_model(component_id, 'test')
    exit(0)
#
if True:
    a = EasyedaApi()
    res = a.get_cad_data_of_component(component_id)
    print(pprint.pformat(res))
    if not res:
        logging.error('Not found')
        exit(1)
    c = Easyeda3dModelImporter(res, True)
    print("********************************************")
    print(pprint.pformat(c.__dict__))
    with open('model.pkl', 'wb') as file:
        pickle.dump(c, file)
else:
    with open('model.pkl', 'rb') as file:
        c = pickle.load(file)
    # print(pprint.pformat(c.__dict__))
    with open('model.obj', 'w') as file:
        file.write(c.output.raw_obj)

exporter = Exporter3dModelKicad(model_3d=c.output)

os.makedirs('a.3dshapes', exist_ok=True)
exporter.export('a.3dshapes')
if exporter.output:
    filename = f"{exporter.output.name}.wrl"
    lib_path = "a.3dshapes"
    logging.error(f"Created 3D model for ID: {component_id}\n"
                  f"       3D model name: {exporter.output.name}\n"
                  f"       3D model path: {os.path.join(lib_path, filename)}")
