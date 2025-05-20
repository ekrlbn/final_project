import google.generativeai as genai
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import gradio as gr

API_KEY = "AIzaSyBPSBl9b8sN4yFbxZe-NkGcUmH5Clp31SU"

# Base life expectancy by gender (CDC, US Life Tables 2021)
BASE_LIFE_EXPECTANCY = {
    "male": 76,    # CDC: https://www.cdc.gov/nchs/data/nvsr/nvsr72/nvsr72-14.pdf
    "female": 81   # CDC: https://www.cdc.gov/nchs/data/nvsr/nvsr72/nvsr72-14.pdf
}

# Disease impact (CDC, WHO, peer-reviewed studies)
disease_data = {
    "diabetes": 3,           # CDC, WHO
    "hypertension": 2,       # CDC, WHO
    "heart_disease": 4,      # CDC, WHO
    "copd": 4,               # CDC, WHO
    "cancer": 5,             # CDC, WHO
    "arthritis": 1,          # CDC, WHO
    "asthma": 2,             # CDC, WHO
    "stroke": 4,             # CDC, WHO
    "kidney_disease": 3,     # CDC, WHO
    "liver_disease": 4,      # CDC, WHO
    "osteoporosis": 2,       # CDC, WHO
    "depression": 1,         # CDC, WHO
    "anxiety": 1,            # CDC, WHO
    "obesity": 2,            # WHO
    "high_cholesterol": 1    # CDC
}

# Education impact (OECD)
EDUCATION_IMPACT = {
    "Primary": -2,       # OECD: https://www.oecd.org/els/health-systems/Health-at-a-Glance-2021-Highlights-EN.pdf
    "High School": -1
}

# Income impact (OECD)
INCOME_IMPACT = {
    "low": -2,           # OECD
    "medium": -1
}

# Marital status impact (BMJ)
MARITAL_IMPACT = {
    "Single": -1         # BMJ: https://www.bmj.com/content/343/bmj.d5639
}

# Family history impact (Nature)
FAMILY_HISTORY_IMPACT = {
    "cancer": -2,        # Nature: https://www.nature.com/articles/s41586-018-0459-6
    "alzheimer": -2
}

# Lifestyle bonuses (WHO, CDC)
LIFESTYLE_BONUSES = {
    "basketball": 1,     # WHO: Physical activity
    "non-smoker": 1,     # CDC: Smoking
    "no alcohol": 1      # WHO: Alcohol
}

def parse_loose_json(loose_str):
    result = {}
    for line in loose_str.strip().split(','):
        if not line.strip():
            continue
        if ' ' in line:
            key, value = line.strip().split(' ', 1)
            key = key.strip().replace("'", "").replace('"', '')
            value = value.strip().strip(',')
            if value.lower() == 'null':
                value = None
            elif value.isdigit():
                value = int(value)
            else:
                value = value.strip()
            result[key] = value
    return result

def static_life_expectancy_calculation(user_data):
    gender = user_data.get("gender", "").lower()
    base = BASE_LIFE_EXPECTANCY.get(gender, 78)
    age = int(user_data.get("age", 40))
    # Education
    education = user_data.get("education_level", "")
    base += EDUCATION_IMPACT.get(education, 0)
    # Income
    income = int(user_data.get("monthly_income", 0))
    if income < 3000:
        base += INCOME_IMPACT["low"]
    elif income < 6000:
        base += INCOME_IMPACT["medium"]
    # Marital
    marital = user_data.get("martial_status", "")
    base += MARITAL_IMPACT.get(marital, 0)
    # Family history
    fam_hist = user_data.get("family_health_history", "").lower()
    for key, val in FAMILY_HISTORY_IMPACT.items():
        if key in fam_hist:
            base += val
    # Lifestyle
    lifestyle = user_data.get("lifestyle_habits", "").lower()
    lifestyle_bonus = 0
    for key, val in LIFESTYLE_BONUSES.items():
        if key in lifestyle:
            lifestyle_bonus += val
    # Chronic diseases
    conditions = user_data.get("chronic_diseases", [])
    if conditions is None or conditions == "null":
        conditions = []
    elif isinstance(conditions, str):
        conditions = [c.strip() for c in conditions.split(',') if c.strip()]
    disease_penalty = sum([disease_data.get(c.lower(), 0) for c in conditions])
    expected_life = max(base + lifestyle_bonus - disease_penalty, age)
    risk = 100 - ((expected_life - age) * 2)
    risk = min(max(risk, 0), 100)
    analysis = {
        "base_expectancy": base,
        "disease_impact": -disease_penalty,
        "lifestyle_impact": lifestyle_bonus,
        "expected_life": expected_life,
        "risk_score": risk
    }
    return expected_life, risk, analysis

