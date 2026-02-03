"""
PCOS Care AI - Automated Symptom-Based Triage System
A Telegram bot that evaluates PCOS risk using weighted scoring
"""

import telebot
from telebot import types
import os
from datetime import datetime
from threading import Thread
from flask import Flask

# Initialize Flask app for Render health checks
app = Flask(__name__)

@app.route('/')
def home():
    return "PCOS Telegram Bot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "running"}

# Get bot token from environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
bot = telebot.TeleBot(BOT_TOKEN)

# User data storage (in production, use a database)
user_data = {}

# Weighted scoring system
WEIGHTS = {
    'cycle_regularity': {
        'Regular': 0,
        'Irregular': 35,
        'None': 40
    },
    'cycle_length': {
        'normal': 0,      # 21-35 days
        'short': 15,      # <21 days
        'long': 25,       # >35 days
        'none': 30        # No cycle
    },
    'symptoms': {
        'Acne': 8,
        'Facial Hair': 12,
        'Weight Gain': 10,
        'Hair Thinning': 10
    }
}

class PCOSScorer:
    """Calculates PCOS risk based on weighted symptoms"""
    
    @staticmethod
    def calculate_cycle_length_weight(length, regularity):
        """Calculate weight based on cycle length"""
        if regularity == 'None':
            return WEIGHTS['cycle_length']['none']
        
        try:
            days = int(length)
            if 21 <= days <= 35:
                return WEIGHTS['cycle_length']['normal']
            elif days < 21:
                return WEIGHTS['cycle_length']['short']
            else:
                return WEIGHTS['cycle_length']['long']
        except:
            return 0
    
    @staticmethod
    def calculate_total_score(data):
        """Calculate total PCOS probability score"""
        score = 0
        
        # Cycle regularity weight (highest impact)
        regularity = data.get('cycle_regularity', 'Regular')
        score += WEIGHTS['cycle_regularity'].get(regularity, 0)
        
        # Cycle length weight
        cycle_length = data.get('cycle_length', '28')
        score += PCOSScorer.calculate_cycle_length_weight(cycle_length, regularity)
        
        # Physical symptoms weight
        symptoms = data.get('symptoms', [])
        for symptom in symptoms:
            score += WEIGHTS['symptoms'].get(symptom, 0)
        
        # Convert to percentage (max possible score ~100)
        max_score = 100
        percentage = min((score / max_score) * 100, 100)
        
        return round(percentage, 1)
    
    @staticmethod
    def get_risk_category(percentage):
        """Categorize risk based on percentage"""
        if percentage < 30:
            return "Low"
        elif percentage <= 70:
            return "Medium"
        else:
            return "High"


