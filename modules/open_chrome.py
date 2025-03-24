import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.settings import generated_resume_path
from config.secrets import username, password
from config.personals import first_name, middle_name, last_name

# ✅ Primary method: Always install the latest ChromeDriver
try:
    service = Service(ChromeDriverManager().install())  # Automatically installs the correct ChromeDriver version
    print("✅ Using ChromeDriverManager().install() to get the latest compatible version.")
except Exception as e:
    print(f"⚠️ Failed to use ChromeDriverManager().install(): {e}")
    
    # ✅ Fallback: Use manually downloaded ChromeDriver if installation fails
    chromedriver_path = os.path.join(os.getcwd(), 'setup', 'chromedriver', 'chromedriver.exe')
    if os.path.exists(chromedriver_path):
        service = Service(executable_path=chromedriver_path)
        print("✅ Fallback: Using manually downloaded ChromeDriver.")
    else:
        print("❌ No valid ChromeDriver found. Please check installation.")

# ✅ Initialize WebDriver globally
driver = None  

# ✅ Generate the resume filename dynamically
resume_name = f"{first_name} {middle_name + ' ' if middle_name.strip() else ''}{last_name}_resume.pdf"
resume_path = os.path.join(generated_resume_path, resume_name)

# ✅ Check if the resume exists
if os.path.exists(resume_path):
    print(f"✅ Resume found: {resume_path}")
else:
    print(f"❌ Resume not found in {generated_resume_path}! Ensure the file exists.")

try:
    # ✅ Launch ChromeDriver
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    print("✅ ChromeDriver launched successfully.")

    # ✅ Open LinkedIn login page
    driver.get("https://www.linkedin.com/login")
    print("🔵 Opened LinkedIn login page.")

    # ✅ Wait for the username field and enter login details
    wait = WebDriverWait(driver, 30)
    
    username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
    username_field.clear()
    username_field.send_keys(username)
    print(f"🔵 Entered username: {username}")

    password_field = driver.find_element(By.ID, "password")
    password_field.clear()
    password_field.send_keys(password)
    print("🔵 Entered password.")

    # ✅ Click the login button
    login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
    login_button.click()
    print("🔵 Clicked login button.")

    # ✅ Wait for successful login
    wait.until(EC.url_contains("feed"))
    print("✅ Logged in successfully.")

except Exception as e:
    print(f"❌ Error launching Chrome or logging in: {e}")

# ✅ Ensure `driver` is initialized even if login fails
if driver is None:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# ✅ Do NOT close the browser automatically
# This allows `runAiBot.py` to use the same session
