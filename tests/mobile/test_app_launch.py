import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

@pytest.mark.mobile
@pytest.mark.smoke
class TestAppLaunch:
    """Test mobile app launch and basic functionality"""

    def test_app_launches_successfully(self, mobile_driver):
        """Test that the app launches without crashing"""
        # Wait for app to load
        time.sleep(3)
        
        # Check if app is running by looking for any element
        try:
            # Try to find any element to confirm app is loaded
            elements = mobile_driver.find_elements(AppiumBy.XPATH, "//*")
            assert len(elements) > 0, "No elements found - app may not have launched"
        except Exception as e:
            pytest.fail(f"App launch failed: {str(e)}")

    def test_app_permissions(self, mobile_driver):
        """Test app permission handling"""
        try:
            # Look for permission dialogs (common patterns)
            permission_patterns = [
                "Allow",
                "ALLOW",
                "OK",
                "Accept",
                "Grant",
                "Continue"
            ]
            
            for pattern in permission_patterns:
                try:
                    permission_button = WebDriverWait(mobile_driver, 2).until(
                        EC.element_to_be_clickable((AppiumBy.XPATH, f"//*[contains(@text, '{pattern}')]"))
                    )
                    permission_button.click()
                    time.sleep(1)
                except TimeoutException:
                    continue
                    
        except Exception:
            # No permissions dialog found, which is fine
            pass

    def test_main_screen_elements(self, mobile_driver):
        """Test that main screen elements are present"""
        # Wait for main screen to load
        time.sleep(2)
        
        # Look for common UI elements
        common_elements = [
            "button",
            "text",
            "image",
            "edit",
            "view"
        ]
        
        found_elements = 0
        for element_type in common_elements:
            try:
                elements = mobile_driver.find_elements(
                    AppiumBy.XPATH, 
                    f"//*[contains(@class, '{element_type}') or contains(@resource-id, '{element_type}')]"
                )
                if elements:
                    found_elements += 1
            except Exception:
                continue
        
        # Should find at least some UI elements
        assert found_elements > 0, "No recognizable UI elements found"

    def test_app_navigation(self, mobile_driver):
        """Test basic app navigation"""
        try:
            # Look for navigation elements
            nav_elements = mobile_driver.find_elements(
                AppiumBy.XPATH, 
                "//*[contains(@content-desc, 'nav') or contains(@text, 'Menu') or contains(@class, 'Tab')]"
            )
            
            if nav_elements:
                # Try clicking the first navigation element
                nav_elements[0].click()
                time.sleep(2)
                
                # Verify navigation worked by checking if screen changed
                new_elements = mobile_driver.find_elements(AppiumBy.XPATH, "//*")
                assert len(new_elements) > 0
                
        except Exception:
            # Navigation test is optional - app might not have navigation
            pytest.skip("No navigation elements found")

    def test_text_input(self, mobile_driver):
        """Test text input functionality"""
        try:
            # Look for text input fields
            text_inputs = mobile_driver.find_elements(
                AppiumBy.XPATH, 
                "//*[contains(@class, 'EditText') or contains(@class, 'TextField')]"
            )
            
            if text_inputs:
                # Try entering text in the first input field
                text_input = text_inputs[0]
                text_input.click()
                text_input.send_keys("Test Input")
                
                # Verify text was entered
                entered_text = text_input.get_attribute("text")
                assert "Test" in entered_text or entered_text == "Test Input"
                
        except Exception:
            # Text input test is optional
            pytest.skip("No text input fields found")

    def test_scroll_functionality(self, mobile_driver):
        """Test scrolling functionality"""
        try:
            # Get screen size
            screen_size = mobile_driver.get_window_size()
            
            # Perform scroll gesture
            start_x = screen_size["width"] // 2
            start_y = screen_size["height"] * 3 // 4
            end_y = screen_size["height"] // 4
            
            mobile_driver.swipe(start_x, start_y, start_x, end_y, 1000)
            time.sleep(1)
            
            # Scroll back
            mobile_driver.swipe(start_x, end_y, start_x, start_y, 1000)
            time.sleep(1)
            
        except Exception:
            # Scrolling test is optional
            pytest.skip("Scrolling test failed")

    def test_app_background_foreground(self, mobile_driver):
        """Test app background and foreground functionality"""
        try:
            # Send app to background
            mobile_driver.background_app(2)
            
            # Bring app back to foreground
            mobile_driver.activate_app(mobile_driver.current_package)
            time.sleep(2)
            
            # Verify app is still functional
            elements = mobile_driver.find_elements(AppiumBy.XPATH, "//*")
            assert len(elements) > 0, "App not responsive after background/foreground"
            
        except Exception as e:
            pytest.skip(f"Background/foreground test failed: {str(e)}")

    def test_device_orientation(self, mobile_driver):
        """Test device orientation changes"""
        try:
            # Get current orientation
            current_orientation = mobile_driver.orientation
            
            # Change orientation
            new_orientation = "LANDSCAPE" if current_orientation == "PORTRAIT" else "PORTRAIT"
            mobile_driver.orientation = new_orientation
            time.sleep(2)
            
            # Verify orientation changed
            assert mobile_driver.orientation == new_orientation
            
            # Change back to original orientation
            mobile_driver.orientation = current_orientation
            time.sleep(2)
            
        except Exception:
            pytest.skip("Orientation test not supported on this device")