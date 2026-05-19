import json
import time
import requests
import io
import pdfplumber
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# 1. إعدادات السكريبت الأساسية
# ==========================================
BASE_URL = "https://www.htw-berlin.de"
PROGRAMS_URL = f"{BASE_URL}/studium/studiengaenge/"

# ==========================================
# 2. دوال الفلترة والذكاء (Core Logic)
# ==========================================
def is_valid_pdf_link(href, text):
    """فلترة صارمة للتأكد أن الملف هو خطة دراسية وليس قرار إداري أو خريطة"""
    href_lower = href.lower() if href else ""
    text_lower = text.lower() if text else ""
    
    # استبعاد ملفات القوانين الإدارية العامة
    if "satzung" in href_lower or "satzung" in text_lower:
        return False
        
    # الشروط المطلوبة لملف المواد
    if ("stpo" in text_lower or 
        "ordnung" in text_lower or 
        "ambl" in text_lower or 
        "_ba.pdf" in href_lower or 
        "_ma.pdf" in href_lower or 
        "stpo" in href_lower):
        return True
    return False

def is_valid_nav_link(href, text):
    """تحديد التبويبات التي من المحتمل أن تحتوي على الخطة الدراسية"""
    href_lower = href.lower() if href else ""
    text_lower = text.lower().strip() if text else ""
    
    # استبعاد تبويبات اللجان لتجنب الفخ
    if "ausschuss" in text_lower or "ausschuss" in href_lower:
        return False
        
    # الشروط المطلوبة للتبويبات الفرعية
    if ("ordnung" in text_lower or 
        "studienablauf" in text_lower or 
        text_lower == "studium" or 
        "modul" in text_lower or 
        "ordnung" in href_lower or 
        "studien" in href_lower):
        return True
    return False

def search_pdf_in_current_page(driver):
    """البحث عن رابط الـ PDF في الصفحة المفتوحة حالياً"""
    pdf_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='.pdf']")
    for el in pdf_elements:
        try:
            href = el.get_attribute("href")
            text = el.text
            if is_valid_pdf_link(href, text):
                return href
        except:
            continue
    return None

def find_and_sort_nav_links(driver):
    """استخراج وترتيب التبويبات الفرعية حسب الأهمية (لضمان الوصول السريع)"""
    links_found = []
    elements = driver.find_elements(By.TAG_NAME, "a")
    for el in elements:
        try:
            txt = el.text
            href = el.get_attribute("href")
            
            if is_valid_nav_link(href, txt):
                # منع التكرار
                if href not in [l['href'] for l in links_found]:
                    prio = 4
                    txt_lower = txt.lower()
                    href_lower = href.lower()
                    
                    if "ordnung" in txt_lower or "ordnung" in href_lower: prio = 1
                    elif "studienablauf" in txt_lower or "studienablauf" in href_lower: prio = 2
                    elif "modul" in txt_lower or "modul" in href_lower: prio = 3
                    
                    links_found.append({"href": href, "prio": prio})
        except:
            continue
    return sorted(links_found, key=lambda x: x['prio'])

# ==========================================
# 3. دالة استخراج البيانات من الـ PDF
# ==========================================
def extract_modules_from_pdf(pdf_url):
    print(f"   -> Reading PDF: {pdf_url.split('/')[-1]}")
    modules = []
    try:
        response = requests.get(pdf_url, timeout=15) # إضافة مهلة لتجنب التعليق
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # استهداف العمود الثاني غالباً لتخطي الأرقام التعريفية
                        if len(row) > 1 and row[1]: 
                            module_name = str(row[1]).replace('\n', ' ').strip()
                            
                            # تنظيف البيانات من العناوين العامة
                            if len(module_name) > 4 and "Modul" not in module_name and "कलन" not in module_name:
                                modules.append(module_name)
                                
        # إزالة التكرارات
        return list(set(modules))
    except Exception as e:
        print(f"   -> Error reading PDF: {e}")
        return []

