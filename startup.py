"""
startup.py - Run this as a build/init step on Render
to initialize the database and vector store before the API starts.
This is called automatically via the lifespan event in api/main.py
"""

import os
from database.init_db import init_database
from vector_store.chroma_manager import ChromaManager
from config import Config


def run_startup():
    print("Running SalesBot startup initialization...")

    os.makedirs("./database", exist_ok=True)
    os.makedirs("./vector_store/chroma_db", exist_ok=True)

    print("Initializing database...")
    init_database(Config.DATABASE_PATH)

    print("Initializing vector store...")
    chroma_manager = ChromaManager(Config.CHROMA_PERSIST_DIR)

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
    print("Startup complete!")


if __name__ == "__main__":
    run_startup()
