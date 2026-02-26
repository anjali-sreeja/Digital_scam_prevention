"""
STEP 1 — DATA PREPARATION (SMS + Voice Transcript Dataset)
============================================================
File    : data/prepare_data.py
Command : python data/prepare_data.py

Kya karta hai:
━━━━━━━━━━━━━━
1. spam.csv (UCI — 5572 real SMS) load karta hai
2. Extra Indian SMS scam patterns add karta hai
3. NEW: Digital Arrest voice call TRANSCRIPTS add karta hai
   - English digital arrest scripts
   - Hindi digital arrest scripts (Roman transliteration)
   - Kannada digital arrest scripts (Roman transliteration)
   - student_true_positive.txt, student_true_positive_kannada.txt
   - student_false_negative.txt (soft-spoken scam — harder to detect)
4. Shuffle + save → data/sms_dataset.csv

Why voice transcripts in SMS dataset?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voice calls detect karne ke liye:
  Audio → Whisper/Google STT → transcript text → SAME ML model
So model ko voice call patterns bhi seekhne chahiye.
Yeh dataset dono SMS aur voice transcripts handle karta hai.

Digital Arrest Scam kya hai?
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scammer police/CBI/customs officer banta hai.
Kehta hai: "Your Aadhaar/PAN is linked to a crime, you are under DIGITAL ARREST"
Victim ko phone pe rokta hai, transfer karwata hai.
2024 mein India mein Rs 120 crore+ ka fraud hua is scam se.
"""

import csv
import os
import pandas as pd


# ─── 1. EXTRA SMS SCAM MESSAGES ──────────────────────────────────────────────

EXTRA_SPAM_SMS = [
    # Banking fraud
    "ALERT: Your SBI debit card was used at AMAZON for Rs.7542. If NOT done by you CALL IMMEDIATELY 1800-XXX-XXXX or your account will be BLOCKED",
    "Dear Customer, your KYC is incomplete. Your account will be suspended within 24 hours. Update your KYC now: http://sbi-kyc-update.tk/verify",
    "Income Tax Refund of Rs 15,490 is approved. Provide your bank account details at http://incometax-refund.ml to receive refund",
    "Congratulations! You have won Rs 50,00,000 (50 Lakh) in our lucky draw! Call 9876543210 to claim. Offer expires in 24 hours",
    "Your UPI ID has been deactivated due to suspicious activity. Reply with your UPI PIN to reactivate immediately",
    "FREE: 500 MB extra data added to your Jio account. Click http://jio-free-data.cf to activate within next 2 hours",
    "LOTTERY WIN: You have been selected as the winner of KBC international lottery worth Rs 25 Lakh. Claim: kbclottery@gmail.com",
    "Your AADHAAR card is linked to 3 suspicious mobile numbers. To disconnect call cybercrime helpline 1800-XXX-XXXX now",
    "SBI ALERT: We noticed suspicious login to your NetBanking. Verify your identity immediately: http://192.168.1.100/sbi/verify",
    "Dear Customer, HDFC Bank: Your account will be blocked due to non-updation of PAN. Update: http://hdfc-pan-update.gq",
    "Your EPF account shows unclaimed amount of Rs 2,35,000. To claim provide Aadhaar OTP. Reply OTP to 9876543210",
    "PAYTM ALERT: Your wallet account suspended. KYC verification pending. Share OTP received on your mobile to restore",
    "Amazon Quiz: You are today's winner! Claim your iPhone 14 worth Rs 79,990 by clicking: http://amazon-quiz-prize.tk",
    "TRAI: Your mobile number will be disconnected in 2 hours due to illegal activities. Press 9 to talk to officer",
    "Pm Kisan Yojana: Rs 6000 has been approved for you. Click link to claim: http://pmkisan-claim.cf Send Aadhaar number",
    "WhatsApp Gold: Upgrade to WhatsApp Gold for exclusive features. Click http://whatsapp-gold-upgrade.tk to install now",
    "FedEx: Your package is held at customs. Pay Rs 1,200 customs duty at http://fedex-customs.tk to release your parcel",
    "Your credit card ending 4521 will be blocked due to KYC update. Call 1800-XXX-XXXX or update at http://icici-kyc.ml",
    "Narendra Modi Government Scheme: Get free gas connection & Rs 1500 monthly. Send Aadhaar and bank details to 9876543210",
    "URGENT: Arrest warrant has been issued against your PAN card number. Call CBI officer on 011-XXXXXXXX immediately to avoid arrest",
]

