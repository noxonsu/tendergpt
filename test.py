import openai
import time

# Создаем экземпляр клиента один раз
openai.organization = "ildario1"

client = openai.OpenAI()

# Загрузка файла с целью "assistants"
#with open("70916611_Извещение.doc", "rb") as file:
#    file_response = client.files.create(file=file, purpose="assistants")

# Создание пустой нити (thread)
empty_thread_response = client.beta.threads.create()
print(empty_thread_response)

# Функция для ожидания завершения выполнения задачи
def wait_for_completion(run):
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(
            thread_id=run.thread_id,
            run_id=run.id
        )
        time.sleep(1)
    return run

# Создание и запуск нити с сообщением и файлом
run_response = client.beta.threads.create_and_run(
    assistant_id="asst_mjrrw6UamzL17K4ow9uz9dT7",
    thread={
        "messages": [
            {
                "role": "user",
                "content": "перечисли критичные условия поставки из этого документа. add annotations",
                "file_ids": ["file-7azqQGuiFwvAyhHTsVX9s2Pb"]
            }
        ]
    }
)



# Ожидание завершения выполнения задачи
completed_run = wait_for_completion(run_response)

# Получение и вывод результатов
thread_messages_response = client.beta.threads.messages.list(completed_run.thread_id)

for message in thread_messages_response.data:
    #if message.role == "assistant" and message.content[0].type == "text":
    print(message.content[0].text.value)
