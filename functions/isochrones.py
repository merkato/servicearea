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
        return 'isochrones'
    
    @classmethod
    def getControlNames(self):
        return ['labelGeometry','lineEditGeometry',
            'labelTable','lineEditTable',
            'labelId', 'lineEditId','pd_brec_checkbox']
    
    #@classmethod
    #def isEdgeBase(self):
        #return False
    
    #@classmethod
    #def canExport(self):
        #return False
    
    def getQuery(self, args):
		if args['pd_brec_checked'] == True:
			return """DROP TABLE IF EXISTS %(schemat)s.potencjal;
					CREATE TABLE %(schemat)s.potencjal AS
					WITH kawalki AS 
					(SELECT ST_Transform(ST_Collect(geom_way), 2180) as geom,source FROM %(schemat)s.catchment_final GROUP BY source) 
					SELECT z.source, SUM(l.total_pop), ST_ConcaveHull((z.geom),0.75) AS geometry 
					FROM public.ludnosc l, kawalki z 
					WHERE ST_Intersects(l.geom, z.geom) GROUP BY z.source, z.geom;""" % args
		else:
			return """DROP TABLE IF EXISTS %(schemat)s.potencjal;
					CREATE TABLE %(schemat)s.potencjal AS
					WITH kawalki AS 
					(SELECT ST_Transform(ST_Collect(geom_way), 2180) as geom,source FROM %(schemat)s.catchment_final GROUP BY source) 
					SELECT z.source, ST_ConcaveHull((z.geom),0.75) AS geometry 
					FROM kawalki z GROUP BY z.source, z.geom;""" % args

    def __init__(self, ui):
		FunctionBase.__init__(self, ui)
