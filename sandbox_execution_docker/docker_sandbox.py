from dotenv import load_dotenv
import docker
import os
import argparse
import time


load_dotenv()

class DockerSandbox:
    def __init__(self):
        self.client = docker.from_env()
        self.container = None
        self.image_name = "agent-sandbox"

    def build_image(self):
        try:
            print("Building Docker image...")
            image, build_logs = self.client.images.build(
                path=".",  # Assumes Dockerfile is in current directory
                tag=self.image_name,
                rm=True,
                forcerm=True
            )
            print("Image built successfully")
            return image
        except docker.errors.BuildError as e:
            print("Build error logs:")
            for log in e.build_log:
                if 'stream' in log:
                    print(log['stream'].strip())
            raise

    def create_container(self):
        if not self.container:
            try:
                # Ensure image exists
                try:
                    self.client.images.get(self.image_name)
                except docker.errors.ImageNotFound:
                    self.build_image()
                
                print("Creating container...")
                # Create container with security constraints
                self.container = self.client.containers.run(
                    self.image_name,
                    command="tail -f /dev/null",  # Keep container running
                    detach=True,
                    tty=True,
                    mem_limit="512m",
                    cpu_quota=50000,
                    pids_limit=100,
                    security_opt=["no-new-privileges"],
                    cap_drop=["ALL"],
                    environment={
                        "HF_TOKEN": os.getenv("HF_TOKEN"),
                        "OPENAI_MODEL": os.getenv("OPENAI_MODEL"),
                        "OPENAI_API_URL":os.getenv("OPENAI_API_URL"),
                        "API_KEY": os.getenv("API_KEY")
                    },
                    volumes={
                        os.path.abspath("."): {"bind": "/app", "mode": "ro"}
                    }
                )
                print(f"Container created with ID: {self.container.id}")
            except Exception as e:
                print(f"Error creating container: {e}")
                raise

    def run_agent_file(self, agent_file, query=None):
        self.create_container()
        
        # Prepare command to run the agent file
        cmd = ["python", agent_file]
        if query:
            cmd.append(query)
        
        print(f"Running agent with command: {' '.join(cmd)}")
        
        # Execute code in container
        exec_result = self.container.exec_run(
            cmd=cmd,
            user="nobody"
        )
        
        # Get output
        output = exec_result.output.decode() if exec_result.output else None
        exit_code = exec_result.exit_code
        
        if exit_code != 0:
            print(f"Warning: Command exited with code {exit_code}")
        
        return output

    def cleanup(self):
        if self.container:
            try:
                print(f"Stopping container {self.container.id}...")
                self.container.stop()
                print(f"Removing container {self.container.id}...")
                self.container.remove()
                print("Container removed")
            except docker.errors.NotFound:
                # Container already removed
                pass
            except Exception as e:
                print(f"Error during cleanup: {e}")
            finally:
                self.container = None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run agent code in a Docker sandbox')
    parser.add_argument('agent_file', help='Python file containing the agent code')
    parser.add_argument('--query', help='Query to pass to the agent')
    args = parser.parse_args()
    
    sandbox = DockerSandbox()
    
    try:
        # Run the agent file in the sandbox
        output = sandbox.run_agent_file(args.agent_file, args.query)
        print("Agent output:")
        print(output)
    finally:
        sandbox.cleanup()