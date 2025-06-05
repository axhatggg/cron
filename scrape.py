from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import time

import os
uri = os.environ.get("MONGO_URI")
# MongoDB connection
# uri = "mongodb+srv://akshatgupta9612:SMAA51933@cluster0.5wfkz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['test']
collection = db['scholarships']

# Setup headless Chrome
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

# Open scholarship page
print("📡 Opening scholarship page...")
driver.get("https://www.buddy4study.com/scholarships")
time.sleep(5)

cards = driver.find_elements(By.CLASS_NAME, "Listing_categoriesBox__CiGvQ")
base_url = "https://www.buddy4study.com"

scholarships = []

print(f"📦 Found {len(cards)} scholarship cards. Extracting basic info...")

for idx, card in enumerate(cards, 1):
    try:
        title = card.find_element(By.CLASS_NAME, "Listing_scholarshipName__VLFMj").text.strip()
        link = card.get_attribute("href")
        if not link.startswith("http"):
            link = base_url + link

        try:
            deadline = card.find_element(By.CLASS_NAME, "Listing_noofDays__WtI47").text.strip()
        except:
            try:
                deadline = card.find_element(By.CLASS_NAME, "Listing_maxnine__XpCvm").text.strip()
            except:
                try:
                    deadline = card.find_element(By.CLASS_NAME, "Listing_calendarDate__WCgKV") \
                                   .find_elements(By.TAG_NAME, "p")[-1].text.strip()
                except:
                    deadline = "Unknown"

        try:
            award = card.find_elements(By.CLASS_NAME, "Listing_awardCont__qnjQK")[0] \
                        .find_element(By.TAG_NAME, "span").text.strip()
        except:
            award = "N/A"

        try:
            eligibility = card.find_elements(By.CLASS_NAME, "Listing_awardCont__qnjQK")[1] \
                              .find_element(By.TAG_NAME, "span").text.strip()
        except:
            eligibility = "N/A"

        scholarship = {
            'title': title,
            'link': link,
            'deadline': deadline,
            'award': award,
            'eligibility': eligibility,
            'scraped_at': datetime.utcnow()
        }

        scholarships.append(scholarship)

        print(f"🎓 [{idx}] {title}")
        print(f"   ⏰ Deadline: {deadline}")
        print(f"   🏆 Award: {award}")
        print(f"   ✅ Eligibility: {eligibility}")
        print(f"   🔗 Link: {link}")
        print("--------------------------------------------------")

    except Exception as e:
        print(f"❌ Error extracting card [{idx}]: {e}")

# Visit each scholarship link to extract official website
print("\n🌐 Visiting individual pages to extract official websites...")

for i, scholarship in enumerate(scholarships, 1):
    try:
        driver.get(scholarship['link'])
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        official_website = 'N/A'

        for a in soup.find_all('a', href=True):
            href = a['href']
            if "http" in href and "buddy4study" not in href \
               and "pinterest" not in href and "instagram" not in href:
                official_website = href
                break

        scholarships[i - 1]['official_website'] = official_website
        print(f"🌐 [{i}] Official Website found: {official_website}")

    except Exception as e:
        print(f"⚠️ Error visiting link [{i}]: {e}")
        scholarships[i - 1]['official_website'] = "N/A"

driver.quit()

# Optional: clear old data
print("\n🧹 Clearing old data from MongoDB collection...")
collection.delete_many({})

# Insert new data
print("💾 Inserting new scholarship data into MongoDB...")
collection.insert_many(scholarships)

print(f"\n✅ DONE: {len(scholarships)} scholarships saved to MongoDB.")
