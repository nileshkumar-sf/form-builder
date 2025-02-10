from fastapi import FastAPI, HTTPException
from service.form_service import FormService
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
form_service = FormService()

@app.post("/create-form")
async def create_form(prompt: str):
    try:
        # Pass the user prompt to the service to generate the form and trigger the API
        response = form_service.create_and_trigger_form(prompt)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
