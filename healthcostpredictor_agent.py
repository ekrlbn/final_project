import gradio as gr
from gradio.interface import Interface
from gradio.components import Number, Dropdown, Textbox, Slider, Checkbox, File, JSON
import pandas as pd
import json
import os
from typing import List, Dict, Any, Optional, Union
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from google import genai
import time
from google.api_core import retry
import re

# Initialize Gemini with API key
api_key = "AIzaSyDLV_MD6HshxX15UnnLZ0V9YqhwrH2NN-0"  # Replace this with your actual API key
client = genai.Client(api_key=api_key)

def load_costs():
    """Load health costs by region and age group"""
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Default costs if file doesn't exist
    default_costs = [
        {'region': 'USA', 'age_group': '30-39', 'base_cost': 2000},
        {'region': 'USA', 'age_group': '40-49', 'base_cost': 3000},
        {'region': 'USA', 'age_group': '50-59', 'base_cost': 4000},
        {'region': 'USA', 'age_group': '60+', 'base_cost': 6000},
        {'region': 'Europe', 'age_group': '30-39', 'base_cost': 1500},
        {'region': 'Europe', 'age_group': '40-49', 'base_cost': 2250},
        {'region': 'Europe', 'age_group': '50-59', 'base_cost': 3000},
        {'region': 'Europe', 'age_group': '60+', 'base_cost': 4500},
        {'region': 'Asia', 'age_group': '30-39', 'base_cost': 1000},
        {'region': 'Asia', 'age_group': '40-49', 'base_cost': 1500},
        {'region': 'Asia', 'age_group': '50-59', 'base_cost': 2000},
        {'region': 'Asia', 'age_group': '60+', 'base_cost': 3000},
        {'region': 'Turkey', 'age_group': '30-39', 'base_cost': 800},
        {'region': 'Turkey', 'age_group': '40-49', 'base_cost': 1200},
        {'region': 'Turkey', 'age_group': '50-59', 'base_cost': 1600},
        {'region': 'Turkey', 'age_group': '60+', 'base_cost': 2400}
    ]
    
    # Try to load existing file, if not exists create with default data
    try:
        costs_df = pd.read_csv('data/health_costs_by_region.csv')
        if costs_df.empty:
            costs_df = pd.DataFrame(default_costs)
            costs_df.to_csv('data/health_costs_by_region.csv', index=False)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        costs_df = pd.DataFrame(default_costs)
        costs_df.to_csv('data/health_costs_by_region.csv', index=False)
    
    return costs_df

def load_weights():
    """Load chronic condition risk weights"""
    # Default weights if file doesn't exist
    default_weights = {
        "diabetes": 0.96,
        "hypertension": 0.72,
        "heart_disease": 1.20,
        "asthma": 0.33,
        "cancer": 1.44,
        "copd": 0.96,
        "depression": 0.48,
        "obesity": 0.72,
        "alzheimer": 1.20,
        "bone_cancer": 1.44
    }
    
    # Try to load existing file, if not exists create with default data
    try:
        with open('data/chronic_condition_weights.json', 'r') as f:
            weights = json.load(f)
            if not weights:
                weights = default_weights
                with open('data/chronic_condition_weights.json', 'w') as f:
                    json.dump(weights, f, indent=4)
    except (FileNotFoundError, json.JSONDecodeError):
        weights = default_weights
        with open('data/chronic_condition_weights.json', 'w') as f:
            json.dump(weights, f, indent=4)
    
    return weights

