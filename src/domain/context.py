from typing import Any
from pandas import DataFrame
from numpy import ndarray
from sentence_transformers import SentenceTransformer
from sqlite3 import Connection

from ..infrastructure.infra_manager import InfraManager


class ServiceContext:
    """
    Central dependency container (Service Locator pattern for DI).
    Holds initialized instances and shared assets required by the Domain Engines.
    """
    def __init__(self, infra_manager: InfraManager):
        # Data and DB Assets
        self.db_conn: Connection = infra_manager.db_conn
        self.query_executor: Any = infra_manager.execute_query
        self.df_data: DataFrame = infra_manager.df_data
        
        # NLP/AI Assets
        self.nlp_model: SentenceTransformer = infra_manager.nlp_model
        self.embeddings: ndarray = infra_manager.embeddings
        self.generator: Any = infra_manager.generator