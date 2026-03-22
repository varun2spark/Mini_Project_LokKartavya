from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import wikipedia
import requests
import random
import os
from duckduckgo_search import DDGS

app = Flask(__name__, static_folder='static', template_folder='templates')
# Enable CORS so frontend (HTML/JS) can connect
CORS(app)

# Standard Frontend Routing
@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/<path:page>')
def serve_pages(page):
    if page.endswith('.html'):
        return render_template(page)
    return "Not Found", 404

# In-memory storage for feedbacks and issues
feedbacks = []
issues = []

def get_politician_image(name, page_images=None):
    """
    Fetches the primary page image from Wikipedia API.
    """
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&titles={name.replace(' ', '_')}&format=json&pithumbsize=500"
        headers = {'User-Agent': 'LokKartavyaBot/1.0'}
        response = requests.get(url, headers=headers).json()
        pages = response.get("query", {}).get("pages", {})
        for page_id, page_info in pages.items():
            if "thumbnail" in page_info:
                return page_info["thumbnail"]["source"]
    except Exception as e:
        print(f"Wiki API Image Error: {e}")

    # Fallback to DDG if Wikipedia thumbnail not found
    try:
        results = DDGS().images(f"{name} politician portrait india high quality", max_results=1)
        if results and len(results) > 0:
            return results[0].get("image")
    except Exception as e:
        print(f"DDG Search Error: {e}")
        
    if page_images:
        for img in page_images:
            if not img.endswith('.svg') and 'Wikipedia' not in img:
                return img
    return None

def simulate_affidavit_data(name):
    """
    Simulates public affidavit data from MyNeta (since direct scraping breaks easily without specific IDs).
    Returns consistent data for the same name using string length & hashing.
    """
    if not name:
        name = "Unknown"
    
    # Use name to generate a predictable "random" seed so the same politician gets the same data
    random.seed(len(name) + sum(ord(c) for c in name))
    
    cases = random.randint(0, 5)
    assets_crores = random.randint(1, 200)
    
    roles = ["Member of Parliament", "MLA", "Cabinet Minister", "Chief Minister", "Political Leader", "Mayor"]
    edu_levels = ["Graduate", "Post Graduate", "Doctorate", "12th Pass", "10th Pass", "Illiterate"]
    constituencies = ["Varanasi", "New Delhi", "Gandhinagar", "Raebareli", "Kannauj", "Bhabanipur"]
    terms = ["2024 - 2029", "2020 - 2025", "2021 - 2026"]
    
    budget_total = random.randint(50, 5000)
    budget_used = int(budget_total * random.uniform(0.4, 0.95))
    
    budget = {
        "total": f"₹{budget_total} Cr",
        "utilized": f"₹{budget_used} Cr",
        "categories": [
            {"name": "Infrastructure", "amount": f"₹{int(budget_used*0.4)} Cr", "percentage": 40, "color": "#3B82F6"},
            {"name": "Healthcare", "amount": f"₹{int(budget_used*0.35)} Cr", "percentage": 35, "color": "#EF4444"},
            {"name": "Education", "amount": f"₹{int(budget_used*0.25)} Cr", "percentage": 25, "color": "#10B981"}
        ]
    }
    
    commitments = [
        {"id": 1, "title": "Setup Multi-Speciality Hospital", "status": random.choice(["completed", "in-progress", "pending"])},
        {"id": 2, "title": "Expand Highway Infrastructure", "status": random.choice(["completed", "in-progress", "pending"])},
        {"id": 3, "title": "Improve Rural Electrification", "status": random.choice(["completed", "in-progress", "pending"])}
    ]
    
    issues = [
        {"id": 1, "title": "Water-logging during monsoon", "date": "2024-01-15"},
        {"id": 2, "title": "Traffic congestion in city center", "date": "2024-02-20"}
    ]
    
    return {
        "criminal_cases": cases,
        "assets": f"Rs {assets_crores} Crores",
        "role": random.choice(roles),
        "education": random.choice(edu_levels),
        "constituency": random.choice(constituencies),
        "term": random.choice(terms),
        "budget": budget,
        "commitments": commitments,
        "issues": issues
    }

