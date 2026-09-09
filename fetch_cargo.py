import asyncio
import os
from playwright.async_api import async_playwright
import pandas as pd

USERNAME = os.getenv("CARGO_USERNAME", "htninja")
PASSWORD = os.getenv("CARGO_PASSWORD", "spv123456")

async def function_run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # เพิ่ม User-Agent ให้เหมือนเบราว์เซอร์จริงเพื่อลดการโดนหน่วง/บล็อก
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("กำลังเข้าสู่ระบบ...")
        try:
            # 📌 ขยายเวลา Timeout เป็น 90000ms (90 วินาที)
            await page.goto("https://www.uneedcargo.com/login", wait_until="domcontentloaded", timeout=90000)
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลดหน้า Login: {e}")
            await browser.close()
            return

        # กรอกข้อมูลล็อกอิน
        await page.fill('input[name="username"]', USERNAME)
        await page.fill('input[name="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        
        await page.wait_for_timeout(5000)

        all_data = []

        for page_num in range(1, 6):
            target_url = f"https://www.uneedcargo.com/package/{page_num}/?qty=20&search=&type=&status="
            print(f"กำลังดึงข้อมูลหน้า {page_num}...")
            
            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=90000)
                await page.wait_for_selector("table", timeout=20000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"เกิดข้อผิดพลาดในการโหลดหน้า {page_num}: {e}")
                continue

            rows = await page.query_selector_all("table tbody tr")

            for row in rows:
                cols = await row.query_selector_all("td")
                col_texts = [(await col.inner_text()).strip() for col in cols]
                
                if len(col_texts) >= 5:
                    def get_val(idx):
                        return col_texts[idx] if idx < len(col_texts) else ""

                    all_data.append({
                        "หน้า": page_num,
                        "รหัสพัสดุ": get_val(0),
                        "รายการสั่งซื้อ": get_val(1),
                        "ชำระเงินค่าสินค้า": get_val(2),
                        "ประเภทสินค้า/ล็อต": get_val(3),
                        "เข้าโกดัง": get_val(4),
                        "ออกโกดัง": get_val(5),
                        "ถึงไทย": get_val(6),
                        "กิโล": get_val(7),
                        "คิว": get_val(8),
                        "จำนวน": get_val(12),
                        "ราคากิโล": get_val(13),
                        "ราคาคิว": get_val(14),
                        "หมายเหตุ": get_val(15),
                    })

        if all_data:
            df = pd.DataFrame(all_data)
            filename = "cargo_packages_p1-5.xlsx"
            df.to_excel(filename, index=False)
            print(f"\nบันทึกข้อมูลสำเร็จ! บันทึกทับลงในไฟล์: {filename} รวม {len(all_data)} รายการ")
        else:
            print("\nไม่พบข้อมูลพัสดุ")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(function_run())