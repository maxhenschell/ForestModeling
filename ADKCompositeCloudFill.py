#!C:/Users/mxhensch/AppData/Local/Continuum/anaconda3/envs/arcgispro-py3 python
# -*- coding: utf-8 -*-
"""
Spyder Editor

This is an attempt to fill clouds in sentinel data
"""
#import ADKCompositeMasks

print("prepping...")
import arcpy, os, fnmatch, logging, glob
import numpy as np
#from decimal import Decimal
import datetime
from arcpy.sa import *
import matplotlib.pyplot as plt
arcpy.CheckOutExtension("Spatial")
arcpy.Delete_management("in_memory")  #Clear in_memory to avoid schema lock errors

#set some envs 
inDir = r"C:\Users\mxhensch\GIS_data\ForestModeling\Sentinel\ADK"
os.chdir(inDir)


clDate = "20170730"
cfData = "20180923"
tmpGDB = os.path.join(inDir,"tmp.gdb")
refRas = r"C:\Users\mxhensch\GIS_data\ForestModeling\Sentinel\ADK\20170730_B02.tif"#os.path.join(inDir,arcpy.ListRasters("JP2")[1])
resX = arcpy.GetRasterProperties_management(refRas, "CELLSIZEX")
res = resX.getOutput(0)
arcpy.env.outputCoordinateSystem = refRas
sr = arcpy.Describe(refRas)
sr = sr.SpatialReference
arcpy.env.cellSize = refRas
arcpy.env.nodata = "NoData"
#arcpy.env.outputCoordinateSystem = refRas
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.resamplingMethod = "BILINEAR"
arcpy.env.snapRaster = refRas
arcpy.env.overwriteOutput = True

#Start logging
lgFile = os.path.join(inDir,"CloudFill.log")
logging.basicConfig(filename=lgFile,level=logging.DEBUG)
#now = str(datetime.datetime.now())
#print(now)
logging.info("-----------Start: %s -----------"%str(datetime.datetime.now()))

#
#read in data
#
arcpy.env.workspace = inDir

#target images
inTar = glob.glob("*20180923*.tif")

#reference images
inRef = glob.glob("*20170730*.tif")

#
#calculate cloud and shadow masks 
#method from Jin et al 2016
#

#define bands
print("reading bands...")
#target bands
b2T= fnmatch.filter(inTar,"*B02.tif")[0]
b3T= fnmatch.filter(inTar,"*B03.tif")[0]
b4T= fnmatch.filter(inTar,"*B04.tif")[0]
b5T= fnmatch.filter(inTar,"*B05.tif")[0]
b6T= fnmatch.filter(inTar,"*B06.tif")[0]
b7T= fnmatch.filter(inTar,"*B07.tif")[0]
b8T= fnmatch.filter(inTar,"*B08.tif")[0]
b8AT = fnmatch.filter(inTar,"*B8A.tif")[0]
#b9T= fnmatch.filter(inTar,"*B09*")[0]
b11T= fnmatch.filter(inTar,"*B11.tif")[0]
b12T= fnmatch.filter(inTar,"*B12.tif")[0]

#reference bands
b2R= fnmatch.filter(inRef,"*B02.tif")[0]
b3R= fnmatch.filter(inRef,"*B03.tif")[0]
b4R= fnmatch.filter(inRef,"*B04.tif")[0]
b5R= fnmatch.filter(inRef,"*B05.tif")[0]
b6R= fnmatch.filter(inRef,"*B06.tif")[0]
b7R= fnmatch.filter(inRef,"*B07.tif")[0]
b8R= fnmatch.filter(inRef,"*B08.tif")[0]
b8AR = fnmatch.filter(inRef,"*B8A.tif")[0]
#b9R= fnmatch.filter(inRef,"*B09*")[0]
b11R= fnmatch.filter(inRef,"*B11.tif")[0]
b12R= fnmatch.filter(inRef,"*B12.tif")[0]

