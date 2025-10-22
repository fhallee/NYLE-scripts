library(vowels)

vowel_data <- read.delim("for_NORM.txt", header = TRUE, sep = "\t", stringsAsFactors = FALSE)
nearey_normalized <- norm.nearey(vowel_data, formant.int = TRUE)
write.csv(nearey_normalized, "nearey_normalized.csv", row.names = FALSE)