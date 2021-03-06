#!C:/Users/mxhensch/AppData/Local/Continuum/anaconda3/envs/arcgispro-py3 python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Slope_Curv.py
# Created on: 2018-11-09 12:19:15.00000
#   (generated by ArcGIS/ModelBuilder)
# Description: From SDM-EV-Tools. Modified for Forest Preserve tree modeling
# ---------------------------------------------------------------------------

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
arcpy.env.extent = clip
arcpy.env.mask = clip
outSamp = "in_memory/Outsamp"
WGS = arcpy.SpatialReference(os.path.join(ADK,"WGS_1984.prj"))
NAD = arcpy.SpatialReference(os.path.join(ADK,"NAD_1983_UTM_Zone_18N.prj"))
snapRs = r"H:\GIS_data\ForestModeling\ADK\modelData\Filled_L2A_20170730_B02.tif"
arcpy.env.snapRaster = snapRs

#set arc env values
arcpy.env.overwriteOutput = True
arcpy.env.nodata = "None"
arcpy.CheckOutExtension("Spatial")
arcpy.env.workspace = os.path.join(root,"ADK/DEM/")
arcpy.Delete_management("in_memory")

#get master raster 
#else: res = resX.getOutput(0) +" "+ resY.getOutput(0) 
arcpy.env.cellSize = snapRs

# Script arguments
Input_DEM = os.path.join(DEM,"ADK_DEM.tif")

## print("Registering DEM...")
## arcpy.RegisterRaster_management (in_raster = Input_DEM, register_mode = "REGISTER", reference_raster = SenMaster)
#
#print("Resampling DEM...")
#arcpy.Resample_management(in_raster = Input_DEM,out_raster = outSamp, cell_size = res, resampling_type = "BILINEAR")

#Output files
Output_slope_raster__degrees_ = os.path.join(outDir,"ADK_slope.tif")
Output_curvature_raster = os.path.join(outDir,"ADK_curv.tif")
Output_profile_curvature_raster = os.path.join(outDir,"ADK_profCurve.tif")
Output_plan_curvature_raster = os.path.join(outDir,"ADK_planCurv.tif")

# Local variables:
Output_slope_measure = "DEGREE"
Z_factor = "1"

#Process: Slope
print("Calculating slope...")
outSlope = Slope(in_raster = Input_DEM, output_measurement = Output_slope_measure, z_factor = Z_factor)
outSlope.save(Output_slope_raster__degrees_)

# Process: Curvature
print("Calculating curvature...")
outCurve = Curvature(in_raster = Input_DEM, z_factor = Z_factor, out_profile_curve_raster = Output_profile_curvature_raster, out_plan_curve_raster = Output_plan_curvature_raster)
outCurve.save(Output_curvature_raster)


##arcpy.gp.Slope_sa(outSamp, "in_memory/slope", Output_slope_measure, Z_factor)
#arcpy.Clip_management(in_raster = outSlope, out_raster = outSamp, in_template_dataset = clip, maintain_clipping_extent = "NO_MAINTAIN_EXTENT", clipping_geometry = "ClippingGeometry")
#arcpy.CopyRaster_management(outSamp, Output_slope_raster__degrees_)
#arcpy.Delete_management("in_memory/slope", outSamp)
#
#
#arcpy.gp.Curvature_sa(outSamp, "in_memory/curv", Z_factor, "in_memory/profcurv", "in_memory/plancurv")
#
##Output clipped DEM derivatives
#arcpy.Clip_management(in_raster = "in_memory/curv", out_raster = "in_memory/Ccurv", in_template_dataset = clip, maintain_clipping_extent = "NO_MAINTAIN_EXTENT", clipping_geometry = "ClippingGeometry")
#
#print("Writing slope...")
#arcpy.CopyRaster_management("in_memory/Ccurv", Output_curvature_raster)
#arcpy.Delete_management("in_memory/curv","in_memory/Ccurv")
#
#arcpy.Clip_management(in_raster = "in_memory/profcurv", out_raster = "in_memory/Prcurv", in_template_dataset = clip, maintain_clipping_extent = "NO_MAINTAIN_EXTENT", clipping_geometry = "ClippingGeometry")
#
#print("Writing profile curvature...")
#arcpy.CopyRaster_management("in_memory/Prcurv", Output_profile_curvature_raster)
#arcpy.Delete_management("in_memory/profcurv","in_memory/Prcurv")
#
#arcpy.Clip_management(in_raster = "in_memory/plancurv", out_raster = "in_memory/Plcurv", in_template_dataset = clip, maintain_clipping_extent = "NO_MAINTAIN_EXTENT", clipping_geometry = "ClippingGeometry")
#
#print("Writing planar curvature...")
#arcpy.CopyRaster_management("in_memory/Plcurv", Output_plan_curvature_raster)
#
#arcpy.Delete_management("in_memory")