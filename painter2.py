import streamlit as st
import pandas as pd
import numpy as np
import itertools
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# Load the Excel file
@st.cache_data
def load_data():
    file_path = "paints.xlsx"
    try:
        xls = pd.ExcelFile(file_path)
        brands = {}

        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1).dropna(how='all')

            # Identify the name and RGB columns
            name_col = df.columns[1]  # Assuming second column is paint name
            rgb_col = df.columns[2]   # Assuming third column contains RGB values

            # Convert RGB strings to numerical tuples
            df['RGB'] = df[rgb_col].astype(str).apply(
                lambda x: tuple(map(int, x.split(','))) if isinstance(x, str) and ',' in x else None
            )
            df = df.dropna(subset=['RGB'])  # Remove invalid rows

            if name_col and 'RGB' in df.columns:
                brands[sheet] = df[[name_col, 'RGB']].rename(columns={name_col: "Name"})
        
        return brands
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return {}

def solve_recipe(colors, target):
    """
    Optimizes the mix ratios to minimize color difference.
    """
    def objective(x):
        mix = np.dot(x, colors)
        return np.linalg.norm(mix - target)  # Reduce absolute error

    cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]  # Ensure sum is 1
    bounds = [(0, 1)] * len(colors)
    x0 = np.full(len(colors), 1/len(colors))

    res = minimize(objective, x0, bounds=bounds, constraints=cons, method="SLSQP")
    if res.success:
        return res.x, np.linalg.norm(np.dot(res.x, colors) - target)
    else:
        return None, float('inf')

def generate_recipes(paints_df, target, n_recipes=3):
    """
    Generates optimized color mixing recipes.
    """
    recipes = []
    
    for combo_size in [3, 4, 5]:  # Try mixing 3, 4, or 5 colors
        for combo in itertools.combinations(range(len(paints_df)), combo_size):
            colors = np.array([paints_df.iloc[i]['RGB'] for i in combo])
            weights, error = solve_recipe(colors, target)
            if weights is not None:
                recipes.append({
                    "paints": [paints_df.iloc[i]['Name'] for i in combo],
                    "weights": weights,
                    "error": error
                })

    return sorted(recipes, key=lambda x: x['error'])[:n_recipes]

def display_color_block(color, label):
    """
    Displays a colored box with a label.
    """
    hex_color = "#{:02x}{:02x}{:02x}".format(*[int(c) for c in color])
    st.markdown(
        f"<div style='width:100px; height:50px; background:{hex_color}; border:1px solid black; "
        f"text-align:center; line-height:50px; margin:5px;'>{label}</div>",
        unsafe_allow_html=True
    )

def main():
    st.title("🎨 Paint Mixer - Find the Best Color Match!")

    brands = load_data()
    brand_names = list(brands.keys())

    if not brand_names:
        st.error("No paint data loaded. Check the Excel file.")
        return
    
    selected_brand = st.selectbox("Select Paint Brand", brand_names)

    # User inputs RGB values manually
    target_R = st.number_input("Enter Red (R)", 0, 255, 128)
    target_G = st.number_input("Enter Green (G)", 0, 255, 128)
    target_B = st.number_input("Enter Blue (B)", 0, 255, 128)

    target_rgb = (target_R, target_G, target_B)

    # Show target color visually
    st.subheader("🎯 Target Color")
    display_color_block(target_rgb, "Target")

    if st.button("Generate Recipes"):
        target = np.array(target_rgb)
        paints_df = brands[selected_brand]

        if paints_df.empty:
            st.error("No paints available for the selected brand.")
            return
        
        recipes = generate_recipes(paints_df, target)

        if not recipes:
            st.warning("No good match found. Try adjusting the color.")
        else:
            for idx, rec in enumerate(recipes, 1):
                st.subheader(f"🎨 Recipe {idx} (Error: {rec['error']:.2f})")

                # Compute mixed result color
                mix_rgb = np.dot(rec["weights"], [paints_df[paints_df['Name'] == paint]['RGB'].values[0] for paint in rec["paints"]])
                mix_rgb = np.clip(mix_rgb, 0, 255).astype(int)

                # Show result color
                st.markdown("🔹 **Final Mixed Color:**")
                display_color_block(mix_rgb, "Mixed Result")

                # Show individual paint colors used
                st.markdown("🔹 **Used Paints:**")
                for paint, weight in zip(rec["paints"], rec["weights"]):
                    paint_rgb = paints_df[paints_df['Name'] == paint]['RGB'].values[0]
                    display_color_block(paint_rgb, f"{paint} ({weight*100:.1f}%)")
                
                st.write("---")

if __name__ == "__main__":
    main()
