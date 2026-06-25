Minimal AI agent with tool calling and zero dependencies in 60 lines of Python

<div align="center">
    <img alt="Agent demo execution example" src="https://github.com/user-attachments/assets/27e05a96-3e80-4609-a7d9-6333df2b3b26" />
</div>

# Code

```python
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
            print(f"Reply:\n{msg.get('content', '')}")
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
```

# Installation

```
git clone https://github.com/99991/MinimalAgent.git
cd MinimalAgent
python3 agent.py
```

By default, the `big-pickle` model ([GLM-4.6](https://github.com/anomalyco/opencode/issues/4276)) provided by OpenCode is used, which might be overloaded.

If you have your own OpenAI-compatible API that you want to use, change the API key, URL and model in the code.
You can also use a self-hosted model:

# Using a local model with llama.cpp's `llama serve`

1. Install [llama.cpp's](https://github.com/ggml-org/llama.cpp) [llama app](https://llama.app/):

```bash
curl -LsSf https://llama.app/install.sh | sh
```

2. Serve a model, e.g. Qwen3.5-4B:
```bash
llama serve --no-mmproj -hf unsloth/Qwen3.5-4B-GGUF:Q5_K_M
```

  * This model is very small (only about 4GB of VRAM) and has only been chosen due to its accessibility. See [llama.app](https://llama.app) and [HuggingFace](https://huggingface.co/models?apps=llama.cpp) for more models. Qwen3.6-27B is pretty good if you have the (V)RAM, but might get stuck in loops if quantized too heavily (gets better with Q5 and up).

3. Change the URL in the `call_llm` function to the `llama-server` URL:

```python
def call_llm(messages, url="http://127.0.0.1:8080/v1/chat/completions"):
```

4. Run `python agent.py`

# Explanation

At its core, AI agents are very simple. All they do is:

1. Append the user's prompt to the current context
2. Query an LLM for tool calls and text replies
3. Run the tools (`bash` in our case)
4. Append the tool outputs and text reply to the context
5. Continue at 1.

Since LLMs are very proficient in using `bash`, they don't necessarily require any other tools. They can just use `bash` to do whatever they need, e.g. edit files using `sed` or make HTTP requests using `curl`.
