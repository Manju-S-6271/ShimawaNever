from database import engine
import models

# これが実行されて初めてテーブルが作られる
models.Base.metadata.create_all(bind=engine)