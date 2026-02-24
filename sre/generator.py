import streamlit as st
import os
from google import genai  # Use the new SDK
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
# The new SDK uses genai.Client() and handles models through client.models
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.5-flash"

# --- UI LAYOUT ---
with st.sidebar:
    st.header("Project Settings")
    project_type = st.selectbox("Project Type", ["Python/Flask", "Node.js", "Go", "Java/Spring", "C++ (CMake)"])
    include_docker = st.checkbox("Dockerfile", value=True)
    include_k8s = st.checkbox("Kubernetes Manifests", value=True)
    include_terraform = st.checkbox("Terraform (EKS/VPC)", value=True)
    include_actions = st.checkbox("GitHub Actions", value=True)
    
    st.divider()
    st.info("SRE Tip: Always use multi-stage builds for smaller, more secure images.")

st.subheader("1. Project Directory Structure")
tree_input = st.text_area("Paste your project tree here:", height=200, placeholder="""
my-app/
├── src/
│   └── main.py
├── requirements.txt
└── README.md
""")

def generate_devops_files(tree, p_type, configs):
    selected_configs = [c for c, v in configs.items() if v]
    
    prompt = f"""
    Act as a Senior Site Reliability Engineer. 
    Analyze this directory structure: {tree}
    
    This is a {p_type} project.
    Generate production-grade configurations for: {', '.join(selected_configs)}.
    
    Requirements:
    - Docker: Multi-stage builds, non-root user, optimized caching.
    - K8s: Deployment (with resource limits), Service, and HPA.
    - Terraform: Use official AWS modules for VPC and EKS.
    - GitHub Actions: Build and Push to ECR, then deploy to EKS.
    
    Output each file in a clear Markdown code block.
    """
    
    # NEW SDK SYNTAX: client.models.generate_content
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt
    )
    return response.text

if st.button("🚀 Generate Scaffolding"):
    if not tree_input:
        st.error("Please provide a directory tree.")
    else:
        configs = {
            "Dockerfile": include_docker,
            "Kubernetes": include_k8s,
            "Terraform": include_terraform,
            "GitHub Actions": include_actions
        }
        
        with st.spinner(f"Using {MODEL_ID} to architect your infrastructure..."):
            try:
                result = generate_devops_files(tree_input, project_type, configs)
                st.success("Infrastructure generated successfully!")
                
                # Render the AI response
                st.markdown(result)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")