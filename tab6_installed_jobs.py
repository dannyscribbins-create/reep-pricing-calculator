import streamlit as st
import pandas as pd
from pathlib import Path

@st.cache_data
def load_jobs_data():
    data_path = Path(__file__).parent / "2025_Shingle_Color_Book_Converted_FIXED.xlsx"
    if not data_path.exists():
        data_path = Path("2025_Shingle_Color_Book_Converted_FIXED.xlsx")
    df = pd.read_excel(data_path, sheet_name='Data')
    df['Zip Code'] = df['Zip Code'].astype(str).str.zfill(5)
    return df

def render_tab6():
    st.header("Installed Jobs Catalogue")
    st.markdown("*Searchable catalog of roofs installed in 2025*")
    
    df = load_jobs_data()
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Filters")
        
        manufacturers = sorted(df['Manufacturer'].unique().tolist())
        selected_manufacturers = st.multiselect(
            "Manufacturer",
            manufacturers,
            default=[],
            key="mfg_filter"
        )
        
        product_lines = sorted(df['Product Line'].unique().tolist())
        selected_products = st.multiselect(
            "Product Line",
            product_lines,
            default=[],
            key="product_filter"
        )
        
        colors = sorted(df['Color'].unique().tolist())
        selected_colors = st.multiselect(
            "Color",
            colors,
            default=[],
            key="color_filter"
        )
        
        st.divider()
        
        city_search = st.text_input(
            "Search by City",
            placeholder="e.g., Atlanta, Marietta",
            key="city_search"
        )
        
        zip_min, zip_max = int(df['Zip Code'].min()), int(df['Zip Code'].max())
        zip_range = st.slider(
            "Zip Code Range",
            zip_min, zip_max,
            (zip_min, zip_max),
            key="zip_slider"
        )
    
    filtered_df = df[
        (df['Manufacturer'].isin(selected_manufacturers)) &
        (df['Product Line'].isin(selected_products)) &
        (df['Color'].isin(selected_colors)) &
        (df['Zip Code'].astype(int) >= zip_range[0]) &
        (df['Zip Code'].astype(int) <= zip_range[1])
    ]
    
    if city_search:
        filtered_df = filtered_df[
            filtered_df['City'].str.contains(city_search, case=False, na=False)
        ]
    
    with col2:
        st.subheader(f"Results ({len(filtered_df)} jobs)")
        
        if len(filtered_df) == 0:
            st.info("No jobs match your filters. Try adjusting your search.")
        else:
            cols = st.columns(2)
            for idx, (_, row) in enumerate(filtered_df.iterrows()):
                col = cols[idx % 2]
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{row['Street Address']}**")
                        st.markdown(f"{row['City']}, {row['Zip Code']}")
                        
                        st.divider()
                        
                        badge_col1, badge_col2, badge_col3 = st.columns(3)
                        with badge_col1:
                            st.caption("Manufacturer")
                            st.markdown(f"`{row['Manufacturer']}`")
                        with badge_col2:
                            st.caption("Product")
                            st.markdown(f"`{row['Product Line']}`")
                        with badge_col3:
                            st.caption("Color")
                            st.markdown(f"`{row['Color']}`")
                        
                        st.divider()
                        st.caption(f"Source Page: {int(row['Source Page'])}")

