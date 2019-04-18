#Get TSS

rootDir = 'H:/GIS_data/ForestModeling/'
RDdir = 'W:/Projects/Lands&Forests/Forest Preserves/SSP/adk/SecondRun_rdata'
RDfiles = data.frame(file = unlist(list.files(RDdir))); RDfiles = as.vector(RDfiles[,1])
TSS = data.frame("File" = RDfiles, "TSS" = rep(0,length(RDfiles)), "MTP" = rep(0,length(RDfiles)), "maxSSS" = rep(0,length(RDfiles)))

f = 1
for(f in 1:length(RDfiles)){
  attach(paste0(RDdir,'/',RDfiles[f]))
  TSS[f,c(2:4)] = c(tss.summ[,1], MTP, maxSSS)
    
  detach()
}

write.csv(TSS, "TSS.csv", row.names = FALSE)