EXTRA_HAM_SMS = [
    "Kal office late hoga. Meeting 7 baje tak chalegi. Khana mat wait karna.",
    "Aaj baarish bahut tez hai. Umbrella leke jaana. Main office se call karunga.",
    "Mom, aaj dinner mein kya banega? Main 8 baje tak aa jaunga.",
    "Bhai, kal cricket ka match dekhne chalein? Ticket mila hai CSK vs MI ka.",
    "Your OTP for SBI net banking login is 847291. Valid for 10 minutes. Do not share with anyone.",
    "Your order #ORD5634 from Flipkart has been dispatched. Expected delivery: Tomorrow.",
    "Flight AI202 to Delhi is on time. Boarding begins at 14:30 at gate 5B. Have a pleasant journey.",
    "Reminder: Your electricity bill of Rs 1,450 is due on 15th August. Pay to avoid disconnection.",
    "Your vaccination appointment is confirmed for Saturday 10 AM at City Hospital, Hall 3.",
    "Hi! Are you free this Sunday? We are planning a small birthday party for Priya.",
    "Your prescription is ready for pickup at MedPlus Pharmacy, Andheri West.",
    "Hey just wanted to say happy birthday! Hope you have a wonderful day ahead.",
    "Mom surgery went well. Doctor says she can come home by Thursday. Don't worry.",
    "Please bring milk and bread on your way home tonight. Also some bananas if you see.",
    "Your interview is scheduled for Monday at 11am at their Bandra office. Bring all originals.",
    "We reached home safely. Thanks for the wonderful dinner and hospitality!",
    "The meeting has been rescheduled to Wednesday 3 PM. Same conference room.",
    "Kal school chhutti hai. Principal ne COVID precaution ke liye announcement ki hai.",
    "Bhai, Rs 500 bhej de please. Forgot my wallet at home, need to pay for lunch.",
    "Good morning! Don't forget your 8 AM diabetes medicine. Love you, take care.",
    "Your HDFC Bank account XXXX1234: Rs 5,000 debited on 12-Aug towards EMI. Available bal: Rs 23,450.",
    "IRCTC: Your ticket PNR 2345678901 for 12951 Mumbai Rajdhani is confirmed. Coach: B2, Berth: 32.",
    "Swiggy: Your order from Dominos is on the way! Estimated delivery: 30 minutes.",
    "PhonePe: Rs 200 received from Amit Kumar. UPI Ref: 234567890123. Balance: Rs 1,450.",
    "Ola: Your driver Ramesh will arrive in 3 minutes. Car: MH 01 AB 1234, Swift Dzire.",
]


# ─── 2. DIGITAL ARREST VOICE TRANSCRIPTS ─────────────────────────────────────
# Yeh actual voice calls ke transcripts hain (audio_samples/ folder mein hain)
# Model inhe seekhega taaki voice call transcripts bhi detect ho sakein
#
# Source labels:
#   TRUE_POSITIVE  = actual scam call (SPAM)
#   FALSE_NEGATIVE = soft-spoken scam, harder to detect (still SPAM)
#   TRUE_NEGATIVE  = legitimate call (HAM)

