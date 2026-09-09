import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

USERNAME = "htninja"  # ใส่ Username ของคุณ
PASSWORD = "spv123456"  # ใส่ Password ของคุณ

async def function_run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("กำลังเข้าสู่ระบบ...")
        await page.goto("https://www.uneedcargo.com/login", wait_until="domcontentloaded")
        
        # กรอกข้อมูลล็อกอิน
        await page.fill('input[name="username"]', USERNAME)
        await page.fill('input[name="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        
        # รอให้ล็อกอินเสร็จสมบูรณ์
        await page.wait_for_timeout(4000)

        all_data = [] # ตัวแปรสำหรับเก็บข้อมูลรวมจากทุกหน้า

        # วนลูปดึงข้อมูลตั้งแต่หน้า 1 ถึง 5
        for page_num in range(1, 6):
            target_url = f"https://www.uneedcargo.com/package/{page_num}/?qty=20&search=&type=&status="
            print(f"กำลังดึงข้อมูลหน้า {page_num}...")
            
            try:
                # ใช้ domcontentloaded เพื่อป้องกันการค้างจนโดน Abort
                await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector("table", timeout=15000)
                await page.wait_for_timeout(2000) # รอให้ตารางโหลดข้อมูลเสร็จ
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

        # บันทึกข้อมูลรวมลง Excel
        if all_data:
            df = pd.DataFrame(all_data)
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"cargo_packages_p1-5_{today}.xlsx"
            df.to_excel(filename, index=False)
            print(f"\nบันทึกข้อมูลสำเร็จ! รวมทั้งหมด {len(all_data)} รายการ ลงในไฟล์: {filename}")
        else:
            print("\nไม่พบข้อมูลพัสดุในหน้าดังกล่าว")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(function_run())