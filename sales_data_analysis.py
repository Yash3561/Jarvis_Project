import pandas as pd
import matplotlib.pyplot as plt

def analyze_sales_data(sales_data_path):
    try:
        sales_data = pd.read_csv(sales_data_path)
    except FileNotFoundError:
        return "Error: sales data file not found."

    category_counts = sales_data.groupby('Category')['Product'].nunique()

    plt.figure(figsize=(8, 8))
    plt.pie(category_counts, labels=category_counts.index, autopct='%1.1f%%', startangle=90)
    plt.title('Distribution of Unique Products Across Categories')
    plt.savefig('category_distribution.png')

    return category_counts.to_string()



# Example usage (replace with your actual file path)
sales_data_path = 'data/sales_data.csv'  
summary = analyze_sales_data(sales_data_path)
print(summary)
