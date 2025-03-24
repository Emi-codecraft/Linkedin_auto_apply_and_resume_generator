# Imports
import os
import csv
import re
import pyautogui

from random import choice, shuffle, randint
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchWindowException, ElementNotInteractableException

from config.personals import *
from config.questions import *
from config.search import *
import importlib
import config.secrets
importlib.reload(config.secrets)  # Ensure the latest secrets are loaded
from config.secrets import use_AI, username, password

from config.settings import *

from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
from modules.validator import validate_config
from modules.ai.openaiConnections import *

from typing import Literal




pyautogui.FAILSAFE = False




actions = ActionChains(driver)  




#< Global Variables and logics

if run_in_background == True:
    pause_at_failed_question = False
    pause_before_submit = False
    run_non_stop = False

first_name = first_name.strip()
middle_name = middle_name.strip()
last_name = last_name.strip()
full_name = first_name + " " + middle_name + " " + last_name if middle_name else first_name + " " + last_name

useNewResume = True
randomly_answered_questions = set()

tabs_count = 1
easy_applied_count = 0
external_jobs_count = 0
failed_count = 0
skip_count = 0
dailyEasyApplyLimitReached = False

re_experience = re.compile(r'[(]?\s*(\d+)\s*[)]?\s*[-to]*\s*\d*[+]*\s*year[s]?', re.IGNORECASE)

desired_salary_lakhs = str(round(desired_salary / 100000, 2))
desired_salary_monthly = str(round(desired_salary/12, 2))
desired_salary = str(desired_salary)

current_ctc_lakhs = str(round(current_ctc / 100000, 2))
current_ctc_monthly = str(round(current_ctc/12, 2))
current_ctc = str(current_ctc)

notice_period_months = str(notice_period//30)
notice_period_weeks = str(notice_period//7)
notice_period = str(notice_period)

aiClient = None
#>
import os
from config.settings import generated_resume_path

# Set the expected resume filename (modify if needed)
resume_filename = "John Doe Smith_resume.pdf"
resume_path = os.path.join(generated_resume_path, resume_filename)

# Check if the resume exists
if os.path.exists(resume_path):
    print(f"✅ Resume found at: {resume_path}")
else:
    print(f"❌ Resume NOT found in expected path: {resume_path}\nPlease check your resume generation settings!")
      # Stop execution if resume is missing



#< Login Functions
def is_logged_in_LN() -> bool:
    '''
    Function to check if user is logged-in in LinkedIn
    * Returns: `True` if user is logged-in or `False` if not
    '''
    if driver.current_url == "https://www.linkedin.com/feed/": return True
    if try_linkText(driver, "Sign in"): return False
    if try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]'):  return False
    if try_linkText(driver, "Join now"): return False
    print_lg("Didn't find Sign in link, so assuming user is logged in!")
    return True


def login_LN() -> None:
    '''
    Logs into LinkedIn using the username and password from secrets.py.
    '''
    driver.get("https://www.linkedin.com/login")

    try:
        wait = WebDriverWait(driver, 10)  # Wait for elements to be available

        # Locate and enter username
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        driver.execute_script("arguments[0].value = '';", username_field)  # Clear field using JavaScript
        username_field.send_keys(username)  # Enter actual username

        # Locate and enter password
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
        driver.execute_script("arguments[0].value = '';", password_field)  # Clear field using JavaScript
        password_field.send_keys(password)

        # Click the Sign In button
        sign_in_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
        sign_in_button.click()

        # Wait for successful login
        wait.until(EC.url_contains("feed"))
        print("✅ Login successful!")

    except Exception as e:
        print("❌ Login failed! Please check your credentials.")
        print(e)




def get_applied_job_ids() -> set:
    '''
    Function to get a `set` of applied job's Job IDs
    * Returns a set of Job IDs from existing applied jobs history csv file
    '''
    job_ids = set()
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                job_ids.add(row[0])
    except FileNotFoundError:
        print_lg(f"The CSV file '{file_name}' does not exist.")
    return job_ids



from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def set_search_location(driver, actions, search_location):
    """
    Function to set the job search location in LinkedIn's job search page.
    
    :param driver: Selenium WebDriver instance
    :param actions: Selenium ActionChains instance
    :param search_location: The location to set in the LinkedIn job search
    """
    if not search_location.strip():
        print_lg("⚠️ Search location input was not provided! Using the default location.")
        return  # Exit function if no location is given

    try:
        print_lg(f'🔍 Setting search location as: "{search_location.strip()}"')

        # Wait for the search location input to be interactable
        search_location_ele = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(("xpath", "//input[@aria-label='City, state, or zip code' and not(@disabled)]"))
        )

        # Clear and enter the new search location
        search_location_ele.clear()
        search_location_ele.send_keys(search_location.strip())
        search_location_ele.send_keys(Keys.RETURN)
        time.sleep(2)  # Allow time for LinkedIn to update

    except (ElementNotInteractableException, NoSuchElementException, TimeoutException):
        try:
            print_lg("⚠️ Direct input failed. Attempting alternative method...")
            actions.send_keys(Keys.TAB, Keys.TAB).perform()
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            actions.send_keys(search_location.strip()).perform()
            time.sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located(("xpath", "//button[@aria-label='Cancel']"))
            ).click()
        except Exception as e:
            print_lg(f"❌ Failed to update search location! Continuing with default location. Error: {e}")


