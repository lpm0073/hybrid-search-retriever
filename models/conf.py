# -*- coding: utf-8 -*-
# pylint: disable=no-member
# pylint: disable=E0213,C0103
"""
Configuration for Lambda functions.

This module is used to configure the Lambda functions. It uses the pydantic_settings
library to validate the configuration values. The configuration values are read from
any of the following sources:
    - constructor arguments
    - environment variables
    - terraform.tfvars
    - default values
"""

import importlib.util
import os  # library for interacting with the operating system
import platform  # library to view information about the server host this Lambda runs on
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import Field, ValidationError, validator
from pydantic_settings import BaseSettings

from models.const import HERE
from models.exceptions import ModelConfigurationError, ModelValueError


DOT_ENV_LOADED = load_dotenv()


def load_version() -> Dict[str, str]:
    """Stringify the __version__ module."""
    version_file_path = os.path.join(HERE, "__version__.py")
    spec = importlib.util.spec_from_file_location("__version__", version_file_path)
    version_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(version_module)
    return version_module.__dict__


VERSION = load_version()


def get_semantic_version() -> str:
    """
    Return the semantic version number.

    Example valid values of __version__.py are:
    0.1.17
    0.1.17-next.1
    0.1.17-next.2
    0.1.17-next.123456
    0.1.17-next-major.1
    0.1.17-next-major.2
    0.1.17-next-major.123456

    Note:
    - pypi does not allow semantic version numbers to contain a dash.
    - pypi does not allow semantic version numbers to contain a 'v' prefix.
    - pypi does not allow semantic version numbers to contain a 'next' suffix.
    """
    version = VERSION["__version__"]
    version = re.sub(r"-next\.\d+", "", version)
    return re.sub(r"-next-major\.\d+", "", version)


# pylint: disable=too-few-public-methods
class SettingsDefaults:
    """Default values for Settings"""

    DEBUG_MODE = False
    DUMP_DEFAULTS = False

    LANGCHAIN_MEMORY_KEY = "chat_history"

    PINECONE_API_KEY = None
    PINECONE_ENVIRONMENT = "gcp-starter"
    PINECONE_INDEX_NAME = "rag"
    PINECONE_VECTORSTORE_TEXT_KEY = "lc_id"
    PINECONE_METRIC = "dotproduct"
    PINECONE_DIMENSIONS = 1536

    OPENAI_API_ORGANIZATION = None
    OPENAI_API_KEY = None
    OPENAI_ENDPOINT_IMAGE_N = 4
    OPENAI_ENDPOINT_IMAGE_SIZE = "1024x768"
    OPENAI_CHAT_CACHE = True
    OPENAI_CHAT_MODEL_NAME = "gpt-3.5-turbo"
    OPENAI_PROMPT_MODEL_NAME = "text-davinci-003"
    OPENAI_CHAT_TEMPERATURE = 0.0
    OPENAI_CHAT_MAX_RETRIES = 3

    @classmethod
    def to_dict(cls):
        """Convert SettingsDefaults to dict"""
        return {
            key: value
            for key, value in SettingsDefaults.__dict__.items()
            if not key.startswith("__") and not callable(key) and key != "to_dict"
        }


def empty_str_to_bool_default(v: str, default: bool) -> bool:
    """Convert empty string to default boolean value"""
    if v in [None, ""]:
        return default
    return v.lower() in ["true", "1", "t", "y", "yes"]


def empty_str_to_int_default(v: str, default: int) -> int:
    """Convert empty string to default integer value"""
    if v in [None, ""]:
        return default
    try:
        return int(v)
    except ValueError:
        return default


