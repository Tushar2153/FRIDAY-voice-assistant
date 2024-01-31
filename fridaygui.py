from PyQt5.QtWidgets import QWidget
from click import BaseCommand
import pyttsx3
import requests
import sys
import wikipedia
import datetime
import webbrowser 
import operator
import pywhatkit
import psutil
from urllib.parse import quote
import os
import fitz
import pyscreenshot
import cv2
import random
import pyautogui
import speedtest
import pyjokes
from googletrans import Translator
import pyautogui as pi
import speech_recognition as sr
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QTimer , QTime , QDate, Qt
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import*
from PyQt5.QtGui import*
from PyQt5.QtWidgets import*
from PyQt5.uic import loadUiType
from friday1 import Ui_MainWindow 


engine=pyttsx3.init('sapi5')
voices=engine.getProperty('voices')
print(voices[1].id)
engine.setProperty('voice', voices[1].id)


def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def wishme():           
    hour = int (datetime.datetime.now().hour)
    if hour>=0 and hour<12:
        speak("good morning sir i am friday how may i help you ")
    elif hour>=12 and hour<18 :
        speak("good afternoon sir i am friday how may i help you")
    else:
        speak("Hello sir I am friday how may i help you")  

def translate_text(text, target_language='en'):
    translator = Translator()
    translated_text = translator.translate(text, dest=target_language)
    return translated_text.text

def get_weather(api_key, city):
    base_url = 'http://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': city,
        'appid': api_key,
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if response.status_code == 200:
            weather_description = data['weather'][0]['description']
            temperature = data['main']['temp']
            humidity = data['main']['humidity']

            weather_info = f"The weather in {city} is {weather_description}. Temperature: {temperature}Kelvin, Humidity: {humidity}%."
            return weather_info
        else:
            return f"Error: {data.get('message', 'Unknown error')}"

    except Exception as e:
        return f"An error occurred: {e}"
    
def get_news(api_key, country='IN', category='general', num_articles=3):
    base_url = 'https://newsapi.org/v2/top-headlines'
    params = {
        'apiKey': api_key,
        'country': country,
        'category': category,
        'pageSize': num_articles,
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if response.status_code == 200:
            articles = data['articles']
            news_info = []
            for article in articles:
                title = article['title']
                description = article['description']
                news_info.append(f"{title}: {description}")
            return news_info
        else:
            return f"Error: {data.get('message', 'Unknown error')}"

    except Exception as e:
        return f"An error occurred: {e}"
    
def convert_units(self, conversion_query):
        try:
            import pint
            ureg = pint.UnitRegistry()

            converted_value = ureg(conversion_query).to_base_units().magnitude
            return converted_value

        except Exception as e:
            print(e)
            return "Error: Unable to perform unit conversion. Please check your input."
def read_pdf(file_path):
    try:
        pdf_document = fitz.open(file_path)
        num_pages = pdf_document.page_count

        speak(f"The PDF document has {num_pages} pages. Starting to read...")

        for page_number in range(num_pages):
            page = pdf_document[page_number]
            text = page.get_text()
            speak(f"Page {page_number + 1}: {text}")

        speak("Reading complete.")

    except Exception as e:
        speak(f"An error occurred while reading the PDF: {e}")

def detect():

    recognizer = cv2.face.LBPHFaceRecognizer_create() # Local Binary Patterns Histograms
    recognizer.read('trainer/trainer.yml')   #load trained model
    cascadePath = "haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascadePath) #initializing haar cascade for object detection approach

    font = cv2.FONT_HERSHEY_SIMPLEX #denotes the font type


    id = 2 #number of persons you want to Recognize


    names = ['','Tushar']  #names, leave first empty bcz counter starts from 0
    

    cam = cv2.VideoCapture(0 , cv2.CAP_DSHOW) #cv2.CAP_DSHOW to remove warning
    cam.set(3, 640) # set video FrameWidht
    cam.set(4, 480) # set video FrameHeight

    # Define min window size to be recognized as a face
    minW = 0.1*cam.get(3)
    minH = 0.1*cam.get(4)

    flag = True

    while flag:

        ret,img =cam.read() #read the frames using the above created object

        converted_image = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)  #The function converts an input image from one color space to another

        faces = faceCascade.detectMultiScale( 
            converted_image,
            scaleFactor = 1.2,
            minNeighbors = 5,
            minSize = (int(minW), int(minH)),
        )

        for(x,y,w,h) in faces :

            cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2) #used to draw a rectangle on any image

            id, accuracy = recognizer.predict(converted_image[y:y+h,x:x+w]) #to predict on every single image

            # Check if accuracy is less them 100 ==> "0" is perfect match 
            if (accuracy<60):
                id = names[id]
                accuracy = "  {0}%".format(round(100 - accuracy))
                speak("verification successful")
                flag=False

            else:
                id = "unknown"
                accuracy = "  {0}%".format(round(100 - accuracy))
                speak("cannot verify")
                
                sys.exit()
           
            
            cv2.putText(img, str(id), (x+5,y-5), font, 1, (255,255,255), 2)
            cv2.putText(img, str(accuracy), (x+5,y+h-5), font, 1, (255,255,0), 1)  
        
        cv2.imshow('camera',img) 

        if (cv2.waitKey(1) ==ord('q')):
            break

    cam.release()
    cv2.destroyAllWindows() 


