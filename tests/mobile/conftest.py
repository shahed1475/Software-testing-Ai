import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="session")
def appium_server_url():
    """Appium server URL"""
    return os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")

@pytest.fixture(scope="session")
def android_capabilities():
    """Android device capabilities"""
    return {
        "platformName": "Android",
        "platformVersion": os.getenv("ANDROID_PLATFORM_VERSION", "13.0"),
        "deviceName": os.getenv("ANDROID_DEVICE_NAME", "Android Emulator"),
        "automationName": "UiAutomator2",
        "app": os.getenv("ANDROID_APP_PATH", ""),
        "appPackage": os.getenv("ANDROID_APP_PACKAGE", ""),
        "appActivity": os.getenv("ANDROID_APP_ACTIVITY", ""),
        "noReset": False,
        "fullReset": False,
        "newCommandTimeout": 300,
        "autoGrantPermissions": True
    }

@pytest.fixture(scope="session")
def ios_capabilities():
    """iOS device capabilities"""
    return {
        "platformName": "iOS",
        "platformVersion": os.getenv("IOS_PLATFORM_VERSION", "16.0"),
        "deviceName": os.getenv("IOS_DEVICE_NAME", "iPhone 14"),
        "automationName": "XCUITest",
        "app": os.getenv("IOS_APP_PATH", ""),
        "bundleId": os.getenv("IOS_BUNDLE_ID", ""),
        "noReset": False,
        "fullReset": False,
        "newCommandTimeout": 300,
        "autoAcceptAlerts": True
    }

@pytest.fixture
def android_driver(appium_server_url, android_capabilities):
    """Android driver fixture"""
    if not android_capabilities.get("app") and not android_capabilities.get("appPackage"):
        pytest.skip("No Android app configured")
    
    options = UiAutomator2Options()
    for key, value in android_capabilities.items():
        if value:  # Only set non-empty values
            options.set_capability(key, value)
    
    driver = webdriver.Remote(appium_server_url, options=options)
    driver.implicitly_wait(10)
    
    yield driver
    
    driver.quit()

@pytest.fixture
def ios_driver(appium_server_url, ios_capabilities):
    """iOS driver fixture"""
    if not ios_capabilities.get("app") and not ios_capabilities.get("bundleId"):
        pytest.skip("No iOS app configured")
    
    options = XCUITestOptions()
    for key, value in ios_capabilities.items():
        if value:  # Only set non-empty values
            options.set_capability(key, value)
    
    driver = webdriver.Remote(appium_server_url, options=options)
    driver.implicitly_wait(10)
    
    yield driver
    
    driver.quit()

@pytest.fixture
def mobile_driver(request, android_driver, ios_driver):
    """Generic mobile driver that returns appropriate driver based on platform"""
    platform = request.config.getoption("--platform", default="android")
    
    if platform.lower() == "ios":
        return ios_driver
    else:
        return android_driver

def pytest_addoption(parser):
    """Add command line options for mobile testing"""
    parser.addoption(
        "--platform",
        action="store",
        default="android",
        help="Mobile platform: android or ios"
    )
    parser.addoption(
        "--device",
        action="store",
        default="emulator",
        help="Device type: emulator, simulator, or real"
    )

@pytest.fixture(autouse=True)
def mobile_test_metadata(request):
    """Automatically capture mobile test metadata"""
    platform = request.config.getoption("--platform", default="android")
    device_type = request.config.getoption("--device", default="emulator")
    
    request.node.mobile_metadata = {
        "platform": platform,
        "device_type": device_type,
        "test_name": request.node.name,
        "test_file": request.node.fspath.basename
    }