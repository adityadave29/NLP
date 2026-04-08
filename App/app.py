from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import shutil
import tempfile
from werkzeug.utils import secure_filename
import numpy as np
import docx
import re
import spacy
import pdfplumber
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import util

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
RESUME_FOLDER = 'resumes'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)

# Global variables for storing processed data
jd_text = ""
resume_text_list = []
JD_struct = {}
Resume_struct = []

# Load models at startup
print("Loading models...")
try:
    nlp = spacy.load("en_core_sci_sm")
    print("✅ scispaCy loaded successfully")
except OSError:
    print("⚠️  scispaCy not found, falling back to regular spaCy")
    nlp = spacy.load("en_core_web_sm")

model = SentenceTransformer('all-MiniLM-L6-v2')
print("Models loaded successfully!")

# Skills and Education constants
COMPREHENSIVE_SKILLS = [
    "AJAX", "API Design", "API Development", "API Gateways", "API Security", "Agile Methodologies",
    "Algorithms", "Ansible", "Application Architecture", "Application Security", "Architectural Patterns",
    "Architecture Principles", "Asynchronous Communication", "Authentication & Authorization", "Automated Deployment",
    "Automated Testing", "Backend Development", "Backup & Restore", "Behavior-Driven Development", "Benchmarking",
    "Big Data", "Block Storage", "Blockchain", "Blue-Green Deployments", "Build Automation", "Build Tools",
    "Business Alignment", "Business Intelligence (BI)", "Business Process Modeling", "C++", "Caching Strategies",
    "Capacity Planning", "Cloud Architectures", "Cloud Automation", "Cloud Cost Management", "Cloud Databases",
    "Cloud Infrastructure Management", "Cloud Security", "Cloud Services", "Cloud Storage", "Cloud-native Development",
    "Clustering", "Code Documentation", "Code Quality", "Code Reviews", "Collaboration Tools",
    "Command-Line Interfaces", "Communication Tools", "Compliance Standards", "Configuration Management",
    "Container Security", "Containerization", "Content Delivery Networks", "Content Management Systems (CMS)",
    "Continuous Delivery (CD)", "Continuous Deployment (CD)", "Continuous Integration (CI)", "Cost Estimates",
    "Cost-Benefit Analysis", "Cryptography", "Customer Relationship Management (CRM)", "Cybersecurity Awareness",
    "Cybersecurity Standards", "Data Analysis", "Data Anonymization", "Data Architecture", "Data Backup",
    "Data Consistency", "Data Entry", "Data Federation", "Data Governance", "Data Integration",
    "Data Integrity", "Data Lakes", "Data Lifecycle Management", "Data Lineage", "Data Loss Prevention",
    "Data Migration", "Data Modeling", "Data Partitioning", "Data Profiling", "Data Quality",
    "Data Replication Strategies", "Data Structures", "Data Types", "Data Visualization", "Data Warehousing",
    "Database Administration", "Database Design", "Database Security", "Debugging", "Decoupled Architecture",
    "Deduplication", "Deep Learning", "Deployment Automation", "Design Patterns", "Distributed Systems",
    "Docker", "Documentation", "Domain-Driven Design", "Elasticsearch", "Elasticsearch", "Encryption",
    "ETL", "Event-Driven Architecture", "Fault Tolerance", "Feature Engineering", "Frontend Development",
    "Full Stack Development", "Git", "GitHub", "GitLab", "GraphQL", "Hadoop", "HTML", "HTML5",
    "HTTP", "HTTPS", "Integration Testing", "Java", "JavaScript", "Jenkins", "JSON", "JWT",
    "Kafka", "Kubernetes", "Linux", "Logging", "Machine Learning", "Microservices", "MongoDB",
    "MySQL", "NGINX", "Node.js", "NoSQL", "OAuth", "Object-Oriented Programming", "OpenAPI",
    "Performance Optimization", "PostgreSQL", "Python", "RabbitMQ", "React", "Redis", "REST",
    "RESTful APIs", "Ruby", "Ruby on Rails", "S3", "Scala", "Security", "Serverless Architecture",
    "SQL", "SQLite", "Swagger", "System Design", "Testing", "TypeScript", "Unit Testing", "Version Control",
    "Vue.js", "Web Development", "Web Security", "XML", "YAML"
]

