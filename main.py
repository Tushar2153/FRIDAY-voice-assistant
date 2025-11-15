"""
Friday: A PyQt5-based Voice Assistant
Refactored for stability, security, and maintainability.
Now powered by a Large Language Model (Gemini) for NLU
and a Hybrid Router to save API quota.
"""

# --- 1. Standard Library Imports ---
import sys
import os
import datetime
import random
import operator

# --- 2. Third-Party Library Imports ---
import cv2
import fitz  # PyMuPDF, for reading PDFs
import pint  # For unit conversions
import pyjokes
import psutil
import pyttsx3
import pyautogui
import pywhatkit
import requests
import speedtest
import speech_recognition as sr
import wikipedia
import webbrowser
from googletrans import Translator
from pywikihow import search_wikihow
import pyscreenshot

# --- New LLM Imports ---
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- 3. PyQt5 Imports ---
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QTimer, QTime, QDate, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QWidget, QMainWindow, QApplication
from PyQt5.uic import loadUiType

# --- 4. Local Imports ---
import config  # Import your new configuration file
try:
    # This imports your compiled UI file (e.g., from friday1.ui)
    from friday1 import Ui_MainWindow
except ImportError:
    print("Error: Could not import 'friday1.py'.")
    print("Please make sure you have compiled your .ui file to a .py file named 'friday1.py'.")
    sys.exit(1)


# --- Global Engine Setup ---
try:
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
except Exception as e:
    print(f"Error initializing text-to-speech engine: {e}")
    engine = pyttsx3.init()

def speak(audio):
    """Speaks the given text."""
    try:
        engine.say(audio)
        engine.runAndWait()
    except Exception as e:
        print(f"Error during speech: {e}")

def wishme():
    """Greets the user based on the time of day."""
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        speak("good morning sir i am friday how may i help you ")
    elif 12 <= hour < 18:
        speak("good afternoon sir i am friday how may i help you")
    else:
        speak("Hello sir I am friday how may i help you")

def translate_text(text, target_language='en'):
    """Translates text to a target language."""
    try:
        translator = Translator()
        translated_text = translator.translate(text, dest=target_language)
        return translated_text.text
    except Exception as e:
        print(f"Translation Error: {e}")
        return "Sorry, I couldn't translate that."

def get_weather(city):
    """Fetches weather information for a city. Returns a string."""
    base_url = 'http://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': city,
        'appid': config.WEATHER_API_KEY,  # Use key from config
        'units': 'metric'  # Request in Celsius
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if response.status_code == 200:
            weather_description = data['weather'][0]['description']
            temperature = data['main']['temp']
            humidity = data['main']['humidity']
            return f"The weather in {city} is {weather_description}. The temperature is {temperature} degrees Celsius, with {humidity} percent humidity."
        else:
            return f"Error: {data.get('message', 'Unknown error')}"
    except requests.exceptions.RequestException as e:
        print(f"Weather API Request Error: {e}")
        return "An error occurred: Could not connect to the weather service."

