import tkinter as tk
from tkinter import filedialog, messagebox
import joblib
import speech_recognition as sr
from pydub import AudioSegment
import os

# Load your trained model
model = joblib.load("scam_model (1).pkl")

# Function to check text
def check_text():
    text = text_entry.get("1.0", tk.END).strip()
    
    if not text:
        messagebox.showwarning("Warning", "Please enter some text")
        return
    
    prediction = model.predict([text])
    
    if prediction[0] == 1:
        result_label.config(text="This is likely a SCAM/SPAM message", fg="red")
    else:
        result_label.config(text="This message appears SAFE", fg="green")


# Function to analyze audio
def analyze_audio():
    file_path = filedialog.askopenfilename(
        filetypes=[("Audio Files", "*.wav *.mp3")]
    )
    
    if not file_path:
        return
    
    try:
        # Convert to wav if needed
        sound = AudioSegment.from_file(file_path)
        sound.export("converted.wav", format="wav")
        
        recognizer = sr.Recognizer()
        
        with sr.AudioFile("converted.wav") as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
        
        messagebox.showinfo("Transcribed Text", text)
        
        prediction = model.predict([text])
        
        if prediction[0] == 1:
            result_label.config(text="This call appears to be SCAM", fg="red")
        else:
            result_label.config(text="This call appears SAFE", fg="green")
            
        os.remove("converted.wav")
        
    except Exception as e:
        messagebox.showerror("Error", f"Could not process audio\n{e}")


# ---------------- UI ---------------- #

root = tk.Tk()
root.title("Senior Citizen Scam Detection AI")
root.geometry("500x400")

title = tk.Label(root, text="🛡 Scam Detection System", font=("Arial", 16, "bold"))
title.pack(pady=10)

# Text input
tk.Label(root, text="Enter Suspicious Message:").pack()
text_entry = tk.Text(root, height=5, width=50)
text_entry.pack(pady=5)

tk.Button(root, text="Check Text", command=check_text).pack(pady=5)

# Audio button
tk.Button(root, text="Upload & Analyze Audio", command=analyze_audio).pack(pady=10)

# Result label
result_label = tk.Label(root, text="", font=("Arial", 12, "bold"))
result_label.pack(pady=20)

root.mainloop()