class HealthCostPredictorAgent:
    def __init__(self, 
                 cost_data: pd.DataFrame, 
                 weights: Dict[str, float],
                 chronic_condition_sources: Optional[Dict[str, str]] = None,
                 family_history_risk: Optional[Dict[str, float]] = None,
                 lifestyle_source: Optional[str] = None,
                 insurance_source: Optional[str] = None,
                 insurance_discount_rate: float = 0.3):
        """
        Initialize the HealthCostPredictorAgent.
        
        Args:
            cost_data (pd.DataFrame): DataFrame containing base costs by region and age group
            weights (Dict[str, float]): Dictionary of chronic condition risk weights
            chronic_condition_sources (Dict[str, str], optional): Dictionary mapping conditions to their data sources
            family_history_risk (Dict[str, float], optional): Dictionary of family history risk factors
            lifestyle_source (str, optional): Source URL for lifestyle data
            insurance_source (str, optional): Source URL for insurance data
            insurance_discount_rate (float, optional): Insurance discount rate (default: 0.3 for 30%)
        """
        self.cost_data = cost_data
        
        # Define default data sources if not provided
        self.chronic_condition_sources = chronic_condition_sources or {
            "diabetes": "https://www.cdc.gov/diabetes/data/statistics-report/index.html",
            "hypertension": "https://www.heart.org/en/health-topics/high-blood-pressure",
            "heart_disease": "https://www.heart.org/en/health-topics/consumer-healthcare/what-is-cardiovascular-disease",
            "asthma": "https://www.lung.org/lung-health-diseases/lung-disease-lookup/asthma",
            "cancer": "https://www.cancer.org/cancer/cancer-basics/cancer-facts-and-figures.html",
            "copd": "https://www.lung.org/lung-health-diseases/lung-disease-lookup/copd",
            "depression": "https://www.nimh.nih.gov/health/statistics/major-depression",
            "obesity": "https://www.cdc.gov/obesity/data/index.html",
            "alzheimer": "https://www.alz.org/alzheimers-dementia/facts-figures",
            "bone_cancer": "https://www.cancer.org/cancer/bone-cancer.html"
        }
        
        self.family_history_risk = family_history_risk or {
            "cancer": 0.15,
            "heart_disease": 0.20,
            "diabetes": 0.15,
            "alzheimer": 0.15,
            "bone_cancer": 0.15
        }
        
        self.lifestyle_source = lifestyle_source or "https://www.who.int/data/gho/data/themes/topics/health-behaviours"
        self.insurance_source = insurance_source or "https://www.oecd.org/health/health-data.htm"
        self.insurance_discount_rate = insurance_discount_rate
        
        # Initialize weights with source information
        self.weights = {}
        for condition, weight in weights.items():
            if condition in self.chronic_condition_sources:
                self.weights[condition] = {
                    'value': float(weight),
                    'source': self.chronic_condition_sources[condition]
                }
            else:
                self.weights[condition] = {
                    'value': float(weight),
                    'source': 'General medical research data'
                }

    def _get_age_group(self, age: int) -> str:
        """Convert age to age group category."""
        if age < 40:
            return "30-39"
        elif age < 50:
            return "40-49"
        elif age < 60:
            return "50-59"
        else:
            return "60+"

    def _calculate_lifestyle_score(self, lifestyle_habits: str) -> int:
        """Calculate lifestyle score based on habits."""
        score = 0
        habits = lifestyle_habits.lower()
        
        # Exercise
        if "weekly" in habits and any(sport in habits for sport in ["basketball", "football", "tennis", "swimming", "running"]):
            score += 3
        elif "monthly" in habits and any(sport in habits for sport in ["basketball", "football", "tennis", "swimming", "running"]):
            score += 2
        elif "occasionally" in habits and any(sport in habits for sport in ["basketball", "football", "tennis", "swimming", "running"]):
            score += 1
            
        # Smoking and alcohol
        if "non-smoker" in habits:
            score += 2
        if "no alcohol" in habits:
            score += 2
            
        # Diet (assuming healthy if not specified)
        if "healthy diet" in habits or "balanced diet" in habits:
            score += 3
        else:
            score += 1  # Default score for unspecified diet
            
        return min(score, 10)

    def predict(self, input_data: Dict[str, Any]) -> dict:
        """
        Predict health costs based on input JSON data.
        """
        # Extract relevant data from input
        age = input_data.get('age', 0)
        region = input_data.get('location', 'USA')
        chronic_conditions = input_data.get('chronic_diseases', [])
        # Fix: if chronic_conditions is a string, handle properly
        if isinstance(chronic_conditions, str):
            if ',' in chronic_conditions:
                chronic_conditions = [c.strip() for c in chronic_conditions.split(',') if c.strip()]
            elif chronic_conditions.strip():
                chronic_conditions = [chronic_conditions.strip()]
            else:
                chronic_conditions = []
        elif not chronic_conditions:
            chronic_conditions = []
        # Only process valid, non-empty condition names
        chronic_conditions = [c for c in chronic_conditions if c and isinstance(c, str)]
        family_history = input_data.get('family_health_history', '').split(',')
        lifestyle_habits = input_data.get('lifestyle_habits', '')
        monthly_income = input_data.get('monthly_income', 0)
        
        # Calculate lifestyle score
        lifestyle_score = self._calculate_lifestyle_score(lifestyle_habits)
        
        # Determine insurance status based on income
        insurance_status = monthly_income >= 2000  # Assuming $2000 monthly income threshold for insurance
        
        # Get base cost for region and age group
        age_group = self._get_age_group(age)
        try:
            # Use proper pandas type hints
            cost_data: pd.DataFrame = self.cost_data
            filtered_data = cost_data.loc[(cost_data['region'] == region) & 
                                         (cost_data['age_group'] == age_group)]
            if not filtered_data.empty:
                base_cost = float(filtered_data['base_cost'].iloc[0])
            else:
                base_cost = float(cost_data['base_cost'].mean())
        except (IndexError, KeyError):
            base_cost = float(self.cost_data['base_cost'].mean())

        details = []
        details.append({
            'step': 'Base Cost',
            'desc': f'Region: {region}, Age Group: {age_group}',
            'value': base_cost,
            'source': self.insurance_source
        })

        # Calculate risk factors
        risk = 0.0
        chronic_risk = 0.0
        chronic_breakdown = []
        for condition in chronic_conditions:
            cond_info = self.weights.get(condition.lower(), {'value': 0.0, 'source': 'Data not available'})
            cond_risk = cond_info['value']
            chronic_risk += cond_risk
            chronic_breakdown.append((condition, cond_risk, cond_info['source']))
        if chronic_breakdown:
            details.append({
                'step': 'Chronic Conditions',
                'desc': ', '.join([f"{c}: +{r:.2f} (Source: {s})" for c, r, s in chronic_breakdown]),
                'value': chronic_risk,
                'source': '; '.join([s for _, _, s in chronic_breakdown])
            })
        risk += chronic_risk

        family_risk = 0.0
        family_breakdown = []
        for condition in family_history:
            condition = condition.strip().lower()
            if condition in self.family_history_risk:
                fam_risk = self.family_history_risk[condition]
                family_risk += fam_risk
                family_breakdown.append((condition, fam_risk, self.chronic_condition_sources.get(condition, 'General medical research data')))
        if family_breakdown:
            details.append({
                'step': 'Family History',
                'desc': ', '.join([f"{c}: +{r:.2f} (Source: {s})" for c, r, s in family_breakdown]),
                'value': family_risk,
                'source': '; '.join([s for _, _, s in family_breakdown])
            })
        risk += family_risk

        lifestyle_risk = (10 - lifestyle_score) * 0.03
        details.append({
            'step': 'Lifestyle Score',
            'desc': f'Score: {lifestyle_score}/10 -> Risk: +{lifestyle_risk:.2f}',
            'value': lifestyle_risk,
            'source': self.lifestyle_source
        })
        risk += lifestyle_risk

        details.append({
            'step': 'Total Risk Factor',
            'desc': 'Sum of all risk factors (Chronic Conditions + Family History + Lifestyle)',
            'value': risk,
            'source': 'Internal Model Calculation'
        })

        predicted_cost = base_cost * (1 + risk)
        details.append({
            'step': 'Cost Before Insurance',
            'desc': f'Base Cost (${base_cost:,.2f}) x (1 + Total Risk {risk:.2f})',
            'value': predicted_cost,
            'source': 'Internal Model Calculation'
        })

        if insurance_status:
            discount_amount = predicted_cost * self.insurance_discount_rate
            final_cost = predicted_cost - discount_amount
            details.append({
                'step': 'Insurance Discount',
                'desc': f'Applied {self.insurance_discount_rate*100:.0f}% discount for insurance',
                'value': discount_amount,
                'source': self.insurance_source
            })
            details.append({
                'step': 'Final Cost After Insurance',
                'desc': 'Cost after insurance discount applied',
                'value': final_cost,
                'source': self.insurance_source
            })
        else:
            final_cost = predicted_cost
            details.append({
                'step': 'Insurance Discount',
                'desc': 'No insurance discount applied',
                'value': 0.0,
                'source': self.insurance_source
            })
            details.append({
                'step': 'Final Cost After Insurance',
                'desc': 'Cost after insurance discount applied',
                'value': final_cost,
                'source': self.insurance_source
            })

        return {
            'final_cost': round(final_cost, 2),
            'details': details,
            'lifestyle_score': lifestyle_score,
            'insurance_status': insurance_status
        }

