import streamlit as st
import pandas as pd
import numpy as np
from itertools import combinations
from scipy.optimize import minimize

# ---------- Utility Functions ----------

def hex_to_rgb(hex_str):
    """Convert hex color (e.g. '#AABBCC') to an (R, G, B) tuple."""
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def find_recipe_for_target(target_rgb, base_colors, num_colors, tolerance=5.0):
    """
    Given a target RGB and a list of base_colors (each a dict with keys 'name' and 'rgb'),
    try all combinations of 'num_colors' paints and return valid recipes (if the mixture error is below tolerance).
    Each recipe is a dict with keys 'colors' and 'weights'.
    """
    recipes = []
    # Iterate over all combinations (order does not matter)
    for comb in combinations(base_colors, num_colors):
        colors_array = np.array([col['rgb'] for col in comb])  # shape: (num_colors, 3)

        # Define the objective: squared error between mix and target
        def objective(weights):
            mix = np.dot(weights, colors_array)  # weighted sum, shape (3,)
            return np.sum((mix - target_rgb)**2)

        # Constraints: weights sum to 1 and each weight is >= 0
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = [(0, 1)] * num_colors
        init_guess = [1/num_colors] * num_colors

        res = minimize(objective, init_guess, bounds=bounds, constraints=constraints)
        if res.success:
            error = np.sqrt(objective(res.x))
            if error < tolerance:
                recipe = {
                    'colors': [col['name'] for col in comb],
                    'weights': res.x * 100,  # convert fraction to percentage
                    'error': error
                }
                recipes.append(recipe)
    return recipes

# ---------- Main App ----------

st.title("Painter App – Color Mixing Recipes")

st.markdown("""
This app lets you select a paint brand and pick your desired target RGB color.
It then computes mixing recipes – each recipe being a combination of paints (from the selected brand) 
with the corresponding percentages, such that the weighted average of their RGB values approximates your target color.
""")

# Load the Excel file (ensure 'paints.xlsx' is in the same directory)
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("paints.xlsx")
        return df
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return None

df = load_data()
if df is None:
    st.stop()

# Display available brands from the Excel database
brands = sorted(df["Brand"].unique())
brand = st.selectbox("Select a Brand", options=brands)

# Filter the dataframe for the selected brand
brand_df = df[df["Brand"] == brand]

# Let the user pick a target color using a color picker
target_hex = st.color_picker("Pick your desired target color", "#AABBCC")
target_rgb = np.array(hex_to_rgb(target_hex), dtype=float)

st.write("Target RGB:", target_rgb)

# Prepare the list of base colors (each with a name and its RGB as a numpy array)
base_colors = []
for _, row in brand_df.iterrows():
    base_colors.append({
        "name": row["ColorName"],
        "rgb": np.array([row["R"], row["G"], row["B"]], dtype=float)
    })

if st.button("Find Recipes"):
    st.info("Searching for recipes...")
    recipes_found = []
    
    # First, try recipes with 3 base colors
    recipes_3 = find_recipe_for_target(target_rgb, base_colors, num_colors=3, tolerance=5.0)
    recipes_found.extend(recipes_3)
    
    # If fewer than 3 recipes are found, try combinations of 4 colors
    if len(recipes_found) < 3:
        recipes_4 = find_recipe_for_target(target_rgb, base_colors, num_colors=4, tolerance=5.0)
        recipes_found.extend(recipes_4)
    
    if not recipes_found:
        st.error("No recipes found that match the target color within tolerance. Try a different target color or check your database.")
    else:
        st.success(f"Found {len(recipes_found)} recipe(s). Displaying up to 3 recipes below:")
        # Display up to 3 recipes
        for i, recipe in enumerate(recipes_found[:3], start=1):
            st.markdown(f"### Recipe {i}")
            for color, weight in zip(recipe["colors"], recipe["weights"]):
                st.write(f"**{color}**: {weight:.1f}%")
            st.write(f"Mix Error: {recipe['error']:.2f}")
