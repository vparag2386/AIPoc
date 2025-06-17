# M&A Quality Check Demo

# Required packages:
# python-docx, flask, langchain, langchain-community

from docx import Document
from flask import Flask, request, jsonify
import threading

# Create sample contracts with optional omissions

def create_doc(filename, indemnity=True, non_compete=True, law=True):
    doc = Document()
    doc.add_heading("M&A Agreement", level=1)
    doc.add_paragraph("Date: 2024-01-01")
    doc.add_paragraph("Parties: Acme Corp and Target LLC")
    if indemnity:
        doc.add_paragraph("Indemnity: The parties agree to indemnify each other.")
    if non_compete:
        doc.add_paragraph("Non-compete: The seller shall not compete.")
    if law:
        doc.add_paragraph("Governing Law: Delaware applies.")
    doc.save(filename)

# Generate two sample documents
create_doc('doc123.docx', indemnity=False)
create_doc('doc124.docx', non_compete=False, law=False)

# Flask quality check server
app = Flask(__name__)

CLAUSES = {
    'indemnity': 'indemnity',
    'non-compete': 'non-compete',
    'governing-law': 'governing law'
}

def check_contract(path):
    doc = Document(path)
    text = '\n'.join(p.text.lower() for p in doc.paragraphs)
    missing = [c for c, k in CLAUSES.items() if k not in text]
    result = {
        'missing_clauses': missing,
        'date_mismatch': '2024' not in text,
        'entity_mismatch': 'acme corp' not in text
    }
    return result

@app.route('/mcp/quality', methods=['POST'])
def quality():
    data = request.json
    return jsonify(check_contract(data['path']))

# Start server in background
threading.Thread(target=app.run, kwargs={'port': 5000}, daemon=True).start()

# LangChain tool and agent using ChatOllama
from langchain.tools import tool
import requests

@tool
def run_quality_check(path: str) -> dict:
    """send file path to quality server"""
    r = requests.post('http://localhost:5000/mcp/quality', json={'path': path})
    return r.json()

from langchain_community.chat_models import ChatOllama
from langchain.agents import initialize_agent, AgentType

llm = ChatOllama(model='llama3.2')
agent = initialize_agent([run_quality_check], llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)

# Demo queries
if __name__ == '__main__':
    print(agent.run('Check doc123 for missing clauses.'))
    print(agent.run('Run a quality check on doc124.'))
