# Data processing with Pandas
import pandas as pd

def main():
    data = {
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'City': ['NYC', 'LA', 'Chicago']
    }

    df = pd.DataFrame(data)
    print(df)

    print(f'\nMean age: {df["Age"].mean()}')
    print(f'\nSummary:')
    print(df.describe())

    return {
        'rows': len(df),
        'mean_age': df['Age'].mean(),
        'columns': list(df.columns)
    }

if __name__ == '__main__':
    main()
