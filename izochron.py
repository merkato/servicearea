"""
/***************************************************************************
 Izochron
                                 a QGIS plugin
                                 
 based on "Fast SQL Layer" plugin Copyright 2011 Pablo Torres Carreira and "pgRouting Layer" by Anita Graser
                             -------------------
        begin                : 2014-01-07
        copyright            : (c) 2014 by Tomasz Nycz
        email                : tomasz.nycz@gis-support.pl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 **************************************************************************/
"""
# Import the PyQt and QGIS libraries
from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import qgis.utils
import dbConnection
import izochron_utils as Utils
#import highlighter as hl
import os
import psycopg2
import psycopg2.extensions # for isolation levels
import re

conn = dbConnection.ConnectionManager()

class izochron:

    SUPPORTED_FUNCTIONS = [
        'createDd',
        'updateDd',
        'clearDd',
        'isochrones',
    ]
    TOGGLE_CONTROL_NAMES = [
        'labelGeometry','lineEditGeometry',
        'labelTable','lineEditTable',
        'labelId', 'lineEditId',
        'labelSource', 'lineEditSource',
        'labelTarget', 'lineEditTarget',
        'labelCost', 'lineEditCost',
        'labelDistance', 'lineEditDistance',
        'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
        'pd_brec_checkbox',
    ]
    FIND_RADIUS = 15
    
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        
        self.idsVertexMarkers = []
        self.sourceIdVertexMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.sourceIdVertexMarker.setColor(Qt.red)
        self.sourceIdVertexMarker.setPenWidth(3)
        self.sourceIdVertexMarker.setVisible(False)
        self.sourceIdRubberBand = QgsRubberBand(self.iface.mapCanvas(), Utils.getRubberBandType(False))
        self.sourceIdRubberBand.setColor(Qt.cyan)
        self.sourceIdRubberBand.setWidth(4)
        self.canvasItemList = {}
        self.canvasItemList['markers'] = []
        
    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/izochron_plugin/icons/icon.png"), "Izochron", self.iface.mainWindow())
        #Add toolbar button and menu item
        self.iface.addPluginToDatabaseMenu("&Czasy nominalne", self.action)
        
        #load the form
        path = os.path.dirname(os.path.abspath(__file__))
        self.dock = uic.loadUi(os.path.join(path, "ui_izochron.ui"))
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        self.sourceIdEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())
        #connect the action to each method
        QObject.connect(self.action, SIGNAL("triggered()"), self.show)
        QObject.connect(self.dock.comboBoxFunction, SIGNAL("currentIndexChanged(const QString&)"), self.updateFunctionEnabled)        
        QObject.connect(self.dock.buttonSelectSourceId, SIGNAL("clicked(bool)"), self.selectSourceId)
        QObject.connect(self.sourceIdEmitPoint, SIGNAL("canvasClicked(const QgsPoint&, Qt::MouseButton)"), self.setSourceId)
        QObject.connect(self.dock.buttonRun, SIGNAL("clicked()"), self.run)
        
        #populate the combo with connections
        actions = conn.getAvailableConnections()
        self.actionsDb = {}
        for a in actions:
            self.actionsDb[ unicode(a.text()) ] = a
        for i in self.actionsDb:
            self.dock.comboConnections.addItem(i)
        
        self.prevType = None
        self.functions = {}
        for funcfname in self.SUPPORTED_FUNCTIONS:
            # import the function
            exec("from functions import %s as function" % funcfname)
            funcname = function.Function.getName()
            self.functions[funcname] = function.Function(self.dock)
            self.dock.comboBoxFunction.addItem(funcname)
        
        self.dock.lineEditSourceId.setValidator(QIntValidator())
        self.loadSettings()
        
    def show(self):
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        
    def unload(self):
        self.saveSettings()
        # Remove the plugin menu item and icon
        self.iface.removePluginDatabaseMenu("&czasy nominalne", self.action)
        self.iface.removeDockWidget(self.dock)
        
    def updateFunctionEnabled(self, text):
        function = self.functions[str(text)]
        
        self.toggleSelectButton(None)
        
        for controlName in self.TOGGLE_CONTROL_NAMES:
            control = getattr(self.dock, controlName)
            control.setVisible(False)
        
        for controlName in function.getControlNames():
            control = getattr(self.dock, controlName)
            control.setVisible(True)
        
        contents = self.dock.scrollAreaWidgetContents
        margins = contents.layout().contentsMargins()
        self.dock.scrollAreaColumns.setMaximumHeight(contents.sizeHint().height() + margins.top() + margins.bottom())
                
        # if type(edge/node) changed, clear input
        if (self.prevType != None) and (self.prevType != function.isEdgeBase()):
            self.clear()
            
        self.prevType = function.isEdgeBase()
        
    def selectSourceId(self, checked):
        if checked:
            self.toggleSelectButton(self.dock.buttonSelectSourceId)
            self.dock.lineEditSourceId.setText("")
            self.sourceIdVertexMarker.setVisible(False)
            self.sourceIdRubberBand.reset(Utils.getRubberBandType(False))
            self.iface.mapCanvas().setMapTool(self.sourceIdEmitPoint)
        else:
            self.iface.mapCanvas().unsetMapTool(self.sourceIdEmitPoint)
        
    def setSourceId(self, pt):
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]
        args = self.getBaseArguments()
        if not function.isEdgeBase():
            result, id, wkt = self.findNearestNode(args, pt)
            if result:
                self.dock.lineEditSourceId.setText(str(id))
                geom = QgsGeometry().fromWkt(wkt)
                self.sourceIdVertexMarker.setCenter(geom.asPoint())
                self.sourceIdVertexMarker.setVisible(True)
                self.dock.buttonSelectSourceId.click()
        else:
            result, id, wkt = self.findNearestLink(args, pt)
            if result:
                self.dock.lineEditSourceId.setText(str(id))
                geom = QgsGeometry().fromWkt(wkt)
                if geom.wkbType() == QGis.WKBMultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            self.sourceIdRubberBand.addPoint(pt)
                elif geom.wkbType() == QGis.WKBLineString:
                    for pt in geom.asPolyline():
                        self.sourceIdRubberBand.addPoint(pt)
                self.dock.buttonSelectSourceId.click()
        self.iface.mapCanvas().refresh()

                
    def run(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]
        args = self.getArguments(function.getControlNames())
        
        empties = []
        for key in args.keys():
            if args[key] is None:
                empties.append(key)
        
        if len(empties) > 0:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self.dock, self.dock.windowTitle(),
                'Following argument is not specified.\n' + ','.join(empties))
            return
        
        try:
			dados = str(self.dock.comboConnections.currentText())
			db = self.actionsDb[dados].connect()
			con = db.con
			srid, geomType = self.getSridAndGeomType(con, args)
			function.prepare(con, args, geomType, self.canvasItemList)
			query = function.getQuery(args)         
			cur = con.cursor()
			cur.execute(query)
			con.commit()
			#QMessageBox.information(self.dock, self.dock.windowTitle(), query)
			self.refresh_layers()
			          
        except psycopg2.DatabaseError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            
        except SystemError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            
        except AssertionError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self.dock, self.dock.windowTitle(), '%s' % e)
            
        finally:
            QApplication.restoreOverrideCursor()
            if db and db.con:
                try:
                    db.con.close()
                except:
                    QMessageBox.critical(self.dock, self.dock.windowTitle(),
                        'server closed the connection unexpectedly')
                     
        
    def clear(self):
        self.dock.lineEditIds.setText("")
        for marker in self.idsVertexMarkers:
            marker.setVisible(False)
        self.idsVertexMarkers = []
        self.dock.lineEditSourceId.setText("")
        self.sourceIdVertexMarker.setVisible(False)
        #self.sourceIdRubberBand.reset(Utils.getRubberBandType(False))
        for marker in self.canvasItemList['markers']:
            marker.setVisible(False)
        self.canvasItemList['markers'] = []
        
    def toggleSelectButton(self, button):
        selectButtons = [
            self.dock.buttonSelectSourceId,
        ]
        for selectButton in selectButtons:
            if selectButton != button:
                if selectButton.isChecked():
                    selectButton.click()
        
    def getArguments(self, controls):
        args = {}
        args['schemat'] = self.dock.lineEditSchemat.text()
        if 'lineEditTable' in controls:
			args['edge_table'] = self.dock.lineEditTable.text()
        if 'lineEditGeometry' in controls:
			args['geometry'] = self.dock.lineEditGeometry.text()
             
        if 'lineEditId' in controls:
            args['id'] = self.dock.lineEditId.text()
        if 'lineEditSource' in controls:
            args['source'] = self.dock.lineEditSource.text()
        
        if 'lineEditTarget' in controls:
            args['target'] = self.dock.lineEditTarget.text()
        
        if 'lineEditCost' in controls:
            args['cost'] = self.dock.lineEditCost.text()
        
        if 'lineEditSourceId' in controls:
            args['source_id'] = self.dock.lineEditSourceId.text()
        
        if 'lineEditDistance' in controls:
            args['distance'] = self.dock.lineEditDistance.text()
        
        if 'pd_brec_checkbox' in controls:
            args['pd_brec_checked'] = self.dock.pd_brec_checkbox.isChecked()
        else:
			args['pd_brec_checked'] = 'Nieczynne'
        
        if 'plainTextEditTurnRestrictSql' in controls:
            args['turn_restrict_sql'] = self.dock.plainTextEditTurnRestrictSql.toPlainText();
        
        return args
        
    def getBaseArguments(self):
        args = {}
        args['edge_table'] = self.dock.lineEditTable.text()
        args['geometry'] = self.dock.lineEditGeometry.text()
        args['schemat'] = self.dock.lineEditSchemat.text()        
        args['id'] = self.dock.lineEditId.text()
        args['source'] = self.dock.lineEditSource.text()
        args['target'] = self.dock.lineEditTarget.text()
        
        empties = []
        for key in args.keys():
            if args[key] is None:
                empties.append(key)
        
        if len(empties) > 0:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self.dock, self.dock.windowTitle(),
                'Following argument is not specified.\n' + ','.join(empties))
            return None
        
        return args
        
    def getSridAndGeomType(self, con, args):
        cur = con.cursor()
        cur.execute("""
            SELECT ST_SRID(%(geometry)s), ST_GeometryType(%(geometry)s)
                FROM %(schemat)s.%(edge_table)s
                WHERE %(id)s = (SELECT MIN(%(id)s) FROM %(schemat)s.%(edge_table)s)""" % args)
        row = cur.fetchone()
        srid = row[0]
        geomType = row[1]
        return srid, geomType
        
    # emulate "matching.sql" - "find_nearest_node_within_distance"
    def findNearestNode(self, args, pt):
        distance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * self.FIND_RADIUS
        rect = QgsRectangle(pt.x() - distance, pt.y() - distance, pt.x() + distance, pt.y() + distance)
        canvasCrs = Utils.getDestinationCrs(self.iface.mapCanvas().mapRenderer())
        db = None
        try:
            dados = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dados].connect()
            
            con = db.con
            srid, geomType = self.getSridAndGeomType(con, args)
            if self.iface.mapCanvas().hasCrsTransformEnabled():
                layerCrs = QgsCoordinateReferenceSystem()
                Utils.createFromSrid(layerCrs, srid)
                trans = QgsCoordinateTransform(canvasCrs, layerCrs)
                pt = trans.transform(pt)
                rect = trans.transform(rect)
            
            args['canvas_srid'] = Utils.getCanvasSrid(canvasCrs)
            args['srid'] = srid
            args['x'] = pt.x()
            args['y'] = pt.y()
            args['minx'] = rect.xMinimum()
            args['miny'] = rect.yMinimum()
            args['maxx'] = rect.xMaximum()
            args['maxy'] = rect.yMaximum()
            
            Utils.setStartPoint(geomType, args)
            Utils.setEndPoint(geomType, args)
            Utils.setTransformQuotes(args)
            
            # Getting nearest source
            query1 = """
            SELECT %(source)s,
                ST_Distance(
                    %(startpoint)s,
                    ST_GeomFromText('POINT(%(x)f %(y)f)', %(srid)d)
                ) AS dist,
                ST_AsText(%(transform_s)s%(startpoint)s%(transform_e)s)
                FROM %(schemat)s.%(edge_table)s
                WHERE ST_SetSRID('BOX3D(%(minx)f %(miny)f, %(maxx)f %(maxy)f)'::BOX3D, %(srid)d)
                    && %(geometry)s ORDER BY dist ASC LIMIT 1""" % args
            
            cur1 = con.cursor()
            cur1.execute(query1)
            row1 = cur1.fetchone()
            d1 = None
            source = None
            wkt1 = None
            if row1:
                d1 = row1[1]
                source = row1[0]
                wkt1 = row1[2]
            
            # Getting nearest target
            query2 = """
            SELECT %(target)s,
                ST_Distance(
                    %(endpoint)s,
                    ST_GeomFromText('POINT(%(x)f %(y)f)', %(srid)d)
                ) AS dist,
                ST_AsText(%(transform_s)s%(endpoint)s%(transform_e)s)
                FROM %(schemat)s.%(edge_table)s
                WHERE ST_SetSRID('BOX3D(%(minx)f %(miny)f, %(maxx)f %(maxy)f)'::BOX3D, %(srid)d)
                    && %(geometry)s ORDER BY dist ASC LIMIT 1""" % args
            
            cur2 = con.cursor()
            cur2.execute(query2)
            row2 = cur2.fetchone()
            d2 = None
            target = None
            wkt2 = None
            if row2:
                d2 = row2[1]
                target = row2[0]
                wkt2 = row2[2]
            
            # Checking what is nearer - source or target
            d = None
            node = None
            wkt = None
            if d1 and (not d2):
                node = source
                d = d1
                wkt = wkt1
            elif (not d1) and d2:
                node = target
                d = d2
                wkt = wkt2
            elif d1 and d2:
                if d1 < d2:
                    node = source
                    d = d1
                    wkt = wkt1
                else:
                    node = target
                    d = d2
                    wkt = wkt2
            
            if (d == None) or (d > distance):
                node = None
                wkt = None
                fail_message = 'Node not found in search radius.\nRadius: ' + str(distance) + '\nSRS: ' + str(Utils.getCanvasSrid(canvasCrs))
                QMessageBox.information(self.dock, self.dock.windowTitle(), fail_message)
                return False, None, None
            
            return True, node, wkt
            
        except psycopg2.DatabaseError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            return False, None, None
            
        finally:
            if db and db.con:
                db.con.close()

    def loadSettings(self):
        settings = QSettings()
        idx = self.dock.comboConnections.findText(Utils.getStringValue(settings, '/izochron/Database', ''))
        if idx >= 0:
            self.dock.comboConnections.setCurrentIndex(idx)
        idx = self.dock.comboBoxFunction.findText(Utils.getStringValue(settings, '/izochron/Function', 'updateDd'))
        if idx >= 0:
            self.dock.comboBoxFunction.setCurrentIndex(idx)
        
        self.dock.lineEditTable.setText(Utils.getStringValue(settings, '/izochron/sql/edge_table', 'osm_2po_4pgr'))
        self.dock.lineEditGeometry.setText(Utils.getStringValue(settings, '/izochron/sql/geometry', 'geom_way'))
        self.dock.lineEditSchemat.setText(Utils.getStringValue(settings, '/izochron/sql/schemat', 'public'))        
        self.dock.lineEditId.setText(Utils.getStringValue(settings, '/izochron/sql/id', 'id'))
        self.dock.lineEditSource.setText(Utils.getStringValue(settings, '/izochron/sql/source', 'source'))
        self.dock.lineEditTarget.setText(Utils.getStringValue(settings, '/izochron/sql/target', 'target'))
        self.dock.lineEditCost.setText(Utils.getStringValue(settings, '/izochron/sql/cost', 'cost'))
        
        self.dock.lineEditSourceId.setText(Utils.getStringValue(settings, '/izochron/source_id', ''))
        self.dock.lineEditDistance.setText(Utils.getStringValue(settings, '/izochron/distance', ''))
        
    def saveSettings(self):
        settings = QSettings()
        settings.setValue('/izochron/Database', self.dock.comboConnections.currentText())
        settings.setValue('/izochron/Function', self.dock.comboBoxFunction.currentText())
        
        settings.setValue('/izochron/sql/edge_table', self.dock.lineEditTable.text())
        settings.setValue('/izochron/sql/geometry', self.dock.lineEditGeometry.text())
        settings.setValue('/izochron/sql/schemat', self.dock.lineEditSchemat.text())        
        settings.setValue('/izochron/sql/id', self.dock.lineEditId.text())
        settings.setValue('/izochron/sql/source', self.dock.lineEditSource.text())
        settings.setValue('/izochron/sql/target', self.dock.lineEditTarget.text())
        settings.setValue('/izochron/sql/cost', self.dock.lineEditCost.text())
        
        settings.setValue('/izochron/source_id', self.dock.lineEditSourceId.text())
        settings.setValue('/izochron/distance', self.dock.lineEditDistance.text())
        #settings.setValue('/izochron/pd_brec_checked', self.dock.pd_brec_check.isChecked()
    def refresh_layers(self):
		for layer in qgis.utils.iface.mapCanvas().layers():
			layer.triggerRepaint()
