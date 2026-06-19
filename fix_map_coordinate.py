# ============================================================
# FIX — Add Full Brazilian State Names for Power BI Map
# Run this once, then reload olist_delivered.csv in Power BI
# ============================================================

import pandas as pd

print("Loading olist_delivered.csv...")
delivered = pd.read_csv(r'C:\Users\a\Desktop\E-Commerce Sales Dashboard by Olist\olist_delivered.csv', low_memory=False)

# Full Brazilian state names mapping
state_names = {
    'AC': 'Acre, Brazil',
    'AL': 'Alagoas, Brazil',
    'AM': 'Amazonas, Brazil',
    'AP': 'Amapá, Brazil',
    'BA': 'Bahia, Brazil',
    'CE': 'Ceará, Brazil',
    'DF': 'Distrito Federal, Brazil',
    'ES': 'Espírito Santo, Brazil',
    'GO': 'Goiás, Brazil',
    'MA': 'Maranhão, Brazil',
    'MG': 'Minas Gerais, Brazil',
    'MS': 'Mato Grosso do Sul, Brazil',
    'MT': 'Mato Grosso, Brazil',
    'PA': 'Pará, Brazil',
    'PB': 'Paraíba, Brazil',
    'PE': 'Pernambuco, Brazil',
    'PI': 'Piauí, Brazil',
    'PR': 'Paraná, Brazil',
    'RJ': 'Rio de Janeiro, Brazil',
    'RN': 'Rio Grande do Norte, Brazil',
    'RO': 'Rondônia, Brazil',
    'RR': 'Roraima, Brazil',
    'RS': 'Rio Grande do Sul, Brazil',
    'SC': 'Santa Catarina, Brazil',
    'SE': 'Sergipe, Brazil',
    'SP': 'São Paulo, Brazil',
    'TO': 'Tocantins, Brazil',
}

# Add full state name column
delivered['state_full_name'] = delivered['customer_state'].map(state_names)

# Add latitude and longitude for each state capital
state_coords = {
    'AC': (-9.0238, -70.812),
    'AL': (-9.5713, -36.782),
    'AM': (-3.4168, -65.856),
    'AP': (1.4102,  -51.770),
    'BA': (-12.579, -41.700),
    'CE': (-5.4984, -39.320),
    'DF': (-15.780, -47.929),
    'ES': (-19.183, -40.308),
    'GO': (-15.827, -49.836),
    'MA': (-5.4220, -45.440),
    'MG': (-18.512, -44.555),
    'MS': (-20.769, -54.785),
    'MT': (-12.642, -55.422),
    'PA': (-3.4168, -52.333),
    'PB': (-7.2399, -36.782),
    'PE': (-8.8137, -36.954),
    'PI': (-7.7183, -42.729),
    'PR': (-24.891, -51.557),
    'RJ': (-22.908, -43.173),
    'RN': (-5.8127, -36.208),
    'RO': (-10.834, -63.343),
    'RR': (2.0895,  -61.217),
    'RS': (-30.034, -51.217),
    'SC': (-27.242, -50.218),
    'SE': (-10.576, -37.385),
    'SP': (-23.549, -46.633),
    'TO': (-10.175, -48.298),
}

delivered['latitude']  = delivered['customer_state'].map(
    lambda x: state_coords.get(x, (None, None))[0])
delivered['longitude'] = delivered['customer_state'].map(
    lambda x: state_coords.get(x, (None, None))[1])

print(f"✅ Added state_full_name, latitude, longitude columns")
print(f"\nSample mapping:")
sample = delivered[['customer_state','state_full_name',
                     'latitude','longitude']].drop_duplicates().head(10)
print(sample.to_string(index=False))

# Save
delivered.to_csv(r'C:\Users\a\Desktop\E-Commerce Sales Dashboard by Olist\olist_delivered.csv', index=False)
print(f"\n✅ olist_delivered.csv updated and saved!")
print("""
Next steps in Power BI:
1. Home → Transform Data → Refresh olist_delivered table
2. Click 'Close & Apply'
3. On Map visual:
   - Use 'latitude'  → Latitude field
   - Use 'longitude' → Longitude field
   - Use 'Total Revenue' → Bubble size field
   - Use 'customer_state' → Tooltips field
""")