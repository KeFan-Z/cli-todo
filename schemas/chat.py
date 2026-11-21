from openai import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str


class AskRequest(BaseModel):
    question: str


class AgentChatRequest(BaseModel):
    message: str
    history: list[dict] = []
