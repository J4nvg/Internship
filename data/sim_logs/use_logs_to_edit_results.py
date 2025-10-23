from scipy.stats import binomtest
import pandas as pd
import os


print(os.listdir('./'))


for file in os.listdir('./'):
    if not file.endswith('.csv'):
        continue
    df = pd.read_csv(file,header = 1)

    df['all_hiders_found'] = (df['hider_frac_found'] == 1).astype(int)

    k = df['all_hiders_found'].sum()
    n = len(df)
    result = binomtest(k=k, n=n)
    p_all_hiders_found = result.statistic

    ci = result.proportion_ci()
    print(f"p(All found) = {p_all_hiders_found} 95% Confidence Interval: (low={ci.low:.6f}, high={ci.high:.6f})")
    print(df)

    print(df['all_hiders_found'].mean())
    df.to_csv(file,sep='\t', encoding='utf-8', header=True)
    print(file + " saved as csv")


    all_found = {
        "min": 'NA',
        "max": 'NA',
        "mean": p_all_hiders_found,
        "var": 'NA',
        "ci_lower": ci.low,
        "ci_upper": ci.high,
        "Half_width": 'NA',
    }

    summary_file_path = os.path.join('../sim_results', file)

    if os.path.exists(summary_file_path):
        try:
            with open(summary_file_path, 'r') as f:
                lines = f.readlines()

            lines_to_keep = lines[:-1]

            new_line = (
                f"all_found\t{all_found['min']}\t{all_found['max']}\t"
                f"{all_found['mean']}\t{all_found['var']}\t"
                f"{all_found['ci_lower']}\t{all_found['ci_upper']}\t"
                f"{all_found['Half_width']}\n"
            )

            with open(summary_file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines_to_keep)
                f.write(new_line)

            print(f"Successfully updated summary file: {summary_file_path}\n")

        except Exception as e:
            print(f"Error processing summary file {summary_file_path}: {e}\n")
    else:
        print(f"Warning: Summary file not found at {summary_file_path}\n")
