import os
from pydantic import BaseModel, Field, field_validator, PositiveInt, NonNegativeInt, NonNegativeFloat
from typing import Optional, Literal, Union, List, Dict, Any


def _get_openai_api_key():
    """從環境變數獲取 OPENAI_API_KEY，如果不存在則返回預設值 'key'"""
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        return "dummy-key"
    elif key.startswith("sk-"):
        return key
    else:
        return "dummy-key"    


class OpenaiStreamOptions(BaseModel):
    include_usage: bool = Field(True, description="If set, an additional chunk will be streamed before the `data: [DONE]` message. The `usage` field on this chunk shows the token usage statistics for the entire request, and the `choices` field will always be an empty array. All other chunks will also include a `usage` field, but with a null value.")


class OpenaiFunction(BaseModel):
    description: Optional[str] = Field(None, description="A description of what the function does, used by the model to choose when and how to call the function.")
    name: str = Field(..., description="The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.")
    parameters: Optional[Dict[str, Any]] = Field(None, description="The parameters the functions accepts, described as a JSON Schema object, detail refer to https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools")
    strict: bool = Field(False, description="Whether to enable strict schema adherence when generating the function call. If set to true, the model will follow the exact schema defined in the `parameters` field. Only a subset of JSON Schema is supported when `strict` is `true`. Learn more about Structured Outputs in the [function calling guide](https://platform.openai.com/docs/api-reference/chat/docs/guides/function-calling).")


class OpenaiTool(BaseModel):
    type: str = Field("function", description="The type of the tool. Currently, only `function` is supported.")
    function: OpenaiFunction = Field(..., description="Function setting")


class OpenaiOptions(BaseModel):
    frequency_penalty: float = Field(0, description="Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.")
    logit_bias: Optional[Dict] = Field(None, description="Modify the likelihood of specified tokens appearing in the completion. (detail refer to: https://platform.openai.com/docs/api-reference/chat/create#chat-create-logit_bias)")
    logprobs: bool = Field(False, description="Whether to return log probabilities of the output tokens or not. If true, returns the log probabilities of each output token returned in the `content` of `message`.")
    top_logprobs: Optional[NonNegativeInt] = Field(None, description="An integer between 0 and 20 specifying the number of most likely tokens to return at each token position, each with an associated log probability. `logprobs` must be set to `true` if this parameter is used.")
    max_completion_tokens: Optional[PositiveInt] = Field(None, description="An upper bound for the number of tokens that can be generated for a completion, including visible output tokens and reasoning tokens.")
    n: Optional[PositiveInt] = Field(1, description="How many chat completion choices to generate for each input message. Note that you will be charged based on the number of generated tokens across all of the choices. Keep `n` as `1` to minimize costs.")
    modalities: Optional[List[str]] = Field(["text"], description="Output types that you would like the model to generate for this request.")
    presence_penalty: float = Field(0, description="Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.")
    response_format: Optional[Dict[str, Any]] = Field(None, description="An object specifying the format that the model must output, detail refer to https://platform.openai.com/docs/api-reference/chat/create#chat-create-response_format")
    seed: Optional[int] = Field(None, description="This feature is in Beta. If specified, our system will make a best effort to sample deterministically, such that repeated requests with the same `seed` and parameters should return the same result. Determinism is not guaranteed, and you should refer to the `system_fingerprint` response parameter to monitor changes in the backend.")
    stream: bool = Field(False, description="If set to `True`, partial message deltas will be sen")
    temperature: NonNegativeFloat = Field(1, description="What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. We generally recommend altering this or `top_p` but not both.")
    top_p: NonNegativeFloat = Field(1.0, description="An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered. We generally recommend altering this or `temperature` but not both.")
    tools: Optional[List[OpenaiTool]] = Field(None, description="A list of tools the model may call. Currently, only functions are supported as a tool. Use this to provide a list of functions the model may generate JSON inputs for. A max of 128 functions are supported.")
    parallel_tool_calls: bool = Field(True, description="Whether to enable [parallel function calling](https://platform.openai.com/docs/guides/function-calling#configuring-parallel-function-calling) during tool use.")
    stream_option: Optional[OpenaiStreamOptions] = Field(None, description="Options for streaming response. Only set this when you set `stream` to `True`.")
    
    class Config:
        extra = "allow"  
    
    @field_validator("frequency_penalty")
    def chk_frequency_penalty(cls, v):
        if not -2.0 <= v <= 2.0:
            raise ValueError(f"`frequency_penalty` must be a value between -2.0 to 2.0")
        return v
    
    @field_validator("top_logprobs")
    def chk_top_logprobs(cls, v):
        if v and not 0 <= v <= 20:
            raise ValueError(f"`top_logprobs` must be a value between 0 to 20")
        return v
    
    @field_validator("presence_penalty")
    def chk_presence_penalty(cls, v):
        if not -2.0 <= v <= 2.0:
            raise ValueError(f"`presence_penalty` must be a value between -2.0 to 2.0")
        return v
    
    @field_validator("temperature")
    def chk_ptemperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError(f"`temperature` must be a value between 0 to 2")
        return v


