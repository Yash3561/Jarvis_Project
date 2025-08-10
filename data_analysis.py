import pandas as pd
import matplotlib.pyplot as plt

try:
    df = pd.read_csv("data.csv")  # Replace "data.csv" with the actual filename if different
except FileNotFoundError:
    print("Error: 'data.csv' not found. Please provide the correct filename.")
    exit()

category_counts = df.groupby('Category')['Product'].nunique()

plt.figure(figsize=(10, 6))
plt.pie(category_counts, labels=category_counts.index, autopct='%1.1f%%', startangle=90)
plt.title('Distribution of Unique Products Across Categories')
plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
plt.savefig('category_distribution.png')

summary = f"""
Total Unique Products: {df['Product'].nunique()}
Unique Product Counts per Category:\n{category_counts}
"""
print(summary)