def get_recommendations(risk_category, percentage):
    """Generate personalized recommendations based on risk level"""
    
    recommendations = {
        "Low": {
            "message": f"🟢 **Low Risk Detected ({percentage}%)**\n\nYour symptoms suggest a low risk of PCOS. However, maintaining healthy habits is essential for prevention.",
            "recommendations": [
                "🏃‍♀️ **Exercise**: Light cardio 4-5 times a week (30 min)",
                "🥗 **Nutrition**: Focus on complex carbs (whole grains, quinoa, oats)",
                "⚖️ **BMI Management**: Maintain healthy weight (BMI 18.5-24.9)",
                "😴 **Sleep**: Maintain consistent 7-8 hour sleep cycle",
                "💧 **Hydration**: Drink 2-3 liters of water daily",
                "🧘‍♀️ **Stress**: Practice relaxation techniques regularly"
            ]
        },
        "Medium": {
            "message": f"🟡 **Medium Risk Detected ({percentage}%)**\n\nModerate symptoms detected. Hormonal imbalance is likely. Lifestyle modifications and medical consultation recommended.",
            "recommendations": [
                "🍵 **Spearmint Tea**: Drink 2 cups daily (helps reduce androgens)",
                "🏋️‍♀️ **HIIT Exercise**: 3x per week (20-30 min sessions)",
                "🩸 **Blood Tests**: Consult doctor for LH/FSH ratio, testosterone, insulin levels",
                "🥑 **Diet**: Low glycemic index foods, increase fiber intake",
                "🌰 **Seed Cycling**: Flax/pumpkin seeds (Days 1-14), Sesame/sunflower (Days 15-28)",
                "⏰ **Meal Timing**: Avoid late-night eating, maintain regular meal schedule",
                "📊 **Track Symptoms**: Keep a menstrual and symptom diary",
                "💊 **Supplements**: Consider Inositol, Vitamin D (consult doctor first)"
            ]
        },
        "High": {
            "message": f"🔴 **High Risk Detected ({percentage}%)**\n\n⚠️ High PCOS probability detected. Clinical intervention is strongly advised. Please consult a gynecologist urgently.",
            "recommendations": [
                "🏥 **URGENT**: Schedule gynecological consultation within 1-2 weeks",
                "🔬 **Ultrasound Scan**: Get transvaginal ultrasound for ovarian assessment",
                "🩺 **Comprehensive Tests**: Complete hormonal panel, glucose tolerance test",
                "🚫 **Strict Low-GI Diet**: Eliminate processed sugars, refined carbs",
                "🌾 **Seed Cycling**: Implement hormone regulation protocol",
                "💊 **Medical Management**: Discuss Metformin, birth control with doctor",
                "⚖️ **Weight Management**: If BMI >25, aim for 5-10% weight loss",
                "🧘‍♀️ **Stress Management**: Daily meditation/yoga (cortisol control)",
                "📝 **Document Everything**: Keep detailed symptom and cycle records"
            ]
        }
    }
    
    return recommendations.get(risk_category, recommendations["Low"])


def get_daily_precautions():
    """Return universal daily precautions for all users"""
    return """
━━━━━━━━━━━━━━━━━━━━━━
📋 **DAILY PRECAUTIONS**
━━━━━━━━━━━━━━━━━━━━━━

**For All Users (Prevention & Management):**

🍬 **Sugar Control**
   • Avoid processed sugars and refined carbs
   • Replace white rice/bread with brown alternatives
   • Limit fruit juice, choose whole fruits

😌 **Stress Management**
   • 10-minute daily meditation or deep breathing
   • Cortisol management is crucial for hormone balance
   • Consider yoga or mindfulness apps

😴 **Sleep Hygiene**
   • Maintain consistent 8-hour sleep window
   • Sleep regulates insulin sensitivity
   • Avoid screens 1 hour before bed

💧 **Hydration**
   • 2-3 liters of water daily
   • Helps flush toxins and regulate metabolism

🚶‍♀️ **Daily Movement**
   • At least 30 minutes of activity
   • Take stairs, walk after meals

🥗 **Anti-inflammatory Foods**
   • Turmeric, ginger, green tea
   • Omega-3 rich foods (fish, walnuts, flax)

⏰ **Regular Meals**
   • Don't skip breakfast
   • Eat every 3-4 hours to stabilize blood sugar
"""


# Bot Commands

@bot.message_handler(commands=['start'])
def start(message):
    """Welcome message and introduction"""
    user_id = message.from_user.id
    user_data[user_id] = {}
    
    welcome_text = """
🌸 **Welcome to PCOS Care AI** 🌸

I'm your automated PCOS risk assessment assistant. I'll help you understand your risk level through a series of simple questions.

**What I do:**
✅ Evaluate PCOS risk based on symptoms
✅ Provide personalized recommendations
✅ Suggest lifestyle modifications
✅ Guide you on next steps

**Commands:**
/assess - Start PCOS risk assessment
/logic - View scoring algorithm
/help - Get help and information
/about - About PCOS

**Privacy:** Your data is used only for this assessment and not shared.

Ready to begin? Type /assess to start! 🚀
    """
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')