def get_news(country='in', category='general', num_articles=3):
    """Fetches top news headlines. Returns a single formatted string."""
    base_url = 'https://newsapi.org/v2/top-headlines'
    params = {
        'apiKey': config.NEWS_API_KEY,  # Use key from config
        'country': country,
        'category': category,
        'pageSize': num_articles,
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if response.status_code == 200:
            articles = data.get('articles', [])
            if not articles:
                return "No news articles found."
            
            news_info = ["Here are the top headlines: "]
            for i, article in enumerate(articles):
                title = article.get('title', 'No Title')
                news_info.append(f"Headline {i+1}: {title}.")
            return " ".join(news_info)
        else:
            return f"Error: {data.get('message', 'Unknown error')}"
    except requests.exceptions.RequestException as e:
        print(f"News API Request Error: {e}")
        return "An error occurred: Could not connect to the news service."

def convert_units(conversion_query):
    """Performs unit conversions (e.g., '10 meters to feet'). Returns a string."""
    try:
        ureg = pint.UnitRegistry()
        parts = conversion_query.split(' to ')
        if len(parts) != 2:
            return "Error: Please format your query as 'value unit to other_unit'."
        
        from_part = parts[0]
        to_unit = parts[1].strip()
        
        quantity = ureg(from_part)
        converted_quantity = quantity.to(to_unit)
        
        return str(converted_quantity)

    except Exception as e:
        print(f"Unit Conversion Error: {e}")
        return "Error: Unable to perform unit conversion. Please check your input."

def read_pdf(file_path):
    """Reads text from the first page of a PDF file. Returns a string."""
    try:
        pdf_document = fitz.open(file_path)
        num_pages = pdf_document.page_count
        
        if num_pages == 0:
            return "The PDF is empty and has no pages."

        page = pdf_document[0] # Read only the first page
        text = page.get_text()
        
        if not text:
            return f"The PDF has {num_pages} pages, but the first page has no readable text."

        return f"The PDF has {num_pages} pages. Here is the text from the first page: {text}"

    except Exception as e:
        return f"An error occurred while reading the PDF: {e}"

def detect():
    """Performs face recognition to verify the user."""
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(config.TRAINER_PATH)
        faceCascade = cv2.CascadeClassifier(config.CASCADE_PATH)
    except cv2.error as e:
        print(f"OpenCV Error: {e}")
        speak("Error loading face detection models. Please check config file paths.")
        return False
        
    font = cv2.FONT_HERSHEY_SIMPLEX
    names = config.RECOGNIZED_NAMES
    
    try:
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cam.isOpened():
            speak("Error: Cannot open camera.")
            return False
            
        cam.set(3, 640)
        cam.set(4, 480)
        minW = 0.1 * cam.get(3)
        minH = 0.1 * cam.get(4)
    except Exception as e:
        print(f"Camera Error: {e}")
        speak("Error initializing camera.")
        return False

    flag = True
    verified = False

    while flag:
        ret, img = cam.read()
        if not ret:
            speak("Error reading frame from camera.")
            break
            
        converted_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(
            converted_image,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(minW), int(minH)),
        )

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            try:
                id_index, accuracy = recognizer.predict(converted_image[y:y + h, x:x + w])
                
                if (accuracy < 60):
                    id_name = names[id_index] if id_index < len(names) else "Known"
                    accuracy_str = "  {0}%".format(round(100 - accuracy))
                    speak("verification successful")
                    verified = True
                    flag = False  # Exit loop
                else:
                    id_name = "unknown"
                    accuracy_str = "  {0}%".format(round(100 - accuracy))
                    speak("cannot verify")
                    
                cv2.putText(img, str(id_name), (x + 5, y - 5), font, 1, (255, 255, 255), 2)
                cv2.putText(img, str(accuracy_str), (x + 5, y + h - 5), font, 1, (255, 255, 0), 1)
            
            except cv2.error as e:
                print(f"Face prediction error: {e}")
                cv2.putText(img, "Error", (x + 5, y - 5), font, 1, (0, 0, 255), 2)
        
        cv2.imshow('camera', img)
        if (cv2.waitKey(1) == ord('q')):
            break

    cam.release()
    cv2.destroyAllWindows()
    
    if not verified:
        speak("Verification failed.")
        return False
        
    return True


