@echo off
cd chainforge/platform-backend
pip install -r requirements.txt
uvicorn main:app --reload
pause
