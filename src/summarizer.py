
import os
from dotenv import load_dotenv, find_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq  # or wherever your ChatGroq lives
from src.utils import SummarizationError
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field, ValidationError


_dotenv = find_dotenv()
if _dotenv:
    load_dotenv(_dotenv, override=True)

model_name  = os.getenv("MODEL_NAME")
api_key      = os.getenv("GROQ_API_KEY")

if not model_name or not api_key:
    raise RuntimeError("MODEL_NAME and GROQ_API_KEY must be set in your .env")


class PaperMeta(BaseModel):
    doi_issn: str = Field("", description="The DOI or ISSN of the paper, or empty string if none")
    title:    str = Field(..., description="The full title of the paper")
    authors:  str = Field(..., description="Comma-separated list of authors")
    summary:  str = Field(..., description="A 3–5 sentence summary of the paper")

output_parser = JsonOutputParser(pydantic_object=PaperMeta)


EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert research assistant. "
     "Extract the following from the paper text and return valid JSON:\n"
     "- doi_issn: the paper's DOI or ISSN, or an empty string if not found\n"
     "- title: the full paper title\n"
     "- authors: comma-separated list of author names\n"
     "- summary: a concise 3–5 sentence summary of objective, methods, key results, and significance"
    ),
    ("user", "{paper_text}")
])


class LLMModel:
    """Wraps the Groq chat API via LangChain-style interface."""
    def __init__(self, model_name: str = model_name):
        self.llm = ChatGroq(model=model_name,
                                temperature=0,
                                max_tokens=None,
                                timeout=None,
                                api_key = api_key)
    def invoke(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        messages = prompt.format_messages(**kwargs)
        result   = self.llm.invoke(messages)
        print(result)
        return result  

class Summarizer:
    def __init__(self, model_name: str = model_name):
        self.llm_model = LLMModel(model_name=model_name)

    def summarize(self, paper_text: str) -> str:
        """
        Summarize the given research paper text.
        """
        paper_text_ = paper_text[:5000]  # Truncate to 5000 characters
        prompt = ChatPromptTemplate.from_messages([
            ("system",
            "You are an expert research assistant. "
            "When I give you the full text of a research paper, you must output _only_ a concise 3–5 sentence paragraph summarizing the paper’s objective, methods, key results, and significance. "
            "Do not include any leading phrases like “Here is a summary,” or repeat the prompt itself."
            ),
            ("user",
            "{paper_text_}\n\nSummarize the paper in 3–5 sentences:"
            )
        ])

        try:
            summary = self.llm_model.invoke(prompt, paper_text_=paper_text_)
            
            if hasattr(summary, "content"):
                return summary.content.strip()
           
            if hasattr(summary, "generations"):
                return summary.generations[0][0].message.content.strip()
            
            return str(summary).strip()
        except Exception as e:
            raise SummarizationError(f"Groq/LangChain summarization failed: {e}") from e

    def extract_metadata(self, paper_text: str) -> PaperMeta:
        try:
            paper_text  = paper_text[:5000]  # Truncate to 5000 characters
            ai_msg = self.llm_model.invoke(EXTRACTION_PROMPT, paper_text=paper_text)
            content = ai_msg.content
            
            content = content.replace("```json", "").replace("```", "")
            start = content.find("{")
            end   = content.rfind("}") + 1
            if start < 0 or end < 0:
                raise SummarizationError("Could not locate JSON payload in model response.")
            json_str = content[start:end]

            
            parsed_dict = output_parser.parse(json_str)

            try:
                meta = PaperMeta(**parsed_dict)
            except ValidationError as ve:
                raise SummarizationError(f"JSON validation failed: {ve}") from ve

            return meta

        except SummarizationError:
            raise
        except Exception as e:
            raise SummarizationError(f"Failed to extract metadata: {e}") from e