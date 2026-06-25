import json
import urllib.request
from subprocess import check_output, STDOUT, CalledProcessError

headers = {
    #"Authorization": f"Bearer SET_YOUR_API_KEY_HERE_IF_YOU_HAVE_ONE",
    "Content-Type": "application/json",
    "User-Agent": "Minimal Agent/0.1",
}

def call_llm(messages, url="https://opencode.ai/zen/v1/chat/completions"): # Set URL here
    payload = {
        "model": "big-pickle", # Set model here
        "messages": messages,
        "tools": [{
            "type": "function",
            "function": {
                "name": "bash",
                "description": "Runs a bash command.",
                "parameters": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
            },
        }],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def bash(command):
    try:
        return check_output(command, stderr=STDOUT, text=True)
    except CalledProcessError as e:
        return f"[ERROR: exit code {e.returncode} for `{command}`]\n" + e.output

messages = [{"role": "system", "content": "You are a helpful assistant."}]

while True:
    prompt = input(">> ")

    messages.append({"role": "user", "content": prompt})

    while True:
        response = call_llm(messages)
        msg = response["choices"][0]["message"]
        messages.append(msg)

        tool_calls = msg.get("tool_calls")

        if not tool_calls:
            print(msg.get("content", ""))
            break

        for tool_call in tool_calls:
            fn = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            tool_call_id = tool_call["id"]
            command = ["bash", "-c", tool_args["command"]]

            print(f"[Tool: {fn}] {json.dumps(tool_args)}")

            result = bash(command) if fn == "bash" else f"Unknown tool {fn}"

            print(result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result,
            })
