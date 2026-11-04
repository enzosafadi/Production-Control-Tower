import streamlit as st
import pandas as pd
import plotly.express as px

from database import initialize_database, add_project, get_projects, update_project, delete_project


# Application configuration
st.set_page_config(
    page_title="Production Control Tower",
    page_icon="📊",
    layout="wide"
)

initialize_database()

STATUSES = ["On Track", "At Risk", "Delayed", "Completed"]

st.title("Production Control Tower")
st.subheader("Project Delivery & Resource Optimization")
st.caption("Portfolio prototype - fictional sample projects and resources. Locally saved projects are separate from the sample dashboard.")

# Sample production data
projects = pd.DataFrame({
    "Project": [
        "Newsletter Launch",
        "Website Redesign",
        "Email Campaign",
        "Landing Page",
        "Brand Refresh"
    ],
    "Manager": [
        "Alex", "Sarah", "James", "Emma", "Daniel"
    ],
    "Progress": [85, 45, 100, 30, 65],
    "Status": [
        "On Track",
        "At Risk",
        "Completed",
        "Delayed",
        "On Track"
    ]
})

# Employee resource data
resources = pd.DataFrame({
    "Employee": ["Alex", "Sarah", "James", "Emma", "Daniel"],
    "Available Hours": [40, 40, 40, 40, 40],
    "Assigned Hours": [45, 50, 30, 48, 25]
})

resources["Utilization (%)"] = (
    resources["Assigned Hours"] /
    resources["Available Hours"] * 100
).round(1)

# Retrieve saved projects from SQLite
saved_projects = get_projects()

st.divider()
st.header("Production Risk Alerts")
overloaded = resources[resources["Utilization (%)"] > 100]
at_risk = projects[projects["Status"].isin(["At Risk", "Delayed"])]
if not overloaded.empty:
    st.error(f"Capacity Alert: {len(overloaded)} employees exceed their available working hours.")
    for _, person in overloaded.iterrows():
        st.warning(f"{person['Employee']} is overloaded by {person['Assigned Hours'] - person['Available Hours']} hours.")
if not at_risk.empty:
    st.error(f"Delivery Alert: {len(at_risk)} projects require management attention.")
    for _, project in at_risk.iterrows():
        st.warning(f"{project['Project']} — Status: {project['Status']}")
if overloaded.empty and at_risk.empty:
    st.success("All production operations are within acceptable limits.")

st.divider()
st.header("Production Performance KPIs")
completion_rate = (projects["Status"] == "Completed").mean() * 100 if len(projects) else 0
available_hours = resources["Available Hours"].sum()
utilization = resources["Assigned Hours"].sum() / available_hours * 100 if available_hours else 0
excess = (resources["Assigned Hours"] - resources["Available Hours"]).clip(lower=0).sum()
k1, k2, k3 = st.columns(3)
k1.metric("Project Completion Rate", f"{completion_rate:.1f}%")
k2.metric("Team Utilization", f"{utilization:.1f}%")
k3.metric("Excess Workload", f"{excess:.0f} hrs")

st.divider()
st.header("Workload Rebalancing Recommendations")
remaining = {row["Employee"]: max(0, row["Available Hours"] - row["Assigned Hours"]) for _, row in resources.iterrows()}
recommendations = []
for _, employee in overloaded.iterrows():
    extra = employee["Assigned Hours"] - employee["Available Hours"]
    for colleague, capacity in remaining.items():
        if colleague == employee["Employee"] or extra <= 0:
            continue
        transfer = min(extra, capacity)
        if transfer > 0:
            recommendations.append({"From": employee["Employee"], "To": colleague, "Hours to Transfer": transfer})
            remaining[colleague] -= transfer
            extra -= transfer
if recommendations:
    st.dataframe(pd.DataFrame(recommendations), width="stretch", hide_index=True)
else:
    st.success("No workload redistribution required.")

