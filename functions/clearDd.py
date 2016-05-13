from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import psycopg2
from .. import izochron_utils as Utils
from FunctionBase import FunctionBase

class Function(FunctionBase):
    
    @classmethod
    def getName(self):
        return 'clearDd'
    
    @classmethod
    def getControlNames(self):
        return ['labelGeometry','lineEditGeometry',
            'labelTable','lineEditTable',
            'labelId', 'lineEditId']
    
    @classmethod
    def isEdgeBase(self):
        return False
    
    @classmethod
    def canExport(self):
        return False
    
    def prepare(self, con, args, geomType, canvasItemList):
        resultNodesVertexMarkers = canvasItemList['markers']
        for marker in resultNodesVertexMarkers:
            marker.setVisible(False)
        canvasItemList['markers'] = []
    
    def getQuery(self, args):
        return """TRUNCATE TABLE %(schemat)s.catchment;""" % args

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