# TARGET masks
tarMask = os.path.join(tmpGDB, "tarMask")
if not arcpy.Exists(tarMask):
    print("calculating target cloud mask...")
    TcMask1 = float(arcpy.GetRasterProperties_management(b2T, "MEAN").getOutput(0)) + 1*float(arcpy.GetRasterProperties_management(b2T, "STD").getOutput(0))
    b2TR = Raster(b2T)-Raster(b2R)
    TcMask2 = float(arcpy.GetRasterProperties_management(b2TR, "MEAN").getOutput(0)) + 1*float(arcpy.GetRasterProperties_management(b2TR, "STD").getOutput(0))
    TcMask3 = float(arcpy.GetRasterProperties_management(b8T, "MEAN").getOutput(0))
    TcMask4 = float(arcpy.GetRasterProperties_management(b12T, "MEAN").getOutput(0))
    TcMask = Con(((Raster(b2T) > TcMask1) & (b2TR > TcMask2) & (Raster(b8T) > TcMask3) & (Raster(b12T) > TcMask4)),1,0)
    TcMask = SetNull(RegionGroup(in_raster = TcMask, number_neighbors = "FOUR"), TcMask, "COUNT < 4")
    TcMaskOut = os.path.join(tmpGDB, "TcMask"); TcMask.save(TcMaskOut)
    
    print("calculating target shadow mask...")
    TsMask1 = float(arcpy.GetRasterProperties_management(b11T, "MEAN").getOutput(0)) - 0.5*float(arcpy.GetRasterProperties_management(b11T, "STD").getOutput(0))
    b11TR = Raster(b11T)-Raster(b11R)
    TsMask2 = float(arcpy.GetRasterProperties_management(b11TR, "MEAN").getOutput(0)) - 1*float(arcpy.GetRasterProperties_management(b11TR, "STD").getOutput(0))
    TsMask3 = TcMask3
    TsMask = Con(((Raster(b11T) < TsMask1) & (b11TR < TsMask2) & (Raster(b8T) < TsMask3)),1,0)#TsMask = Shrink(in_raster = TsMask, number_cells = 2, zone_values = [1])
    TsMask = SetNull(RegionGroup(in_raster = TsMask, number_neighbors = "FOUR"), TsMask, "COUNT < 4")
    TsMaskOut = os.path.join(tmpGDB, "TsMask"); TsMask.save(TsMaskOut)
    print("joining masks...")
    print("...T1...")
    nullTC = SetNull(TcMask,TcMask,"Value = 0")
    print("...T2...")
    nullTS = SetNull(TsMask,TsMask,"Value = 0")
    print("...T3...")
    DistTC = EucDistance(in_source_data = nullTC, maximum_distance = 1200)
    print("...T4...")
    conTS = Con(in_conditional_raster = DistTC, in_true_raster_or_constant = nullTS, in_false_raster_or_constant = 0)    #nullTC = Con(IsNull(nullTC),0,nullTC)#conTS = Con(IsNull(conTS),0,conTS)
    print("...T5...")
    tMask = conTS+TcMask#
    print("...T6...")
    tMask = Con((~IsNull(tMask)),1)
    print("...T7...")
    tMask = Expand(in_raster = tMask, number_cells = 6, zone_values = [1])
    print("...T8...")
    tMask.save(tarMask)
    print("Target masks done!")
else: print("Target mask exists")

# REFERENCE masks
refMask = os.path.join(tmpGDB, "refMask")
if not arcpy.Exists(refMask):
    print("calculating reference cloud mask...")
    RcMask1 = float(arcpy.GetRasterProperties_management(b2R, "MEAN").getOutput(0)) + 1*float(arcpy.GetRasterProperties_management(b2R, "STD").getOutput(0))
    b2RT = Raster(b2R)-Raster(b2T)
    RcMask2 = float(arcpy.GetRasterProperties_management(b2RT, "MEAN").getOutput(0)) + 1*float(arcpy.GetRasterProperties_management(b2RT, "STD").getOutput(0))
    RcMask3 = float(arcpy.GetRasterProperties_management(b8R, "MEAN").getOutput(0))
    RcMask4 = float(arcpy.GetRasterProperties_management(b12R, "MEAN").getOutput(0))
    RcMask = Con(((Raster(b2R) > RcMask1) & (b2RT > RcMask2) & (Raster(b8R) > RcMask3) & (Raster(b12R) > RcMask4)),1,0)#RcMask = Shrink(in_raster = RcMask, number_cells = 1, zone_values = [1])
    #remove single pixels
    RcMask = SetNull(RegionGroup(in_raster = RcMask, number_neighbors = "FOUR"), RcMask, "COUNT < 4")
    RcMaskOut = os.path.join(tmpGDB, "RcMask"); RcMask.save(RcMaskOut)
    
    print("calculating reference shadow mask...")
    RsMask1 = float(arcpy.GetRasterProperties_management(b11R, "MEAN").getOutput(0)) - 0.5*float(arcpy.GetRasterProperties_management(b11R, "STD").getOutput(0))
    b11RT = Raster(b11R)-Raster(b11T)
    RsMask2 = float(arcpy.GetRasterProperties_management(b11RT, "MEAN").getOutput(0)) - 0.5*float(arcpy.GetRasterProperties_management(b11RT, "STD").getOutput(0))
    RsMask3 = RcMask3
    RsMask = Con(((Raster(b11R) < RsMask1) & (b11RT < RsMask2) & (Raster(b8R) < RsMask3)),1,0)#RsMask = Shrink(in_raster = RsMask, number_cells = 2, zone_values = [1])
    RsMask = SetNull(RegionGroup(in_raster = RsMask, number_neighbors = "FOUR"), RsMask, "COUNT < 4")
    RsMaskOut = os.path.join(tmpGDB, "RsMask"); RsMask.save(RsMaskOut)
    
    print("joining masks...")
    print("...T1...")
    nullRC = SetNull(RcMask,RcMask,"Value = 0")
    print("...T2...")
    nullRS = SetNull(RsMask,RsMask,"Value = 0")
    print("...T3...")
    DistRC = EucDistance(in_source_data = nullRC, maximum_distance = 1200)
    print("...T4...")
    conRS = Con(in_conditional_raster = DistRC, in_true_raster_or_constant = nullRS, in_false_raster_or_constant = 0)    #nullRC = Con(IsNull(nullRC),0,nullRC)#conRS = Con(IsNull(conRS),0,conRS)
    print("...T5...")
    RMask = conRS+RcMask#
    print("...T6...")
    RMask = Con((~IsNull(RMask)),1)
    print("...T7...")
    RMask = Expand(in_raster = RMask, number_cells = 6, zone_values = [1])
    print("...T8...")
    RMask.save(refMask)
    print("...T9...")
