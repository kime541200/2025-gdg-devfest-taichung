from pydantic import BaseModel, Field, PositiveInt, NonNegativeInt
from typing import Optional, Literal, List


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

    @classmethod
    def from_dicts(cls, data: List[dict]) -> List["Message"]:
        return [cls(**item) for item in data]

    @classmethod
    def to_dicts(cls, messages: List["Message"]) -> List[dict]:
        return [msg.model_dump() for msg in messages]
    
    @classmethod
    def to_convo_string(cls, messages: List["Message"]) -> str:
        convo_string = ""
        for msg in messages:
            convo_string += msg.model_dump_json()
        return convo_string


class IncontextLearnMessage(BaseModel):
    role: str
    content: str


class IncontextLearn(BaseModel):
    shots: List[IncontextLearnMessage]


class ChatConfig(BaseModel):
    system: Optional[str] = Field(None, description='set system prompt')
    template: Optional[str] = Field(None, description='set prompt template')
    incontext_learns: Optional[List[IncontextLearn]] = Field(None, description='set few-shot prompt to do the in-context learning')

    generate_retry: PositiveInt = Field(5, description='the maximum number of times the output can be regenerated')
    
    use_tool: bool = Field(False, description="Whether the model able to use tool.")
    
    use_history: bool = Field(False, description="Whether to use chat history, if set to `Ture`, system automatically summary the conversation once it over the model's context window.")
    history_window: NonNegativeInt = Field(5, description=
        """
        If set `use_history` to `True`, system automatically summary/trim the amount conversation reach the value. 
        ex1: if set to `3`, means to keep up to 3 latest user message and 3 latest assistant message in conversation history.
        ex2: if set to `0`, means to keep all chat history, but system will still trim the older message when the token of conversation is higher than the context size.
        """
        )