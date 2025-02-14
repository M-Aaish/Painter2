@st.cache_data
def load_data():
    file_path = "paints.xlsx"  # Ensure file is in the app directory
    try:
        xls = pd.ExcelFile(file_path)
        brands = {}

        # Debug: Show available sheets
        st.write("Available Sheets:", xls.sheet_names)

        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)

            # Debug: Show columns in each sheet
            st.write(f"Checking sheet: {sheet}, Columns: {df.columns.tolist()}")

            # Find the closest matching columns
            name_col = next((col for col in df.columns if "name" in col.lower()), None)
            rgb_col = next((col for col in df.columns if "rgb" in col.lower()), None)

            if name_col and rgb_col:
                # Convert RGB values from string to tuple if needed
                df[rgb_col] = df[rgb_col].apply(
                    lambda x: tuple(map(int, x.split(','))) if isinstance(x, str) else (0, 0, 0)
                )
                brands[sheet] = df[[name_col, rgb_col]].rename(columns={name_col: "Name", rgb_col: "RGB"})

        # Debug: Show loaded brands
        st.write("Loaded Brands:", list(brands.keys()))

        return brands

    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return {}
