# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 14:48:38 2021

@author: Nicolas

https://github.com/Gortaf
"""

# Generally usefull stuff
from tqdm import tqdm
import time
import random as rn

# threading stuff
import concurrent.futures

# webscrapping stuff
import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

# Classes from other files
from TimeTable import TimeTable

# A class that wraps a selenium webdriver to execute retrieval of data from
# the student center. This class should be instancied from the BrowserController
class Browser():
    def __init__(self):
        options = Options()
        self.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(),options=options)

    def wait_for_load_gif(self):
        try:
            WebDriverWait(self.driver, 1).until(
                EC.visibility_of_element_located((
                    By.XPATH,'//div[@class="gh-loader-popup gh-loader-preinit"]')))
            WebDriverWait(self.driver, 1).until(
                EC.visibility_of_element_located((
                    By.XPATH,'//div[@class="gh-loader-popup-inner"]')))
        except selenium.common.exceptions.TimeoutException:
            pass
        WebDriverWait(self.driver, 25).until(
            EC.invisibility_of_element_located((
                By.XPATH,'//div[@class="gh-loader-popup gh-loader-preinit"]')))
        WebDriverWait(self.driver, 25).until(
            EC.invisibility_of_element_located((
                By.XPATH,'//div[@class="gh-loader-popup-inner"]')))

    def to_login(self):
        self.driver.get("https://identification.umontreal.ca/cas/login.aspx")

    def login_with(self, user, unip):
        self.driver.find_element_by_id("txtIdentifiant").send_keys(user)
        self.driver.find_element_by_id("txtMDP").send_keys(unip)
        self.driver.find_element_by_id("btnValider").click()
        if "succès" in self.driver.page_source:
            return True
        else:
            self.driver.find_element_by_id("txtIdentifiant").clear()
            return False

    def to_session_selection(self):

        # Loads the student center
        self.driver.get("https://academique-dmz.synchro.umontreal.ca/")
        btn_to_stud_center = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,'//a[@href="/psp/acprpr9/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.SSS_STUDENT_CENTER.GBL"]')))
        btn_to_stud_center.click()

        # Skips the whole loading thing by executing the script
        # linked to the "panier" button
        self.driver.execute_script("javascript:submitAction_win0(document.win0,\'DERIVED_SSS_SCL_SSS_ENRL_CART$276$\');")

    def acquire_sessions(self):
        self.wait_for_load_gif()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH, '//ul[@class="gridformatter gh-listview"]')))

        rows = self.driver.find_elements_by_css_selector('li[id^="row"]')
        sessions = [row.find_element_by_tag_name("h3").text for row in rows]

        return sessions

    def select_session(self, sess_id):

        # We use similar waits as acquire_sessions, as executing the script
        # too fast doesn't work on synchro. This isn't a problem when the user
        # needs to select the session as it provides enough time, but it's a pain
        # for testing without those waits
        self.wait_for_load_gif()
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((
                By.XPATH, '//ul[@class="gridformatter gh-listview"]')))
        self.driver.execute_script(f"javascript:selectTerm({sess_id})")

    def acquire_timetable(self):
        self.wait_for_load_gif()

        # This is perhaps the weakest webscrapping hook. If something breaks after
        # an update on synchro, check this one first. ID is randomly generated,
        # so the only hook that makes some sense here is the class name, but
        # it really looks like something that could change anytime...
        timetable_url = self.driver.current_url
        table = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, 'table[class="PSLEVEL1GRID ui-table table-stroke table-stripe gh-sortable tablesaw ghtables ghtables-full"]')))
        table = table.find_element_by_tag_name("tbody").find_elements_by_tag_name("tr")
        raw_classes = list()
        raw_hours = list()

        for tr in table:
            cols = tr.find_elements_by_tag_name("td")
            class_name = cols[0].text
            class_hours = cols[2].text
            raw_classes.append(class_name)
            raw_hours.append(class_hours.split("\n"))

        return TimeTable(raw_classes, raw_hours), timetable_url

    def to_class_list(self):
        self.wait_for_load_gif()
        btn_to_class_list = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((
                By.ID,'DERIVED_REGFRM1_SSR_PB_SRCH')))
        self.wait_for_load_gif()
        btn_to_class_list.click()

    def acquire_all_blocs(self, ttb_url):
        # This should be runned by the first slave thread as a way to
        # acquire the repartition of blocs (computed by controller)
        self.wait_for_load_gif()
        blocs = WebDriverWait(self.driver, 20).until(
            EC.presence_of_all_elements_located((
                By.CSS_SELECTOR, "a[href^=\"javascript:submitAction_win0(document.win0,'DERIVED_SAA_DPR_SSR_EXPAND_COLLAPS$\"]")))

        blocs_id = [bloc.get_attribute("id") for bloc in blocs]
        # Goes back to session selection
        self.driver.get(ttb_url)
        self.wait_for_load_gif()
        return blocs_id

    def get_data_from_blocs(self, blocs_id, blocs_nb, ttb_url):
        for i, bloc_info in enumerate(zip(blocs_id, blocs_nb)):
            bloc_id, bloc_nb = bloc_info[0], bloc_info[1]
            # Naviguates to the class list
            self.get_data_from_bloc(bloc_id, bloc_nb, ttb_url, i)


    def get_data_from_bloc(self, bloc_id, bloc_nb, ttb_url, cur_iter):
        self.driver.get(ttb_url)
        self.to_class_list()

        try:
            bloc = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((
                    By.ID, bloc_id)))

        except selenium.common.exceptions.TimeoutException:
            # print(ttb_url)
            self.get_data_from_bloc(bloc_id, bloc_nb, ttb_url, cur_iter)
            # time.sleep(60)
            return

        # developps the blocs menu
        print(f"this one's good: {bloc_nb}")
        print(bloc_nb, cur_iter)
        #FIXME
        # apparament le click doesn't always go through... I have no idea why, need to test
        # the selenium element objects
        #HINT
        # maybe using the onclick script element of those arrows will help
        # need to test how synchro reacts with that.
        if not (bloc_nb == 0):
            bloc.click()
        print(f"tr[id^=\"trCOURSE_LIST${bloc_nb}\"]")

        # Acquires every row of the bloc
        self.wait_for_load_gif()
        bloc_rows = WebDriverWait(self.driver, 20).until(
            EC.presence_of_all_elements_located((
                By.CSS_SELECTOR, f"tr[id^=\"trCOURSE_LIST${bloc_nb}\"]")))
        print(bloc_rows)


    def end(self):
        self.driver.quit()


# A controller class that manages multiple Browsers over muliple threads,
# and coordinates them to retrieve information from the student center at
# an optimised rate
class BrowserController():
    def __init__(self, threads = 2):
        tqdm.write(f"[PRIMUS: BrowserController] - creating {threads} browser instances...")
        with concurrent.futures.ThreadPoolExecutor() as exe:
            futures = [exe.submit(Browser) for t in range(threads)]
        self.browsers = [b.result() for b in futures]
        tqdm.write(f"[PRIMUS: BrowserController] - browser instances ready.")

    def login_sequence(self, user, unip):
        tqdm.write("[PRIMUS: BrowserController] - naviguating browsers to login page...")
        with concurrent.futures.ThreadPoolExecutor() as exe:
            futures = [exe.submit(browser.to_login) for browser in self.browsers]

        tqdm.write(f"[PRIMUS: BrowserController] - attempting to connect as {user}...")
        with concurrent.futures.ThreadPoolExecutor() as exe:
            futures = [exe.submit(browser.login_with, user, unip) for browser in self.browsers]

        result = futures[0].result()
        tqdm.write(f"[PRIMUS: BrowserController] - sequence complete. Browser 0 returned {result}")
        return result

    def session_selection_sequence(self):
        tqdm.write("[PRIMUS: BrowserController] - attempting to retrieve sessions...")
        with concurrent.futures.ThreadPoolExecutor() as exe:
            futures = [exe.submit(browser.to_session_selection) for browser in self.browsers]

        sessions = self.browsers[0].acquire_sessions()
        tqdm.write(f"[PRIMUS: BrowserController] - sequence complete. Browser 0 found {len(sessions)} sessions.")
        return sessions

    def session_timetable_sequence(self, sess_id):
        tqdm.write(f"[PRIMUS: BrowserController] - acquiring root timetable from session {sess_id}.")
        # with concurrent.futures.ThreadPoolExecutor() as exe:
            # futures = [exe.submit(browser.select_session, sess_id) for browser in self.browsers]
        self.browsers[0].select_session(sess_id)
        self.ttb, self.ttb_url = self.browsers[0].acquire_timetable()
        self.sess_id = sess_id

    def acquire_bloc_distribution_sequence(self):
        tqdm.write("[PRIMUS: BrowserController] - Maneuvering browser 0 to acquire all blocs")
        self.browsers[0].to_class_list()
        self.blocs = self.browsers[0].acquire_all_blocs(self.ttb_url)
        tqdm.write(f"[PRIMUS: BrowserController] - {len(self.blocs)} blocs were found. Beginning distribution.")

        # Calculate the number of blocs per browsers (there might be extras)
        distribution_indice = len(self.blocs)//len(self.browsers)

        # Creates a list of list where every sublist is a list of blocs for a browser
        # to investigate
        iblocs = iter(self.blocs)
        self.dis = [list(bloc) for bloc in zip(*[iblocs for i in range(distribution_indice)])]
        nblocs = iter([i for i,b in enumerate(self.blocs)])
        self.dis_nb = [list(bloc) for bloc in zip(*[nblocs for i in range(distribution_indice)])]
        tqdm.write(f"[PRIMUS: BrowserController] - Distriution of {len(self.blocs)} blocs over {len(self.dis)} threads ready.")

        # If the division had extras, we need to redistribute them over the non-extra subslists
        if len(self.dis) != len(self.browsers):
            extras = self.dis.pop()
            # The length of the extras will never surpass the number of browsers (euclidian division principal)
            for i, extra in enumerate(extras):
                self.dis[i].append(extra)

    def main_extraction_sequence(self):
        if not hasattr(self, "dis"):
            return

        with concurrent.futures.ThreadPoolExecutor() as exe:
            for i, browser in enumerate(self.browsers):
                blocs, blocs_nb = self.dis[i], self.dis_nb[i]
                exe.submit(browser.get_data_from_blocs, blocs, blocs_nb, self.ttb_url)

    def end_sequence(self):
        tqdm.write("[PRIMUS: BrowserController] - attempting to safely end all browser instances.")
        with concurrent.futures.ThreadPoolExecutor() as exe:
            for browser in self.browsers:
                exe.submit(browser.end)
        tqdm.write("[PRIMUS: BrowserController] - browsers were safely closed.")

if __name__ == "__main__":
    # import traceback
    try:
        browser_controller = BrowserController(threads=3)
        browser_controller.login_sequence("pXXXXXX", "mot de passe")
        browser_controller.session_selection_sequence()
        browser_controller.session_timetable_sequence(2)
        browser_controller.acquire_bloc_distribution_sequence()
        browser_controller.main_extraction_sequence()
    except Exception as error:
        # traceback.print_exc(error)
        print("An error occured")
        print(error)
    browser_controller.end_sequence()