from config.secrets import *
from config.settings import showAiErrorAlerts
from config.personals import ethnicity, gender, disability_status, veteran_status
from config.questions import *
from config.search import security_clearance, did_masters

from modules.helpers import print_lg, critical_error_log, convert_to_json
from modules.ai.prompts import *

from pyautogui import confirm
from openai import OpenAI
from openai.types.model import Model
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from typing import Iterator, Literal

# AI Configuration Instructions
AI_ERROR_MSG = """
1. Ensure AI API details (URL, key, model) are correct.
2. If using a local LLM, check if the server is running.
3. Verify the appropriate LLM models are loaded.

Check `secrets.py` in `/config` to configure your AI API.
"""

# Function to log AI errors
def ai_error_alert(message: str, stack_trace: str, title: str = "AI Connection Error") -> None:
    global showAiErrorAlerts
    if showAiErrorAlerts:
        if confirm(f"{message}{stack_trace}\n", title, ["Pause AI error alerts", "Okay Continue"]) == "Pause AI error alerts":
            showAiErrorAlerts = False
    critical_error_log(message, stack_trace)

# Function to check for AI errors in responses
def ai_check_error(response: ChatCompletion | ChatCompletionChunk) -> None:
    if response.model_extra.get("error"):
        raise ValueError(f'API Error: "{response.model_extra.get("error")}"')

# Function to create OpenAI client
from openai import OpenAI

def ai_create_openai_client():
    """
    Function to create an OpenAI client.
    """
    try:
        print_lg("Creating OpenAI client...")
        if not use_AI:
            raise ValueError("⚠️ AI is disabled! Enable it in `secrets.py` under `config`.")

        client = OpenAI(base_url=llm_api_url, api_key=llm_api_key)

        models = ai_get_models_list(client)
        if "error" in models:
            raise ValueError(models[1])
        if not models:
            raise ValueError("⚠️ No AI models available!")
        if llm_model not in [model.id for model in models]:
            raise ValueError(f"⚠️ Model `{llm_model}` not found!")

        print_lg(f"✅ OpenAI Client Ready - Using Model: {llm_model}")
        return client
    except Exception as e:
        print(f"❌ AI Client Error: {e}")
        return None  # ✅ Return None if AI client creation fails

# Function to close OpenAI client
def ai_close_openai_client(client: OpenAI) -> None:
    try:
        if client:
            print_lg("Closing OpenAI client...")
            client.close()
    except Exception as e:
        ai_error_alert("Error closing OpenAI client.", e)

# Function to get available AI models
def ai_get_models_list(client: OpenAI) -> list[Model | str]:
    try:
        print_lg("Fetching AI models list...")
        if not client:
            raise ValueError("AI client is unavailable!")
        models = client.models.list()
        ai_check_error(models)
        print_lg(f"✅ Available Models: {models.data}", pretty=True)
        return models.data
    except Exception as e:
        critical_error_log("Error retrieving AI models list!", e)
        return ["error", e]

# Function to call OpenAI API for chat completion
def ai_completion(client: OpenAI, messages: list[dict], response_format: dict = None, temperature: float = 0, stream: bool = stream_output) -> dict | ValueError:
    if not client:
        raise ValueError("AI client is unavailable!")

    request_params = {
        "model": llm_model,
        "messages": messages,
        "temperature": temperature,
        "stream": stream
    }
    if response_format and llm_spec in ["openai", "openai-like"]:
        request_params["response_format"] = response_format

    completion = client.chat.completions.create(**request_params)
    result = ""

    if stream:
        print_lg("-- AI STREAMING STARTED --")
        for chunk in completion:
            ai_check_error(chunk)
            if chunk.choices[0].delta.content:
                result += chunk.choices[0].delta.content
                print_lg(chunk.choices[0].delta.content, end="", flush=True)
        print_lg("\n-- AI STREAMING COMPLETE --")
    else:
        ai_check_error(completion)
        result = completion.choices[0].message.content

    if response_format:
        result = convert_to_json(result)

    print_lg("\n🔎 Extracted AI Response:\n", pretty=response_format)
    return result

# Function to extract skills from job description using AI
def ai_extract_skills(client: OpenAI, job_description: str, stream: bool = False) -> dict:
    """
    Function to extract skills from job description using AI.
    """
    print_lg("-- Extracting Skills from Job Description --")
    
    if client is None:
        print("⚠️ AI Client is unavailable! Skipping AI-related tasks.")
        return {}  # ✅ Return empty dictionary to avoid crashes

    try:
        prompt = extract_skills_prompt.format(job_description)
        messages = [{"role": "user", "content": prompt}]
        response = ai_completion(client, messages, response_format={"type": "json_object"}, stream=stream)

        if isinstance(response, dict) and all(k in response for k in ['tech_stack', 'technical_skills', 'other_skills', 'required_skills', 'nice_to_have']):
            print_lg("✅ Extracted Skills:", response)
            return response
        else:
            print_lg("⚠️ Unexpected AI response format:", response)
            return {}
    except Exception as e:
        print(f"❌ Error extracting skills: {e}")
        return {}


# Function to answer job-related questions using AI
def answer_questions(modal, questions_list, work_location):
    """
    Fills in the application questions, selecting the first available option or entering a default response.
    """
    global aiClient

    # Get all question fields
    questions = modal.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-element")
    
    for question in questions:
        label, default_answer = get_label_and_default_answer(question)  # Get label and predefined answer
        print_lg(f"🔹 Answering: {label} -> {default_answer}")

        try:
            # Handle text input fields
            input_field = question.find_element(By.TAG_NAME, "input")
            input_type = input_field.get_attribute("type")

            if input_type in ["text", "email", "tel"]:
                input_field.clear()
                input_field.send_keys(default_answer)
                continue

            if input_type == "number":
                input_field.clear()
                input_field.send_keys("3")  # Default 3 years experience
                continue

        except NoSuchElementException:
            pass  # No input field found, try other options

        try:
            # Handle dropdown (select menu)
            select_element = Select(question.find_element(By.TAG_NAME, "select"))
            select_element.select_by_index(1)  # Select the first option
            continue

        except NoSuchElementException:
            pass  # No select found, try other options

        try:
            # Handle radio buttons
            radio_buttons = question.find_elements(By.TAG_NAME, "input")
            if radio_buttons:
                radio_buttons[0].click()  # Click first available radio button (e.g., Yes)
                continue

        except NoSuchElementException:
            pass  # No radio button found, try other options

        # If no default value found, use AI to generate an answer
        if aiClient and label not in questions_list:
            print_lg(f"🤖 Using AI to answer: {label}")
            ai_answer = ai_answer_question(aiClient, label)
            questions_list.add(label)

            try:
                input_field = question.find_element(By.TAG_NAME, "input")
                input_field.clear()
                input_field.send_keys(ai_answer)

            except NoSuchElementException:
                pass  # No input field found, skip

    return questions_list