def apply_filters(driver, actions, search_location) -> None:
    """
    Function to apply job search filters.
    
    :param driver: Selenium WebDriver instance
    :param actions: Selenium ActionChains instance
    :param search_location: The location to set in the LinkedIn job search
    """
    print("🔎 Applying job filters...")

    # Set search location correctly
    set_search_location(driver, actions, search_location)

    try:
        recommended_wait = 1 if click_gap < 1 else 0

        # Open the "All Filters" section
        all_filters_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//button[normalize-space()="All filters"]')))
        all_filters_button.click()
        buffer(recommended_wait)
        print("✅ Opened 'All Filters' menu.")

        # Apply filters one by one
        wait_span_click(driver, sort_by)
        wait_span_click(driver, date_posted)
        buffer(recommended_wait)

        multi_sel(driver, experience_level)
        multi_sel_noWait(driver, companies, actions)
        if experience_level or companies:
            buffer(recommended_wait)

        multi_sel(driver, job_type)
        multi_sel(driver, on_site)
        if job_type or on_site:
            buffer(recommended_wait)

        if easy_apply_only:
            boolean_button_click(driver, actions, "Easy Apply")

        multi_sel_noWait(driver, location)
        multi_sel_noWait(driver, industry)
        if location or industry:
            buffer(recommended_wait)

        multi_sel_noWait(driver, job_function)
        multi_sel_noWait(driver, job_titles)
        if job_function or job_titles:
            buffer(recommended_wait)

        if under_10_applicants:
            boolean_button_click(driver, actions, "Under 10 applicants")
        if in_your_network:
            boolean_button_click(driver, actions, "In your network")
        if fair_chance_employer:
            boolean_button_click(driver, actions, "Fair Chance Employer")

        wait_span_click(driver, salary)
        buffer(recommended_wait)

        multi_sel_noWait(driver, benefits)
        multi_sel_noWait(driver, commitments)
        if benefits or commitments:
            buffer(recommended_wait)

        # Click "Show Results"
        show_results_button = driver.find_element(By.XPATH, '//button[contains(@aria-label, "Apply current filters to show")]')
        show_results_button.click()
        print("✅ Applied all filters and displayed results.")

        # Pause after applying filters if needed
        global pause_after_filters
        if pause_after_filters:
            decision = pyautogui.confirm(
                "These are your configured search results and filters.\nIt is safe to change them while this dialog is open. "
                "Any changes later could result in errors and skipping this search run.",
                "Please check your results",
                ["Turn off Pause after search", "Looks good, Continue"]
            )
            if decision == "Turn off Pause after search":
                pause_after_filters = False

    except Exception as e:
        print("❌ Setting the preferences failed!")
        print(e)


def get_page_info() -> tuple[WebElement | None, int | None]:
    '''
    Function to get pagination element and current page number
    '''
    try:
        pagination_element = try_find_by_classes(driver, ["artdeco-pagination", "artdeco-pagination__pages"])
        scroll_to_view(driver, pagination_element)
        current_page = int(pagination_element.find_element(By.XPATH, "//li[contains(@class, 'active')]").text)
    except Exception as e:
        print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
        pagination_element = None
        current_page = None
        print_lg(e)
    return pagination_element, current_page



