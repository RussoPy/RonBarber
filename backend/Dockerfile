FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install flask-cors firebase-admin Flask pyautogui pyperclip python-dotenv

EXPOSE 8000

CMD ["python", "app/server.py"]