def generate_health_cost_report(age: int,
                              gender: str,
                              height: float,
                              weight: float,
                              region: str,
                              chronic_conditions: list,
                              family_history: list,
                              lifestyle_score: int,
                              insurance_status: bool,
                              smoke: bool,
                              alcohol: bool,
                              predicted_cost: float,
                              calculation_details: Optional[list] = None,
                              recommendations: Optional[list] = None,
                              output_dir: str = "reports") -> str:
    """
    Generate a PDF report for health cost prediction.
    """
    if calculation_details is None:
        calculation_details = []
    if recommendations is None:
        recommendations = []
    
    # Create reports directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"health_cost_prediction_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # Create the PDF document
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12
    )
    
    source_style = ParagraphStyle(
        'SourceStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        spaceBefore=2,
        spaceAfter=6
    )
    
    # Build the content
    content = []
    
    # Title
    content.append(Paragraph("Health Cost Prediction Report", title_style))
    content.append(Spacer(1, 20))
    
    # Personal Information (height and weight removed)
    content.append(Paragraph("Personal Information", heading_style))
    personal_data = [
        ["Age:", str(age)],
        ["Gender:", gender],
        ["Region:", region],
        ["Lifestyle Score:", f"{lifestyle_score}/10"],
        ["Insurance Status:", "Yes" if insurance_status else "No"],
        ["Smoking:", "Yes" if smoke else "No"],
        ["Alcohol Consumption:", "Yes" if alcohol else "No"]
    ]
    personal_table = Table(personal_data, colWidths=[2*inch, 4*inch])
    personal_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    content.append(personal_table)
    content.append(Spacer(1, 20))
    
    # Health Information
    content.append(Paragraph("Health Information", heading_style))
    health_data = [
        ["Chronic Conditions:", ", ".join(chronic_conditions) if chronic_conditions else "None"],
        ["Family History:", ", ".join(family_history) if family_history else "None"]
    ]
    health_table = Table(health_data, colWidths=[2*inch, 4*inch])
    health_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    content.append(health_table)
    content.append(Spacer(1, 20))
    
    # Prediction Results
    content.append(Paragraph("Prediction Results", heading_style))
    prediction_data = [
        ["Predicted Annual Health Cost:", f"${predicted_cost:,.2f}"]
    ]
    prediction_table = Table(prediction_data, colWidths=[2*inch, 4*inch])
    prediction_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.red),
        ('FONTSIZE', (1, 0), (1, 0), 14),
    ]))
    content.append(prediction_table)
    content.append(Spacer(1, 20))
    
    # Detailed Calculation Steps (with formulas and values)
    if calculation_details:
        content.append(Paragraph("How Was This Cost Calculated?", heading_style))
        calc_data = [
            [
                Paragraph("Step", styles["Normal"]),
                Paragraph("Description", styles["Normal"]),
                Paragraph("Value", styles["Normal"]),
                Paragraph("Source", source_style)
            ]
        ]
        for d in calculation_details:
            step_para = Paragraph(str(d.get('step', '')), styles["Normal"])
            desc_para = Paragraph(str(d.get('desc', '')), styles["Normal"])
            value_para = Paragraph(f"{d.get('value', 0):,.2f}", styles["Normal"])
            source_para = Paragraph(d.get('source', ''), source_style)
            calc_data.append([
                step_para,
                desc_para,
                value_para,
                source_para
            ])
        calc_table = Table(calc_data, colWidths=[0.9*inch, 2.0*inch, 0.9*inch, 4.0*inch], repeatRows=1)
        calc_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, 0), colors.lightblue),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),  # header
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # body
            ('TEXTCOLOR', (3, 1), (3, -1), colors.gray),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        content.append(calc_table)
        content.append(Spacer(1, 20))
        # Add a summary formula explanation
        content.append(Paragraph(
            "<b>Calculation Formula:</b> <br/>"
            "<i>Final Cost = Base Cost × (1 + Total Risk Factor) × (1 - Insurance Discount [if applicable])</i><br/>"
            "<b>Where:</b><br/>"
            "- <b>Base Cost</b>: Determined by region and age group.<br/>"
            "- <b>Total Risk Factor</b>: Sum of chronic conditions, family history, and lifestyle risk.<br/>"
            "- <b>Insurance Discount</b>: Applied if insurance is present.<br/>"
            , styles["Normal"]))
        content.append(Spacer(1, 10))
    
    # Recommendations Section
    if recommendations:
        content.append(Paragraph("Recommendations", heading_style))
        for rec in recommendations:
            content.append(Paragraph(f"• {rec}", styles["Normal"]))
            # Split recommendation and source
            if "Source:" in rec:
                rec_text, source = rec.split("Source:")
                content.append(Paragraph(rec_text, styles["Normal"]))
                content.append(Paragraph(f"Source: {source}", source_style))
            else:
                content.append(Paragraph(rec, styles["Normal"]))
        content.append(Spacer(1, 16))
    
    # Disclaimer
    content.append(Paragraph("Disclaimer", heading_style))
    disclaimer = Paragraph(
        "This report is generated using AI-powered analysis and should be reviewed by a qualified financial advisor. All calculations are "
        "based on provided data and industry-standard actuarial tables. Past performance is not indicative of future results.",
        styles["Normal"]
    )
    content.append(disclaimer)
    
    # Add data sources section
    content.append(Spacer(1, 20))
    content.append(Paragraph("Data Sources", heading_style))
    sources = [
        "• World Health Organization (WHO) - Healthcare cost statistics and lifestyle impact data",
        "• Centers for Disease Control and Prevention (CDC) - Chronic condition costs and risk factors",
        "• Organization for Economic Co-operation and Development (OECD) - Regional healthcare costs and insurance data",
        "• American Heart Association - Cardiovascular disease costs and risk factors",
        "• American Cancer Society - Cancer screening and treatment costs",
        "• American Lung Association - Respiratory condition costs",
        "• National Institute of Mental Health - Mental health condition costs",
        "• Arthritis Foundation - Arthritis treatment costs",
        "• National Kidney Foundation - Kidney disease costs",
        "• American Diabetes Association - Diabetes management costs"
    ]
    for source in sources:
        content.append(Paragraph(source, source_style))
    
    # Build the PDF
    doc.build(content)
    
    return filepath