def get_job_main_details(job: WebElement, blacklisted_companies: set, rejected_jobs: set) -> tuple[str, str, str, str, str, bool]:
    '''
    # Function to get job main details.
    Returns a tuple of (job_id, title, company, work_location, work_style, skip)
    * job_id: Job ID
    * title: Job title
    * company: Company name
    * work_location: Work location of this job
    * work_style: Work style of this job (Remote, On-site, Hybrid)
    * skip: A boolean flag to skip this job
    '''
    job_details_button = job.find_element(By.TAG_NAME, 'a')  # job.find_element(By.CLASS_NAME, "job-card-list__title")  # Problem in India
    scroll_to_view(driver, job_details_button, True)
    job_id = job.get_dom_attribute('data-occludable-job-id')
    title = job_details_button.text
    title = title[:title.find("\n")]
    # company = job.find_element(By.CLASS_NAME, "job-card-container__primary-description").text
    # work_location = job.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text
    other_details = job.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle').text
    index = other_details.find(' · ')
    company = other_details[:index]
    work_location = other_details[index+3:]
    work_style = work_location[work_location.rfind('(')+1:work_location.rfind(')')]
    work_location = work_location[:work_location.rfind('(')].strip()
    
    # Skip if previously rejected due to blacklist or already applied
    skip = False
    if company in blacklisted_companies:
        print_lg(f'Skipping "{title} | {company}" job (Blacklisted Company). Job ID: {job_id}!')
        skip = True
    elif job_id in rejected_jobs: 
        print_lg(f'Skipping previously rejected "{title} | {company}" job. Job ID: {job_id}!')
        skip = True
    try:
        if job.find_element(By.CLASS_NAME, "job-card-container__footer-job-state").text == "Applied":
            skip = True
            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
    except: pass
    try: 
        if not skip: job_details_button.click()
    except Exception as e:
        print_lg(f'Failed to click "{title} | {company}" job on details button. Job ID: {job_id}!') 
        # print_lg(e)
        discard_job()
        job_details_button.click() # To pass the error outside
    buffer(click_gap)
    return (job_id,title,company,work_location,work_style,skip)


# Function to check for Blacklisted words in About Company
def check_blacklist(rejected_jobs: set, job_id: str, company: str, blacklisted_companies: set) -> tuple[set, set, WebElement] | ValueError:
    jobs_top_card = try_find_by_classes(driver, ["job-details-jobs-unified-top-card__primary-description-container","job-details-jobs-unified-top-card__primary-description","jobs-unified-top-card__primary-description","jobs-details__main-content"])
    about_company_org = find_by_class(driver, "jobs-company__box")
    scroll_to_view(driver, about_company_org)
    about_company_org = about_company_org.text
    about_company = about_company_org.lower()
    skip_checking = False
    for word in about_company_good_words:
        if word.lower() in about_company:
            print_lg(f'Found the word "{word}". So, skipped checking for blacklist words.')
            skip_checking = True
            break
    if not skip_checking:
        for word in about_company_bad_words: 
            if word.lower() in about_company: 
                rejected_jobs.add(job_id)
                blacklisted_companies.add(company)
                raise ValueError(f'\n"{about_company_org}"\n\nContains "{word}".')
    buffer(click_gap)
    scroll_to_view(driver, jobs_top_card)
    return rejected_jobs, blacklisted_companies, jobs_top_card





def get_job_description(
) -> tuple[
    str | Literal['Unknown'],
    int | Literal['Unknown'],
    bool,
    str | None,
    str | None
    ]:
    '''
    # Job Description
    Function to extract job description from About the Job.
    ### Returns:
    - `jobDescription: str | 'Unknown'`
    - `experience_required: int | 'Unknown'`
    - `skip: bool`
    - `skipReason: str | None`
    - `skipMessage: str | None`
    '''
    try:
        jobDescription = "Unknown"
        experience_required = "Unknown"
        found_masters = 0
        jobDescription = find_by_class(driver, "jobs-box__html-content").text
        jobDescriptionLow = jobDescription.lower()
        skip = False
        skipReason = None
        skipMessage = None
        for word in bad_words:
            if word.lower() in jobDescriptionLow:
                skipMessage = f'\n{jobDescription}\n\nContains bad word "{word}". Skipping this job!\n'
                skipReason = "Found a Bad Word in About Job"
                skip = True
                break
        if not skip and security_clearance == False and ('polygraph' in jobDescriptionLow or 'clearance' in jobDescriptionLow or 'secret' in jobDescriptionLow):
            skipMessage = f'\n{jobDescription}\n\nFound "Clearance" or "Polygraph". Skipping this job!\n'
            skipReason = "Asking for Security clearance"
            skip = True
        if not skip:
            if did_masters and 'master' in jobDescriptionLow:
                print_lg(f'Found the word "master" in \n{jobDescription}')
                found_masters = 2
            experience_required = extract_years_of_experience(jobDescription)
            if current_experience > -1 and experience_required > current_experience + found_masters:
                skipMessage = f'\n{jobDescription}\n\nExperience required {experience_required} > Current Experience {current_experience + found_masters}. Skipping this job!\n'
                skipReason = "Required experience is high"
                skip = True
    except Exception as e:
        if jobDescription == "Unknown":    print_lg("Unable to extract job description!")
        else:
            experience_required = "Error in extraction"
            print_lg("Unable to extract years of experience required!")
            # print_lg(e)
    finally:
        return jobDescription, experience_required, skip, skipReason, skipMessage
        


