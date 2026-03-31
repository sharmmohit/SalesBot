from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from vector_store.chroma_manager import ChromaManager
from agents.rag_pipeline import RAGPipeline
from agents.sales_agent import SalesAgent

app = FastAPI(title="SalesBot AI CRM Agent")

config = Config()
chroma_manager = ChromaManager(config.CHROMA_PERSIST_DIR)
rag_pipeline = RAGPipeline(config.DATABASE_PATH, chroma_manager, config.GROQ_API_KEY)
sales_agent = SalesAgent(config.DATABASE_PATH, config.GROQ_API_KEY, rag_pipeline)

class QueryRequest(BaseModel):
    customer_id: int
    query: str

class LeadScoreUpdate(BaseModel):
    customer_id: int
    score: int

class FollowupRequest(BaseModel):
    customer_id: int
    days: int = 3
    notes: str = ""

@app.get("/")
def read_root():
    return {"message": "SalesBot AI CRM Agent API", "status": "running"}

@app.post("/chat")
def chat(request: QueryRequest):
    try:
        response = rag_pipeline.generate_response(request.customer_id, request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/qualify/{customer_id}")
def qualify_lead(customer_id: int):
    try:
        result = sales_agent.qualify_lead(customer_id)
        return {"qualification_report": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_lead_score")
def update_lead_score(request: LeadScoreUpdate):
    try:
        result = sales_agent.update_lead_score(request.customer_id, request.score)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule_followup")
def schedule_followup(request: FollowupRequest):
    try:
        result = sales_agent.schedule_followup(request.customer_id, request.days, request.notes)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pending_followups")
def get_pending_followups():
    try:
        followups = sales_agent.get_pending_followups()
        return {"followups": followups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute_followups")
def execute_followups():
    try:
        results = sales_agent.execute_followups()
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/outreach/{customer_id}")
def generate_outreach(customer_id: int):
    try:
        outreach = sales_agent.generate_outreach(customer_id)
        return {"outreach_message": outreach}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))