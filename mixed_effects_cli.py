import pandas as pd
import statsmodels.formula.api as smf
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run mixed effects models on CSV data")
    
    parser.add_argument("--csv_path", type=str, required=True, help="Path to CSV file")
    parser.add_argument("--dependent_variable", type=str, required=True, help="Dependent variable")
    parser.add_argument("--independent_variables", type=str, nargs="+", required=True, help="Independent variables")
    parser.add_argument("--categorical_variables", type=str, nargs="*", default=[], help="Variables to treat as categorical")
    parser.add_argument("--groups", type=str, required=True, help="Variable for random intercepts")

    args = parser.parse_args()
    
    df = pd.read_csv(args.csv_path)
    
    # Builds formula
    var_terms = []
    for var in args.independent_variables:
        if var in args.categorical_variables:
            var_terms.append(f"C({var})")
        else:
            var_terms.append(var)
    
    formula = f"{args.dependent_variable} ~ {' + '.join(var_terms)}"
    
    model = smf.mixedlm(formula, data=df, groups=args.groups)
    model_fit = model.fit()
    
    print(model_fit.summary())

if __name__ == "__main__":
    main()