# Function to upload resume
def upload_resume(modal: WebElement, resume: str) -> tuple[bool, str]:
    try:
        modal.find_element(By.NAME, "file").send_keys(os.path.abspath(resume))
        return True, os.path.basename(default_resume_path)
    except: return False, "Previous resume"

# Function to answer common questions for Easy Apply
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from openai import OpenAI

# Ensure 'actions' is initialized in every function where needed
def initialize_selenium_objects(driver):
    """Initialize ActionChains and WebDriverWait objects."""
    actions = ActionChains(driver)
    wait = WebDriverWait(driver, 10)
    return actions, wait

# Function to answer questions using AI fallback
def ask_ai_for_answers(client, question, options=None):
    """Try to answer a question using AI. If AI fails, return a default response."""
    try:
        response = ai_answer_question(client, question, options)
        if response and isinstance(response, dict):
            return response.get("answer", "Yes")  # Use AI answer or fallback to 'Yes'
    except Exception as e:
        print(f"⚠️ AI Failed! Using default response. Error: {e}")
    return "Yes"

# Fix function to answer Easy Apply questions

from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import random

def answer_questions(modal, questions_list, work_location, client):
    """Automatically answer required (*) questions with a random number (2, 4, 3, 5) or 'Yes'."""
    
    all_questions = modal.find_elements(By.XPATH, ".//div[@data-test-form-element]")
    random_numbers = [2, 4, 3, 5]  # Possible random values for numeric inputs

    for question in all_questions:
        # Check if the question is required (*)
        required_field = question.find_elements(By.XPATH, ".//span[contains(text(), '*')]")
        if not required_field:
            continue  # Skip non-required questions

        label_text = question.find_element(By.TAG_NAME, "label").text.strip() if question.find_elements(By.TAG_NAME, "label") else "Unknown"

        # Identify input type
        text_box = question.find_elements(By.TAG_NAME, "input")
        dropdown = question.find_elements(By.TAG_NAME, "select")
        radio_buttons = question.find_elements(By.XPATH, ".//input[@type='radio']")

        # Fill text boxes: Random number for numeric fields, "Yes" for text fields
        if text_box:
            text_box[0].clear()
            if text_box[0].get_attribute("type") == "number":
                value = str(random.choice(random_numbers))  # Pick a random number
            else:
                value = "Yes"  # Use "Yes" for text inputs
            text_box[0].send_keys(value)
            questions_list.add((label_text, f"Typed '{value}'"))

        # Click the first radio button
        elif radio_buttons:
            try:
                radio_buttons[0].click()
                questions_list.add((label_text, "Clicked first radio button"))
            except Exception as e:
                print(f"⚠️ Error clicking radio button: {e}")

        # Select the first option in dropdowns
        elif dropdown:
            select = Select(dropdown[0])
            select.select_by_index(0)
            questions_list.add((label_text, "Selected first dropdown option"))

    return questions_list


def get_label_and_default_answer(question):
    """Extract label and determine default answer for required questions."""
    label = question.find_element(By.TAG_NAME, "label").text.strip() if question.find_elements(By.TAG_NAME, "label") else "Unknown"
    
    # Predefined answers for specific fields
    default_answers = {
        "phone": phone_number,
        "city": current_city,
        "experience": years_of_experience,
        "years": "3",
        "name": full_name,
        "email": email,
        "zip": "10001",
        "postal": "10001",
        "authorized": "Yes",
        "sponsorship": "No",
        "relocate": "Yes",
        "consulting": "Yes",
        "master": "No",
        "education": "Bachelor's Degree"
    }

    # ✅ Step 1: Check predefined answers
    for key, value in default_answers.items():
        if key in label.lower():
            return label, value  # Use predefined response

    # ✅ Step 2: If it's a radio button, select the first option
    if question.find_elements(By.TAG_NAME, "input") and question.get_attribute("type") == "radio":
        return label, "select_first_radio"

    # ✅ Step 3: If it's a dropdown, select the first available option
    if question.find_elements(By.TAG_NAME, "select"):
        return label, "select_first_dropdown"

    # ✅ Step 4: If none of the above, use AI for complex text-based answers
    return label, "ask_ai"


# Fix clicking issues for Next button
def click_next_button(modal, retries=3):
    """
    Click the 'Next', 'Continue', or 'Review' button safely.
    Retries up to 3 times if click fails due to interception.
    """
    for _ in range(retries):
        for btn_text in ["Next", "Continue", "Review"]:
            try:
                button = modal.find_element(By.XPATH, f".//button[contains(., '{btn_text}')]")
                button.click()
                return True
            except NoSuchElementException:
                continue
            except ElementClickInterceptedException:
                print(f"⚠️ Click Intercepted! Retrying for '{btn_text}' button...")
                buffer(1)  # Wait before retrying
    print("⚠️ Click Failed! Couldn't find Next/Continue/Review button.")
    return False