DIGITAL_ARREST_SPAM = [

    # ── English — True Positive (direct, obvious) ──────────────────────────
    # File: true_positive_digital_arrest_english_sample.mp3, student_true_positive.txt
    "Hello. This is Inspector Rao from the Cyber Crime Unit. Your Aadhaar details are linked to a serious digital case, and you are currently under digital arrest. You must remain on this call and follow instructions, otherwise the matter will be escalated for immediate legal action.",

    "This is a call from the Central Bureau of Investigation. We have detected illegal activity linked to your Aadhaar number. You are now under digital arrest. Do not disconnect this call or we will send officers to your address immediately.",

    "I am calling from the Ministry of Home Affairs cyber division. Your mobile number has been flagged for suspicious transactions. You are placed under digital arrest pending verification. Share your bank details to clear your name.",

    "Hello, I am DCP Sharma from the National Cyber Crime Reporting Portal. Your PAN card has been used in a money laundering case. You are under digital surveillance and digital arrest. Cooperate immediately or face arrest within 2 hours.",

    "This is a notice from the Enforcement Directorate. Multiple transactions linked to your Aadhaar show involvement in hawala operations. You are under digital arrest. Transfer Rs 50,000 to our secure government account for temporary clearance.",

    "Attention. You have been identified in connection with a cybercrime investigation. The Central Bureau of Investigation has placed you under digital arrest. Stay on the line and do not contact anyone or your bail application will be rejected.",

    "I am Inspector Verma from the Crime Branch. We have a warrant for your digital arrest issued by the High Court. Your Aadhaar is linked to 3 shell companies involved in tax fraud. Provide your account details for immediate verification.",

    "This call is from TRAI Cybercrime Division. Your phone number is being used for illegal activities. As per section 66 of IT Act, you are placed under digital arrest. If you disconnect, we will file an FIR against you.",

    # ── Hindi — Digital Arrest (from Hindi audio files) ───────────────────
    # Files: Digital_Arrest_Hindi_1.m4a, Digital_Arrest_Hindi_2.mp3, Digital_Arrest_Hindi_3.m4a
    "Namaste. Main CBI se Inspector Suresh bol raha hoon. Aapka Aadhaar number ek galit digital case mein link hua hai. Aap abhi digital arrest mein hain. Kripya phone mat kaatna, warna turant legal action hoga.",

    "Yeh CBI ka official notice hai. Aapka PAN card money laundering mein use hua hai. Aap digital arrest ke antargat hain. Abhi apna bank account number aur OTP share karein, warna 2 ghante mein griftari hogi.",

    "Main Cyber Crime Unit se bol raha hoon. Aapke naam pe 3 illegal SIM card hain. Yeh ek sangin apraadh hai. Aap digital arrest mein hain. Phone mat kaatna. Apna Aadhaar aur bank details dena hoga clearance ke liye.",

    "Suno. Aapka mobile number hawala transactions mein involved hai. Enforcement Directorate ne aapke upar digital arrest ka order jaari kiya hai. Agar aap sahyog nahi karenge toh police aapke ghar aayegi aadhe ghante mein.",

    "Yeh Enforcement Directorate ka important call hai. Aapke account mein suspicious transactions hain. Section 420 ke antargat aap digital arrest mein hain. Rs 1 lakh government secure account mein transfer karo, FIR band ho jayegi.",

    "Main National Cyber Crime Helpline se Inspector Sharma bol raha hoon. Aapka Aadhaar card ek drug trafficking network se linked hai. Aap abhi se digital arrest mein hain. Agar call kaata toh aapke against warrant jaari hoga.",

    # ── Kannada — Digital Arrest ────────────────────────────────────────────
    # File: true_positive_digital_arrest_kannada_sample.mp3, student_true_positive_kannada.txt
    "Namaskara. Nanu Cyber Crime Ghatakada Inspector Rao matanaadutidhene. Nimma Aadhaar vivaragalu gambhira digital prakaranakke sambandhisive, mattu neevu prastutha digital bandhanadalli iddiri. Neevu ee karelalli ulidu suchanegalannu anusarisabeku, illadidhare takshana kanoonakriyakke vishayavannu hechisilaguvudu.",
    # Native Kannada script (student_true_positive_kannada.txt)
    "ನಮಸ್ಕಾರ. ನಾನು ಸೈಬರ್ ಕ್ರೈಮ್ ಘಟಕದ ಇನ್ಸ್ ಪೆಕ್ಟರ್ ರಾವ್ ಮಾತನಾಡುತ್ತಿದ್ದೇನೆ. ನಿಮ್ಮ ಆಧಾರ್ ವಿವರಗಳು ಗಂಭೀರ ಡಿಜಿಟಲ್ ಪ್ರಕರಣಕ್ಕೆ ಸಂಬಂಧಿಸಿವೆ, ಮತ್ತು ನೀವು ಪ್ರಸ್ತುತ ಡಿಜಿಟಲ್ ಬಂಧನದಲ್ಲಿದ್ದೀರಿ. ನೀವು ಈ ಕರೆಯಲ್ಲಿ ಉಳಿದು ಸೂಚನೆಗಳನ್ನು ಅನುಸರಿಸಬೇಕು.",

    "Namaskara. Nanu CBI Cyber Division Inspector Krishnaiah matanaadutidhene. Nimage serious notice. Nimma mobile number illegal transactions mele use aagide. Neevu digital arrest mele iddiri. Nimma bank details kodi namma investigation help maadi, illandre 1 gandeyalli police nimma manege baruttare.",

    "Ee call Central Bureau of Investigation ninda. Nimma Aadhaar number money laundering case nalli ide. Neevu digital arrest mele iddiri. Call cut maadabedi. Nimma account number mattu OTP kodi turant clearance siguttade.",

    # ── False Negative — Soft spoken, no obvious keywords ──────────────────
    # File: student_false_negative.txt, digital_arrest_english_sample.mp3
    # These are STILL SCAM but use vague language to avoid detection
    "Good afternoon. This is a verification officer from the Compliance Review Desk from Customs department regarding a routine internal profile check linked to your identity record. There is a minor inconsistency that needs to be resolved today to avoid automated system escalation, so we request that you remain available on this call until the review is completed.",

    "Hello, I am calling from the Federal Verification Department. We are conducting a mandatory identity audit this week. Your profile has been flagged for a secondary review. Please cooperate with us and stay on the line. This is for your own protection and to avoid any unintended consequences.",

    "This is a call from the Regulatory Compliance Office. We have received a complaint registered under your identity number. For resolution, we require your cooperation. Please do not disconnect. A supervisor will join this call in a moment to guide you through the verification process.",

    "Good morning. I am from the Government Revenue Department. We have noticed some discrepancies in your tax filing history. To prevent automatic penalties from being applied to your account, please remain on the call and we will walk you through a quick clearance procedure.",

    "Hello. This is the Income Tax grievance cell calling. We have detected a mismatch in your PAN records which requires immediate attention. If not resolved by today, your accounts may be frozen under standard regulatory procedure. Please cooperate with our officer who will guide you.",

    # ── More obvious English digital arrest variants ────────────────────────
    "You are being monitored by the cyber police. Your IP address has been tracked engaging in illegal downloads and financial fraud. This is an official digital arrest notice. Do not use any other device. Stay on line for verification or a physical warrant will be issued.",

    "This is the Cyber Crimes Division of the Mumbai Police. We have intercepted communications linking your number to an international scam network. You are under digital arrest effective immediately. Cooperate fully or face charges under IPC section 420 and IT Act.",
]