st.divider()
st.header("Workload Rebalancing Simulation")
simulated = resources.copy()
simulated["Original Hours"] = simulated["Assigned Hours"]
for transfer in recommendations:
    simulated.loc[simulated["Employee"] == transfer["From"], "Assigned Hours"] -= transfer["Hours to Transfer"]
    simulated.loc[simulated["Employee"] == transfer["To"], "Assigned Hours"] += transfer["Hours to Transfer"]
simulated["New Utilization (%)"] = (simulated["Assigned Hours"] / simulated["Available Hours"] * 100).round(1)
st.dataframe(simulated[["Employee", "Original Hours", "Assigned Hours", "New Utilization (%)"]], width="stretch", hide_index=True)
fig_simulation = px.bar(simulated, x="Employee", y=["Original Hours", "Assigned Hours"], barmode="group",
    title="Workload Before vs. After Rebalancing", labels={"value": "Assigned Hours", "variable": "Scenario"})
st.plotly_chart(fig_simulation, width="stretch")

st.divider()
st.header("Project Management")
st.subheader("Create a New Project")
with st.form("new_project_form", clear_on_submit=True):
    project_name = st.text_input("Project Name")
    project_manager = st.selectbox("Assign Project Manager", resources["Employee"].tolist())
    project_status = st.selectbox("Project Status", STATUSES)
    project_progress = st.slider("Project Progress (%)", 0, 100, 0)
    submitted = st.form_submit_button("Create Project")
if submitted:
    if project_name.strip():
        add_project(project_name.strip(), project_manager, project_status, project_progress)
        st.success(f"Project '{project_name.strip()}' saved successfully!")
        st.rerun()
    else:
        st.error("Please enter a project name.")

st.divider()
st.header("Saved Projects")
if saved_projects:
    saved_df = pd.DataFrame(saved_projects, columns=["ID", "Project", "Manager", "Status", "Progress (%)"])
    st.dataframe(saved_df, width="stretch", hide_index=True)
else:
    st.info("No projects have been saved yet.")

st.divider()
st.header("Edit Existing Project")
if saved_projects:
    project_options = {f"{p[0]} - {p[1]}": p for p in saved_projects}
    selected_project = st.selectbox("Select Project to Edit", list(project_options), key="edit_selection")
    project = project_options[selected_project]
    with st.form("edit_project_form"):
        edit_name = st.text_input("Project Name", value=project[1])
        edit_manager = st.text_input("Project Manager", value=project[2])
        current_status = project[3] if project[3] in STATUSES else STATUSES[0]
        edit_status = st.selectbox("Project Status", STATUSES, index=STATUSES.index(current_status))
        edit_progress = st.slider("Project Progress (%)", 0, 100, int(project[4]))
        update_submitted = st.form_submit_button("Update Project")
    if update_submitted:
        if not edit_name.strip():
            st.error("Project name cannot be empty.")
        elif not edit_manager.strip():
            st.error("Project manager cannot be empty.")
        elif update_project(project[0], edit_name.strip(), edit_manager.strip(), edit_status, edit_progress):
            st.success("Project updated successfully!")
            st.rerun()
        else:
            st.error("Project could not be updated.")
else:
    st.info("Create a project to enable editing.")

st.divider()
st.header("Delete Project")
if saved_projects:
    delete_options = {f"{p[0]} - {p[1]}": p[0] for p in saved_projects}
    selected_delete = st.selectbox("Select Project to Delete", list(delete_options), key="delete_selection")
    confirm_delete = st.checkbox("I understand this project will be permanently deleted.")
    if st.button("Delete Project", type="primary"):
        if not confirm_delete:
            st.warning("Please confirm deletion first.")
        elif delete_project(delete_options[selected_delete]):
            st.success("Project deleted successfully!")
            st.rerun()
        else:
            st.error("Project could not be deleted.")
else:
    st.info("No projects available to delete.")

