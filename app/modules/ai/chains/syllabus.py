from langchain_core.prompts import ChatPromptTemplate
from app.modules.ai.llm import get_llm
from app.modules.ai.schemas import GeneratedGraph

SYLLABUS_PROMPT = """You are an expert curriculum designer. Analyze the following syllabus/course material and extract a structured learning graph.

Create nodes for each major topic/lecture. Connect them with PRECEDES edges showing the natural learning order. Identify deadlines (exams, quizzes, homework submissions).

Dates must be in YYYY-MM-DD format.

For each deadline set the type field:
- type="exam" for midterms, finals, and any other exams
- type="quiz" for quizzes, tests, and short assessments
- type="assignment" for homework, projects, lab submissions, and all other deadlines

Syllabus content:
{text}

Custom instructions (if any): {custom_prompt}"""


def generate_graph_from_text(text: str, custom_prompt: str = "") -> GeneratedGraph:
    prompt = ChatPromptTemplate.from_template(SYLLABUS_PROMPT)
    llm = get_llm().with_structured_output(GeneratedGraph)
    chain = prompt | llm
    return chain.invoke({
        "text": text,
        "custom_prompt": custom_prompt or "No custom instructions.",
    })