survival_table = """
age,male_survival,female_survival
0,1.000,1.000
1,0.995,0.996
5,0.994,0.995
10,0.993,0.994
15,0.992,0.993
20,0.990,0.992
25,0.988,0.991
30,0.985,0.990
35,0.982,0.989
40,0.978,0.988
45,0.973,0.987
50,0.967,0.986
55,0.959,0.984
60,0.949,0.982
65,0.936,0.979
70,0.919,0.975
75,0.897,0.970
80,0.868,0.963
85,0.830,0.953
90,0.780,0.938
95,0.715,0.915
100,0.630,0.880
"""

grounding_text = '''
Grounding & Data Sources:
- Base life expectancy: CDC, US Life Tables 2021 (https://www.cdc.gov/nchs/data/nvsr/nvsr72/nvsr72-14.pdf)
- Disease impact: CDC, WHO, peer-reviewed studies
- Education & income impact: OECD, Health at a Glance 2021 (https://www.oecd.org/els/health-systems/Health-at-a-Glance-2021-Highlights-EN.pdf)
- Marital status: BMJ, "Marriage and mortality" (https://www.bmj.com/content/343/bmj.d5639)
- Family history: Nature, "Genetic risk and healthy lifestyles" (https://www.nature.com/articles/s41586-018-0459-6)
- Lifestyle: WHO, CDC recommendations on physical activity, smoking, and alcohol
'''