# Fix postal code defaulting
zipcode = "10001"  # New York postal code



def external_apply(pagination_element: WebElement, job_id: str, job_link: str, resume: str, date_listed, application_link: str, screenshot_name: str) -> tuple[bool, str, int]:
    '''
    Function to open new tab and save external job application links
    '''
    global tabs_count, dailyEasyApplyLimitReached
    if easy_apply_only:
        try:
            if "exceeded the daily application limit" in driver.find_element(By.CLASS_NAME, "artdeco-inline-feedback__message").text: dailyEasyApplyLimitReached = True
        except: pass
        print_lg("Easy apply failed I guess!")
        if pagination_element != None: return True, application_link, tabs_count
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3')]"))).click() # './/button[contains(span, "Apply") and not(span[contains(@class, "disabled")])]'
        wait_span_click(driver, "Continue", 1, True, False)
        windows = driver.window_handles
        tabs_count = len(windows)
        driver.switch_to.window(windows[-1])
        application_link = driver.current_url
        print_lg('Got the external application link "{}"'.format(application_link))
        if close_tabs and driver.current_window_handle != linkedIn_tab: driver.close()
        driver.switch_to.window(linkedIn_tab)
        return False, application_link, tabs_count
    except Exception as e:
        # print_lg(e)
        print_lg("Failed to apply!")
        failed_job(job_id, job_link, resume, date_listed, "Probably didn't find Apply button or unable to switch tabs.", e, application_link, screenshot_name)
        global failed_count
        failed_count += 1
        return True, application_link, tabs_count



def follow_company(modal: WebDriver = driver) -> None:
    '''
    Function to follow or un-follow easy applied companies based om `follow_companies`
    '''
    try:
        follow_checkbox_input = try_xp(modal, ".//input[@id='follow-company-checkbox' and @type='checkbox']", False)
        if follow_checkbox_input and follow_checkbox_input.is_selected() != follow_companies:
            try_xp(modal, ".//label[@for='follow-company-checkbox']")
    except Exception as e:
        print_lg("Failed to update follow companies checkbox!", e)
    


#< Failed attempts logging
def failed_job(job_id: str, job_link: str, resume: str, date_listed, error: str, exception: Exception, application_link: str, screenshot_name: str) -> None:
    '''
    Function to update failed jobs list in excel
    '''
    try:
        with open(failed_file_name, 'a', newline='', encoding='utf-8') as file:
            fieldnames = ['Job ID', 'Job Link', 'Resume Tried', 'Date listed', 'Date Tried', 'Assumed Reason', 'Stack Trace', 'External Job link', 'Screenshot Name']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':job_id, 'Job Link':job_link, 'Resume Tried':resume, 'Date listed':date_listed, 'Date Tried':datetime.now(), 'Assumed Reason':error, 'Stack Trace':exception, 'External Job link':application_link, 'Screenshot Name':screenshot_name})
            file.close()
    except Exception as e:
        print_lg("Failed to update failed jobs list!", e)
        pyautogui.alert("Failed to update the excel of failed jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")


def screenshot(driver: WebDriver, job_id: str, failedAt: str) -> str:
    '''
    Function to to take screenshot for debugging
    - Returns screenshot name as String
    '''
    screenshot_name = "{} - {} - {}.png".format( job_id, failedAt, str(datetime.now()) )
    path = logs_folder_path+"/screenshots/"+screenshot_name.replace(":",".")
    # special_chars = {'*', '"', '\\', '<', '>', ':', '|', '?'}
    # for char in special_chars:  path = path.replace(char, '-')
    driver.save_screenshot(path.replace("//","/"))
    return screenshot_name
#>



def submitted_jobs(job_id: str, title: str, company: str, work_location: str, work_style: str, description: str, experience_required: int | Literal['Unknown', 'Error in extraction'], 
                   skills: list[str] | Literal['In Development'], hr_name: str | Literal['Unknown'], hr_link: str | Literal['Unknown'], resume: str, 
                   reposted: bool, date_listed: datetime | Literal['Unknown'], date_applied:  datetime | Literal['Pending'], job_link: str, application_link: str, 
                   questions_list: set | None, connect_request: Literal['In Development']) -> None:
    '''
    Function to create or update the Applied jobs CSV file, once the application is submitted successfully
    '''
    try:
        with open(file_name, mode='a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'About Job', 'Experience required', 'Skills required', 'HR Name', 'HR Link', 'Resume', 'Re-posted', 'Date Posted', 'Date Applied', 'Job Link', 'External Job link', 'Questions Found', 'Connect Request']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':job_id, 'Title':title, 'Company':company, 'Work Location':work_location, 'Work Style':work_style, 
                            'About Job':description, 'Experience required': experience_required, 'Skills required':skills, 
                                'HR Name':hr_name, 'HR Link':hr_link, 'Resume':resume, 'Re-posted':reposted, 
                                'Date Posted':date_listed, 'Date Applied':date_applied, 'Job Link':job_link, 
                                'External Job link':application_link, 'Questions Found':questions_list, 'Connect Request':connect_request})
        csv_file.close()
    except Exception as e:
        print_lg("Failed to update submitted jobs list!", e)
        pyautogui.alert("Failed to update the excel of applied jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")