# --- Main Worker Thread (Refactored for LLM) ---
# --- Main Worker Thread (Refactored for LLM) ---
class MainThread(QThread):
    def __init__(self):
        super(MainThread, self).__init__()
        self.running = True

        # --- THIS IS THE NEW LOCAL COMMAND MAP ---
        self.local_command_map = {
            # New Local Searches
            'youtube': self.handle_youtube_local,
            'google': self.handle_google_local,
            'search': self.handle_google_local,
            'wikipedia': self.handle_wikipedia_local,
            'wikihow': self.handle_wikihow_local,
            'how to': self.handle_wikihow_local,

            # Existing Local Commands
            'screenshot': self.handle_screenshot,
            'time': self.handle_time,
            'battery': self.handle_battery,
            'power left': self.handle_battery,
            'internet speed': self.handle_internet_speed,
            'volume up': lambda query: self.handle_volume('up'),
            'volume down': lambda query: self.handle_volume('down'),
            'mute': lambda query: self.handle_volume('mute'),
            'volume mute': lambda query: self.handle_volume('mute'),
            'play music': self.handle_play_music,
            'open code': lambda query: self.handle_open_app('code'),
            'open notepad': lambda query: self.handle_open_app('notepad'),
            'sleep': self.handle_sleep,
        }
        # --- END OF NEW MAP ---

        # --- 1. Configure the LLM ---
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            
            # --- 2. Define Your Tools (Functions) ---
            # These are for the AI to use
            self.tools = [
                {
                    "function_declarations": [
                        # --- Web & Search Tools (Still here for the AI to use if needed) ---
                        {
                            "name": "handle_wikipedia",
                            "description": "Get a brief summary of a topic from Wikipedia.",
                            "parameters": { "type": "OBJECT", "properties": { "topic": { "type": "STRING", "description": "The topic to search for" } }, "required": ["topic"] }
                        },
                        {
                            "name": "handle_youtube",
                            "description": "Open YouTube and search for a video. Can also play the first result.",
                            "parameters": { "type": "OBJECT", "properties": { "search_query": { "type": "STRING", "description": "The search term for the video" } }, "required": ["search_query"] }
                        },
                        {
                            "name": "handle_google",
                            "description": "Perform a Google search in the browser for a given query.",
                            "parameters": { "type": "OBJECT", "properties": { "search_query": { "type": "STRING", "description": "The term to search on Google" } }, "required": ["search_query"] }
                        },
                        {
                            "name": "handle_open_web",
                            "description": "Open a specific website in the browser.",
                            "parameters": { "type": "OBJECT", "properties": { "site_name": { "type": "STRING", "description": "The name of the site (e.g., 'google', 'gmail')" } }, "required": ["site_name"] }
                        },
                        # --- System & OS Tools ---
                        {
                            "name": "handle_open_app",
                            "description": "Opens a local application like VS Code or Notepad.",
                            "parameters": { "type": "OBJECT", "properties": { "app_name": { "type": "STRING", "description": "The name of the app (e.g., 'code', 'notepad')" } }, "required": ["app_name"] }
                        },
                        {
                            "name": "handle_open_camera",
                            "description": "Open the computer's webcam.",
                            "parameters": {}
                        },
                        {
                            "name": "handle_battery",
                            "description": "Get the current battery percentage of the laptop.",
                            "parameters": {}
                        },
                        {
                            "name": "handle_internet_speed",
                            "description": "Test the current internet download and upload speed.",
                            "parameters": {}
                        },
                        {
                            "name": "handle_screenshot",
                            "description": "Take a screenshot of the entire screen and save it.",
                            "parameters": {}
                        },
                        {
                            "name": "handle_volume",
                            "description": "Adjust the system volume.",
                            "parameters": { "type": "OBJECT", "properties": { "direction": { "type": "STRING", "description": "e.g., 'up', 'down', or 'mute'" } }, "required": ["direction"] }
                        },
                        {
                            "name": "handle_sleep",
                            "description": "Stop the assistant and put it in sleep mode.",
                            "parameters": {}
                        },
                        # --- Productivity Tools ---
                        {
                            "name": "handle_time",
                            "description": "Get the current time.",
                            "parameters": {}
                        },
                        {
                            "name": "handle_calculate",
                            "description": "Calculate a simple arithmetic expression (e.g., '5 plus 2').",
                            "parameters": { "type": "OBJECT", "properties": { "expression": { "type": "STRING", "description": "The expression to calculate, e.g., '10 times 5'" } }, "required": ["expression"] }
                        },
                        {
                            "name": "handle_convert",
                            "description": "Perform a unit conversion.",
                            "parameters": { "type": "OBJECT", "properties": { "conversion_query": { "type": "STRING", "description": "The conversion to perform, e.g., '10 meters to feet'" } }, "required": ["conversion_query"] }
                        },
                        {
                            "name": "handle_translate",
                            "description": "Translate text from English to another language.",
                            "parameters": { "type": "OBJECT", "properties": { "text": { "type": "STRING", "description": "The text to translate" }, "target_language": { "type": "STRING", "description": "The target language (e.g., 'hindi', 'french')" } }, "required": ["text", "target_language"] }
                        },
                        {
                            "name": "handle_remember",
                            "description": "Remember a short piece of information.",
                            "parameters": { "type": "OBJECT", "properties": { "text_to_remember": { "type": "STRING", "description": "The information to save" } }, "required": ["text_to_remember"] }
                        },
                        {
                            "name": "handle_recall",
                            "description": "Retrieve the information that was saved.",
                            "parameters": {}
                        },
                        {
                            "name": "handle_read_pdf",
                            "description": "Read the first page of a PDF file from the local PDF directory.",
                            "parameters": { "type": "OBJECT", "properties": { "pdf_name": { "type": "STRING", "description": "The name of the PDF file (without .pdf)" } }, "required": ["pdf_name"] }
                        },
                        # --- Information & Fun Tools ---
                        {
                            "name": "handle_weather",
                            "description": "Get the current weather for a specific city.",
                            "parameters": { "type": "OBJECT", "properties": { "city": { "type": "STRING", "description": "The city name" } }, "required": ["city"] }
                        },
                        {
                            "name": "handle_news",
                            "description": "Get the top news headlines.",
                            "parameters": { "type": "OBJECT", "properties": { "category": { "type": "STRING", "description": "e.g., 'general', 'business', 'technology'" }, "country": { "type": "STRING", "description": "e.g., 'in' (India), 'us' (USA)" } }, "required": [] } # No required params, will use defaults
                        },
                        {
                            "name": "handle_play_music",
                            "description": "Play a random song from the user's music directory.",
                            "parameters": {}
                        },
                        {
                            "name": "handle_joke",
                            "description": "Tell a random programming joke.",
                            "parameters": {}
                        },
                        {
                            "name": "handle_wikihow",
                            "description": "Find a 'how-to' guide from WikiHow.",
                            "parameters": { "type": "OBJECT", "properties": { "task": { "type": "STRING", "description": "The task to learn, e.g., 'tie a tie'" } }, "required": ["task"] }
                        },
                    ]
                }
            ]

            # --- 3. Map Tool Names to Your Actual Python Functions ---
            # This map is still needed for Gemini
            self.function_map = {
                "handle_wikipedia": self.handle_wikipedia,
                "handle_youtube": self.handle_youtube,
                "handle_google": self.handle_google,
                "handle_open_web": self.handle_open_web,
                "handle_open_app": self.handle_open_app,
                "handle_open_camera": self.handle_open_camera,
                "handle_battery": self.handle_battery,
                "handle_internet_speed": self.handle_internet_speed,
                "handle_screenshot": self.handle_screenshot,
                "handle_volume": self.handle_volume,
                "handle_sleep": self.handle_sleep,
                "handle_time": self.handle_time,
                "handle_calculate": self.handle_calculate,
                "handle_convert": self.handle_convert,
                "handle_translate": self.handle_translate,
                "handle_remember": self.handle_remember,
                "handle_recall": self.handle_recall,
                "handle_read_pdf": self.handle_read_pdf,
                "handle_weather": self.handle_weather,
                "handle_news": self.handle_news,
                "handle_play_music": self.handle_play_music,
                "handle_joke": self.handle_joke,
                "handle_wikihow": self.handle_wikihow,
            }
            
            # Safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }

            # System instruction to set the assistant's persona
            system_instruction = "You are Friday, a helpful and professional personal assistant. You were created by Tushar, Tanishka, and Vishakha. Your responses should be concise and helpful."

            # Initialize the generative model
            self.model = genai.GenerativeModel(
                model_name='gemini-2.5-pro', # Updated model name
                safety_settings=safety_settings,
                tools=self.tools,
                system_instruction=system_instruction
            )
            
            # Start a chat session
            self.chat = self.model.start_chat(enable_automatic_function_calling=True)
            
        except Exception as e:
            print(f"Error initializing Gemini Model: {e}")
            speak("Error initializing my AI brain. Please check the API key and internet connection.")
            self.running = False


    def run(self):
        """The main execution loop for the assistant."""
        if not detect():
            speak("Verification failed. Shutting down.")
            return  # Stops the thread cleanly

        wishme()

        while self.running:
            try:
                query = self.takeCommand().lower()
                if query == "none":
                    continue

                if not self.running:  # Check if handle_sleep was called
                    break

                # --- THIS IS THE UPDATED HYBRID ROUTER ---
                if "friday" in query:
                    
                    # 1. Clean the query
                    command_found = False
                    # Remove "friday" to get the clean command
                    clean_query = query.replace("friday", "").strip()

                    # 2. Check Local Commands FIRST
                    # We use startswith() to be more accurate
                    for trigger, function in self.local_command_map.items():
                        if clean_query.startswith(trigger): # <-- IMPROVED
                            print(f"Handling local command: {trigger}")
                            # Call the local function, passing the query
                            response_text = function(clean_query) 
                            speak(response_text)
                            command_found = True
                            break # Stop checking local commands
                    
                    # 3. If NOT a local command, send to Gemini (and use a quota slot)
                    if not command_found:
                        print(f"Sending to Gemini (uses 1 quota): {query}")
                        
                        # Send the user's original query (with "friday") to the LLM
                        response = self.chat.send_message(query)
                        final_response = response.text

                        print(f"LLM Response: {final_response}")
                        speak(final_response)
                
                else:
                    # Ignored (no trigger word)
                    print(f"Ignored query (no trigger): {query}")
                    pass
                # --- END OF HYBRID ROUTER ---

            except Exception as e:
                print(f"An error occurred in the main loop: {e}")
                speak("Sorry, something went wrong. Please try again.")

    def takeCommand(self):
        """Listens for user voice command and returns it as text."""
        r = sr.Recognizer()
        
        with sr.Microphone() as source:
            print("Listening...")
            r.adjust_for_ambient_noise(source)
            r.pause_threshold = 1
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
            except sr.WaitTimeoutError:
                print("Listen timed out, listening again...")
                return "none"

        try:
            print("Recognizing...")    
            query = r.recognize_google(audio, language='en-in')
            print(f"User said: {query}\n")
            return query
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return "none"
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            speak("Unable to reach Google services. Please check your internet connection.")
            return "none"
        except Exception as e:
            print(f"Unknown error in takeCommand: {e}")    
            speak("Unable to Recognize your voice.")  
            return "none"
    
    # --- Helper for handle_calculate ---
    def _eval_binary_expr(self, op1, oper, op2):
        try:
            op1, op2 = int(op1), int(op2)
            
            op_map = {
                '+': operator.add, 'plus': operator.add,
                '-': operator.sub, 'minus': operator.sub,
                'x': operator.mul, 'multiplied': operator.mul, 'times': operator.imul,
                'divided': operator.truediv, 'by': operator.truediv,
            }
            return op_map[oper](op1, op2)
        except Exception:
            return None

    # --- REFACRTORED Handler Methods ---

    # --- NEW LOCAL HANDLERS ---
    def handle_youtube_local(self, query: str):
        """
        Parses a local query to search YouTube.
        Query example: "youtube lofi beats"
        """
        try:
            # Simple parsing: remove "youtube"
            search_query = query.replace("youtube", "").strip()
            if not search_query:
                return "Sorry, I didn't catch what to search for on YouTube."

            print(f"Locally searching YouTube for: {search_query}")
            web = "https://www.youtube.com/results?search_query=" + search_query
            webbrowser.open(web)
            pywhatkit.playonyt(search_query)
            return f"Done, I've opened YouTube and am playing {search_query}."
        except Exception as e:
            return f"I've opened the search results for {search_query}, but couldn't auto-play. {e}"

    def handle_google_local(self, query: str):
        """
        Parses a local query to search Google.
        Query example: "google the weather"
        """
        try:
            # Simple parsing: remove "google" or "search"
            search_query = query.replace("google", "").replace("search", "").strip()
            if not search_query:
                return "Sorry, I didn't catch what to search for on Google."
            
            print(f"Locally searching Google for: {search_query}")
            pywhatkit.search(search_query)
            return f"Opening Google search results for {search_query}."
        except Exception as e:
            return f"Sorry, I couldn't perform the Google search. {e}"

    def handle_wikipedia_local(self, query: str):
        """
        Parses a local query to search Wikipedia.
        Query example: "wikipedia albert einstein"
        """
        try:
            search_topic = query.replace("wikipedia", "").strip()
            if not search_topic:
                return "Sorry, I didn't catch what to search for on Wikipedia."
            
            print(f"Locally searching Wikipedia for: {search_topic}")
            # Call the original handler
            return self.handle_wikipedia(search_topic)
        except Exception as e:
            return f"Sorry, I couldn't search Wikipedia. {e}"

    def handle_wikihow_local(self, query: str):
        """
        Parses a local query to search WikiHow.
        Query example: "how to tie a tie"
        """
        try:
            task = query.replace("wikihow", "").replace("how to", "").strip()
            if not task:
                return "Sorry, I didn't catch what you want to know how to do."

            print(f"Locally searching WikiHow for: {task}")
            # Call the original handler
            return self.handle_wikihow(task)
        except Exception as e:
            return f"Sorry, I couldn't search WikiHow. {e}"


    # --- AI HANDLERS (Still used by Gemini) ---
    def handle_wikipedia(self, topic: str):
        try:
            print(f"Searching Wikipedia for: {topic}")
            results = wikipedia.summary(topic, sentences=2)
            return f"According to Wikipedia, {results}"
        except wikipedia.exceptions.DisambiguationError as e:
            return f"That topic is ambiguous. It could mean: {e.options[0]}, or {e.options[1]}."
        except wikipedia.exceptions.PageError:
            return f"Sorry, I could not find any Wikipedia page for {topic}."
        except Exception as e:
            return f"Sorry, I couldn't find that on Wikipedia. {e}"

    def handle_youtube(self, search_query: str):
        # This is the AI version
        try:
            print(f"AI searching YouTube for: {search_query}")
            web = "https://www.youtube.com/results?search_query=" + search_query
            webbrowser.open(web)
            pywhatkit.playonyt(search_query)
            return f"Done, I've opened YouTube and am playing {search_query}."
        except Exception as e:
            return f"I've opened the search results for {search_query}, but couldn't auto-play. {e}"

    def handle_google(self, search_query: str):
        # This is the AI version
        try:
            print(f"AI searching Google for: {search_query}")
            pywhatkit.search(search_query)
            return f"Opening Google search results for {search_query}."
        except Exception as e:
            return f"Sorry, I couldn't perform the Google search. {e}"

    def handle_open_web(self, site_name: str):
        site_name = site_name.lower()
        url_map = {
            'gmail': "https://gmail.com",
            'google': "https://google.com",
            'instagram': "https://instagram.com",
            'facebook': "https://facebook.com",
            'chat': "https://chat.openai.com", # chatgpt
            'wikipedia': "https://wikipedia.com",
        }
        if site_name in url_map:
            webbrowser.open(url_map[site_name])
            return f"Opening {site_name}."
        else:
            return f"Sorry, I don't have a URL for {site_name}."

    def handle_open_app(self, app_name: str):
        app_name = app_name.lower()
        if 'code' in app_name:
            try:
                os.startfile(config.CODE_PATH)
                return "Opening VS Code."
            except Exception as e:
                return f"Error opening VS Code. Check config path. {e}"
        elif 'notepad' in app_name:
            try:
                os.startfile(config.NOTEPAD_PATH)
                return "Opening Notepad."
            except Exception as e:
                return f"Error opening Notepad. Check config path. {e}"
        else:
            return f"Sorry, I can't open the app '{app_name}'."

    def handle_open_camera(self, query=None): # Added query=None
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            if ret:
                cv2.imshow('Camera', frame)
                cv2.waitKey(5000)
            cap.release()
            cv2.destroyAllWindows()
            return "Opening camera."
        except Exception as e:
            return f"Sorry, I couldn't open the camera. {e}"

    def handle_battery(self, query=None): # Added query=None
        try:
            battery = psutil.sensors_battery()
            percentage = battery.percent
            return f"Sir our system has {percentage} percent battery"
        except Exception as e:
            return f"Sorry, I can't retrieve battery information. {e}"

    def handle_internet_speed(self, query=None): # Added query=None
        try:
            st = speedtest.Speedtest()
            dl_mbps = round(st.download() / 1_000_000, 2)
            up_mbps = round(st.upload() / 1_000_000, 2)
            return f"sir we have {dl_mbps} megabits per second downloading speed and {up_mbps} megabits per second uploading speed"
        except Exception as e:
            return f"Sorry, I couldn't test the internet speed. {e}"

    def handle_screenshot(self, query=None): # Added query=None
        try:
            a = datetime.datetime.now()
            filename = f"screenshot_{a.strftime('%Y-%m-%d_%H-%M-%S')}.png"
            if not os.path.exists("screenshot"):
                os.mkdir("screenshot")
            image_path = os.path.join("screenshot", filename)
            image = pyscreenshot.grab()
            image.save(image_path)
            image.show()
            return f"Screenshot saved as {filename}"
        except Exception as e:
            return f"Sorry, I was unable to take a screenshot. {e}"

    def handle_volume(self, direction: str):
        direction = direction.lower()
        if 'up' in direction:
            pyautogui.press("volumeup")
            return "Volume up."
        elif 'down' in direction:
            pyautogui.press("volumedown")
            return "Volume down."
        elif 'mute' in direction:
            pyautogui.press("volumemute")
            return "Volume muted."
        else:
            return "Sorry, I didn't understand that volume command."

    def handle_sleep(self, query=None): # Added query=None
        self.running = False  # Gracefully stops the loop
        return "Thanks for using me sir, have a good day. Bye."

    def handle_time(self, query=None): # Added query=None
        strTime = datetime.datetime.now().strftime("%I:%M %p")
        return f"sir the time is {strTime}"

    def handle_calculate(self, expression: str):
        try:
            parts = expression.lower().split()
            if len(parts) == 3:
                result = self._eval_binary_expr(parts[0], parts[1], parts[2])
                if result is not None:
                    return f"The result is {result}"
            
            return "Sorry, I can only calculate simple expressions like '5 plus 2'."

        except Exception as e:
            return f"Sorry, I was unable to calculate that. {e}"

    def handle_convert(self, conversion_query: str):
        return convert_units(conversion_query) # Already returns a string

    def handle_translate(self, text: str, target_language: str):
        translated_phrase = translate_text(text, target_language)
        return f"The translation is: {translated_phrase}"

    def handle_remember(self, text_to_remember: str):
        try:
            with open('data.txt', 'w') as remember:
                remember.write(text_to_remember)
            return f"Okay, I will remember that: {text_to_remember}"
        except Exception as e:
            return f"Sorry, I had trouble writing that to my memory. {e}"

    def handle_recall(self, query=None): # Added query=None
        try:
            with open('data.txt', 'r') as remember:
                return "You said me to remember that: " + remember.read()
        except FileNotFoundError:
            return "Sorry, I don't remember anything."
        except Exception as e:
            return f"Sorry, I had trouble recalling that. {e}"

    def handle_read_pdf(self, pdf_name: str):
        pdf_path = os.path.join(config.PDF_DIR, f"{pdf_name.lower()}.pdf")
        
        if os.path.isfile(pdf_path):
            return read_pdf(pdf_path) # Already returns a string
        else:
            return "No valid PDF found with that name. Please try again."

    def handle_weather(self, city: str):
        return get_weather(city) # Already returns a string

    def handle_news(self, category: str = 'general', country: str = 'in'):
        return get_news(country, category) # Already returns a string

    def handle_play_music(self, query=None): # Added query=None
        try:
            music_dir = config.MUSIC_DIR
            songs = os.listdir(music_dir)
            if songs:
                song_to_play = os.path.join(music_dir, random.choice(songs))
                os.startfile(song_to_play)
                return f"Playing {song_to_play.split('.')[0]}"
            else:
                return "Sorry, I couldn't find any songs in your music directory."
        except Exception as e:
            return f"Sorry, I couldn't play music. {e}"

    def handle_joke(self):
        return pyjokes.get_joke()

    def handle_wikihow(self, task: str):
        try:
            how_to = search_wikihow(task, max_results=1)
            if how_to:
                return f"Here is a summary for {task}: {how_to[0].summary}"
            else:
                return f"Sorry, I couldn't find a how-to guide for {task}."
        except Exception as e:
            return f"Sorry sir, I am not able to find this. {e}"
