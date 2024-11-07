from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.action_chains import ActionChains
import sys
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import csv
from selenium.webdriver.chrome.options import Options
import re

class PerkinsWebScraper:
    URL = "https://misweb.cccco.edu/perkinsv/Core_Indicator_Reports/Forms_All.aspx"
    SELECT_FORM_TYPE = 'ASPxRoundPanel1_ASPxComboBoxFT_I'
    SELECT_DISTRICT_COLLEGE = 'ASPxRoundPanel1_ASPxComboBoxC_I'
    FISCAL_YEAR = 'ASPxRoundPanel1_ASPxComboBoxFY_I'
    TOP_CODE = 'ASPxRoundPanel1_ASPxComboBoxTCode_I'
    TABLE_DIV_ID = 'VisibleReportContentASPxRoundPanel2_ReportViewer2_ctl09'
    VIEW_REPORT = 'ASPxRoundPanel1_ASPxButtonRS_B'
    ELEMENT_INFO = {
        'form_type': SELECT_FORM_TYPE,
        'district_college': SELECT_DISTRICT_COLLEGE,
        'fiscal_year': FISCAL_YEAR,
        'top_code': TOP_CODE
    }
    def __init__(self, url = URL, implicit_wait=1, explicit_wait=10, record_csv_path='scrape_record.csv', headless: bool = False):
        """
        Initialize the webdriver and open the given URL.

        Parameters:
        - url (str): The URL to navigate to.
        - implicit_wait (int): The implicit wait time in seconds.
        - explicit_wait (int): The explicit wait time in seconds for WebDriverWait.
        - record_csv_path (str): Path to the CSV file for recording scraped parameters.
        """
        if headless:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
        else:
            chrome_options = None
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(implicit_wait)
        self.wait = WebDriverWait(self.driver, explicit_wait)
        self.url = url
        self.soup = None
        self.record_csv_path = record_csv_path
        self.form_type = 'None'
        self.district_college = 'None'
        self.fiscal_year = 'None'
        self.top_code = 'NA'
        if record_csv_path:
            try:
                self.scrape_record = pd.read_csv(record_csv_path, keep_default_na=False)
            except FileNotFoundError:
                # If the file doesn't exist, create an empty DataFrame with the required columns
                self.scrape_record = pd.DataFrame(columns=['form_type', 'district_college', 'fiscal_year', 'top_code', 'headcount', 'enrollment', 'file_path'])
        else:
            self.scrape_record = pd.DataFrame(columns=['form_type', 'district_college', 'fiscal_year', 'top_code', 'headcount', 'enrollment', 'file_path'])

    def get_url(self):
        self.driver.get(self.url)
    
    def is_recorded(self, form_type, district_college, fiscal_year, top_code):
        """
        Check if the given parameters are already recorded in the scrape_record.
        """
        if self.scrape_record.empty:
            #print("No records to check against.")
            return False

        # Create a boolean mask for the matching row
        mask = (
            (self.scrape_record['form_type'] == form_type) &
            (self.scrape_record['district_college'] == district_college.strip()) &
            (self.scrape_record['fiscal_year'] == fiscal_year) &
            (self.scrape_record['top_code'] == top_code)
        )
        exists = mask.any()
        return exists
        

    def input_value(self, input_box, value):
        """
        Inputs a value into a specified input box on the webpage.

        Parameters:
        - input_box (str): The key representing the input box in element_info.
        - value (str): The value to input into the box.
        - element_info (dict): A dictionary mapping input_box keys to element IDs.
        """
        if value == 'NA':
            return
        if input_box not in self.ELEMENT_INFO:
            print(f"Box name should be one of these values: {list(self.ELEMENT_INFO.keys())}. Please input a proper box name.")
        else:
            element_id = self.ELEMENT_INFO[input_box]
            try:
                input_element = self.wait.until(EC.presence_of_element_located((By.ID, element_id)))
                input_element.click()  # Click on the input box to focus
                input_element.clear()  # Clear any existing text (optional)
                input_element.send_keys(value)
            except Exception as e:
                print(f"An error occurred while inputting value into '{input_box}'.")

    def view_report(self):
        """
        Clicks the report button to view a report.

        Parameters:
        - report_button (str): The identifier of the report button element.
        """
        try:
            report_button_element = self.wait.until(EC.element_to_be_clickable((By.ID, self.VIEW_REPORT)))
            report_button_element.click()
        except Exception as e:
            print(f"An error occurred while clicking the report button: {e}")

    def get_content(self, parser='html.parser'):
        """
        Waits for the table to appear and parses the page source with BeautifulSoup.

        Parameters:
        - table_div_id (str): The ID of the table's div element to wait for.
        - parser (str): The parser to use with BeautifulSoup.

        Returns:
        - soup (BeautifulSoup object): The parsed HTML content.
        """
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, self.TABLE_DIV_ID)))
            page_source = self.driver.page_source
            self.soup = BeautifulSoup(page_source, parser)
            self.close()
            return self.soup
        except Exception as e:
            print(f"An error occurred while getting content.")
            return None

    def get_top_codes(self, form_type, district_college, fiscal_year):
        """
        Get all available top codes given if form type is top code
        """
        self.get_url()
        self.input_value('form_type', form_type)
        self.input_value('fiscal_year', fiscal_year)
        time.sleep(1)
        self.input_value('district_college', district_college)
        self.wait.until(EC.presence_of_element_located((By.ID, self.TOP_CODE)))
        self.wait.until(EC.element_to_be_clickable((By.ID, self.TOP_CODE)))
        top_code_dropdown_button = self.wait.until(
            EC.element_to_be_clickable((By.ID, self.TOP_CODE))
        )
        self.wait.until(EC.element_to_be_clickable((By.ID, self.TOP_CODE)))
        top_code_dropdown_button.click()
        self.wait.until(EC.element_to_be_clickable((By.ID, self.TOP_CODE)))
        time.sleep(2)
        top_code_dropdown_button.click()

        top_code_options = self.wait.until(
            EC.visibility_of_all_elements_located((By.XPATH, "//table[@id='ASPxRoundPanel1_ASPxComboBoxTCode_DDD_L_LBT']//td[@class='dxeListBoxItem_Aqua']"))
        )
        top_codes = [top_code.text for top_code in top_code_options]
        self.close()
        return top_codes

    def scrape_report(self, form_type, district_college, fiscal_year, top_code):
        """
        Orchestrates the scraping process.

        Parameters:
        - form_type (str): The form type to input.
        - district_college (str): The college or district to select.
        - fiscal_year (str): The fiscal year to input.
        - top_code (str): The TOP code to input.

        Returns:
        - soup (BeautifulSoup object): The parsed HTML content.
        """
        if self.is_recorded(form_type, district_college, fiscal_year, top_code):
            print(f'{form_type}, {district_college.strip()}, {fiscal_year}, {top_code} is scraped already.')
            return None
        try:
            #get url
            self.get_url()
            # Input values
            self.input_value('form_type', form_type)
            self.input_value('fiscal_year', fiscal_year)
            time.sleep(1)
            self.input_value('district_college', district_college)
            if top_code and top_code != 'NA':
                #time.sleep(1)
                self.input_value('top_code', top_code)
                time.sleep(1)
                self.input_value('top_code', top_code)

            # Click the view report button
            #time.sleep(1)
            self.view_report()

            # Get and parse the content
            #time.sleep(2)
            self.wait.until(EC.visibility_of_element_located((By.ID, self.TABLE_DIV_ID)))
            soup = self.get_content()

            if soup:
                self.form_type = form_type
                self.district_college = district_college.strip()
                self.fiscal_year = fiscal_year
                self.top_code = top_code if top_code else 'NA'
                return soup
            else:
                print("Failed to retrieve content from the page.")
                return None
        except Exception as e:
            print(f"An error occurred during scraping: {e}")
            return None

    def add_record(self, headcount, enrollment, file_path):
        """
        Add a new record to the scrape_record DataFrame and save to CSV if path is provided.
        """
        new_record = pd.DataFrame([{
            'form_type': self.form_type,
            'district_college': self.district_college,
            'fiscal_year': self.fiscal_year,
            'top_code': self.top_code,
            'headcount': headcount,
            'enrollment': enrollment,
            'file_path': file_path
        }])
        self.scrape_record = pd.concat([self.scrape_record, new_record], ignore_index=True)

        if self.record_csv_path:
            self.scrape_record.to_csv(self.record_csv_path, index=False)

    def close(self):
        """
        Closes the webdriver instance.
        """
        self.driver.quit()