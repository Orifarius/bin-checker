import os
import requests
from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash

app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY', '3XhdworgQzaiC3N3yocQ')

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

APP_PASSWORD = os.environ.get('APP_PASSWORD', 'admin')
HANDY_API_TOKEN = os.environ.get('HANDY_API_TOKEN', '')

def get_card_icon(scheme):
    scheme = str(scheme).lower()
    if 'visa' in scheme: return 'fa-cc-visa'
    if 'master' in scheme: return 'fa-cc-mastercard'
    if 'amex' in scheme: return 'fa-cc-amex'
    if 'discover' in scheme: return 'fa-cc-discover'
    if 'jcb' in scheme: return 'fa-cc-jcb'
    if 'diners' in scheme: return 'fa-cc-diners-club'
    return 'fa-credit-card'

def check_bin(bin_number):
    url = f"https://data.handyapi.com/bin/{bin_number}"
    headers = {}
    if HANDY_API_TOKEN:
        headers['Authorization'] = f"Bearer {HANDY_API_TOKEN}"
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("Status") == "NOT FOUND":
                 return {"error": "Nie znaleziono takiego numeru BIN."}
            data['icon'] = get_card_icon(data.get('Scheme', ''))
            return data
        elif response.status_code == 401:
            return {"error": "Błąd autoryzacji API."}
        elif response.status_code == 404:
            return {"error": "Nie znaleziono danych (404)."}
        else:
            return {"error": f"Błąd API: {response.status_code}"}
    except Exception as e:
        return {"error": f"Błąd połączenia: {str(e)}"}

@app.route('/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    
    error = None
    if request.method == 'POST':
        if request.form.get('password') == APP_PASSWORD:
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = 'Nieprawidłowe hasło.'
            
    return render_template('login.html', error=error)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    result = None
    searched_bin = ""
    
    if request.method == 'POST':
        raw_bin = request.form.get('bin_code', '')
        bin_clean = ''.join(filter(str.isdigit, raw_bin))
        searched_bin = raw_bin
        
        if len(bin_clean) >= 6:
            result = check_bin(bin_clean[:8]) 
        else:
            flash("Wpisz minimum 6 cyfr.")

    return render_template('index.html', result=result, searched_bin=searched_bin)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)