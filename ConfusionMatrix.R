require(tidyverse)
require(raster)
require(sp)
require(rgdal)
require(rgeos)
library(classInt)
library(BAMMtools)
require(openxlsx)
require(janitor)
detach()
rootDir = 'H:/GIS_data/ForestModeling/'
RDdir = 'W:/Projects/Lands&Forests/Forest Preserves/SSP/adk/SecondRun_rdata'
RDfiles = data.frame(file = unlist(list.files(RDdir, pattern = '*5_fold*')))
spp = separate(RDfiles,file , c("Species", NA),sep = '_', extra = "drop") %>% separate(Species, c("Species", NA),sep = 'id', extra = "drop")
spp = as.vector(spp[,1]) ##NOTE CHANGED
FP = 'ADK'; FPdir = paste0(rootDir,FP)
rasDir = paste0(FPdir,'/models')

#Con in R
Con=function(condition, trueValue, falseValue){
  return(condition * trueValue + (!condition)*falseValue)
}

Preserve = readOGR(dsn = paste0(FPdir), layer = FP)
Random = spsample(Preserve,n=1000,"random")
#plot(Random, add = TRUE)
water = raster(paste0(FPdir,'/',FP,'_MajorWaterbodies.tif'))#; NAvalue(water) <- 0
#plot(water)
sp = spp[1]
i = 1
for(sp in spp){
  cat(sp)
  
  #
  #get Rdata
  outBook = paste0(sp,"_Summary.xlsx")
  rf = RDfiles[grep(sp, RDfiles$file),]
  attach(paste0(RDdir,'/',rf))
  cut = maxSSS
  lst = list()
  lst[[1]] = allThresh
  lst[[2]] = EnvVars[order(EnvVars$impVal, decreasing = TRUE), c(1:2)] 
  lst[[3]] = summ.table
  detach()
  
  #
  #read rasters
  rasNHP = raster(list.files(rasDir, pattern = paste0("*",sp,"_",FP,"_NHP.tif$"), full.names = TRUE))
  #plot(rasNHP); plot(Random, add = TRUE); plot(Preserve, add=TRUE); plot(water, add = TRUE)
  rasFS = raster(list.files(rasDir, pattern = paste0("*",sp,"_",FP,"_FS.tif$"), full.names = TRUE))
  #plot(rasFS); plot(Random, add = TRUE); plot(Preserve, add=TRUE)
  
  #
  #remove water values from NHP; convert to binary
  
  #plot(NHPwater)
  NHPbin = Con(rasNHP>cut, 1,0)
  NHPbin = Con(is.na(water), NHPbin,0)
  plot(NHPbin)
  
  #
  #reclassify FS raster 
  fsClass = classIntervals(values(rasFS), n = 5, style = "kmeans")
  fsReclass = data.frame("from" = fsClass$brks[c(1:5)], "to" = fsClass$brks[c(2:6)], "becomes" = seq(1:5))# matrix(nrow = length(fsClass$brks), ncol = 3))
  
  FSrcl = reclassify(x=rasFS, rcl=fsReclass)
  #OR reclassify to binary
  FSbin0 = Con(rasFS > 0, 1,0)
  FSbin1 = Con(rasFS > 1, 1,0)
  #plot(rclFS)
  
  #
  #get tables, write to excel
  lst[[4]] = janitor::tabyl(data.frame('NHPbin' = raster::extract(NHPbin, Random), 'FSbin0' = raster::extract(FSbin0, Random)), FSbin0, NHPbin)
  lst[[5]] = janitor::tabyl(data.frame('NHPbin' = raster::extract(NHPbin, Random), 'FSbin1' = raster::extract(FSbin1, Random)), FSbin1, NHPbin)
  lst[[6]] = janitor::tabyl(data.frame('NHPbin' = raster::extract(NHPbin, Random), 'FSrcl' = raster::extract(FSrcl, Random)), FSrcl, NHPbin)
  lst[[7]] = fsReclass
  write.xlsx(lst, outBook, sheetName = c("allTresh", "EnvVars", "SummaryTable", "FSbin0", "FSbin1", "FSrcl", "FSbreaks"))
  }