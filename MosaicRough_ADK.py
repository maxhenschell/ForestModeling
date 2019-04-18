#!C:/Users/mxhensch/AppData/Local/Continuum/anaconda3/envs/arcgispro-py3 python
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 14:48:23 2018

@author: mxhensch
"""
#import modules
import os
import arcpy
from arcpy import env
from arcpy.sa import *

#Directories
root = r'C:\Users\mxhensch\GIS_data'
ADK = os.path.join(root,"ADK")
DEM = os.path.join(ADK,"DEM")
outDir = DEM#os.path.join(DEM)#os.path.join("H:/GIS_data/ForestModeling/Catskills/DEM/")
clip = os.path.join(ADK,"ADK_1km.shp")
#arcpy.env.extent = clip
#arcpy.env.mask = clip
outSamp = "in_memory/Outsamp"
snapRs = r"H:\GIS_data\ForestModeling\ADK\modelData\Filled_L2A_20170730_B02.tif"
arcpy.env.snapRaster = snapRs

# Script arguments
Input_DEM = os.path.join(DEM,"ADK_DEM.tif")
CellSize = 20
Z_factor = "1"

#set arc env values
arcpy.env.overwriteOutput = True
arcpy.env.nodata = "None"
arcpy.CheckOutExtension("Spatial")
arcpy.env.workspace = ADK
arcpy.Delete_management("in_memory")
arcpy.env.snapRaster = Input_DEM
WGS = arcpy.SpatialReference(os.path.join(root,"WGS_1984.prj"))
UTM18 = arcpy.SpatialReference(root,"NAD_1983_UTM_Zone_18N.prj")
arcpy.env.overwriteOutput = True
arcpy.env.resamplingMethod = "BILINEAR"
arcpy.env.nodata = "NoData"
CellSize = float(arcpy.GetRasterProperties_management(Input_DEM, 'CELLSIZEX').getOutput(0))
clip = os.path.join(root,"ADK_1km.shp")

# get dirs in root
dirList = arcpy.ListWorkspaces("ADKR*", "FileGDB")
dd = dirList[0]

for dd in dirList:
	print(dd)
	arcpy.env.workspace = dd
	inRas = arcpy.ListRasters("*", "All")
	len(inRas)
	Ras = ';'.join(inRas)
	#valType = arcpy.GetRasterProperties_management(inRas[0], "VALUETYPE")
	bands = arcpy.GetRasterProperties_management(inRas[1], "BANDCOUNT")

	print("Mosaicing...")
	mos = "in_memory/mos"
	rrr =  "in_memory/rrr"
	arcpy.MosaicToNewRaster_management(input_rasters = Ras, output_location = "in_memory", raster_dataset_name_with_extension = "mos", pixel_type = "32_BIT_FLOAT", mosaic_method = "FIRST", coordinate_system_for_the_raster = UTM18, number_of_bands = bands)

	# print("Resampling...")
	# arcpy.Resample_management(mos, rrr, CellSize, "BILINEAR")
	print("Clipping...")
	outClip = "in_memory/clp"
	OutFinal = os.path.splitext(os.path.basename(os.path.normpath(dd)))[0]+".tif"
	outFinal = os.path.join(outDir,outFinal)
	arcpy.Clip_management(in_raster = rrr, out_raster = outFinal, in_template_dataset = clip, maintain_clipping_extent = "NO_MAINTAIN_EXTENT", nodata_value = "NoData", clipping_geometry = "ClippingGeometry")
	arcpy.Delete_management(mos, rrr) 


	# print("Writing %s.."%(outFinal))
	# arcpy.CopyRaster_management(outClip, outFinal) 
	# arcpy.Delete_management("in_memory") 
	print("Done!")


