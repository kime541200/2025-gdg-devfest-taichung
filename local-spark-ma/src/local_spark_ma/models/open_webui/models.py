from enum import Enum
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Union, List, Dict

from ..openai.Openai import OpenaiUsage
from ..chat.Chat import Message


#####################
# Models
#####################
class OpenWebUI_Model(BaseModel):
    id: str
    name: str
    object: str = Field("model")

class OpenWebUI_ListModelsOutput(BaseModel):
    object: str = Field("list")
    data: List[OpenWebUI_Model]


#####################
# File
#####################

class OuiFileData(BaseModel):
    content: str

class OuiFileMeta(BaseModel):
    name: str
    content_type: str
    size: int
    source: Optional[str] = None
    collection_name: str
    chatfile: str

class OuiFileInfo(BaseModel):
    id: str
    user_id: str
    hash: str
    filename: str
    data: OuiFileData
    meta: OuiFileMeta
    created_at: int
    updated_at: int

class OuiCollectionFileMeta(BaseModel):
    name: str
    content_type: str
    size: int
    source: str
    chatfile: str
    collection_name: str

class OuiCollection(BaseModel):
    name: str
    description: str
    
class OuiCollectionData(BaseModel):
    file_ids: List[str]

class OuiCollectionFile(BaseModel):
    id: str
    meta: OuiCollectionFileMeta
    created_at: int
    updated_at: int

class OuiUserData(BaseModel):
    id: str
    name: str
    email: str
    role: str
    profile_image_url: str
    

class AllFilesItem(BaseModel):
    id: str
    type: str
    status: str
    name: str
    file: Optional[OuiFileInfo] = None
    meta: Optional[OuiCollectionFileMeta] = None
    url: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    collection: Optional[OuiCollection] = None
    description: Optional[str] = None
    collection_name: Optional[str] = None
    size: Optional[int] = None
    error: Optional[str] = None
    itemId: Optional[str] = None
    context: Optional[str] = None
    user_id: Optional[str] = None
    data: Optional[OuiCollectionData] = None
    access_control: Optional[str] = None # 待確認類別
    user: Optional[OuiUserData] = None
    files: Optional[List[OuiCollectionFile]] = None
    

#####################
# Open_webui Citations (for Open-webui 0.5.12)
#####################

class FileData(BaseModel):
    content: str = Field(..., description="檔案內容")


class Meta(BaseModel):
    name: str = Field(..., description="檔案名稱")
    content_type: str = Field("text/plain", description="檔案的 MIME 類型")
    size: int = Field(0, description="檔案大小")
    data: Dict = Field(default_factory=dict, description="額外的數據")
    collection_name: str = Field(..., description="檔案集合名稱")


class File(BaseModel):
    id: Union[str, int] = Field(..., description="檔案 ID")
    user_id: str = Field("user_id", description="用戶 ID")
    hash: str = Field("hash", description="檔案哈希值")
    filename: str = Field(..., description="檔案名稱")
    data: FileData = Field(..., description="檔案內容封裝")
    meta: Meta = Field(..., description="檔案的元數據")
    created_at: int = Field(0, description="建立時間 (timestamp)")
    updated_at: int = Field(0, description="更新時間 (timestamp)")


class SourceFile(BaseModel):
    type: str = Field("file", description="來源類型")
    file: File = Field(..., description="檔案詳細資訊")
    id: Union[str, int] = Field(..., description="來源 ID")
    url: str = Field(..., description="檔案 URL")
    name: str = Field(..., description="檔案名稱")
    collection_name: str = Field(..., description="集合名稱")
    status: str = Field("uploaded", description="上傳狀態")
    size: int = Field(0, description="檔案大小")
    error: str = Field("", description="錯誤訊息 (若有)")
    itemId: str = Field("itemId", description="項目 ID")


