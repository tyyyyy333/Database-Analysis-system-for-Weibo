import logging
from typing import Dict, Optional, List, Union

import pandas as pd
from sqlalchemy import create_engine
from pandasai import SmartDataframe
from pandasai.llm.openai import OpenAI


class AIAnalyzer:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_engine = create_engine(config['database_url'])

        llm = OpenAI(
            api_token=config.get('openai_api_key'),
            model=config.get('openai_model', 'gpt-3.5-turbo'),
            temperature=config.get('temperature', 0.7)
        )
        self.pandas_ai = SmartDataframe([], config={"llm": llm})

    def get_all_table_names(self) -> List[str]:
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        with self.db_engine.connect() as conn:
            return [row[0] for row in conn.execute(query).fetchall()]

    def analyze_by_question(self, question: str, table_name: Optional[str] = None) -> Dict[str, Union[str, Dict]]:
        try:
            if table_name:
                df = pd.read_sql(f"SELECT * FROM {table_name}", self.db_engine)
            else:
                df = {
                    name: pd.read_sql(f"SELECT * FROM {name}", self.db_engine)
                    for name in self.get_all_table_names()
                }
            result = self.pandas_ai.run(df, question)
            return {"status": "success", "data": result}
        except Exception as e:
            self.logger.error(f"自然语言分析失败: {str(e)}")
            return {"status": "error", "message": str(e)}
