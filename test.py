from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from bs4 import BeautifulSoup
import parse

options = ChromeOptions()
options.set_capability("se:name", "test_visit_basic_auth_secured_page (ChromeTests)")
driver = webdriver.Remote(options=options, command_executor="http://jupiter:4444")
url = "https://travelplus.virginatlantic.com/reward-flight-finder/results/month"
orgn = "LHR"
dest = "MLE"
a = "VS"
m = "11"
y = "2024"
out = f"{url}?origin={orgn}&destination={dest}&airline={a}&month={m}&year={y}"
ret = f"{url}?origin={dest}&destination={orgn}&airline={a}&month={m}&year={y}"

driver.get(out)
html = driver.page_source
soup = BeautifulSoup(html)
driver.quit()
for tag in soup.find_all("title"):
    print(tag.text)

days = soup.find_all("article", "css-1f0ownv")
for day in days:
    if day.text.startswith("None"):
        parts = parse.parse(
            "None available{dow} {day}No flight on this day, or no reward seats left",
            day.text,
        )
        print(f"none: {parts}")
    if day.text.startswith("Good"):
        parts = parse.parse(
            "Good{dow} {day}Upper Class{uc}Premium{prem}Economy{econ}", day.text
        )
        print(f"good: {parts}")
    if day.text.startswith("Limited"):
        parts = parse.parse(
            "Limited{dow} {day}Upper Class{uc}Premium{prem}Economy{econ}", day.text
        )
        print(f"limited: {parts}")


day = soup.find("article", "css-1f0ownv")
day = day.find_next("article", "css-1f0ownv")
divs = day.find_all("div")
for div in day.find_all("div"):
    print(div.text)

driver.quit()