# Function to discard the job application
def discard_job() -> None:
    actions.send_keys(Keys.ESCAPE).perform()
    wait_span_click(driver, 'Discard', 2)






# Function to apply to jobs
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException, ElementClickInterceptedException
import random
import pyautogui
import datetime


import pyautogui

def apply_to_jobs(search_terms: list[str]) -> None:
    """
    Searches and applies for jobs on LinkedIn.
    If no new jobs are found, prompts the user to quit or change location.
    """
    global search_location  # Allow modifying location globally

    while True:  # Keep searching until the user chooses to quit
        print_lg("\n🔎 Starting job search and application process...\n")

        applied_jobs = get_applied_job_ids()
        rejected_jobs = set()
        blacklisted_companies = set()

        global current_city, failed_count, skip_count, easy_applied_count, external_jobs_count, tabs_count, pause_before_submit, pause_at_failed_question, useNewResume, aiClient
        current_city = current_city.strip()

        if use_AI and aiClient is None:
            aiClient = ai_create_openai_client()

        if randomize_search_order:
            random.shuffle(search_terms)

        actions = ActionChains(driver)
        wait = WebDriverWait(driver, 10)

        already_applied_count = 0  # ✅ Track repeated "Already applied" messages

        for searchTerm in search_terms:
            print_lg(f'\n>>> Searching for: "{searchTerm}" <<<\n')

            # ✅ Set search location before searching
            set_search_location(driver, actions, search_location)

            driver.get(f"https://www.linkedin.com/jobs/search/?keywords={searchTerm}")
            buffer(3)

            # Apply LinkedIn job filters
            try:
                print("🔎 Applying job filters...")
                apply_filters(driver, actions, search_location)
                print("✅ Applied LinkedIn job filters successfully.")
            except Exception as e:
                print(f"❌ Failed to apply filters: {e}")
                continue

            print("🔎 Checking if job search results are available...")

            try:
                wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-occludable-job-id]")))
                job_listings = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")

                if job_listings:
                    print(f"✅ Found {len(job_listings)} job listings for '{searchTerm}'")
                else:
                    print("❌ No job listings found!")
                    continue

            except Exception as e:
                print(f"❌ Failed to find job listings! Error: {e}")
                continue

            current_count = 0
            while current_count < switch_number:
                try:
                    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-occludable-job-id]")))
                    job_listings = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")

                    for job in job_listings:
                        if current_count >= switch_number:
                            break

                        job_id, title, company, work_location, work_style, skip = get_job_main_details(job, blacklisted_companies, rejected_jobs)
                        if skip:
                            continue

                        if job_id in applied_jobs:
                            print_lg(f'✅ Already applied to "{title} | {company}". Skipping...')
                            already_applied_count += 1  # ✅ Track repeated "Already applied" messages

                            # ✅ If too many "Already applied" messages, ask user for next step
                            if already_applied_count >= 10:
                                user_choice = pyautogui.confirm(
                                    "All jobs applied!\nDo you want to change location or quit?",
                                    "Job Application Complete",
                                    ["Change Location", "Quit"]
                                )

                                if user_choice == "Change Location":
                                    new_location = pyautogui.prompt("Enter a new job search location:", "Change Search Location")
                                    if new_location:
                                        search_location = new_location.strip()
                                        print_lg(f"🔄 Changing search location to: {search_location}")
                                        return apply_to_jobs(search_terms)  # Restart with new location
                                else:
                                    print_lg("✅ Stopping job application process.")
                                    return  # Exit function if user cancels

                            continue

                        job.click()
                        buffer(2)

                        if try_xp(driver, ".//button[contains(@class,'jobs-apply-button') and contains(@aria-label, 'Easy')]"):
                            print_lg("🔵 Attempting Easy Apply...")
                            easy_apply(job_id, title, company)
                        else:
                            print_lg("⚠️ No Easy Apply button found. Skipping...")
                            continue

                        current_count += 1
                        applied_jobs.add(job_id)
                        already_applied_count = 0  # ✅ Reset counter when a new job is applied

                except StaleElementReferenceException:
                    print("⚠️ Job element became stale. Retrying...")
                    continue
                except NoSuchElementException:
                    print("❌ Failed to locate job element. Skipping...")
                    continue
                except Exception as e:
                    print(f"❌ Unexpected error during job application: {e}")
                    continue

        print_lg("\n✅ Job Application Process Completed!\n")

        # ✅ If the script finishes without triggering the "already applied" limit, ask for next action
        user_choice = pyautogui.confirm(
            "All jobs applied!\nDo you want to change location or quit?",
            "Job Application Complete",
            ["Change Location", "Quit"]
        )

        if user_choice == "Change Location":
            new_location = pyautogui.prompt("Enter a new job search location:", "Change Search Location")
            if new_location:
                search_location = new_location.strip()
                print_lg(f"🔄 Changing search location to: {search_location}")
        else:
            print_lg("✅ Stopping job application process.")
            break  # Exit loop if the user chooses to quit


