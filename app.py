from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests  # For making API calls to OpenWeatherMap

# Load environment variables
load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Set a secret key for session management

# OpenWeatherMap API key
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# Model configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-exp-1206",
    generation_config=generation_config,
    system_instruction=(
        "You are a chatbot named Ram, an experienced Indian farmer who provides advice to fellow farmers based on their "
        "specific farming conditions. Your answers should be clear and practical, helping other farmers with common challenges "
        "related to agriculture. Each response you provide should be structured as HTML content.\n\n"
        "- Use `<h1>` tags for any main heading, such as advice topics or key points.\n"
        "- Use `<ul>` and `<li>` tags to list out detailed steps or recommendations.\n"
        "- For any subheading or important point under a main heading, use `<h2>` tags.\n"
        "- Do not provide plain text or explanations outside the HTML structure.\n"
        "- Do not use any code block formatting (e.g., ` ```html ` or similar).\n"
        "- Ensure the advice is region-appropriate for Indian farmers, considering local weather, crops, and agricultural practices.\n"
        "- Make the tone conversational and friendly, as if you’re talking directly to a fellow farmer.\n\n"
        "Example structure for your response:\n"
        "<h1>Crop Selection Tips</h1>\n"
        "<ul>\n"
        "    <li><h2>Choose crops based on soil type</h2>\n"
        "        <ul>\n"
        "            <li>For clay soil, consider paddy, wheat, or gram.</li>\n"
        "            <li>For sandy soil, pulses like moong dal work well.</li>\n"
        "        </ul>\n"
        "    </li>\n"
        "    <li><h2>Monitor weather patterns</h2>\n"
        "        <ul>\n"
        "            <li>If there is consistent rainfall, plant crops that require water, like rice.</li>\n"
        "            <li>For dry conditions, opt for drought-resistant crops like millet.</li>\n"
        "        </ul>\n"
        "    </li>\n"
        "</ul>"
    ),
)

# Homepage
@app.route('/')
def home():
    return render_template('index.html')

# Sign-in Page
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        # Handle sign-in logic here
        email = request.form['email']
        password = request.form['password']
        # Add your authentication logic here
        session['user'] = email  # Store user in session
        return redirect(url_for('dashboard'))
    return render_template('signin.html')

# Sign-up Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Handle sign-up logic here
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        # Add your user registration logic here
        return redirect(url_for('signin'))
    return render_template('signup.html')

# Dashboard Page
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    return redirect(url_for('signin'))

# Chatbot Page
@app.route('/chatbot')
def chatbot():
    if 'user' in session:
        return render_template('chatbot.html', user=session['user'])
    return redirect(url_for('signin'))

# Chatbot API route
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")

    try:
        # Create or continue a chat session
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(user_message)

        # Extract the response text
        response_text = response.text

        return jsonify({"response": response_text})
    except Exception as e:
        # Handle any errors
        return jsonify({"error": str(e)}), 500

# Weather Page
@app.route('/weather', methods=['GET', 'POST'])
def weather():
    if 'user' not in session:
        return redirect(url_for('signin'))

    if request.method == 'POST':
        # Get the city/area from the form
        city = request.form.get('city')
        
        # Fetch weather data from OpenWeatherMap API
        weather_data = get_weather_data(city)
        
        if weather_data:
            return render_template('weather.html', weather_data=weather_data, city=city)
        else:
            return render_template('weather.html', error="Unable to fetch weather data. Please try again.")
    
    # Render the form to input the city
    return render_template('weather.html')

def get_weather_data(city):
    # Fetch weather data using OpenWeatherMap API
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(base_url)
    
    if response.status_code == 200:
        data = response.json()
        weather = {
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed']
        }
        return weather
    else:
        return None

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)