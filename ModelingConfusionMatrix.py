# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 14:40:49 2019

@author: mxhensch
"""

import arcpy 
from arcpy.sa import *
import os

arcpy.Delete_management("in_memory")
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension('3D')
arcpy.CheckOutExtension('Spatial')
rt = r'H:/GIS_data/ForestModeling'
FP = 'ADK'
out = os.path.join(rt,FP)


#get clip boundaries
buffer = os.path.join(rt,FP,FP+'_1km.shp')
clip = os.path.join(rt,FP,FP+'.shp')
arcpy.env.mask = clip
gdb = r'H:/GIS_data/ForestModeling/ForestModelling.gdb'
water = os.path.join(gdb,'ADK_MajorWaterBodies_Clip')
pts = os.path.join(gdb,'ADK_1k')
numberZones = 5
baseOutputZone = 1

#get FS raster list
rasDir = os.path.join(rt,FP+"\models")
arcpy.env.workspace = rasDir
fsRasters = sorted(arcpy.ListRasters("*FS.tif"))
#get NHP raster list
nhpRasters = sorted(arcpy.ListRasters("*NHP.tif"))
if FP == 'ADK':
    SSS = [0.13,0.10,0.05,0.01,0.01,0.09,0.05,0.08]
else: SSS = [0.46,0.44,0.46]
len(fsRasters) == len(nhpRasters)
f = fsRasters[0]; n = nhpRasters[0]; m = SSS[0]

#loop through rasters
for (f,n,m) in zip(fsRasters, nhpRasters, SSS):
    if f.split('_')[0] == n.split('_')[0]:
        nm = f.split('_')[0]
        print('Processing {}...'.format(nm))
        # water to 0 for NHP
        nhpBin = Con(Raster(n) > m, 1, 0)
        waterNHP = Con(IsNull(Raster(water)),nhpBin,0)
        #reclass FS
        FSslice = "in_memory/FSslice"
        arcpy.Slice_3d(f, FSslice, numberZones, "NATURAL_BREAKS", baseOutputZone)
        outTable = os.path.join(out,nm+"_Zonal"+FP+"_FS.dbf")
        outZSaT = ZonalStatisticsAsTable(FSslice, "VALUE", f, outTable, "NODATA", "MIN_MAX")
        
        inRasterList = [[FSslice, nm+"_FS"], [waterNHP, nm+"_NHP"]]
        ExtractMultiValuesToPoints(in_point_features = pts, in_rasters = inRasterList)
    
        arcpy.Delete_management("in_memory")
    else: print("Species {} and {} don't match".format(f.split('_')[0],n.split('_')[0]))