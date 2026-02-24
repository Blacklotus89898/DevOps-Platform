import streamlit as st
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="SRE Automation Generator", layout="wide")
st.title("🛠️ SRE & DevOps Scaffold Generator")

# Setup Google AI
API_KEY = "AIzaSyAQ42AVV4dkX48IKChuHb3fgVaIMrF3DXY" # Replace with your actual key
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- UI LAYOUT ---
with st.sidebar:
    st.header("Project Settings")
    project_type = st.selectbox("Project Type", ["Python/Flask", "Node.js", "Go", "Java/Spring"])
    include_docker = st.checkbox("Dockerfile", value=True)
    include_k8s = st.checkbox("Kubernetes Manifests", value=True)
    include_terraform = st.checkbox("Terraform (EKS/VPC)", value=True)
    include_actions = st.checkbox("GitHub Actions", value=True)

st.subheader("1. Paste Project Directory Tree")
tree_input = st.text_area("Paste 'tree' output or describe structure:", height=200, placeholder="""
my-app/
├── src/
│   └── app.py
├── requirements.txt
└── static/
""")

def generate_devops_files(tree, p_type, configs):
    prompt = f"""
    Act as a Senior SRE. Based on this project tree:
    {tree}
    
    This is a {p_type} project.
    Generate the following configurations as separate code blocks:
    {', '.join([c for c, v in configs.items() if v])}
    
    Ensure the Dockerfile uses best practices (multi-stage builds), 
    K8s includes a Deployment and Service, and Terraform uses AWS EKS modules.
    """
    response = model.generate_content(prompt)
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
        
        with st.spinner("Gemini is architecting your infrastructure..."):
            result = generate_devops_files(tree_input, project_type, configs)
            
            # Display results in Tabs for clean UI
            tabs = st.tabs([c for c, v in configs.items() if v])
            
            # Note: This logic assumes Gemini outputs separate blocks. 
            # In a production version, you'd parse the Markdown blocks.
            st.markdown(result)