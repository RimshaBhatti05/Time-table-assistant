import streamlit as st
import pandas as pd
from io import BytesIO

# —————————————————————————
# Utility functions
# —————————————————————————

def reset_app():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.experimental_rerun()

def create_empty_timetable(classes, days, periods):
    # Returns a dict of class → DataFrame(day × period)
    tables = {}
    for cls in classes:
        df = pd.DataFrame("", index=days, columns=periods)
        tables[cls] = df
    return tables

def to_excel_bytes(tables):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for cls, df in tables.items():
            df.to_excel(writer, sheet_name=cls)
    output.seek(0)
    return output.read()

# —————————————————————————
# App setup
# —————————————————————————

st.set_page_config(page_title="Timetable Assistant", layout="centered")
st.title("📅 School Timetable Assistant")

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.name = ""
    st.session_state.classes = []
    st.session_state.teachers = []
    st.session_state.incharges = {}
    st.session_state.timetable = {}

def next_step():
    st.session_state.step += 1

# —————————————————————————
# Step 0: Get user name
# —————————————————————————
if st.session_state.step == 0:
    st.subheader("👋 What’s your name?")
    st.session_state.name = st.text_input("Enter your name")
    if st.button("Next"):
        if st.session_state.name.strip():
            next_step()
        else:
            st.error("Please enter your name.")

# —————————————————————————
# Step 1: Enter classes
# —————————————————————————
elif st.session_state.step == 1:
    st.subheader(f"Hello, {st.session_state.name}! Enter your classes/sections:")
    classes_txt = st.text_area("Comma-separated (e.g., 5th Pink, 6th Red)")
    if st.button("Next"):
        cls = [c.strip() for c in classes_txt.split(",") if c.strip()]
        if cls:
            st.session_state.classes = cls
            next_step()
        else:
            st.error("Enter at least one class.")

# —————————————————————————
# Step 2: Add teachers
# —————————————————————————
elif st.session_state.step == 2:
    st.subheader("➕ Add Teachers (one at a time)")
    with st.form("teacher_form", clear_on_submit=True):
        name = st.text_input("Teacher Name")
        ttype = st.radio("Type", ["Full-time (9 lect, 2 free)", "Visiting (≤5 lect)"])
        subjects = st.text_input("Subject(s) (comma-separated)")
        secs = st.multiselect("Which classes?", st.session_state.classes)
        submitted = st.form_submit_button("Add Teacher")
        if submitted:
            if not (name and subjects and secs):
                st.error("Fill all fields.")
            else:
                st.session_state.teachers.append({
                    "name": name,
                    "type": ttype,
                    "subjects": [s.strip() for s in subjects.split(",")],
                    "sections": secs
                })
                st.success(f"Added {name}")
    if st.session_state.teachers:
        st.write("**Teachers so far:**")
        df_t = pd.DataFrame(st.session_state.teachers)
        st.dataframe(df_t, height=200)
    if st.button("Next"):
        if st.session_state.teachers:
            next_step()
        else:
            st.error("Add at least one teacher.")

# —————————————————————————
# Step 3: Assign in-charges
# —————————————————————————
elif st.session_state.step == 3:
    st.subheader("👩‍🏫 Assign In-charge for first lecture")
    for cls in st.session_state.classes:
        opts = [t["name"] for t in st.session_state.teachers if cls in t["sections"]]
        st.session_state.incharges[cls] = st.selectbox(f"In-charge for {cls}", opts, key=cls)
    if st.button("Next"):
        next_step()

# —————————————————————————
# Step 4: Generate timetable
# —————————————————————————
elif st.session_state.step == 4:
    st.subheader("📊 Generating Timetable…")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = [f"P{p}" for p in range(1, 8)]  # 7 periods/day

    # Create empty tables
    tables = create_empty_timetable(st.session_state.classes, days, periods)

    # Fill in-charge in period 1
    for cls, teacher in st.session_state.incharges.items():
        for d in days:
            tables[cls].at[d, "P1"] = teacher

    # Allocate other lectures
    for t in st.session_state.teachers:
        max_lec = 9 if "Full-time" in t["type"] else 5
        free = 2 if "Full-time" in t["type"] else 0
        slots = max_lec - free
        for cls in t["sections"]:
            df = tables[cls]
            placed = 0
            for d in days:
                for p in periods[1:]:
                    if placed >= slots:
                        break
                    if df.at[d, p] == "":
                        df.at[d, p] = t["name"]
                        placed += 1
                if placed >= slots:
                    break

    st.session_state.timetable = tables

    # Display & download
    for cls, df in tables.items():
        st.markdown(f"### 🏫 {cls}")
        st.dataframe(df, height=300)

    excel_bytes = to_excel_bytes(tables)
    st.download_button(
        "⬇️ Download Excel",
        data=excel_bytes,
        file_name="timetable.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.button("🔁 Start Over"):
        reset_app()



