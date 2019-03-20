# ----------------------------------------------------------------------------------------
# BatchSolarRad.py
# Version:  Python 2.7.5
# Creation Date: 2015-04-06
# Last Edit: 2016-05-17
# Creator:  Kirsten R. Hazler and Roy Gilb
#
# Summary:
#     Derives solar radiation from a DEM, for a specified set of footprints polygons.
#     These polygons should already be in the desired format and projected coordinate 
#     system to match the DEM.
#
# Usage Tips:
#
# Syntax:
# ----------------------------------------------------------------------------------------

# Import required modules
import arcpy
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
import os # provides access to operating system funtionality such as file and directory paths
import sys # provides access to Python system functions
import traceback # used for error handling
from datetime import datetime # for time-stamping

# set in folder
root = r'C:/Users/mxhensch/GIS_data/ForestModeling/'
inDir = os.path.join(root,"ADK/ADKSolRad/")
arcpy.env.workspace = inDir
# set out folder
outDir = inDir#os.path.join(root,"ADK/FINAL")
arcpy.Delete_management("in_memory")  #Clear in_memory to avoid schema lock errors

#Set env
#WGS = arcpy.SpatialReference("WGS_1984.prj")
#UTM18 = outDir+"NAD_1983_UTM_Zone_18N.prj"
#clip = os.path.join(root+"ADK_buffer.shp")
#arcpy.env.extent = clip
arcpy.env.overwriteOutput = True

##get master raster 
#SenMaster = os.path.join(outDir,"FINAL/0730_B02.tif")
##arcpy.env.outputCoordinateSystem = WGS
#arcpy.env.snapRaster = SenMaster
#resX = arcpy.GetRasterProperties_management(SenMaster, "CELLSIZEX")
#resY = arcpy.GetRasterProperties_management(SenMaster, "CELLSIZEY")
#if resX.getOutput(0) == resY.getOutput(0):
#    res = resX.getOutput(0)
#else: res = resX.getOutput(0) +" "+ resY.getOutput(0) 
#arcpy.env.cellSize = SenMaster#os.path.join(outDir,"0730_B02.tif")
#res = arcpy.env.cellSize

# Script arguments to be input by user
in_DEM = os.path.join(inDir,"ADKSolRadDEM.tif")#arcpy.GetParameterAsText(0) # Input digital elevation model
z_factor = 1#arcpy.GetParameter(1) # The number of ground x,y units in one surface z unit.
   # Default:  1
in_Tiles = os.path.join(inDir,"ADKStrips.shp")#arcpy.GetParameterAsText(2) 
   # Polygon feature class outlining footprints of tiles to be processed
   # Recommend using footprints covering narrow strips of constant latitude; can be long east-west
fld_ID = "Id"#arcpy.GetParameterAsText(3)
   # A field to use as unique ID for each tile
out_GDB1 = os.path.join(outDir,"ADKWinter.gdb")#arcpy.GetParameterAsText(4) # File geodatabases to store the output solar radiation tiles - one per band
out_GDB2 = os.path.join(outDir,"ADKEqnx.gdb")#arcpy.GetParameterAsText(5)
out_GDB3 = os.path.join(outDir,"ADKSummer.gdb")#arcpy.GetParameterAsText(6)
#scratch_GDB = arcpy.GetParameterAsText(7)
ProcLog = os.path.join(outDir,"ADKSRlog.txt")#arcpy.GetParameterAsText(7) # Text file to record processing record
DEMRast = Raster(in_DEM)

# Hard-coded parameters required by Area Solar Radiation tool

# in_surface_raster 
   # Not needed here; use raster extracted in loop
latitude = '' 
   # No value given, so the average latitude for the extracted raster will be usedarea
sky_size = 200 
   # Square side length, in cells, for the viewshed, sky map, and sun map grids
time_configuration = 'TimeSpecialDays()' 
   # Specifies the time configuration (period) used for calculating solar radiation.
day_interval = ''
   # Use default
hour_interval = ''
   # Use default
each_interval = 'INTERVAL'
   # For a whole year with monthly intervals, results in 12 output radiation values for each location. 
# z_factor
   # Not needed here; entered by user
slope_aspect_input_type = 'FROM_DEM'
   # The slope and aspect grids are calculated from the input surface raster. 
calculation_directions = 32
   # Number of azimuth directions used when calculating the viewshed.  Default is 32.
zenith_divisions = 16
   # Number of divisions, relative to zenith, used to create sky sectors in the sky map.  Default is 8.
azimuth_divisions = 16
   # Number of divisions, relative to north, used to create sky sectors in the sky map.  Default is 8.
diffuse_model_type = 'UNIFORM_SKY'
   # Uniform diffuse model. The incoming diffuse radiation is the same from all sky directions. 
diffuse_proportion = 0.3 
   # This is the default value for generally clear sky conditions.
transmittivity = 0.5 
   # This is the default for a generally clear sky.
# out_direct_radiation_raster
   # Not needed here; use raster naming convention in loop
# out_diffuse_radiation_raster
   # Not needed here; use raster naming convention in loop
# out_direct_duration_raster
   # Not needed here; use raster naming convention in loop

   
#Extract strip number from in_Tiles fro creating unique scratch and current workspaces
stripPath = in_Tiles
stripFile = os.path.basename(stripPath)
stripNo = stripFile.replace('ADKStrips', '')
outPath = inDir#r'C:\Users\mxhensch\GIS_data\ForestModeling\ADK'#"E:\Defaults"
currName = 'SolRadGrp' + stripNo    #Create temporary, unique GDBs for current and scratch
scrName = 'ScrSolarRadGrp' + stripNo   #

currGDB = arcpy.CreateFileGDB_management(outPath, currName)
scrGDB = arcpy.CreateFileGDB_management(outPath, scrName)