DEGREE_KEYWORDS = [
    "btech", "b.tech", "be", "b.e", "bachelor of engineering",
    "bachelor of technology", "bachelor", "bsc", "b.sc",
    "bachelor of science", "bachelor", "bsc", "b.sc",
    "bachelor of computer applications", "bca", "bachelor of computer applications",
    "bcom", "bachelor of commerce", "ba", "bachelor of arts",
    "mba", "master of business administration",
    "mtech", "m.tech", "me", "m.e", "master of engineering",
    "master of technology", "master", "msc", "m.sc",
    "master of science", "master", "msc", "m.sc",
    "mca", "master of computer applications", "master of computer applications",
    "phd", "ph.d", "doctor of philosophy",
    "diploma", "polytechnic", "advanced diploma",
    "certification", "certificate", "nondegree"
]

FIELD_KEYWORDS = [
    "computer science", "computer science engineering", "cse",
    "cs", "information technology", "it", "software engineering",
    "computer engineering",
    "artificial intelligence", "ai", "machine learning", "ml",
    "data science", "data analytics", "big data",
    "deep learning", "nlp", "natural language processing",
    "computer vision",
    "electronics", "electronics engineering",
    "electronics and communication", "ece",
    "electrical engineering", "ee",
    "mechanical engineering", "mech",
    "civil engineering", "civil",
    "chemical engineering", "biotechnology",
    "biomedical engineering", "aerospace engineering",
    "business administration", "finance", "marketing",
    "human resources", "operations",
    "mathematics", "statistics", "physics"
]

START_KEYWORDS = [
    "experience", "work experience", "professional experience",
    "employment", "employment history", "work history",
    "career history", "professional background",
    "experience summary", "relevant experience",
    "industry experience", "technical experience",
    "internship", "internships", "internship experience",
    "positions held", "roles and responsibilities",
    "career profile", "professional profile"
]

END_KEYWORDS = [
    "education", "academic background", "academic qualifications",
    "skills", "technical skills", "core competencies",
    "key skills", "skills summary",
    "projects", "project experience", "academic projects",
    "certifications", "certification", "licenses",
    "achievements", "awards", "publications",
    "languages", "interests", "hobbies",
    "summary", "objective", "profile"
]

PROJECT_KEYWORDS = [
    "projects", "project experience", "academic projects", "project work",
    "project", "work project", "personal projects", "portfolio",
    "development projects", "software projects", "web projects",
    "application projects", "mobile projects", "desktop projects",
    "database projects", "api projects", "system projects",
    "research projects", "thesis projects", "capstone projects", "final year projects",
    "github projects", "gitlab projects", "bitbucket projects", "open source projects",
    "freelance projects", "consulting projects", "internship projects", "college projects",
    "university projects", "student projects", "team projects", "individual projects",
    "group projects", "collaborative projects", "enterprise projects", "startup projects",
    "iot projects", "machine learning projects", "ai projects", "data science projects",
    "web development projects", "full stack projects", "frontend projects", "backend projects",
    "devops projects", "cloud projects", "mobile app projects", "desktop applications",
    "software development projects", "application development", "system design projects",
    "database projects", "api development projects", "microservices projects"
]

CERTIFICATION_KEYWORDS = [
    "certifications", "certification", "certificates", "certificate", "certified",
    "licenses", "license", "licensed", "professional certification", "industry certification",
    "technical certification", "software certification", "cloud certification", "security certification",
    "programming certification", "development certification", "it certification", "computer certification",
    "aws certification", "azure certification", "gcp certification", "google certification",
    "microsoft certification", "oracle certification", "cisco certification", "compTIA certification",
    "pmi certification", "scrum certification", "agile certification", "devops certification",
    "kubernetes certification", "docker certification", "jenkins certification", "git certification",
    "python certification", "java certification", "javascript certification", "react certification",
    "nodejs certification", "angular certification", "vuejs certification", "database certification",
    "sql certification", "nosql certification", "mongodb certification", "postgresql certification",
    "mysql certification", "data science certification", "machine learning certification", "ai certification",
    "cybersecurity certification", "network security certification", "information security certification",
    "ethical hacking certification", "penetration testing certification", "cloud security certification",
    "full stack certification", "backend certification", "frontend certification", "web development certification"
]

