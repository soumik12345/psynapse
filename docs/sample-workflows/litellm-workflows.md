# LiteLLM Workflows

## LiteLLM LLM Response

This workflow demonstrates how to use the LiteLLM to generate a response to a user's message.

[ :material-download: Download Workflow](../assets/workflows/litellm-llm-response.json){ .md-button .md-button--primary }

???+ note
    - Make sure that you have the respective environment variable set in preferences.
    - Make sure that the output mode in the `Text` Node is set to `LiteLLM Content`.
    - The exact index to access the response from a non-reasoning OpenAI response is `['choices'][0]['message']['content']`. This is the value that you need to pass to the `query with index` node.

![](../assets/images/litellm-llm-response.png)

## LiteLLM Vision Response

This workflow demonstrates how to use the LiteLLM to generate a response to a user's message to use the vision capabilities of an LLM.

[ :material-download: Download Workflow](../assets/workflows/openai-vision-response.json){ .md-button .md-button--primary }

???+ note
    - Make sure that you have the respective environment variable set in preferences.
    - Make sure that the output mode in the `Text` and `Image` Nodes is set to `LiteLLM Content`.
    - The exact index to access the response from a non-reasoning OpenAI response is `['choices'][0]['message']['content']`. This is the value that you need to pass to the `query with index` node.

![](../assets/images/litellm-vision-response.png)