DIGITAL_ARREST_HAM = [
    # Legitimate calls from real institutions (not scam)
    "Hello, this is Dr. Sharma from City Hospital calling to confirm your appointment tomorrow at 10 AM. Please bring your previous reports. Call us back at 080-XXXX-XXXX if you need to reschedule.",

    "Hi, this is Rahul from HDFC Bank customer service. I am calling regarding your home loan application submitted last week. We need one more document — your latest salary slip. Please visit the branch or email it to us.",

    "Good morning, this is Priya from Infosys HR department. We are happy to inform you that your application has been shortlisted. Your interview is scheduled for Monday at 11 AM at our Bangalore office. Please confirm your attendance.",

    "Hello, I am calling from the Indian Embassy regarding your visa application. Your documents have been processed and your visa is ready for collection. Please visit our office on any working day between 9 AM and 5 PM.",

    "This is a reminder call from Apollo Pharmacy. Your prescription medicine is ready for pickup. Our store is open from 8 AM to 10 PM. You can also request home delivery by calling back on this number.",

    "Hello, I am calling from Tata Consultancy Services recruitment team. This is regarding your job application. We would like to schedule a technical interview with you. Are you available this week?",

    "Namaste, yeh SBI ke genuine customer care se call hai. Aapne naya account open karne ke liye application di thi. Aapka account ready hai. Branch mein aakar passbook aur debit card collect kar lijiye.",

    "Hi this is Maya calling from Practo. Your doctor consultation for tomorrow at 4 PM is confirmed with Dr. Nair. The clinic address is MG Road, second floor. Do carry your insurance card.",
]


