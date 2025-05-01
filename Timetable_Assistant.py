import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Timetable Assistant", layout="centered")

# Initialize the step counter
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.name = ""
    st.session_state.classes = []
    st.session_state.teachers = []
    st.session_state.incharge = ""
    st.session_state.timetable = None

def next_step():
    st.session_state.step += 1

# Step 0: Enter Name
if st.session_state.step == 0:
    st.title("📅 Timetable Assistant")
    st.subheader("👋 Hello! What's your name?")
    st.session_state.name = st.text_input("Your Name")
    if st.button("Next"):
        if st.session_state.name.strip() != "":
            next_step()
        else:
            st.error("Please enter your name.")

# Step 1: Enter Classes & Sections
elif st.session_state.step == 1:
    st.subheader(f"Hi {st.session_state.name}! Enter your classes & sections")
    classes_input = st.text_area("Comma-separate each class-section (e.g. 5th Pink, 6th Red)")
    if st.button("Next"):
        items = [c.strip() for c in classes_input.split(",") if c.strip()]
        if items:
            st.session_state.classes = items
            next_step()
        else:
            st.error("Please enter at least one class-section.")

# Step 2: Add Teachers
elif st.session_state.step == 2:
    st.subheader("➕ Add Teachers")
    with st.form("teacher_form", clear_on_submit=True):
        tname = st.text_input("Teacher Name")
        ttype = st.selectbox("Type", ["Full-time (9 lectures incl. 2 free)", "Visiting (≤5 lectures)"])
        tsubs = st.text_input("Subjects (comma-separated)")
        tsecs = st.multiselect("Which of your classes?", st.session_state.classes)
        submitted = st.form_submit_button("Add this Teacher")
        if submitted:
            if not (tname and tsubs and tsecs):
                st.error("Fill out all fields.")
            else:
                st.session_state.teachers.append({
                    "name": tname,
                    "type": ttype,
                    "subjects": [s.strip() for s in tsubs.split(",")],
                    "sections": tsecs
                })
                st.success(f"Added {tname}")

    if st.session_state.teachers:
        st.write("**Teachers so far:**")
        df = pd.DataFrame(st.session_state.teachers)
        st.dataframe(df, height=200)

    if st.button("Next: Assign In-charge"):
        if st.session_state.teachers:
            next_step()
        else:
            st.error("Add at least one teacher.")

# Step 3: Select In-charge Teacher for First Lecture
elif st.session_state.step == 3:
    st.subheader("👩‍🏫 Choose In-charge for First Lecture of Each Class")
    incharge_map = {}
    for cls in st.session_state.classes:
        # Filter teachers who teach this class
        options = [t["name"] for t in st.session_state.teachers if cls in t["sections"]]
        if options:
            incharge_map[cls] = st.selectbox(f"{cls} In-charge:", options, key=cls)
        else:
            st.warning(f"No teacher assigned to {cls} yet.")

    if st.button("Next: Generate Timetable"):
        st.session_state.incharge = incharge_map
        next_step()

# Step 4: Generate and Display Timetable
elif st.session_state.step == 4:
    st.subheader("📊 Generated Timetable")

    days = ["Mon","Tue","Wed","Thu","Fri","Sat"]
    periods = [f"P{i+1}" for i in range(7)]
    # Build an empty structure
    timetable = {}
    for cls in st.session_state.classes:
        df = pd.DataFrame("", index=days, columns=periods)
        # First lecture is in-charge
        for d in days:
            df.at[d, "P1"] = st.session_state.incharge.get(cls, "")
        timetable[cls] = df

    # Auto-allocate other lectures
    for t in st.session_state.teachers:
        max_lec = 9 if "Full-time" in t["type"] else 5
        free = 2 if "Full-time" in t["type"] else 0
        assignable = max_lec - free
        for cls in t["sections"]:
            df = timetable[cls]
            placed = 0
            for d in days:
                for p in periods[1:]:
                    if placed >= assignable:
                        break
                    if df.at[d, p] == "":
                        df.at[d, p] = t["name"]
                        placed += 1
                if placed >= assignable:
                    break

    # Store and display
    st.session_state.timetable = timetable
    for cls, df in timetable.items():
        st.markdown(f"### 🏫 {cls}")
        st.dataframe(df)

    # Download as Excel
    def to_excel(dfs):
        bio = BytesIO()
        with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
            for cls, df in dfs.items():
                df.to_excel(writer, sheet_name=cls)
        return bio.getvalue()

    excel_data = to_excel(st.session_state.timetable)
    st.download_button("⬇️ Download All as Excel", data=excel_data,
                       file_name="timetable.xlsx", mime="application/vnd.ms-excel")

    if st.button("🔁 Start Over"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()


