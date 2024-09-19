from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import List
from pydantic import BaseModel, field_validator
import json
import os
import asyncio
import aiohttp
import uvicorn

app = FastAPI()
security = HTTPBasic()


#Файл с заметками
NOTES_FILE = 'notes.json'
#Файл с пользователями
USERS_FILE = 'users.json'

#Для каждого соответственно по классу с валидацией на вводимый тип данных
class Note(BaseModel):
    title: str
    content: str

class User(BaseModel):
    username: str
    password: str

# функция запроса в яндекс спелер для валидации
async def check_correct(value):
    async with aiohttp.ClientSession() as session:
        async with session.get('https://speller.yandex.net/services/spellservice.json/checkText?',
                               params={'text': value}) as response: #формируем запрос на сайт Яндекс
            html = json.loads(await response.text()) #возвращает так же JSON файл с информацией включая предложенные исправления
            return html
# Загружаем пользователей из файла
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Ошибка при загрузке пользователей: {e}")
            return {}
    return {}

# Загружаем заметки из файла
def load_notes():
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Ошибка при загрузке файла: {e}")
            return {}
    return {}
#Сохраняем юзеров в файл
def save_users(users):
    try:
        with open(USERS_FILE, 'w') as file:
            json.dump(users, file)
    except Exception as e:
        print(f"Ошибка при сохранении пользователей: {e}")

# Сохраняем заметки в файл
def save_notes(notes):
    try:
        with open(NOTES_FILE, 'w') as file:
            json.dump(notes, file)
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")



# Аутентифицируем пользователя на основе предустановленных учетных данных
def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    users = load_users()
    if credentials.username in users and users[credentials.username] == credentials.password:
        return credentials.username
    raise HTTPException(
        status_code=401,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Basic"},
    )

# Создание нового пользователя
@app.post("/users")
async def create_user(user: User):
    users = load_users()
    if user.username in users:
        raise HTTPException(status_code=400, detail="Username already exists")
    users[user.username] = user.password
    save_users(users)
    return {"message": "User created successfully"}

# Возвращаем список заметок для аутентифицированного пользователя
@app.get("/notes", response_model=List[Note])
async def get_notes(user: str = Depends(get_current_user)):
    notes = load_notes()
    user_notes = notes.get(user, [])
    return user_notes


@app.post("/notes")
async def add_note(note: Note, user: str = Depends(get_current_user)):
    corrects_title = await check_correct(note.title)
    corrects_content = await check_correct(note.content)
    notes = load_notes()
    if corrects_title and corrects_title[0].get('s'):
        suggestion = corrects_title[0]['s'][0]  # Берем первую исправленную версию
        raise HTTPException(status_code=400,
                            detail=f'В заголовке ошибка! Возможно вы имели ввиду "{suggestion}"? исправьте и повторите попытку')
    if corrects_content and corrects_content[0].get('s'):
        suggestion = corrects_content[0]['s'][0]  # Берем первую исправленную версию
        raise HTTPException(status_code=400,
                            detail=f'В тексте заметки ошибка! Возможно вы имели ввиду "{suggestion}"? исправьте и повторите попытку')
    if user not in notes:
        notes[user] = []
    notes[user].append(note.dict())
    save_notes(notes)
    return {"message": "Note added successfully", "note": note}


# Удаляем заметку по её идентификатору для аутентифицированного пользователя
@app.delete("/notes/{note_id}", response_model=dict)
async def delete_note(note_id: int, user: str = Depends(get_current_user)):
    notes = load_notes()
    if user in notes and 0 <= note_id < len(notes[user]):
        deleted_note = notes[user].pop(note_id)
        save_notes(notes)
        return {"message": "Note deleted", "note": deleted_note}
    else:
        raise HTTPException(status_code=404, detail="Note not found")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
