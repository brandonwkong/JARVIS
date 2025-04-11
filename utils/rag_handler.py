from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import json
import os
from datetime import datetime
from utils.database import Database  # Add this with other imports

load_dotenv(override=True)

class RAGHandler:
    def __init__(self):
        # Admin mode initialization
        self.admin_mode = False
        self.admin_chat_history = []
        self.learning_buffer = []
        self.db = Database() 
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        # Load personal data
        with open('personal_data.json', 'r') as f:
            self.personal_data = json.load(f)
        
        self.load_all_knowledge()
        # Initialize embeddings
        self.documents = self._prepare_documents()
        self.vector_store = Chroma.from_texts(
            texts=self.documents,
            embedding=self.embeddings
        )
        
        # Initialize chat model
        self.chat_model = ChatOpenAI(
            temperature=0.7,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",  # Change this
            return_messages=True,
            output_key='answer',
            input_key='question'
        )

        # Create custom prompt templates for both modes
        self.admin_template = """You are my personal AI assistant. We are having a direct conversation.
        - Use first person when referring to me
        - Remember our previous conversations
        - Learn from my corrections and new information
        - Keep track of important details I share
        - Ask for clarification if needed
        
        Context about me:
        {context}
        
        Current conversation history:
        {chat_history}
        """

        self.public_template = """You are Brandon's AI assistant. Use the following context to answer questions about Brandon:
        
        {context}
        
        Important guidelines:
        - Respond conversationally, not by reading directly from the data
        - Adapt your tone to match the question's formality
        - Only share information that would be appropriate in a professional context
        - If you're not sure about something, say so rather than making assumptions
        - Have your own personality, you just know everything about Brandon
        - Use third-person perspective ("Brandon is" instead of "I am")
        
        Current conversation history:
        {chat_history}
        """

        # Initialize the chain
        self._initialize_chain(self.public_template)  # Start with public mode

    def load_all_knowledge(self):
        print("\n=== LOADING KNOWLEDGE BASE ===")
        # Start with base documents
        self.documents = self._prepare_documents()
        
        # Add learned info
        learned_info = self.db.get_all_verified_info()
        for category, content in learned_info:
            if not content.startswith("Brandon"):
                content = f"Brandon {content}"
            self.documents.append(content)
            print(f"Added to knowledge base: {content}")
        
        # Update vector store
        self.vector_store = Chroma.from_texts(
            texts=self.documents,
            embedding=self.embeddings
        )
        print("=== KNOWLEDGE BASE LOADED ===\n")

    def _initialize_chain(self, system_template):
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.chat_model,
            retriever=self.vector_store.as_retriever(),
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={
                "prompt": ChatPromptTemplate.from_messages([
                    SystemMessagePromptTemplate.from_template(system_template),
                    HumanMessagePromptTemplate.from_template("{question}")
                ])
            },
            chain_type="stuff",  # Add this
            verbose=True  # Add this for debugging
    )

    def get_response(self, query):
        print(f"\nProcessing query in {'Admin' if self.admin_mode else 'Public'} mode")
        print(f"Query: {query}")

        if self.admin_mode:
            # Process for potential learning
            should_learn, learning_confirmation = self._process_learning(query, None)
            
            if should_learn:
                return learning_confirmation
        
        # Normal response processing
        result = self.chain({
            "question": query,
            "chat_history": self.admin_chat_history if self.admin_mode else []
        })
        
        if self.admin_mode:
            self.db.add_conversation("assistant", result['answer'])
            self.admin_chat_history.append({"role": "assistant", "content": result['answer']})
        
        return result['answer']

    def toggle_admin_mode(self, password):
        if password == os.getenv("ADMIN_PASSWORD"):  # Change this to a secure password
            self.admin_mode = not self.admin_mode
            # Reinitialize chain with appropriate template
            template = self.admin_template if self.admin_mode else self.public_template
            self._initialize_chain(template)
            return {"success": True, "mode": "admin" if self.admin_mode else "public"}
        return {"success": False}

    def _process_learning(self, query, response):
        print("\n=== ANALYZING INPUT FOR NEW INFORMATION ===")
        
        # Create an analysis prompt
        analysis_prompt = f"""
        Analyze this input and determine if it contains new personal information about the user that should be saved.
        Focus on extracting clear factual statements about hobbies, skills, or experiences.
        
        Input: "{query}"
        
        Respond in JSON format:
        {{
            "contains_new_info": true/false,
            "category": "hobby/skill/experience",
            "extracted_info": "the information in third-person format starting with 'Brandon'",
            "confidence": 0-1
        }}
        """
        
        try:
            analyzer = ChatOpenAI(
                temperature=0,
                model="gpt-3.5-turbo-0125",
                openai_api_key=os.getenv('OPENAI_API_KEY')
            )
            
            analysis_response = analyzer.invoke(analysis_prompt)
            result = json.loads(analysis_response.content)
            
            print(f"Analysis result: {json.dumps(result, indent=2)}")
            
            if result["contains_new_info"] and result["confidence"] > 0.7:
                # Format the information
                info_to_save = result["extracted_info"]
                if not info_to_save.startswith("Brandon"):
                    info_to_save = f"Brandon {info_to_save}"
                
                print(f"Saving information: {info_to_save}")
                
                # Store in database
                self.db.add_learned_info(result["category"], info_to_save)
                
                # Update knowledge base
                self.load_all_knowledge()
                
                # Reinitialize chain
                template = self.admin_template if self.admin_mode else self.public_template
                self._initialize_chain(template)
                
                return True, f"I've learned something new: {info_to_save}"
            
            return False, None
            
        except Exception as e:
            print(f"Error in learning analysis: {e}")
            return False, None
    def _prepare_documents(self):
        documents = []
        documents.append(self.personal_data['bio']['content'])
        
        for job in self.personal_data['work_experience']:
            doc = f"Work at {job['company']} as {job['title']} ({job['period']}): {job['description']}"
            documents.append(doc)
        
        for edu in self.personal_data['education']:
            doc = f"Education at {edu['institution']}: {edu['degree']} ({edu['period']}). {edu['description']}"
            documents.append(doc)
            
        return documents
    
    def view_learned_info(self):
        """View all stored learned information"""
        return self.db.get_all_verified_info()

    def view_recent_conversations(self, limit=10):  
        """View recent admin conversations"""
        return self.db.get_recent_conversations(limit)