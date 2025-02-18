import streamlit as st
import itertools
import math
import numpy as np
import os

# Set page config at the very beginning.
st.set_page_config(page_title="Painter App", layout="wide")

COLOR_DB_FILE = "color.txt"

# -----------------------------
# Read the color database from the text file.
# -----------------------------
@st.cache_data
def read_color_file(filename=COLOR_DB_FILE):
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception as e:
        st.error("Error reading color.txt: " + str(e))
        return ""

# -----------------------------
# Parsing function: read the text and create a dictionary of databases.
# -----------------------------
def parse_color_db(txt):
    databases = {}
    current_db = None
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        # If line does not start with a digit, treat it as a database header.
        if not line[0].isdigit():
            current_db = line
            databases[current_db] = []
        else:
            tokens = line.split()
            # First token is an index, last token is the RGB string, the rest form the color name.
            index = tokens[0]
            rgb_str = tokens[-1]
            color_name = " ".join(tokens[1:-1])
            try:
                r, g, b = [int(x) for x in rgb_str.split(",")]
            except Exception:
                continue
            databases[current_db].append((color_name, (r, g, b)))
    return databases

# Read and parse the color file.
color_txt = read_color_file()
databases = parse_color_db(color_txt)

# -----------------------------
# Helper: Convert list of (name, rgb) tuples to a dictionary.
# -----------------------------
def convert_db_list_to_dict(color_list):
    d = {}
    for name, rgb in color_list:
        d[name] = {"rgb": list(rgb)}
    return d

# -----------------------------
# Existing helper functions.
# -----------------------------
def rgb_to_hex(r, g, b):
    """Convert RGB (0-255) to a hex string."""
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

def display_thin_color_block(color):
    hex_color = rgb_to_hex(*color)
    st.markdown(
        f"<div style='background-color: {hex_color}; width:50px; height:20px; border:1px solid #000; display:inline-block; margin-right:10px;'></div>",
        unsafe_allow_html=True,
    )

# -----------------------------
# File update helpers
# -----------------------------
def add_color_to_db(selected_db, color_name, r, g, b):
    """
    Add a new color to the specified database section in the color.txt file.
    It reads the file, finds the section, appends a new line with the next index,
    and writes back the file.
    """
    # Read file lines.
    try:
        with open(COLOR_DB_FILE, "r") as f:
            lines = f.readlines()
    except Exception as e:
        st.error("Error reading file for update: " + str(e))
        return False

    new_color_line = ""
    # Find the section for selected_db.
    new_lines = []
    in_section = False
    index = 0
    section_found = False
    for line in lines:
        stripped = line.strip()
        # Check if line is a header (doesn't start with digit)
        if stripped and not stripped[0].isdigit():
            if in_section:
                # End of current section.
                in_section = False
            if stripped == selected_db:
                section_found = True
                in_section = True
                new_lines.append(line)
                continue
        if in_section:
            # In the section, try to get the last index.
            tokens = stripped.split()
            if tokens and tokens[0].isdigit():
                index = max(index, int(tokens[0]))
            new_lines.append(line)
        else:
            new_lines.append(line)
    if not section_found:
        st.error("Selected database not found in file.")
        return False

    # Next index
    new_index = index + 1
    new_color_line = f"{new_index} {color_name} {r},{g},{b}\n"
    # Insert the new line at the end of the section.
    updated_lines = []
    inserted = False
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped[0].isdigit():
            # Header
            if stripped == selected_db:
                in_section = True
            else:
                if in_section and not inserted:
                    updated_lines.append(new_color_line)
                    inserted = True
                in_section = False
        updated_lines.append(line)
    if in_section and not inserted:
        updated_lines.append(new_color_line)
    
    try:
        with open(COLOR_DB_FILE, "w") as f:
            f.writelines(updated_lines)
        # Clear the cache for read_color_file so new data is loaded.
        read_color_file.clear()
        return True
    except Exception as e:
        st.error("Error writing to file: " + str(e))
        return False

def create_custom_database(new_db_name):
    """
    Append a new database header to the end of the color.txt file.
    """
    line = f"\n{new_db_name}\n"
    try:
        with open(COLOR_DB_FILE, "a") as f:
            f.write(line)
        read_color_file.clear()
        return True
    except Exception as e:
        st.error("Error writing to file: " + str(e))
        return False

# -----------------------------
# Colors DataBase Subpages
# -----------------------------
def show_databases_page():
    st.title("Color Database - Data Bases")
    selected_db = st.selectbox("Select a color database:", list(databases.keys()))
    st.write(f"### Colors in database: {selected_db}")
    for name, rgb in databases[selected_db]:
        st.write(f"**{name}**: {rgb_to_hex(*rgb)} ({rgb[0]},{rgb[1]},{rgb[2]})")
        display_thin_color_block(rgb)

def show_add_colors_page():
    global databases  # declare at the very beginning
    st.title("Colors DataBase - Add Colors")
    # Dropdown to select which database to add a new color to.
    selected_db = st.selectbox("Select database to add a new color:", list(databases.keys()))
    with st.form("add_color_form"):
        new_color_name = st.text_input("New Color Name")
        r = st.number_input("Red", min_value=0, max_value=255, value=255)
        g = st.number_input("Green", min_value=0, max_value=255, value=255)
        b = st.number_input("Blue", min_value=0, max_value=255, value=255)
        submitted = st.form_submit_button("Add Color")
        if submitted:
            if new_color_name:
                success = add_color_to_db(selected_db, new_color_name, int(r), int(g), int(b))
                if success:
                    st.success(f"Color '{new_color_name}' added to {selected_db}!")
                    # Re-read file and update databases
                    color_txt = read_color_file(COLOR_DB_FILE)
                    databases = parse_color_db(color_txt)
                else:
                    st.error("Failed to add color.")
            else:
                st.error("Please enter a color name.")

def show_create_custom_db_page():
    global databases  # declare global here
    st.title("Colors DataBase - Create Custom Data Base")
    with st.form("create_db_form"):
        new_db_name = st.text_input("Enter new database name:")
        submitted = st.form_submit_button("Create Database")
        if submitted:
            if new_db_name:
                success = create_custom_database(new_db_name)
                if success:
                    st.success(f"Database '{new_db_name}' created!")
                    color_txt = read_color_file(COLOR_DB_FILE)
                    databases = parse_color_db(color_txt)
                else:
                    st.error("Failed to create database.")
            else:
                st.error("Please enter a database name.")
# -----------------------------
# Main app navigation
# -----------------------------
def main():
    # Initialize subpage state if not set.
    if "subpage" not in st.session_state:
        st.session_state.subpage = None

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
        
        # Slider for percentage step (4 to 10).
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
        st.session_state.subpage = None

    elif page == "Colors DataBase":
        st.title("Colors DataBase")
        st.write("Select an action:")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Data Bases"):
                st.session_state.subpage = "databases"
        with col2:
            if st.button("Add Colors"):
                st.session_state.subpage = "add"
        with col3:
            if st.button("Create Custom Data Base"):
                st.session_state.subpage = "custom"
        
        if st.session_state.subpage == "databases":
            show_databases_page()
        elif st.session_state.subpage == "add":
            show_add_colors_page()
        elif st.session_state.subpage == "custom":
            show_create_custom_db_page()

if __name__ == "__main__":
    main()
