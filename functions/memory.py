mem_layer = QgsVectorLayer("Polygon?crs=epsg:4326", "temp_layer", "memory")
if not mem_layer.isValid(): raise Exception("Failed to create memory layer")            
mem_layer_provider = mem_layer.dataProvider()

clip_polygon = QgsFeature()
clip_polygon.setGeometry(QgsGeometry.fromRect( 
    QgsRectangle(
        self.output_layer.extent().xMinimum() + 10,
        self.output_layer.extent().yMinimum() + 10,
        self.output_layer.extent().xMaximum() - 10,
        self.output_layer.extent().yMaximum() - 10
    )
))
mem_layer_provider.addFeatures([clip_polygon])
mem_layer.updateExtents()

output = self.output_layer_path + "2"
processing.runalg("qgis:clip", layer, mem_layer, output) # Fails