class MainThread(QThread):
      
    def __init__(self):
        super(MainThread,self).__init__()

    def run(self):
        self.TaskExecution()
        
                            
    def takeCommand(self):
        
        r = sr.Recognizer()
        
        with sr.Microphone() as source:
            
            print("Listening...")
            r.adjust_for_ambient_noise(source)
            r.pause_threshold = 1
            audio = r.listen(source)

        try:
            print("Recognizing...")    
            query = r.recognize_google(audio, language ='en-in')
            print(f"User said: {query}\n")
    
        except Exception as e:
            print(e)    
            speak("Unable to Recognize your voice.")  
            return "None"
        
        return query
    
    def TaskExecution(self):
            
            detect()
            wishme()
            while True:
                    self.query = self.takeCommand().lower()

                    if 'wikipedia' in self.query:
                        speak('Searching Wikipedia...')
                        self.query = self.query.replace("wikipedia","")
                        results= wikipedia.summary(self.query, sentences=2)
                        speak("according to wikipedia")
                        print(results)
                        speak(results)

                    elif 'friday' in self.query:
                        print("yes sir")
                        speak("yes sir")
                    elif 'who are you' in self.query:
                        print("I am friday")
                        speak("I am friday")
                    elif 'who created you' in self.query:
                        speak("i was created by tushar , tanishka and vishakha")
                    elif 'thank you' in self.query:
                        speak("welcome")
                    elif 'how are you' in self.query:
                        speak("I am fine sir, what about you")
                    elif 'i am good' in self.query:
                        speak("great, can i do something for you")
                    elif 'thank you' in self.query:
                        speak("Welcome sir")
                    elif 'open gmail' in self.query:
                        webbrowser.open("gmail.com")
                    elif 'open wikipedia' in self.query:
                        webbrowser.open("wikipedia.com")
                    elif 'open google' in self.query:
                        webbrowser.open("google.com")
                    elif 'open instagram' in self.query:
                        webbrowser.open("instagram.com")
                    elif 'open facebook' in self.query:
                        webbrowser.open("facebook.com")    
                    elif 'open chat' in self.query:
                        webbrowser.open("chat.openai.com")    
                    
                    elif 'the time' in self.query:
                        strTime=datetime.datetime.now().strftime("%H:%M:%S")
                        speak(f"sir the time is {strTime} ")
                        
                    elif 'open code' in self.query:
                        codepath="C:\\Users\\Varun\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe" 
                        os.startfile(codepath)

                    elif "calculate" in self.query:
                        try:
                            r=sr.Recognizer()
                            with sr.Microphone() as source:
                                speak("say what you want to calculate")
                                print("listening...")
                                r.adjust_for_ambient_noise(source)
                                audio=r.listen(source)           
                                my_string=r.recognize_google(audio)
                                print(my_string)
                                def get_operator_fn(op):
                                    return{
                                        '+' : operator.add, #plus
                                        '-' : operator.sub, #minus
                                        'x' : operator.mul, #multiplied by
                                        'divided' : operator.__truediv__, #divided                
                                        }[op]
                                def eval_binary_expr(op1, oper, op2):
                                    op1,op2=int(op1), int(op2)
                                    return get_operator_fn(oper)(op1, op2)
                                speak("your result is")
                                print(eval_binary_expr(*(my_string.split())))
                                speak(eval_binary_expr(*(my_string.split())))
                        except:
                            speak("try again")
                            
                    elif 'open notepad' in self.query:
                        notepad_path="C:\\Windows\\System32\\notepad.exe"
                        os.startfile(notepad_path)
                    elif 'open camera' in self.query:
                        cap=cv2.VideoCapture(0)
                        while True:
                            ret, frame = cap.read()
                            cv2.imshow('frame', frame)
                            if cv2.waitKey(1) & 0xff ==ord('c'):
                                break
                        
                        cap.release()
                        cv2.destroyAllWindows()   

                    elif 'play music' in self.query:
                        music_dir='C:\\Users\\Default\\Music'   
                        songs=os.listdir(music_dir)
                        os.startfile(os.path.join(music_dir, random.choice(songs)))
                    
                    elif "translate" in self.query:
                        speak("Sure, please say the phrase you want to translate.")
                        phrase_to_translate = self.takeCommand().lower()
                        speak("To which language would you like to translate it?")
                        target_language = self.takeCommand().lower()
                        translated_phrase = translate_text(phrase_to_translate, target_language)
                        speak(f"The translation is: {translated_phrase}")

                    elif 'joke' in self.query:
                        speak(pyjokes.get_joke())

                    elif 'you can sleep'in self.query:
                        speak("thanks for using me sir , have a good day , Bye")
                        sys.exit()

                    elif 'youtube' in self.query:
                        speak("This is what i found on youtube")
                        self.query =self.query.replace("youtube search","")
                        self.query =self.query.replace("youtube","")
                        self.query =self.query.replace("friday" ,"")
                        web="https://www.youtube.com/results?search_self.query=" + self.query
                        webbrowser.open(web)
                        pywhatkit.playonyt(self.query)
                        speak("done, sir")

                    elif 'google' in self.query:
                        import wikipedia as googlescrap
                        self.query= self.query.replace("friday","")
                        self.query= self.query.replace("google search","")
                        self.query= self.query.replace("google","")
                        speak("this is what i found on google")

                        try:
                            pywhatkit.search(self.query)
                            result =googlescrap.summary(self.query,1)
                            speak(result)
                        except:
                            speak("no speakable output available")

                    elif "how much power left" in self.query or "how much power we have" in self.query or "battery" in self.query:
                        
                        battery=psutil.sensors_battery()
                        percentage=battery.percent
                        speak(f"Sir our system have {percentage} percent battery")

                    elif 'weather' in self.query:
                        speak("Sure, please specify the city.")
                        city = self.takeCommand().lower()
                        api_key = '0da807011bfc48b519463a35f102db26'
                        weather_info = get_weather(api_key, city)
                        speak(weather_info)

                    elif "internet speed" in self.query:
                        st=speedtest.Speedtest()
                        dl=st.download()
                        up=st.upload()
                        print(f"sir we have {dl} bit per second downloading speed and {up} bit per second uploading speed")
                        speak(f"sir we have {dl} bit per second downloading speed and {up} bit per second uploading speed")
                    
                    elif "screenshot" in self.query:
                        try:
                            image = pyscreenshot.grab()
                            image.show()
                            a = datetime.datetime.now()
                            if not os.path.exists("screenshot"):
                                os.mkdir("screenshot")
                            image.save(f"screenshot/{a.day, a.month, a.year}_screenshot.png")
                            print(f"Screenshot taken: screenshot/{a.day, a.month, a.year}_screenshot.png ")
                        except Exception as e:
                            print(e)
                            speak("unable to take screenshot")

                    elif "convert" in self.query:
                        speak("Sure, please specify the unit conversion you want to perform.")
                        conversion_query = self.takeCommand().lower()

                        conversion_result = self.convert_units(conversion_query)
                        speak(f"The result of the unit conversion is: {conversion_result}")
                        print(f"Unit Conversion Result: {conversion_result}")

                     
                    elif 'remember that' in self.query:
                        speak("what should i remember sir")
                        rememberMessage = self.takeCommand()
                        speak("you said me to remember"+rememberMessage)
                        remember = open('data.txt', 'w')
                        remember.write(rememberMessage)
                        remember.close()

                    elif 'do you remember anything' in self.query:
                        remember = open('data.txt', 'r')
                        speak("you said me to remember that" + remember.read())

                    elif 'volume up' in self.query:
                        pyautogui.press("volumeup")

                    elif 'volume down' in self.query:
                        pyautogui.press("volumedown")

                    elif 'volume mute' in self.query or 'mute' in self.query:
                        pyautogui.press("volumemute")
                    
                    elif 'news' in self.query:
                        speak("Sure, let me fetch the latest news for you.")
                        api_key = '058d28c50920436e9adedf847531ec03'  
                        news_info = get_news(api_key)
                        if news_info:
                            for news in news_info:
                                print(news)
                                speak(news)
                        else:
                            speak("Sorry, I couldn't fetch the news at the moment.")
                    elif 'read pdf' in self.query:
                        pdf_directory ="C:\\Users\\Varun\\OneDrive\\Documents"
                        speak("Sure, please provide the path to the PDF file without extension")
                        pdf_file_name = self.takeCommand().lower()
                        pdf_path = os.path.join(pdf_directory, f"{pdf_file_name}.pdf")
                        if os.path.isfile(pdf_path):
                            speak(f"Attempting to read the PDF at the path: {pdf_file_name}")
                            read_pdf(pdf_path)
                        else:
                            speak("No valid PDF found with that name. Please try again.")

startExecution = MainThread()       
class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.startTask)
        self.ui.pushButton_2.clicked.connect(self.close)

    def startTask(self):
        self.ui.movie=QtGui.QMovie("../Pictures/MImN.gif")
        self.ui.label.setMovie(self.ui.movie)
        self.ui.movie.start()
        self.ui.movie=QtGui.QMovie("../Pictures/ai2.gif")
        self.ui.label_2.setMovie(self.ui.movie)
        self.ui.movie.start()
        self.ui.movie=QtGui.QMovie("../Pictures/init.gif")
        self.ui.label_3.setMovie(self.ui.movie)
        self.ui.movie.start()
        self.ui.movie=QtGui.QMovie("../Pictures/source.gif")
        self.ui.label_4.setMovie(self.ui.movie)
        self.ui.movie.start()
        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start(1000)
        startExecution.start()

    def showTime(self):
        current_time=QTime.currentTime()
        current_date = QDate.currentDate()
        label_time = current_time.toString('hh:mm:ss')
        label_date = current_date.toString(Qt.ISODate)
        self.ui.textBrowser.setText(label_date)
        self.ui.textBrowser_2.setText(label_time)

app = QApplication(sys.argv)
friday = Main()
friday.show()
exit(app.exec_())

