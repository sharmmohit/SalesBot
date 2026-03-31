import sqlite3
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

class RAGPipeline:
    def __init__(self, db_path, chroma_manager, groq_api_key):
        self.db_path = db_path
        self.chroma_manager = chroma_manager
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.3
        )
    
    def get_customer_details(self, customer_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, email, company, industry, status, lead_score, last_contact
            FROM customers WHERE id = ?
        """, (customer_id,))
        
        customer = cursor.fetchone()
        conn.close()
        
        if customer:
            return {
                "id": customer[0],
                "name": customer[1],
                "email": customer[2],
                "company": customer[3],
                "industry": customer[4],
                "status": customer[5],
                "lead_score": customer[6],
                "last_contact": customer[7]
            }
        return None
    
    def get_customer_interactions(self, customer_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT interaction_type, content, sentiment, created_at
            FROM interactions
            WHERE customer_id = ?
            ORDER BY created_at DESC LIMIT 5
        """, (customer_id,))
        
        interactions = cursor.fetchall()
        conn.close()
        
        return interactions
    
    def get_products(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, description, price, category, features FROM products")
        products = cursor.fetchall()
        conn.close()
        
        return products
    
    def generate_response(self, customer_id, query):
        customer = self.get_customer_details(customer_id)
        if not customer:
            return "Customer not found"
        
        interactions = self.get_customer_interactions(customer_id)
        products = self.get_products()
        
        vector_context = self.chroma_manager.retrieve_context(query)
        
        system_msg = SystemMessage(content="""You are SalesBot AI, an autonomous CRM agent. 
        Your role is to handle sales conversations, qualify leads, schedule follow-ups, 
        and provide personalized product recommendations.
        
        Be professional, concise, and focused on moving the sales process forward.""")
        
        user_msg = HumanMessage(content=f"""
        Customer Information:
        Name: {customer['name']}
        Company: {customer['company']}
        Industry: {customer['industry']}
        Status: {customer['status']}
        Lead Score: {customer['lead_score']}
        
        Recent Interactions:
        {interactions}
        
        Available Products:
        {products}
        
        Vector Database Context:
        {vector_context}
        
        Customer Query: {query}
        
        Generate a personalized response:
        """)
        
        response = self.llm.invoke([system_msg, user_msg])
        
        self.log_interaction(customer_id, query, response.content)
        
        return response.content
    
    def log_interaction(self, customer_id, query, response):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO interactions (customer_id, interaction_type, content, sentiment)
            VALUES (?, ?, ?, ?)
        """, (customer_id, "query", f"User: {query}\nBot: {response}", "neutral"))
        
        conn.commit()
        conn.close()