def generate_recommendations(input_data: Dict[str, Any], calculation_details: List[Dict[str, Any]]) -> List[str]:
    """
    Generate personalized health and financial recommendations using Gemini,
    with accurate numerical references and no repetition.
    """
    
    prompt = f"""
You are a highly knowledgeable health and financial advisor.
Your task is to generate 15 **unique**, **user-specific**, and **data-driven** recommendations based on the following detailed user profile and risk assessment.
Each recommendation should:

- Refer **directly** to at least one user-specific input (e.g., "with 20000 USD debt", "based on your 1/10 lifestyle score", etc.)
- Be written as a **single, complete sentence**
- Include **exact numbers** from the input (e.g., "debt: 20000 USD", "monthly income: 4500 USD")
- Be **actionable**, **evidence-based**, and where applicable cite a source (e.g., WHO, CDC, NIH) in parentheses
- Avoid all forms of repetition or vague suggestions

Use the data below **as-is**. Do not round or interpret numbers. Use the original format (e.g., 20000 USD instead of "$20k" or "$20").

PATIENT PROFILE
- Name: {input_data.get('name_surname', 'N/A')}
- Age: {input_data.get('age', 'N/A')} years
- Gender: {input_data.get('gender', 'N/A')}
- Marital Status: {input_data.get('martial_status', 'N/A')}
- Education: {input_data.get('education_level', 'N/A')}
- Occupation: {input_data.get('occupation', 'N/A')}
- Location: {input_data.get('location', 'N/A')}
- Monthly Income: {input_data.get('monthly_income', 'N/A')} USD
- Monthly Expenses: {input_data.get('monthly_expenses', 'N/A')} USD
- Debt: {input_data.get('debt', 'N/A')} USD
- Assets: {input_data.get('assets', 'N/A')}

HEALTH PROFILE
- Chronic Conditions: {', '.join(input_data.get('chronic_diseases', []) or ['None reported'])}
- Family Medical History: {input_data.get('family_health_history', 'None reported')}
- Lifestyle Habits: {input_data.get('lifestyle_habits', 'N/A')}
- Lifestyle Score: {input_data.get('lifestyle_score', 'N/A')}/10

RETIREMENT GOALS
- Target Retirement Age: {input_data.get('target_retirement_age', 'N/A')}
- Target Retirement Income: {input_data.get('target_retirement_income', 'N/A')} USD/month

RISK CALCULATION SUMMARY
{chr(10).join([f"- {detail['step']}: {detail['desc']}" for detail in calculation_details])}

Please return exactly 15 recommendations in a numbered list (1–15), each on a new line, and strictly follow the above rules.
"""
    response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config={
                'temperature': 0.4,  # Lower temp = more deterministic & fact-based
                'top_p': 0.9,
                'top_k': 40
            }
        )
    text = getattr(response, 'text', None)
    if not text:
        return ["Unable to generate recommendations at this time. Please consult with your healthcare provider."]
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    seen = set()
    unique_recommendations = []
    for line in lines:
        # Remove leading bullets, numbers, and whitespace
        clean = re.sub(r'^[•\-\d\.\s]+', '', line).strip()
        # Remove citation (parentheses and after)
        rec_main = re.split(r'\s*\([^)]*\)\s*$', clean)[0]
        # Normalize: lowercase, remove extra spaces, remove trailing dot
        norm = re.sub(r'\s+', ' ', rec_main).lower().rstrip('.')
        if norm and norm not in seen:
            unique_recommendations.append(clean)
            seen.add(norm)
        if len(unique_recommendations) == 15:
            break
    return unique_recommendations

