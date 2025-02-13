import streamlit as st
import numpy as np
import json
import random
from PIL import Image, ImageColor, ImageDraw
from streamlit_drawable_canvas import st_canvas

# Helper function to convert HEX color to RGB tuple
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Helper function to convert RGB tuple to HEX color
def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

# Function to compute the mixed color from base colors and ratios.
def mix_colors(colors, ratios):
    # ratios should be percentages that sum to 100
    total = sum(ratios)
    if total == 0:
        return "#ffffff"  # default white if no ratios
    mixed = np.array([0, 0, 0], dtype=float)
    for color, ratio in zip(colors, ratios):
        rgb = np.array(hex_to_rgb(color))
        mixed += (ratio/total) * rgb
    mixed = np.clip(mixed, 0, 255).astype(int)
    return rgb_to_hex(tuple(mixed))

# Generate three recipe variations by perturbing the current ratios slightly
def generate_recipe_variations(base_ratios, num_variations=3, perturbation=5):
    recipes = []
    n = len(base_ratios)
    for _ in range(num_variations):
        # Start with the current ratios
        new_ratios = np.array(base_ratios, dtype=float)
        # Perturb each ratio by a random value in [-perturbation, perturbation]
        perturb = np.random.uniform(-perturbation, perturbation, size=n)
        new_ratios += perturb
        # Ensure no negative percentages
        new_ratios = np.clip(new_ratios, 0, None)
        # Normalize to sum to 100
        if new_ratios.sum() == 0:
            new_ratios = np.ones(n)
        new_ratios = new_ratios / new_ratios.sum() * 100
        # Round to two decimals
        new_ratios = [round(val, 2) for val in new_ratios]
        recipes.append(new_ratios)
    return recipes

st.set_page_config(page_title="Paint Recipe Maker", layout="wide")

st.title("Paint Recipe Maker")

# Sidebar: Input target color (HEX) or upload an image to pick a color
st.sidebar.header("Target Color Selection")
mode = st.sidebar.radio("Choose input method:", ("Color Picker", "Image Upload"))

target_color = None
if mode == "Color Picker":
    target_color = st.sidebar.color_picker("Pick a target color", "#ff5733")
    st.sidebar.write("Target Color:", target_color)
else:
    uploaded_file = st.sidebar.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.sidebar.image(image, caption="Uploaded Image", use_column_width=True)
        st.sidebar.write("Draw on the canvas to pick a color:")
        # Create a canvas component for drawing/selecting a point.
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
            stroke_width=3,
            stroke_color="#000000",
            background_image=image,
            update_streamlit=True,
            height=image.height//2,
            width=image.width//2,
            drawing_mode="point",
            key="canvas",
        )
        # If a point is drawn, use its coordinates to sample the image color.
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if len(objects) > 0:
                # Use the first drawn point's coordinates (rounding to int)
                obj = objects[0]
                x = int(obj["left"])
                y = int(obj["top"])
                # Adjust for scaling: assume the canvas is a scaled version of the original image.
                scale_x = image.width / (image.width//2)
                scale_y = image.height / (image.height//2)
                x_orig = int(x * scale_x)
                y_orig = int(y * scale_y)
                try:
                    target_rgb = image.convert("RGB").getpixel((x_orig, y_orig))
                    target_color = rgb_to_hex(target_rgb)
                    st.sidebar.write("Selected color from image:", target_color)
                except Exception as e:
                    st.sidebar.error("Error picking color: " + str(e))
    else:
        st.sidebar.write("Upload an image to select a color.")

if target_color:
    st.markdown(f"### Target Color: <span style='background-color:{target_color};padding:10px;'>{target_color}</span>", unsafe_allow_html=True)

st.markdown("---")
st.header("Customize Your Base Colors")
# Using session state to store dynamic list of base colors and ratios
if "base_colors" not in st.session_state:
    # Initialize with three default base colors and equal ratios
    st.session_state.base_colors = ["#ff0000", "#00ff00", "#0000ff"]
if "base_ratios" not in st.session_state:
    st.session_state.base_ratios = [33.33, 33.33, 33.34]

# Display each base color with a color picker and a slider for its ratio.
cols = st.columns(3)
for idx in range(len(st.session_state.base_colors)):
    with cols[idx % 3]:
        st.text(f"Base Color {idx+1}")
        new_color = st.color_picker("",
                                    value=st.session_state.base_colors[idx],
                                    key=f"color_{idx}")
        st.session_state.base_colors[idx] = new_color
        new_ratio = st.slider("Ratio (%)", 0.0, 100.0,
                              value=st.session_state.base_ratios[idx],
                              key=f"ratio_{idx}",
                              step=0.1)
        st.session_state.base_ratios[idx] = new_ratio
        # Provide a remove button for each color if more than one exists
        if st.button("Remove", key=f"remove_{idx}") and len(st.session_state.base_colors) > 1:
            st.session_state.base_colors.pop(idx)
            st.session_state.base_ratios.pop(idx)
            st.experimental_rerun()

# Button to add a new base color
if st.button("Add New Base Color"):
    st.session_state.base_colors.append("#ffffff")
    st.session_state.base_ratios.append(0.0)
    st.experimental_rerun()

# Real-time color mixing visualization
st.markdown("### Mixed Color Preview")
mixed_color = mix_colors(st.session_state.base_colors, st.session_state.base_ratios)
st.markdown(f"<div style='width:150px; height:150px; background-color:{mixed_color}; border:1px solid #000;'></div>", unsafe_allow_html=True)
st.write("Mixed Color HEX:", mixed_color)

st.markdown("---")
st.header("Generate Paint Recipes")
if st.button("Generate Recipes"):
    # Get current ratios
    base_ratios = st.session_state.base_ratios
    recipes = generate_recipe_variations(base_ratios)
    st.session_state.generated_recipes = recipes
    st.success("Recipes generated!")

if "generated_recipes" in st.session_state:
    st.subheader("Recipes")
    for i, recipe in enumerate(st.session_state.generated_recipes, start=1):
        # Calculate the mixed color for this recipe
        recipe_color = mix_colors(st.session_state.base_colors, recipe)
        st.markdown(f"#### Recipe {i}")
        for base, ratio in zip(st.session_state.base_colors, recipe):
            st.write(f"Color {base} at {ratio}%")
        st.markdown(f"**Mixed Color:** <span style='background-color:{recipe_color};padding:5px;'>{recipe_color}</span>", unsafe_allow_html=True)
        # Create a JSON for the recipe
        recipe_data = {
            "recipe": [{"color": base, "percentage": ratio} for base, ratio in zip(st.session_state.base_colors, recipe)],
            "mixed_color": recipe_color
        }
        json_str = json.dumps(recipe_data, indent=4)
        st.download_button(label="Download Recipe",
                           data=json_str,
                           file_name=f"recipe_{i}.json",
                           mime="application/json")
