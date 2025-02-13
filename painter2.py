import streamlit as st
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

############# UTILITY FUNCTIONS #############
def hex_to_rgb(hex_color):
    hex_color = hex_color.strip().lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([ch * 2 for ch in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def parse_color_input(color_str):
    """Parse user input as HEX (e.g. "#123456") or RGB (e.g. "255,100,50")."""
    color_str = color_str.strip()
    if color_str.startswith('#'):
        try:
            return hex_to_rgb(color_str)
        except Exception:
            return None
    elif ',' in color_str:
        parts = color_str.split(',')
        if len(parts) == 3:
            try:
                r = int(parts[0])
                g = int(parts[1])
                b = int(parts[2])
                return (max(0, min(r,255)), max(0, min(g,255)), max(0, min(b,255)))
            except ValueError:
                return None
    else:
        # Try to interpret without '#'
        if len(color_str) in [3, 6]:
            return hex_to_rgb("#" + color_str)
    return None

def mix_colors(base_colors, base_ratios):
    """Compute the mixed color (HEX) from base colors and their percentage ratios."""
    total = sum(base_ratios)
    if total == 0:
        return "#ffffff"
    mixed = np.array([0.0, 0.0, 0.0])
    for c_hex, ratio in zip(base_colors, base_ratios):
        rgb = np.array(hex_to_rgb(c_hex))
        mixed += (ratio / total) * rgb
    mixed = np.clip(mixed, 0, 255).astype(int)
    return rgb_to_hex(tuple(mixed))

def color_distance(rgb1, rgb2):
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))

def find_two_recipes(target_rgb, base_colors, max_tries=2000):
    """
    Use a simple random search to generate 2 distinct recipes (percentage mixes)
    that, when combined, are close in RGB space to the target_rgb.
    """
    n = len(base_colors)
    best_solutions = []  # list of tuples (distance, [ratios])
    for _ in range(max_tries):
        raw = np.random.rand(n)
        if raw.sum() == 0:
            raw = np.ones(n)
        ratios = (raw / raw.sum()) * 100
        mixed_hex = mix_colors(base_colors, ratios)
        mixed_rgb = hex_to_rgb(mixed_hex)
        dist = color_distance(target_rgb, mixed_rgb)
        if len(best_solutions) < 2:
            best_solutions.append((dist, ratios))
            best_solutions.sort(key=lambda x: x[0])
        else:
            if dist < best_solutions[-1][0]:
                best_solutions[-1] = (dist, ratios)
                best_solutions.sort(key=lambda x: x[0])
    return [sol[1] for sol in best_solutions]

############# FEATURE FUNCTIONS #############
def feature_simple_mixing():
    st.header("Simple Color Mixing")
    st.write("Add or remove base colors, adjust their percentages, and view the live mixed color.")

    # Initialize session state for base colors if needed
    if "base_colors" not in st.session_state:
        st.session_state.base_colors = ["#ff0000", "#00ff00", "#0000ff"]
    if "base_ratios" not in st.session_state:
        st.session_state.base_ratios = [33.33, 33.33, 33.34]

    # Display each base color with a color picker and a slider.
    for i in range(len(st.session_state.base_colors)):
        with st.expander(f"Base Color {i+1}", expanded=True):
            col1, col2, col3 = st.columns([2, 3, 1])
            new_color = col1.color_picker("Color", value=st.session_state.base_colors[i], key=f"simple_color_{i}")
            new_ratio = col2.slider("Percentage (%)", 0.0, 100.0, value=st.session_state.base_ratios[i], key=f"simple_ratio_{i}", step=0.1)
            st.session_state.base_colors[i] = new_color
            st.session_state.base_ratios[i] = new_ratio
            # Remove button: refresh if color is removed
            if col3.button("Remove", key=f"simple_remove_{i}") and len(st.session_state.base_colors) > 1:
                st.session_state.base_colors.pop(i)
                st.session_state.base_ratios.pop(i)
                st.experimental_rerun()

    # Button to add a new base color
    if st.button("Add Base Color"):
        st.session_state.base_colors.append("#ffffff")
        st.session_state.base_ratios.append(0.0)
        st.experimental_rerun()

    # Show the mixed color preview.
    mixed = mix_colors(st.session_state.base_colors, st.session_state.base_ratios)
    st.write("**Mixed Color Preview:**")
    st.markdown(f"<div style='width:150px; height:100px; background-color:{mixed}; border:1px solid #000;'></div>", unsafe_allow_html=True)
    st.write("Mixed Color HEX:", mixed)

