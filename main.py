# Third-party imports
from openai import OpenAI
from fastapi import FastAPI, Form, Depends
from decouple import config
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Internal imports
from models import Conversation, SessionLocal
from utils import send_message, logger


app = FastAPI()
# Set up the OpenAI API client
client = OpenAI(api_key=config("OPENAI_API_KEY"))
whatsapp_number = config("TO_NUMBER")

# Dependency
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@app.post("/message")
async def reply(Body: str = Form(),
                db: Session = Depends(get_db)
                ):
    # Call the OpenAI API to generate text with GPT-3.5
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 使用新接口推荐的模型，比如 gpt-3.5-turbo 或 gpt-4
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},  # 系统消息，用来设定模型角色
            {"role": "user", "content": Body}  # 用户输入的内容
        ],
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.5,
    )

    # The generated text
    chat_response = response.choices[0].message.content.strip()

    # Store the conversation in the database
    try:
        conversation = Conversation(
            sender=whatsapp_number,
            message=Body,
            response=chat_response
            )
        # db.add(conversation)
        # db.commit()
        logger.info(f"Conversation #{conversation.id} stored in database")
    # except:
    #     None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error storing conversation in database: {e}")
    send_message(whatsapp_number, chat_response)
    return ""