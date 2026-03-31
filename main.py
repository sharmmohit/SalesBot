import sys
import os
from database.init_db import init_database
from vector_store.chroma_manager import ChromaManager
from agents.rag_pipeline import RAGPipeline
from agents.sales_agent import SalesAgent
from config import Config

def initialize_system():
    print("Initializing SalesBot AI CRM Agent...")
    
    os.makedirs("./database", exist_ok=True)
    os.makedirs("./vector_store/chroma_db", exist_ok=True)
    
    print("1. Initializing database...")
    init_database(Config.DATABASE_PATH)
    
    print("2. Initializing vector store...")
    chroma_manager = ChromaManager(Config.CHROMA_PERSIST_DIR)
    
    print("3. Loading data into vector store...")
    import sqlite3
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()
    for customer in customers:
        customer_data = {
            "id": customer[0],
            "name": customer[1],
            "email": customer[2],
            "company": customer[4],
            "industry": customer[5],
            "status": customer[6],
            "lead_score": customer[8]
        }
        chroma_manager.add_customer_data(customer_data)
    
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    for product in products:
        product_data = {
            "id": product[0],
            "name": product[1],
            "description": product[2],
            "price": product[3],
            "category": product[4],
            "features": product[5]
        }
        chroma_manager.add_product_knowledge(product_data)
    
    conn.close()
    
    print("4. Initializing RAG pipeline...")
    rag_pipeline = RAGPipeline(Config.DATABASE_PATH, chroma_manager, Config.GROQ_API_KEY)
    
    print("5. Initializing sales agent...")
    sales_agent = SalesAgent(Config.DATABASE_PATH, Config.GROQ_API_KEY, rag_pipeline)
    
    print("System initialized successfully!")
    
    return rag_pipeline, sales_agent

def interactive_mode(rag_pipeline):
    print("\n" + "="*50)
    print("SalesBot AI CRM Agent - Interactive Mode")
    print("="*50)
    print("Commands:")
    print("  /help - Show this help")
    print("  /customers - List available customers")
    print("  /exit - Exit the program")
    print("="*50 + "\n")
    
    import sqlite3
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, company FROM customers")
    customers = cursor.fetchall()
    conn.close()
    
    print("Available customers:")
    for customer in customers:
        print(f"  ID {customer[0]}: {customer[1]} ({customer[2]})")
    print()
    
    while True:
        try:
            user_input = input("\nEnter customer ID and query (format: 'ID: your question'): ").strip()
            
            if user_input.lower() == '/exit':
                print("Goodbye!")
                break
            elif user_input.lower() == '/help':
                print("Commands: /help, /customers, /exit")
                continue
            elif user_input.lower() == '/customers':
                conn = sqlite3.connect(Config.DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, company FROM customers")
                customers = cursor.fetchall()
                conn.close()
                for customer in customers:
                    print(f"  ID {customer[0]}: {customer[1]} ({customer[2]})")
                continue
            
            if ':' in user_input:
                parts = user_input.split(':', 1)
                try:
                    customer_id = int(parts[0].strip())
                    query = parts[1].strip()
                    
                    print(f"\nProcessing query for customer ID {customer_id}...")
                    response = rag_pipeline.generate_response(customer_id, query)
                    print(f"\nSalesBot: {response}")
                except ValueError:
                    print("Error: Invalid customer ID. Please use format: 'ID: your question'")
            else:
                print("Error: Please use format: 'ID: your question'")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    rag_pipeline, sales_agent = initialize_system()
    
    print("\nStarting API server...")
    print("Run: uvicorn api.main:app --reload --port 8000")
    print("\nOr use interactive mode:")
    
    interactive_mode(rag_pipeline)