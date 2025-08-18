import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

# Configure page
st.set_page_config(
    page_title="Class Schedule Generator",
    page_icon="🗓️",
    layout="wide"
)

# Default time periods (your current schedule)
DEFAULT_TIME_PERIODS = {
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
    if 'time_periods' not in st.session_state:
        st.session_state.time_periods = DEFAULT_TIME_PERIODS.copy()

def get_time_periods():
    """Get current time periods (custom or default)"""
    return st.session_state.time_periods

def update_time_period(period, new_time):
    """Update a specific time period"""
    st.session_state.time_periods[period] = new_time

def add_class(course_name, day, period, classroom, color):
    """Add a class to the schedule"""
    time_periods = get_time_periods()
    new_class = {
        'course_name': course_name,
        'day': day,
        'period': period,
        'classroom': classroom,
        'color': color,
        'time': time_periods[period]
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
    time_periods = get_time_periods()
    
    # Create base schedule grid
    schedule_data = {}
    for day in DAYS:
        schedule_data[day] = {}
        for period in PERIODS:
            schedule_data[day][period] = {"content": "", "color": "#f8f9fa"}
    
    # Fill in classes
    for class_info in st.session_state.classes:
        day = class_info['day']
        period = class_info['period']
        # Update time in case periods were changed after class was added
        current_time = time_periods[period]
        schedule_data[day][period] = {
            "content": f"<b>{class_info['course_name']}</b><br>{class_info['classroom']}<br><i>{current_time}</i>",
            "color": class_info['color']
        }
    
    # Prepare table data
    header_values = ["<b>Time</b>"] + [f"<b>{day}</b>" for day in DAYS]
    
    # Create rows data
    table_values = []
    table_colors = []
    
    # Time column
    time_column = []
    time_colors = []
    
    # Data columns for each day
    day_columns = {day: [] for day in DAYS}
    day_colors = {day: [] for day in DAYS}
    
    # Build rows
    for period in PERIODS:
        # Time column
        time_column.append(f"<b>Period {period}</b><br>{time_periods[period]}")
        time_colors.append("#e9ecef")
        
        # Day columns
        for day in DAYS:
            if schedule_data[day][period]["content"]:
                day_columns[day].append(schedule_data[day][period]["content"])
                day_colors[day].append(schedule_data[day][period]["color"])
            else:
                day_columns[day].append("")
                day_colors[day].append("#f8f9fa")
        
        # Add lunch break after period 2
        if period == 2:
            time_column.append(f"<b>Lunch Break</b><br>{time_periods['Lunch']}")
            time_colors.append("#ffc107")
            
            for day in DAYS:
                day_columns[day].append("")
                day_colors[day].append("#fff3cd")
    
    # Combine all columns
    all_values = [time_column] + [day_columns[day] for day in DAYS]
    all_colors = [time_colors] + [day_colors[day] for day in DAYS]
    
    # Create figure
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=header_values,
            fill_color="#343a40",
            font=dict(color="white", size=14),
            height=40,
            align="center"
        ),
        cells=dict(
            values=all_values,
            fill_color=all_colors,
            font=dict(color="white", size=12),
            height=80,
            align="center"
        )
    )])
    
    fig.update_layout(
        title={
            'text': "Weekly Class Schedule",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
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

def generate_pdf_schedule(semester, professor_name):
    """Generate a PDF of the class schedule"""
    time_periods = get_time_periods()
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=1,  # Center alignment
        textColor=colors.black
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=10,
        alignment=1,  # Center alignment
        textColor=colors.grey
    )
    
    # Title
    if professor_name:
        title = Paragraph(f"{professor_name} - {semester}", title_style)
    else:
        title = Paragraph(f"Class Schedule - {semester}", title_style)
    elements.append(title)
    
    subtitle = Paragraph("Weekly Class Schedule", subtitle_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 20))
    
    # Create schedule data for PDF
    schedule_grid = {}
    for day in DAYS:
        schedule_grid[day] = {}
        for period in PERIODS:
            schedule_grid[day][period] = ""
    
    # Fill in classes
    for class_info in st.session_state.classes:
        day = class_info['day']
        period = class_info['period']
        schedule_grid[day][period] = f"{class_info['course_name']}\n{class_info['classroom']}"
    
    # Create table data
    table_data = []
    
    # Header row
    header_row = ['Time'] + DAYS
    table_data.append(header_row)
    
    # Period rows
    for period in PERIODS:
        row = [f"Period {period}\n{time_periods[period]}"]
        for day in DAYS:
            cell_content = schedule_grid[day][period] if schedule_grid[day][period] else ""
            row.append(cell_content)
        table_data.append(row)
        
        # Add lunch break after period 2
        if period == 2:
            lunch_row = [f"Lunch Break\n{time_periods['Lunch']}"] + [""] * 5
            table_data.append(lunch_row)
    
    # Create table
    table = Table(table_data, colWidths=[1.2*inch, 1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
    
    # Table style
    table_style = TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        
        # Time column styling
        ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (0, -1), 9),
        
        # General cell styling
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.lightgrey]),
        
        # Lunch break styling
        ('BACKGROUND', (0, 3), (-1, 3), colors.orange),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.black),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
    ])
    
    # Apply different background colors for class cells
    row_idx = 1
    for period in PERIODS:
        for col_idx, day in enumerate(DAYS, 1):
            if schedule_grid[day][period]:  # If there's a class
                # Find the class info to get its color
                class_color = colors.lightblue  # default
                for class_info in st.session_state.classes:
                    if class_info['day'] == day and class_info['period'] == period:
                        # Convert hex color to RGB
                        hex_color = class_info['color'].lstrip('#')
                        rgb = tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))
                        class_color = colors.Color(rgb[0], rgb[1], rgb[2])
                        break
                
                table_style.add('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), class_color)
                table_style.add('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), colors.white)
                table_style.add('FONTNAME', (col_idx, row_idx), (col_idx, row_idx), 'Helvetica-Bold')
        
        row_idx += 1
        if period == 2:  # Skip lunch row
            row_idx += 1
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Office hours section
    if st.session_state.office_hours:
        elements.append(Spacer(1, 20))
        oh_title = Paragraph("Office Hours", styles['Heading2'])
        elements.append(oh_title)
        
        oh_data = [['Day', 'Time', 'Location']]
        for oh in st.session_state.office_hours:
            oh_data.append([oh['day'], oh['time_display'], oh['location']])
        
        oh_table = Table(oh_data, colWidths=[1.5*inch, 1.5*inch, 2*inch])
        oh_table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ])
        oh_table.setStyle(oh_table_style)
        elements.append(oh_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def main():
    st.title("🗓️ Professor Class Schedule Generator")
    st.markdown("Create a professional weekly class schedule for your semester.")
    
    initialize_session_state()
    
    # Sidebar for inputs
    st.sidebar.header("📝 Schedule Input")
    
    # Time periods customization
    st.sidebar.subheader("⏰ Time Periods")
    with st.sidebar.expander("🔧 Customize Time Periods", expanded=False):
        st.markdown("**Edit the start and end times for each period:**")
        
        time_periods = get_time_periods()
        
        # Period 1
        period1_time = st.text_input("Period 1", value=time_periods[1], key="period1")
        if period1_time != time_periods[1]:
            update_time_period(1, period1_time)
        
        # Period 2
        period2_time = st.text_input("Period 2", value=time_periods[2], key="period2")
        if period2_time != time_periods[2]:
            update_time_period(2, period2_time)
        
        # Lunch Break
        lunch_time = st.text_input("Lunch Break", value=time_periods["Lunch"], key="lunch")
        if lunch_time != time_periods["Lunch"]:
            update_time_period("Lunch", lunch_time)
        
        # Period 3
        period3_time = st.text_input("Period 3", value=time_periods[3], key="period3")
        if period3_time != time_periods[3]:
            update_time_period(3, period3_time)
        
        # Period 4
        period4_time = st.text_input("Period 4", value=time_periods[4], key="period4")
        if period4_time != time_periods[4]:
            update_time_period(4, period4_time)
        
        # Period 5
        period5_time = st.text_input("Period 5", value=time_periods[5], key="period5")
        if period5_time != time_periods[5]:
            update_time_period(5, period5_time)
        
        # Reset to defaults button
        if st.button("🔄 Reset to Default Times"):
            st.session_state.time_periods = DEFAULT_TIME_PERIODS.copy()
            st.rerun()
        
        st.info("💡 Format examples: 9:00-10:30, 14:15-15:45")
    
    # Show current time periods
    current_times = get_time_periods()
    st.sidebar.markdown("**Current Schedule:**")
    for period in PERIODS:
        st.sidebar.write(f"Period {period}: {current_times[period]}")
    st.sidebar.write(f"Lunch: {current_times['Lunch']}")
    
    # Semester info
    st.sidebar.subheader("📚 Semester Information")
    semester = st.sidebar.text_input("Semester", placeholder="Fall 2024", value="Fall 2024")
    professor_name = st.sidebar.text_input("Professor Name", placeholder="Dr. Smith")
    
    # Add classes
    st.sidebar.subheader("➕ Add Classes")
    
    # Define color palette with yellow added
    COLOR_PALETTE = {
        "Royal Blue": "#1f77b4",
        "Forest Green": "#2ca02c", 
        "Crimson Red": "#d62728",
        "Purple": "#9467bd",
        "Orange": "#ff7f0e",
        "Yellow": "#f1c40f",
        "Teal": "#17becf",
        "Brown": "#8c564b",
        "Pink": "#e377c2",
        "Gray": "#7f7f7f",
        "Navy": "#1f3a93",
        "Emerald": "#2ecc71",
        "Burgundy": "#922b21"
    }
    
    with st.sidebar.form("add_class_form"):
        course_name = st.text_input("Course Name", placeholder="CS 101 - Intro to Programming")
        col1, col2 = st.columns(2)
        with col1:
            day = st.selectbox("Day", DAYS)
        with col2:
            period = st.selectbox("Period", PERIODS)
        
        classroom = st.text_input("Classroom", placeholder="Room 205")
        
        # Simple color selection - no preview needed
        color_name = st.selectbox(
            "Color", 
            options=list(COLOR_PALETTE.keys()),
            index=0
        )
        color = COLOR_PALETTE[color_name]
        
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
                    # Use black text for yellow background, get current time
                    current_time = get_time_periods()[class_info['period']]
                    text_color = "black" if class_info['color'] == "#f1c40f" else "white"
                    st.markdown(f"""
                    <div style="background-color: {class_info['color']}; color: {text_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <b>{class_info['course_name']}</b><br>
                        {class_info['day']} - Period {class_info['period']} ({current_time})<br>
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
        
        # PDF Export
        st.subheader("📄 PDF Export")
        if st.session_state.classes:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 Generate PDF", type="primary"):
                    with st.spinner("Generating PDF..."):
                        try:
                            pdf_buffer = generate_pdf_schedule(semester, professor_name)
                            
                            st.download_button(
                                label="📄 Download Schedule PDF",
                                data=pdf_buffer.getvalue(),
                                file_name=f"schedule_{semester.lower().replace(' ', '_')}.pdf",
                                mime="application/pdf"
                            )
                            st.success("✅ PDF generated successfully!")
                        except Exception as e:
                            st.error(f"❌ Error generating PDF: {str(e)}")
            
            with col2:
                st.info("""
                **PDF Features:**
                • Professional landscape layout
                • Color-coded classes
                • Custom time periods
                • Office hours included  
                • Print-ready format
                """)
        else:
            st.info("👈 Add some classes first to generate a PDF!")
        
        st.markdown("---")
        
        # Other export methods
        st.subheader("🖼️ Other Export Methods")
        st.markdown("""
        **📸 Screenshot Method:**
        1. Go to the "Visual Schedule" tab
        2. Take a screenshot of the schedule table
        3. Use your favorite image editor to crop if needed
        
        **🖨️ Browser Print Method:**
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
                'time_periods': st.session_state.time_periods,
                'export_date': datetime.now().isoformat()
            }
            
            json_str = json.dumps(backup_data, indent=2)
            st.download_button(
                label="📥 Download Backup (JSON)",
                data=json_str,
                file_name=f"schedule_backup_{semester.lower().replace(' ', '_')}.json",
                mime="application/json"
            )
        
        # JSON import functionality
        st.subheader("📂 Restore from Backup")
        
        uploaded_file = st.file_uploader(
            "Upload a backup JSON file", 
            type=['json'],
            help="Upload a previously saved schedule backup to restore your data"
        )
        
        if uploaded_file is not None:
            try:
                # Read the JSON file
                backup_data = json.load(uploaded_file)
                
                # Validate required fields
                required_fields = ['classes', 'office_hours', 'time_periods']
                if all(field in backup_data for field in required_fields):
                    
                    # Show preview of what will be imported
                    st.info(f"""
                    **Import Preview:**
                    • Semester: {backup_data.get('semester', 'Not specified')}
                    • Professor: {backup_data.get('professor_name', 'Not specified')}
                    • Classes: {len(backup_data['classes'])} classes
                    • Office Hours: {len(backup_data['office_hours'])} entries
                    • Export Date: {backup_data.get('export_date', 'Unknown')}
                    """)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("✅ Import Data", type="primary"):
                            # Restore the data
                            st.session_state.classes = backup_data['classes']
                            st.session_state.office_hours = backup_data['office_hours'] 
                            st.session_state.time_periods = backup_data['time_periods']
                            
                            st.success(f"✅ Successfully imported {len(backup_data['classes'])} classes and {len(backup_data['office_hours'])} office hours!")
                            st.balloons()
                            st.rerun()
                    
                    with col2:
                        if st.button("🔄 Merge with Current", help="Add imported data to existing schedule"):
                            # Merge instead of replace
                            st.session_state.classes.extend(backup_data['classes'])
                            st.session_state.office_hours.extend(backup_data['office_hours'])
                            
                            # Ask about time periods
                            if backup_data['time_periods'] != st.session_state.time_periods:
                                st.warning("⚠️ Time periods in backup differ from current. Keeping current time periods.")
                            
                            st.success(f"✅ Successfully merged {len(backup_data['classes'])} classes and {len(backup_data['office_hours'])} office hours!")
                            st.rerun()
                    
                else:
                    st.error("❌ Invalid backup file. Missing required fields.")
                    st.write("Required fields:", required_fields)
                    st.write("Found fields:", list(backup_data.keys()))
                    
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file. Please check the file format.")
            except Exception as e:
                st.error(f"❌ Error reading backup file: {str(e)}")
        
        st.info("""
        💡 **Import Tips:**
        • **Import Data**: Completely replaces your current schedule
        • **Merge with Current**: Adds imported classes to existing ones
        • Only JSON files exported from this app are supported
        • Time periods from backup will be restored when importing
        """)
            
if __name__ == "__main__":
    main()
