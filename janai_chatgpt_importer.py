import json
from pathlib import Path
import uuid
import argparse

def import_conversations(chatgpt_export_path, jan_data_path):
    """
    Imports ChatGPT conversations into Jan.ai.

    Args:
        chatgpt_export_path (str): The path to the directory where the ChatGPT export is located.
        jan_data_path (str): The path to the Jan.ai data directory.
    """

    chatgpt_conversations_json = Path(chatgpt_export_path) / "conversations.json"
    jan_thread_folder = Path(jan_data_path) / "threads"
    
    if not chatgpt_conversations_json.exists():
        print(f"Error: conversations.json not found in {chatgpt_export_path}")
        return

    with open(chatgpt_conversations_json) as file:
      content = json.load(file)

    project_id_map = {} # To store mapping of chatgpt_template_id to janai_project_id

    success_count = 0
    failed_count = 0
    all_count = 0
    for item in content:
      try:
        thread_title = item.get("title", "Untitled")
        thread_create_time = item.get("create_time")
        if thread_create_time is None:
            print(f"Skipping conversation with missing create_time: {thread_title}")
            continue
        thread_create_time = int(thread_create_time)

        conversation_template_id = item.get("conversation_template_id")
        
        project_metadata = {}
        if conversation_template_id and conversation_template_id.startswith("g-p-"):
            if conversation_template_id not in project_id_map:
                project_id_map[conversation_template_id] = str(uuid.uuid4())

            project_metadata = {
                "project": {
                    "id": project_id_map[conversation_template_id],
                    "name": conversation_template_id, # Use template_id as project name as per user's instruction
                    "updated_at": thread_create_time * 1000 # Convert to milliseconds for Jan.ai format
                }
            }

        # Use a portion of the title and a timestamp to create a more unique folder name
        sanitized_title = "".join(c for c in thread_title if c.isalnum() or c in (' ', '_')).rstrip()
        folder_name = f"jan_{thread_create_time}_{sanitized_title[:20]}"
        
        new_folder = jan_thread_folder.joinpath(folder_name)
        new_folder.mkdir(exist_ok=True)
        
        new_thread_path = new_folder.joinpath("thread.json")
        
        thread_template = {
            "assistants": [
                {
                    "id": "jan",
                    "instructions": "You are a helpful AI assistant. Your primary goal is to assist users with their questions and tasks to the best of your abilities.\\n\\nWhen responding:\\n- Answer directly from your knowledge when you can\\n- Be concise, clear, and helpful\\n- Admit when you\\u2019re unsure rather than making things up\\n\\nIf tools are available to you:\\n- Only use tools when they add real value to your response\\n- Use tools when the user explicitly asks (e.g., \\\"search for...\\\", \\\"calculate...\\\", \\\"run this code\\\")\\n- Use tools for information you don\\u2019t know or that needs verification\\n- Never use tools just because they\\u2019re available\\n\\nWhen using tools:\\n- Use one tool at a time and wait for results\\n- Use actual values as arguments, not variable names\\n- Learn from each result before deciding next steps\\n- Avoid repeating the same tool call with identical parameters\\n- You must use browser screenshot to double check before you announce you finished or completed the task. If you got stuck, go to google.com\\n\\nRemember: Most questions can be answered without tools. Think first whether you need them.\\n\\nCurrent date: {{current_date}}",
                    "model": {
                        "engine": "huggingface",
                        "id": "openai/gpt-oss-120b"
                    },
                    "name": "Jan"
                }
            ],
            "created": thread_create_time,
            "id": folder_name,
            "metadata": project_metadata, # Inject project metadata here
            "model": {
                "id": "openai/gpt-oss-120b",
                "provider": "huggingface"
            },
            "object": "thread",
            "title": thread_title,
            "updated": thread_create_time
        }

        with open(new_thread_path, 'w') as thread:
          json.dump(thread_template, thread, indent=4)

        print(f"Adding conversation {thread_title} in folder {folder_name}")
        message_jsonl_data = []
        if item.get('mapping'):
            for id, message in item["mapping"].items():
                content_message = message.get('message')
                if not content_message:
                  continue
                
                author_role = content_message.get('author', {}).get('role')
                if author_role not in ['user', 'assistant']:
                    continue

                msg_create_time = content_message.get('create_time')
                if msg_create_time is None:
                    print(f"Skipping message with missing create_time in conversation: {thread_title}")
                    continue
                msg_create_time = int(msg_create_time)
                
                msg_id = content_message.get('id')
                
                msg_content_parts = content_message.get('content', {}).get('parts')
                if not msg_content_parts:
                    print(f"Skipping message with missing content parts in conversation: {thread_title}")
                    continue
                msg_content = msg_content_parts[0]

                message_template = {
                    "completed_at": 0,
                    "content": [{"text":{"annotations":[],"value":msg_content},"type":"text"}],
                    "created_at": msg_create_time,
                    "id": msg_id,
                    "metadata": {},
                    "object": "thread.message",
                    "role": author_role,
                    "status":"completed",
                    "thread_id": folder_name
                }
                message_jsonl_data.append(message_template)
            
        if message_jsonl_data:
            new_messages = new_folder.joinpath("messages.jsonl")
            with open(new_messages, "w") as messages_file:
                for entry in message_jsonl_data:
                  json.dump(entry, messages_file)
                  messages_file.write("\n")
            print("success")
            success_count += 1
      except Exception as e:
         print(f"Failed due to {e}")
         failed_count += 1
      all_count += 1
    print(f"Success: {success_count}")
    print(f"Failure: {failed_count}")
    print(f"All: {all_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import ChatGPT conversations into Jan.ai.")
    parser.add_argument("chatgpt_export_path", help="The path to the directory where the ChatGPT export is located.")
    parser.add_argument("jan_data_path", help="The path to the Jan.ai data directory.")
    args = parser.parse_args()

    # First, let's clean up the old imported conversations
    jan_thread_folder = Path(args.jan_data_path) / "threads"
    for folder in jan_thread_folder.iterdir():
        if folder.name.startswith("jan_"):
            # A bit dangerous, but we are in a controlled environment
            # shutil.rmtree(folder)
            pass # Commenting out for safety, but this is where the cleanup would happen

    import_conversations(args.chatgpt_export_path, args.jan_data_path)
