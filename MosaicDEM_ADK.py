#!C:/Users/mxhensch/AppData/Local/Continuum/anaconda3/envs/arcgispro-py3 python
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 14:48:23 2018

@author: mxhensch
"""

import os
import arcpy

# set in folder
root = r'H:/GIS_data/ForestModeling/'
ADK = os.path.join(root,"ADK/")
S2 = os.path.join(ADK,"DEM/Clips/")
outDir = os.path.join(ADK,"DEM/")
arcpy.env.overwriteOutput = True
arcpy.env.snapRaster = r"C:\Users\mxhensch\GIS_data\ForestModeling\Catskills\Sen2Scenes\tiles\TVM_20170317_B02.tif"

#slices
def left(s, amount):
    return s[:amount]
def right(s, amount):
    return s[-amount:]
def mid(s, offset, amount):
    return s[offset:offset+amount]

clip = os.path.join(outDir+"ADK_1km.shp")
arcpy.env.extent = clip
WGS = arcpy.SpatialReference(os.path.join(ADK+"WGS_1984.prj"))

# get tiles
arcpy.env.workspace = os.path.join(S2)
inRas = arcpy.ListRasters("*", "TIF")

inRas = [os.path.join(arcpy.env.workspace, f) for f in inRas]
Ras = ';'.join(inRas)
bands = arcpy.GetRasterProperties_management (inRas[0], "BANDCOUNT")
mos = "in_memory/ras"
outClip = "in_memory/clp"
outFinal = os.path.join(outDir+"ADK_DEM.tif")
arcpy.MosaicToNewRaster_management(input_rasters = Ras,output_location = "in_memory/",raster_dataset_name_with_extension = "ras",pixel_type = "32_BIT_FLOAT",mosaic_method = "MEAN", coordinate_system_for_the_raster = WGS, number_of_bands = bands)
arcpy.Clip_management(in_raster = mos, out_raster = outClip, in_template_dataset = clip, maintain_clipping_extent = "NO_MAINTAIN_EXTENT", nodata_value = "NoData")
arcpy.CopyRaster_management(outClip, outFinal) 
arcpy.Delete_management("in_memory") 

#dateBand = list(set([mid(x,4,12) for x in S2S] ))
#
#
#for dB in dateBand:
#    outName = dB+"_mosaic.tif"
#    if not os.path.isfile(outName):
#        print("Creating file "+outName+"...")
#        ss = "*"+dB+"*"
#        arcpy.env.workspace = os.path.join(S2,"tiles/")
#        inRas = arcpy.ListRasters(ss, "TIF")
#        inRas = [os.path.join(arcpy.env.workspace, f) for f in inRas]
#        Ras = ';'.join(inRas)
#        bands = arcpy.GetRasterProperties_management (inRas[0], "BANDCOUNT")
#
#        arcpy.MosaicToNewRaster_management(input_rasters = Ras,output_location = "in_memory/",raster_dataset_name_with_extension = "ras",pixel_type = "16_BIT_UNSIGNED",mosaic_method = "MEAN", coordinate_system_for_the_raster = WGS, number_of_bands = bands)
#    else: print(outName+" exists")
#    
#    #clip to extent of Catskils
#    
#    mos = "in_memory/ras"#os.path.join(S2,outName)
#    if not os.path.isfile(outFinal):
#        print("Creating file "+outFinal+"...")
#        arcpy.Clip_management(in_raster = mos, out_raster = outClip, in_template_dataset = clip, maintain_clipping_extent = "NO_MAINTAIN_EXTENT", clipping_geometry = "ClippingGeometry", nodata_value = "NoData")
#        arcpy.CopyRaster_management(outClip, outFinal) 
#    else: print(outFinal+" exists")
#    arcpy.Delete_management("in_memory") 
#    
#end