# ─── MAIN FUNCTION ────────────────────────────────────────────────────────────

def prepare_dataset(
    spam_csv_path: str = "data/spam.csv",
    output_path: str = "data/sms_dataset.csv"
):
    """
    Combines:
    1. UCI SMS Spam dataset (spam.csv) — 5572 messages
    2. Extra Indian SMS scam patterns — 20 spam + 25 ham
    3. Digital Arrest voice transcripts — 28 spam + 8 ham

    Total expected: ~5573+ messages with strong digital arrest coverage.
    """

    print("=" * 60)
    print("  Guardian Angel — Data Preparation (SMS + Voice)")
    print("=" * 60)

    # ── Load spam.csv ─────────────────────────────────────────
    print(f"\n📂 Loading UCI SMS dataset: {spam_csv_path}")
    df_uci = pd.read_csv(
        spam_csv_path,
        encoding='latin-1',
        usecols=[0, 1],
        names=['label', 'message'],
        header=0
    )
    df_uci.dropna(inplace=True)
    df_uci['label_num'] = df_uci['label'].map({'ham': 0, 'spam': 1})

    print(f"   UCI rows  : {len(df_uci)}")
    print(f"   ham       : {(df_uci['label']=='ham').sum()}")
    print(f"   spam      : {(df_uci['label']=='spam').sum()}")

    # ── Build extra rows ──────────────────────────────────────
    extra_rows = []
    for msg in EXTRA_SPAM_SMS:
        extra_rows.append({'label': 'spam', 'label_num': 1, 'message': msg, 'source': 'indian_sms'})
    for msg in EXTRA_HAM_SMS:
        extra_rows.append({'label': 'ham',  'label_num': 0, 'message': msg, 'source': 'indian_sms'})
    for msg in DIGITAL_ARREST_SPAM:
        extra_rows.append({'label': 'spam', 'label_num': 1, 'message': msg, 'source': 'digital_arrest_voice'})
    for msg in DIGITAL_ARREST_HAM:
        extra_rows.append({'label': 'ham',  'label_num': 0, 'message': msg, 'source': 'digital_arrest_voice'})

    df_extra = pd.DataFrame(extra_rows)

    # Add source column to UCI data too
    df_uci['source'] = 'uci_sms'

    print(f"\n📝 Extra data added:")
    print(f"   Indian SMS spam         : {len(EXTRA_SPAM_SMS)}")
    print(f"   Indian SMS ham          : {len(EXTRA_HAM_SMS)}")
    print(f"   Digital Arrest SPAM     : {len(DIGITAL_ARREST_SPAM)}")
    print(f"   Digital Arrest HAM      : {len(DIGITAL_ARREST_HAM)}")

    # ── Combine & shuffle ─────────────────────────────────────
    df_final = pd.concat([df_uci, df_extra], ignore_index=True)
    df_final = df_final.sample(frac=1, random_state=42).reset_index(drop=True)

    # ── Save ──────────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    df_final[['label', 'label_num', 'message', 'source']].to_csv(
        output_path, index=False, encoding='utf-8'
    )

    print(f"\n✅ Dataset saved: {output_path}")
    print(f"   Total messages  : {len(df_final)}")
    print(f"   Total ham       : {(df_final['label']=='ham').sum()}")
    print(f"   Total spam      : {(df_final['label']=='spam').sum()}")
    print(f"\n   By source:")
    print(df_final.groupby(['source','label']).size().to_string())
    print(f"\n▶  Next: python models/train.py")


if __name__ == "__main__":
    prepare_dataset()
