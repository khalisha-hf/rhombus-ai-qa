# Start with input dataframe
output_df = input_df_1.copy()

# Strip leading/trailing whitespace and convert to title case
output_df['customer_name'] = output_df['customer_name'].str.strip().str.title()

# Build output mask: mark customer_name column as True (modified), others as False
output_mask = input_mask_1.copy()
output_mask['customer_name'] = True
for col in output_df.columns:
    if col != 'customer_name':
        output_mask[col] = False
