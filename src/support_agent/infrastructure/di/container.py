from dependency_injector import containers, providers

from support_agent.config.settings import get_settings, Settings
from support_agent.infrastructure.factories import RetrievalSystemFactory
from support_agent.logging.config import get_logger


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["support_agent"])  # allow wiring

    config: Settings = providers.Singleton(get_settings)

    logger = providers.Factory(get_logger, name="support_agent")

    retrieval_factory = providers.Factory(RetrievalSystemFactory, settings=config)

    # Example providers for commonly used singletons
    vector_store = providers.Singleton(lambda factory: factory.create_vector_store(), retrieval_factory)
    hybrid_retriever = providers.Singleton(lambda factory: factory.create_hybrid_retriever(), retrieval_factory)
    document_loader = providers.Singleton(lambda factory: factory.create_document_loader(), retrieval_factory)
    chunker = providers.Singleton(lambda factory: factory.create_chunker(), retrieval_factory)
    escalation_engine = providers.Singleton(lambda factory: factory.create_escalation_engine(), retrieval_factory)
    memory_manager = providers.Singleton(lambda factory: factory.create_memory_manager(), retrieval_factory)
