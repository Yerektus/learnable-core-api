from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.modules.ai.llm import get_llm
from app.modules.ai.schemas import GeneratedMaterials

CARDS_PROMPT = """Create flashcards for the following content. Each card has a front (question/term) and back (answer/definition).
Create 8-15 cards covering the key concepts.

{format_instructions}

Content: {text}"""

NOTES_PROMPT = """Create a concise study summary/notes for the following content.
Structure it with clear sections. Use markdown formatting.

Content: {text}
Custom instructions: {custom_prompt}"""

def generate_cards(text: str) -> list[dict]:
    from app.modules.ai.schemas import GeneratedMaterials
    parser = PydanticOutputParser(pydantic_object=GeneratedMaterials)
    prompt = ChatPromptTemplate.from_template(CARDS_PROMPT)
    llm = get_llm()
    chain = prompt | llm | parser
    result = chain.invoke({"text": text, "format_instructions": parser.get_format_instructions()})
    return [{"front": c.front, "back": c.back} for c in result.cards]

def generate_notes(text: str, custom_prompt: str = "") -> str:
    prompt = ChatPromptTemplate.from_template(NOTES_PROMPT)
    llm = get_llm()
    chain = prompt | llm
    result = chain.invoke({"text": text, "custom_prompt": custom_prompt or "None"})
    return result.content
