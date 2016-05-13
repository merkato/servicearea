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
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

def name():
    return "izochron"
def description():
    return "Dokowalny widget do obliczania izochron"
def version():
    return "Version 0.1"
def icon():
    return "icon.png"
def qgisMinimumVersion():
    return "1.9"
def classFactory(iface):
    from izochron import izochron
    return izochron(iface)
