import streamlit as st
import numpy as np
from PIL import Image
import base64
from streamlit_drawable_canvas import st_canvas
from io import BytesIO

############# UTILITY FUNCTIONS #############

def pil_image_to_data_url(img):
    """Convert a PIL image to a base64 data URL."""
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    data = buffer.getvalue()
    data_url = "data:image/png;base64," + base64.b64encode(data).decode()
    return data_url

def hex_to_rgb(hex_color):
    """Convert a HEX color (e.g. '#ff00ff') to an (R,G,B) tuple."""
    hex_color = hex_color.strip().lstrip('#')
    if len(hex_color) == 3:
        # Expand shorthand (e.g. 'f0a' -> 'ff00aa')
        hex_color = ''.join([ch * 2 for ch in hex_color])
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """Convert an (R,G,B) tuple to a HEX color (e.g. '#ff00ff')."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def parse_color_input(color_str):
    """
    Parse a user-input string as either:
      - HEX: '#ff00ff' or 'ff00ff' or '#abc' or 'abc'
      - RGB: '255,0,255'
    Returns an (R,G,B) tuple or None if invalid.
    """
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
                return (max(0, min(r, 255)), max(0, min(g, 255)), max(0, min(b, 255)))
            except Exception:
                return None
    else:
        if len(color_str) in [3, 6]:
            try:
                return hex_to_rgb('#' + color_str)
            except Exception:
                return None
    return None

def mix_colors(base_colors, base_ratios):
    """
    Given a list of HEX colors and a list of percentages,
    compute the resulting mixed color in HEX.
    """
    total = sum(base_ratios)
    if total == 0:
        return "#ffffff"
    mix_rgb = np.array([0.0, 0.0, 0.0])
    for c_hex, ratio in zip(base_colors, base_ratios):
        rgb = np.array(hex_to_rgb(c_hex))
        mix_rgb += (ratio / total) * rgb
    mix_rgb = np.clip(mix_rgb, 0, 255).astype(int)
    return rgb_to_hex(tuple(mix_rgb))

def color_distance(rgb1, rgb2):
    """Euclidean distance in RGB space."""
    return np.sqrt((rgb1[0] - rgb2[0])**2 + (rgb1[1] - rgb2[1])**2 + (rgb1[2] - rgb2[2])**2)

def find_two_recipes(target_rgb, base_colors, max_tries=2000):
    """
    Simple random search to find 2 sets of ratios that produce
    a color close to target_rgb when mixing the given base_colors.
    """
    n = len(base_colors)
    best_solutions = []  # List of tuples: (distance, ratios)
    for _ in range(max_tries):
        raw = np.random.rand(n)
        if raw.sum() == 0:
            raw = np.ones(n)
        ratios = (raw / raw.sum()) * 100
        candidate_hex = mix_colors(base_colors, ratios)
        candidate_rgb = hex_to_rgb(candidate_hex)
        dist = color_distance(target_rgb, candidate_rgb)
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
    """
    Redesigned Simple Color Mixing:
      - Start with three base colors.
      - Use a form to adjust colors and percentages.
      - Option to add another color or remove an existing one.
      - Updates the mixed color after clicking “Apply changes.”
    """
    st.header("Simple Color Mixing (Redesigned)")
    st.write("We start with three base colors. Adjust their percentages, add new colors, or remove them, then click 'Apply changes' to update the mix.")

    # Initialize session state for base colors if not set.
    if "mix_colors" not in st.session_state:
        st.session_state.mix_colors = ["#ff0000", "#00ff00", "#0000ff"]
    if "mix_ratios" not in st.session_state:
        st.session_state.mix_ratios = [33.33, 33.33, 33.34]

    with st.form("mixing_form"):
        new_colors = []
        new_ratios = []
        remove_indices = []
        st.write("**Edit your base colors:**")
        for i, color in enumerate(st.session_state.mix_colors):
            col1, col2, col3 = st.columns([3, 3, 1])
            c = col1.color_picker(f"Color {i+1}", value=color, key=f"mix_color_{i}")
            r = col2.slider("Percentage (%)", 0.0, 100.0,
                            value=st.session_state.mix_ratios[i],
                            step=0.1, key=f"mix_ratio_{i}")
            remove = col3.checkbox("Remove", key=f"mix_remove_{i}")
            new_colors.append(c)
            new_ratios.append(r)
            if remove:
                remove_indices.append(i)
        add_color = st.checkbox("Add another color", key="add_color_checkbox")
        submitted = st.form_submit_button("Apply changes")
        if submitted:
            # Remove selected colors (in reverse order to avoid index shifting)
            for idx in sorted(remove_indices, reverse=True):
                if len(new_colors) > 1:  # Ensure at least one color remains
                    del new_colors[idx]
                    del new_ratios[idx]
            if add_color:
                new_colors.append("#ffffff")
                new_ratios.append(0.0)
            st.session_state.mix_colors = new_colors
            st.session_state.mix_ratios = new_ratios

    st.write("### Current Base Colors:")
    for i, (c, r) in enumerate(zip(st.session_state.mix_colors, st.session_state.mix_ratios)):
        st.write(f"**Color {i+1}:** {c} — **Percentage:** {r}%")
    mixed_hex = mix_colors(st.session_state.mix_colors, st.session_state.mix_ratios)
    st.write("**Mixed Color Preview:**")
    st.markdown(f"<div style='width:150px; height:50px; background-color:{mixed_hex}; border:1px solid #000;'></div>", unsafe_allow_html=True)
    st.write(f"Resulting HEX: {mixed_hex}")

def feature_target_recipe():
    """
    Generate Recipes for a Target Color:
      - Enter a target color (HEX or RGB).
      - Generates 2 candidate recipes using the current base colors.
    """
    st.header("Generate Recipes for a Target Color")
    if "mix_colors" not in st.session_state:
        st.session_state.mix_colors = ["#ff0000", "#00ff00", "#0000ff"]
    if "mix_ratios" not in st.session_state:
        st.session_state.mix_ratios = [33.33, 33.33, 33.34]

    color_str = st.text_input("Enter a target color (HEX or RGB)", value="#123456", key="target_color_input")
    if st.button("Generate 2 Recipes", key="generate_target_recipe"):
        target_rgb = parse_color_input(color_str)
        if not target_rgb:
            st.error("Invalid color format. Please enter a HEX value (e.g. #aabbcc) or an RGB value (e.g. 255,100,50).")
        else:
            recipes = find_two_recipes(target_rgb, st.session_state.mix_colors)
            st.subheader(f"Recipes for {color_str}")
            for idx, recipe in enumerate(recipes, start=1):
                mix_hex = mix_colors(st.session_state.mix_colors, recipe)
                st.markdown(f"**Recipe {idx}:** Mixed color = {mix_hex}")
                for bc, perc in zip(st.session_state.mix_colors, recipe):
                    st.write(f"• {bc}: {round(perc, 2)}%")
                st.markdown("---")

def feature_image_recipe():
    """
    Upload an Image & Pick a Color:
      - Upload an image.
      - The canvas displays the image (using a data URL) so you can click to pick a color.
      - Generates 2 recipes for the picked color.
    """
    st.header("Upload an Image & Pick a Color")
    if "mix_colors" not in st.session_state:
        st.session_state.mix_colors = ["#ff0000", "#00ff00", "#0000ff"]
    if "mix_ratios" not in st.session_state:
        st.session_state.mix_ratios = [33.33, 33.33, 33.34]

    uploaded_file = st.file_uploader("Upload an image (PNG/JPG)", type=["png", "jpg", "jpeg"], key="image_upload")
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file).convert("RGB")
        except Exception as e:
            st.error(f"Could not open image: {e}")
            return

        # Show the image for reference.
        st.image(image, caption="Uploaded Image", use_container_width=True)
        st.write("Click on the canvas below (using the point tool) to pick a color from the image.")

        # Convert the image to a data URL for the canvas background.
        img_url = pil_image_to_data_url(image)
        canvas_width = min(image.width, 600)
        canvas_height = min(image.height, 400)
        canvas_result = st_canvas(
            fill_color="rgba(255,165,0,0.3)",
            stroke_width=3,
            stroke_color="#000000",
            background_image=img_url,
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode="point",
            key="canvas_image_feature",
        )

        if canvas_result.json_data is not None:
            objects = canvas_result.json_data.get("objects", [])
            if objects:
                # Use the last drawn point.
                last_obj = objects[-1]
                x = int(last_obj.get("left", 0))
                y = int(last_obj.get("top", 0))
                # Adjust coordinates to match original image size.
                scale_x = image.width / canvas_width
                scale_y = image.height / canvas_height
                x_orig = int(x * scale_x)
                y_orig = int(y * scale_y)
                if 0 <= x_orig < image.width and 0 <= y_orig < image.height:
                    picked_rgb = image.getpixel((x_orig, y_orig))
                    st.write(f"Picked Color (RGB): {picked_rgb}")
                    if st.button("Generate 2 Recipes for Picked Color"):
                        recipes = find_two_recipes(picked_rgb, st.session_state.mix_colors)
                        st.subheader(f"Recipes for {picked_rgb}")
                        for idx, recipe in enumerate(recipes, start=1):
                            mix_hex = mix_colors(st.session_state.mix_colors, recipe)
                            st.markdown(f"**Recipe {idx}:** Mixed color = {mix_hex}")
                            for bc, perc in zip(st.session_state.mix_colors, recipe):
                                st.write(f"• {bc}: {round(perc, 2)}%")
                            st.markdown("---")
                else:
                    st.warning("The selected point is outside the image bounds. Please click within the image area.")
            else:
                st.info("Use the point tool and click on the image to pick a color.")

############# MAIN APP #############

st.set_page_config(page_title="PaintMaker Demo", layout="wide")
st.title("PaintMaker Demo")

# Two-column layout: main content + feature selection on the right.
col_main, col_right = st.columns([3, 1])
with col_right:
    feature_choice = st.selectbox(
        "Select Feature",
        [
            "Simple Color Mixing",
            "Generate Recipes for a Target Color",
            "Upload an Image & Pick a Color"
        ]
    )

with col_main:
    if feature_choice == "Simple Color Mixing":
        feature_simple_mixing()
    elif feature_choice == "Generate Recipes for a Target Color":
        feature_target_recipe()
    elif feature_choice == "Upload an Image & Pick a Color":
        feature_image_recipe()
