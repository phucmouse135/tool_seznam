import asyncio
from playwright.async_api import async_playwright
from utils import Logger, ProxyManager, BrowserUtils , DataHelper , FileManager, OnlineSimHelper
from config import Config

# --- CẤU HÌNH TỔNG ---
PROXY_API_URL = Config.PROXY_API_BASE
TARGET_CONFIG = Config.TARGET_CONFIG
NUM_THREADS = Config.NUM_THREADS
BASE_PORT = Config.BASE_PORT
SEMAPHORE_LIMIT = Config.SEMAPHORE_LIMIT
RETRY_LIMIT = Config.RETRY_LIMIT

# --- MODULE 1: WORKER XỬ LÝ (LOGIC) ---
async def worker(thread_id, port, semaphore, data_chunk):
    # Setup Proxy URL (Local)
    # local_proxy = f"http://127.0.0.1:{port}"

    async with semaphore:  # 1. Chiếm slot chạy
        Logger.info(thread_id, f"🚀 Khởi động Worker trên Port {port}")
        
        # Init IP lần đầu cho chắc ăn
        # ProxyManager.rotate_ip(port, thread_id=thread_id)

        # 2. Bật Playwright MỘT LẦN cho cả lô data này (Tiết kiệm RAM)
        async with async_playwright() as p:
            # Launch Browser (Reuse browser instance)
            browser = await p.chromium.launch(
                headless=False,
                args=BrowserUtils.get_launch_args()
            )

            # 3. Duyệt qua từng tài khoản trong gói data
            for item in data_chunk:
                auth = item.split("|")
                username = auth[0]  # Giả sử item là username
                password = auth[1] if len(auth) > 1 else "DefaultPass123!"
                phone_number = ""
                failed_reason = ""
                Logger.info(thread_id, f"▶️ Đang xử lý: {username}")
                isOk = False

                # 4. Cơ chế RETRY cho từng Item cụ thể
                for attempt in range(Config.RETRY_LIMIT):
                    context = None
                    try:
                        print(f"[Thread {thread_id}] Attempt {attempt+1} for {username}")
                        # Tạo Context mới cho mỗi acc (Sạch sẽ cookie)
                        context, page = await BrowserUtils.create_stealth_context(
                            browser, port,
                            TARGET_CONFIG["timezone"],
                            TARGET_CONFIG["locale"],
                            TARGET_CONFIG["geolocation"]
                        )

                        # --- CHẶN TÀI NGUYÊN TRƯỚC KHI ĐI ---
                        # await BrowserUtils.block_resources(page)

                        # Check IP (Optional)
                        # await page.goto("https://whoer.net", timeout=60000)
                        
                        # --- [MAIN LOGIC] ---
                        Logger.info(thread_id, "Truy cập Seznam...")
                        
                        # Tăng timeout lên 60s
                        await page.goto(
                            "https://registrace.seznam.cz/?service=ucet&return_url=https%3A%2F%2Fucet.seznam.cz" , timeout=60000
                        )
                        
                        Logger.info(thread_id, "Trang đăng ký đã tải xong.")
                        await page.wait_for_load_state("networkidle")
                        
                        
                        # Click Đăng ký
                        reg_btn = page.locator("#register form.intro button.official")
                        if await reg_btn.is_visible(timeout=10000):
                            await reg_btn.click()
                        else:
                            raise Exception("Không tìm thấy nút đăng ký")

                        # Điền form
                        print("Điền username...", username)
                        input_username = page.locator("#register-username")
                        await input_username.click()
                        await input_username.press("Control+A")
                        await input_username.press("Backspace")
                        await input_username.press_sequentially(username, delay=100)
                        print("Điền xong username.")
                        BrowserUtils.random_sleep(1,2)
                        
                        print("Fill password...", password)
                        input_password = page.locator("#register > form.main > label.magic.password.errorable > input[type=password]")
                        await input_password.fill("")
                        await input_password.press_sequentially(password, delay=100)  
                        print("Điền xong password.")
                        BrowserUtils.random_sleep(1,2)
                        
                        # press ENTER to submit
                        await page.keyboard.press("Enter")
                        await page.wait_for_load_state("networkidle")
                        await BrowserUtils.random_sleep(1,2)
                        
                        # check if phone not null 
                        if(len(phone_number) == 0): 
                            print("Call api to get phone number...")
                            
                            tzid = None
                            for _retry in range(10):
                                result = await OnlineSimHelper.get_number(service="seznam", country=420)
                                if result:
                                    tzid, phone_number = result
                                    print("Received phone number:", phone_number)
                                    break
                                Logger.warning(thread_id, f"⚠️ Lấy số thất bại (Lần {_retry+1}/10). Đợi 2s...")
                                await asyncio.sleep(2)
                            
                            if not tzid:
                                Logger.error(thread_id, "❌ Đã thử 10 lần không lấy được số. Dừng chương trình!")
                                import sys
                                sys.exit(1)
                        
                        print("Fill phone number...", phone_number)
                        input_phone = page.locator("#register > form.phone > label.magic.phone.errorable > input[type=text]")
                        await input_phone.fill("")
                        await input_phone.press_sequentially(phone_number, delay=100)  
                        await page.keyboard.press("Enter")
                        await page.wait_for_load_state("networkidle")
                        print("Điền xong phone number.")
                        await BrowserUtils.random_sleep(1,2)
                        
                        # <div class="alert" style="left: 680px; top: 259px;"><p>Registrace nebyla dokončena z důvodu prevence hromadných/robotických registrací. Zkuste registraci zopakovat později.</p><div><button type="submit">Rozumím</button></div></div>
                        pop_up_locator = page.locator("div.alert")
                        if await pop_up_locator.is_visible(timeout=10000):
                            pop_up_text = await pop_up_locator.inner_text()
                            Logger.error(thread_id, f"⚠️ Phát hiện pop-up lỗi: {pop_up_text}")
                            failed_reason = "IP_BANNED"
                            raise Exception(f"IP_BANNED: {pop_up_text}")
                        
                        # xuat hien error khong hop le tren form Bylo posláno příliš SMS. Další lze odeslat za 24h.
                        error_locator = page.locator("div.error")
                        if await error_locator.is_visible(timeout=10000):
                            error_text = await error_locator.inner_text()
                            Logger.error(thread_id, f"⚠️ Phát hiện lỗi form: {error_text}")
                            failed_reason = "SMS_SPAM_LIMIT"
                            raise Exception(f"SMS_SPAM_LIMIT: {error_text}")
                        
                        # dien code xac minh 
                        print("Chờ nhận code xác minh...")
                        try:
                            code = await OnlineSimHelper.wait_for_code(tzid =tzid, timeout=180)
                        except Exception as e:
                            raise Exception(f"Lỗi nhận code: {e}")
                        if not code:
                            # Nếu không có code thì lỗi NO_CODE
                            failed_reason = "NO_CODE"
                            raise Exception("NO_CODE: Không nhận được code xác minh trong thời gian chờ.")
                    
                        print("Nhận được code:", code)
                        
                        input_code = page.locator("#register > form.phone-verification > label.magic.code.errorable > input[type=text]")
                        await input_code.fill("")
                        await input_code.press_sequentially(code, delay=100)
                        await page.wait_for_load_state("networkidle")
                        print("Điền xong code xác minh.")
                        
                        # press ENTER to submit final form
                        await page.keyboard.press("Enter")
                        await page.wait_for_load_state("networkidle")
                    
                        # sau do chọn I agree and continue (<button type="submit" data-action="ok"><font dir="auto" style="vertical-align: inherit;"><font dir="auto" style="vertical-align: inherit;">I agree and continue</font></font></button>) 
                        agree_btn = page.locator("button[data-action='ok']")
                        if await agree_btn.is_visible(timeout=10000):
                            await agree_btn.click()
                            await page.wait_for_load_state("networkidle")
                        else:
                            raise Exception("Không tìm thấy nút I agree and continue")
                        
                        #  sau do chờ giao diện load tiến hành nhấn <button type="submit" class="back" data-locale="back_to_inbox"><font dir="auto" style="vertical-align: inherit;"><font dir="auto" style="vertical-align: inherit;">Quay lại Email</font></font></button>
                        back_btn = page.locator("button.back[data-locale='back_to_inbox']")
                        if await back_btn.is_visible(timeout=10000):
                            await back_btn.click()
                            await page.wait_for_load_state("networkidle")
                        else:
                            raise Exception("Không tìm thấy nút Quay lại Email")
                        
                        # đẩy output ra 2 file
                        FileManager.append_line("data/success.txt", f"{username}|{password}|{phone_number}|Success")
                        
                        # Log thành công    
                        Logger.success(thread_id, f"✅ Xử lý xong: {username}")
                        isOk = True
                        
                        # Xử lý xong thì đóng context, thoát Retry loop -> sang item tiếp theo
                        await context.close()
                        break 

                    except Exception as e:
                        Logger.error(thread_id, f"⚠️ Lỗi (Lần {attempt+1}): {e}")
                        
                        # Đóng context cũ bị lỗi
                        if context: await context.close()
                        
                        if "NO_CODE" in str(e):
                            failed_reason = "NO_CODE"
                            # Không cần retry nữa, lỗi này không khắc phục được bằng cách đổi IP
                            break
                    
                        if "SMS_SPAM_LIMIT" in str(e): 
                            failed_reason = "SMS_SPAM_LIMIT"
                            break

                        # --- [FIX 3] LOGIC ĐỔI IP KHI LỖI ---
                        if "Timeout" in str(e) or "IP_BANNED" in str(e) or "Target closed" in str(e):
                            failed_reason = str(e)
                            Logger.warning(thread_id, "Phát hiện mạng kém/Ban -> Đổi IP...")
                            await ProxyManager.rotate_ip(port=port, thread_id=thread_id) 
                            
                            # Đợi 5s cho ổn định 
                            BrowserUtils.random_sleep(3,5)
                            
                        
                        # Nếu là lần cuối cùng mà vẫn lỗi -> Ghi log Failed
                        if attempt == Config.RETRY_LIMIT - 1:
                             Logger.error(thread_id, f"❌ GỤC NGÃ acc: {username}")
                
                if( not isOk ):
                    FileManager.append_result("data/failed.txt", f"{username}|{password}|{phone_number}|Failed" + (f"|{failed_reason}" if failed_reason else ""))
                    

            # Đóng Browser khi xong hết data của thread này
            await browser.close()
# --- MODULE 2: ĐIỀU PHỐI (MAIN) ---
async def main():
    # Nhap so luong thread tu config 
    print("Nhập số luồng (threads) muốn chạy song song:")
    num_threads = int(input())
    base_port = BASE_PORT
    
    # Chỉ cho phép tối đa 3 trình duyệt mở cùng lúc để đỡ lag máy
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT) 
    
    # Đọc data
    list_data = FileManager.read_lines("data/input.txt")
    if not list_data:
        Logger.error("System", "File data/input.txt rỗng!")
        return
    
    # Chia data thành các chunk cho từng thread
    data_chunks = DataHelper.chunk_data(list_data, num_threads)
    
    tasks = []
    for i in range(len(data_chunks)):
        # Port tịnh tiến: 60000, 60001...
        port = base_port + i
        Logger.info(f"Đổi IP cho port {port}")
        await ProxyManager.rotate_ip(port, thread_id=i)
        await BrowserUtils.random_sleep(2,4)
        Logger.info(f"Đổi IP xong cho port {port}")
        # Gán nhiệm vụ
        tasks.append(worker(i+1, port, semaphore, data_chunks[i]))  
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())