# pylint: disable=too-many-public-methods
# pylint: disable=too-many-instance-attributes
class Settings(BaseSettings):
    """Settings for Lambda functions"""

    _cloudwatch_dump: dict = None
    _pinecone_api_key_source: str = "unset"
    _openai_api_key_source: str = "unset"

    def __init__(self, **data: Any):
        super().__init__(**data)
        if "PINECONE_API_KEY" in os.environ:
            self._pinecone_api_key_source = "environment variable"
        elif data.get("pinecone_api_key"):
            self._pinecone_api_key_source = "init argument"
        if "OPENAI_API_KEY" in os.environ:
            self._openai_api_key_source = "environment variable"
        elif data.get("openai_api_key"):
            self._openai_api_key_source = "init argument"

    debug_mode: Optional[bool] = Field(
        SettingsDefaults.DEBUG_MODE,
        env="DEBUG_MODE",
        pre=True,
        getter=lambda v: empty_str_to_bool_default(v, SettingsDefaults.DEBUG_MODE),
    )
    dump_defaults: Optional[bool] = Field(
        SettingsDefaults.DUMP_DEFAULTS,
        env="DUMP_DEFAULTS",
        pre=True,
        getter=lambda v: empty_str_to_bool_default(v, SettingsDefaults.DUMP_DEFAULTS),
    )

    langchain_memory_key: Optional[str] = Field(SettingsDefaults.LANGCHAIN_MEMORY_KEY, env="LANGCHAIN_MEMORY_KEY")

    openai_api_organization: Optional[str] = Field(
        SettingsDefaults.OPENAI_API_ORGANIZATION, env="OPENAI_API_ORGANIZATION"
    )
    openai_api_key: Optional[str] = Field(SettingsDefaults.OPENAI_API_KEY, env="OPENAI_API_KEY")
    openai_endpoint_image_n: Optional[int] = Field(
        SettingsDefaults.OPENAI_ENDPOINT_IMAGE_N, env="OPENAI_ENDPOINT_IMAGE_N"
    )
    openai_endpoint_image_size: Optional[str] = Field(
        SettingsDefaults.OPENAI_ENDPOINT_IMAGE_SIZE, env="OPENAI_ENDPOINT_IMAGE_SIZE"
    )
    openai_chat_cache: Optional[bool] = Field(
        SettingsDefaults.OPENAI_CHAT_CACHE,
        env="OPENAI_CHAT_CACHE",
        pre=True,
        getter=lambda v: empty_str_to_bool_default(v, SettingsDefaults.OPENAI_CHAT_CACHE),
    )
    openai_chat_model_name: Optional[str] = Field(SettingsDefaults.OPENAI_CHAT_MODEL_NAME, env="OPENAI_CHAT_MODEL_NAME")
    openai_prompt_model_name: Optional[str] = Field(
        SettingsDefaults.OPENAI_PROMPT_MODEL_NAME, env="OPENAI_PROMPT_MODEL_NAME"
    )
    openai_chat_temperature: Optional[float] = Field(
        SettingsDefaults.OPENAI_CHAT_TEMPERATURE, env="OPENAI_CHAT_TEMPERATURE"
    )
    openai_chat_max_retries: Optional[int] = Field(
        SettingsDefaults.OPENAI_CHAT_MAX_RETRIES, env="OPENAI_CHAT_MAX_RETRIES"
    )

    pinecone_api_key: Optional[str] = Field(SettingsDefaults.PINECONE_API_KEY, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(SettingsDefaults.PINECONE_ENVIRONMENT, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: Optional[str] = Field(SettingsDefaults.PINECONE_INDEX_NAME, env="PINECONE_INDEX_NAME")
    pinecone_vectorstore_text_key: Optional[str] = Field(
        SettingsDefaults.PINECONE_VECTORSTORE_TEXT_KEY, env="PINECONE_VECTORSTORE_TEXT_KEY"
    )
    pinecone_metric: Optional[str] = Field(SettingsDefaults.PINECONE_METRIC, env="PINECONE_METRIC")
    pinecone_dimensions: Optional[int] = Field(SettingsDefaults.PINECONE_DIMENSIONS, env="PINECONE_DIMENSIONS")

    @property
    def pinecone_api_key_source(self) -> str:
        """Pinecone API key source"""
        return self._pinecone_api_key_source

    @property
    def openai_api_key_source(self) -> str:
        """OpenAI API key source"""
        return self._openai_api_key_source

    @property
    def is_using_dotenv_file(self) -> bool:
        """Is the dotenv file being used?"""
        return DOT_ENV_LOADED

    @property
    def environment_variables(self) -> List[str]:
        """Environment variables"""
        return list(os.environ.keys())

    @property
    def is_using_tfvars_file(self) -> bool:
        """Is the tfvars file being used?"""
        return False

    @property
    def tfvars_variables(self) -> List[str]:
        """Terraform variables"""
        return []

    @property
    def is_using_aws_rekognition(self) -> bool:
        """Future: Is the AWS Rekognition service being used?"""
        return False

    @property
    def is_using_aws_dynamodb(self) -> bool:
        """Future: Is the AWS DynamoDB service being used?"""
        return False

    @property
    def version(self) -> str:
        """OpenAI API version"""
        return get_semantic_version()

    # use the boto3 library to initialize clients for the AWS services which we'll interact
    @property
    def cloudwatch_dump(self):
        """Dump settings to CloudWatch"""

        def recursive_sort_dict(d):
            return {k: recursive_sort_dict(v) if isinstance(v, dict) else v for k, v in sorted(d.items())}

        if self._cloudwatch_dump:
            return self._cloudwatch_dump

        self._cloudwatch_dump = {
            "secrets": {
                "openai_api_source": self.openai_api_key_source,
                "pinecone_api_source": self.pinecone_api_key_source,
            },
            "environment": {
                "is_using_tfvars_file": self.is_using_tfvars_file,
                "is_using_dotenv_file": self.is_using_dotenv_file,
                "os": os.name,
                "system": platform.system(),
                "release": platform.release(),
                "debug_mode": self.debug_mode,
                "dump_defaults": self.dump_defaults,
                "version": self.version,
            },
            "langchaint": {
                "langchain_memory_key": self.langchain_memory_key,
            },
            "openai_api": {
                "openai_endpoint_image_n": self.openai_endpoint_image_n,
                "openai_endpoint_image_size": self.openai_endpoint_image_size,
                "openai_chat_cache": self.openai_chat_cache,
                "openai_chat_model_name": self.openai_chat_model_name,
                "openai_prompt_model_name": self.openai_prompt_model_name,
                "openai_chat_temperature": self.openai_chat_temperature,
                "openai_chat_max_retries": self.openai_chat_max_retries,
            },
            "pinecone_api": {
                "pinecone_environment": self.pinecone_environment,
                "pinecone_index_name": self.pinecone_index_name,
                "pinecone_vectorstore_text_key": self.pinecone_vectorstore_text_key,
                "pinecone_metric": self.pinecone_metric,
                "pinecone_dimensions": self.pinecone_dimensions,
            },
        }
        if self.dump_defaults:
            settings_defaults = SettingsDefaults.to_dict()
            self._cloudwatch_dump["settings_defaults"] = settings_defaults

        if self.is_using_dotenv_file:
            self._cloudwatch_dump["environment"]["dotenv"] = self.environment_variables

        if self.is_using_tfvars_file:
            self._cloudwatch_dump["environment"]["tfvars"] = self.tfvars_variables

        self._cloudwatch_dump = recursive_sort_dict(self._cloudwatch_dump)
        return self._cloudwatch_dump

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration"""

        frozen = True

    @validator("debug_mode", pre=True)
    def parse_debug_mode(cls, v):
        """Parse debug_mode"""
        if isinstance(v, bool):
            return v
        if v in [None, ""]:
            return SettingsDefaults.DEBUG_MODE
        return v.lower() in ["true", "1", "t", "y", "yes"]

    @validator("dump_defaults", pre=True)
    def parse_dump_defaults(cls, v):
        """Parse dump_defaults"""
        if isinstance(v, bool):
            return v
        if v in [None, ""]:
            return SettingsDefaults.DUMP_DEFAULTS
        return v.lower() in ["true", "1", "t", "y", "yes"]

    @validator("langchain_memory_key", pre=True)
    def check_langchain_memory_key(cls, v):
        """Check langchain_memory_key"""
        if isinstance(v, int):
            return v
        if v in [None, ""]:
            return SettingsDefaults.LANGCHAIN_MEMORY_KEY
        return v

    @validator("openai_api_organization", pre=True)
    def check_openai_api_organization(cls, v):
        """Check openai_api_organization"""
        if v in [None, ""]:
            return SettingsDefaults.OPENAI_API_ORGANIZATION
        return v

    @validator("openai_api_key", pre=True)
    def check_openai_api_key(cls, v):
        """Check openai_api_key"""
        if v in [None, ""]:
            return SettingsDefaults.OPENAI_API_KEY
        return v

    @validator("openai_endpoint_image_n", pre=True)
    def check_openai_endpoint_image_n(cls, v):
        """Check openai_endpoint_image_n"""
        if isinstance(v, int):
            return v
        if v in [None, ""]:
            return SettingsDefaults.OPENAI_ENDPOINT_IMAGE_N
        return int(v)

    @validator("openai_endpoint_image_size", pre=True)
    def check_openai_endpoint_image_size(cls, v):
        """Check openai_endpoint_image_size"""
        if v in [None, ""]:
            return SettingsDefaults.OPENAI_ENDPOINT_IMAGE_SIZE
        return v

    @validator("openai_chat_cache", pre=True)
    def check_openai_chat_cache(cls, v):
        """Check openai_chat_cache"""
        if isinstance(v, bool):
            return v
        if v in [None, ""]:
            return SettingsDefaults.OPENAI_CHAT_CACHE
        return v.lower() in ["true", "1", "t", "y", "yes"]

    @validator("openai_chat_model_name", pre=True)
    def check_openai_chat_model_name(cls, v):
        """Check openai_chat_model_name"""
        if v in [None, ""]:
            return SettingsDefaults.OPENAI_CHAT_MODEL_NAME
        return v

    @validator("openai_prompt_model_name", pre=True)
    def check_openai_prompt_model_name(cls, v):
        """Check openai_prompt_model_name"""
        if v in [None, ""]:
            return SettingsDefaults.OPENAI_PROMPT_MODEL_NAME
        return v

    @validator("openai_chat_temperature", pre=True)
    def check_openai_chat_temperature(cls, v):
        """Check openai_chat_temperature"""
        if v in [None, ""]:
            return SettingsDefaults.OPENAI_CHAT_TEMPERATURE
        return float(v)

    @validator("openai_chat_max_retries", pre=True)
    def check_openai_chat_max_retries(cls, v):
        """Check openai_chat_max_retries"""
        if v in [None, ""]:
            return SettingsDefaults.OPENAI_CHAT_MAX_RETRIES
        return int(v)

    @validator("pinecone_api_key", pre=True)
    def check_pinecone_api_key(cls, v):
        """Check pinecone_api_key"""
        if v in [None, ""]:
            return SettingsDefaults.PINECONE_API_KEY
        return v

    @validator("pinecone_environment", pre=True)
    def check_pinecone_environment(cls, v):
        """Check pinecone_environment"""
        if v in [None, ""]:
            return SettingsDefaults.PINECONE_ENVIRONMENT
        return v

    @validator("pinecone_index_name", pre=True)
    def check_pinecone_index_name(cls, v):
        """Check pinecone_index_name"""
        if v in [None, ""]:
            return SettingsDefaults.PINECONE_INDEX_NAME
        return v

    @validator("pinecone_vectorstore_text_key", pre=True)
    def check_pinecone_vectorstore_text_key(cls, v):
        """Check pinecone_vectorstore_text_key"""
        if v in [None, ""]:
            return SettingsDefaults.PINECONE_VECTORSTORE_TEXT_KEY
        return v

    @validator("pinecone_metric", pre=True)
    def check_pinecone_metric(cls, v):
        """Check pinecone_metric"""
        if v in [None, ""]:
            return SettingsDefaults.PINECONE_METRIC
        return v

    @validator("pinecone_dimensions", pre=True)
    def check_pinecone_dimensions(cls, v):
        """Check pinecone_dimensions"""
        if v in [None, ""]:
            return SettingsDefaults.PINECONE_DIMENSIONS
        return int(v)


settings = None
try:
    settings = Settings()
except (ValidationError, ValueError, ModelConfigurationError, ModelValueError) as e:
    raise ModelConfigurationError("Invalid configuration: " + str(e)) from e