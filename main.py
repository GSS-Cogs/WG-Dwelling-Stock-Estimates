# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.2.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # Dwelling stock estimates by local authority and tenure
#
# These statistics are available from [StatsWales](https://statswales.gov.wales/Catalogue/Housing/Dwelling-Stock-Estimates/dwellingstockestimates-by-localauthority-tenure) using Microsoft's [Open Data Protocol](https://en.wikipedia.org/wiki/Open_Data_Protocol)

# +
from gssutils import *

scraper = Scraper('https://statswales.gov.wales/Catalogue/Housing/Dwelling-Stock-Estimates/dwellingstockestimates-by-localauthority-tenure')
scraper
# -

if len(scraper.distributions) == 0:
    from gssutils.metadata import Distribution
    dist = Distribution(scraper)
    dist.title = 'Dataset'
    dist.downloadURL = 'http://open.statswales.gov.wales/dataset/hous0501'
    dist.mediaType = 'application/json'
    scraper.distributions.append(dist)

table = scraper.distribution(title='Dataset').as_pandas()
from IPython.core.display import HTML
for col in table:
    if col not in ['Area_Code', 'Data', 'Area_SortOrder', 'RowKey', 'PartitionKey',
                   'Tenure_SortOrder', 'Year_Code', 'Year_SortOrder']:
        table[col] = table[col].astype('category')
        display(HTML(f'<h3>{col}</h3>'))
        display(table[col].cat.categories)
table

areas = table[['Area_Code', 'Area_ItemName_ENG']].drop_duplicates()
areas.set_index('Area_Code', inplace=True)
table.drop(columns=['Area_ItemName_ENG', 'Area_SortOrder', 'PartitionKey', 'RowKey',
                    'Tenure_SortOrder', 'Year_ItemName_ENG', 'Year_SortOrder'],
           inplace=True)
areas

wales_gss_codes = pd.read_csv('wales-gss.csv', index_col='Label')
areas = areas.join(wales_gss_codes, on='Area_ItemName_ENG')

table['Period'] = table['Year_Code'].map(
    lambda x: f'gregorian-interval/{str(x)[:4]}-03-31T00:00:00/P1Y'
)
table.drop(columns=['Year_Code'], inplace=True)
table

table.rename(columns={
    'Tenure_ItemName_ENG': 'Tenure'
}, inplace=True)
table['Measure Type'] = table['Tenure'].map(
    lambda x: 'Count' if x.endswith('(Number)') else 'Percentage'
)
table['Unit'] = 'dwellings'
table['Tenure'] = table['Tenure'].map(
    lambda x: pathify(x[:-len(' (Number)')] if x.endswith(' (Number)') else
                      x[:-len(' (%}')] if x.endswith(' (%)') else x).replace('/','-')
    if x != 'All tenures (Number)' else 'total')
table

table['Geography'] = table['Area_Code'].map(
    lambda x: areas.loc[int(x)]['Code']
)
table.drop(columns=['Area_Code', 'Area_ItemNotes_ENG', 'Tenure_Code', 'Tenure_ItemNotes_ENG', 
                    'Tenure_Hierarchy', 'Area Hierarchy'], inplace=True)
table.rename(columns={'Data': 'Value'}, inplace=True)
table = table[table['Measure Type'] != 'Percentage']
table['Value'] = table['Value'].astype(int)
table

# +
out = Path('out')
out.mkdir(exist_ok=True, parents=True)

table.to_csv(out / 'observations.csv', index = False)
# -

schema = CSVWMetadata('https://gss-cogs.github.io/ref_housing/')
schema.create(out / 'observations.csv', out / 'observations.csv-schema.json')

from datetime import datetime
scraper.dataset.family = 'housing'
scraper.dataset.theme = THEME['housing-planning-local-services']
scraper.dataset.modified = datetime.now()
scraper.dataset.creator = scraper.dataset.publisher
with open(out / 'dataset.trig', 'wb') as metadata:
    metadata.write(scraper.generate_trig())

# +
#table['Tenure'].unique()

# +
#table['Tenure_Hierarchy'].unique()

# +
#table['Area_Hierarchy'].unique()

# +
#table['Geography'].unique()
