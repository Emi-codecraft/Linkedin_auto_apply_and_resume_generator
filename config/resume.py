
from personals import *  # Import personal information from the personals.py file
import json  # Import JSON module for handling JSON data

###################################################### CONFIGURE YOUR RESUME HERE ######################################################

# Specify the relative path of your default resume to be uploaded.
# If the file is not found, the bot will continue using your previously uploaded resume on LinkedIn.
default_resume_path = "all resumes/default/resume.pdf"  # (In Development)

'''
YOU DON'T HAVE TO EDIT THIS FILE IF YOU ADDED YOUR DEFAULT RESUME.
'''

# Example of how to create a resume headline using JSON.
# Uncomment and modify the following lines if you want to customize the resume headline.
# resume_headline = json.dumps({
#     "first_name": first_name,
#     "last_name": last_name,
#     "headline": "Software Engineer with expertise in AI and Machine Learning"  # Example headline
# })

# Note: Ensure that the JSON structure matches the expected format for your resume processing logic.