# Geoprocessing environment settings
#arcpy.env.snapRaster = DEMRast # Set the snap raster for alignment of outputs
arcpy.env.overwriteOutput = True # Set overwrite option so that existing data may be overwritten
arcpy.Delete_management("in_memory")  #Clear in_memory to avoid schema lock errors
arcpy.env.workspace = str(currGDB)
arcpy.env.scratchWorkspace = str(scrGDB)

#scratch = scratch_GDB
#scratch = arcpy.env.scratchGDB # Scratch workspace (default)



# Initialize a list for processing records, and start processing log
Log = open(ProcLog, 'w+') 
timeStamp = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
Log.write('Solar radiation processing started %s.\n' % timeStamp)

#Inform the user on the value of each input and output
Log.write('The input DEM is: ' + in_DEM)
Log.write('\nThe input Z-factor is: ' + str(z_factor))  
Log.write('\nThe input Latitude strip feature class is: ' + in_Tiles)    
Log.write('\nThe input ID field for the latitude strips is: ' + fld_ID)
Log.write('\nThe output GDB for the winter files is: ' + out_GDB1)
Log.write('\nThe output GDB for the equinox files is: ' + out_GDB2)
Log.write('\nThe output GDB for the summer files is: ' + out_GDB3)
Log.write('\nThe temporary default GDB for the intermediate files is: ' + str(currGDB))
### Add records of tool parameters to the log, here
Log.close()

myProcList = [] # Empty list to keep track of features processed.
listCount = -1
Footprints = arcpy.da.SearchCursor(in_Tiles, [fld_ID, "SHAPE@"]) ### Set up the search cursor from in_Tiles here.
#fp = Footprints.next()
with Footprints as cursor:
   for fp in Footprints:
      try:
         listCount = listCount + 1
         fp_ID = str(fp[0])
         fp_geom = fp[1]
         mem = 'in_memory'
         print('Working on tile %s...' % fp_ID)
         
         # Make a temp feature class from the single footprint - save to in_memory
         fprint = mem + os.sep + 'tile'
         arcpy.FeatureClassToFeatureClass_conversion(fp_geom, mem, 'tile')
     
         # Buffer the footprint by the sky_size - save in in_memory
         buff_fp = mem + os.sep + 'buffertile'
         arcpy.Buffer_analysis(fprint, buff_fp, sky_size)
         
         # Extract the DEM for the buffered footprint - save to memory (change to scratch if it crashes)     
         subset_DEM = mem + os.sep + 'clipDEM' #+fp_ID      --> Possible change this if we want to keep the buffers
         arcpy.Clip_management(DEMRast, "#", subset_DEM, buff_fp, "", "ClippingGeometry")
    
         # Run solar radiation - save to mem (change to scratch if it crashes)
         solarRad_Buff = AreaSolarRadiation(subset_DEM, '', sky_size, time_configuration, day_interval, hour_interval, each_interval, z_factor, slope_aspect_input_type, calculation_directions, zenith_divisions, azimuth_divisions, diffuse_model_type, diffuse_proportion, transmittivity, '', '', '')
         
         # Clip output solar radiation rasters to original footprint - save to memory 
         #solarRad_Clip = mem + os.sep + 'solarR' # + fp_ID
         #arcpy.Clip_management(solarRad_Buff, "#", solarRad_Clip, fprint, "", "ClippingGeometry")
         
         #Extract each individual band and save them to the output GDBs using nametags and tile ID --> w = winter solstice, e = equinox, s = summer solstice
         band1 = out_GDB1 + os.sep + 'solRad_w' + fp_ID
         band2 = out_GDB2 + os.sep + 'solRad_e' + fp_ID
         band3 = out_GDB3 + os.sep + 'solRad_s' + fp_ID
         arcpy.MakeRasterLayer_management(solarRad_Buff, band1, '', '', '1')
         arcpy.MakeRasterLayer_management(solarRad_Buff, band2, '', '', '2')
         arcpy.MakeRasterLayer_management(solarRad_Buff, band3, '', '', '3')
         
         #Save the temporary layers to rasters
         (Raster(band1)).save(band1)
         (Raster(band2)).save(band2)
         (Raster(band3)).save(band3)   
         
         #Delete intermediate scratch or memory data if necessary  
         arcpy.Delete_management("in_memory")

         Log = open(ProcLog, 'a+')
         print('Successfully processed tile %s' % fp_ID)
         myProcList.append('\nSuccessfully processed tile %s' % fp_ID)
         
         Log.write(myProcList[listCount])    
         
         
      except:
         print('Failed to process %s' % fp_ID)
         myProcList.append('\nFailed to process %s' % fp_ID)
         Log = open(ProcLog, 'a+')
         Log.write(myProcList[listCount])    
         # Error handling code swiped from "A Python Primer for ArcGIS"
         tb = sys.exc_info()[2]
         tbinfo = traceback.format_tb(tb)[0]
         pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n " + str(sys.exc_info()[1])
         msgs = "ARCPY ERRORS:\n" + arcpy.GetMessages(2) + "\n"

         arcpy.AddWarning(msgs)
         arcpy.AddWarning(pymsg)
         print(arcpy.GetMessages(1))
      
      
# Write processing results to a log file.
# If this log file already exists, it will be overwritten.  If it does not exist, it will be created
Log = open(ProcLog, 'a+')
timeStamp = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
Log.write('\nSolar radiation processing completed %s. Results shown above.\n' % timeStamp)
Log.close()
print('Processing results can be viewed in %s' % ProcLog)

#Delete temp current and scratch GDBs
#arcpy.Delete_management(str(currGDB))         
#arcpy.Delete_management(str(scrGDB))   
















