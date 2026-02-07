from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os

app = FastAPI()

# Allow React (running on port 5173) to talk to FastAPI (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# def run_terraform():
#     # Replace with the path to your terraform folder
#     os.chdir("./terraform")
#     subprocess.run(["terraform", "apply", "-auto-approve"])

# @app.post("/deploy")
# async def deploy_infra(background_tasks: BackgroundTasks):
#     background_tasks.add_task(run_terraform)
#     return {"message": "Deployment started! Check your Proxmox console."}
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/status")
async def get_status():
    # Simple check to see if the bridge we made is active
    result = subprocess.run(["ip", "a", "show", "vmbr1"], capture_output=True, text=True)
    return {"online": "10.10.10.1" in result.stdout}