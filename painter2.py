import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations
from scipy.optimize import minimize

# Base colors with densities
db_colors = {
    "Burnt Sienna": {"rgb": [58, 22, 14], "density": 1073},
    "Burnt Umber": {"rgb": [50, 27, 15], "density": 1348},
    "Cadmium Orange Hue": {"rgb": [221, 105, 3], "density": 1338},
    "Cadmium Red Deep Hue": {"rgb": [171, 1, 5], "density": 902},
    "Cadmium Red Medium": {"rgb": [221, 63, 0], "density": 1547},
    "Cadmium Red Light": {"rgb": [225, 83, 0], "density": 1573},
    "Cadmium Red Dark": {"rgb": [166, 0, 9], "density": 1055},
    "Cadmium Yellow Hue": {"rgb": [255, 193, 0], "density": 1230},
    "Cadmium Yellow Light": {"rgb": [255, 194, 0], "density": 1403},
    "Cadmium Yellow Medium": {"rgb": [255, 161, 0], "density": 1534},
    "Cerulean Blue Hue": {"rgb": [0, 74, 91], "density": 1216},
    "Cobalt Blue": {"rgb": [0, 39, 71], "density": 1317},
    "Dioxazine Purple": {"rgb": [215, 17, 115], "density": 1268},
    "French Ultramarine": {"rgb": [8, 8, 32], "density": 1277},
    "Ivory Black": {"rgb": [27, 28, 28], "density": 1228},
    "Lamp Black": {"rgb": [21, 21, 20], "density": 958},
    "Lemon Yellow": {"rgb": [239, 173, 0], "density": 1024},
    "Magenta": {"rgb": [98, 4, 32], "density": 1822},
    "Permanent Alizarin Crimson": {"rgb": [74, 16, 16], "density": 1217},
    "Permanent Rose": {"rgb": [130, 0, 24], "density": 1227},
    "Permanent Sap Green": {"rgb": [28, 42, 10], "density": 1041},
    "Phthalo Blue (Red Shade)": {"rgb": [17, 12, 37], "density": 1080},
    "Phthalo Green (Yellow Shade)": {"rgb": [0, 32, 24], "density": 1031},
    "Phthalo Green (Blue Shade)": {"rgb": [3, 26, 33], "density": 1021},
    "Prussian Blue": {"rgb": [15, 11, 11], "density": 984},
    "Raw Sienna": {"rgb": [117, 70, 17], "density": 1211},
    "Raw Umber": {"rgb": [37, 28, 20], "density": 1273},
    "Titanium White": {"rgb": [249, 245, 234], "density": 1423},
    "Viridian": {"rgb": [0, 53, 40], "density": 1149},
    "Yellow Ochre": {"rgb": [187, 128, 18], "density": 1283},
    "Zinc White (Mixing White)": {"rgb": [250, 242, 222], "density": 1687},
}

# Function to mix colors using least squares optimization
def optimize_color_mix(target_rgb, selected_colors):
    # Extract the RGB values of the selected colors
    color_rgbs = np.array([db_colors[name]["rgb"] for name in selected_colors])

    # Define an objective function to minimize the color difference
    def objective(weights):
        mixed_rgb = np.dot(weights, color_rgbs)
        return np.linalg.norm(mixed_rgb - target_rgb)  # Minimize RGB difference

    # Initial guess: equal distribution
    initial_weights = np.ones(len(selected_colors)) / len(selected_colors)

    # Constraints: sum of weights must be 1
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

    # Bounds: each weight between 0 and 1
    bounds = [(0, 1)] * len(selected_colors)

    # Solve the optimization problem
    result = minimize(objective, initial_weights, bounds=bounds, constraints=constraints)

    return result.x if result.success else None

# Streamlit UI
st.title("🎨 Paint Recipe Generator")
st.markdown("Enter an RGB value and get optimized paint mixing recipes.")

# User Input
r = st.slider("Red", 0, 255, 128)
g = st.slider("Green", 0, 255, 128)
b = st.slider("Blue", 0, 255, 128)
target_color = np.array([r, g, b])

# Display Desired Color
st.subheader("🎨 Desired Color")
st.markdown(f"<div style='width:150px; height:75px; background-color:rgb({r},{g},{b});'></div>", unsafe_allow_html=True)

if st.button("Generate Recipe"):
    # Find best 5 closest colors
    color_names = list(db_colors.keys())
    color_rgbs = np.array([db_colors[name]["rgb"] for name in color_names])
    
    # Compute Euclidean distances
    distances = np.linalg.norm(color_rgbs - target_color, axis=1)
    closest_indices = np.argsort(distances)[:5]  # Get 5 closest colors

    # Generate optimized paint recipes
    best_recipes = []
    for combo in combinations([color_names[i] for i in closest_indices], 3):
        weights = optimize_color_mix(target_color, combo)
        if weights is not None:
            mixed_rgb = np.dot(weights, np.array([db_colors[c]["rgb"] for c in combo])).astype(int)
            error = np.linalg.norm(mixed_rgb - target_color)
            best_recipes.append({"colors": combo, "weights": weights, "mixed_rgb": mixed_rgb, "error": error})

    # Sort by best match
    best_recipes = sorted(best_recipes, key=lambda x: x["error"])[:3]

    # Display recipes
    for idx, recipe in enumerate(best_recipes, start=1):
        st.markdown(f"### Recipe {idx}")

        # Display colors with percentages
        cols = st.columns(3)
        for i, color_name in enumerate(recipe["colors"]):
            with cols[i]:
                st.markdown(f"<div style='width:100px; height:50px; background-color:rgb({db_colors[color_name]['rgb'][0]},{db_colors[color_name]['rgb'][1]},{db_colors[color_name]['rgb'][2]});'></div>", unsafe_allow_html=True)
                st.write(f"**{color_name}**: {round(recipe['weights'][i] * 100, 1)}%")

        # Display mixed color result
        st.markdown("##### Mixed Color Result")
        mixed_rgb = recipe["mixed_rgb"]
        st.markdown(f"<div style='width:150px; height:75px; background-color:rgb({mixed_rgb[0]},{mixed_rgb[1]},{mixed_rgb[2]});'></div>", unsafe_allow_html=True)

        # Show RGB error
        st.write(f"**Color Match Error:** {round(recipe['error'], 2)}")
