import datetime
import os
import time

from azure.batch import BatchServiceClient, batch_auth
from azure.batch.models import (
    ContainerConfiguration,
    ImageReference,
    PoolAddParameter,
    VirtualMachineConfiguration,
)
from dotenv import load_dotenv

load_dotenv(verbose=True)  # take environment variables

# Azure Batch credentials
account = os.getenv("AZURE_BATCH_ACCOUNT_NAME", None)
key = os.getenv("AZURE_BATCH_ACCOUNT_KEY", None)
batch_url = os.getenv("AZURE_BATCH_ACCOUNT_URL", None)

# Container registry details
registry_server = os.getenv("CONTAINER_REGISTRY_LOGIN_SERVER", None)
registry_username = os.getenv("CONTAINER_REGISTRY_LOGIN_USERNAME", None)
registry_password = os.getenv("CONTAINER_REGISTRY_LOGIN_PASSWORD", None)

# Create batch client
creds = batch_auth.SharedKeyCredentials(account, key)
client = BatchServiceClient(creds, batch_url)

# Configure the pool
pool_id = f"docker-pool-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
vm_size = "Standard_D2s_v3"
node_count = 2
sku = "22_04-lts-gen2"

image_name = os.getenv("IMAGE_NAME", "solar-panel-processor:latest")

# Create container configuration
container_conf = ContainerConfiguration(
    type="dockerCompatible",
    container_image_names=[f"{registry_server}/{image_name}"],
    container_registries=[
        {
            "registry_server": registry_server,
            "user_name": registry_username,
            "password": registry_password,
        }
    ],
)

# Configure the pool with Ubuntu image
image_ref = ImageReference(
    publisher="microsoft-dsvm", offer="ubuntu-hpc", sku="2204", version="latest"
)

vm_config = VirtualMachineConfiguration(
    image_reference=image_ref,
    node_agent_sku_id="batch.node.ubuntu 22.04",
    container_configuration=container_conf,
)

pool = PoolAddParameter(
    id=pool_id,
    vm_size=vm_size,
    target_dedicated_nodes=node_count,
    virtual_machine_configuration=vm_config,
)

# Create the pool
client.pool.add(pool)

print("Waiting for pool to be created...")


while True:
    pool_info = client.pool.get(pool_id)
    if pool_info.state == "active":
        break
    print(f"Pool state: {pool_info.state}. Waiting...")
    time.sleep(10)

client.pool.delete(pool_id)

# # Create a job
# job_id = f"docker-job-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
# job = JobAddParameter(id=job_id, pool_info={"pool_id": pool_id})

# client.job.add(job)

# # Create tasks with different inputs
# task_inputs = ["input1.json", "input2.json", "input3.json"]

# for idx, task_input in enumerate(task_inputs):
#     task_id = f"task_{idx}"

#     # Configure container command line
#     command_line = f"python /app/main.py --input {task_input}"

#     task = TaskAddParameter(
#         id=task_id,
#         command_line=f"/bin/bash -c '{command_line}'",
#         container_settings={
#             "image_name": f"{registry_server}/your-image:latest",
#             "working_directory": "TaskContainer",
#         },
#     )

#     client.task.add(job_id=job_id, task=task)

# print(f"Created pool {pool_id}")
# print(f"Created job {job_id} with {len(task_inputs)} tasks")
