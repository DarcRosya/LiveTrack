from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.security.password_hashing import verify_password, hash_password
from src.security.validators import is_password_strong_enough
from src.schemas.user_dto import PasswordChange
from src.models.user import User

async def change_user_password(
    db: AsyncSession, 
    user_to_update: User, 
    password_data: PasswordChange
) -> None:
    # 1. We verify that the current password entered by the user is correct.
    if not verify_password(password_data.current_password, user_to_update.password_in_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    
    # 2. (Optional) Check that the new password does not match the old one.
    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the old one",
        )
        

    # 3. Checking the strength of your new password
    if not is_password_strong_enough(password_data.new_password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Password is not strong enough. It must be at least 8 characters long, "
                "contain at least one digit, one uppercase and one lowercase letter, "
                "and no spaces."
            )
        )
    
    # 4. We hash the new password and save it.
    user_to_update.password_in_hash = hash_password(password_data.new_password)
    db.add(user_to_update)
    await db.commit()