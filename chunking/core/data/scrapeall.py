from playwright.sync_api import sync_playwright
import json
from pathlib import Path
import time
import re

cookies_path = Path("auth/allpyq_cookies.json")
output_file = Path("data/raw/CDSII_allpyq_clickversion.json")
output_file.parent.mkdir(exist_ok=True)

def find_correct_answer_by_clicking(card, page) -> tuple:
    try:
        option_inputs = card.query_selector_all("li.list-group-item")
        correct_answer_label = None
        correct_answer_text = None

        for i, opt in enumerate(option_inputs):
            input_tag = opt.query_selector("input")
            label_tag = opt.query_selector("label")
            span_tag = opt.query_selector("span.text-primary")

            if input_tag and label_tag and span_tag:
                label_letter = span_tag.inner_text().strip().replace(")", "")
                label_text = label_tag.inner_text().strip()
                full_option = f"{label_letter}) {label_text}"

                input_tag.click()
                try:
                    card.wait_for_selector("text='Correct Answer!'", timeout=500)
                    correct_answer_label = label_letter
                    correct_answer_text = full_option
                    input_tag.click()
                    time.sleep(0.2)
                    return correct_answer_label, correct_answer_text
                except Exception:
                    continue
        return correct_answer_label, correct_answer_text
    except Exception as e:
        print(f"❌ Error finding correct answer by clicking: {e}")
        return None, None

def extract_question_card(h5_elem, page) -> dict:
    try:
        question_text = h5_elem.inner_text().strip()
        card = h5_elem.evaluate_handle("node => node.closest('div.ques_ans')").as_element()

        options = []
        option_inputs = card.query_selector_all("li.list-group-item")

        for i, opt in enumerate(option_inputs):
            input_tag = opt.query_selector("input")
            label_tag = opt.query_selector("label")
            span_tag = opt.query_selector("span.text-primary")

            if input_tag and label_tag and span_tag:
                label_letter = span_tag.inner_text().strip().replace(")", "")
                label_text = label_tag.inner_text().strip()
                full_option = f"{label_letter}) {label_text}"
                options.append(full_option)

        correct_answer_label, correct_answer_text = find_correct_answer_by_clicking(card, page)

        meta_tag = card.query_selector("div.qustagsclass")
        year, subject, topic = None, None, None
        if meta_tag:
            meta_text = meta_tag.inner_text().strip()
            parts = [p.strip() for p in meta_text.split("//")]
            for p in parts:
                match = re.match(r"20\d{2}", p.strip())
                if match:
                    year = int(match.group())
                    break
            parts_wo_year = [p for p in parts if not (p.isdigit() and 2010 <= int(p) <= 2025)]
            if len(parts_wo_year) >= 2:
                subject = parts_wo_year[1]
            if len(parts_wo_year) >= 3:
                topic = parts_wo_year[2]

        return {
            "question": question_text,
            "options": options,
            "correct_answer_label": correct_answer_label,
            "correct_answer_text": correct_answer_text,
            "explanation": None,
            "exam": "CDSII",
            "year": year,
            "subject": subject,
            "topic": topic,
            "subtopic1": None,
            "subtopic2": None,
            "subtopic3": None,
            "subtopic4": None,
            "subtopic5": None,
            "difficulty": None,
            "cognitive_skill": None,
            "question_type": None,
            "source_chunk": None,
            "concept_tags": [],
            "test_series_id": None,
            "rephrases": [],
            "solve_hint": None,
            "revision_bucket": None,
            "last_seen": None,
            "history": []
        }
    except Exception as e:
        print(f"❌ Error parsing card: {e}")
        return None

def scrape_allpyq() -> None:
    all_data = []
    total_skips = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        if cookies_path.exists():
            with open(cookies_path, "r") as f:
                context.add_cookies(json.load(f))
            print("🍪 Cookies loaded.")
        else:
            print("❌ No cookies found. Run login_and_save_cookies.py first.")
            return

        page = context.new_page()
        page.goto("https://allpyq.com/home?page=1")
        input("🟢 Toggle 'CDSII' filter manually, then press ENTER to begin scraping...\n")
        page.wait_for_selector("h5.question", timeout=10000)

        pg = 1
        MAX_PAGES = 140

        while True:
            print(f"\n🔄 Scraping page {pg}...")

            h5_questions = page.query_selector_all("h5.question")
            prev_questions = [h.inner_text().strip() for h in h5_questions]
            prev_first = prev_questions[0] if prev_questions else ""

            if not h5_questions:
                debug_file = Path(f"debug_page_{pg}.html")
                with debug_file.open("w", encoding="utf-8") as f:
                    f.write(page.content())
                print(f"💾 Saved debug HTML to {debug_file}")

            page_count = 0
            for i, h5 in enumerate(h5_questions):
                print(f"  Processing question {i+1}/{len(h5_questions)}...")
                parsed = extract_question_card(h5, page)
                if parsed:
                    if parsed["options"] and parsed["correct_answer_label"]:
                        all_data.append(parsed)
                        page_count += 1
                        print(f"    ✅ Found answer: {parsed['correct_answer_label']}")
                    else:
                        total_skips += 1
                        print(f"    ⚠️ Skipped - no answer found")
                else:
                    total_skips += 1
                    print(f"    ❌ Failed to parse card")

            print(f"✅ Page {pg}: {page_count} saved | ⚠️ Skipped: {total_skips} (Total: {len(all_data)})")

            next_pg = pg + 1
            if next_pg > MAX_PAGES:
                print("🛑 Max page limit reached.")
                break

            try:
                selector = f"a.page-link[data-page='{next_pg}']"
                if not page.query_selector(selector):
                    print(f"🚫 Pagination button not found for page {next_pg}")
                    break

                print("🖱️ Clicking pagination link...")
                page.click(selector)
                time.sleep(2)

                print("⏳ Waiting for new questions to load...")
                page.wait_for_function(
                    f"""
                    () => {{
                        const q = document.querySelectorAll('h5.question');
                        return q.length > 0 && q[0].innerText.trim() !== {json.dumps(prev_first)};
                    }}
                    """,
                    timeout=30000
                )

                pg = next_pg
                time.sleep(1)

            except Exception as e:
                print(f"🚫 Could not load page {next_pg}: {e}")
                break

        browser.close()

    with output_file.open("w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n🎉 Done! Final saved: {len(all_data)} | Total skipped: {total_skips}")
    print(f"📁 Output: {output_file}")

if __name__ == "__main__":
    scrape_allpyq()