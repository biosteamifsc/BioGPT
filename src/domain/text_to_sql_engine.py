from typing import Dict, Any
from pandas import DataFrame

from ..config import Config
from .context import ServiceContext


class TextToSqlEngine:
    """
    Implements the Text-to-SQL logic, translating natural language into 
    structured queries for the database.
    """
    
    def __init__(self, context: ServiceContext):
        # Dependencies injected from the context
        self.query_executor = context.query_executor
        self.df_data = context.df_data 

    def translate_query(self, text_query: str) -> str:
        """Generates a SQLite SELECT query using rule-based mapping."""
        query = text_query.lower()
        sql_select = "SELECT "
        
        # 1. Determine SELECT columns
        if 'count' in query or 'how many' in query:
            sql_select += "COUNT(*)"
        elif 'protein name' in query or 'what proteins' in query:
            sql_select += "Entry_Name, Protein_names, Mass, Subcellular_location__CC_"
        else:
            sql_select += "*"
            
        sql_where = f" FROM {Config.DB_TABLE_NAME} WHERE 1=1"

        # 2. Determine WHERE conditions using Config.SQL_COL_MAP
        if 'mass' in query:
            if 'above' in query or 'greater than' in query:
                num = next((int(s) for s in query.split() if s.isdigit()), 50000)
                sql_where += f" AND {Config.SQL_COL_MAP['mass']} > {num}"

        if 'secreted' in query or 'location' in query:
            sql_where += f" AND {Config.SQL_COL_MAP['location']} LIKE '%Secreted%'"
            
        if 'coagulation' in query or 'clotting' in query:
            sql_where += f" AND {Config.SQL_COL_MAP['coagulation']} LIKE '%coagulation%'"

        if 'inhibitor' in query or 'protease' in query:
            sql_where += f" AND {Config.SQL_COL_MAP['function']} LIKE '%inhibitor activity%'"
            
        return sql_select + sql_where

    def execute_and_format(self, sql_query: str) -> Dict[str, Any]:
        """Executes the SQL query and formats the structured output."""
        query_result = self.query_executor(sql_query)
        
        if isinstance(query_result, DataFrame):
            is_count_query = 'COUNT(*)' in query_result.columns
            
            if is_count_query:
                data_output = query_result.to_dict('records')
                count_value = query_result.iloc[0, 0]
            else:
                key_cols = [c for c in ['Entry', 'Entry_Name', 'Protein_names', 'Mass', 'Length', 'Subcellular_location__CC_'] if c in query_result.columns]
                data_output = query_result[key_cols].head(Config.DEFAULT_TOP_RESULTS).to_dict('records')
                count_value = len(query_result)
            
            return {
                "status": "success",
                "count": count_value,
                "data": data_output,
                "message": f"Query executed successfully, found {count_value} records."
            }
        else:
            return {"status": "error", "message": query_result}