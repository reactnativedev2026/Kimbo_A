import os
import sys

sys.path.append(os.getcwd())

from app.database import engine
from sqlmodel import Session
from app.api.rewards import request_redeem
from app.schemas.app_schemas import RewardRedeemCreate, RewardRedeemResponse
from app.models import User

redeem_data = RewardRedeemCreate(scheme_id=1)
with Session(engine) as session:
    user = session.get(User, 2)
    try:
        res = request_redeem(redeem_data=redeem_data, session=session, current_user=user)
        # Try to validate via pydantic just like FastAPI does
        validated = RewardRedeemResponse.model_validate(res)
        print("Validation successful!")
    except Exception as e:
        import traceback
        traceback.print_exc()
