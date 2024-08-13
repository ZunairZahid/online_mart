from fastapi import FastAPI, Depends, HTTPException, APIRouter
from typing import Annotated
from jose import JWTError
from datetime import timedelta

from sqlmodel import Session, select, update
from app.model import Tser
from app.token import create_access_token, decode_access_token

from fastapi.security import OAuth2PasswordRequestForm

from app.utils import get_session, hash_password, verify_password



router = APIRouter(prefix="/accesscontrol",
                 tags=["accesscontrol   "]

)



@router.post("/gettoken")

def token(form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)], 
          session: Annotated[Session, Depends(get_session)]):
   
    """
    Understanding the login system
    -> Takes form_data that have username and password
    """
    statement  =  select(Tser).where(Tser.username == form_data.username)
    user = session.exec(statement).one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username")
    
    print(f"Plain password: {form_data.password}")
    print(f"Hashed password from DB: {user.password_hash}")
    print(f"Hashed password from DB: {form_data.password}")
    print(f" formula {verify_password(form_data.password, user.password_hash)}")

    if not verify_password(form_data.password , user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")

    access_token_expires = timedelta(minutes=1)

    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer", "expires_in": access_token_expires.total_seconds() }


@router.get("/decode_token")
def decoding_token(access_token: str):
    """
    Understanding the access token decoding and validation
    """
    try:
        decoded_token_data = decode_access_token(access_token)
        return {"decoded_token": decoded_token_data}
    except JWTError as e:
        return {"error": str(e)}


@router.get("/login")
def read_users_me(token: str, session: Annotated[Session, Depends(get_session)]):
    """
    Get the current user's information using the authorization token
    """
    try:
        user_token_data = decode_access_token(token)
        username = user_token_data.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")

        statement = select(Tser).where(Tser.username == username)
        user = session.exec(statement).one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
@router.post("/update-password")
def update_password(old_password: str, new_password: str, token: str, 
                    session: Annotated[Session, Depends(get_session)]):
    """
    Update the user's password using the authorization token.
    """
    try:
        # Decode the token to get the username
        user_token_data = decode_access_token(token)
        username = user_token_data.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Fetch the user from the database
        statement = select(Tser).where(Tser.username == username)
        user = session.exec(statement).one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify old password
        if not verify_password(old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect old password")

        # Hash the new password and update in the database
        new_password_hash = hash_password(new_password)
        statement = update(Tser).where(Tser.username == username).values(password_hash=new_password_hash)
        session.exec(statement)
        session.commit()

        return {"detail": "Password updated successfully"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")