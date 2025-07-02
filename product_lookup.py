import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(page_title="🔁 Product Description Finder", layout="wide")
st.title("🔍 Old ➡ New Product Description Finder")

# Load file helper
def load_file(name_base):
    for ext in ['.xlsx', '.csv']:
        path = f"{name_base}{ext}"
        if os.path.exists(path):
            if ext == '.xlsx':
                return pd.read_excel(path)
            else:
                return pd.read_csv(path)
    return None

# Load files
old_df = load_file("old_products")
new_df = load_file("new_products")

if old_df is None or new_df is None:
    st.error("❌ Could not find `old_products` or `new_products` in this folder.")
else:
    # Normalize headers
    old_df.columns = old_df.columns.str.strip().str.lower()
    new_df.columns = new_df.columns.str.strip().str.lower()

    if 'product code' not in old_df.columns or 'product description' not in old_df.columns:
        st.error("❌ `old_products` must contain: `Product Code`, `Product Description`")
    elif 'sku' not in new_df.columns or 'sku name' not in new_df.columns:
        st.error("❌ `new_products` must contain: `SKU`, `SKU Name`")
    else:
        # Merge on product code
        merged = old_df.merge(new_df, left_on='product code', right_on='sku', how='left')

        # --- SEARCH FORM ---
        st.subheader("🔎 Search Options")
        with st.form("search_form"):
            query = st.text_input("Search by OLD Product Code or OLD Description", "")
            strengths = ['0mg', '20mg', '40mg', '50mg']
            selected_strength = st.selectbox("🧪 Filter by Nicotine Strength (optional)", ["All"] + strengths)
            submitted = st.form_submit_button("🔍 Search")

        if submitted:
            filtered = merged.copy()

            if query:
                filtered = filtered[
                    filtered['product code'].astype(str).str.contains(query, case=False, na=False) |
                    filtered['product description'].astype(str).str.contains(query, case=False, na=False)
                ]

            if selected_strength != "All":
                filtered = filtered[
                    filtered['product description'].str.contains(selected_strength, case=False, na=False) |
                    filtered['sku name'].str.contains(selected_strength, case=False, na=False)
                ]
            filtered = filtered.drop_duplicates(subset=['product code', 'sku name'])
            if not filtered.empty:
                st.success(f"✅ Found {len(filtered)} matching product(s)")

                display_df = filtered[['product code', 'product description', 'sku name']].rename(columns={
                    'product code': 'Product Code',
                    'product description': 'Old Description',
                    'sku name': 'New Description'
                })

                for i, row in display_df.iterrows():
                    col1, col2, col3, col4 = st.columns([2, 5, 5, 1])
                    col1.markdown(f"`{row['Product Code']}`")
                    col2.markdown(row['Old Description'])
                    col3.text_area("New Description", row['New Description'] if pd.notna(row['New Description']) else "❌ Not Found", height=70, key=i)

                # Excel download
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    display_df.to_excel(writer, index=False, sheet_name='Matches')
                st.download_button("📥 Download as Excel", data=output.getvalue(), file_name="matched_products.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            else:
                st.warning("🚫 No matches found.")
