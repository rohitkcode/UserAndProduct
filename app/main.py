from typing import Union
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, model_validator
import sqlite3
import uuid
import hashlib
from datetime import datetime
from pymongo import MongoClient

app = FastAPI()

conn = sqlite3.connect("./sqlite.db",check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id, username, password) ")

client = MongoClient("mongodb+srv://rohitkcode:learnMongo@userproduct.yjmgly4.mongodb.net/")
mongo_db = client.product_database

sessions = {}

def create_session(user_id: int):
    session_id = uuid.uuid4().hex
    sessions[session_id] = user_id
    return session_id

class RegistrationDetails(BaseModel):
    username: str = Field(min_length=5,max_length=30)
    password :str = Field(min_length=8,max_length=25)
    confirm_password: str = Field(min_length=8,max_length=25)

    @model_validator(mode="after")
    def match_password(self):
        assert self.confirm_password == self.password, "password does not match"
        return self


class LoginDetails(BaseModel):
    username: str = Field(min_length=5,max_length=30)
    password :str = Field(min_length=8,max_length=25)

class Product(BaseModel):
    product_id:str = Field()
    name: str = Field(min_length=2,max_length=100)
    description: str|None = Field(None,max_length=1000)
    date_of_manufacture:datetime = Field()

class AddProductRequest(BaseModel):
    product: Product
    session_id: str = Field(min_length=32,max_length=32)


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/register_user")
def register_user(user_details: RegistrationDetails):
    if cur.execute(f"select * from users where username='{user_details.username}'").fetchone() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="USERNAME is already taken."
        )
    mongo_db.create_collection(user_details.username)
    cur.execute(f"""INSERT into users VALUES 
                (   '{uuid.uuid4()}','{user_details.username}',
                    '{hashlib.sha512(user_details.password.encode()).hexdigest()}'
                )""")
    conn.commit()
    return {"message":f"{user_details.username} registration successfull"}

@app.post("/login")
def login_user(user_details:LoginDetails):
    user = cur.execute(f"""select * from users where username='{user_details.username}'
                       and password='{hashlib.sha512(user_details.password.encode()).hexdigest()}'""").fetchone()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    session_id = create_session(user_details.username)
    return {"message": "Logged in successfully", "session_id": session_id}

@app.post("/logout")
def logout_user(session_id: str):
    del sessions[session_id]
    return {"message": "You are logged out in successfully"}

@app.post("/delete")
def remove_user(user_details:LoginDetails, session_id: str):
    user = cur.execute(f"""select * from users where username='{user_details.username}'
                       and password='{hashlib.sha512(user_details.password.encode()).hexdigest()}'""").fetchone()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    del sessions[session_id]
    mongo_db[user_details.username].drop()
    cur.execute(f""" DELETE from users where username == '{user_details.username}' """)
    return {"message":f"{user_details.username} account is successfully deleted."}


@app.post("/add_product")
def add_product(request:AddProductRequest):
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    username = sessions[request.session_id]

    if username in mongo_db.list_collection_names():
        mongo_db[username].insert_one(dict(request.product))
    
    return {"message":"Product added Successfully"}

@app.get("/list_products")
def list_products(session_id:str):
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied",
            headers={"WWW-Authenticate": "Basic"},
        )
    cursor = mongo_db[sessions[session_id]].find()
    result_list = []
    for document in cursor:
        document["_id"] = str(document["_id"])
        result_list.append(document)

    return result_list

@app.get("/product_detail")
def products_details(product_id:str,session_id:str):
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied",
            headers={"WWW-Authenticate": "Basic"},
        )
    # if product_id in mongo_db[sessions[session_id]]:
    cursor = mongo_db[sessions[session_id]].find({"product_id": product_id})
    result_list = []
    for document in cursor:
        document["_id"] = str(document["_id"])
        result_list.append(document)
    if len(result_list):
        return result_list
    
    raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product Not Found",
            headers={"WWW-Authenticate": "Basic"},
        )
    
@app.get("/remove_product")
def remove_product(product_id:str, session_id):
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied",
            headers={"WWW-Authenticate": "Basic"},
        )
    username = sessions[session_id]
    if mongo_db[username].count_documents({"product_id": product_id}):    
        mongo_db[username].delete_one({"product_id": product_id})
        return {"message": "Product removed successfully"}, 200
    raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enter correct Product ID",
                headers={"WWW-Authenticate": "Basic"},
                )



