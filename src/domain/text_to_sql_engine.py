from typing import Dict, Any, List
from pandas import DataFrame
import numpy as np 

from ..config import Config
from .context import ServiceContext

class TextToSqlEngine:
    """
    Implements the Text-to-SQL logic, translating natural language into 
    structured queries.
    """
    
    def __init__(self, context: ServiceContext):
        # CORREÇÃO: Remove dependência de executor. Só precisa de dados para contexto (se necessário)
        self.df_data = context.df_data

    @staticmethod
    def _convert_to_python_types(data: Any) -> Any:
        """Recursively converts NumPy data types to native Python types."""
        if isinstance(data, dict):
            return {k: TextToSqlEngine._convert_to_python_types(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [TextToSqlEngine._convert_to_python_types(item) for item in data]
        # CORREÇÃO: np.int_ e np.float_ removidos (NumPy 2.0 fix)
        elif isinstance(data, (np.int64, np.int32)):
            return int(data)
        elif isinstance(data, (np.float64, np.float32)):
            return float(data)
        elif isinstance(data, bool):
            return bool(data)
        return data

    def translate_query(self, text_query: str) -> str:
        """Generates a SQLite SELECT query using rule-based mapping."""
        query = text_query.lower()
        sql_select = "SELECT "
        
        # 1. Determine SELECT columns
        if 'count' in query or 'how many' in query:
            sql_select += "COUNT(*)"
        elif 'protein name' in query or 'what proteins' in query:
            # Assumes correct name from config
            sql_select += "Entry_Name, Protein_names, Mass, Subcellular_location_CC" 
        else:
            sql_select += "*"
            
        sql_where = f" FROM {Config.DB_TABLE_NAME} WHERE 1=1"

        # 2. Determine WHERE conditions using Config.SQL_COL_MAP
        if 'mass' in query:
            if 'above' in query or 'greater than' in query:
                try:
                    # Improved number extraction
                    num = next((int(s) for s in query.split() if s.isdigit()), 50000)
                    sql_where += f" AND {Config.SQL_COL_MAP['mass']} > {num}"
                except StopIteration:
                    pass # Fallback or ignore if no number found

        if 'secreted' in query or 'location' in query:
            sql_where += f" AND {Config.SQL_COL_MAP['location']} LIKE '%Secreted%'"
            
        if 'coagulation' in query or 'clotting' in query:
            sql_where += f" AND {Config.SQL_COL_MAP['coagulation']} LIKE '%coagulation%'"

        if 'inhibitor' in query or 'protease' in query:
            sql_where += f" AND {Config.SQL_COL_MAP['function']} LIKE '%inhibitor activity%'"
            
        # Add complement activation logic (Based on user error logs)
        if 'complement' in query:
             sql_where += f" AND {Config.SQL_COL_MAP['process']} LIKE '%complement%'"

        return sql_select + sql_where

    def format_output(self, query_result: DataFrame) -> Dict[str, Any]:
        """Formats the executed DataFrame result into a serializable API dictionary."""
        
        is_count_query = 'COUNT(*)' in query_result.columns
        
        if is_count_query:
            # Convert the count value directly to a native Python int
            count_value = int(query_result.iloc[0, 0])
            data_output = [] 
        else:
            # Filter columns for output
            desired_cols = ['Entry', 'Entry_Name', 'Protein_names', 'Mass', 'Length', 'Subcellular_location_CC']
            available_cols = query_result.columns.tolist()
            key_cols = [c for c in desired_cols if c in available_cols]
            
            # Apply conversion to the list of dictionaries
            data_output = TextToSqlEngine._convert_to_python_types(
                query_result[key_cols].head(Config.DEFAULT_TOP_RESULTS).to_dict('records')
            )
            count_value = len(query_result)
        
        return {
            "status": "success",
            "count": count_value,
            "data": data_output,
            "message": f"Query executed successfully, found {count_value} records."
        }