@bot.message_handler(commands=['help'])
def help_command(message):
    """Help information"""
    help_text = """
📚 **PCOS Care AI - Help**

**Available Commands:**
/start - Restart the bot
/assess - Begin PCOS assessment
/logic - View decision algorithm
/about - Learn about PCOS
/help - This help message

**How the Assessment Works:**
1. I'll ask about your menstrual cycle
2. Then about physical symptoms
3. I calculate a risk score (0-100%)
4. You get personalized recommendations

**Risk Categories:**
🟢 Low (<30%): Preventive care
🟡 Medium (30-70%): Lifestyle changes + medical consultation
🔴 High (>70%): Urgent medical attention

**Note:** This is a screening tool, not a diagnosis. Always consult healthcare professionals.
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')


@bot.message_handler(commands=['about'])
def about_pcos(message):
    """Information about PCOS"""
    about_text = """
🔬 **About PCOS (Polycystic Ovary Syndrome)**

PCOS is a common hormonal disorder affecting women of reproductive age.

**Common Symptoms:**
• Irregular or absent periods
• Excess androgens (male hormones)
• Polycystic ovaries (visible on ultrasound)
• Acne and oily skin
• Excess facial/body hair
• Weight gain
• Hair thinning
• Difficulty getting pregnant

**Diagnosis Requires (2 of 3):**
1. Irregular ovulation
2. High androgen levels
3. Polycystic ovaries on ultrasound

**Long-term Risks:**
⚠️ Type 2 diabetes
⚠️ Heart disease
⚠️ Endometrial cancer
⚠️ Sleep apnea

**Good News:**
✅ Manageable with lifestyle changes
✅ Treatable with medication
✅ Many women lead healthy lives

Type /assess to check your risk!
    """
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown')


@bot.message_handler(commands=['logic'])
def show_logic(message):
    """Display the scoring algorithm and decision logic"""
    logic_text = """
🧮 **PCOS Risk Scoring Algorithm**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**WEIGHTED SCORING SYSTEM**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**1️⃣ CYCLE REGULARITY (Primary Factor)**
├─ Regular: 0 points
├─ Irregular: 35 points ⚠️
└─ None/Absent: 40 points ⚠️⚠️

**2️⃣ CYCLE LENGTH (Secondary Factor)**
├─ Normal (21-35 days): 0 points
├─ Short (<21 days): 15 points
├─ Long (>35 days): 25 points
└─ No cycle: 30 points

**3️⃣ PHYSICAL SYMPTOMS**
├─ Acne: 8 points
├─ Facial Hair: 12 points
├─ Weight Gain: 10 points
└─ Hair Thinning: 10 points

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**DECISION TREE**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Score = Regularity + Length + Symptoms
Percentage = (Total Score / 100) × 100

IF Percentage < 30 THEN
   Risk = LOW
   
ELSE IF 30 ≤ Percentage ≤ 70 THEN
   Risk = MEDIUM
   
