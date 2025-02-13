import streamlit as st
import numpy as np
from PIL import Image, ImageColor, ImageDraw
from streamlit_drawable_canvas import st_canvas

############# UTILITY FUNCTIONS #############

def hex_to_rgb(hex_color):
    """Convert a HEX color string (e.g. '#ff0000') to an (R, G, B) tuple."""
    hex_color = hex_color.strip().lstrip('#')
    if len(hex_color) == 3:
        # e.g. 'f00' -> 'ff0000'
        hex_color = ''.join([ch*2 for ch in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """Convert an (R, G, B) tuple to a HEX string (e.g. '#ff0000')."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def parse_color_input(color_str):
    """
    Attempt to parse user input (which might be RGB or HEX).
    - If input starts with '#' or looks like a valid hex, parse as hex.
    - Else if input has commas, parse as 'R,G,B'.
    """
    color_str = color_str.strip()
    if color_str.startswith('#'):
        # Assume it's a valid hex
        return hex_to_rgb(color_str)
    elif ',' in color_str:
        # Parse as R,G,B
        parts = color_str.split(',')
        if len(parts) == 3:
            try:
                r = int(parts[0])
                g = int(parts[1])
                b = int(parts[2])
                # Clip to 0-255
                r = max(0, min(r, 255))
                g = max(0, min(g, 255))
                b = max(0, min(b, 255))
                return (r, g, b)
            except ValueError:
                pass
        return None
    else:
        # Try to parse as hex without '#'
        if len(color_str) in (3, 6):
            color_str = '#' + color_str
            return hex_to_rgb(color_str)
        return None

def mix_colors(base_colors, base_ratios):
    """
    Return the resulting color (as a HEX string) from mixing the base_colors
    with given percentages. base_colors is a list of HEX strings.
    base_ratios is a list of floats that sum up to ~100.
    """
    total = sum(base_ratios)
    if total == 0:
        return "#ffffff"
    mixed = np.array([0.0, 0.0, 0.0])
    for c_hex, ratio in zip(base_colors, base_ratios):
        c_rgb = np.array(hex_to_rgb(c_hex))
        mixed += (ratio/total) * c_rgb
    mixed = np.clip(mixed, 0, 255).astype(int)
    return rgb_to_hex(tuple(mixed))

def color_distance(rgb1, rgb2):
    """
    Simple Euclidean distance in RGB space.
    """
    return np.sqrt((rgb1[0]-rgb2[0])**2 + (rgb1[1]-rgb2[1])**2 + (rgb1[2]-rgb2[2])**2)

def find_two_recipes(target_rgb, base_colors, max_tries=2000):
    """
    Generate 2 different recipes (sets of percentages) that produce
    a color close to target_rgb when mixing the given base_colors.

    We'll do a simple random search, picking random distributions of
    the base colors, then keep track of the best two distinct solutions.
    """
    n = len(base_colors)
    best_solutions = []  # list of (distance, [ratios])

    for _ in range(max_tries):
        # Random ratios that sum to 100
        raw = np.random.rand(n)
        if raw.sum() == 0:
            raw = np.ones(n)
        ratios = (raw / raw.sum()) * 100
        # Mix
        c_hex = mix_colors(base_colors, ratios)
        c_rgb = hex_to_rgb(c_hex)
        dist = color_distance(target_rgb, c_rgb)

        # Keep track of top 2 solutions
        if len(best_solutions) < 2:
            best_solutions.append((dist, ratios))
            best_solutions.sort(key=lambda x: x[0])
        else:
            # Compare with the worst of the top 2
            if dist < best_solutions[-1][0]:
                best_solutions[-1] = (dist, ratios)
                best_solutions.sort(key=lambda x: x[0])

    return [sol[1] for sol in best_solutions]

############# STREAMLIT APP #############

st.set_page_config(page_title="PaintMaker Demo", layout="wide")
st.title("PaintMaker Demo")

# Session state initialization
if "base_colors" not in st.session_state:
    # Default to 3 base colors
    st.session_state.base_colors = ["#ff0000", "#00ff00", "#0000ff"]
if "base_ratios" not in st.session_state:
    st.session_state.base_ratios = [33.33, 33.33, 33.34]

#####################
# 1. BASE COLOR MIX #
#####################
st.header("1. Simple Color Mixing")
st.write("Add or remove base colors, set their percentages, and see the mixed color below.")

# Display base colors in a layout
cols = st.columns([2,2,2,1])  # 3 wide columns + 1 narrower column for 'Add color' button
num_colors = len(st.session_state.base_colors)

# We'll handle add/remove in a form to avoid partial re-runs
with st.form("base_color_form"):
    # Each color gets a row
    for i in range(num_colors):
        with st.expander(f"Base Color {i+1}", expanded=True):
            c1, c2 = st.columns([2,3])
            with c1:
                new_color = st.color_picker("Pick a color", 
                                            key=f"base_color_{i}",
                                            value=st.session_state.base_colors[i])
            with c2:
                new_ratio = st.slider("Percentage (%)",
                                      0.0, 100.0,
                                      st.session_state.base_ratios[i],
                                      0.1,
                                      key=f"base_ratio_{i}")
            # If user changed anything, update session state
            st.session_state.base_colors[i] = new_color
            st.session_state.base_ratios[i] = new_ratio

            # Remove button
            if st.button("Remove this color", key=f"remove_{i}") and len(st.session_state.base_colors) > 1:
                st.session_state.base_colors.pop(i)
                st.session_state.base_ratios.pop(i)
                st.experimental_rerun()

    st.form_submit_button("Apply changes")

# "Add color" button outside the form
if cols[-1].button("Add Base Color"):
    st.session_state.base_colors.append("#ffffff")
    st.session_state.base_ratios.append(0.0)
    st.experimental_rerun()

# Show the resulting mix
mixed_hex = mix_colors(st.session_state.base_colors, st.session_state.base_ratios)
st.write("**Mixed Color Preview:**")
st.markdown(f"<div style='width:100px; height:50px; background-color:{mixed_hex};'></div>", unsafe_allow_html=True)
st.write(f"HEX: {mixed_hex}")

###################################################
# 2. INPUT A TARGET COLOR (HEX or RGB) -> RECIPES #
###################################################
st.header("2. Generate Recipes for a Target Color")
st.write("Enter a target color (HEX or RGB), then generate 2 different recipes that approximate it using your base colors.")

col_left, col_right = st.columns([2,3])
with col_left:
    color_input = st.text_input("Enter a color (e.g. '#123456' or '120, 30, 255')", "#123456")
    generate_button = st.button("Generate 2 Recipes")

with col_right:
    if generate_button:
        parsed_rgb = parse_color_input(color_input)
        if not parsed_rgb:
            st.error("Invalid color format. Please enter a valid HEX (e.g. '#abc123') or RGB (e.g. '255, 100, 50').")
        else:
            # Generate 2 recipes
            solutions = find_two_recipes(parsed_rgb, st.session_state.base_colors)
            st.subheader(f"Recipes for {color_input}")
            for idx, recipe in enumerate(solutions, start=1):
                # Show the recipe
                c_hex = mix_colors(st.session_state.base_colors, recipe)
                st.markdown(f"**Recipe {idx}:** Mixed color = {c_hex}")
                # Show bars for each color
                for bc, r in zip(st.session_state.base_colors, recipe):
                    st.write(f"• {bc} : {round(r,2)}%")
                st.markdown("---")

############################################
# 3. UPLOAD IMAGE & SELECT COLOR -> RECIPE #
############################################
st.header("3. Upload an Image and Pick a Color")
uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    st.write("Use the canvas below to click on the color you want. The point tool will add a dot; we read its coordinates and sample the color.")
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=3,
        stroke_color="#000000",
        background_image=img,
        update_streamlit=True,
        height= min(400, img.height),
        width= min(600, img.width),
        drawing_mode="point",
        key="canvas_image",
    )
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        if len(objects) > 0:
            # We'll use the last drawn point
            obj = objects[-1]
            x = int(obj["left"])
            y = int(obj["top"])
            # Adjust for possible scaling
            scale_x = img.width / min(600, img.width)
            scale_y = img.height / min(400, img.height)
            x_orig = int(x * scale_x)
            y_orig = int(y * scale_y)
            if 0 <= x_orig < img.width and 0 <= y_orig < img.height:
                selected_rgb = img.getpixel((x_orig, y_orig))
                st.write(f"Selected color (RGB): {selected_rgb}")
                # Generate 2 recipes for that color
                if st.button("Generate 2 Recipes from Selected Color"):
                    solutions = find_two_recipes(selected_rgb, st.session_state.base_colors)
                    st.subheader(f"Recipes for {selected_rgb}")
                    for idx, recipe in enumerate(solutions, start=1):
                        c_hex = mix_colors(st.session_state.base_colors, recipe)
                        st.markdown(f"**Recipe {idx}:** Mixed color = {c_hex}")
                        for bc, r in zip(st.session_state.base_colors, recipe):
                            st.write(f"• {bc} : {round(r,2)}%")
                        st.markdown("---")
            else:
                st.warning("Point is out of image bounds. Try again.")
