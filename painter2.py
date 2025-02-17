import streamlit as st
import itertools
import math
import numpy as np

# Set page config as the very first Streamlit command.
st.set_page_config(page_title="Painter App", layout="wide")

# -----------------------------
# Read the color database from a text file.
# -----------------------------
@st.cache_data
def read_color_file(filename="color.txt"):
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception as e:
        st.error("Error reading color.txt: " + str(e))
        return ""

# -----------------------------
# Parsing function: reads the text and creates a dictionary of databases.
# -----------------------------
def parse_color_db(txt):
    databases = {}
    current_db = None
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        # If the line doesn't start with a digit, treat it as a header (database name)
        if not line[0].isdigit():
            current_db = line
            databases[current_db] = []
        else:
            tokens = line.split()
            # First token is an index, last token is the RGB string, rest form the color name.
            index = tokens[0]
            rgb_str = tokens[-1]
            color_name = " ".join(tokens[1:-1])
            try:
                r, g, b = [int(x) for x in rgb_str.split(",")]
            except Exception:
                continue
            databases[current_db].append((color_name, (r, g, b)))
    return databases

# Read and parse the file.
color_txt = read_color_file("color.txt")
databases = parse_color_db(color_txt)

# -----------------------------
# Helper: convert a list of (name, rgb) tuples into a dictionary format.
# -----------------------------
def convert_db_list_to_dict(color_list):
    d = {}
    for name, rgb in color_list:
        d[name] = {"rgb": list(rgb)}
    return d

# -----------------------------
# Helper functions.
# -----------------------------
def rgb_to_hex(r, g, b):
    """Convert RGB (0-255) to hex string."""
    return f'#{r:02x}{g:02x}{b:02x}'

def mix_colors(recipe):
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
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def generate_recipes(target, base_colors_dict, step=10.0):
    """
    Generate candidate recipes from 3-color combinations using only base colors
    from the selected database.
    'step' is the percentage increment.
    Returns a list of tuples (recipe, mixed_color, error).
    Each recipe is a list of tuples (base_color_name, percentage).
    """
    candidates = []
    base_list = [(name, info["rgb"]) for name, info in base_colors_dict.items()]
    
    # Special case: if any base color nearly matches the target.
    for name, rgb in base_list:
        err = color_error(tuple(rgb), target)
        if err < 5:
            recipe = [(name, 100.0)]
            candidates.append((recipe, tuple(rgb), err))
    
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
    candidates.sort(key=lambda x: x[2])
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
    hex_color = rgb_to_hex(*color)
    st.markdown(
        f"<div style='background-color: {hex_color}; width:100px; height:100px; border:1px solid #000; text-align: center; line-height: 100px;'>{label}</div>",
        unsafe_allow_html=True,
    )

# Helper: display a thin rectangle for color visualization.
def display_thin_color_block(color):
    hex_color = rgb_to_hex(*color)
    st.markdown(
        f"<div style='background-color: {hex_color}; width:50px; height:20px; border:1px solid #000; display:inline-block; margin-right:10px;'></div>",
        unsafe_allow_html=True,
    )

# -----------------------------
# Colors DataBase Subpage: "Data Bases"
# -----------------------------
def show_databases_page():
    st.title("Color Database - Data Bases")
    selected_db = st.selectbox("Select a color database:", list(databases.keys()))
    st.write(f"### Colors in database: {selected_db}")
    for name, rgb in databases[selected_db]:
        st.write(f"**{name}**: {rgb_to_hex(*rgb)} ({rgb[0]},{rgb[1]},{rgb[2]})", unsafe_allow_html=True)
        display_thin_color_block(rgb)

# -----------------------------
# Main app navigation
# -----------------------------
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", ["Recipe Generator", "Colors DataBase"])
    
    if page == "Recipe Generator":
        st.title("Painter App - Recipe Generator")
        st.write("Enter your desired paint color to generate paint recipes using base colors.")
        
        # Dropdown to select a database.
        db_choice = st.selectbox("Select a color database:", list(databases.keys()))
        selected_db_dict = convert_db_list_to_dict(databases[db_choice])
        
        # Input method for desired color.
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
        
        # Slider to select percentage step (values between 4 and 10).
        step = st.slider("Select percentage step for recipe generation:", 4.0, 10.0, 10.0, step=0.5)
        
        if st.button("Generate Recipes"):
            recipes = generate_recipes(desired_rgb, selected_db_dict, step=step)
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
                                base_rgb = tuple(selected_db_dict[name]["rgb"])
                                st.write(f"- **{name}**: {perc:.1f}%")
                                display_color_block(base_rgb, label=name)
                    with cols[3]:
                        st.write("Difference:")
                        st.write(f"RGB Distance: {err:.2f}")
            else:
                st.error("No recipes found.")
    
    elif page == "Colors DataBase":
        st.title("Colors DataBase")
        st.write("Select an action:")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Data Bases"):
                show_databases_page()
        with col2:
            if st.button("Add Colors"):
                st.write("Interface to add colors to a database (coming soon).")
        with col3:
            if st.button("Create Custom Data Base"):
                st.write("Interface to create a custom color database (coming soon).")

if __name__ == "__main__":
    main()
