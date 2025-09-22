# src/generate_cvs.py

import os
import json
import random
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from fpdf import FPDF
from dotenv import load_dotenv
from io import BytesIO

# --- New Imports for Image Generation ---
from openai import OpenAI
from PIL import Image

# --- Configuration ---
# Load environment variables from.env file
load_dotenv()

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in.env file.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in.env file.")

# Configure the OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Constants
NUM_CVS_TO_GENERATE = 1
OUTPUT_JSON_DIR = "data"
OUTPUT_IMAGE_DIR = "data"
OUTPUT_PDF_DIR = "cvs_generated"

# Define candidate personas to ensure variety in generated profiles
PERSONAS = ["Software Engineer", "Data Scientist", "Product Manager", "UX Designer", "Marketing Manager", "Sales Manager", "HR Manager", "Financial Analyst", "Project Manager", "IT Manager", "Graphic Designer", "Copywriter", "Social Media Manager", "Content Strategist", "Event Planner", "Veterinarian", "Architect", "Lawyer", "Accountant", "Chef", "Photographer", "Videographer", "Journalist", "Editor", "Writer", "Reporter", "Analyst", "Strategist", "Consultant", "Trainer", "Coach", "Mentor", "Advisor", "Investor", "Entrepreneur", "Freelancer", "Consultant", "Strategist", "Trainer", "Coach", "Mentor", "Advisor", "Investor", "Entrepreneur", "Freelancer", "Consultant", "Strategist", "Trainer", "Coach", "Mentor", "Advisor", "Investor", "Entrepreneur", "Freelancer"]

# --- LLM and Prompt Setup ---
llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    temperature=0.8,
)

prompt_template = """
Generate a realistic, synthetic professional profile for a candidate in the tech industry,
specifically for the role of: {persona}.

Provide the output in a clean JSON format. Do not include any explanatory text, code block markers, or anything outside of the single JSON object.

The JSON schema should be:
{{
  "full_name": "string",
  "job_title": "string",
  "contact": {{
    "email": "string (fake but realistic format)",
    "phone": "string (fake but realistic format)",
    "linkedin": "string (URL format, e.g., 'linkedin.com/in/username')"
  }},
  "summary": "string (A 2-4 sentence professional summary)",
  "work_experience": [
    {{
      "title": "string",
      "company": "string",
      "dates": "string (e.g., 'Jan 2020 - Present')",
      "description": ["string (bullet point 1)", "string (bullet point 2)", "string (bullet point 3)"]
    }},
    {{
      "title": "string",
      "company": "string",
      "dates": "string (e.g., 'Mar 2018 - Dec 2019')",
      "description": ["string (bullet point 1)", "string (bullet point 2)"]
    }}
  ],
  "education": [
    {{
      "degree": "string",
      "university": "string",
      "year": "string (e.g., '2014 - 2018')"
    }}
  ],
  "skills": {{
    "programming_languages": ["string"],
    "tools_and_technologies": ["string"],
    "soft_skills": ["string"]
  }}
}}
"""

prompt = ChatPromptTemplate.from_template(prompt_template)
output_parser = StrOutputParser()
chain = prompt | llm | output_parser

# --- Core Functions ---

