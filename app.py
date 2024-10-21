from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI
from shiny.express import input, render, ui
from shiny import ui as shinyui
import logging
from langchain_openai import ChatOpenAI
import re
from docx import Document
from shiny.express import input, render, ui

models = {
    "openai": ["gpt-4o", "gpt-3.5-turbo"],
    "claude": [
        "claude-3-opus-20240229",
        "claude-3-5-sonnet-20240620",
        "claude-3-haiku-20240307",
    ],
    "google": ["gemini-1.5-pro-latest"],
}

model_choices: dict[str, dict[str, str]] = {}
for key, value in models.items():
    model_choices[key] = dict(zip(value, value))

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        logging.error(f"Error extracting text from docx: {str(e)}")
        return ""

def create_timestamp_dictionary(content):
    lines = content.split('\n')
    
    timestamp_dict = {}
    current_timestamp = None
    current_text = []

    for line in lines:
        if re.match(r'^\d+:\d+$', line.strip()):
            if current_timestamp:
                timestamp_dict[current_timestamp] = ' '.join(current_text).strip()
            current_timestamp = line.strip()
            current_text = []
        else:
            if line.strip():
                current_text.append(line.strip())

    if current_timestamp:
        timestamp_dict[current_timestamp] = ' '.join(current_text).strip()

    return timestamp_dict

def get_context_before_timestamp(timestamp_dict, current_timestamp):
    timestamp_seconds = {sum(int(x) * 60 ** i for i, x in enumerate(reversed(ts.split(':')))):ts 
                         for ts in timestamp_dict.keys()}
    
    context_timestamps = [ts for ts in timestamp_seconds.keys() if ts <= current_timestamp]
    
    context = []
    for ts in sorted(context_timestamps):
        original_ts = timestamp_seconds[ts]
        context.append(f"{original_ts}: {timestamp_dict[original_ts]}")

    return "\n\n".join(context)

file_path = 'Transcription for Mod 1 Lecture 2.docx'
document_content = extract_text_from_docx(file_path)
timestamp_dict = create_timestamp_dictionary(document_content)

shinyui.page_fluid(
    ui.tags.head(
        ui.tags.script(src="https://www.youtube.com/iframe_api"),
        ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css"),
        ui.tags.style("""
            body { 
                font-family: 'Roboto', sans-serif; 
                background-color: #f0f2f5;
                color: #333;
            }
            .app-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 30px;
                background-color: white;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
                border-radius: 12px;
            }
            .app-title {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 15px;
                margin-bottom: 30px;
                font-size: 2.5em;
                font-weight: 700;
            }
            .video-container {
                background-color: #f9f9f9;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                height: 100%;
            }
            .chat-container {
                background-color: #fff;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                height: 600px;
                display: flex;
                flex-direction: column;
            }
            .chat-messages {
                flex-grow: 1;
                overflow-y: auto;
                padding: 20px;
            }
            .chat-input {
                padding: 20px;
                background-color: #f0f0f0;
                border-top: 1px solid #ddd;
            }
            .current-time {
                margin-top: 15px;
                font-weight: bold;
                color: #2c3e50;
                font-size: 1.1em;
            }
            .sidebar {
                background-color: #f0f0f0;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .sidebar .form-group {
                margin-bottom: 20px;
            }
            .sidebar label {
                font-weight: 600;
                color: #2c3e50;
            }
            .btn-primary {
                background-color: #3498db;
                border-color: #3498db;
            }
            .btn-primary:hover {
                background-color: #2980b9;
                border-color: #2980b9;
            }
        """)
    ),
    shinyui.div(
        {"class": "app-container"},
        shinyui.h1("Interactive Video Learning", class_="app-title"),
        shinyui.row(
            shinyui.column(6,
                shinyui.div(
                    {"class": "video-container"},
                    shinyui.tags.div(id="player"),
                )
            ),
            shinyui.column(6,
                shinyui.div(
                    {"class": "chat-container"},
                    # shinyui.div(
                    #     {"class": "chat-messages"},
                    #     shinyui.panel_title("AI Tutor Chat"),
                    #     shinyui.chat_ui("chat", placeholder="Ask a question about the video...")
                    #     fillable_mobile=True,
                    # )
                    shinyui.page_fillable(
                    shinyui.chat_ui("chat", placeholder="Ask a question about the video..."),
                    fillable_mobile=True,
                )
                )
            )
        ),
        shinyui.br(),
        shinyui.row(
            shinyui.column(12,
                shinyui.div(
                    {"class": "sidebar"},
                    shinyui.row(
                        shinyui.column(3, ui.input_select("model", "AI Model", choices=model_choices)),
                        shinyui.column(3, ui.input_slider("temperature", "Temperature", min=0, max=2, step=0.1, value=1)),
                        shinyui.column(3, ui.input_slider("max_tokens", "Max Tokens", min=1, max=4096, step=1, value=100))
                    )
                )
            )
        )
    ),
    shinyui.tags.script("""
        var player;
        function onYouTubeIframeAPIReady() {
            player = new YT.Player('player', {
                height: '400',
                width: '100%',
                videoId: '8P_C-SRwheE',
                events: {
                    'onReady': onPlayerReady
                }
            });
        }
                        
        function onPlayerReady(event) {
            setInterval(updateTime, 1000);
        }
        
        function updateTime() {
            if (player && player.getCurrentTime) {
                var time = player.getCurrentTime();
                Shiny.setInputValue('videoTime', time);
            }
        }
    """)
)

@render.express(fill=True, fillable=True)
def chat_ui():
    chat = ui.Chat(id="chat", messages=[])
    model_params = {
        "model": input.model(),
        "temperature": input.temperature(),
        "max_tokens": input.max_tokens(),
    }
    if input.model() in models["openai"]:
        llm = ChatOpenAI(**model_params)
    elif input.model() in models["claude"]:
        llm = ChatAnthropic(**model_params)
    else:
        raise ValueError(f"Invalid model: {input.model()}")

    @chat.on_user_submit
    async def _():
        current_timestamp = input.videoTime()
        if current_timestamp is not None:
            context = get_context_before_timestamp(timestamp_dict, current_timestamp)
        else:
            context = ''

        # Get the user's input
        user_input = chat.user_input()

        # Construct the system message with the context
        system_message = {
            "content": f"""
            You are a helpful assistant for a microbiology course at Harvard Medical School. You answer student questions relating to video lecture material. You never answer questions that are unrelated to the video lecture.
            Video Transcript up to current moment: {context}. Answer the student's question, referencing your own knowledge and the information in the transcript. Do not answer questions that do not relate to the context.
            """,
            "role": "system",
        }

        # Get all messages, including the system message
        chat_messages = chat.messages(format="langchain")
        messages = [system_message] + (list(chat_messages) if isinstance(chat_messages, tuple) else chat_messages)

        # Add the user's latest input
        messages.append({"role": "user", "content": user_input})

        # Generate and stream the response
        response = llm.astream(messages)
        await chat.append_message_stream(response)
