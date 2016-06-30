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
        return 'createDd'
    
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
            'labelDistance', 'lineEditDistance', 'labelDelay', 'lineEditDelay',
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
        return """CREATE TABLE %(schemat)s.catchment AS
		SELECT id1, %(geometry)s, route.cost + %(delay)s AS cost, row_number() over () AS qgis_id, %(source_id)s AS source
			FROM %(schemat)s.%(edge_table)s
JOIN (SELECT * FROM pgr_drivingDistance('
SELECT %(id)s AS id,
                    %(source)s::int4 AS source,
                    %(target)s::int4 AS target,
                    %(cost)s::float8 AS cost
                    FROM %(schemat)s.%(edge_table)s',
%(source_id)s, %(distance)s,      false,      false)) AS route 
ON %(schemat)s.%(edge_table)s.source = route.id1;
CREATE OR REPLACE VIEW %(schemat)s.catchment_final AS
SELECT row_number() over () AS qgis_id, id1, geom_way, source, cost * 60::double precision AS cost FROM %(schemat)s.catchment a WHERE NOT EXISTS (SELECT 1 FROM %(schemat)s.catchment b WHERE a.id1 = b.id1 and b.cost < a.cost);
CREATE OR REPLACE VIEW %(schemat)s.points_min AS SELECT cost, row_number() over () AS qgis_id, ST_Transform(ST_Centroid(%(geometry)s), 2180) AS geometry FROM %(schemat)s.catchment_final;
CREATE INDEX cost_idx ON %(schemat)s.catchment (cost);
CREATE INDEX ident_idx ON %(schemat)s.catchment (id1);
""" % args
  
 
    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