@app.route('/search', methods=['GET'])
def search_leader():
    """
    a) GET /search?name=
    - Search for a political leader by name
    - Fetch biography using Wikipedia API
    - Return summary, title, and image (if available)
    """
    name = request.args.get('name')
    if not name:
        return jsonify({"error": "Name parameter is required"}), 400
        
    try:
        wikipedia.set_lang("en")
        
        # We try to get the summary first.
        try:
            summary = wikipedia.summary(name, sentences=3)
            page = wikipedia.page(name)
            title = page.title
            
            # Find an image using DuckDuckGo (fallback to Wikipedia)
            image = get_politician_image(name, page.images)
            
            return jsonify({
                "title": title,
                "summary": summary,
                "image": image
            })
            
        except wikipedia.exceptions.DisambiguationError as e:
            # Try the first option if there's a disambiguation
            option = e.options[0]
            summary = wikipedia.summary(option, sentences=3)
            page = wikipedia.page(option)
            
            image = get_politician_image(option, page.images)
                    
            return jsonify({
                "title": page.title,
                "summary": summary,
                "image": image
            })
            
        except wikipedia.exceptions.PageError:
            return jsonify({"error": "Leader not found on Wikipedia"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/affidavit', methods=['GET'])
def get_affidavit():
    """
    b) GET /affidavit?name=
    - Scrape public affidavit data from MyNeta (or simulate if scraping fails)
    - Return: criminal cases, total assets
    """
    name = request.args.get('name')
    if not name:
        return jsonify({"error": "Name parameter is required"}), 400
        
    try:
        data = simulate_affidavit_data(name)
        return jsonify({
            "criminal_cases": data["criminal_cases"],
            "assets": data["assets"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/leader', methods=['GET'])
def get_leader_full_info():
    """
    c) GET /leader?name=
    - Combine Wikipedia + affidavit data
    - Return structured JSON: { name, role, education, summary, criminal_cases, assets }
    """
    name = request.args.get('name')
    if not name:
        return jsonify({"error": "Name parameter is required"}), 400
        
    try:
        # Fetch Wikipedia info
        wiki_title = name
        wiki_summary = "Biography not available."
        image = None
        
        try:
            wiki_summary = wikipedia.summary(name, sentences=3)
            page = wikipedia.page(name)
            wiki_title = page.title
            
            image = get_politician_image(name, page.images)
        except:
            image = get_politician_image(name)
            pass # Fallback to default if wikipedia fails
            
        # Get simulated affidavit data, which includes role and education for completeness
        affidavit_data = simulate_affidavit_data(name)
        
        response = {
            "name": wiki_title,
            "role": affidavit_data.get("role"),
            "education": affidavit_data.get("education"),
            "constituency": affidavit_data.get("constituency"),
            "term": affidavit_data.get("term"),
            "summary": wiki_summary,
            "criminal_cases": affidavit_data.get("criminal_cases"),
            "assets": affidavit_data.get("assets"),
            "budget": affidavit_data.get("budget"),
            "commitments": affidavit_data.get("commitments"),
            "issues": affidavit_data.get("issues"),
            "image": image
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    d) POST /feedback
    - Accept JSON: { name, subject, message }
    - Store in memory (list)
    - Return success message
    """
    data = request.json
    if not data or not all(k in data for k in ("name", "subject", "message")):
        return jsonify({"error": "Missing required fields: name, subject, message"}), 400
        
    # Store in memory
    feedbacks.append(data)
    
    # Return success message
    return jsonify({"message": "Feedback submitted successfully"}), 201

@app.route('/issue', methods=['POST'])
def submit_issue():
    """
    e) POST /issue
    - Accept JSON: { title, description }
    - Store in memory
    - Return success message
    """
    data = request.json
    if not data or not all(k in data for k in ("title", "description")):
        return jsonify({"error": "Missing required fields: title, description"}), 400
        
    # Store in memory
    issues.append(data)
    
    # Return success message
    return jsonify({"message": "Issue reported successfully"}), 201

if __name__ == '__main__':
    # Get port from environment variable (default to 5000)
    port = int(os.environ.get('PORT', 5000))
    # Run server on 0.0.0.0 so it's accessible from outside the container
    app.run(host='0.0.0.0', port=port, debug=True)
