import streamlit as st
import os
from google import genai
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# --- CONFIGURATION ---
st.set_page_config(page_title="SRE Scaffolding Engine", layout="wide")
st.title("🛠️ SRE & DevOps Scaffold Generator")

if not API_KEY:
    st.warning("⚠️ API Key not found. Please set the GOOGLE_API_KEY environment variable in your .env file.")
    st.stop()

# 2. Initialize the New Client
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.5-flash"

# --- UI LAYOUT ---
with st.sidebar:
    st.header("Project Settings")
    project_type = st.selectbox("Project Type", ["Python/Flask", "Node.js", "Go", "Java/Spring", "C++ (CMake)"])
    
    # Store checkboxes in a dictionary for easy filtering
    config_selection = {
        "Dockerfile": st.checkbox("Dockerfile", value=True),
        "Kubernetes": st.checkbox("Kubernetes Manifests", value=True),
        "Terraform": st.checkbox("Terraform (EKS/VPC)", value=True),
        "GitHub Actions": st.checkbox("GitHub Actions", value=True)
    }
    
    st.divider()
    st.info("SRE Tip: Tabs will only be generated for the items checked above.")

st.subheader("1. Project Directory Structure")
tree_input = st.text_area("Paste your project tree here:", height=200, placeholder="""
my-app/
├── src/
│   └── main.py
├── requirements.txt
└── README.md
""")

def generate_devops_files(tree, p_type, configs_to_gen):
    """Only generates content for the checked items."""
    prompt = f"""
    Act as a Senior Site Reliability Engineer. 
    Analyze this directory structure: {tree}
    This is a {p_type} project.
    
    ONLY generate configurations for the following requested items: {', '.join(configs_to_gen)}.
    Do not include any other files.
    
    Format the output as follows for each item:
    ---START [ITEM_NAME]---
    [Code Block]
    ---END [ITEM_NAME]---
    
    Requirements:
    - Docker: Multi-stage, non-root user.
    - K8s: Deployment (with limits), Service.
    - Terraform: AWS EKS/VPC modules.
    """
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt
    )
    return response.text

def parse_output(text, requested_items):
    """Parses the AI output to separate content by section."""
    sections = {}
    for item in requested_items:
        start_marker = f"---START {item}---"
        end_marker = f"---END {item}---"
        if start_marker in text and end_marker in text:
            content = text.split(start_marker)[1].split(end_marker)[0].strip()
            sections[item] = content
    return sections

if st.button("🚀 Generate Scaffolding"):
    # Filter to only checked items
    active_configs = [name for name, checked in config_selection.items() if checked]
    
    if not tree_input:
        st.error("Please provide a directory tree.")
    elif not active_configs:
        st.warning("Please select at least one configuration to generate.")
    else:
        with st.spinner(f"Architecting {len(active_configs)} components..."):
            try:
                raw_result = generate_devops_files(tree_input, project_type, active_configs)
                parsed_content = parse_output(raw_result, active_configs)
                
                if not parsed_content:
                    st.error("AI failed to format the output correctly. Try again.")
                    st.text(raw_result) # Fallback to raw text
                else:
                    st.success("Infrastructure generated!")
                    
                    # --- NAVIGATION TABS ---
                    # This creates the navigation buttons you wanted
                    tabs = st.tabs(active_configs)
                    
                    for i, tab_name in enumerate(active_configs):
                        with tabs[i]:
                            st.subheader(f"{tab_name} Configuration")
                            st.markdown(parsed_content.get(tab_name, "No content generated for this section."))
                            st.download_button(
                                label=f"Download {tab_name}",
                                data=parsed_content.get(tab_name, ""),
                                file_name=f"{tab_name.lower().replace(' ', '_')}_config.txt",
                                mime="text/plain"
                            )
                
            except Exception as e:
                st.error(f"An error occurred: {e}")