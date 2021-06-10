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
import threading

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
from TimeTable import TimeTable, SectionTimeTable, SynchroClass, TimeTree

# A class that wraps a selenium webdriver to execute retrieval of data from
# the student center. This class should be instancied from the BrowserController
class Browser():
    def __init__(self, controller):
        options = Options()
        options.headless = True
        options.add_argument('-headless')
        self.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(),options=options)
        self.controller = controller

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

        try:
            WebDriverWait(self.driver, 25).until(
                EC.invisibility_of_element_located((
                    By.XPATH,'//div[@class="gh-loader-popup gh-loader-preinit"]')))
            WebDriverWait(self.driver, 25).until(
                EC.invisibility_of_element_located((
                    By.XPATH,'//div[@class="gh-loader-popup-inner"]')))
        except selenium.common.exceptions.TimeoutException:
            pass

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
        # self.wait_for_load_gif()
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

    def get_data_from_blocs(self, blocs_nb, ttb_url):
        for bloc_nb in blocs_nb:
            # Naviguates to the class list
            self.get_data_from_bloc(bloc_nb, ttb_url, 0)


    def get_data_from_bloc(self, bloc_nb, ttb_url, cur_class):

        # This function will be called recursivly to go through assigned blocs
        self.driver.get(ttb_url)
        time.sleep(bloc_nb/4)  # small delay to reduce collisions between drivers
        self.to_class_list()
        self.wait_for_load_gif()
        bloc_selector = f"a[id=\"DERIVED_SAA_DPR_SSR_EXPAND_COLLAPS${bloc_nb}\"]"

        # We try to acquire all the blocs, so we can go to the one we're looking for
        # however, bad loads and collisions with other drivers happen, so if the
        # blocs cannot be located, we try again from the ttb page
        try:
            bloc = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, bloc_selector)))

        except selenium.common.exceptions.TimeoutException:
            self.get_data_from_bloc(bloc_nb, ttb_url, cur_class)
            return

        # developps the blocs menu
        self.wait_for_load_gif()
        if not (bloc_nb == 0):
            bloc.click()

        # Acquires every row of the bloc
        self.wait_for_load_gif()
        try:
            bloc_rows = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((
                    By.CSS_SELECTOR, f"tr[id^=\"trCOURSE_LIST${bloc_nb}\"]")))

        except selenium.common.exceptions.TimeoutException:
            self.get_data_from_bloc(bloc_nb, ttb_url, cur_class)
            return

        # Decomposing the bloc's table to extract the row of the class we're looking for
        row_data = bloc_rows[cur_class].find_elements_by_tag_name("td")
        row_sigle, row_link, row_status = row_data[0].text, row_data[1], row_data[5]

        # Detecting the class's status (last col)
        # if len(row_status.find_elements_by_tag_name("span")) == 0:
        #     # print("Class hasn't been taken")
        # else:
        #     # print("Class was either done, is in progress or was failed or abandonned")  #TODO: Distinguishe some of those cases

        # Acquiring the link on which to click ot get to the class page, and clicking
        row_link.find_element_by_tag_name("a").click()

        # Then we scrap the class's page. Actually treating the data to check
        # compatibility is done on an another thread by the controller
        callback_args = (bloc_nb, ttb_url, cur_class)
        class_object = self.acquire_class_timetables(row_sigle, callback_args)
        threading.Thread(target=self.controller.check_compatibility, args=[class_object]).start()

        # Recursivly calls itself if nescessary, with the nescessary parameters
        if cur_class+1 < len(bloc_rows):
            self.get_data_from_bloc(bloc_nb, ttb_url, cur_class+1)
            return
        else:
            return

    def acquire_class_timetables(self, class_name, callback_args):

        # Acquiring the big table with group names & timetables
        self.wait_for_load_gif()

        try:
            sections_name_elems = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located((
                        By.CSS_SELECTOR, 'a[id^="CLASS_SECTION$"]')))

            sections_table_elems = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located((
                        By.CSS_SELECTOR, 'table[id^="CLASS_MTGPAT$scroll$"]')))
        except selenium.common.exceptions.TimeoutException:
            self.get_data_from_bloc(*callback_args)

        # We are now going to build SectionTimeTables based on the tables
        # for each section available
        sections = dict()
        # First, we see which section "category" this table is (TH, TP, LAB, etc...)
        for name, table in zip(sections_name_elems, sections_table_elems):
            section_cat = name.text[name.text.rindex("_")+1: name.text.index("(")]
            rows = table.find_element_by_tag_name("tbody").find_elements_by_tag_name("tr")
            section_hours = []
            # Then we decompose the associated timetable into something we can use
            for row in rows:
                cells = row.find_elements_by_tag_name("td")
                day = cells[0].text
                hour_start = cells[1].text
                hour_end = cells[2].text
                section_hours.append([day, hour_start, hour_end])

            # We wrap the timetable into an nice object
            section = SectionTimeTable(name.text, section_hours)
            # We check if there's already an entry for that section type
            # if there isn't, we add one. If there is, we append to it
            if section_cat in sections.keys():
                sections[section_cat].append(section)

            else:
                sections[section_cat] = [section]

        # The SynchroClass is a wrapper for several SectionTimeTables and additional info
        # essentially, an internal dictionnary gives infos on all the sections
        # available for each section "category", as we need at least one
        # valid combination of each category
        return SynchroClass(class_name, sections)


    def end(self):
        self.driver.quit()

