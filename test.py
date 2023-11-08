from openai import OpenAI
import time
client = OpenAI()


# Upload a file with an "assistants" purpose
file = client.files.create(
  file=open("70916611_Извещение.doc", "rb"),
  purpose="assistants"
)


empty_thread = client.beta.threads.create(

)
print(empty_thread)

tid = empty_thread.id #"thread_MYpjAVCkzx3EKSSD7uAHNeR8"

from openai import OpenAI
client = OpenAI()

run = client.beta.threads.create_and_run(
  assistant_id="asst_mjrrw6UamzL17K4ow9uz9dT7",
  thread={
    "messages": [
      {"role": "user", 
      "content": "фракционный жир",
      "file_ids": [file.id]
      }
    ]
  }
)


while (run.status == "queued" or run.status == "in_progress"):
  run = client.beta.threads.runs.retrieve(
    thread_id=run.thread_id,
    run_id=run.id
  )
  time.sleep(1)

#print result
thread_messages = client.beta.threads.messages.list(run.thread_id)


# Assuming thread_messages.data is a list of ThreadMessage objects
for message in thread_messages.data:
    # Access the 'content' attribute of the ThreadMessage object
    for content in message.content:  # Use dot notation here
        if content.type == 'text':
            print(content.text.value)

