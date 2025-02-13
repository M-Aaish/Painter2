import streamlit as st
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

############# UTILITY FUNCTIONS #############

def hex_to_rgb(hex_color):
    """Convert a HEX color (e.g. '#ff00ff') to an (R,G,B) tuple."""
    hex_color = hex_color.strip().lstrip('#')
    if len(hex_color) == 3:
        # short form like '#f0a' -> '#ff00aa'
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
        # Likely hex
        try:
            return hex_to_rgb(color_str)
        except:
            return None
    elif ',' in color_str:
        # Possibly 'R,G,B'
        parts = color_str.split(',')
        if len(parts) == 3:
            try:
                r = int(parts[0])
                g = int(parts[1])
                b = int(parts[2])
                r, g, b = max(0, min(r,255)), max(0, min(g,255)), max(0, min(b,255))
                return (r, g, b)
            except:
                return None
    else:
        # Maybe hex without '#'
        if len(color_str) in [3, 6]:
            try:
                return hex_to_rgb('#' + color_str)
            except:
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
    best_solutions = []  # will store tuples of (distance, [ratios])
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
            # Compare with worst of the top 2
            if dist < best_solutions[-1][0]:
                best_solutions[-1] = (dist, ratios)
                best_solutions.sort(key=lambda x: x[0])
    return [sol[1] for sol in best_solutions]

############# FEATURE FUNCTIONS #############

def feature_simple_mixing():
    """
    Redesigned Simple Color Mixing:
    - Always start with three base colors if none in session state.
    - Button to add new color.
    - Changing a color or ratio updates the preview immediately.
    """
    st.header("Simple Color Mixing (Redesigned)")
    st.write("We start with three base colors. You can add or remove colors, adjust their percentages, and see the mixed color in real time.")

    # 1) Session state init
    if "mix_colors" not in st.session_state:
        st.session_state.mix_colors = ["#ff0000", "#00ff00", "#0000ff"]
    if "mix_ratios" not in st.session_state:
        st.session_state.mix_ratios = [33.33, 33.33, 33.34]

    # 2) Display each color in a loop
    i = 0
    while i < len(st.session_state.mix_colors):
        col1, col2, col3 = st.columns([3, 3, 1])
        # Color picker
        new_color = col1.color_picker(
            label=f"Color {i+1}",
            value=st.session_state.mix_colors[i],
            key=f"mix_col_{i}"
        )
        # Ratio slider
        new_ratio = col2.slider(
            "Percentage (%)",
            0.0, 100.0,
            value=st.session_state.mix_ratios[i],
            step=0.1,
            key=f"mix_ratio_{i}"
        )
        st.session_state.mix_colors[i] = new_color
        st.session_state.mix_ratios[i] = new_ratio

        # Remove button
        if col3.button("Remove", key=f"remove_{i}") and len(st.session_state.mix_colors) > 1:
            st.session_state.mix_colors.pop(i)
            st.session_state.mix_ratios.pop(i)
            st.experimental_rerun()
        else:
            i += 1

    # 3) Button to add another color
    if st.button("Add another color"):
        st.session_state.mix_colors.append("#ffffff")
        st.session_state.mix_ratios.append(0.0)
        st.experimental_rerun()

    # 4) Compute the mixed color in real time
    mixed_hex = mix_colors(st.session_state.mix_colors, st.session_state.mix_ratios)
    st.write("**Mixed Color Preview:**")
    st.markdown(
        f"<div style='width:150px; height:50px; background-color:{mixed_hex}; border:1px solid #000;'></div>",
        unsafe_allow_html=True
    )
    st.write(f"Resulting HEX: {mixed_hex}")

def feature_target_recipe():
    """
    2) Generate Recipes for a Target Color
    - User inputs a color (HEX or RGB)
    - We find 2 different sets of base color ratios that approximate that color
    """
    st.header("Generate Recipes for a Target Color")

    # Ensure base colors exist
    if "mix_colors" not in st.session_state:
        st.session_state.mix_colors = ["#ff0000", "#00ff00", "#0000ff"]
    if "mix_ratios" not in st.session_state:
        st.session_state.mix_ratios = [33.33, 33.33, 33.34]

    color_str = st.text_input("Enter a color (HEX or RGB)", value="#123456", key="target_color_input")
    if st.button("Generate 2 Recipes", key="generate_target_recipe"):
        target_rgb = parse_color_input(color_str)
        if not target_rgb:
            st.error("Invalid color format. Please enter #aabbcc or 255,100,50, etc.")
        else:
            # Do the random search for 2 solutions
            solutions = find_two_recipes(target_rgb, st.session_state.mix_colors)
            st.subheader(f"Recipes for {color_str}")
            for idx, recipe in enumerate(solutions, start=1):
                mix_hex = mix_colors(st.session_state.mix_colors, recipe)
                st.markdown(f"**Recipe {idx}** -> Mixed color: {mix_hex}")
                for bc, perc in zip(st.session_state.mix_colors, recipe):
                    st.write(f"• {bc}: {round(perc,2)}%")
                st.markdown("---")

def feature_image_recipe():
    """
    3) Upload an Image & Pick a Color
    - Upload image
    - Click to pick color from the canvas (requires background_image).
    - Generate 2 recipes for the picked color
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

        # Display the image
        st.image(image, caption="Uploaded Image", use_container_width=True)

        st.write("Click on the image below to pick a color (use the point tool).")

        # Canvas size constraints
        canvas_width = min(image.width, 600)
        canvas_height = min(image.height, 400)

        # If the following call triggers an error about 'image_to_url',
        # try pinning streamlit and streamlit_drawable-canvas versions,
        # or remove `background_image=image`.
        canvas_result = st_canvas(
            fill_color="rgba(255,165,0,0.3)",
            stroke_width=3,
            stroke_color="#000000",
            background_image=image,
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode="point",
            key="canvas_image_feature",
        )

        if canvas_result.json_data is not None:
            objects = canvas_result.json_data.get("objects", [])
            if objects:
                # We'll use the last point object
                last_obj = objects[-1]
                x = int(last_obj.get("left", 0))
                y = int(last_obj.get("top", 0))

                # Adjust for scaling
                scale_x = image.width / canvas_width
                scale_y = image.height / canvas_height
                x_orig = int(x * scale_x)
                y_orig = int(y * scale_y)

                if 0 <= x_orig < image.width and 0 <= y_orig < image.height:
                    picked_rgb = image.getpixel((x_orig, y_orig))
                    st.write(f"Picked Color (RGB): {picked_rgb}")
                    if st.button("Generate 2 Recipes for Picked Color"):
                        solutions = find_two_recipes(picked_rgb, st.session_state.mix_colors)
                        st.subheader(f"Recipes for {picked_rgb}")
                        for idx, recipe in enumerate(solutions, start=1):
                            mix_hex = mix_colors(st.session_state.mix_colors, recipe)
                            st.markdown(f"**Recipe {idx}** -> Mixed color: {mix_hex}")
                            for bc, perc in zip(st.session_state.mix_colors, recipe):
                                st.write(f"• {bc}: {round(perc,2)}%")
                            st.markdown("---")
                else:
                    st.warning("The selected point is outside the image bounds. Try clicking within the image area.")
            else:
                st.info("Use the point tool and click on the image to pick a color.")

############# MAIN APP #############

st.set_page_config(page_title="PaintMaker Demo", layout="wide")
st.title("PaintMaker Demo")

# Layout: main column + right column for feature selection
col_main, col_right = st.columns([3,1])

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