from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
import time

def easy_apply(job_id, title, company):
    """
    Automates the Easy Apply process, detects required questions, and fills them.
    """
    try:
        modal = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-easy-apply-modal")))
        print_lg("🟢 Easy Apply modal opened.")

        while True:
            required_fields = modal.find_elements(By.XPATH, ".//div[@data-test-form-element]")

            for field in required_fields:
                try:
                    label_text = field.text.strip().lower()
                    input_box = field.find_elements(By.TAG_NAME, "input")
                    textarea = field.find_elements(By.TAG_NAME, "textarea")
                    dropdown = field.find_elements(By.TAG_NAME, "select")
                    radio_buttons = field.find_elements(By.XPATH, ".//input[@type='radio']")

                    # Handling different input types
                    if dropdown:
                        select = Select(dropdown[0])
                        select.select_by_index(1 if len(select.options) > 1 else 0)  # Select first valid option

                    elif radio_buttons:
                        radio_buttons[0].click()  # Click the first available radio button

                    elif input_box:
                        default_value = get_default_value(label_text)
                        input_box[0].clear()
                        input_box[0].send_keys(default_value)

                    elif textarea:
                        textarea[0].clear()
                        textarea[0].send_keys("N/A")  # Default text-based answer

                except Exception as e:
                    print_lg(f"⚠️ Error handling field: {e}")

            # Click "Next" if available
            try:
                next_button = modal.find_element(By.XPATH, ".//button[contains(., 'Next')]")
                if next_button.is_enabled():
                    next_button.click()
                    time.sleep(2)
                    print_lg("➡️ Clicked 'Next'.")
                    continue  # Continue looping to the next step
            except NoSuchElementException:
                print_lg("❌ 'Next' button not found. Moving to Review step.")
                break  # Break the loop if there's no "Next" button

        # Click "Review" if available
        try:
            review_button = driver.find_element(By.XPATH, ".//button[contains(., 'Review')]")
            if review_button.is_enabled():
                review_button.click()
                time.sleep(2)
                print_lg("🔍 Clicked 'Review'.")
        except NoSuchElementException:
            print_lg("❌ 'Review' button not found. Moving to Submit step.")

        # Click "Submit Application"
        try:
            submit_button = driver.find_element(By.XPATH, ".//button[contains(., 'Submit application')]")
            if submit_button.is_enabled():
                submit_button.click()
                print_lg(f'✅ Successfully applied to "{title} | {company}".')
                time.sleep(2)
        except NoSuchElementException:
            print_lg("❌ 'Submit Application' button not found.")

        # Click "Done" if available
        try:
            done_button = driver.find_element(By.XPATH, ".//button[contains(., 'Done')]")
            if done_button.is_enabled():
                done_button.click()
                print_lg("✅ Clicked 'Done'.")
        except NoSuchElementException:
            print_lg("❌ 'Done' button not found.")

    except Exception as e:
        print_lg(f"❌ Easy Apply failed: {e}")
        failed_job(job_id, "Unknown", "Unknown", "Easy Apply Failed", e, "Skipped", "Unknown")

def run(total_runs: int) -> int:
    if dailyEasyApplyLimitReached:
        return total_runs
    print_lg("\n########################################################################################################################\n")
    print_lg(f"Date and Time: {datetime.now()}")
    print_lg(f"Cycle number: {total_runs}")
    print_lg(f"Currently looking for jobs posted within '{date_posted}' and sorting them by '{sort_by}'")
    apply_to_jobs(search_terms)
    print_lg("########################################################################################################################\n")
    if not dailyEasyApplyLimitReached:
        print_lg("Sleeping for 10 min...")
        sleep(300)
        print_lg("Few more min... Gonna start with in next 5 min...")
        sleep(300)
    buffer(3)
    return total_runs + 1



chatGPT_tab = False
linkedIn_tab = False

