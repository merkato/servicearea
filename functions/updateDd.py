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
        return 'updateDd'
    
    @classmethod
    def getControlNames(self):
        return [
            'labelGeometry','lineEditGeometry',
            'labelTable','lineEditTable',
            'labelId', 'lineEditId',
            'labelSource', 'lineEditSource',
            'labelTarget', 'lineEditTarget',
            'labelCost', 'lineEditCost',
			'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
            'labelDistance', 'lineEditDistance','labelDelay', 'lineEditDelay',
        ]
    
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
        return """INSERT INTO %(schemat)s.catchment
		SELECT id1, %(geometry)s, route.cost+'%(delay)s' AS route.cost, row_number() over () AS qgis_id, %(source_id)s AS source
			FROM %(schemat)s.%(edge_table)s
JOIN (SELECT * FROM pgr_drivingDistance('
SELECT %(id)s AS id,
                    %(source)s::int4 AS source,
                    %(target)s::int4 AS target,
                    %(cost)s::float8 AS cost
                    FROM %(schemat)s.%(edge_table)s',
%(source_id)s, %(distance)s,      false,      false)) AS route 
ON %(schemat)s.%(edge_table)s.source = route.id1;""" % args
   
 
    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
