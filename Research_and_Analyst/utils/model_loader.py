import os
import sys
import json
import asyncio
from dotenv import load_dotenv
from utils.config_loader import load_config
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from logger import GLOBAL_LOGGER as log
from exceptions.custom_exception import ResearchAnalystException


class ApiKeyManager:
    """
    Loads and manages all environment-based API keys.
    """

    def __init__(self):
        load_dotenv()

        self.api_keys = {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
            "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        }

        log.info("Initializing API Key Manager")

        #Log loaded key statuses without exposing secrets
        for key, val in self.api_keys.items():
            if val:
                log.info(f"Loaded API Key for {key}")
            else:
                log.warning(f"No API Key found for {key}")

    
    def get(self, key: str):
        """
        Retrieves an API key by name.

        Args:
            key (str): The name of the API key to retrieve.
        
        Returns:
            str | None: The API key value.
        """

        return self.api_keys.get(key.upper(), None)


class ModelLoader:
    """
    Loads Embedding models & LLMs dynamically based on YAML configuration & environment settings.
    """

    def __init__(self):
        """
        Initialize the ModelLoader and load configuration
        """

        try:
            self.api_key_manager = ApiKeyManager()
            self.config = load_config()
            log.info("YAML configuration loaded successfully", config_keys=list(self.config.keys()))
        except Exception as e:
            log.error("Error initializing ModelLoader", error=str(e))
            raise ResearchAnalystException(f"Failed to initialize ModelLoader", sys)

        
    # ------------------------------------------------------------ #
    # ----------Embedding Loader -------------------------------- #
    # ------------------------------------------------------------ #
    def load_embeddings(self):
        """
        Load and return a Google Generative AI Embedding model.

        Returns:
            GoogleGenerativeAIEmbeddings: The loaded embedding model.
        """
        try:
            model_name = self.config["embedding_model"]["model_name"]
            log.info(f"Loading embedding model: {model_name}")

            # Ensure event loop exists for grpc-based embedding API
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())

            embeddings = GoogleGenerativeAIEmbeddings(
                model=model_name,
                api_key=self.api_key_manager.get("GOOGLE_API_KEY"),
            )

            log.info(f"Embedding model {model_name} loaded successfully")
            return embeddings

        except Exception as e:
            log.error(f"Error loading embedding model {model_name}", error=str(e))
            raise ResearchAnalystException(f"Failed to load embedding model {model_name}", sys)

    
    # ------------------------------------------------------------ #
    # ----------LLM Loader ------------------------------------- #
    # ------------------------------------------------------------ #
    def load_llm(self):
        """
        Load and return a chat-based LLM according to the configured provider.

        Supported Providers:
        - OpenAI
        - Google
        - Groq

        Returns:
            ChatOpenAI | ChatGoogleGenerativeAI | ChatGroq: The loaded LLM model.
        """

        try:
            llm_block = self.config["llm"]
            provider_key = os.getenv("LLM_PROVIDER", "openai").upper()

            if provider_key not in llm_block:
                log.error("LLM provider not found in configuration", provider = provider_key)
                raise ResearchAnalystException(f"LLM provider {provider_key} not found in configuration", sys)

            llm_config = llm_block[provider_key]
            provider = llm_config.get("provider")
            model_name = llm_config.get("model_name")
            temperature = llm_config.get("temperature", 0.7)
            max_tokens = llm_config.get("max_tokens", 1000)

            log.info(f"Loading LLM: {provider} {model_name} with temperature {temperature} and max_tokens {max_tokens}")

            if provider == "openai":
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    api_key=self.api_key_manager.get("OPENAI_API_KEY"),
                )
            
            elif provider == "google":
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=temperature,
                    api_key=self.api_key_manager.get("GOOGLE_API_KEY"),
                    max_output_tokens=max_tokens,
                )

            elif provider == "groq":
                llm = ChatGroq(
                    model=model_name,
                    temperature=temperature,
                    api_key=self.api_key_manager.get("GROQ_API_KEY"),
                )

            else:
                log.error("Unsupported LLM provider", provider = provider)
                raise ValueError(f"Unsupported LLM provider {provider}")

            log.info(f"LLM {model_name} loaded successfully")
            return llm

        except Exception as e:
            log.error(f"Error loading LLM {model_name}", error=str(e))
            raise ResearchAnalystException(f"Failed to load LLM {model_name}", sys)

        

# ------------------------------------------------------------ #
# STANDALONE TESTING
# ------------------------------------------------------------ #

if __name__ == "__main__":
    try:
        model_loader = ModelLoader()

        # test embedding model loading
        embeddings = model_loader.load_embeddings()
        print(f"Embedding model loaded successfully: {embeddings}")
        result = embeddings.embed_query("Hello, how are you?")
        print(f"Embedding result: {result[:5]}...")

        # test LLM loading
        llm = model_loader.load_llm()
        print(f"LLM loaded successfully: {llm}")
        response = llm.invoke("Hello, how are you?")
        print(f"LLM response: {response.content}")

        log.info("All tests completed successfully")

    except Exception as e:
        log.error("Critical failure in ModelLoader test", error=str(e))