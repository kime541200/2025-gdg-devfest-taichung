import os
from typing import Optional
from pydantic import BaseModel, Field, model_validator

class SystemSetting(BaseModel):
    verbose: bool = Field(False, description='是否啟用囉唆模式')
    logs_dir: Optional[str] = Field(None, description='日誌目錄路徑')
    
    @model_validator(mode="after")
    def chk_values(self):
        if self.logs_dir and not os.path.exists(self.logs_dir):
            print("\033[0;33m" + f'{self.logs_dir} not exist, auto created.' + "\033[0m")
            os.makedirs(self.logs_dir)
        return self