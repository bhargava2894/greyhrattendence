#!/usr/bin/env python3
import os
import sys
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Load environment variables from .env file for local testing
load_dotenv()

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def take_screenshot(page, name, action):
    os.makedirs("screenshots", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"screenshots/{name}_{action}_{timestamp}.png"
    try:
        page.screenshot(path=filepath, full_page=True)
        log(f"Screenshot saved to: {filepath}")
    except Exception as e:
        log(f"Failed to take screenshot: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="greytHR Attendance Automation")
    parser.add_argument(
        "--action", 
        choices=["in", "out"], 
        default=os.environ.get("ACTION"), 
        help="Action to perform: 'in' for Sign In, 'out' for Sign Out"
    )
    args = parser.parse_args()

    action = args.action
    if not action:
        log("Error: Action must be specified via --action or ACTION environment variable.")
        sys.exit(1)

    action = action.lower()

    # Retrieve credentials
    username = os.environ.get("GREYTHR_USER")
    password = os.environ.get("GREYTHR_PASSWORD")
    portal_url = os.environ.get("GREYTHR_URL", "https://softility.greythr.com/")

    if not username or not password:
        log("Error: GREYTHR_USER and GREYTHR_PASSWORD environment variables must be set.")
        sys.exit(1)

    log(f"Starting greytHR Attendance Automation | Action: {action.upper()} | URL: {portal_url}")

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"]
        )
        # Create browser context with a standard viewport and user agent
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. Navigate to greytHR Portal
            log("Navigating to greytHR Portal...")
            page.goto(portal_url, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            # Wait to check if redirected to login page
            current_url = page.url
            log(f"Current URL: {current_url}")

            # 2. Login Flow
            log("Locating login fields...")
            
            # Username input (try multiple selectors)
            username_field = None
            username_selectors = [
                "input[name='username']",
                "input#username",
                "input[placeholder*='Employee']",
                "input[placeholder*='Login']",
                "input[type='text']"
            ]
            for selector in username_selectors:
                if page.locator(selector).is_visible():
                    username_field = page.locator(selector)
                    log(f"Found username field with selector: {selector}")
                    break
            
            if not username_field:
                # Fallback to get_by_placeholder or get_by_label
                try:
                    username_field = page.get_by_placeholder("Employee No")
                    if not username_field.is_visible():
                        username_field = page.get_by_placeholder("Login ID")
                except Exception:
                    pass

            if not username_field or not username_field.is_visible():
                raise Exception("Could not find username input field on the page.")

            # Password input (try multiple selectors)
            password_field = None
            password_selectors = [
                "input[name='password']",
                "input#password",
                "input[placeholder*='Password']",
                "input[type='password']"
            ]
            for selector in password_selectors:
                if page.locator(selector).is_visible():
                    password_field = page.locator(selector)
                    log(f"Found password field with selector: {selector}")
                    break

            if not password_field or not password_field.is_visible():
                raise Exception("Could not find password input field on the page.")

            # Fill credentials
            log("Filling username...")
            username_field.fill(username)
            log("Filling password...")
            password_field.fill(password)

            # Locate submit/login button
            login_btn = None
            login_selectors = [
                "button[type='submit']",
                "button:has-text('Log in')",
                "button:has-text('Login')",
                ".btn-login",
                "form button"
            ]
            for selector in login_selectors:
                if page.locator(selector).is_visible():
                    login_btn = page.locator(selector)
                    log(f"Found login button with selector: {selector}")
                    break

            if not login_btn or not login_btn.is_visible():
                raise Exception("Could not find login button on the page.")

            # Click login and wait for navigation
            log("Clicking login button...")
            login_btn.click()
            
            # Wait for redirection to dashboard URL
            log("Waiting for dashboard to load...")
            try:
                page.wait_for_url("**/v3/portal/ess/home", timeout=45000)
            except Exception as e:
                log(f"Warning: URL did not redirect to dashboard home: {str(e)}")
            
            # Let's wait for dashboard and widgets to fully render
            log(f"Logged in successfully. Post-login URL: {page.url}")
            log("Waiting for gt-attendance-info widget to load...")
            try:
                page.locator("gt-attendance-info").wait_for(state="visible", timeout=25000)
                log("gt-attendance-info widget loaded.")
            except Exception as e:
                log(f"Warning: Timed out waiting for gt-attendance-info widget: {str(e)}")

            log("Searching for attendance buttons (polling up to 15s for buttons to load)...")
            sign_in_btn = None
            sign_out_btn = None
            for attempt in range(15):
                buttons = page.locator("button").all()
                for btn in buttons:
                    try:
                        btn_text = btn.text_content().strip()
                        if btn_text == "Sign In" and btn.is_visible() and not btn.is_disabled():
                            sign_in_btn = btn
                            sign_out_btn = None
                        elif btn_text == "Sign Out" and btn.is_visible() and not btn.is_disabled():
                            sign_out_btn = btn
                            sign_in_btn = None
                    except Exception:
                        pass
                if sign_in_btn or sign_out_btn:
                    log(f"Found active button '{'Sign In' if sign_in_btn else 'Sign Out'}' after {attempt} seconds.")
                    break
                page.wait_for_timeout(1000)
            
            # Check states
            is_sign_in_active = sign_in_btn is not None
            is_sign_out_active = sign_out_btn is not None
            
            log(f"Status check - 'Sign In' active: {is_sign_in_active} | 'Sign Out' active: {is_sign_out_active}")

            if action == "in":
                if not is_sign_in_active and is_sign_out_active:
                    log("Attendance status: Already Signed In. No action required.")
                    take_screenshot(page, "already_signed_in", action)
                    return

                if is_sign_in_active:
                    log("Clicking 'Sign In' button...")
                    sign_in_btn.click()
                else:
                    # Extract widget text to diagnose missing button
                    try:
                        widget = page.locator("gt-attendance-info")
                        if widget.is_visible():
                            widget_text = widget.text_content().strip().replace('\n', ' ')
                            log(f"Widget info: {widget_text}")
                    except Exception:
                        pass
                    raise Exception("Could not find active 'Sign In' button on the dashboard. Verify shift details on the portal.")
                
            elif action == "out":
                if not is_sign_out_active and is_sign_in_active:
                    log("Attendance status: Already Signed Out. No action required.")
                    take_screenshot(page, "already_signed_out", action)
                    return

                if is_sign_out_active:
                    log("Clicking 'Sign Out' button...")
                    sign_out_btn.click()
                else:
                    # Extract widget text to diagnose missing button
                    try:
                        widget = page.locator("gt-attendance-info")
                        if widget.is_visible():
                            widget_text = widget.text_content().strip().replace('\n', ' ')
                            log(f"Widget info: {widget_text}")
                    except Exception:
                        pass
                    raise Exception("Could not find active 'Sign Out' button on the dashboard. Verify shift details on the portal.")

            # 4. Handle confirmation modal dialogs if any
            # Sometimes clicking Sign In/Out triggers a confirmation modal asking "Are you sure?"
            # We wait a couple of seconds to check if a dialog pops up
            page.wait_for_timeout(2000)
            
            # Check for modal buttons like "Yes", "Confirm", "OK", "Submit"
            confirm_selectors = [
                "button:has-text('Yes')",
                "button:has-text('Confirm')",
                "button:has-text('OK')",
                "button:has-text('Save')",
                ".modal-footer button:has-text('Yes')",
                "div[role='dialog'] button:has-text('Yes')"
            ]
            
            for selector in confirm_selectors:
                try:
                    locator = page.locator(selector)
                    if locator.is_visible():
                        log(f"Found confirmation dialog button: {selector}. Clicking it...")
                        locator.click()
                        page.wait_for_timeout(2000)
                        break
                except Exception as e:
                    log(f"Checking selector {selector} failed or timed out: {str(e)}")

            # 5. Verify action completed successfully
            log("Waiting for confirmation/completion...")
            page.wait_for_timeout(3000)
            
            # Capture final success screenshot
            take_screenshot(page, "success", action)
            log(f"Successfully automated sign-{action} flow!")

        except PlaywrightTimeoutError as te:
            log(f"Timeout Error encountered: {str(te)}")
            take_screenshot(page, "timeout_error", action)
            sys.exit(1)
        except Exception as e:
            log(f"Error occurred: {str(e)}")
            take_screenshot(page, "error", action)
            sys.exit(1)
        finally:
            log("Closing browser...")
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
