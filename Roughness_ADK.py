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

# Import required modules
import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
import os # provides access to operating system functionality such as file and directory paths
#import sys # provides access to Python system functions
#import traceback # used for error handling
#import gc # garbage collection
from datetime import datetime # for time-stamping

#set arc env values
arcpy.env.overwriteOutput = True
arcpy.env.nodata = "None"
arcpy.CheckOutExtension("Spatial")
arcpy.env.workspace = r"H:/GIS_data/ForestModeling/ADK/DEM/"
arcpy.Delete_management("in_memory")
FailList = list() # List to keep track of units where processing failed

#Directories
root = r'C:/Users/mxhensch/GIS_data/ForestModeling/'
ADK = os.path.join(root,"ADK/")
outDir = os.path.join(ADK, "FINAL/")
clip = os.path.join(ADK,"ADK_buffer.shp")
arcpy.env.extent = clip
outSamp = "in_memory/Outsamp"
WGS = arcpy.SpatialReference(os.path.join(ADK+"WGS_1984.prj"))

#get master raster 
SenMaster = os.path.join(outDir,"0730_B02.tif")
arcpy.env.outputCoordinateSystem = WGS
arcpy.env.snapRaster = SenMaster
resX = arcpy.GetRasterProperties_management(SenMaster, "CELLSIZEX")
resY = arcpy.GetRasterProperties_management(SenMaster, "CELLSIZEY")
#if resX.getOutput(0) == resY.getOutput(0):
res = resX.getOutput(0)
#else: res = resX.getOutput(0) +" "+ resY.getOutput(0) 
arcpy.env.cellSize = os.path.join(outDir,"0730_B02.tif")
CellSize = float(res)#arcpy.env.cellSize

# Script arguments
inDEM = os.path.join(ADK,"ADK_DEM_resamp.tif")

# print("Registering DEM...")
# arcpy.RegisterRaster_management (in_raster = Input_DEM, register_mode = "REGISTER", reference_raster = SenMaster)

#print("Resampling DEM...")
#arcpy.Resample_management(in_raster = Input_DEM,out_raster = outSamp, cell_size = res, resampling_type = "BILINEAR")
Z_factor = "1"

inProcUnits = os.path.join(ADK,"ADK_Quads.shp")#arcpy.GetParameterAsText(1) # Polygon feature class determining units to be processed
   # Default : N:\SDM\ProcessedData\SDM_ReferenceLayers.gdb\fc_ned_1arcsec_g
   
inFld = "PREFIX"#arcpy.GetParameterAsText(2) # Field containing the unit ID
   # Default: FILE_ID
  
R1 = 1#arcpy.GetParameter(3) # Radius 1 (in raster cells)
   # Default:  1
   
R2 = 10#arcpy.GetParameter(4) # Radius 2 (in raster cells)
   # Default: 10
   
R3 = 100#arcpy.GetParameter(5) # Radius 3 (in raster cells)   
   # Default: 100
   
outGDB1 = os.path.join(ADK,"ADKR1.gdb")#arcpy.GetParameterAsText(6) # Geodatabase to hold final products for neighborhood 1
outGDB2 = os.path.join(ADK,"ADKR10.gdb")#arcpy.GetParameterAsText(7) # Geodatabase to hold final products for neighborhood 2
outGDB3 = os.path.join(ADK,"ADKR100.gdb")#arcpy.GetParameterAsText(8) # Geodatabase to hold final products for neighborhood 3
scratchGDB = os.path.join(ADK,"ADKScratch.gdb")#arcpy.GetParameterAsText(9) # Geodatabase to hold intermediate products
ProcLogFile = os.path.join(ADK,"ADKRoughLog.txt")#arcpy.GetParameterAsText(10) # Text file to contain processing results

maxRad = max(R1, R2, R3)

# Create and open a log file.
# If this log file already exists, it will be overwritten.  If it does not exist, it will be created.
Log = open(ProcLogFile, 'w+') 
FORMAT = '%Y-%m-%d %H:%M:%S'
timestamp = datetime.now().strftime(FORMAT)
Log.write("Process logging started %s \n" % timestamp)