DOMAIN_KEYWORDS = [
    "web development", "frontend", "backend", "full stack", "full-stack",
    "mobile development", "android", "ios", "react native", "flutter",
    "data science", "machine learning", "artificial intelligence", "ai", "ml", "deep learning", "nlp",
    "cloud computing", "cloud", "aws", "azure", "gcp", "devops", "kubernetes", "docker",
    "cybersecurity", "security", "network security", "information security",
    "database", "sql", "nosql", "mysql", "postgresql", "mongodb", "redis",
    "software engineering", "system design", "architecture", "scalability",
    "blockchain", "web3", "cryptocurrency", "smart contracts",
    "game development", "gaming", "unity", "unreal engine",
    "iot", "internet of things", "embedded systems", "hardware"
]

LOCATION_KEYWORDS = [
    "location", "city", "state", "country", "remote", "onsite", "offsite",
    "work location", "job location", "workplace", "office location", "based in",
    "currently located", "living in", "residing in", "address",
    "willing to relocate", "relocation", "ready to relocate", "open to relocation",
    "preferred location", "desired location", "target location", "work from home", "remote work",
    "work from home", "wfh", "telecommute", "telecommuting", "virtual work",
    "hybrid work", "flexible work", "local work", "in-office work", "onsite work",
    "regional preference", "location preference", "geographical preference"
]

# Default weightage configuration
DEFAULT_WEIGHTAGE = {
    "skill_matching": 0.5,
    "semantic_similarity": 0.3,
    "experience": 0.2,
    "education": 0.0,
    "projects": 0.0,
    "certifications": 0.0,
    "domain_match": 0.0,
    "location_preference": 0.0,
    "technical_skills_count": 0.0
}

DOMAIN_MAP = {
    "machine learning": "AI/ML",
    "deep learning": "AI/ML", 
    "nlp": "AI/ML",
    "data science": "AI/ML",
    "react": "Web Development",
    "node": "Web Development",
    "spring": "Backend",
    "docker": "DevOps",
    "kubernetes": "DevOps",
    "javascript": "Web Development",
    "frontend": "Web Development",
    "backend": "Web Development",
    "typescript": "Web Development",
    "html": "Web Development",
    "css": "Web Development",
    "aws": "Cloud Services",
    "azure": "Cloud Services", 
    "gcp": "Cloud Services",
    "cloud": "Cloud Services",
    "sql": "Data Engineering",
    "mysql": "Data Engineering",
    "mongodb": "Data Engineering",
    "postgresql": "Data Engineering",
    "database": "Data Engineering",
    "data warehouse": "Data Engineering",
    "etl": "Data Engineering",
    "python": "Programming",
    "java": "Programming",
    "c": "Programming",
    "c++": "Programming",
    "git": "DevOps",
    "jenkins": "DevOps",
    "ci/cd": "DevOps",
    "linux": "Systems",
    "ubuntu": "Systems",
    "windows": "Systems",
    "api": "Backend",
    "rest": "Backend",
    "graphql": "Backend",
    "microservices": "Architecture",
    "kafka": "Data Engineering",
    "redis": "Data Engineering",
    "elasticsearch": "Data Engineering",
    "security": "Security",
    "authentication": "Security",
    "authorization": "Security",
    "encryption": "Security",
    "testing": "Quality Assurance",
    "unit testing": "Quality Assurance",
    "integration testing": "Quality Assurance"
}