ELSE IF Percentage > 70 THEN
   Risk = HIGH
    """
    bot.send_message(message.chat.id, logic_text, parse_mode='Markdown')


@bot.message_handler(commands=['assess'])
def start_assessment(message):
    """Begin the PCOS assessment"""
    user_id = message.from_user.id
    user_data[user_id] = {'stage': 'cycle_regularity'}
    
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Regular', 'Irregular', 'None')
    
    bot.send_message(
        message.chat.id,
        "🩺 **PCOS Risk Assessment**\n\n**Question 1/3:**\nHow would you describe your menstrual cycle?",
        reply_markup=markup,
        parse_mode='Markdown'
    )


@bot.message_handler(func=lambda message: True)
def handle_responses(message):
    """Handle all user responses during assessment"""
    user_id = message.from_user.id
    
    if user_id not in user_data:
        bot.send_message(message.chat.id, "Please start with /assess command")
        return
    
    stage = user_data[user_id].get('stage')
    
    if stage == 'cycle_regularity':
        handle_cycle_regularity(message)
    elif stage == 'cycle_length':
        handle_cycle_length(message)
    elif stage == 'symptoms':
        handle_symptoms(message)


def handle_cycle_regularity(message):
    """Handle cycle regularity response"""
    user_id = message.from_user.id
    response = message.text
    
    if response not in ['Regular', 'Irregular', 'None']:
        bot.send_message(message.chat.id, "Please select from the options provided.")
        return
    
    user_data[user_id]['cycle_regularity'] = response
    user_data[user_id]['stage'] = 'cycle_length'
    
    if response == 'None':
        user_data[user_id]['cycle_length'] = '0'
        ask_symptoms(message)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Less than 21', '21-35 (Normal)', 'More than 35', 'Variable/Unsure')
        
        bot.send_message(
            message.chat.id,
            "**Question 2/3:**\nWhat is your typical cycle length (in days)?",
            reply_markup=markup,
            parse_mode='Markdown'
        )


def handle_cycle_length(message):
    """Handle cycle length response"""
    user_id = message.from_user.id
    response = message.text
    
    # Map responses to numeric values
    length_map = {
        'Less than 21': '20',
        '21-35 (Normal)': '28',
        'More than 35': '40',
        'Variable/Unsure': '35'
    }
    
    if response in length_map:
        user_data[user_id]['cycle_length'] = length_map[response]
    else:
        # Try to parse as number
        try:
            days = int(response)
            user_data[user_id]['cycle_length'] = str(days)
        except:
            bot.send_message(message.chat.id, "Please provide a valid response.")
            return
    
    ask_symptoms(message)


def ask_symptoms(message):
    """Ask about physical symptoms"""
    user_id = message.from_user.id
    user_data[user_id]['stage'] = 'symptoms'
    
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Acne', 'Facial Hair', 'Weight Gain', 'Hair Thinning')
    markup.add('None of these', 'Done')
    
    bot.send_message(
        message.chat.id,
        "**Question 3/3:**\nDo you experience any of these symptoms?\n\n(Select one at a time, then click 'Done' when finished)",
        reply_markup=markup,
        parse_mode='Markdown'
    )


def handle_symptoms(message):
    """Handle symptom selection"""
    user_id = message.from_user.id
    response = message.text
    
    if 'symptoms' not in user_data[user_id]:
        user_data[user_id]['symptoms'] = []
    
    if response == 'Done' or response == 'None of these':
        generate_report(message)
    elif response in ['Acne', 'Facial Hair', 'Weight Gain', 'Hair Thinning']:
        if response not in user_data[user_id]['symptoms']:
            user_data[user_id]['symptoms'].append(response)
            bot.send_message(
                message.chat.id,
                f"✅ {response} added. Select more or click 'Done'."
            )
        else:
            bot.send_message(message.chat.id, f"{response} already selected.")
    else:
        bot.send_message(message.chat.id, "Please select from the options.")


def generate_report(message):
    """Generate final PCOS risk report"""
    user_id = message.from_user.id
    data = user_data[user_id]
    
    # Calculate score
    percentage = PCOSScorer.calculate_total_score(data)
    risk_category = PCOSScorer.get_risk_category(percentage)
    
    # Get recommendations
    reco = get_recommendations(risk_category, percentage)
    
    # Build report
    report = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **PCOS RISK ASSESSMENT REPORT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

**Your Inputs:**
• Cycle: {data.get('cycle_regularity', 'N/A')}
• Length: {data.get('cycle_length', 'N/A')} days
• Symptoms: {', '.join(data.get('symptoms', ['None']))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{reco['message']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📋 Personalized Recommendations:**

"""
    
    for rec in reco['recommendations']:
        report += f"{rec}\n\n"
    
    report += get_daily_precautions()
    
    report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚕️ **IMPORTANT DISCLAIMER**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This assessment is a screening tool only and NOT a medical diagnosis. 

✅ **Next Steps:**
• Consult a gynecologist or endocrinologist
• Get proper diagnostic tests
• Follow medical advice

**Questions?** Type /help
**New Assessment?** Type /assess

Thank you for using PCOS Care AI! 🌸
    """
    
    # Remove keyboard
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, report, parse_mode='Markdown', reply_markup=markup)
    
    # Clear user data
    user_data[user_id] = {}


def run_bot():
    """Run the bot with polling"""
    print("🤖 PCOS Care AI Bot is starting...")
    bot.infinity_polling()


if __name__ == '__main__':
    # Run Flask app in a separate thread
    port = int(os.environ.get('PORT', 10000))
    
    # Start bot in background thread
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run Flask app (this keeps the service alive for Render)
    print(f"🌐 Starting web server on port {port}...")
    app.run(host='0.0.0.0', port=port)