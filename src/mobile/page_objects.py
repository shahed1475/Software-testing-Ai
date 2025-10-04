from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

class BasePage:
    """Base page object for mobile testing"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def find_element(self, locator_type, locator_value, timeout=10):
        """Find element with explicit wait"""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located((locator_type, locator_value)))
    
    def find_elements(self, locator_type, locator_value):
        """Find multiple elements"""
        return self.driver.find_elements(locator_type, locator_value)
    
    def click_element(self, locator_type, locator_value, timeout=10):
        """Click element with explicit wait"""
        element = self.find_element(locator_type, locator_value, timeout)
        element.click()
        return element
    
    def send_keys(self, locator_type, locator_value, text, timeout=10):
        """Send keys to element"""
        element = self.find_element(locator_type, locator_value, timeout)
        element.clear()
        element.send_keys(text)
        return element
    
    def get_text(self, locator_type, locator_value, timeout=10):
        """Get text from element"""
        element = self.find_element(locator_type, locator_value, timeout)
        return element.get_attribute("text")
    
    def is_element_present(self, locator_type, locator_value, timeout=5):
        """Check if element is present"""
        try:
            self.find_element(locator_type, locator_value, timeout)
            return True
        except TimeoutException:
            return False
    
    def scroll_to_element(self, locator_type, locator_value, max_scrolls=5):
        """Scroll to find element"""
        for _ in range(max_scrolls):
            if self.is_element_present(locator_type, locator_value, 2):
                return self.find_element(locator_type, locator_value)
            self.scroll_down()
        raise TimeoutException(f"Element not found after {max_scrolls} scrolls")
    
    def scroll_down(self):
        """Scroll down on the screen"""
        screen_size = self.driver.get_window_size()
        start_x = screen_size["width"] // 2
        start_y = screen_size["height"] * 3 // 4
        end_y = screen_size["height"] // 4
        self.driver.swipe(start_x, start_y, start_x, end_y, 1000)
        time.sleep(1)
    
    def scroll_up(self):
        """Scroll up on the screen"""
        screen_size = self.driver.get_window_size()
        start_x = screen_size["width"] // 2
        start_y = screen_size["height"] // 4
        end_y = screen_size["height"] * 3 // 4
        self.driver.swipe(start_x, start_y, start_x, end_y, 1000)
        time.sleep(1)
    
    def take_screenshot(self, filename):
        """Take screenshot"""
        self.driver.save_screenshot(f"artifacts/{filename}.png")

class LoginPage(BasePage):
    """Login page object"""
    
    # Locators
    USERNAME_INPUT = (AppiumBy.ID, "username")
    PASSWORD_INPUT = (AppiumBy.ID, "password")
    LOGIN_BUTTON = (AppiumBy.ID, "login_button")
    ERROR_MESSAGE = (AppiumBy.ID, "error_message")
    
    # Alternative locators for different apps
    USERNAME_INPUT_ALT = (AppiumBy.XPATH, "//*[contains(@resource-id, 'username') or contains(@content-desc, 'username')]")
    PASSWORD_INPUT_ALT = (AppiumBy.XPATH, "//*[contains(@resource-id, 'password') or contains(@content-desc, 'password')]")
    LOGIN_BUTTON_ALT = (AppiumBy.XPATH, "//*[contains(@text, 'Login') or contains(@text, 'Sign In')]")
    
    def enter_username(self, username):
        """Enter username"""
        try:
            self.send_keys(*self.USERNAME_INPUT, username)
        except TimeoutException:
            self.send_keys(*self.USERNAME_INPUT_ALT, username)
    
    def enter_password(self, password):
        """Enter password"""
        try:
            self.send_keys(*self.PASSWORD_INPUT, password)
        except TimeoutException:
            self.send_keys(*self.PASSWORD_INPUT_ALT, password)
    
    def click_login(self):
        """Click login button"""
        try:
            self.click_element(*self.LOGIN_BUTTON)
        except TimeoutException:
            self.click_element(*self.LOGIN_BUTTON_ALT)
    
    def login(self, username, password):
        """Perform complete login"""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
    
    def get_error_message(self):
        """Get error message text"""
        try:
            return self.get_text(*self.ERROR_MESSAGE)
        except TimeoutException:
            return None

class HomePage(BasePage):
    """Home page object"""
    
    # Locators
    MENU_BUTTON = (AppiumBy.ID, "menu_button")
    SEARCH_BUTTON = (AppiumBy.ID, "search_button")
    PROFILE_BUTTON = (AppiumBy.ID, "profile_button")
    
    # Alternative locators
    MENU_BUTTON_ALT = (AppiumBy.XPATH, "//*[contains(@content-desc, 'menu') or contains(@text, 'Menu')]")
    SEARCH_BUTTON_ALT = (AppiumBy.XPATH, "//*[contains(@content-desc, 'search') or contains(@text, 'Search')]")
    
    def click_menu(self):
        """Click menu button"""
        try:
            self.click_element(*self.MENU_BUTTON)
        except TimeoutException:
            self.click_element(*self.MENU_BUTTON_ALT)
    
    def click_search(self):
        """Click search button"""
        try:
            self.click_element(*self.SEARCH_BUTTON)
        except TimeoutException:
            self.click_element(*self.SEARCH_BUTTON_ALT)
    
    def click_profile(self):
        """Click profile button"""
        self.click_element(*self.PROFILE_BUTTON)

class SearchPage(BasePage):
    """Search page object"""
    
    # Locators
    SEARCH_INPUT = (AppiumBy.ID, "search_input")
    SEARCH_BUTTON = (AppiumBy.ID, "search_submit")
    SEARCH_RESULTS = (AppiumBy.ID, "search_results")
    
    # Alternative locators
    SEARCH_INPUT_ALT = (AppiumBy.XPATH, "//*[contains(@resource-id, 'search') and contains(@class, 'EditText')]")
    
    def enter_search_query(self, query):
        """Enter search query"""
        try:
            self.send_keys(*self.SEARCH_INPUT, query)
        except TimeoutException:
            self.send_keys(*self.SEARCH_INPUT_ALT, query)
    
    def click_search(self):
        """Click search button"""
        self.click_element(*self.SEARCH_BUTTON)
    
    def search(self, query):
        """Perform complete search"""
        self.enter_search_query(query)
        self.click_search()
    
    def get_search_results(self):
        """Get search results"""
        return self.find_elements(*self.SEARCH_RESULTS)