# ==========================================
# 4. الدالة الرئيسية (دورة العمل)
# ==========================================
def main():
    print("Starting the browser...")
    options = Options()
    options.add_argument('--start-maximized') 
    options.add_argument('--log-level=3') # لتقليل رسائل الكروم المزعجة
    options.add_experimental_option("detach", True) 
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print(f"Loading main programs page: {PROGRAMS_URL}")
        driver.get(PROGRAMS_URL)
        
        # انتظار صريح لحين تحميل الكروت بدل الـ Sleep العشوائي
        print("Waiting for program cards to load...")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.card")))
        time.sleep(2) # انتظار إضافي للجافاسكربت
        
        cards = driver.find_elements(By.CSS_SELECTOR, "div.card")
        if len(cards) == 0:
            print("No programs found. Exiting.")
            return

        print(f">>> Found {len(cards)} programs! <<<")
        
        # تجميع روابط التخصصات
        links = []
        for card in cards:
            try:
                a_tag = card.find_element(By.TAG_NAME, "a")
                href = a_tag.get_attribute('href')
                if href:
                    full_url = href if href.startswith('http') else BASE_URL + href
                    program_name = card.get_attribute('aria-label')
                    if not program_name:
                        headline = card.find_element(By.CSS_SELECTOR, "div.card-headline")
                        program_name = headline.text.strip()
                        
                    links.append({"name": program_name, "url": full_url})
            except:
                continue
                
        database_data = []
        
        # البدء بالمرور على التخصصات
        for prog in links:
            print(f"\n[+] Program: {prog['name']}")
            try:
                driver.get(prog['url'])
                time.sleep(1.5)
                
                # 1. البحث في الصفحة الرئيسية
                pdf_url = search_pdf_in_current_page(driver)
                
                # 2. البحث العميق (Deep Scanning) في حال عدم التواجد
                if not pdf_url:
                    first_layer_tabs = find_and_sort_nav_links(driver)
                    
                    for tab in first_layer_tabs:
                        tab_name = tab['href'].split('/')[-1] or tab['href'].split('/')[-2]
                        print(f"   -> Checking tab: {tab_name}")
                        driver.get(tab['href'])
                        time.sleep(1.5)
                        
                        pdf_url = search_pdf_in_current_page(driver)
                        if pdf_url:
                            break
                            
                        # البحث في المستوى الثاني (Sub-tabs)
                        second_layer_tabs = find_and_sort_nav_links(driver)
                        for sub_tab in second_layer_tabs:
                            if sub_tab['prio'] < 4 and sub_tab['href'] not in [t['href'] for t in first_layer_tabs]:
                                sub_tab_name = sub_tab['href'].split('/')[-1] or sub_tab['href'].split('/')[-2]
                                print(f"      -> Going deeper to sub-tab: {sub_tab_name}")
                                driver.get(sub_tab['href'])
                                time.sleep(1.5)
                                
                                pdf_url = search_pdf_in_current_page(driver)
                                if pdf_url:
                                    break
                        if pdf_url:
                            break

                # 3. استخراج المواد بعد تحديد مسار الـ PDF
                modules = []
                if pdf_url:
                    modules = extract_modules_from_pdf(pdf_url)
                else:
                    print("   -> ❌ Could not find PDF (StPO) even in deep sub-tabs.")
                    
                # حفظ النتيجة في المصفوفة
                database_data.append({
                    "fachbereich": "Not specified",
                    "studiengang": prog['name'],
                    "url": prog['url'],
                    "module": modules
                })
                
            except Exception as e:
                print(f"   -> ⚠️ Skipped due to page error: {e}")
                continue # إكمال السكريبت للتخصص التالي في حال حدوث خطأ مفاجئ بالصفحة
            
        # ==========================================
        # 5. تصدير البيانات
        # ==========================================
        with open('htw_modules.json', 'w', encoding='utf-8') as f:
            json.dump(database_data, f, ensure_ascii=False, indent=4)
            
        print("\n[✔] Completely finished. Clean data saved in htw_modules.json")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        driver.quit() # إغلاق المتصفح وتنظيف الذاكرة

if __name__ == "__main__":
    main()