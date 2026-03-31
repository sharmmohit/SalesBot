import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

class ChromaManager:
    def __init__(self, persist_directory):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "sales_knowledge"
        self.collection = self.get_or_create_collection()
    
    def get_or_create_collection(self):
        try:
            collection = self.client.get_collection(self.collection_name)
        except:
            collection = self.client.create_collection(self.collection_name)
        return collection
    
    def generate_embedding(self, text):
        return self.model.encode(text).tolist()
    
    def add_customer_data(self, customer_data):
        doc_id = f"customer_{customer_data['id']}"
        content = f"""
        Customer: {customer_data['name']}
        Company: {customer_data['company']}
        Industry: {customer_data['industry']}
        Status: {customer_data['status']}
        Lead Score: {customer_data['lead_score']}
        """
        
        embedding = self.generate_embedding(content)
        
        self.collection.upsert(
            documents=[content],
            embeddings=[embedding],
            metadatas=[{
                "type": "customer",
                "customer_id": customer_data['id'],
                "name": customer_data['name']
            }],
            ids=[doc_id]
        )
        return doc_id
    
    def add_product_knowledge(self, product_data):
        doc_id = f"product_{product_data['id']}"
        content = f"""
        Product: {product_data['name']}
        Description: {product_data['description']}
        Price: ${product_data['price']}
        Category: {product_data['category']}
        Key Features: {product_data['features']}
        """
        
        embedding = self.generate_embedding(content)
        
        self.collection.upsert(
            documents=[content],
            embeddings=[embedding],
            metadatas=[{
                "type": "product",
                "product_id": product_data['id'],
                "name": product_data['name']
            }],
            ids=[doc_id]
        )
        return doc_id
    
    def retrieve_context(self, query, n_results=3):
        query_embedding = self.generate_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        context = []
        if results['documents']:
            for doc in results['documents'][0]:
                context.append(doc)
        
        return " ".join(context)