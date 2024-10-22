import os
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta

CACHE_EXPIRY_DAYS = 60 

file_whitelist = {'bnn_accuracy.py', 'testing_tool.py', 'unununion_find.py'}
image_src = 'https://github.com/abrahamcalf/programming-languages-logos/blob/master/src/' # hey this a credit!
image_mapper = {
    'py':   'python',
    'c':    'c',
    'cpp':  'cpp',
    'cs':   'csharp',
    'go':   'go',
    'hs':   'haskell',
    'java': 'java',
    'kt':   'kotlin',
    'php':  'php',
    'rb':   'ruby',
    'js':   'javascript'
}

get_image = lambda e,s=24: f'{image_src}{image_mapper[e]}/{image_mapper[e]}_{s}x{s}.png'

def get_current_date():
    return datetime.now().strftime('%Y-%m-%d')

def load_cached_difficulties(cache_file='difficulty_cache.json'):
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return {}

def save_cached_difficulties(cache, cache_file='difficulty_cache.json'):
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=4)

def get_problem_difficulty(pid, cache):
    # If the difficulty is cached, return it
    if pid in cache:
        last_updated = cache[pid].get('last_updated')
        if last_updated:
            last_updated_date = datetime.strptime(last_updated, '%Y-%m-%d')
            if (datetime.now() - last_updated_date).days <= CACHE_EXPIRY_DAYS:
                return cache[pid]['difficulty'] 
    
    # Otherwise, request the difficulty from the Kattis website
    url = f"https://open.kattis.com/problems/{pid}"
    response = requests.get(url)

    if response.status_code == 200:
        # Parse the page using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find the difficulty number based on the class name
        difficulty_span = soup.find('span', class_='difficulty_number')
        if difficulty_span:
            difficulty = difficulty_span.text.strip()
            cache[pid] = {
                'difficulty': difficulty,
                'last_updated': get_current_date()
            }
            return difficulty
    return "N/A"

difficulty_cache = load_cached_difficulties()

contents = []
# Iterate through files in the 'solutions' directory
for file in sorted(os.listdir('solutions')):
    file_path = os.path.join('solutions', file)
    
    # Check if the item is a file and its extension is in image_mapper
    if os.path.isfile(file_path):
        ext = file.split('.')[-1]

        if ext in image_mapper:
            pid = file.split('.')[0]  # Use the filename without extension as the problem ID
            kattis_url = f"https://open.kattis.com/problems/{pid}"
            repo_url = f"https://github.com/simonsejse/competitive-programming/tree/main/solutions/{file}"

            # Get the difficulty from Kattis or from the cache
            difficulty = get_problem_difficulty(pid, difficulty_cache)

            # Generate the display for the file
            image_icon = f"[![{ext}]({get_image(ext)})]({file_path})" if file not in file_whitelist else ""
            
            # Append the formatted line to contents, including difficulty
            contents.append([pid, f"|[{file}]({file})| [{pid}]({kattis_url}) | {difficulty} | {image_icon}|\n"])

# Save the updated difficulties cache
save_cached_difficulties(difficulty_cache)

# Read the current content of the README file
lines = open('README.md', 'r', encoding='utf8').readlines()

# Define the start and end markers
start_marker = '<!-- START_SOLVED_STATS -->'
end_marker = '<!-- END_SOLVED_STATS -->'

# Find the start and end markers in the lines
start_index = None
end_index = None
for i, line in enumerate(lines):
    if start_marker in line:
        start_index = i
    if end_marker in line:
        end_index = i
        break

# If both markers are found, replace content between them
if start_index is not None and end_index is not None:
    # Keep the lines outside the markers and prepare new content for inside
    lines = lines[:start_index+1] + [
        f'## Total problems solved: {len(contents)}\n\n',
        'Note that the table below is auto-generated. There might be slight inaccuracies.\n\n',
        '|Problem Name|Problem ID|Difficulty|Languages|\n|:---|:---|:---|:---|\n'
    ] + [content for _, content in sorted(contents)] + lines[end_index:]

# Write the modified content back to the README file
with open('README.md', 'w', encoding='utf8') as f:
    f.writelines(lines)


########################### THIS IS FOR TABLE OF CONTENTS ###########################

def generate_slug(heading):
    # Remove '##', strip whitespace, and remove special characters (emojis, etc.)
    heading = heading.replace('##', '').strip()
    # Remove all non-alphanumeric characters except spaces (this removes emojis and symbols)
    heading = re.sub(r'[^\w\s-]', '', heading)
    # Replace spaces with hyphens, make it lowercase
    return heading.lower().replace(' ', '-')

# Function to create the table of contents based on ## headings
def generate_table_of_contents(lines):
    toc = ["## Table of Contents\n"]
    for line in lines:
        if line.startswith('## ') and not line.startswith('## Table of Contents'):
            # Extract the heading text and generate a slug for the link
            heading_text = line.strip().replace('##', '').strip()
            heading_slug = generate_slug(heading_text)
            toc.append(f"- [{heading_text}](#{heading_slug})\n")
    return toc

# Read the current content of the README file
lines = open('README.md', 'r', encoding='utf8').readlines()

# Define the start and end markers for the Table of Contents
toc_start_marker = '<!-- START_TABLE_OF_CONTENTS -->'
toc_end_marker = '<!-- END_TABLE_OF_CONTENTS -->'

# Find the start and end markers for the Table of Contents
toc_start_index = None
toc_end_index = None
for i, line in enumerate(lines):
    if toc_start_marker in line:
        toc_start_index = i
    if toc_end_marker in line:
        toc_end_index = i
        break

# Generate the Table of Contents based on the ## headings
table_of_contents = generate_table_of_contents(lines)

# If both TOC markers are found, replace content between them
if toc_start_index is not None and toc_end_index is not None:
    # Keep the lines outside the TOC markers and insert the new Table of Contents inside
    lines = lines[:toc_start_index+1] + table_of_contents + lines[toc_end_index:]

# Write the modified content back to the README file
with open('README.md', 'w', encoding='utf8') as f:
    f.writelines(lines)