class MetadataItem(BaseModel):
    created_by: str = Field("user_id", description="建立者 ID")
    embedding_config: str = Field("{\"engine\": \"openai\", \"model\": \"gte-Qwen2-7B-instruct\"}", description="嵌入設定")  # TODO: 目前先固定填現在在使用的嵌入模型
    file_id: Union[str, int] = Field(..., description="關聯檔案 ID")
    hash: str = Field("hash", description="檔案哈希值")
    name: str = Field(..., description="檔案名稱")
    source: str = Field(..., description="來源描述")
    start_index: int = Field(0, description="開始索引")


class SourceData(BaseModel):
    source: SourceFile = Field(..., description="來源檔案詳細資訊")
    document: List[str] = Field(..., description="文件內容列表")
    metadata: List[MetadataItem] = Field(..., description="文件元數據列表")
    distances: List[float] = Field(default_factory=list, description="相關距離或相似度列表")
    

#####################
# Chat-open_webui (stream)
#####################


class OpenwebuiChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = True 
    id: Optional[str] = None
    chat_id: Optional[str] = None
    session_id: Optional[str] = None
    seed: Optional[int] = None
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    logit_bias: Optional[Dict[str, float]] = None
    
    class Config:
        extra = "allow"


class OpenwebuiChatCompletionChunkUsage(BaseModel):
    total_duration: int = Field(..., description="time spent generating the response" )
    load_duration: int = Field(..., description="time spent in nanoseconds loading the model" )
    prompt_eval_count: int = Field(..., description="number of tokens in the prompt" )
    prompt_eval_duration: int = Field(..., description="time spent in nanoseconds evaluating the prompt" )
    eval_count: int = Field(..., description="number of tokens in the response" )
    eval_duration: int = Field(..., description="time in nanoseconds spent generating the response" )
    tokens_per_second: float = Field(..., description="numbers of tokens been generated per second")
    

class OpenwebuiChatCompletionChunkChoiceDelta(BaseModel):
    content: Optional[str] = Field(None, description="The contents of the chunk message.")


class OpenwebuiChatCompletionChunkChoice(BaseModel):
    index: int = Field(0, description="The index of the choice in the list of choices.")
    delta: OpenwebuiChatCompletionChunkChoiceDelta = Field(..., description="A chat completion delta generated by streamed model responses.")
    finish_reason: Optional[str] = Field(None, description="The reason the model stopped generating tokens.")


class OpenwebuiChatCompletionFileTypes(Enum):
    IMAGE = 'image'


class OpenwebuiChatCompletionFiles(BaseModel):
    type: OpenwebuiChatCompletionFileTypes = Field(..., description="The type of file")
    encode_img: Optional[str] = Field(None, description="The encoded image(with image format), can be byte encode or base64 encode")
    url: Optional[str] = Field(None, description="The path to this file", deprecated=True)
    
    @model_validator(mode="after")
    def chk_values(self):
        if self.type == OpenwebuiChatCompletionFileTypes.IMAGE and not (self.encode_img or self.url):
            raise ValueError("Please provide the `encode_img` or `url` of this image.")
        return self


class OpenwebuiChatCompletionChunk(BaseModel):
    id: str = Field(..., description="A unique identifier for the chat completion. Each chunk has the same ID.")
    choices: Optional[List[OpenwebuiChatCompletionChunkChoice]] = Field(None, description='A list of chat completion choices. Can contain more than one elements if `n` is greater than 1. Can also be empty for the last chunk if you set `stream_options: {"include_usage": true}`.')
    created: float = Field(..., description="The Unix timestamp (in seconds) of when the chat completion was created. Each chunk has the same timestamp.")
    model: str = Field(..., description="The model used to generate the chat completion.")
    object: str = Field("chat.completion.chunk", description="The object type, which is always `chat.completion.chunk`.")
    done: bool= Field(False, description="A boolean indicating whether the chat completion is done.")
    done_reason: Optional[str] = Field(None, description="A reason why the chat completion is done.")
    usage: Optional[Union[OpenwebuiChatCompletionChunkUsage | OpenaiUsage]] = Field(None, description="Information about the usage of tokens in this chunk.")
    files: Optional[List[OpenwebuiChatCompletionFiles]] = Field(None, description="要輸出到前端的檔案")
    sources: Optional[List[SourceData]] = Field(None, description="Citations associated with this chunk of text.")