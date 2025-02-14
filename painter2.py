import streamlit as st
import pandas as pd
import numpy as np
import itertools
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# Load the Excel file
@st.cache_data
def load_data():
    file_path = "paints.xlsx"  # Ensure file is in the app directory
    try:
        xls = pd.ExcelFile(file_path)
        brands = {}
        
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=1).dropna(how='all')
            possible_name_col = df.columns[0]  # First column as Name
            rgb_cols = [col for col in df.columns if any(c in col.lower() for c in ['r', 'g', 'b'])]
            
            if len(rgb_cols) == 3:
                df['RGB'] = df[rgb_cols].apply(lambda row: (row[0], row[1], row[2]), axis=1)
                brands[sheet] = df[[possible_name_col, 'RGB']].rename(columns={possible_name_col: "Name", 'RGB': 'RGB'})
        
        return brands
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return {}

# Solve recipe with better optimization
def solve_recipe(colors, target):
    def objective(x):
        mix = np.dot(x, colors)
        return np.linalg.norm(mix - target)
    
    cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    bounds = [(0, 1)] * len(colors)
    x0 = np.full(len(colors), 1/len(colors))
    
    res = minimize(objective, x0, bounds=bounds, constraints=cons, method="SLSQP")
    return res.x, np.linalg.norm(np.dot(res.x, colors) - target)

# Generate optimized recipes
def generate_recipes(paints_df, target, n_recipes=3):
    best_recipes = []
    for combo in itertools.combinations(range(len(paints_df)), 3):
        colors = np.array([paints_df.iloc[i]['RGB'] for i in combo], dtype=float)
        weights, error = solve_recipe(colors, target)
        best_recipes.append({
            "paints": [paints_df.iloc[i]['Name'] for i in combo],
            "colors": colors,
            "weights": weights,
            "error": error
        })
    
    return sorted(best_recipes, key=lambda x: x['error'])[:n_recipes]

# Visual representation of colors
def plot_colors(target, best_recipe):
    fig, ax = plt.subplots(1, 3, figsize=(9, 3))
    
    ax[0].imshow([[target / 255]])
    ax[0].set_title("Target Color")
    ax[0].axis('off')
    
    mix_result = np.dot(best_recipe['weights'], best_recipe['colors']) / 255
    ax[1].imshow([[mix_result]])
    ax[1].set_title("Mixed Result")
    ax[1].axis('off')
    
    colors = [c / 255 for c in best_recipe['colors']]
    ax[2].imshow([colors])
    ax[2].set_title("Used Colors")
    ax[2].axis('off')
    
    st.pyplot(fig)

def main():
    st.title("Painter Mixing App")
    brands = load_data()
    brand_names = list(brands.keys())
    selected_brand = st.selectbox("Select Brand", brand_names)
    
    target_color = st.color_picker("Pick Target Color", "#808080")
    target_R, target_G, target_B = tuple(int(target_color[i:i+2], 16) for i in (1, 3, 5))
    
    if st.button("Generate Recipes"):
        target = np.array([target_R, target_G, target_B])
        paints_df = brands[selected_brand]
        recipes = generate_recipes(paints_df, target)
        
        if recipes:
            best_recipe = recipes[0]
            plot_colors(target, best_recipe)
            
            for idx, rec in enumerate(recipes, 1):
                st.markdown(f"**Recipe {idx} (Error: {rec['error']:.2f})**")
                for paint, weight in zip(rec["paints"], rec["weights"]):
                    st.write(f"{paint}: **{weight*100:.1f}%**")
                st.write("---")
        else:
            st.warning("No recipes found. Try adjusting your target color.")

if __name__ == "__main__":
    main()