class OpenaiConfig(BaseModel):
    base_url: str = Field(default='https://api.openai.com/v1', description="The base URL for the OpenAI API.")
    api_key: str = Field(default_factory=_get_openai_api_key, description="Your OpenAI API key used for authenticating requests.")
    timeout: PositiveInt = Field(30, description="Maximum duration (in seconds) to wait for a response from the API.")
    max_retries: PositiveInt = Field(3, description="The number of times to retry requests in case of transient errors.")    
    model: str = Field("gpt-4o-mini", description="Which models work with the Chat API.")    
    options: OpenaiOptions = Field(default_factory=OpenaiOptions, description="LLM模型參數")
    
    class Config:
        extra = "allow"
    

class OpenaiUsage(BaseModel):
    completion_tokens: int = Field(..., description="Number of tokens in the generated completion.")
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt.")
    total_tokens: int = Field(..., description="Total number of tokens used in the request (prompt + completion).")



#####################
# OpenAI ChatCompletionObject (invoke)
#####################


class ChatCompletionObjectChoiceLogprobsContentTopLogprobs(BaseModel):
    token: str = Field(..., description="The token.")
    logprob: float = Field(..., description="The log probability of this token, if it is within the top 20 most likely tokens. Otherwise, the value `-9999.0` is used to signify that the token is very unlikely.")
    bytes: Optional[List[int]] = Field(None, description="A list of integers representing the UTF-8 bytes representation of the token. Useful in instances where characters are represented by multiple tokens and their byte representations must be combined to generate the correct text representation. Can be null if there is no bytes representation for the token.")


class ChatCompletionObjectChoiceLogprobsRefusal(BaseModel):
    token: str = Field(..., description="The token.")
    logprob: float = Field(..., description="The log probability of this token, if it is within the top 20 most likely tokens. Otherwise, the value `-9999.0` is used to signify that the token is very unlikely.")
    bytes: Optional[List[int]] = Field(None, description="A list of integers representing the UTF-8 bytes representation of the token. Useful in instances where characters are represented by multiple tokens and their byte representations must be combined to generate the correct text representation. Can be `null` if there is no bytes representation for the token.")
    top_logprobs: List[ChatCompletionObjectChoiceLogprobsContentTopLogprobs] = Field(default_factory=list, description="List of the most likely tokens and their log probability, at this token position. In rare cases, there may be fewer than the number of requested `top_logprobs` returned.")


class ChatCompletionObjectChoiceLogprobsContent(BaseModel):
    token: str = Field(..., description="The token.")
    logprob: float = Field(..., description="The log probability of this token, if it is within the top 20 most likely tokens. Otherwise, the value `-9999.0` is used to signify that the token is very unlikely.")
    bytes: Optional[List[int]] = Field(None, description="A list of integers representing the UTF-8 bytes representation of the token. Useful in instances where characters are represented by multiple tokens and their byte representations must be combined to generate the correct text representation. Can be `null` if there is no bytes representation for the token.")
    top_logprobs: List[ChatCompletionObjectChoiceLogprobsContentTopLogprobs] = Field(default_factory=list, description="List of the most likely tokens and their log probability, at this token position. In rare cases, there may be fewer than the number of requested `top_logprobs` returned.")

class ChatCompletionObjectChoiceLogprobs(BaseModel):
    content: Optional[List[ChatCompletionObjectChoiceLogprobsContent]] = Field(None, description="A list of message content tokens with log probability information.")
    refusal: Optional[List[ChatCompletionObjectChoiceLogprobsRefusal]] = Field(None, description="A list of message refusal tokens with log probability information.")

class ChatCompletionObjectChoiceMessageAudio(BaseModel):
    id: str = Field(..., description="Unique identifier for this audio response.")
    expires_at: int = Field(..., description="The Unix timestamp (in seconds) for when this audio response will no longer be accessible on the server for use in multi-turn conversations.")
    data: str = Field(..., description="Base64 encoded audio bytes generated by the model, in the format specified in the request.")
    transcript: str = Field(..., description="Transcript of the audio generated by the model.")

class ChatCompletionObjectChoiceMessageToolCallFunction(BaseModel):
    name: str = Field(..., description="The name of the function to call.")
    arguments: str = Field(..., description="The arguments to call the function with, as generated by the model in JSON format. Note that the model does not always generate valid JSON, and may hallucinate parameters not defined by your function schema. Validate the arguments in your code before calling your function.")

class ChatCompletionObjectChoiceMessageToolCall(BaseModel):
    id: str = Field(..., description="The ID of the tool call.")
    type: str = Field('function', description="The type of the tool. Currently, only `function` is supported.")
    function: ChatCompletionObjectChoiceMessageToolCallFunction = Field(..., description="The function that the model called.")

class ChatCompletionObjectChoiceMessage(BaseModel):
    content: Optional[str] = Field(None, description="The contents of the message.")
    refusal: Optional[str] = Field(None, description="The refusal message generated by the model.")
    tool_calls: Optional[List[ChatCompletionObjectChoiceMessageToolCall]] = Field(None, description="The tool calls generated by the model, such as function calls.")
    role: str = Field(..., description="The role of the author of this message.")
    audio: Optional[ChatCompletionObjectChoiceMessageAudio] = Field(None, description="If the audio output modality is requested, this object contains data about the audio response from the model. [Learn more](https://platform.openai.com/docs/guides/audio).")

