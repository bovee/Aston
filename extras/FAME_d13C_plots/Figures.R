# Code to make nice plots of FAME C isotope data as exported from Aston
#
# Copyright Roderick Bovee 2013

# libraries needed to run this script
library(plyr)
library(ggplot2)

# isotopic value of the methanol we used (CHANGE THIS)
MeOH.d13C <- -39.0

# read in all the files
compounds <- read.csv('Compounds.csv')
samps <- read.csv('AstonSamples.csv')
stds <- read.csv('AllFAMEStds.csv')

# figure which compounds are which
# first make a function that converts a retention time to a compound name
rt.to.cmpd <- function(df) {
	lib.cmpd <- subset(compounds, df$Peak.Retention.Time..min. >= compounds$RT - compounds$RT.tol & df$Peak.Retention.Time..min. <= compounds$RT + compounds$RT.tol, select=c(Compound, Ncs))[1,]
	if(nrow(lib.cmpd) == 0) {lib.cmpd <- data.frame(Compound="", Ncs=0)}
	return(lib.cmpd)
}
# apply that function to all the samples
samps <- adply(samps, 1, rt.to.cmpd)

# filter out samples which don't have an identity
samps <- subset(samps, samps$Ncs != 0)

# filter out samples which are the wrong size
samps <- subset(samps, samps$Peak.Height <= 10000 & samps$Peak.Height >= 500)

# create a linear model of the standards
# this model can be changed to best reflect what's causing shifts in linearity
mod <- lm(Dd13C ~ Peak.Height + Peak.Width..min. * Ncs, data=stds)

# calculate the correct values for the samples using the model
samps <- cbind(samps, samps$X.13C.Value.... - predict(mod, samps, interval='predict'))

# correct for methanol in the FAMEs
samps$fit <- (samps$fit * (samps$Ncs + 1) - MeOH.d13C) / samps$Ncs
samps$lwr <- (samps$lwr * (samps$Ncs + 1) - MeOH.d13C) / samps$Ncs
samps$upr <- (samps$upr * (samps$Ncs + 1) - MeOH.d13C) / samps$Ncs

# compounds should be in the right order
# should really get this from the compounds file, but this works (kind of)
samps$Compound <- factor(samps$Compound, levels=c('C14:0', 'I-C15:0', 'A-C15:0', 'C16:1', 'I-C16:0', 'C16:0', 'C18:1W', 'C18:1', 'C18:0', 'C22:0', 'C24:0', 'C25:0'), ordered=TRUE)

# make a pretty plot using ggplot
print(ggplot(samps, aes(Compound, fit, color=Sample)) + geom_point(aes(size=Peak.Height)) + geom_errorbar(aes(ymin=lwr, ymax=upr)) + facet_grid(Fxn~ Sample) + opts(axis.text.x=theme_text(angle=90, hjust=1)))
