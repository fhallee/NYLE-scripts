import pandas as pd
import statsmodels.formula.api as smf

file_path = '/Users/foresthallee/Documents/School/CUNY/Fall 25/Thesis/Data/ls_final.csv'
df = pd.read_csv(file_path)

formula = "F2 ~ latino + C(following_phone) + following_F2"
# 'C(following_phone)' treats 'following_phone' as a categorical variable
model = smf.mixedlm(formula, data=df, groups=df["speaker"])
model_fit = model.fit()

print(model_fit.summary())