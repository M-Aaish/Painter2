import streamlit as st
import pandas as pd
import numpy as np
import itertools
from scipy.optimize import minimize

# Load the Excel file
@st.cache_data
def load_data():
    file_path = "paints.xlsx"  # Ensure the file is in the app directory
    xls = pd.ExcelFile(file_path)
    brands = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        if 'Name' in df.columns and 'RGB' in df.columns:
            # Convert RGB column from string to numerical tuple
            df['RGB'] = df['RGB'].apply(lambda x: tuple(map(int, x.split(','))) if isinstance(x, str) else (0, 0, 0))
            brands[sheet] = df[['Name', 'RGB']]
    return brands

def solve_recipe(colors, target):
    """
    Find mix ratios of three colors that approximate the target color.
    """
    def objective(x):
        mix = np.dot(x, colors)
        return np.linalg.norm(mix - target) ** 2
    
    cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    bounds = [(0, 1)] * 3
    x0 = np.array([1/3, 1/3, 1/3])
    res = minimize(objective, x0, bounds=bounds, constraints=cons, method="SLSQP")
    return res.x, np.linalg.norm(np.dot(res.x, colors) - target)

def generate_recipes(paints_df, target, n_recipes=3):
    recipes = []
    for combo in itertools.combinations(range(len(paints_df)), 3):
        colors = np.array([paints_df.iloc[i]['RGB'] for i in combo])
        weights, error = solve_recipe(colors, target)
        recipes.append({
            "paints": [paints_df.iloc[i]['Name'] for i in combo],
            "weights": weights,
            "error": error
        })
    return sorted(recipes, key=lambda x: x['error'])[:n_recipes]

def main():
    st.title("Painter Mixing App")
    brands = load_data()
    brand_names = list(brands.keys())
    selected_brand = st.selectbox("Select Brand", brand_names)
    
    target_R = st.number_input("Target R", 0, 255, 128)
    target_G = st.number_input("Target G", 0, 255, 128)
    target_B = st.number_input("Target B", 0, 255, 128)
    
    if st.button("Generate Recipes"):
        target = np.array([target_R, target_G, target_B])
        paints_df = brands[selected_brand]
        recipes = generate_recipes(paints_df, target)
        
        if recipes:
            for idx, rec in enumerate(recipes, 1):
                st.markdown(f"**Recipe {idx} (Error: {rec['error']:.2f})**")
                for paint, weight in zip(rec["paints"], rec["weights"]):
                    st.write(f"{paint}: **{weight*100:.1f}%**")
                st.write("---")
        else:
            st.warning("No recipes found. Try adjusting your target color.")

if __name__ == "__main__":
    main()