# A controller class that manages multiple Browsers over multiple threads,
# and coordinates them to retrieve information from the student center at
# an optimised rate
class BrowserController():
    def __init__(self, ui, threads = 4):
        tqdm.write(f"[PRIMUS: BrowserController] - creating {threads} browser instances...")
        with concurrent.futures.ThreadPoolExecutor() as exe:
            futures = [exe.submit(Browser, self) for t in range(threads)]
        self.browsers = [b.result() for b in futures]
        tqdm.write(f"[PRIMUS: BrowserController] - browser instances ready.")
        self.ui = ui

    def login_sequence(self, user, unip):
        """
        The first sequence. Will have all the browsers go to the login page
        of synchro and attempt to login with the provided creditentials.
        TODO: differential login sequence to avoid locking with bad creditentials

        Parameters
        ----------
        user : str
            The username with which the browsers will attempt to connect (pXXXXXX)
        unip : str
            The password (UNIP) with which the browsers will attempt to connect

        Returns
        -------
        result : bool
            True if the connection was succesfull, False if anything wrong happened

        """
        tqdm.write("[PRIMUS: BrowserController] - naviguating browsers to login page...")
        with concurrent.futures.ThreadPoolExecutor() as exe:
            futures = [exe.submit(browser.to_login) for browser in self.browsers]

        tqdm.write(f"[PRIMUS: BrowserController] - attempting to connect as {user}...")
        with concurrent.futures.ThreadPoolExecutor() as exe:
            futures = [exe.submit(browser.login_with, user, unip) for browser in self.browsers]

        result = futures[0].result()
        tqdm.write(f"[PRIMUS: BrowserController] - sequence complete. Browser 0 returned a login status of: {result}")
        return result

    def session_selection_sequence(self):
        """
        The second sequence. Should only be called after a succesful login sequence
        This will get all the browsers to the session selection page, and acquire the
        available sessions so the user can choose which one to use

        Returns
        -------
        sessions : list(str)
            A list containing all the available sessions the user can choose from

        """
        tqdm.write("[PRIMUS: BrowserController] - attempting to retrieve sessions...")
        with concurrent.futures.ThreadPoolExecutor() as exe:
            futures = [exe.submit(browser.to_session_selection) for browser in self.browsers]

        sessions = self.browsers[0].acquire_sessions()
        tqdm.write(f"[PRIMUS: BrowserController] - sequence complete. Browser 0 found {len(sessions)} sessions.")
        return sessions

    def session_timetable_sequence(self, sess_id):
        """
        The third sequence. This will save the session choice, and will have the
        leader browser (browser 0) go to the "search" page, and acquire the
        timetable of currently selected classes from there.

        Parameters
        ----------
        sess_id : int
            The id to use in the list of sessions.

        """
        tqdm.write(f"[PRIMUS: BrowserController] - acquiring root timetable from session {sess_id}.")
        # with concurrent.futures.ThreadPoolExecutor() as exe:
            # futures = [exe.submit(browser.select_session, sess_id) for browser in self.browsers]
        self.browsers[0].select_session(sess_id)
        self.ttb, self.ttb_url = self.browsers[0].acquire_timetable()
        self.sess_id = sess_id

    def acquire_bloc_distribution_sequence(self):
        """
        The fourth sequence. This should only be called after the third sequence.
        The browser 0 will search one time for all available class to acquire the number
        of blocs. This is done so blocs can be distributed upon all browsers in
        different threads

        """
        tqdm.write("[PRIMUS: BrowserController] - maneuvering browser 0 to acquire all blocs")
        self.browsers[0].to_class_list()
        self.blocs = self.browsers[0].acquire_all_blocs(self.ttb_url)
        tqdm.write(f"[PRIMUS: BrowserController] - {len(self.blocs)} blocs were found. Beginning distribution.")

        # Calculate the number of blocs per browsers (there might be extras)
        distribution_indice = len(self.blocs)//len(self.browsers)
        print(distribution_indice)

        # Creates a list of list where every sublist is a list of blocs for a browser
        # to investigate
        iblocs = iter(self.blocs)
        self.dis = [list(bloc) for bloc in zip(*[iblocs for i in range(distribution_indice)])]
        nblocs = iter([i for i,b in enumerate(self.blocs)])
        self.dis_nb = [list(bloc) for bloc in zip(*[nblocs for i in range(distribution_indice)])]

        # If the division had extras, we need to redistribute them over the non-extra subslists
        if len(self.dis) != len(self.browsers):
            extras = self.dis.pop()
            # The length of the extras will never surpass the number of browsers (euclidian division principal)
            for i, extra in enumerate(extras):
                self.dis[i].append(extra)
        tqdm.write(f"[PRIMUS: BrowserController] - distribution of {len(self.blocs)} blocs over {len(self.dis)} threads ready.")

    def main_extraction_sequence(self):
        """
        The big daddy sequence. This will get distribute the blocs upon each
        browsers, and unleash them to acquire all the data over different threads

        """
        if not hasattr(self, "dis"):
            return

        with concurrent.futures.ThreadPoolExecutor() as exe:
            for i, browser in enumerate(self.browsers):
                blocs, blocs_nb = self.dis[i], self.dis_nb[i]
                exe.submit(browser.get_data_from_blocs, blocs_nb, self.ttb_url)

        tqdm.write("[PRIMUS: BrowserController] - main sequence is done!")

    def end_sequence(self):
        """
        This should ALWAYS be called no matter what at the end, even if exceptions
        were raised. Failure to execute this procedure will result in heavy files
        (that should be temporary) not being deleted by geckodriver.
        If you fail to call this sequence, the location of the temporary files
        should be: AppData/Local/Temp, any folrder name "rust_mozprofile*****"
        so you can delete these by hand.
        Again, this is easely avoided by just making sure this is called no matter what

        """

        tqdm.write("[PRIMUS: BrowserController] - attempting to safely end all browser instances.")
        with concurrent.futures.ThreadPoolExecutor() as exe:
            for browser in self.browsers:
                exe.submit(browser.end)
        tqdm.write("[PRIMUS: BrowserController] - browsers were safely closed.")

    def check_compatibility(self, class_object):
        """
        This method is called by the browsers in a thread to check compatibility
        of a class.

        Parameters
        ----------
        class_object : SynchroClass
            The SynchroClass object made by the browser.

        """
        if not hasattr(self, "ttb"):
            tqdm.write("[PRIMUS: BrowserController] - Attempted to check a class compatibility without reference table... This is problematics")
            return

        timetree = TimeTree(self.ttb)
        tqdm.write(f"[PRIMUS: Browser] - now testing: {class_object.class_name}")
        for i, sections_keyval in enumerate(class_object.sections_timetable.items()):
            sections = sections_keyval[1]
            sections_key = sections_keyval[0]
            tree_expand_results = list()

            for section in sections:
                tree_expand_results.append(timetree.extand(section))

            timetree.commit_new_leafs()

            if not any(tree_expand_results):
                tqdm.write(f"[PRIMUS: Browser] - {class_object.class_name} is INVALID")
                self.ui.add_result(class_object.class_name, "invalid")
                return

        else:
            if timetree.check_fully_known():
                tqdm.write(f"[PRIMUS: Browser] - {class_object.class_name} is VALID")
                self.ui.add_result(class_object.class_name, "valid")
            else:
                tqdm.write(f"[PRIMUS: Browser] - {class_object.class_name} is UNKNOWN")
                self.ui.add_result(class_object.class_name, "unknown")