"""For data collection which do not have an official overview file, this script is
used to extract the data from a HTML table (developer tools in browser) and save it as a CSV file.
"""

import pandas as pd
from bs4 import BeautifulSoup

# Load the HTML file
# e.g. table from
# https://www.opengeodata.nrw.de/produkte/umwelt_klima/energie/solarkataster/strahlungsenergie_50cm/
file_path = "/Users/kopytjuk/Code/roof-analysis/data/aerial_images.html"
with open(file_path, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Find the table
table = soup.find("tbody")

# Extract the data
data = []
for row in table.find_all("tr"):
    cols = row.find_all("td")
    cols = [col.text.strip() for col in cols]
    data.append(cols)

# Create a DataFrame
df = pd.DataFrame(data, columns=["File", "Date", "Size"])

# Display the DataFrame
print(df)

df.to_csv("data/aerial_images.csv", index=False)