class ChatCompletionObjectChoice(BaseModel):
    finish_reason: str = Field(..., description="The reason the model stopped generating tokens. This will be `stop` if the model hit a natural stop point or a provided stop sequence, `length` if the maximum number of tokens specified in the request was reached, `content_filter` if content was omitted due to a flag from our content filters, `tool_calls` if the model called a tool, or `function_call` (deprecated) if the model called a function.")
    index: int = Field(..., description="The index of the choice in the list of choices.")
    message: ChatCompletionObjectChoiceMessage = Field(..., description="A chat completion message generated by the model.")
    logprobs: Optional[ChatCompletionObjectChoiceLogprobs] = Field(None, description="Log probability information for the choice.")

class ChatCompletionObjectUsageCompletionTokensDetails(BaseModel):
    accepted_prediction_tokens: int = Field(..., description="When using Predicted Outputs, the number of tokens in the prediction that appeared in the completion.")
    audio_tokens: int = Field(..., description="Audio input tokens generated by the model.")
    reasoning_tokens: int = Field(..., description="Tokens generated by the model for reasoning.")
    rejected_prediction_tokens: int = Field(..., description="When using Predicted Outputs, the number of tokens in the prediction that did not appear in the completion. However, like reasoning tokens, these tokens are still counted in the total completion tokens for purposes of billing, output, and context window limits.")

class ChatCompletionObjectUsagePromptTokensDetails(BaseModel):
    audio_tokens: int = Field(..., description="Audio input tokens present in the prompt.")
    cached_tokens: int = Field(..., description="Cached tokens present in the prompt.")

class ChatCompletionObjectUsage(BaseModel):
    completion_tokens: int = Field(..., description="Number of tokens in the generated completion.")
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt.")
    total_tokens: int = Field(..., description="Total number of tokens used in the request (prompt + completion).")
    completion_tokens_details: Optional[ChatCompletionObjectUsageCompletionTokensDetails] = Field(None, description="Breakdown of tokens used in a completion.")
    prompt_tokens_details: Optional[ChatCompletionObjectUsagePromptTokensDetails] = Field(None, description="Breakdown of tokens used in the prompt.")


class ChatCompletionObject(BaseModel):
    """Represents a chat completion response returned by model, based on the provided input."""
    id: str = Field(..., description="A unique identifier for the chat completion.")
    choices: List[ChatCompletionObjectChoice] = Field(..., description='A list of chat completion choices. Can be more than one if `n` is greater than 1.')
    created: int = Field(..., description="The Unix timestamp (in seconds) of when the chat completion was created.")
    model: str = Field(..., description="The model used for the chat completion.")
    object: str = Field("chat.completion", description="The object type, which is always `chat.completion`.")
    service_tier: Optional[str] = Field(None, description="The service tier used for processing the request. This field is only included if the `service_tier` parameter is specified in the request.")
    system_fingerprint: Optional[str] = Field(None, description="This fingerprint represents the backend configuration that the model runs with. Can be used in conjunction with the `seed` request parameter to understand when backend changes have been made that might impact determinism.")
    usage: Optional[ChatCompletionObjectUsage] = Field(None, description="Usage statistics for the completion request.")
    

#####################
# OpenAI Embeddings
#####################


class EmbeddingObject(BaseModel):
    index: int = Field(..., description="The index of the embedding in the list of embeddings.")
    embedding: List[float] = Field(..., description="The embedding vector, which is a list of floats. The length of vector depends on the model.")
    object: str = Field(..., description="The object type, which is always 'embedding'.")


class CreateEmbeddings(BaseModel):
    """Creates an embedding vector representing the input text."""
    input: Union[str, List[str]] = Field(..., description="Input text to embed, encoded as a string or array of tokens. To embed multiple inputs in a single request, pass an array of strings or array of token arrays. The input must not exceed the max input tokens for the model (8192 tokens for text-embedding-ada-002), cannot be an empty string, and any array must be 2048 dimensions or less. Example Python code for counting tokens. Some models may also impose a limit on total number of tokens summed across inputs.")
    model: str = Field(..., description="ID of the model to use.")
    encoding_format: Literal["float", "base64"] = Field("float", description="The format to return the embeddings in. Can be either `float` or `base64`.")
    dimensions: Optional[PositiveInt] = Field(None, description="The number of dimensions the resulting output embeddings should have. Only supported in `text-embedding-3` and later models.")
    user: Optional[str] = Field(None, description="A unique identifier representing your end-user, which can help OpenAI to monitor and detect abuse.")


class EmbeddingResponse(BaseModel):
    object: str = Field(..., description="頂層物件類型，例：'list'")
    data: List[EmbeddingObject] = Field(..., description="包含各筆 embedding 資料的列表")
    model: str = Field(..., description="模型名稱，例：'text-embedding-ada-002'")
    usage: OpenaiUsage = Field(..., description="token 使用量的資訊")