def feature_target_recipe():
    st.header("Generate Recipes for a Target Color")
    st.write("Enter a target color (HEX or RGB) and click the button to generate 2 recipes that approximate it using your base colors.")

    # Ensure base colors exist in session state.
    if "base_colors" not in st.session_state:
        st.session_state.base_colors = ["#ff0000", "#00ff00", "#0000ff"]
    if "base_ratios" not in st.session_state:
        st.session_state.base_ratios = [33.33, 33.33, 33.34]

    color_input = st.text_input("Enter target color (e.g. '#123456' or '255,100,50')", "#123456", key="target_color_input")
    if st.button("Generate Recipes", key="generate_target_recipe"):
        target_rgb = parse_color_input(color_input)
        if not target_rgb:
            st.error("Invalid color format. Please enter a HEX value (e.g. #aabbcc) or RGB value (e.g. 255,100,50).")
        else:
            recipes = find_two_recipes(target_rgb, st.session_state.base_colors)
            st.subheader(f"Recipes for {color_input}")
            for idx, recipe in enumerate(recipes, start=1):
                rec_hex = mix_colors(st.session_state.base_colors, recipe)
                st.markdown(f"**Recipe {idx}:** Mixed color = {rec_hex}")
                for bc, perc in zip(st.session_state.base_colors, recipe):
                    st.write(f"• {bc}: {round(perc, 2)}%")
                st.markdown("---")

def feature_image_recipe():
    st.header("Upload an Image & Pick a Color")
    st.write("Upload an image, click on the color you want, and then generate 2 recipes for that selected color using your base colors.")

    # Ensure base colors exist.
    if "base_colors" not in st.session_state:
        st.session_state.base_colors = ["#ff0000", "#00ff00", "#0000ff"]
    if "base_ratios" not in st.session_state:
        st.session_state.base_ratios = [33.33, 33.33, 33.34]

    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"], key="image_upload")
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Uploaded Image", use_column_width=True)
        st.write("Click on the image below to pick a color:")
        canvas_result = st_canvas(
            fill_color="rgba(255,165,0,0.3)",
            stroke_width=3,
            stroke_color="#000000",
            background_image=image,
            update_streamlit=True,
            height=min(400, image.height),
            width=min(600, image.width),
            drawing_mode="point",
            key="canvas_image_feature",
        )
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data.get("objects", [])
            if objects:
                # Use the last drawn point
                point = objects[-1]
                x = int(point.get("left", 0))
                y = int(point.get("top", 0))
                scale_x = image.width / min(600, image.width)
                scale_y = image.height / min(400, image.height)
                x_orig = int(x * scale_x)
                y_orig = int(y * scale_y)
                if 0 <= x_orig < image.width and 0 <= y_orig < image.height:
                    picked_color = image.getpixel((x_orig, y_orig))
                    st.write(f"Picked color (RGB): {picked_color}")
                    if st.button("Generate Recipes for Picked Color", key="generate_image_recipe"):
                        recipes = find_two_recipes(picked_color, st.session_state.base_colors)
                        st.subheader(f"Recipes for picked color {picked_color}")
                        for idx, recipe in enumerate(recipes, start=1):
                            rec_hex = mix_colors(st.session_state.base_colors, recipe)
                            st.markdown(f"**Recipe {idx}:** Mixed color = {rec_hex}")
                            for bc, perc in zip(st.session_state.base_colors, recipe):
                                st.write(f"• {bc}: {round(perc, 2)}%")
                            st.markdown("---")
                else:
                    st.warning("Selected point is outside the image bounds.")
            else:
                st.info("Click on the image to select a color.")

############# MAIN APP STRUCTURE #############
st.set_page_config(page_title="PaintMaker Demo", layout="wide")
st.title("PaintMaker Demo")

# Create two columns: one for the main content and a narrow one for feature selection.
col_main, col_right = st.columns([3, 1])
with col_right:
    feature = st.selectbox(
        "Select Feature",
        options=[
            "Simple Color Mixing",
            "Generate Recipes for a Target Color",
            "Upload an Image & Pick a Color"
        ]
    )

# Render the selected feature in the main column.
with col_main:
    if feature == "Simple Color Mixing":
        feature_simple_mixing()
    elif feature == "Generate Recipes for a Target Color":
        feature_target_recipe()
    elif feature == "Upload an Image & Pick a Color":
        feature_image_recipe()
