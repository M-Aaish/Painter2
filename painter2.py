import streamlit as st
import itertools
import math
import numpy as np

# ---------------------------------
# Base colors dictionary (with densities; we use only the RGB values here)
# ---------------------------------
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

# ---------------------------------
# Helper functions
# ---------------------------------
def rgb_to_hex(r, g, b):
    """Convert integer RGB values (0-255) to a hex string."""
    return f'#{r:02x}{g:02x}{b:02x}'

def mix_colors(recipe):
    """
    Given a recipe (list of tuples (color, percentage)),
    compute the weighted average of the RGB values.
    Percentages can be floats; returns an (R, G, B) tuple.
    """
    total, r_total, g_total, b_total = 0, 0, 0, 0
    for color, perc in recipe:
        r, g, b = color
        r_total += r * perc
        g_total += g * perc
        b_total += b * perc
        total += perc
    if total == 0:
        return (0, 0, 0)
    return (round(r_total / total), round(g_total / total), round(b_total / total))

def color_error(c1, c2):
    """Euclidean distance between two RGB colors."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def generate_recipes(target, step=10.0):
    """
    Generate candidate recipes from 3-color combinations.
    'step' is the percentage increment (e.g., 1.0, 2.5, 10.0).
    Returns a list of tuples (recipe, mixed_color, error).
    Each recipe is a list of tuples (base_color_name, percentage).
    """
    candidates = []
    # Prepare list of (name, rgb)
    base_list = [(name, info["rgb"]) for name, info in db_colors.items()]
    
    # Special case: if any base color nearly equals the target.
    for name, rgb in base_list:
        err = color_error(tuple(rgb), target)
        if err < 5:  # threshold for an exact match
            recipe = [(name, 100.0)]
            candidates.append((recipe, tuple(rgb), err))
    
    # Generate recipes for every 3-color combination.
    for (name1, rgb1), (name2, rgb2), (name3, rgb3) in itertools.combinations(base_list, 3):
        for p1 in np.arange(0, 100 + step, step):
            for p2 in np.arange(0, 100 - p1 + step, step):
                p3 = 100 - p1 - p2
                if p3 < 0:
                    continue
                recipe = [(name1, p1), (name2, p2), (name3, p3)]
                mix_recipe = [(rgb1, p1), (rgb2, p2), (rgb3, p3)]
                mixed = mix_colors(mix_recipe)
                err = color_error(mixed, target)
                candidates.append((recipe, mixed, err))
    # Sort candidates by error (lowest error first)
    candidates.sort(key=lambda x: x[2])
    # Choose top 3 unique recipes.
    top = []
    seen = set()
    for rec, mixed, err in candidates:
        key = tuple(sorted((name, perc) for name, perc in rec if perc > 0))
        if key not in seen:
            seen.add(key)
            top.append((rec, mixed, err))
        if len(top) >= 3:
            break
    return top

def display_color_block(color, label=""):
    """
    Display a colored block using an HTML div.
    'color' is an (R, G, B) tuple.
    """
    hex_color = rgb_to_hex(*color)
    st.markdown(
        f"<div style='background-color: {hex_color}; width:100px; height:100px; border:1px solid #000; text-align: center; line-height: 100px;'>{label}</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------
# Main app
# ---------------------------------
def main():
    st.title("Painter App")
    st.write("Enter your desired paint color to generate paint recipes using base colors.")
    
    # Input method: choose between Color Picker or RGB Sliders.
    method = st.radio("Select input method:", ["Color Picker", "RGB Sliders"])
    
    if method == "Color Picker":
        desired_hex = st.color_picker("Pick a color", "#ffffff")
        desired_rgb = tuple(int(desired_hex[i:i+2], 16) for i in (1, 3, 5))
    else:
        st.write("Select RGB values manually:")
        r = st.slider("Red", 0, 255, 255)
        g = st.slider("Green", 0, 255, 255)
        b = st.slider("Blue", 0, 255, 255)
        desired_rgb = (r, g, b)
        desired_hex = rgb_to_hex(r, g, b)
    
    st.write("**Desired Color:**", desired_hex)
    display_color_block(desired_rgb, label="Desired")
    
    # Slider to select percentage step, now limited to values between 4 and 10.
    step = st.slider("Select percentage step for recipe generation:", 4.0, 10.0, 10.0, step=0.5)
    
    if st.button("Generate Recipes"):
        recipes = generate_recipes(desired_rgb, step=step)
        if recipes:
            st.write("### Top 3 Paint Recipes")
            for idx, (recipe, mixed, err) in enumerate(recipes):
                st.write(f"**Recipe {idx+1}:** (Error = {err:.2f})")
                cols = st.columns(4)
                with cols[0]:
                    st.write("Desired:")
                    display_color_block(desired_rgb, label="Desired")
                with cols[1]:
                    st.write("Result:")
                    display_color_block(mixed, label="Mixed")
                with cols[2]:
                    st.write("Composition:")
                    for name, perc in recipe:
                        if perc > 0:
                            base_rgb = tuple(db_colors[name]["rgb"])
                            st.write(f"- **{name}**: {perc:.1f}%")
                            display_color_block(base_rgb, label=name)
                with cols[3]:
                    st.write("Difference:")
                    st.write(f"RGB Distance: {err:.2f}")
        else:
            st.error("No recipes found.")

if __name__ == "__main__":
    main()
