import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import json

# Configure page
st.set_page_config(
    page_title="Class Schedule Generator",
    page_icon="🗓️",
    layout="wide"
)

# Define static time periods
TIME_PERIODS = {
    1: "9:00-10:30",
    2: "10:45-12:15",
    "Lunch": "12:15-13:10",
    3: "13:10-14:40", 
    4: "14:55-16:25",
    5: "16:40-18:10"
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
PERIODS = [1, 2, 3, 4, 5]

def initialize_session_state():
    """Initialize session state variables"""
    if 'classes' not in st.session_state:
        st.session_state.classes = []
    if 'office_hours' not in st.session_state:
        st.session_state.office_hours = []

def add_class(course_name, day, period, classroom, color):
    """Add a class to the schedule"""
    new_class = {
        'course_name': course_name,
        'day': day,
        'period': period,
        'classroom': classroom,
        'color': color,
        'time': TIME_PERIODS[period]
    }
    st.session_state.classes.append(new_class)

def add_office_hours(day, start_time, end_time, location):
    """Add office hours to the schedule"""
    office_hour = {
        'day': day,
        'start_time': start_time,
        'end_time': end_time,
        'location': location,
        'time_display': f"{start_time}-{end_time}"
    }
    st.session_state.office_hours.append(office_hour)

def create_schedule_table():
    """Create a visual schedule table using Plotly"""
    
    # Create base schedule grid
    schedule_data = {}
    for day in DAYS:
        schedule_data[day] = {}
        for period in PERIODS:
            schedule_data[day][period] = {"content": "", "color": "#f8f9fa", "text_color": "#000000"}
    
    # Fill in classes
    for class_info in st.session_state.classes:
        day = class_info['day']
        period = class_info['period']
        schedule_data[day][period] = {
            "content": f"<b>{class_info['course_name']}</b><br>{class_info['classroom']}<br><i>{class_info['time']}</i>",
            "color": class_info['color'],
            "text_color": "#ffffff"
        }
    
    # Create figure
    fig = go.Figure()
    
    # Add time labels
    time_labels = [TIME_PERIODS[p] for p in PERIODS]
    
    # Create table
    cell_colors = []
    cell_text = []
    
    for period in PERIODS:
        row_colors = []
        row_text = []
        
        # Add time period
        row_colors.append("#e9ecef")
        row_text.append(f"<b>Period {period}</b><br>{TIME_PERIODS[period]}")
        
        # Add each day
        for day in DAYS:
            content = schedule_data[day][period]["content"]
            color = schedule_data[day][period]["color"] 
            
            row_colors.append(color)
            if content:
                row_text.append(content)
            else:
                row_text.append("")
        
        cell_colors.append(row_colors)
        cell_text.append(row_text)
    
    # Add lunch break row
    lunch_colors = ["#ffc107"] + ["#fff3cd"] * 5
    lunch_text = ["<b>Lunch Break</b><br>12:15-13:10"] + [""] * 5
    
    # Insert lunch after period 2 (index 1)
    cell_colors.insert(2, lunch_colors)
    cell_text.insert(2, lunch_text)
    
    fig.add_trace(go.Table(
        header=dict(
            values=["<b>Time</b>"] + [f"<b>{day}</b>" for day in DAYS],
            fill_color="#343a40",
            font_color="white",
            font_size=14,
            height=40
        ),
        cells=dict(
            values=[[row[i] for row in cell_text] for i in range(6)],  # 6 columns (time + 5 days)
            fill_color=[[row[i] for row in cell_colors] for i in range(6)],
            font_color="black",
            font_size=12,
            height=80,
            align="center"
        )
    ))
    
    fig.update_layout(
        title="Weekly Class Schedule",
        title_x=0.5,
        title_font_size=20,
        height=600,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig

def create_office_hours_display():
    """Create office hours display"""
    if not st.session_state.office_hours:
        return None
    
    oh_text = "**Office Hours:**\n\n"
    for oh in st.session_state.office_hours:
        oh_text += f"• **{oh['day']}**: {oh['time_display']} - {oh['location']}\n"
    
    return oh_text

def main():
    st.title("🗓️ Professor Class Schedule Generator")
    st.markdown("Create a professional weekly class schedule for your semester.")
    
    initialize_session_state()
    
    # Sidebar for inputs
    st.sidebar.header("📝 Schedule Input")
    
    # Semester info
    st.sidebar.subheader("Semester Information")
    semester = st.sidebar.text_input("Semester", placeholder="Fall 2024", value="Fall 2024")
    professor_name = st.sidebar.text_input("Professor Name", placeholder="Dr. Smith")
    
    # Add classes
    st.sidebar.subheader("➕ Add Classes")
    
    with st.sidebar.form("add_class_form"):
        course_name = st.text_input("Course Name", placeholder="CS 101 - Intro to Programming")
        col1, col2 = st.columns(2)
        with col1:
            day = st.selectbox("Day", DAYS)
        with col2:
            period = st.selectbox("Period", PERIODS)
        
        classroom = st.text_input("Classroom", placeholder="Room 205")
        color = st.color_picker("Color", "#1f77b4")
        
        submitted = st.form_submit_button("Add Class")
        
        if submitted and course_name and classroom:
            # Check for conflicts
            conflict = False
            for existing_class in st.session_state.classes:
                if existing_class['day'] == day and existing_class['period'] == period:
                    st.error(f"Conflict! {day} Period {period} already has {existing_class['course_name']}")
                    conflict = True
                    break
            
            if not conflict:
                add_class(course_name, day, period, classroom, color)
                st.success(f"Added {course_name}!")
                st.rerun()
    
    # Add office hours
    st.sidebar.subheader("🏢 Add Office Hours")
    
    with st.sidebar.form("add_office_hours_form"):
        oh_day = st.selectbox("Day", DAYS, key="oh_day")
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("Start Time", value=None)
        with col2:
            end_time = st.time_input("End Time", value=None)
        
        location = st.text_input("Location", placeholder="Office 301")
        
        oh_submitted = st.form_submit_button("Add Office Hours")
        
        if oh_submitted and start_time and end_time and location:
            add_office_hours(oh_day, start_time.strftime("%H:%M"), end_time.strftime("%H:%M"), location)
            st.success("Added office hours!")
            st.rerun()
    
    # Clear data buttons
    st.sidebar.subheader("🗑️ Clear Data")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Classes"):
            st.session_state.classes = []
            st.rerun()
    with col2:
        if st.button("Clear Office Hours"):
            st.session_state.office_hours = []
            st.rerun()
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📅 Visual Schedule", "📋 Class List", "💾 Export"])
    
    with tab1:
        # Semester header
        if professor_name:
            st.markdown(f"### {professor_name} - {semester}")
        else:
            st.markdown(f"### {semester}")
        
        # Create and display schedule
        if st.session_state.classes:
            fig = create_schedule_table()
            st.plotly_chart(fig, use_container_width=True)
            
            # Office hours display
            oh_display = create_office_hours_display()
            if oh_display:
                st.markdown(oh_display)
        else:
            st.info("👈 Add some classes in the sidebar to see your schedule!")
    
    with tab2:
        st.header("📚 Current Classes")
        
        if st.session_state.classes:
            for i, class_info in enumerate(st.session_state.classes):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    <div style="background-color: {class_info['color']}; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <b>{class_info['course_name']}</b><br>
                        {class_info['day']} - Period {class_info['period']} ({class_info['time']})<br>
                        📍 {class_info['classroom']}
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"delete_class_{i}", help="Delete this class"):
                        st.session_state.classes.pop(i)
                        st.rerun()
        else:
            st.info("No classes added yet.")
        
        # Office hours list
        st.header("🏢 Office Hours")
        if st.session_state.office_hours:
            for i, oh in enumerate(st.session_state.office_hours):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.info(f"**{oh['day']}**: {oh['time_display']} - {oh['location']}")
                with col2:
                    if st.button("🗑️", key=f"delete_oh_{i}", help="Delete office hours"):
                        st.session_state.office_hours.pop(i)
                        st.rerun()
        else:
            st.info("No office hours added yet.")
    
    with tab3:
        st.header("💾 Export Options")
        
        st.markdown("""
        ### How to Export Your Schedule:
        
        **📸 Screenshot Method:**
        1. Go to the "Visual Schedule" tab
        2. Take a screenshot of the schedule table
        3. Use your favorite image editor to crop if needed
        
        **🖨️ Print Method:**
        1. Use your browser's print function (Ctrl+P / Cmd+P)
        2. Select "Print to PDF" as destination
        3. Choose landscape orientation for best results
        
        **📱 Mobile Friendly:**
        The schedule is responsive and works well on tablets and phones for quick reference.
        """)
        
        # JSON export for backup
        st.subheader("🔧 Backup Your Data")
        if st.session_state.classes or st.session_state.office_hours:
            backup_data = {
                'semester': semester,
                'professor_name': professor_name,
                'classes': st.session_state.classes,
                'office_hours': st.session_state.office_hours,
                'export_date': datetime.now().isoformat()
            }
            
            json_str = json.dumps(backup_data, indent=2)
            st.download_button(
                label="📥 Download Backup (JSON)",
                data=json_str,
                file_name=f"schedule_backup_{semester.lower().replace(' ', '_')}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()
