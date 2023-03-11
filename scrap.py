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