fallback_abbreviations = {
    "ml": "machine learning",
    "ai": "artificial intelligence", 
    "nlp": "natural language processing",
    "dl": "deep learning",
    "cv": "computer vision"
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_text(file_path):
    if file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        return extract_text_from_docx(file_path)
    else:
        return ""

def clean_text(text):
    text = text.lower()
    text = re.sub(r'(\d)\.(\d)', r'\1DOT\2', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = text.replace("DOT", ".")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fix_numbers(text):
    text = re.sub(r'\b([0-4])\s+([0-9]{2})\b', r'\1.\2', text)
    text = re.sub(r'\b([0-9])\s+00\b', r'\1.00', text)
    return text

def normalize_text(text):
    doc = nlp(text)
    expanded_text = text.lower()
    
    # Use fallback abbreviations since abbreviation detector might not be available
    for abbr, full in fallback_abbreviations.items():
        expanded_text = re.sub(r'\b' + re.escape(abbr) + r'\b', full, expanded_text)
    
    doc = nlp(expanded_text)
    tokens = []
    i = 0
    
    while i < len(doc):
        token = doc[i]
        if (i < len(doc) - 2 and doc[i].like_num and doc[i+1].text == "." and doc[i+2].like_num):
            tokens.append(doc[i].text + "." + doc[i+2].text)
            i += 3
            continue
        if not token.is_stop and not token.is_punct:
            tokens.append(token.lemma_)
        i += 1
    
    return " ".join(tokens)

def extract_comprehensive_skills(text):
    text_lower = text.lower()
    found_skills = []
    
    for skill in COMPREHENSIVE_SKILLS:
        skill_lower = skill.lower()
        if skill_lower in text_lower:
            found_skills.append(skill)
    
    return found_skills

def extract_technical_skills(text):
    text_lower = text.lower()
    found_skills = []
    
    for skill in COMPREHENSIVE_SKILLS:
        skill_lower = skill.lower()
        if skill_lower in text_lower:
            found_skills.append(skill)
    
    return found_skills

def identify_domain(text):
    domains = set()
    text_lower = text.lower()
    
    found_skills = extract_technical_skills(text)
    
    for skill in found_skills:
        skill_lower = skill.lower()
        if skill_lower in DOMAIN_MAP:
            domains.add(DOMAIN_MAP[skill_lower])
    
    if not domains:
        domains.add("General")
    
    return list(domains)

def extract_skills(text):
    technical_skills = extract_technical_skills(text)
    domains = identify_domain(text)
    all_skills = list(set(technical_skills + domains))
    return all_skills

def extract_projects(text):
    text_lower = text.lower()
    found_projects = []
    
    for keyword in PROJECT_KEYWORDS:
        if keyword in text_lower:
            found_projects.append(keyword)
    
    return found_projects

def extract_certifications(text):
    text_lower = text.lower()
    found_certifications = []
    
    for keyword in CERTIFICATION_KEYWORDS:
        if keyword in text_lower:
            found_certifications.append(keyword)
    
    return found_certifications

def extract_domain_match(jd_domains, resume_domains):
    jd_set = set(jd_domains)
    resume_set = set(resume_domains)
    
    if not jd_set or not resume_set:
        return 0.0
    
    intersection = jd_set.intersection(resume_set)
    union = jd_set.union(resume_set)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)

def extract_location_preference(text):
    text_lower = text.lower()
    found_preferences = []
    
    for keyword in LOCATION_KEYWORDS:
        if keyword in text_lower:
            found_preferences.append(keyword)
    
    return found_preferences

def extract_technical_skills_count(text):
    text_lower = text.lower()
    found_skills = []
    
    for skill in COMPREHENSIVE_SKILLS:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    
    return len(found_skills)

def extract_education(text):
    text_lower = text.lower()
    degrees = []
    fields = []
    
    for degree in DEGREE_KEYWORDS:
        if degree in text_lower:
            degrees.append(degree)
    
    for field in FIELD_KEYWORDS:
        if field in text_lower:
            fields.append(field)
    
    return degrees + fields

def get_experience_section(text):
    text = text.lower()
    start_idx = -1
    
    for key in START_KEYWORDS:
        idx = text.find(key)
        if idx != -1:
            start_idx = idx
            break
    
    if start_idx == -1:
        return ""
    
    end_idx = len(text)
    for key in END_KEYWORDS:
        idx = text.find(key, start_idx + 1)
        if idx != -1:
            end_idx = min(end_idx, idx)
    
    return text[start_idx:end_idx]

def extract_experience(text):
    exp_section = get_experience_section(text)
    if not exp_section:
        return 0
    
    year_patterns = [
        r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?experience',
        r'experience\s*:?\s*(\d+)',
        r'(\d+)\s*\+\s*years?',
        r'(\d{4})\s*-\s*(\d{4})',
        r'(\d{4})\s*to\s*present'
    ]
    
    for pattern in year_patterns:
        matches = re.findall(pattern, exp_section)
        if matches:
            if len(matches[0]) == 2:
                start_year, end_year = int(matches[0][0]), int(matches[0][1])
                return end_year - start_year
            else:
                return int(matches[0])
    
    return 0

def exact_skill_match(jd_skills, resume_skills):
    jd_set = set(jd_skills)
    resume_set = set(resume_skills)
    intersection = jd_set.intersection(resume_set)
    
    if len(jd_set) == 0:
        return 0
    
    return len(intersection) / len(jd_set)

def semantic_skill_match(jd_skills, resume_skills, model):
    if not jd_skills or not resume_skills:
        return 0
    
    jd_emb = model.encode(jd_skills)
    res_emb = model.encode(resume_skills)
    
    scores = []
    for j in jd_emb:
        sim = cosine_similarity([j], res_emb)[0]
        max_sim = np.max(sim)
        scores.append(max_sim)
    
    return np.mean(scores)

def skill_score(jd_skills, resume_skills, model):
    exact = exact_skill_match(jd_skills, resume_skills)
    semantic = semantic_skill_match(jd_skills, resume_skills, model)
    final_score = 0.6 * exact + 0.4 * semantic
    return round(final_score, 3)

def process_jd(file_path):
    global jd_text, JD_struct
    
    raw_text = extract_text(file_path)
    cleaned_text = clean_text(raw_text)
    cleaned_text = fix_numbers(cleaned_text)
    normalized_text = normalize_text(cleaned_text)
    
    jd_text = normalized_text
    
    JD_struct = {
        "skills": extract_skills(jd_text),
        "education": extract_education(jd_text),
        "experience": extract_experience(jd_text),
        "domain": identify_domain(jd_text),
        "projects": extract_projects(jd_text),
        "certifications": extract_certifications(jd_text),
        "location_preference": extract_location_preference(jd_text),
        "technical_skills_count": extract_technical_skills_count(jd_text)
    }
    
    return JD_struct

def process_resumes(resume_folder):
    global resume_text_list, Resume_struct
    
    resume_text_list = []
    Resume_struct = []
    
    for filename in os.listdir(resume_folder):
        file_path = os.path.join(resume_folder, filename)
        if not os.path.isfile(file_path):
            continue
        
        raw_text = extract_text(file_path)
        cleaned_text = clean_text(raw_text)
        cleaned_text = fix_numbers(cleaned_text)
        normalized_text = normalize_text(cleaned_text)
        
        resume_text_list.append(normalized_text)
        
        struct = {
            "filename": filename,
            "skills": extract_skills(normalized_text),
            "education": extract_education(normalized_text),
            "experience": extract_experience(normalized_text),
            "domain": identify_domain(normalized_text),
            "projects": extract_projects(normalized_text),
            "certifications": extract_certifications(normalized_text),
            "location_preference": extract_location_preference(normalized_text),
            "technical_skills_count": extract_technical_skills_count(normalized_text)
        }
        
        Resume_struct.append(struct)
    
    return Resume_struct

def calculate_scores():
    if not JD_struct or not Resume_struct:
        return []
    
    jd_skills = JD_struct["skills"]
    results = []
    
    for i, resume_struct in enumerate(Resume_struct):
        skill_matching_score = skill_score(jd_skills, resume_struct["skills"], model)
        
        jd_vector = model.encode(jd_text)
        resume_vector = model.encode(resume_text_list[i])
        semantic_similarity = cosine_similarity([jd_vector], [resume_vector])[0][0]
        
        experience_score = min(resume_struct["experience"] / 10.0, 1.0) if resume_struct["experience"] > 0 else 0.1
        
        final_score = (0.5 * skill_matching_score + 
                      0.3 * semantic_similarity + 
                      0.2 * experience_score)
        
        result = {
            "filename": resume_struct["filename"],
            "skill_matching_score": round(skill_matching_score, 3),
            "semantic_similarity": round(float(semantic_similarity), 3),
            "experience_score": round(experience_score, 3),
            "final_score": round(final_score, 3),
            "skills": resume_struct["skills"],
            "education": resume_struct["education"],
            "experience_years": resume_struct["experience"],
            "domain": resume_struct["domain"]
        }
        
        results.append(result)
    
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results

DEFAULT_WEIGHTAGE = {
    'skill_matching': 30,
    'semantic_similarity': 20,
    'experience': 20,
    'education': 10,
    'projects': 5,
    'certifications': 5,
    'domain_match': 5,
    'location_preference': 5,
    'technical_skills_count': 5
}

@app.route('/')
def index():
    return jsonify({"message": "Resume Shortlisting API", "version": "1.0"})

@app.route('/upload_jd', methods=['POST'])
def upload_jd():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        try:
            jd_struct = process_jd(file_path)
            return jsonify({
                "message": "JD uploaded and processed successfully",
                "jd_data": jd_struct
            })
        except Exception as e:
            return jsonify({"error": f"Error processing JD: {str(e)}"}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/upload_resumes', methods=['POST'])
def upload_resumes():
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files selected"}), 400
    
    # Clear existing resumes
    if os.path.exists(RESUME_FOLDER):
        shutil.rmtree(RESUME_FOLDER)
    os.makedirs(RESUME_FOLDER, exist_ok=True)
    
    uploaded_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(RESUME_FOLDER, filename)
            file.save(file_path)
            uploaded_files.append(filename)
    
    if not uploaded_files:
        return jsonify({"error": "No valid files uploaded"}), 400
    
    try:
        resume_structs = process_resumes(RESUME_FOLDER)
        return jsonify({
            "message": f"{len(uploaded_files)} resumes uploaded and processed successfully",
            "uploaded_files": uploaded_files,
            "resume_data": resume_structs
        })
    except Exception as e:
        return jsonify({"error": f"Error processing resumes: {str(e)}"}), 500

@app.route('/analyze_resumes', methods=['POST'])
def analyze_resumes():
    if not JD_struct:
        return jsonify({"error": "No JD uploaded. Please upload JD first"}), 400
    
    if not Resume_struct:
        return jsonify({"error": "No resumes uploaded. Please upload resumes first"}), 400
    
    try:
        results = calculate_scores()
        return jsonify({
            "message": "Resume analysis completed successfully",
            "jd_summary": {
                "total_jd_skills": len(JD_struct["skills"]),
                "jd_skills": JD_struct["skills"],
                "jd_domains": JD_struct["domain"]
            },
            "results": results,
            "total_resumes": len(results)
        })
    except Exception as e:
        return jsonify({"error": f"Error analyzing resumes: {str(e)}"}), 500

@app.route('/get_top_resumes', methods=['POST'])
def get_top_resumes():
    if not JD_struct:
        return jsonify({"error": "No JD uploaded. Please upload JD first"}), 400
    
    if not Resume_struct:
        return jsonify({"error": "No resumes uploaded. Please upload resumes first"}), 400
    
    data = request.get_json()
    top_n = data.get('top_n', 5) if data else 5
    
    try:
        results = calculate_scores()
        top_resumes = results[:top_n]
        
        return jsonify({
            "message": f"Top {top_n} resumes retrieved successfully",
            "top_resumes": top_resumes,
            "total_analyzed": len(results)
        })
    except Exception as e:
        return jsonify({"error": f"Error retrieving top resumes: {str(e)}"}), 500

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "jd_uploaded": bool(JD_struct),
        "resumes_uploaded": len(Resume_struct),
        "jd_skills_count": len(JD_struct.get("skills", [])) if JD_struct else 0,
        "resumes_count": len(Resume_struct)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
