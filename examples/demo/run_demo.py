from support_agent.infrastructure.vectorstores.inmemory import InMemoryVectorStore
from support_agent.infrastructure.llm.mock_client import MockLLMClient
from support_agent.application.response_generator import ResponseGenerator
from support_agent.domain.personas import PersonaDetectionResult, PersonaType
from support_agent.domain.documents import HybridRetrievalResult


def main():
    store = InMemoryVectorStore(persist_path="data/vector_store/demo_store.json")
    # Simple query that should hit the password reset doc
    query = "How do I reset my password?"

    results = store.similarity_search(query, top_k=4)
    retrieval_result = HybridRetrievalResult(results=results)

    persona = PersonaDetectionResult(persona=PersonaType.FRUSTRATED_USER, confidence=0.9, matched_indicators=[], reasoning="demo")
    llm = MockLLMClient("Follow the password reset steps from the documentation.")
    generator = ResponseGenerator(llm_client=llm)

    response = generator.generate(question=query, persona_result=persona, retrieval_result=retrieval_result)

    print("--- Question ---")
    print(query)
    print("--- Answer ---")
    print(response.answer)
    print("--- Citations ---")
    print(response.citations)


if __name__ == "__main__":
    main()