def main() -> None:
    try:
        global linkedIn_tab, tabs_count, useNewResume, aiClient
        alert_title = "Error Occurred. Closing Browser!"
        total_runs = 1        
        validate_config()
        
        if not os.path.exists(default_resume_path):
            pyautogui.alert(text='Your default resume "{}" is missing! Please update it\'s folder path "default_resume_path" in config.py\n\nOR\n\nAdd a resume with exact name and path (check for spelling mistakes including cases).\n\n\nFor now the bot will continue using your previous upload from LinkedIn!'.format(default_resume_path), title="Missing Resume", button="OK")
            useNewResume = False
        
        # Login to LinkedIn
        tabs_count = len(driver.window_handles)
        driver.get("https://www.linkedin.com/login")
        if not is_logged_in_LN(): login_LN()
        
        linkedIn_tab = driver.current_window_handle

        # # Login to ChatGPT in a new tab for resume customization
        # if use_resume_generator:
        #     try:
        #         driver.switch_to.new_window('tab')
        #         driver.get("https://chat.openai.com/")
        #         if not is_logged_in_GPT(): login_GPT()
        #         open_resume_chat()
        #         global chatGPT_tab
        #         chatGPT_tab = driver.current_window_handle
        #     except Exception as e:
        #         print_lg("Opening OpenAI chatGPT tab failed!")
        if use_AI:
            aiClient = ai_create_openai_client()

        # Start applying to jobs
        driver.switch_to.window(linkedIn_tab)
        total_runs = run(total_runs)
        while(run_non_stop):
            if cycle_date_posted:
                date_options = ["Any time", "Past month", "Past week", "Past 24 hours"]
                global date_posted
                date_posted = date_options[date_options.index(date_posted)+1 if date_options.index(date_posted)+1 > len(date_options) else -1] if stop_date_cycle_at_24hr else date_options[0 if date_options.index(date_posted)+1 >= len(date_options) else date_options.index(date_posted)+1]
            if alternate_sortby:
                global sort_by
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
                total_runs = run(total_runs)
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
            total_runs = run(total_runs)
            if dailyEasyApplyLimitReached:
                break
        

    except NoSuchWindowException:   pass
    except Exception as e:
        critical_error_log("In Applier Main", e)
        pyautogui.alert(e,alert_title)
    finally:
        print_lg("\n\nTotal runs:                     {}".format(total_runs))
        print_lg("Jobs Easy Applied:              {}".format(easy_applied_count))
        print_lg("External job links collected:   {}".format(external_jobs_count))
        print_lg("                              ----------")
        print_lg("Total applied or collected:     {}".format(easy_applied_count + external_jobs_count))
        print_lg("\nFailed jobs:                    {}".format(failed_count))
        print_lg("Irrelevant jobs skipped:        {}\n".format(skip_count))
        if randomly_answered_questions: print_lg("\n\nQuestions randomly answered:\n  {}  \n\n".format(";\n".join(str(question) for question in randomly_answered_questions)))
        quote = choice([
            "You're one step closer than before.", 
            "All the best with your future interviews.", 
            "Keep up with the progress. You got this.", 
            "If you're tired, learn to take rest but never give up.",
            "Success is not final, failure is not fatal: It is the courage to continue that counts. - Winston Churchill",
            "Believe in yourself and all that you are. Know that there is something inside you that is greater than any obstacle. - Christian D. Larson",
            "Every job is a self-portrait of the person who does it. Autograph your work with excellence.",
            "The only way to do great work is to love what you do. If you haven't found it yet, keep looking. Don't settle. - Steve Jobs",
            "Opportunities don't happen, you create them. - Chris Grosser",
            "The road to success and the road to failure are almost exactly the same. The difference is perseverance.",
            "Obstacles are those frightful things you see when you take your eyes off your goal. - Henry Ford",
            "The only limit to our realization of tomorrow will be our doubts of today. - Franklin D. Roosevelt"
            ])
        msg = f"\n{quote}\n\n\nwith hardwork,\nMii\n\n"
        pyautogui.alert(msg, "Exiting..")
        print_lg(msg,"Closing the browser...")
        if tabs_count >= 10:
            msg = "NOTE: IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM!\n\nOr it's highly likely that application will just open browser and not do anything next time!" 
            pyautogui.alert(msg,"Info")
            print_lg("\n"+msg)
        ai_close_openai_client(aiClient)
        try: driver.quit()
        except Exception as e: critical_error_log("When quitting...", e)

if __name__ == "__main__":
    print("🔎 Checking if already logged in...")
    
    if "feed" not in driver.current_url:  # Ensures we are on the LinkedIn homepage before running login
        login_LN()
    
    print("🔎 Starting job search and application process automatically...")
    apply_to_jobs(search_terms)  # Start searching and applying for jobs
