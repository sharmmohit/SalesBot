import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

class SalesAgent:
    def __init__(self, db_path, groq_api_key, rag_pipeline):
        self.db_path = db_path
        self.groq_api_key = groq_api_key
        self.rag_pipeline = rag_pipeline
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.2
        )
    
    def qualify_lead(self, customer_id):
        customer = self.rag_pipeline.get_customer_details(customer_id)
        if not customer:
            return "Customer not found"
        
        interactions = self.rag_pipeline.get_customer_interactions(customer_id)
        
        prompt = PromptTemplate(
            input_variables=["name", "company", "industry", "lead_score", "interactions"],
            template="""
            Evaluate this lead for sales qualification:
            
            Customer: {name}
            Company: {company}
            Industry: {industry}
            Current Lead Score: {lead_score}
            Recent Interactions: {interactions}
            
            Consider:
            1. BANT criteria (Budget, Authority, Need, Timeline)
            2. Engagement level from interactions
            3. Industry fit for our products
            4. Current lead score
            
            Provide:
            - Qualification status (Hot/Warm/Cold)
            - Recommended next steps
            - Suggested products to pitch
            - Any red flags or concerns
            
            Format your response as a structured qualification report.
            """
        )
        
        chain = prompt | self.llm
        result = chain.invoke({
            "name": customer['name'],
            "company": customer['company'],
            "industry": customer['industry'],
            "lead_score": customer['lead_score'],
            "interactions": interactions
        })
        
        return result.content
    
    def schedule_followup(self, customer_id, days_from_now=3, notes=""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        scheduled_date = datetime.now() + timedelta(days=days_from_now)
        
        cursor.execute("""
            INSERT INTO followups (customer_id, scheduled_date, status, notes)
            VALUES (?, ?, ?, ?)
        """, (customer_id, scheduled_date, "pending", notes))
        
        conn.commit()
        conn.close()
        
        return f"Follow-up scheduled for {scheduled_date.strftime('%Y-%m-%d %H:%M')}"
    
    def update_lead_score(self, customer_id, new_score):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE customers 
            SET lead_score = ?, last_contact = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_score, customer_id))
        
        conn.commit()
        conn.close()
        
        return f"Lead score updated to {new_score}"
    
    def get_pending_followups(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT f.id, c.name, c.email, f.scheduled_date, f.notes
            FROM followups f
            JOIN customers c ON f.customer_id = c.id
            WHERE f.status = 'pending' AND f.scheduled_date <= datetime('now')
            ORDER BY f.scheduled_date
        """)
        
        followups = cursor.fetchall()
        conn.close()
        
        return followups
    
    def execute_followups(self):
        pending = self.get_pending_followups()
        results = []
        
        for followup in pending:
            followup_id, customer_name, customer_email, scheduled_date, notes = followup
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id FROM customers WHERE email = ?
            """, (customer_email,))
            
            customer = cursor.fetchone()
            
            if customer:
                response = self.rag_pipeline.generate_response(
                    customer[0],
                    f"Follow-up reminder: {notes}"
                )
                
                cursor.execute("""
                    UPDATE followups SET status = 'completed'
                    WHERE id = ?
                """, (followup_id,))
                
                results.append({
                    "customer": customer_name,
                    "response": response
                })
            
            conn.commit()
            conn.close()
        
        return results
    
    def generate_outreach(self, customer_id):
        customer = self.rag_pipeline.get_customer_details(customer_id)
        if not customer:
            return "Customer not found"
        
        products = self.rag_pipeline.get_products()
        
        few_shot_examples = [
            {
                "industry": "Technology",
                "lead_score": 75,
                "output": "Hi [Name], I noticed your company TechCorp is in the technology sector. With a lead score of 75, you're showing strong interest. Our SalesBot Pro platform could help automate your sales workflow and increase conversion rates by up to 35%. Would you be interested in a 15-minute demo to see how it works?"
            },
            {
                "industry": "Healthcare",
                "lead_score": 60,
                "output": "Hello [Name], HealthSystems Inc has great potential in the healthcare space. I see you're in the lead qualification stage. Our CRM Suite offers HIPAA-compliant features specifically designed for healthcare providers. Would you like to learn more about how we handle patient data security?"
            }
        ]
        
        prompt = FewShotPromptTemplate(
            examples=few_shot_examples,
            example_prompt=PromptTemplate(
                input_variables=["industry", "lead_score", "output"],
                template="Industry: {industry}\nLead Score: {lead_score}\nOutput: {output}"
            ),
            prefix="Generate a personalized sales outreach message:",
            suffix="Industry: {industry}\nLead Score: {lead_score}\nCustomer: {name}\nCompany: {company}\nProducts: {products}\n\nOutreach Message:",
            input_variables=["industry", "lead_score", "name", "company", "products"]
        )
        
        chain = prompt | self.llm
        outreach = chain.invoke({
            "industry": customer['industry'],
            "lead_score": customer['lead_score'],
            "name": customer['name'],
            "company": customer['company'],
            "products": products
        })
        
        return outreach.content