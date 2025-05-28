from playwright.sync_api import sync_playwright
import os
import time
import re

output_dir = "maradmin_pdfs"
os.makedirs(output_dir, exist_ok=True)

# Original message URLs
urls = [
    "https://www.marines.mil/News/Messages/Messages-Display/Article/4188275/officer-candidates-school-physical-fitness-test-induction-and-graduation-standa/",
    "https://www.marines.mil/News/Messages/Messages-Display/Article/4188879/armed-forces-day/",
    "https://www.marines.mil/News/Messages/Messages-Display/Article/4187836/announcement-of-the-calendar-year-2024-male-and-female-athletes-of-the-year/",
    "https://www.marines.mil/News/Messages/Messages-Display/Article/4187760/cancellation-of-maradmin-229-22/",
    "https://www.marines.mil/News/Messages/Messages-Display/Article/4187616/announcement-of-reserve-sergeants-major-slate-for-calendar-year-20252026-cy25cy/"
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()

    for i, original_url in enumerate(urls):
        print(f"📄 Processing: {original_url}")
        try:
            # Extract article ID from original URL
            match = re.search(r"Article/(\d+)", original_url)
            if not match:
                raise Exception("No article ID found in URL")
            article_id = match.group(1)

            # Build Print.aspx version
            print_url = f"https://www.marines.mil/DesktopModules/ArticleCS/Print.aspx?PortalId=1&ModuleId=542&Article={article_id}"

            page = context.new_page()
            page.goto(print_url, timeout=15000)
            page.wait_for_timeout(2000)

            # Use simplified title from original page for filename
            title_parts = original_url.rstrip("/").split("/")[-1].split("-")[:8]
            filename = f"{i+1:02d}_" + "_".join(title_parts) + ".pdf"
            filepath = os.path.join(output_dir, filename)

            page.pdf(path=filepath, format="A4", print_background=True)
            print(f"✅ Saved to {filepath}")

            page.close()
            time.sleep(1)

        except Exception as e:
            print(f"❌ Failed to process {original_url}: {e}")

    browser.close()

print("\n🎯 PDF generation from Print.aspx complete.")
