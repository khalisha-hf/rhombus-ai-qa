import re

# Define email validation regex pattern
# Pattern breakdown:
# ^[^@]+ - at least one character before @
# @ - exactly one @ symbol
# [^@]+ - at least one character after @ (the domain part)
# \. - literal dot
# [^@.]+ - at least one character after the dot
# $ - end of string
# We also need to ensure exactly one @ symbol and valid domain format

def is_valid_email(email):
    """
    Validate email according to requirements:
    - At least one character before @
    - Exactly one @ symbol
    - Domain part after @ contains at least one dot with characters on both sides
    """
    if pd.isna(email) or email == '':
        return False
    
    # Convert to string to handle any edge cases
    email_str = str(email).strip()
    
    if email_str == '' or email_str.lower() == 'none':
        return False
    
    # Check for exactly one @ symbol
    if email_str.count('@') != 1:
        return False
    
    # Split by @
    local_part, domain_part = email_str.split('@')
    
    # Local part must have at least one character
    if len(local_part) < 1:
        return False
    
    # Domain part must contain at least one dot with characters on both sides
    if '.' not in domain_part:
        return False
    
    # Split domain by dot
    domain_parts = domain_part.split('.')
    
    # Must have at least 2 parts (before and after dot)
    if len(domain_parts) < 2:
        return False
    
    # Each part separated by dot must have at least one character
    for part in domain_parts:
        if len(part) < 1:
            return False
    
    return True

# Start with input_df_1 and mask_df
target_df = input_df_1.copy()

# Validate that email column exists
if 'email' not in target_df.columns:
    raise ValueError("Column 'email' does not exist in target_df!")

# Store original email for validation
original_email = target_df['email'].copy()

# Validate each email
email_valid = target_df['email'].apply(is_valid_email)

# Replace invalid emails with null
target_df.loc[~email_valid, 'email'] = None

# Add the email_valid boolean column
target_df['email_valid'] = email_valid

# Build output_mask
output_mask = input_mask_1.reindex(index=target_df.index, columns=target_df.columns, fill_value=False).astype(bool)

# Mark the email column as modified where validation occurred
output_mask.loc[~email_valid, 'email'] = True

# Mark the new email_valid column as created
output_mask['email_valid'] = True

output_df = target_df