from flask import Flask, request, jsonify, render_template
from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential
from azure.ai.agents.models import ListSortOrder
import time

app = Flask(__name__)

# Replace with your actual endpoint and agent ID
AZURE_PROJECT_ENDPOINT = "https://aqnaz-me7h81i9-eastus2.services.ai.azure.com/api/projects/aqnaz-me7h81i9-eastus2_project"
AGENT_ID = "asst_FKK010NLy2Wq7lDf5leaZi8n"

# Initialize project and agent
project = AIProjectClient(
    credential=AzureCliCredential(),
    endpoint=AZURE_PROJECT_ENDPOINT
)
agent = project.agents.get_agent(AGENT_ID)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "")

    # Create a new thread and send user message
    thread = project.agents.threads.create()
    project.agents.messages.create(thread_id=thread.id, role="user", content=user_input)

    # Start and poll the run until complete
    run = project.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

    while run.status not in ["completed", "failed"]:
        time.sleep(1)
        run = project.agents.runs.get(thread_id=thread.id, run_id=run.id)

    if run.status == "failed":
        return jsonify({"response": f"Run failed: {run.last_error}"}), 500

    # Collect and combine all assistant messages
    messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    response_parts = []

    for message in messages:
        if message.role == "assistant" and message.text_messages:
            for text in message.text_messages:
                response_parts.append(text.text.value)

    full_response = "\n\n".join(response_parts)

    return jsonify({"response": full_response or "No reply generated."})


if __name__ == "__main__":
    app.run(debug=True)
