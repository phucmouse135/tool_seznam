import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from utils import Logger, ProxyManager, BrowserUtils , DataHelper , FileManager, APIClient
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
                username = item.strip() # Giả sử item là username
                Logger.info(thread_id, f"▶️ Đang xử lý: {username}")

                # 4. Cơ chế RETRY cho từng Item cụ thể
                for attempt in range(Config.RETRY_LIMIT):
                    context = None
                    try:
                        # Tạo Context mới cho mỗi acc (Sạch sẽ cookie)
                        context, page = await BrowserUtils.create_stealth_context(
                            browser, port,
                            TARGET_CONFIG["timezone"],
                            TARGET_CONFIG["locale"],
                            TARGET_CONFIG["geolocation"]
                        )

                        # --- CHẶN TÀI NGUYÊN TRƯỚC KHI ĐI ---
                        await BrowserUtils.block_resources(page)

                        # Check IP (Optional)
                        # await page.goto("https://whoer.net", timeout=60000)
                        
                        # --- [MAIN LOGIC] ---
                        Logger.info(thread_id, "Truy cập Seznam...")
                        
                        # Tăng timeout lên 60s
                        await page.goto(
                            "https://registrace.seznam.cz/?service=email",  
                            wait_until="domcontentloaded"
                        )
                        
                        # Click Đăng ký
                        # Nên dùng try/catch nhỏ ở đây nếu nút không xuất hiện
                        reg_btn = page.locator("#register form.intro button.official")
                        if await reg_btn.is_visible(timeout=10000):
                            await reg_btn.click()
                        else:
                            raise Exception("Không tìm thấy nút đăng ký")

                        # Điền form
                        # await page.wait_for_selector("#register-username", state="visible")
                        await page.fill("#register-username", username)
                        
                        # ... Các bước tiếp theo (Password, Birthday...) ...
                        
                        Logger.success(thread_id, f"✅ Xử lý xong: {username}")
                        
                        # Xử lý xong thì đóng context, thoát Retry loop -> sang item tiếp theo
                        await context.close()
                        break 

                    except Exception as e:
                        Logger.error(thread_id, f"⚠️ Lỗi (Lần {attempt+1}): {e}")
                        
                        # Đóng context cũ bị lỗi
                        if context: await context.close()

                        # --- [FIX 3] LOGIC ĐỔI IP KHI LỖI ---
                        if "Timeout" in str(e) or "IP_BANNED" in str(e) or "Target closed" in str(e):
                            Logger.warning(thread_id, "Phát hiện mạng kém/Ban -> Đổi IP...")
                            ProxyManager.rotate_ip(port, thread_id=thread_id)
                        
                        # Nếu là lần cuối cùng mà vẫn lỗi -> Ghi log Failed
                        if attempt == Config.RETRY_LIMIT - 1:
                             Logger.error(thread_id, f"❌ GỤC NGÃ acc: {username}")

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
        port = Config.BASE_PORT + i
        # Gán nhiệm vụ
        tasks.append(worker(i+1, port, semaphore, data_chunks[i]))  
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())