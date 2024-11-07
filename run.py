import sys
import os
from tqdm import tqdm

# Define the project root directory
project_root = r"C:\Users\bill1\OneDrive\Desktop\PerkinsCoreIndicatorReport"

# Add the project root to sys.path if not already present
if project_root not in sys.path:
    sys.path.append(project_root)

# Now you can import your modules
from src.PerkinsWebScraper import PerkinsWebScraper
from src.TableParser import TopCodeTableParser, CollegeTableParser


#from PerkinsCoreIndicatorReport import PerkinsWebScraper, TopCodeTableParser, CollegeTableParser

# Define your config here
#====================================================================================
FORM_TYPE_LS = ['Form 1 Part E-C - College',
               'Form 1 Part E-D - District',
               'Form 1 Part F by 6 Digit TOP Code - College']
COLLEGE_LS = ['San Diego City College                  ',
              'San Diego Mesa College                  ',
              'San Diego Miramar College Reg Cntr      ']
YEAR_LS = ['2024-2025', '2023-2024', '2022-2023', '2021-2022', '2020-2021']
#====================================================================================


# Define your file path here
#====================================================================================
# folder to store all data
#data_folder = '/data'
data_folder = r"C:\Users\bill1\OneDrive\Desktop\PerkinsCoreIndicatorReport\Data"

# Using os.path.join for subdirectories
college_fp = os.path.join(data_folder, 'College')
district_fp = os.path.join(data_folder, 'District')
top_code_fp = os.path.join(data_folder, 'Top Code')

# csv file path to log the scraping record.
record_csv_path = os.path.join(data_folder, 'scraping_log.csv')

# Create directories if they don't exist
os.makedirs(college_fp, exist_ok=True)
os.makedirs(district_fp, exist_ok=True)
os.makedirs(top_code_fp, exist_ok=True)
#====================================================================================


def scrape(form_type, district_college, fiscal_year, top_code, record_csv_path, output_folder, headless = False):
    # scrape content soup
    #print(f'Working on {form_type}, {district_college.strip()}, {fiscal_year}, {top_code}...')
    scraper = PerkinsWebScraper(implicit_wait=5, explicit_wait=10, headless=headless, record_csv_path=record_csv_path)
    soup = scraper.scrape_report(form_type, district_college, fiscal_year, top_code)
    
    # parse table
    if soup:
        if form_type == 'Form 1 Part E-C - College':
            parser = CollegeTableParser(soup, output_folder = output_folder, title = f'{district_college.strip()}_{fiscal_year}_NA')
        else:
            parser = TopCodeTableParser(soup, output_folder = output_folder, title = f'{district_college.strip()}_{fiscal_year}_{top_code.replace("/", " or ")}')
        df, enrollment, headcount = parser.get_table_info()
        success = parser.save_df()
        if success:
            scraper.add_record(headcount=parser.headcount, enrollment=parser.enrollment, file_path=os.path.join(parser.output_folder, f'{parser.title}.csv'))
    return



def run(form_type, college_ls=COLLEGE_LS, year_ls=YEAR_LS):
    if form_type == 'Form 1 Part E-C - College':
        top_code = 'NA'
        # Wrap the outer loop with tqdm
        #for college in tqdm(college_ls, desc='Colleges', unit='college', position=0):
        for college in college_ls:
            # Wrap the inner loop with tqdm
            print(f'Working on {college.strip()}...')
            for fiscal_year in tqdm(year_ls, desc='Fiscal Years', unit='year', leave=True, position=0):
                scrape(
                    form_type,
                    college,
                    fiscal_year,
                    top_code,
                    record_csv_path=record_csv_path,
                    output_folder=college_fp
                )
                
    elif form_type == 'Form 1 Part E-D - District':
        print(f'Download the files yourself and put them in {district_fp}.')
    
    elif form_type == 'Form 1 Part F by 6 Digit TOP Code - College':
        for college in college_ls:
            for fiscal_year in year_ls:
                get_top_codes = PerkinsWebScraper()
                top_codes = get_top_codes.get_top_codes(form_type, college, fiscal_year)
                print(f'Working on {college.strip()} in {fiscal_year}...')
                for top_code in tqdm(top_codes, desc='Top Codes', unit='code', leave=True, position=0):
                    out_folder = os.path.join(top_code_fp, college.strip())  # design your path
                    os.makedirs(out_folder, exist_ok=True)
                    scrape(
                        form_type,
                        college,
                        fiscal_year,
                        top_code,
                        record_csv_path=record_csv_path,
                        output_folder=out_folder,
                        headless=False
                    )
    
            print(f'Finished all top codes of {college.strip()} in {fiscal_year}!')


