# --- PyQt5 GUI Class ---
startExecution = MainThread()

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.startTask)
        self.ui.pushButton_2.clicked.connect(self.close)
        
        # Store movie objects to prevent garbage collection
        self.movie1 = None
        self.movie2 = None
        self.movie3 = None
        self.movie4 = None

    def startTask(self):
        try:
            self.movie1 = QtGui.QMovie(config.GIF_1_PATH)
            self.ui.label.setMovie(self.movie1)
            self.movie1.start()
            
            self.movie2 = QtGui.QMovie(config.GIF_2_PATH)
            self.ui.label_2.setMovie(self.movie2)
            self.movie2.start()
            
            self.movie3 = QtGui.QMovie(config.GIF_3_PATH)
            self.ui.label_3.setMovie(self.movie3)
            self.movie3.start()
            
            self.movie4 = QtGui.QMovie(config.GIF_4_PATH)
            self.ui.label_4.setMovie(self.movie4)
            self.movie4.start()
        except Exception as e:
            print(f"Error loading GIFs. Make sure paths are correct in config.py: {e}")
            self.ui.label_2.setText("Error loading GIFs")

        self.timer = QTimer(self) # Store timer as instance attribute
        self.timer.timeout.connect(self.showTime)
        self.timer.start(1000)
        
        startExecution.start()

    def showTime(self):
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()
        label_time = current_time.toString('hh:mm:ss')
        label_date = current_date.toString(Qt.ISODate)
        self.ui.textBrowser.setText(label_date)
        self.ui.textBrowser_2.setText(label_time)
        
    def closeEvent(self, event):
        """Ensure the thread stops when closing the window."""
        speak("Shutting down sir.")
        startExecution.running = False
        startExecution.wait()  # Wait for the thread to finish
        event.accept()


# --- Application Entry Point ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    friday = Main()
    friday.show()
    sys.exit(app.exec())
