#!C:/Users/mxhensch/AppData/Local/Continuum/anaconda3/envs/arcgispro-py3 python
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 14:48:23 2018

@author: mxhensch

Get txt with footprints here: https://viewer.nationalmap.gov/basic/
"""

import sys
#import time
import urllib.request, urllib.parse, urllib.error
import os
#from urllib.parse import urljoin
#from pathlib import Path
import arcpy 
from arcpy.sa import *
import zipfile
import glob

# set in folder
root = r'C:\Users\mxhensch\GIS_data'
ADK = os.path.join(root,"ADK")
DEM = os.path.join(ADK,"DEM")
GRD = os.path.join(ADK,"GRD")
outDir = DEM#os.path.join("H:/GIS_data/ForestModeling/Catskills/DEM/")
arcpy.env.overwriteOutput = True
arcpy.env.snapRaster = r"H:\GIS_data\ForestModeling\ADK\modelData\Filled_L2A_20170730_B02.tif"

#slices
def left(s, amount):
    return s[:amount]
def right(s, amount):
    return s[-amount:]
def mid(s, offset, amount):
    return s[offset:offset+amount]

clip = os.path.join(ADK,"ADK_1km.shp")
#arcpy.env.extent = clip
WGS = arcpy.SpatialReference(os.path.join(ADK,"WGS_1984.prj"))
NAD = arcpy.SpatialReference(os.path.join(ADK,"NAD_1983_UTM_Zone_18N.prj"))

arcpy.env.workspace = os.path.join(DEM)
fp = os.path.join(DEM,'DEM.txt')

#Progress bar for download
def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*d / %d" % (
            percent, len(str(totalsize)), readsofar, totalsize)
        sys.stderr.write(s)
        if readsofar >= totalsize: # near the end
            sys.stderr.write("\n")
    else: # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))
#download saver
def save(url, filename):
    urllib.request.urlretrieve(url, filename, reporthook)
    
#Download footprints
DOWNLOADS_DIR = DEM#os.path.join(ldr,'footprints/'+nm)
if not os.path.exists(DOWNLOADS_DIR):
    os.mkdir(DOWNLOADS_DIR)

lines = open(fp).read().splitlines()
print("number of footprints to download: %d "%len(lines))
for ur in lines:
    # Split on the rightmost / and take everything on the right side of that
    name = ur.rsplit('/', 1)[-1]
    #print(name)
    # Combine the name and the downloads directory to get the local filename
    fil = os.path.join(DOWNLOADS_DIR, name)
    if not os.path.exists(fil):
        save(ur, fil)
    else: print("%s exists"%name)

#unzip

os.chdir(DEM)
for file in glob.glob("*.zip"):
    print(file)
    with zipfile.ZipFile(file,"r") as zip_ref:
        zip_ref.extractall(GRD)

# get tiles
arcpy.env.workspace = GRD
inRas = arcpy.ListRasters("*","GRID")

inRas = [os.path.join(arcpy.env.workspace, f) for f in inRas]
Ras = ';'.join(inRas)
bands = arcpy.GetRasterProperties_management (inRas[0], "BANDCOUNT")
mos = "in_memory/ras"
rproj = "in_memory/rproj"
outClip = "in_memory/clp"
outFinal = os.path.join(outDir,"ADK_DEM.tif")
arcpy.MosaicToNewRaster_management(input_rasters = Ras,output_location = "in_memory/",raster_dataset_name_with_extension = "ras",pixel_type = "32_BIT_FLOAT",mosaic_method = "MEAN", coordinate_system_for_the_raster = WGS, number_of_bands = bands)
arcpy.ProjectRaster_management (mos, out_raster = rproj, out_coor_system = NAD, resampling_type = "BILINEAR", cell_size = "20", geographic_transform = "NAD_1983_To_WGS_1984_5", in_coor_system = WGS)
arcpy.Clip_management(in_raster = rproj, out_raster = outClip, in_template_dataset = clip, maintain_clipping_extent = "NO_MAINTAIN_EXTENT", nodata_value = "NoData")
arcpy.CopyRaster_management(outClip, outFinal) 
arcpy.Delete_management("in_memory") 