def parse_custom_format(input_text: str) -> dict:
    """
    Parse the custom format into a proper JSON dictionary.
    Format:
    {
    key value,
    key value,
    ...
    }
    """
    try:
        # Remove curly braces and split by commas
        content = input_text.strip('{}').strip()
        lines = [line.strip() for line in content.split(',') if line.strip()]
        
        result = {}
        for line in lines:
            # Split by first space to separate key and value
            parts = line.split(' ', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                
                # Convert value to appropriate type
                if value.lower() == 'null':
                    value = None
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit():
                    value = float(value)
                elif value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                
                result[key] = value
        
        return result
    except Exception as e:
        raise ValueError(f"Error parsing input format: {str(e)}")

def predict_health_cost(input_text: str) -> tuple[str, str | None]:
    """
    Predict health costs based on input and generate PDF report.
    """
    try:
        # Parse input text using custom parser
        input_data = parse_custom_format(input_text)
        
        # Initialize the predictor agent
        agent = HealthCostPredictorAgent(load_costs(), load_weights())
        
        # Get prediction with details
        result = agent.predict(input_data)
        final_cost = result['final_cost']
        details = result['details']
        lifestyle_score = result['lifestyle_score']
        insurance_status = result['insurance_status']
        
        # Add lifestyle score to input data for recommendations
        input_data['lifestyle_score'] = lifestyle_score
        
        # Generate recommendations
        recommendations = generate_recommendations(input_data, details)
        
        # Generate PDF report
        pdf_path = generate_health_cost_report(
            age=input_data.get('age', 0),
            gender=input_data.get('gender', ''),
            height=0,  # Not provided in new format
            weight=0,  # Not provided in new format
            region=input_data.get('location', ''),
            chronic_conditions=input_data.get('chronic_diseases', []) or [],
            family_history=input_data.get('family_health_history', '').split(','),
            lifestyle_score=lifestyle_score,
            insurance_status=insurance_status,
            smoke='smoker' not in input_data.get('lifestyle_habits', '').lower(),
            alcohol='no alcohol' in input_data.get('lifestyle_habits', '').lower(),
            predicted_cost=final_cost,
            calculation_details=details,
            recommendations=recommendations
        )
        
        # Format output with details and recommendations
        detail_lines = [f"{d['step']}: {d['desc']} (Value: {d['value']:.2f})" for d in details]
        rec_lines = [f"- {rec}" for rec in recommendations]
        prediction_text = (
            f"Predicted Annual Health Cost: ${final_cost:,.2f}\n\n"
            f"Calculation Steps:\n" + "\n".join(detail_lines) +
            ("\n\nRecommendations:\n" + "\n".join(rec_lines) if rec_lines else "")
        )
        return prediction_text, pdf_path
    except ValueError as e:
        error_message = f"Invalid input format: {str(e)}"
        return error_message, None
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return error_message, None

