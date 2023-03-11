# import requests
# from bs4 import BeautifulSoup
#
# url = 'https://www.classcentral.com/'
#
# # Send an HTTP request to the URL and get the page content
# response = requests.get(url)
# html_content = response.content
#
#
# # Use BeautifulSoup to parse the HTML content
# soup = BeautifulSoup(html_content, 'html.parser')
#
# # Find all the course cards on the homepage
# course_cards = soup.find_all('div', {'class': 'text-left w-3/4'})
# print(course_cards)
#
# for course_card in course_cards:
#     # Extract the course name and description
#     course_name = course_card.h3.text.strip()
#     course_desc = course_card.p.text.strip()
#
#     # Extract the provider name and logo
#     provider_name = course_card.find('span', {'class': 'text-sm text-gray-600'}).text.strip()
#     provider_logo = course_card.find('img')['src']
#
#     # Extract the course rating and review count
#     rating_element = course_card.find('div', {'class': 'text-base font-medium text-yellow-400'})
#     if rating_element:
#         course_rating = rating_element.text.strip()
#         review_count = rating_element.find_next_sibling('div').text.strip()
#     else:
#         course_rating = ''
#         review_count = ''
#
#     # Extract the course start date and duration
#     start_date_element = course_card.find('div', {'class': 'text-sm text-gray-500'})
#     if start_date_element:
#         course_start_date = start_date_element.find('div', {'class': 'text-sm text-gray-600'}).text.strip()
#         course_duration = start_date_element.find('div', {'class': 'text-sm text-gray-500'}).text.strip()
#     else:
#         course_start_date = ''
#         course_duration = ''
#
#     # Extract the course categories and subcategories
#     category_elements = course_card.find_all('div', {'class': 'text-sm text-gray-500 mt-1'})
#     course_categories = [elem.text.strip() for elem in category_elements]
#
#     # Extract the links to the course page and provider page
#     course_link = course_card.find('a')['href']
#     provider_link = course_card.find('div', {'class': 'w-1/4'}).find('a')['href']
#
#     # Print the extracted data
#     print('Course Name:', course_name)
#     print('Course Description:', course_desc)
#     print('Provider Name:', provider_name)
#     print('Provider Logo:', provider_logo)
#     print('Course Rating:', course_rating)
#     print('Review Count:', review_count)
#     print('Course Start Date:', course_start_date)
#     print('Course Duration:', course_duration)
#     print('Course Categories:', course_categories)
#     print('Course Link:', course_link)
#     print('Provider Link:', provider_link)
#     print('----------------------------------------------')


from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from time import sleep
from xlsxwriter import Workbook

base_url = 'https://www.class-central.com'
subject_url = 'https://www.class-central.com/subject/ai'

driver = webdriver.Chrome('chromedriver.exe')
driver.get(subject_url)

# Wait for blocking popout ad and close it
try:
    element = WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="signupModal-ask_for_signup"]/div/div/a'))
    )
    element.click()
except TimeoutException:
    print('Blocking popup ad was not found in 60 seconds.')

# Keep clicking show more courses until all courses are listed
while 1:
    try:
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="show-more-courses"]'))
        )
        element.click()
        # Sleeping for a couple seconds to avoid click spam
        sleep(2)
    except TimeoutException:
        print('Show more courses button not found in 30 seconds.')
        # No more courses!
        break

page = driver.page_source
driver.close()

soup = BeautifulSoup(page, 'lxml')
course_table = soup.find('tbody', id='course-listing-tbody')
rows = course_table.find_all('tr')

courses = []
for row in rows:
    course_name_column = row.find('td', class_='course-name-column')

    # Skip non course rows
    if course_name_column is None:
        continue

    # Skip advertised courses
    if course_name_column.find('a', class_='course-name ad-name') is not None:
        continue

    # Skip advertised courses
    course_url = course_name_column.find('a', class_='course-name').get('href')
    if course_url.startswith('/mooc') == False:
        continue

    course_name = course_name_column.find('a', class_='course-name').get('title')
    course_url = base_url + course_url
    providers = ', '.join([p.a.text for p in course_name_column.find('ul', class_='table-uni-list').find_all('li')])
    platform = course_name_column.find('ul', class_='table-uni-list').find('a', recursive=False).text
    start_date = row.find('td', class_='start-date').text
    rating = row.find('td', class_='course-rating-column').get('data-timestamp')
    course = (course_name, providers, platform, start_date, rating, course_url)

    courses.append(course)

# open courses workbook
workbook = Workbook('courses.xlsx')
worksheet = workbook.add_worksheet()

# write course headers
worksheet.write(0, 0, 'course_name')
worksheet.write(0, 1, 'providers')
worksheet.write(0, 2, 'platform')
worksheet.write(0, 3, 'start_date')
worksheet.write(0, 4, 'course_name')
worksheet.write(0, 5, 'rating')
worksheet.write(0, 6, 'course_url')

# write courses values
row = 1
for course in courses:
    for i in range(len(course)):
        worksheet.write(row, i, course[i])
    row += 1

# close workbook
workbook.close()