# Personal details for the resume
first_name = "Nancy"             # Your first name in quotes Eg: "First", "John"
middle_name = "C"             # Your name in quotes Eg: "Middle", "Doe", ""
last_name = "Loven"             # Your last name in quotes Eg: "Last", "Smith"

# Phone number (required), make sure it's valid.
phone_number = "123-456-7890"   # Enter your 10 digit number in quotes Eg: "123-456-7890"

# What is your current city?
current_city = "New York"               # Empty, so bot will fill in the job's location.

# Address, not so common question but some job applications make it required!
street = "123 Main St"
state = "NY"
zipcode = "10001"  # Manhattan, New York

country = "USA"
# Example of defining email in config/personals.py
email = ""


## US Equal Opportunity questions
ethnicity = "American Indian or Alaska Native"          #"Decline", "Hispanic/Latino", "American Indian or Alaska Native", "Asian", "Black or African American", "Native Hawaiian or Other Pacific Islander", "White", "Other"
gender = "Female"              # "Male", "Female", "Other", "Decline"
disability_status = "No"   # "Yes", "No", "Decline"
veteran_status = "Decline"      # "Yes", "No", "Decline"

'''
For string variables followed by comments with options, only use the answers from given options.
Some valid examples are:
* variable1 = "option1"         # "option1", "option2", "option3" or ("" to not select). Answers are case sensitive.
* variable2 = ""                # "option1", "option2", "option3" or ("" to not select). Answers are case sensitive.

Other variables are free text. No restrictions other than compulsory use of quotes.
Some valid examples are:
* variable3 = "Random Answer 5"         # Enter your answer. Eg: "Answer1", "Answer2"
'''

# Create a function that returns your personal information
def get_personal_info():
    return {
        "name": f"{first_name} {middle_name} {last_name}",
        "phone_number": phone_number,
        "city": current_city,
        "address": f"{street}, {state} {zipcode}, {country}",
        "ethnicity": ethnicity,
        "gender": gender,
        "disability_status": disability_status,
        "veteran_status": veteran_status,
    }

# Get your personal information
personal_info = get_personal_info()

# Use your personal information to fill out your resume template
resume_template = """
Name: {name}
Phone Number: {phone_number}
City: {city}
Address: {address}

US Equal Opportunity Questions:
Ethnicity: {ethnicity}
Gender: {gender}
Disability Status: {disability_status}
Veteran Status: {veteran_status}
"""

# Fill out your resume template with your personal information
resume = resume_template.format(**personal_info)

# Print out your resume
print(resume)