else: print("Reference mask exists")
arcpy.Delete_management("in_memory")  #Clear in_memory

print("Masks complete!")

#numpy arrays
refRas = arcpy.Raster(refRas)
LLC  = arcpy.Point(refRas.extent.XMin,refRas.extent.YMin)
#target mask array
csT = arcpy.RasterToNumPyArray(Raster(refMask), lower_left_corner = LLC ,nodata_to_value=0)
csT = csT.astype(bool)

#reference mask array
csR = arcpy.RasterToNumPyArray(Raster(tarMask), lower_left_corner = LLC ,nodata_to_value=0)
csR = csR.astype(bool)

#bands to process
tbands = [b2R,b3R,b4R]
rbands = [b2T,b3T,b4T]

for t in range(0,len(tbands)):
    tbb = tbands[t]
    rbb = rbands[t]
    nms = tbb[9:12]
    logging.info("----------- Start band %s: %s -----------"%(nms,str(datetime.datetime.now())))
    print("----------- Start band %s: %s -----------"%(nms,str(datetime.datetime.now())))
    tr = arcpy.RasterToNumPyArray(in_raster=tbb,lower_left_corner = LLC, nodata_to_value = 0) #unmasked target
    rr = arcpy.RasterToNumPyArray(in_raster=rbb,lower_left_corner = LLC, nodata_to_value = 0) # unmasked reference
    trOut = tr#np.empty(tr.shape, dtype=int)#tar #copy as the fill target
    trM = tr*~csT #cloud/shadow-masked target
    rrM = rr*~csR #cloud/shadow-masked reference
    rrM2 = rrM*csT # mask of reference, only locations with clouds in target
    rrMU = np.trim_zeros(np.unique(np.array(rrM2))) # get  unique reference raster values within target cloud mask
    trOut = tr#np.empty(tr.shape, dtype=int)#tar #copy as the fill target
    #sceneSD = np.std(rrM)
    for p in rrMU:  
        if p % 100 == 0:
            print(p)
        SSG = ((rrM<=(p+1)) & (rrM>=(p-1)))#mask of locations +/- 1SD of reference. 0 where values are not in range, 1 where they are
        #tt = trM*(((rrM<=(p+1)) & (rrM>=(p-1))).astype(int))#mask of locations +/- 1 of reference. 0 where values are not in range, 1 where they are
        SSG = SSG.astype(int)
        tt = trM*SSG  
        if np.isnan(np.mean(tt[tt != 0])):
            fillVal = -9999
        else:
            fillVal = int(round(np.mean(tt[tt != 0]))) 
        trOut[(rrM2 == p)] = fillVal

        logging.info("unique value %d; SSG size: %d; fill value: %d" %(p, np.sum(SSG),fillVal))
    out = arcpy.NumPyArrayToRaster(in_array = trOut, lower_left_corner = LLC, x_cell_size = int(res), y_cell_size = int(res), value_to_nodata = -9999)
    outRas = os.path.join(inDir,nms+"_filled.tif")
    out.save(outRas)
    logging.info("----------- End band %s: %s -----------"%(nms,str(datetime.datetime.now())))
    print("----------- End band %s: %s -----------"%(nms,str(datetime.datetime.now())))
logging.info("----------- End -----------")