import adsk.core
import adsk.fusion

from ...lib import fusionAddInUtils as futil


def inspect_tab_face(face: adsk.fusion.BRepFace):
    futil.log('--- TAB FACE ---')

    futil.log(f'Area: {face.area}')

    for i in range(face.edges.count):
        edge = face.edges.item(i)

        futil.log(
            f'Edge {i}: '
            f'length = {edge.length}, '
            f'faces = {edge.faces.count}'
        )