ProcUnits = arcpy.da.SearchCursor(inProcUnits, [inFld])
Unit = ProcUnits.next()
for Unit in ProcUnits:
    try:
        UnitID = Unit[0]
        print('Working on unit %s...' % UnitID)
    
    # Make a feature class with the single unit's shape, then buffer it
        print('Selecting feature...')
        where_clause = "%s = '%s'" % (inFld, UnitID) # Create the feature selection expression
        arcpy.MakeFeatureLayer_management (inProcUnits, 'selectFC', where_clause) 
      
        print('Buffering feature...')
        buffFC = "in_memory/buffFC"#scratchGDB + os.sep + 'buffFC' + UnitID
        buffDist = CellSize*maxRad*2
        arcpy.Buffer_analysis('selectFC', buffFC, buffDist)
        # Specify output
        gdb = outGDB3#item[1]
        r = 1
        outRoughness = gdb + os.sep + "rough_" + UnitID + "_" + str(r)
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
        arcpy.Clip_management (in_raster = inDEM, out_raster = clipDEM, rectangle = rectangle, in_template_dataset = buffFC, maintain_clipping_extent = "NO_MAINTAIN_EXTENT", nodata_value = "NoData")
       # arcpy.Clip_management (in_raster = rghnss, out_raster = outRoughness, in_template_dataset = 'selectFC', maintain_clipping_extent = "NO_MAINTAIN_EXTENT", clipping_geometry = "ClippingGeometry", nodata_value = "NoData")
        
        # Set processing mask
        arcpy.env.mask = clipDEM 
        
        # Loop through the focal statistics process for each radius
        r = 1
        #for item in ((R3, outGDB3)):#(R1, outGDB1), (R2, outGDB2), (R3, outGDB3)):
        #   Define neighborhood
        radius = R3#item[0]
        if radius == 1:
            nghbrhd = NbrRectangle(3, 3, "CELL")
        else:
            nghbrhd = NbrCircle(radius, "CELL")
    
        
     
        # Run focal statistics
        print('Calculating roughness for radius %s...' % r)
        rghnss = FocalStatistics(in_raster = clipDEM, neighborhood = nghbrhd, statistics_type = "STD", ignore_nodata = "DATA")
     
        # Clip to original unit shape
        extent = arcpy.Describe('selectFC').extent
        XMin = extent.XMin
        YMin = extent.YMin
        XMax = extent.XMax
        YMax = extent.YMax
        rectangle = '%s %s %s %s' %(XMin, YMin, XMax, YMax) 
        print('Clipping output for radius %s...' % r)
        arcpy.Clip_management (in_raster = rghnss, rectangle = rectangle ,out_raster = outRoughness, in_template_dataset = 'selectFC', maintain_clipping_extent = "NO_MAINTAIN_EXTENT", nodata_value = "NoData")
         #r += 1
        #else: print('unit %s exists!' % UnitID)
    except:
    #      # Error handling code swiped from "A Python Primer for ArcGIS"
            print('                                                      Unit %s failed...' % UnitID)
        
#      tb = sys.exc_info()[2]
#      tbinfo = traceback.format_tb(tb)[0]
#      pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n " + str(sys.exc_info()[1])
#      msgs = "ARCPY ERRORS:\n" + arcpy.GetMessages(2) + "\n"
#
#      arcpy.AddWarning('Unable to process unit %s' % UnitID)
#      FailList.append(UnitID)
#      arcpy.AddWarning(msgs)
#      arcpy.AddWarning(pymsg)
#      print((arcpy.GetMessages(1))
      
## List the units where processing failed
#if FailList:
#   msg = '\nProcessing failed for some units: \n'
#   Log.write(msg)
#   print('%s See the processing log, %s' % (msg, ProcLogFile))
#   for unit in FailList:
#      Log.write('\n   -%s' % unit)
#      print(unit) 
#      
#timestamp = datetime.now().strftime(FORMAT)
#Log.write("\nProcess logging ended %s" % timestamp)   
#Log.close()



















