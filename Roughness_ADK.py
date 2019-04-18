# -----------------------------------------------------------------------------------------
# Roughness.py
# Version:  Python 2.7.5 / ArcGIS 10.2.2
# Creation Date: 2015-07-25
# Last Edit: 2015-07-25
# Creator:  Kirsten R. Hazler
#
# Summary:
#     Uses an input Digital Elevation Model (DEM) to derive terrain roughness indices at three different scales. "Roughness" is defined as the standard deviation of elevation values within a specified neighborhood.  Scale is determined by the neighborhood radii (in units of raster cells) input by the user. Each neighborhood is defined as a circle with radius r, unless r = 1, in which case a square 3x3 neighborhood is used.

# Processing is done by USGS quads or by other units defined by a polygon feature class. Thus, the output for each defined scale (neighborhood) is a set of rasters which will need to be mosaicked together later.
# -----------------------------------------------------------------------------------------

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
#arcpy.env.extent = clip
#arcpy.env.mask = clip
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
CellSize = 20
Z_factor = "1"

quads = r"M:\reg0\reg0data\layerfiles\quad24.lyr"
arcpy.MakeFeatureLayer_management(quads, "quads")
arcpy.SelectLayerByLocation_management("quads", "intersect", clip, 0, "NEW_SELECTION")
   

R1 = 1
R2 = 10
R3 = 100
maxRad = max(R1, R2, R3)
   
outGDB1 = os.path.join(ADK,"ADKR1.gdb")#arcpy.GetParameterAsText(6) # Geodatabase to hold final products for neighborhood 1
if not os.path.exists(outGDB1):
    arcpy.CreateFileGDB_management (ADK, "ADKR1.gdb")

outGDB2 = os.path.join(ADK,"ADKR10.gdb")#arcpy.GetParameterAsText(7) # Geodatabase to hold final products for neighborhood 2
if not os.path.exists(outGDB2):
    arcpy.CreateFileGDB_management (ADK, "ADKR10.gdb")
    
outGDB3 = os.path.join(ADK,"ADKR100.gdb")#arcpy.GetParameterAsText(8) # Geodatabase to hold final products for neighborhood 3
if not os.path.exists(outGDB3):
    arcpy.CreateFileGDB_management (ADK, "ADKR100.gdb")

inFld = "PREFIX"
ProcUnits = arcpy.da.SearchCursor("quads", [inFld])
Unit = ProcUnits.next()
for Unit in ProcUnits:
    try:
        UnitID = Unit[0]
        print('Working on unit %s...' % UnitID)
    
    # Make a feature class with the single unit's shape, then buffer it
        print('Selecting feature...')
        where_clause = "%s = '%s'" % (inFld, UnitID) # Create the feature selection expression
        arcpy.MakeFeatureLayer_management ("quads", 'selectFC', where_clause) 
      
        print('Buffering feature...')
        buffFC = "in_memory/buffFC"#scratchGDB + os.sep + 'buffFC' + UnitID
        buffDist = CellSize*maxRad*2
        arcpy.Buffer_analysis('selectFC', buffFC, buffDist)
        # Specify output

        #if not os.path.isfile(outRoughness): 
        # Clip the DEM to the above feature
        print('Clipping DEM to feature...')
        clipDEM = "in_memory/clipDEM"#scratchGDB + os.sep + 'clipDEM'
        extent = arcpy.Describe(buffFC).extent
        XMin = extent.XMin
        YMin = extent.YMin
        XMax = extent.XMax
        YMax = extent.YMax
        rectangle = '%s %s %s %s' %(XMin, YMin, XMax, YMax) 
        arcpy.Clip_management (in_raster = Input_DEM, out_raster = clipDEM, rectangle = rectangle, in_template_dataset = buffFC, maintain_clipping_extent = "NO_MAINTAIN_EXTENT", nodata_value = "NoData")
       # arcpy.Clip_management (in_raster = rghnss, out_raster = outRoughness, in_template_dataset = 'selectFC', maintain_clipping_extent = "NO_MAINTAIN_EXTENT", clipping_geometry = "ClippingGeometry", nodata_value = "NoData")
        
        # Set processing mask
        arcpy.env.mask = clipDEM 
        
        # Loop through the focal statistics process for each radius
        r = 1
        for item in ((R1, outGDB1), (R2, outGDB2), (R3, outGDB3)):
        #   Define neighborhood
            radius = item[0]
            if radius == 1:
                nghbrhd = NbrRectangle(3, 3, "CELL")
            else:
                nghbrhd = NbrCircle(radius, "CELL")
        
            gdb = item[1]
            outRoughness = gdb + os.sep + "rough_" + UnitID + "_" + str(radius)
            #print(outRoughness)
            # Run focal statistics
            print('Calculating %s roughness for radius %d...' %(UnitID, radius))
            rghnss = FocalStatistics(in_raster = clipDEM, neighborhood = nghbrhd, statistics_type = "STD", ignore_nodata = "DATA")
         
            # Clip to original unit shape
            extent = arcpy.Describe('selectFC').extent
            XMin = extent.XMin
            YMin = extent.YMin
            XMax = extent.XMax
            YMax = extent.YMax
            rectangle = '%s %s %s %s' %(XMin, YMin, XMax, YMax) 
            print('     Clipping output %s roughness for radius %d...' %(UnitID, radius))
            arcpy.Clip_management (in_raster = rghnss, rectangle = rectangle ,out_raster = outRoughness, in_template_dataset = 'selectFC', maintain_clipping_extent = "NO_MAINTAIN_EXTENT", nodata_value = "NoData")
            r += 1
            #else: print('unit %s exists!' % UnitID)
    except:
    #      # Error handling code swiped from "A Python Primer for ArcGIS"
            print('                                                      Unit %s failed...' % UnitID)