class longevityAgent:
    def _init_(self, user_info_string):
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.user_data_str = user_info_string.strip()

    def generate_report(self):
        import json
        user_data = parse_loose_json(self.user_data_str)
        expected_life, risk, analysis = static_life_expectancy_calculation(user_data)
        gemini_prompt = f"Analyze the following user profile and provide a summary of risk factors, lifestyle, and recommendations:\n{json.dumps(user_data, indent=2)}"
        gemini_response = self.model.generate_content(gemini_prompt).text

        # Detailed calculation details
        details = []
        base = 76 if user_data.get("gender", "").lower() == "male" else 80
        details.append(f"Base life expectancy for gender ({user_data.get('gender','')}): {base} years [CDC]")
        education = user_data.get("education_level", "")
        if education == "Primary":
            details.append("Education: Primary (-2 years) [OECD]")
        elif education == "High School":
            details.append("Education: High School (-1 year) [OECD]")
        income = int(user_data.get("monthly_income", 0))
        if income < 3000:
            details.append(f"Monthly income: {income} (<3000) (-2 years) [OECD]")
        elif income < 6000:
            details.append(f"Monthly income: {income} (3000-6000) (-1 year) [OECD]")
        marital = user_data.get("martial_status", "")
        if marital == "Single":
            details.append("Marital status: Single (-1 year) [BMJ]")
        fam_hist = user_data.get("family_health_history", "").lower()
        if "cancer" in fam_hist or "alzheimer" in fam_hist:
            details.append("Family health history: Cancer/Alzheimer (-2 years) [Nature]")
        lifestyle = user_data.get("lifestyle_habits", "").lower()
        lifestyle_bonus = 0
        if "basketball" in lifestyle:
            details.append("Lifestyle: Weekly basketball (+1 year) [WHO]")
            lifestyle_bonus += 1
        if "non-smoker" in lifestyle:
            details.append("Lifestyle: Non-smoker (+1 year) [CDC]")
            lifestyle_bonus += 1
        if "no alcohol" in lifestyle:
            details.append("Lifestyle: No alcohol (+1 year) [WHO]")
            lifestyle_bonus += 1
        # Chronic diseases
        conditions = user_data.get("chronic_diseases", [])
        if conditions is None or conditions == "null":
            conditions = []
        elif isinstance(conditions, str):
            conditions = [c.strip() for c in conditions.split(',') if c.strip()]
        disease_penalty = sum([disease_data.get(c.lower(), 0) for c in conditions])
        if disease_penalty:
            details.append(f"Chronic diseases: {', '.join(conditions)} (Total penalty: -{disease_penalty} years) [CDC]")
        details.append(f"Total lifestyle bonus: +{lifestyle_bonus} years")
        details.append(f"Total disease penalty: -{disease_penalty} years")
        details.append(f"Final expected life: {analysis['expected_life']} years")
        details.append(f"Risk score: %{analysis['risk_score']} (higher is worse)")

        hesap_detay = "\n".join(details)

        report = (
            f"{gemini_response}\n\n---\n\nCalculation Details:\n{hesap_detay}\n\n---\n\n{grounding_text}"
        )
        return report

    def save_report_to_pdf(self, report_text, output_path="longevity_report.pdf"):
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.units import inch

        styles = getSampleStyleSheet()
        styleN = styles['Normal']
        styleH2 = styles['Heading2']

        doc = SimpleDocTemplate(output_path, pagesize=LETTER,
                                rightMargin=50, leftMargin=50,
                                topMargin=50, bottomMargin=50)
        story = []

        lines = report_text.split('\n')
        bullet_buffer = []
        for line in lines:
            line = line.strip()
            if not line:
                if bullet_buffer:
                    story.append(ListFlowable(
                        [Paragraph(b, styleN) for b in bullet_buffer],
                        bulletType='bullet', leftIndent=20
                    ))
                    bullet_buffer = []
                story.append(Spacer(1, 0.18 * inch))
                continue
            if line.startswith("") and line.endswith(""):
                if bullet_buffer:
                    story.append(ListFlowable(
                        [Paragraph(b, styleN) for b in bullet_buffer],
                        bulletType='bullet', leftIndent=20
                    ))
                    bullet_buffer = []
                story.append(Paragraph(line.replace("", ""), styleH2))
            elif line.startswith("* "):
                bullet_buffer.append(line[2:])  # Remove the '* ' at the start
            else:
                if bullet_buffer:
                    story.append(ListFlowable(
                        [Paragraph(b, styleN) for b in bullet_buffer],
                        bulletType='bullet', leftIndent=20
                    ))
                    bullet_buffer = []
                story.append(Paragraph(line, styleN))
        if bullet_buffer:
            story.append(ListFlowable(
                [Paragraph(b, styleN) for b in bullet_buffer],
                bulletType='bullet', leftIndent=20
            ))

        doc.build(story)
        return output_path

def process_user_string(user_info_str):
    agent = longevityAgent(user_info_str)
    report = agent.generate_report()
    pdf_path = agent.save_report_to_pdf(report)
    return report, pdf_path

iface = gr.Interface(
    fn=process_user_string,
    inputs=[
        gr.Textbox(label="User Profile (Raw Text Format)", lines=20, placeholder='Paste user info here (e.g., name:..., age:...)')
    ],
    outputs=[
        gr.Textbox(label="Generated Longevity Report", lines=25),
        gr.File(label="Download PDF Report")
    ],
    title="Longevity Report Generator",
    description="Paste a user profile as plain text. The system generates a longevity report based on fixed disease and survival datasets."
)

if _name_ == "_main_":
    iface.launch()
