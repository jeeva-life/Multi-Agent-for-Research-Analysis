import importlib.metadata

pacakges = [
    "langchain-community",
    "langchain-community",
    "langchain-core",
    "langchain-google-genai",
    "langchain-groq",
    "langchain-openai",
    "langgraph",
]

for pkg in pacakges:
    try:
        version = importlib.metadata.version(pkg)
        print(f"{pkg}=={version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{pkg} not found")