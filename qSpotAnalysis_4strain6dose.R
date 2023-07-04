# qSpotAnalysis_4strain6dose.R
# Kento Yanagisawa 
# This script is for the analysis of semi-quantitative spot-test(4*6 matrix)

# make these packages and their associated functions 
# available to use in this script
library("tikzDevice")
library("dplyr")
library("ggplot2")
library("RColorBrewer")
library("tidyverse")

# clear R's brain
rm(list = ls())

colsBlack = brewer.pal(6, "Greys")
colsOrange = brewer.pal(6, "Oranges")
colsBlue = brewer.pal(6, "Blues")
colsPurple = brewer.pal(5, "Purples")

# set working directory
# setwd()

# read dataset
exp_list <- rep(list.files(path = "./raw"), each = 16*24)
csv_list <- list.files(path = "./raw", recursive=T, pattern = "*.csv", full.names = T)
raw_csv <- do.call(rbind, lapply(csv_list, function(x) read.csv(x, header=TRUE)))
raw_csv <- mutate(raw_csv, exp_ID = exp_list)
raw_csv <- separate(raw_csv, Image, c("exp_condition", "suspension", "dose", "unit", "photo_ID"), sep="_")
raw_csv <- mutate(raw_csv, dose = as.numeric(dose))
raw_csv <- mutate(raw_csv, suspension = as.numeric(suspension))

# calculate mean of each duplicate spot
raw_csv_summarize <- raw_csv %>%
  group_by(suspension, dose, row, column, exp_ID) %>%
  summarize(Colony_mean = mean(Colony, na.rm = TRUE))
raw_csv_summarize <- mutate(raw_csv_summarize, Colony_mean = round(Colony_mean, digit = 2))
raw_csv_summarize <- arrange(raw_csv_summarize, suspension, row, column, exp_ID)

# get control value
raw_csv_control <- filter(raw_csv_summarize, dose == 0)
raw_csv_control_input <- NULL
for (i in 1:4){
  raw_csv_control_input <- rbind(raw_csv_control_input, raw_csv_control)
}
raw_csv_control_input <- arrange(raw_csv_control_input, suspension, row, column, exp_ID)

# bind control value
raw_csv_summarize <- cbind(raw_csv_summarize, raw_csv_control_input)

# check bind correctly
raw_csv_summarize <- mutate(raw_csv_summarize, CHK1 = 
                        ifelse(raw_csv_summarize$suspension...1 != raw_csv_summarize$suspension...7, 1, 
                        ifelse(raw_csv_summarize$row...3 != raw_csv_summarize$row...9, 1,
                        ifelse(raw_csv_summarize$column...4 != raw_csv_summarize$column...10, 1,
                        ifelse(raw_csv_summarize$exp_ID...5 != raw_csv_summarize$exp_ID...11, 1,
                        0
                        )))))
stopifnot(sum(raw_csv_summarize$CHK1) == 0)

# calculate ratio of Colony_mean to Control
# raw_csv_summarize <- filter(raw_csv_summarize, Colony_mean...12 != 0)
expData_raw <- data.frame(
  exp_ID = raw_csv_summarize$exp_ID...5,
  suspention = raw_csv_summarize$suspension...1,
  dose = raw_csv_summarize$dose...2,
  strain = raw_csv_summarize$row...3,
  column = raw_csv_summarize$column...4,
  spot_ratio = raw_csv_summarize$Colony_mean...6 / raw_csv_summarize$Colony_mean...12
)
expData_raw <- mutate(expData_raw, spot_ratio = round(spot_ratio, digit = 2))
expData_raw <- filter(expData_raw, spot_ratio > 0)
expData_raw <- filter(expData_raw, spot_ratio < 1.1)

expData <- expData_raw %>%
  group_by(exp_ID, dose, strain) %>%
  summarise(
    spot_mean = mean(spot_ratio, na.rm = TRUE)
  )
# add exp conditions
expData <- mutate(expData, 
                  strain = str_replace_all(
                    strain,
                    c(
                      "1" = "Strain1",
                      "2" = "Strain2",
                      "3" = "Strain3",
                      "4" = "Strain4"
                    )
                  )
)

write.csv(x = expData, file = "./analyzed/expData.csv")

plotData <- expData %>%
  group_by(dose, strain) %>%
  summarise(
    Survival_mean = mean(spot_mean, na.rm = TRUE),
    Survival_se = sd(spot_mean, na.rm = TRUE)/sqrt(length(spot_mean))
  )
write.csv(x = plotData, file = "./analyzed/plotData.csv")

g = ggplot(
  plotData,
  aes(
    x = dose,
    y = Survival_mean,
    color = strain,
    shape = strain,
    group = strain
  )
)+
  geom_line(linewidth = 1.5)+
  geom_point(size = 5)+
  geom_errorbar(
    aes(
      ymax = Survival_mean + Survival_se,
      ymin = Survival_mean - Survival_se,
      width = 16
    ),
    linewidth = 1.5
  )+
  scale_y_log10()+
  theme_bw(
    base_size = 20
  )+
  xlab("UV dose (J/m2)") +
  ylab("Fold change of spot-coverd area \n relative to UV 0 J/m2")+
  scale_shape_manual(values = c(15, 0, 16, 1))+
  scale_color_manual(values = c(colsBlack[6:5], "#0068b7", "#f39800"))+
  theme(
    axis.text = element_text(size = 20, colour = "black"),
    panel.background = element_rect(fill = "white", colour = "black", linewidth = 3),
    legend.position = "bottom",
    legend.title = element_blank(),
    legend.key.height = unit(1, 'cm'),
    aspect.ratio = 4/6
  ) +
  guides(shape=guide_legend(nrow=2, byrows=TRUE))
plot(g)