def generate_profile(persona, index):
    """Generates a single candidate profile in JSON format using the LLM."""
    print(f"Generating profile {index+1}/{NUM_CVS_TO_GENERATE} for persona: {persona}...")
    response_str = "No response received from LLM." # Initialize for robust error handling
    try:
        raw_response = chain.invoke({"persona": persona})

        # Normalize to string in case we got an AIMessage
        response_str = (
            raw_response.content if hasattr(raw_response, "content") else str(raw_response)
        )

        cleaned_response = (
            response_str
            .strip()
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        # First parse attempt
        try:
            profile_data = json.loads(cleaned_response)
        except Exception:
            # Ask the LLM to repair to strict JSON (handles unescaped quotes, trailing commas, etc.)
            repair_prompt = (
                "Convert the following text into STRICT, valid JSON that matches the schema provided earlier. "
                "Fix any issues such as unescaped quotes inside strings and remove any Markdown fences. "
                "Only output the JSON object and nothing else.\n\n" + cleaned_response
            )
            repaired_raw = llm.invoke(repair_prompt)
            repaired_text = (
                repaired_raw.content if hasattr(repaired_raw, "content") else str(repaired_raw)
            )
            repaired_clean = (
                repaired_text
                .strip()
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )
            profile_data = json.loads(repaired_clean)

        print(f"Profile data: {profile_data}")
        
        file_path = os.path.join(OUTPUT_JSON_DIR, f"candidate_{index:02d}.json")
        with open(file_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        print(f"  -> Successfully saved profile to {file_path}")
        return profile_data
    except Exception as e:
        print(f"  -> Error generating or parsing profile {index}: {e}")
        print("     LLM Response was:\n", response_str)
        return None

def generate_headshot(profile_data, index):
    """Generates a headshot using the OpenAI Images API and saves it."""
    print(f"Generating headshot for candidate {index+1}...")
    try:
        prompt = (
            f"Photorealistic professional headshot of a {profile_data.get('job_title', 'person')}. "
            "Professional attire, neutral studio background, high-resolution, 4k."
        )

        # OpenAI Images API (v1): use 'gpt-image-1' for image generation
        img = openai_client.images.generate(
            model='gpt-image-1',
            prompt=prompt,
            size='1024x1024',
            quality='high',
            n=1,
        )

        if not img.data:
            raise ValueError('No image data returned by OpenAI Images API.')

        # Support both base64 and URL responses depending on SDK version
        image_bytes = None
        import base64, requests
        if getattr(img.data[0], 'b64_json', None):
            image_bytes = base64.b64decode(img.data[0].b64_json)
        elif getattr(img.data[0], 'url', None):
            r = requests.get(img.data[0].url, timeout=30)
            r.raise_for_status()
            image_bytes = r.content
        else:
            raise ValueError('OpenAI Images API returned neither b64_json nor url.')
        image = Image.open(BytesIO(image_bytes))

        file_path = os.path.join(OUTPUT_IMAGE_DIR, f"candidate_{index:02d}.png")
        image.save(file_path, format='PNG')
        print(f"  -> Successfully saved headshot to {file_path}")
        return True
    except Exception as e:
        print(f"  -> Error generating headshot for candidate {index}: {e}")
        return False

def create_cv_pdf(profile_data, index):
    """Assembles a PDF CV from the profile data and a corresponding image."""
    image_path = os.path.join(OUTPUT_IMAGE_DIR, f"candidate_{index:02d}.png")
    if not os.path.exists(image_path):
        print(f"Warning: Image not found for candidate {index}. Skipping PDF generation.")
        return

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    SIDEBAR_WIDTH, MAIN_CONTENT_WIDTH, MARGIN = 60, 130, 10
    
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(0, 0, SIDEBAR_WIDTH, 297, 'F')
    
    pdf.image(image_path, x=MARGIN, y=MARGIN, w=SIDEBAR_WIDTH - 2 * MARGIN)
    
    # Sidebar content (contact + skills)
    pdf.set_xy(MARGIN, MARGIN + (SIDEBAR_WIDTH - 2 * MARGIN) + 10)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "Contact", ln=True)
    pdf.set_font("Arial", "", 8)
    pdf.multi_cell(SIDEBAR_WIDTH - 2 * MARGIN, 5, f"Email: {profile_data['contact']['email']}")
    pdf.set_x(MARGIN)
    pdf.multi_cell(SIDEBAR_WIDTH - 2 * MARGIN, 5, f"Phone: {profile_data['contact']['phone']}")
    pdf.set_x(MARGIN)
    pdf.multi_cell(SIDEBAR_WIDTH - 2 * MARGIN, 5, f"LinkedIn: {profile_data['contact']['linkedin']}")
    
    pdf.set_xy(MARGIN, pdf.get_y() + 10)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "Skills", ln=True)
    
    for skill_type, skills in profile_data['skills'].items():
        pdf.set_font("Arial", "B", 8)
        pdf.set_x(MARGIN)
        pdf.cell(0, 5, skill_type.replace('_', ' ').title() + ":", ln=True)
        pdf.set_font("Arial", "", 8)
        for skill in skills:
            pdf.set_x(MARGIN + 2)
            pdf.cell(0, 5, f"- {skill}", ln=True)

    # Switch to main content column on the right
    pdf.set_left_margin(SIDEBAR_WIDTH + MARGIN)
    pdf.set_right_margin(MARGIN)
    pdf.set_xy(SIDEBAR_WIDTH + MARGIN, MARGIN)
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 10, profile_data['full_name'], ln=True)
    pdf.set_font("Arial", "I", 14)
    pdf.cell(0, 8, profile_data['job_title'], ln=True)
    
    pdf.set_y(pdf.get_y() + 5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Professional Summary", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(MAIN_CONTENT_WIDTH, 5, profile_data['summary'])
    pdf.set_x(SIDEBAR_WIDTH + MARGIN)
    
    pdf.set_y(pdf.get_y() + 5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Work Experience", ln=True)
    for job in profile_data['work_experience']:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, f"{job['title']} | {job['company']}", ln=True)
        pdf.set_font("Arial", "I", 9)
        pdf.cell(0, 5, job['dates'], ln=True)
        pdf.set_font("Arial", "", 10)
        for desc_point in job['description']:
            pdf.multi_cell(MAIN_CONTENT_WIDTH, 5, f"- {desc_point}")
            pdf.set_x(SIDEBAR_WIDTH + MARGIN)
        pdf.ln(3)
        pdf.set_x(SIDEBAR_WIDTH + MARGIN)

    pdf.set_y(pdf.get_y() + 5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Education", ln=True)
    for edu in profile_data['education']:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, f"{edu['degree']}", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, f"{edu['university']} ({edu['year']})", ln=True)
        
    pdf_file_name = f"{profile_data['full_name'].replace(' ', '_')}_CV.pdf"
    pdf_path = os.path.join(OUTPUT_PDF_DIR, pdf_file_name)
    pdf.output(pdf_path)
    print(f"  -> Successfully created PDF: {pdf_path}")

# --- Main Execution ---
if __name__ == "__main__":
    os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)
    os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)

    print("--- Starting Fully Automated CV Generation Process ---")
    
    # Pre-scan existing artifacts
    existing_json = sorted([f for f in os.listdir(OUTPUT_JSON_DIR) if f.startswith("candidate_") and f.endswith(".json")])
    existing_images = sorted([f for f in os.listdir(OUTPUT_IMAGE_DIR) if f.startswith("candidate_") and f.endswith((".png", ".jpg", ".jpeg"))])
    existing_pdfs = sorted([f for f in os.listdir(OUTPUT_PDF_DIR) if f.lower().endswith(".pdf")])

    for i in range(NUM_CVS_TO_GENERATE):
        persona = random.choice(PERSONAS)

        # Decide filenames for this index
        json_path = os.path.join(OUTPUT_JSON_DIR, f"candidate_{i:02d}.json")
        img_path = os.path.join(OUTPUT_IMAGE_DIR, f"candidate_{i:02d}.png")

        # 1) Generate profile only if needed
        profile = None
        if len(existing_json) >= NUM_CVS_TO_GENERATE or os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    profile = json.load(f)
                print(f"Skipping profile generation for candidate {i+1}: JSON already exists.")
            except Exception:
                profile = None
        else:
            profile = generate_profile(persona, i)

        # 2) Generate headshot only if profile is available and needed
        if profile:
            if len(existing_images) >= NUM_CVS_TO_GENERATE or os.path.exists(img_path):
                print(f"Skipping headshot generation for candidate {i+1}: image already exists.")
                headshot_generated = True
            else:
                headshot_generated = generate_headshot(profile, i)

            # 3) Create PDF only if needed and headshot exists
            if headshot_generated:
                if len(existing_pdfs) >= NUM_CVS_TO_GENERATE:
                    print(f"Skipping PDF creation for candidate {i+1}: enough PDFs already exist.")
                else:
                    create_cv_pdf(profile, i)
            else:
                print(f"Skipping PDF creation for profile {i+1} due to headshot generation failure.")
            
    print("\n--- CV Generation Process Finished ---")